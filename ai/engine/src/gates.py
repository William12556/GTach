"""
Gates for the engine loop (design-14e05e35 §6.0; change-e58fd295).

    compile_file      bounded py_compile with a temporary bytecode cache
    syntax_check      built-in: py_compile on .py files named in work-summary.txt
    pytest_targets    maps deliverables to pytest targets (unchanged mapping)
    run_command_gate  command exit code gate: 0 PASS, non-zero FAIL, not runnable UNCHECKED
    add_collection_pass  pytest gate: collection-only pass over tests/

The reviewer verdict gate stays in orchestrator.run_loop. Human approval
gates are never passed by the engine (FR-03-05). Results are returned as the
same [SYNTAX GATE] / [TEST GATE] blocks the reviewer has always received
(FR-03-04); printing stays in orchestrator.py.
"""

from __future__ import annotations

import logging
import os
import re
import shlex
import subprocess
import sys
import tempfile
import traceback

PYTEST_GATE = "pytest"
DEFAULT_PYTEST_COMMAND = "{python} -m pytest -q {targets}"
DEFAULT_TIMEOUT_SECONDS = 300
# change-711a57d5 (audit-caab2052 L-03): bound on one py_compile subprocess.
SYNTAX_TIMEOUT_SECONDS = 30
_OUTPUT_TAIL = 1000


def gate_label(name: str) -> str:
    """Block label: the pytest gate keeps its historical TEST label."""
    return "TEST" if name == PYTEST_GATE else name.upper()


def gate_status(block: str) -> str:
    """PASS, FAIL or UNCHECKED parsed from a gate block; SKIPPED for an empty block."""
    m = re.match(r"\[[A-Z0-9_\- ]+ GATE: (PASS|FAIL|UNCHECKED)\]", block or "")
    return m.group(1) if m else "SKIPPED"


def compile_file(path: str, timeout: float = SYNTAX_TIMEOUT_SECONDS) -> subprocess.CompletedProcess:
    """
    Run python -m py_compile on path, bounded by timeout (change-711a57d5, L-03).

    change-a5bd4fe1 (audit-caab2052 L-12): bytecode goes to a temporary
    directory (PYTHONPYCACHEPREFIX), removed after the call, never beside the
    checked file. subprocess.TimeoutExpired and other errors propagate.
    """
    with tempfile.TemporaryDirectory(prefix="engine-pyc-") as cache:
        return subprocess.run([sys.executable, "-m", "py_compile", path],
                              capture_output=True, text=True, timeout=timeout,
                              env={**os.environ, "PYTHONPYCACHEPREFIX": cache})


def syntax_check(state_dir: str, log: logging.Logger,
                 project_root: str | None = None) -> tuple[str, int]:
    """
    F6: py_compile each existing .py path named in work-summary.txt.

    change-a5bd4fe1 (audit-caab2052 L-12): only paths inside project_root
    (default: the working directory) are checked; a path outside it is
    skipped with a warning. Returns (gate_block, files_checked); ('', 0) when
    nothing applies.
    """
    summary_path = os.path.join(state_dir, "work-summary.txt")
    if not os.path.exists(summary_path):
        return "", 0
    with open(summary_path) as fh:
        summary_content = fh.read()

    root = os.path.realpath(project_root or os.getcwd())
    py_files = re.findall(r'["\']?([\w./\-]+\.py)["\']?', summary_content)
    seen: set[str] = set()
    unique_py_files = []
    for f in py_files:
        if f not in seen and os.path.exists(f):
            seen.add(f)
            # change-a5bd4fe1 (audit-caab2052 L-12): project paths only.
            real = os.path.realpath(os.path.abspath(f))
            if real != root and not real.startswith(root.rstrip(os.sep) + os.sep):
                log.warning("syntax gate: %s is outside the project; not checked", f)
                continue
            unique_py_files.append(f)
    if not unique_py_files:
        return "", 0

    results = []
    all_passed = True
    for py_path in unique_py_files:
        try:
            proc = compile_file(py_path)  # change-a5bd4fe1 (audit-caab2052 L-12)
            if proc.returncode == 0:
                results.append(f"  ✓ {py_path}: OK")
            else:
                all_passed = False
                err = proc.stderr.strip()[:200]
                results.append(f"  ✗ {py_path}: SYNTAX ERROR\n    {err}")
        except subprocess.TimeoutExpired:
            # change-711a57d5 (audit-caab2052 L-03): a hung compile is a failure.
            all_passed = False
            results.append(
                f"  ✗ {py_path}: syntax check timed out after {SYNTAX_TIMEOUT_SECONDS} s"
            )
        except Exception as exc:
            all_passed = False
            results.append(f"  ? {py_path}: check failed ({exc})")

    status = "PASS" if all_passed else "FAIL"
    log.info("syntax gate: %d files checked, status=%s", len(unique_py_files), status)
    block = (
        f"[SYNTAX GATE: {status}]\n"
        f"The orchestrator ran py_compile on {len(unique_py_files)} .py file(s):\n"
        + "\n".join(results)
        + "\n[END SYNTAX GATE]\n"
    )
    return block, len(unique_py_files)


def pytest_targets(deliverables: set[str], project_root: str) -> list[str]:
    """
    F6b: map deliverables to pytest targets.

    tests/ paths are taken directly; src/<component>/ maps to tests/<component>/
    when that directory exists, else to tests/test_<stem>.py or
    tests/<stem>_test.py (change-b7e3d5a9 flat-layout fallback).
    """
    targets: set[str] = set()
    for path in deliverables:
        if project_root and path.startswith(project_root):
            rel_path = path[len(project_root):].lstrip(os.sep)
        else:
            rel_path = path
        if rel_path.startswith("tests" + os.sep) or rel_path.startswith("tests/"):
            if os.path.exists(path):
                targets.add(path)
        elif rel_path.startswith("src" + os.sep) or rel_path.startswith("src/"):
            parts = rel_path.split(os.sep)
            if len(parts) >= 2:
                component = parts[1]
                test_dir = (os.path.join(project_root, "tests", component) if project_root
                            else os.path.join("tests", component))
                if os.path.isdir(test_dir):
                    targets.add(test_dir)
                else:
                    stem = os.path.splitext(os.path.basename(rel_path))[0]
                    for candidate in (f"test_{stem}.py", f"{stem}_test.py"):
                        test_file = (os.path.join(project_root, "tests", candidate) if project_root
                                     else os.path.join("tests", candidate))
                        if os.path.isfile(test_file):
                            targets.add(test_file)
                            break
    return sorted(targets)


def build_command(template: str, python: str, project_root: str, targets: list[str]) -> list[str]:
    """Split a command template; {targets} expands to one argument per target."""
    argv: list[str] = []
    for token in shlex.split(template):
        if token == "{targets}":
            argv.extend(targets)
        else:
            argv.append(token.replace("{python}", python).replace("{project_root}", project_root))
    return argv


def _gate_env(spec: dict) -> dict[str, str] | None:
    """Environment for a gate process: os.environ without spec scrub_env (M-05)."""
    scrub = set(spec.get("scrub_env") or ())
    return {k: v for k, v in os.environ.items() if k not in scrub} if scrub else None


def _truncate(output: str) -> str:
    if len(output) > _OUTPUT_TAIL:
        return "...(truncated)...\n" + output[-_OUTPUT_TAIL:]
    return output


def run_command_gate(name: str, spec: dict, targets: list[str], project_root: str,
                     log: logging.Logger) -> str:
    """
    Run one command gate and return its block.

    spec: {command, python, timeout_seconds, scrub_env}. Exit 0 PASS, non-zero
    FAIL, not runnable (missing executable, timeout, exception) UNCHECKED.
    scrub_env names environment variables removed for the gate process
    (change-82dbf16a, M-05).
    """
    command = spec.get("command") or (DEFAULT_PYTEST_COMMAND if name == PYTEST_GATE else "")
    python = spec.get("python") or sys.executable
    timeout = spec.get("timeout_seconds") or DEFAULT_TIMEOUT_SECONDS
    argv = build_command(command, python, project_root, targets)
    env = _gate_env(spec)
    log.info("%s gate: running %s", name, argv)
    try:
        proc = subprocess.run(argv, capture_output=True, text=True,
                              cwd=project_root or None, timeout=timeout, env=env)
        status = "PASS" if proc.returncode == 0 else "FAIL"
        output = proc.stdout + proc.stderr
    except Exception as exc:
        status = "UNCHECKED"
        output = f"{name} execution failed: {exc}"
        log.warning("%s gate: execution failed — %s", name, exc)
        log.debug("%s gate exception traceback:\n%s", name, traceback.format_exc())

    output = _truncate(output)

    label = gate_label(name)
    if name == PYTEST_GATE:
        target_list_str = "\n".join(f"  - {t}" for t in targets)
        header = f"The orchestrator ran pytest on {len(targets)} test target(s):\n{target_list_str}\n\n"
    else:
        header = f"The orchestrator ran: {' '.join(shlex.quote(a) for a in argv)}\n\n"
    return (f"[{label} GATE: {status}]\n"
            f"{header}"
            f"Output:\n{output.strip()}\n"
            f"[END {label} GATE]\n")


# change-a5bd4fe1 (operator decision 2026-11-05): status precedence of the
# pytest gate's two steps, worst first.
_STATUS_ORDER = ("UNCHECKED", "FAIL", "PASS")


def add_collection_pass(block: str, spec: dict, project_root: str,
                        log: logging.Logger) -> str:
    """
    change-a5bd4fe1 (operator decision 2026-11-05): collection-only pass over
    <project_root>/tests for the pytest gate, so a tests/ module that fails on
    import fails the gate.

    block is the [TEST GATE] block of the target run; returned unchanged when
    tests/ is not a directory. Otherwise the pass runs with the gate's python,
    cwd, timeout and scrub_env (spec command does not apply). Exit 0 or 5 (no
    tests collected) PASS, other exit FAIL, not runnable UNCHECKED. The block
    status becomes the worse of the two steps; the pass and its output are
    added before [END TEST GATE].
    """
    tests_dir = os.path.join(project_root, "tests")
    if not os.path.isdir(tests_dir):
        return block
    python = spec.get("python") or sys.executable
    timeout = spec.get("timeout_seconds") or DEFAULT_TIMEOUT_SECONDS
    argv = [python, "-m", "pytest", "--collect-only", "-q", tests_dir]
    try:
        proc = subprocess.run(argv, capture_output=True, text=True,
                              cwd=project_root or None, timeout=timeout, env=_gate_env(spec))
        status = "PASS" if proc.returncode in (0, 5) else "FAIL"
        output = proc.stdout + proc.stderr
    except Exception as exc:
        status = "UNCHECKED"
        output = f"collection-only pass failed: {exc}"
        log.warning("pytest gate: collection-only pass failed — %s", exc)
        log.debug("collection-only pass exception traceback:\n%s", traceback.format_exc())
    log.info("pytest gate: collection-only pass, status=%s", status)
    output = _truncate(output)

    label = gate_label(PYTEST_GATE)
    target_status = gate_status(block)
    combined = next(s for s in _STATUS_ORDER if s in (target_status, status))
    end = f"[END {label} GATE]\n"
    body = block[:-len(end)] if block.endswith(end) else block
    body = body.replace(f"[{label} GATE: {target_status}]", f"[{label} GATE: {combined}]", 1)
    return (f"{body}\n"
            f"The orchestrator ran a collection-only pass: "
            f"{' '.join(shlex.quote(a) for a in argv)}\n\n"
            f"Collection output:\n{output.strip()}\n"
            f"{end}")
