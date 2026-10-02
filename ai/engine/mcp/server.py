"""
engine-mcp server — MCP server for launching and managing the AI-G&O engine.

Ported from the separate ael-mcp repository under change-5bcd46ad and
versioned with the engine. Run it with the engine's Python environment:
the orchestrator is launched with the same interpreter (sys.executable), so
the dependencies pinned in ai/engine/requirements.txt apply to both.

Tools:
    start_engine   — launch orchestrator.py as a detached background process;
                     loop and worker mode accept only a T03 prompt inside
                     ai/workspace/ (change-793992ae)
    engine_status  — report current run state from the configured state directory
    reset_engine   — invoke orchestrator.py --mode reset synchronously
    work_status    — read-only stage report of every work item (FR-08-06)

Transport: stdio (Claude Desktop)
"""

import datetime
import json
import os
import re
import subprocess
import sys
import uuid
from pathlib import Path

import yaml
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("engine-mcp")

# Paths relative to project_dir (framework convention)
_ORCHESTRATOR_REL = "ai/engine/src/orchestrator.py"
_CONFIG_REL       = "ai/config.yaml"
_STATE_REL        = "ai/state"          # default; loop.state_dir in ai/config.yaml overrides (L-01)
_STAGES_REL       = "ai/engine/src/stages.py"
_WORKSPACE_REL    = "ai/workspace"
_RUN_RECORD       = "mcp-run.json"
_PROMPT_NAME      = re.compile(r"prompt-[0-9a-f]{8}-.+\.md")  # fullmatch (change-82dbf16a F2-01)
_TRACKED_MODES    = ("loop", "worker")

# change-793992ae (L-02): Popen handles of children started by this server,
# keyed by project root, so a finished child is reaped before the liveness probe.
_PROCS: dict[str, subprocess.Popen] = {}

# State files reported by engine_status
_STATE_FILES = [
    "task.md",
    "iteration.txt",
    "work-summary.txt",
    "work-complete.txt",
    "review-result.txt",
    "review-feedback.txt",
    ".complete",
    ".timeout",
    "BLOCKED.md",
    "awaiting-approval.md",
    "context-budget.md",
    _RUN_RECORD,
]


def _validate_project(project_dir: str) -> tuple[Path, Path, Path, Path]:
    """
    Validate project_dir and return resolved paths.
    Raises ValueError with a descriptive message on any failure.
    """
    root = Path(project_dir).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"project_dir not found: {root}")

    orchestrator = root / _ORCHESTRATOR_REL
    if not orchestrator.is_file():
        raise ValueError(f"orchestrator.py not found: {orchestrator}")

    config = root / _CONFIG_REL
    if not config.is_file():
        raise ValueError(f"config.yaml not found: {config}")

    state_dir = root / _state_dir_from_config(config)
    return root, orchestrator, config, state_dir


def _state_dir_from_config(config: Path) -> str:
    """loop.state_dir from ai/config.yaml, else ai/state (change-793992ae, L-01)."""
    try:
        data = yaml.safe_load(config.read_text()) or {}
        value = (data.get("loop") or {}).get("state_dir")
    except Exception:
        value = None
    return str(value) if isinstance(value, str) and value.strip() else _STATE_REL


def _tracked_task_error(root: Path, task: str) -> str | None:
    """
    None when task is a T03 prompt file inside <root>/ai/workspace/, else the
    reason it is refused. A free-text task would bypass the pre-run check.
    """
    path = Path(task).expanduser()
    if not path.is_absolute():
        path = root / path
    path = path.resolve()
    workspace = (root / _WORKSPACE_REL).resolve()
    if not path.is_file():
        return f"task must be a T03 prompt file inside {_WORKSPACE_REL}/; not found: {task}"
    if workspace not in path.parents:
        return f"task must be a T03 prompt file inside {_WORKSPACE_REL}/: {task}"
    if not _PROMPT_NAME.fullmatch(path.name):
        return f"task must be named prompt-<uuid>-<name>.md: {path.name}"
    return None


def _task_document_error(root: Path, task: str) -> str | None:
    """
    change-82dbf16a iteration 2 (audit F-02): the task must be an active
    evidence document of the stage before the loop stage, as the project's own
    stages.py decides (the same rule as the engine's pre-run check).
    """
    stages_py = root / _STAGES_REL
    if not stages_py.is_file():
        return f"stages.py not found: {stages_py}"
    path = Path(task).expanduser()
    if not path.is_absolute():
        path = root / path
    result = subprocess.run([sys.executable, str(stages_py), "--task-check", str(path)],
                            cwd=str(root), capture_output=True, text=True, timeout=60)
    try:
        return json.loads(result.stdout).get("error")
    except (ValueError, AttributeError):
        return f"task check failed: {(result.stderr or result.stdout).strip()[:300]}"


def _read_run_record(state_dir: Path) -> dict:
    path = state_dir / _RUN_RECORD
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            return {}
    return {}


def _write_run_record(state_dir: Path, record: dict) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / _RUN_RECORD).write_text(json.dumps(record, indent=2))


def _pid_alive(pid: int, root: str | None = None) -> bool:
    """
    True while the engine process runs. A finished child is reaped first, so
    it is not reported as alive (change-793992ae, L-02).
    """
    proc = _PROCS.get(root) if root else None
    if proc is not None and proc.pid == pid:
        return proc.poll() is None
    try:
        waited, _ = os.waitpid(pid, os.WNOHANG)
        if waited == pid:
            return False          # our child, now reaped
        return True               # our child, still running
    except ChildProcessError:
        pass                      # not a child of this server (e.g. after a restart)
    except OSError:
        return False
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


@mcp.tool()
def start_engine(project_dir: str, mode: str, task: str) -> str:
    """
    Launch orchestrator.py as a detached background process.

    Args:
        project_dir: Absolute path to the downstream project root.
        mode:        Execution mode — 'worker', 'reviewer', or 'loop'.
        task:        Task string or absolute path to a prompt file.

    Returns:
        JSON object with run_id, pid, and log_path.
    """
    if mode not in ("worker", "reviewer", "loop"):
        return json.dumps({"error": f"invalid mode '{mode}'; must be worker, reviewer, or loop"})

    try:
        root, orchestrator, config, state_dir = _validate_project(project_dir)
    except ValueError as exc:
        return json.dumps({"error": str(exc)})

    if mode in _TRACKED_MODES:
        reason = _tracked_task_error(root, task) or _task_document_error(root, task)
        if reason:
            return json.dumps({"error": reason})

    state_dir.mkdir(parents=True, exist_ok=True)

    run_id   = str(uuid.uuid4())
    log_path = str(state_dir / f"mcp-{run_id[:8]}.log")

    cmd = [
        sys.executable,
        str(orchestrator),
        "--config", str(config),
        "--mode",   mode,
        "--task",   task,
    ]

    with open(log_path, "w") as log_fh:
        proc = subprocess.Popen(
            cmd,
            cwd=str(root),
            stdout=log_fh,
            stderr=log_fh,
            start_new_session=True,  # detach from MCP server process group
        )
    _PROCS[str(root)] = proc

    record = {
        "run_id":     run_id,
        "pid":        proc.pid,
        "mode":       mode,
        "task":       task,
        "started_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "log_path":   log_path,
    }
    _write_run_record(state_dir, record)

    return json.dumps({"run_id": run_id, "pid": proc.pid, "log_path": log_path})


@mcp.tool()
def engine_status(project_dir: str) -> str:
    """
    Report current engine run state for a project.

    Args:
        project_dir: Absolute path to the downstream project root.

    Returns:
        JSON object with run record, pid_alive, state_files, shipped, blocked.
    """
    try:
        root, _, _, state_dir = _validate_project(project_dir)
    except ValueError as exc:
        return json.dumps({"error": str(exc)})

    record = _read_run_record(state_dir)

    pid_alive = False
    if record.get("pid"):
        pid_alive = _pid_alive(record["pid"], str(root))

    present = [f for f in _STATE_FILES if (state_dir / f).exists()]
    # change-82dbf16a iteration 5 (audit F4-01): only a regular file counts.
    _complete = state_dir / ".complete"
    shipped  = _complete.is_file() and not _complete.is_symlink()
    blocked  = (state_dir / "BLOCKED.md").exists()

    return json.dumps({
        **record,
        "pid_alive":   pid_alive,
        "state_files": present,
        "shipped":     shipped,
        "blocked":     blocked,
    })


@mcp.tool()
def reset_engine(project_dir: str) -> str:
    """
    Invoke orchestrator.py --mode reset synchronously to clear engine state.

    Args:
        project_dir: Absolute path to the downstream project root.

    Returns:
        JSON object with returncode and output.
    """
    try:
        root, orchestrator, config, state_dir = _validate_project(project_dir)
    except ValueError as exc:
        return json.dumps({"error": str(exc)})

    cmd = [
        sys.executable,
        str(orchestrator),
        "--config", str(config),
        "--mode",   "reset",
    ]

    result = subprocess.run(
        cmd,
        cwd=str(root),
        capture_output=True,
        text=True,
    )

    output = (result.stdout + result.stderr).strip()

    # Remove run record on successful reset
    if result.returncode == 0:
        run_record_path = state_dir / _RUN_RECORD
        if run_record_path.exists():
            run_record_path.unlink()

    return json.dumps({"returncode": result.returncode, "output": output})


@mcp.tool()
def work_status(project_dir: str) -> str:
    """
    Report the stage of every work item in a project (read-only).

    Runs the project's own ai/engine/src/stages.py, so the project's engine
    and governance model manifest apply.

    Args:
        project_dir: Absolute path to the downstream project root.

    Returns:
        JSON object: work_items (uuid -> path, documents, approvals,
        current_stage, missing, anomalies) and warnings.
    """
    try:
        root, _, _, _ = _validate_project(project_dir)
    except ValueError as exc:
        return json.dumps({"error": str(exc)})
    stages_py = root / _STAGES_REL
    if not stages_py.is_file():
        return json.dumps({"error": f"stages.py not found: {stages_py}"})
    result = subprocess.run([sys.executable, str(stages_py), "--json"], cwd=str(root),
                            capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        return result.stdout.strip() or json.dumps({"error": result.stderr.strip()})
    return result.stdout.strip()


if __name__ == "__main__":
    mcp.run(transport="stdio")
