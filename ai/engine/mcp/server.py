"""
engine-mcp server — MCP server for launching and managing the AI-G&O engine.

Ported from the separate ael-mcp repository under change-5bcd46ad and
versioned with the engine. Run it with the engine's Python environment:
the orchestrator is launched with the same interpreter (sys.executable), so
the dependencies pinned in ai/engine/requirements.txt apply to both.

Tools:
    start_engine   — launch orchestrator.py as a detached background process
    engine_status  — report current run state from ai/state/
    reset_engine   — invoke orchestrator.py --mode reset synchronously

Transport: stdio (Claude Desktop)
"""

import datetime
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("engine-mcp")

# Paths relative to project_dir (framework convention)
_ORCHESTRATOR_REL = "ai/engine/src/orchestrator.py"
_CONFIG_REL       = "ai/config.yaml"
_STATE_REL        = "ai/state"
_RUN_RECORD       = "mcp-run.json"

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

    state_dir = root / _STATE_REL
    return root, orchestrator, config, state_dir


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


def _pid_alive(pid: int) -> bool:
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
        _, _, _, state_dir = _validate_project(project_dir)
    except ValueError as exc:
        return json.dumps({"error": str(exc)})

    record = _read_run_record(state_dir)

    pid_alive = False
    if record.get("pid"):
        pid_alive = _pid_alive(record["pid"])

    present = [f for f in _STATE_FILES if (state_dir / f).exists()]
    shipped  = (state_dir / ".complete").exists()
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


if __name__ == "__main__":
    mcp.run(transport="stdio")
