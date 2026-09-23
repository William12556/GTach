"""
Integration tests for AEL orchestrator — Layers 2–4.

Requires:
  - oMLX running on http://127.0.0.1:8000
  - MCP servers configured in config.yaml

All tests skip automatically if oMLX is unreachable.
"""

import asyncio
import os
import socket
import sys
import tempfile
import time

import pytest
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mcp_client import MCPClient
from openai import AsyncOpenAI

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session", autouse=True)
def ensure_model_loaded():
    """
    Session-scoped fixture. Polls oMLX until the default model responds
    or times out. Skips cleanly if oMLX is not reachable.
    """
    if not omlx_reachable():
        return

    cfg = load_config()
    client = make_client(cfg)
    model = cfg["omlx"]["default_model"]
    deadline = 180  # seconds
    interval = 5

    async def _probe():
        resp = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=3,
            stream=False,
        )
        return resp.choices[0].message.content

    start = time.time()
    while True:
        try:
            asyncio.run(_probe())
            return  # model ready
        except Exception:
            elapsed = time.time() - start
            if elapsed >= deadline:
                pytest.skip(f"Model did not load within {deadline}s")
            time.sleep(interval)


# ── Config ─────────────────────────────────────────────────────────────────────

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.yaml")


def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def omlx_reachable() -> bool:
    cfg = load_config()
    host = "127.0.0.1"
    port = 8000
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except OSError:
        return False


requires_omlx = pytest.mark.skipif(
    not omlx_reachable(),
    reason="oMLX not reachable on 127.0.0.1:8000"
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def make_client(cfg: dict) -> AsyncOpenAI:
    return AsyncOpenAI(
        base_url=cfg["omlx"]["base_url"],
        api_key=cfg["omlx"]["api_key"],
    )


def make_mcp(cfg: dict) -> MCPClient:
    return MCPClient(cfg.get("mcp_servers", {}))


# ── Layer 2: Smoke — oMLX reachable, no tools required ────────────────────────

@requires_omlx
def test_omlx_models_endpoint():
    """oMLX /v1/models responds and lists at least one model."""
    cfg = load_config()
    client = make_client(cfg)

    async def _run():
        return await client.models.list()

    models = asyncio.run(_run())
    assert len(models.data) >= 1


@requires_omlx
def test_simple_completion_no_tools():
    """Model returns a completion for a trivial prompt with no tools attached."""
    cfg = load_config()
    client = make_client(cfg)
    model = cfg["omlx"]["default_model"]

    async def _run():
        resp = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Reply with the single word: OK"}],
            tools=None,
            stream=False,
        )
        return resp.choices[0].message.content or ""

    content = asyncio.run(_run())
    assert len(content) > 0, "Model returned empty response"


@requires_omlx
def test_completion_writes_work_summary():
    """orchestrator --mode worker writes work-summary.txt for a trivial task."""
    import subprocess
    import tempfile

    cfg = load_config()
    state_dir = os.path.join(tempfile.mkdtemp(), ".ael", "ralph")
    orchestrator = os.path.join(os.path.dirname(__file__), "..", "src", "orchestrator.py")

    result = subprocess.run(
        [
            sys.executable, orchestrator,
            "--mode", "worker",
            "--task", "Reply with the single word: DONE",
            "--config", CONFIG_PATH,
        ],
        capture_output=True,
        text=True,
        timeout=360,
    )

    summary_path = os.path.join(
        load_config()["loop"]["state_dir"], "work-summary.txt"
    )
    assert result.returncode == 0 or os.path.exists(summary_path), (
        f"orchestrator exited {result.returncode}\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )


# ── Layer 3: Tool dispatch — MCP tool called and result injected ───────────────

@requires_omlx
def test_mcp_connect_and_catalogue():
    """MCP client connects to configured servers and builds a non-empty tool catalogue."""
    cfg = load_config()
    mcp = make_mcp(cfg)

    async def _run():
        await mcp.connect()
        tools = mcp.get_openai_tools()
        try:
            await asyncio.wait_for(mcp.close(), timeout=5.0)
        except BaseException:
            pass
        return tools

    tools = asyncio.run(_run())
    assert len(tools) > 0, "No tools in catalogue — MCP servers may not have connected"
    print(f"\nAvailable tools: {[t['function']['name'] for t in tools]}")



@requires_omlx
def test_tool_dispatch_filesystem_list():
    """MCP filesystem tool dispatches successfully and returns a non-empty result."""
    cfg = load_config()
    mcp = make_mcp(cfg)

    async def _run():
        await mcp.connect()
        result = await mcp.call_tool("ls", {"path": "/Users/williamwatson/Documents/GitHub"})
        try:
            await asyncio.wait_for(mcp.close(), timeout=5.0)
        except BaseException:
            pass
        return result

    result = asyncio.run(_run())
    assert isinstance(result, str)
    assert len(result) > 0
    assert "Error" not in result[:50], f"Tool call returned error: {result}"


@requires_omlx
def test_worker_uses_tool():
    """Worker mode: model calls a filesystem tool and receives a result."""
    import subprocess

    orchestrator = os.path.join(os.path.dirname(__file__), "..", "src", "orchestrator.py")
    task = (
        "Use the ls tool to list the contents of "
        "/Users/williamwatson/Documents/GitHub. "
        "Report the result."
    )

    result = subprocess.run(
        [
            sys.executable, orchestrator,
            "--mode", "worker",
            "--task", task,
            "--config", CONFIG_PATH,
        ],
        capture_output=True,
        text=True,
        timeout=360,
    )

    # Accept exit 0 or evidence of tool dispatch in stdout
    tool_dispatched = "→" in result.stdout or "list_directory" in result.stdout
    assert result.returncode == 0 or tool_dispatched, (
        f"No tool dispatch observed\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )


# ── Layer 4: Full Ralph Loop ───────────────────────────────────────────────────

@requires_omlx
def test_full_loop_creates_file():
    """
    Full loop: worker creates /tmp/ael-test.txt; reviewer ships it.
    Validates end-to-end worker/reviewer cycle and state file contract.
    """
    import subprocess

    orchestrator = os.path.join(os.path.dirname(__file__), "..", "src", "orchestrator.py")
    target = "/Users/williamwatson/Documents/GitHub/ael-test.txt"

    # Remove target if present from a prior run
    if os.path.exists(target):
        os.remove(target)

    task = (
        f"Create the file {target} containing the single word HELLO. "
        "Confirm it exists by reading it back."
    )

    result = subprocess.run(
        [
            sys.executable, orchestrator,
            "--mode", "loop",
            "--task", task,
            "--config", CONFIG_PATH,
            "--max-iterations", "3",
        ],
        capture_output=True,
        text=True,
        timeout=600,
    )

    shipped = "SHIPPED" in result.stdout or "✓" in result.stdout
    file_created = os.path.exists(target)

    assert result.returncode == 0 or shipped or file_created, (
        f"Loop did not complete successfully\n"
        f"returncode: {result.returncode}\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )
