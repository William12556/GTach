"""
AEL Orchestrator — Ralph Loop.

Standalone tool loop: connects directly to MCP servers, sends tool
definitions to oMLX, parses model tool calls (OpenAI and Mistral
plain-text formats), dispatches tools, injects results, iterates
until no tool calls remain.

Modes:
    worker   — single work phase pass
    reviewer — single review phase pass
    loop     — full worker/reviewer Ralph Loop cycle
    reset    — clear state directory after human acceptance

Usage:
    python orchestrator.py --mode worker   --task workspace/prompt/prompt-abc123.md
    python orchestrator.py --mode reviewer --task workspace/prompt/prompt-abc123.md
    python orchestrator.py --mode loop     --task workspace/prompt/prompt-abc123.md
    python orchestrator.py --mode loop     --task "implement the login module"
    python orchestrator.py --mode reset

Terminal output legend (rich TUI):
    ╔ Ralph Loop — AEL ╗ panel          startup banner with worker/reviewer/task
    ── loop iteration N/M ──  rule      loop-level cycle counter (N = max_iterations)
    ▶ WORK PHASE / ▶ REVIEW PHASE       which loop half is active
    ── WORKER iteration N/M ──  rule    phase-level LLM call counter
    ████░░  X%  N / M tokens            context budget bar (dim/yellow/red by status)
    ╔ think ╗ panel                     model reasoning output
      call →  tool_name(args)           outbound tool call to MCP server
      result ← preview                  MCP result returned (truncated 200 chars)
    ╔ response ╗ panel                  worker final response
    ╔ ✓ SHIPPED ╗ panel                 reviewer wrote SHIP; loop exits
    ╔ ↻ REVISE ╗ panel                  reviewer feedback for next iteration
    ╔ ✗ BLOCKED ╗ panel                 loop blocked; content is RALPH-BLOCKED.md body
"""

import argparse
import asyncio
import datetime
import glob
import json
import logging
import os
import re
import subprocess
import sys
import time
import uuid

import yaml
from openai import AsyncOpenAI

sys.path.insert(0, os.path.dirname(__file__))
from mcp_client import MCPClient
from parser import parse_tool_calls

from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.rule import Rule

console = Console(highlight=False)


def _ctx_bar(estimated: int, context_window: int, status: str) -> str:
    """Render a compact inline context progress bar."""
    filled = int((estimated / context_window) * 20)
    bar = "\u2588" * filled + "\u2591" * (20 - filled)
    pct = (estimated / context_window) * 100
    color = "red" if status == "abort" else "yellow" if status == "warn" else "dim"
    return f"[{color}]  {bar}  {pct:.1f}%  {estimated:,} / {context_window:,} tokens[/{color}]"

_MCP_ERROR_PATTERNS = (
    "Error calling",
    "MCP error",
    "Input validation error",
)

_EDIT_PATTERN_ERRORS = (
    "edits failed to match",
    "E_INVALID_INPUT",
)


def _is_mcp_error(result: str) -> bool:
    """Return True if result string indicates an MCP tool error."""
    return any(result.startswith(p) or p in result for p in _MCP_ERROR_PATTERNS)


# State files cleared by reset (logs and context report excluded)
_RESET_FILES = [
    "task.md",
    "iteration.txt",
    "work-summary.txt",
    "work-complete.txt",
    "review-result.txt",
    "review-feedback.txt",
    ".ralph-complete",
    "RALPH-BLOCKED.md",
]


def load_yaml(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def read_state(state_dir: str, filename: str) -> str:
    path = os.path.join(state_dir, filename)
    return open(path).read().strip() if os.path.exists(path) else ""


def write_state(state_dir: str, filename: str, content: str) -> None:
    os.makedirs(state_dir, exist_ok=True)
    with open(os.path.join(state_dir, filename), "w") as f:
        f.write(content)


def reset_state(state_dir: str) -> int:
    """
    Remove all Ralph Loop state files from state_dir.
    Log files (ael_*.LOG) and context-budget.md are preserved.
    Returns 0 on success, 1 if state_dir does not exist.
    """
    if not os.path.isdir(state_dir):
        console.print(f"[yellow][ael] reset: state directory not found: {state_dir}[/yellow]")
        return 1
    removed = []
    for name in _RESET_FILES:
        path = os.path.join(state_dir, name)
        if os.path.exists(path):
            os.remove(path)
            removed.append(name)
    if removed:
        console.print(f"[green][ael] reset: removed {len(removed)} state file(s)[/green]")
        for name in removed:
            console.print(f"[dim]  {name}[/dim]")
    else:
        console.print("[yellow][ael] reset: state directory already clean[/yellow]")
    return 0


def resolve_context_window(
    model_name: str,
    models_dir: str,
    override: int | None,
    log: logging.Logger,
) -> int | None:
    """
    Resolve the model context window in tokens.

    Priority:
      1. config.yaml context.context_window override (if set)
      2. max_position_embeddings from model config.json on disk
         Searches models_dir recursively for a directory matching model_name.
         Handles both top-level and text_config-nested layout.

    Returns the context window as int, or None if not determinable.
    """
    if override is not None:
        log.info("context window: %d (config override)", override)
        return override

    if not models_dir:
        log.debug("context window: models_dir not set — skipping disk lookup")
        return None

    # Find all config.json files under a directory whose name matches model_name
    pattern = os.path.join(models_dir, "**", model_name, "config.json")
    matches = glob.glob(pattern, recursive=True)
    if not matches:
        log.debug("context window: no config.json found for '%s' under %s", model_name, models_dir)
        return None

    cfg_path = matches[0]
    try:
        with open(cfg_path) as f:
            cfg = json.load(f)
        # Try top-level first, then text_config (Mistral3 / vision model layout)
        ctx = (
            cfg.get("max_position_embeddings")
            or (cfg.get("text_config") or {}).get("max_position_embeddings")
        )
        if ctx:
            log.info("context window: %d (from %s)", ctx, cfg_path)
            return int(ctx)
        log.debug("context window: max_position_embeddings not found in %s", cfg_path)
    except Exception as exc:
        log.warning("context window: failed to read %s: %s", cfg_path, exc)
    return None


def estimate_tokens(messages: list[dict]) -> int:
    """
    Approximate token count for a list of chat messages.
    Uses len(content) // 4 — a standard heuristic for Mistral-family BPE.
    Slightly overestimates, which is the safe direction for budget checks.
    """
    total = 0
    for m in messages:
        content = m.get("content") or ""
        if isinstance(content, str):
            total += len(content) // 4
        elif isinstance(content, list):
            # multimodal content blocks
            for block in content:
                if isinstance(block, dict):
                    total += len(block.get("text", "")) // 4
    return total


def check_context_budget(
    estimated: int,
    context_window: int,
    warn_pct: float,
    abort_pct: float,
) -> tuple[str, float]:
    """
    Compare estimated token count against context window thresholds.
    Returns (status, fraction) where status is 'ok', 'warn', or 'abort'.
    """
    fraction = estimated / context_window
    if fraction >= abort_pct:
        return "abort", fraction
    if fraction >= warn_pct:
        return "warn", fraction
    return "ok", fraction


def write_context_report(
    state_dir: str,
    model: str,
    context_window: int | None,
    initial_tokens: int,
    warn_pct: float,
    abort_pct: float,
) -> None:
    """
    Write context-budget.md to state_dir for Strategic Domain consumption.
    This file informs the Strategic Domain of available context headroom
    before authoring the next tactical_brief or T04 prompt.
    """
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if context_window is None:
        report = (
            f"# AEL Context Budget Report\n\n"
            f"Generated: {now}\n"
            f"Model: {model}\n\n"
            f"Context window could not be determined for this model.\n"
            f"Set `context.context_window` in config.yaml to enable budget tracking.\n"
        )
        write_state(state_dir, "context-budget.md", report)
        return

    headroom = context_window - initial_tokens
    warn_tokens  = int(context_window * warn_pct)
    abort_tokens = int(context_window * abort_pct)
    initial_pct  = (initial_tokens / context_window) * 100
    # Estimate per-iteration accumulation: system prompt + task already counted,
    # each iteration adds roughly one tool call (~100 tokens) + result (~100 tokens)
    # + assistant response (~100 tokens) = ~300 tokens
    est_per_iter   = 300
    iters_to_warn  = max(0, (warn_tokens  - initial_tokens) // est_per_iter)
    iters_to_abort = max(0, (abort_tokens - initial_tokens) // est_per_iter)

    report = f"""# AEL Context Budget Report

Generated: {now}
Model: {model}
Context window: {context_window:,} tokens

## Initial task load
Estimated tokens at task start: {initial_tokens:,} tokens ({initial_pct:.1f}% of window)
Headroom available: {headroom:,} tokens

## Budget thresholds
Warn at:  {warn_tokens:,} tokens ({warn_pct*100:.0f}%)
Abort at: {abort_tokens:,} tokens ({abort_pct*100:.0f}%)

## Iteration estimates
Estimated accumulation per iteration: ~{est_per_iter} tokens
Iterations before warn threshold:  ~{iters_to_warn}
Iterations before abort threshold: ~{iters_to_abort}

## Guidance for Strategic Domain
When authoring the next tactical_brief or T04 prompt:

- Current initial load is {initial_pct:.1f}% of context window
- Each Ralph Loop phase iteration accumulates ~{est_per_iter} tokens
- Recommended tactical_brief size: ≤1,000 tokens
- Avoid embedding large design documents or code blocks in the brief
- Context pressure symptoms: duplicate tool calls, repeated reads, verbose responses
- If symptoms appear, reduce brief size and restart with --mode reset
"""
    write_state(state_dir, "context-budget.md", report)


async def await_model_ready(
    client: AsyncOpenAI,
    model: str,
    timeout: float = 60.0,
    interval: float = 2.0,
) -> None:
    """
    Poll /v1/models until the target model is listed or the endpoint is
    reachable. Raises TimeoutError if the endpoint remains unreachable.
    """
    deadline = time.monotonic() + timeout
    attempt = 0
    while True:
        attempt += 1
        try:
            models = await client.models.list()
            ids = [m.id for m in models.data]
            if model in ids:
                console.print(f"[green][ael] model ready: {model}[/green]")
                return
            # Endpoint up; model not listed — oMLX loads on first request
            console.print(f"[yellow][ael] endpoint ready; '{model}' not listed — proceeding[/yellow]")
            return
        except Exception as e:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(
                    f"[ael] inference endpoint not reachable after {timeout}s: {e}"
                ) from e
            console.print(
                f"[yellow][ael] waiting for endpoint "
                f"(attempt {attempt}, {remaining:.0f}s remaining): {e}[/yellow]"
            )
            await asyncio.sleep(interval)


def clear_state(state_dir: str, *filenames: str) -> None:
    for name in filenames:
        path = os.path.join(state_dir, name)
        if os.path.exists(path):
            os.remove(path)


def setup_logging(state_dir: str) -> logging.Logger:
    os.makedirs(state_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    log_path = os.path.join(state_dir, f"ael_{timestamp}.LOG")
    logger = logging.getLogger("ael")
    logger.setLevel(logging.DEBUG)
    if not logger.handlers:
        fh = logging.FileHandler(log_path)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(fh)
    return logger


def extract_tactical_brief(raw: str, log: logging.Logger) -> str:
    """
    Extract tactical_brief from a T04 prompt document.

    Pass 1: scan all fenced ```yaml blocks for a tactical_brief key.
    Pass 2: if Pass 1 fails, find the first '## N.N Tactical Brief' section
            header and extract the content of the first fenced block beneath it.
    Returns the brief string, or empty string if neither pass succeeds.
    """
    # Pass 1: YAML block with tactical_brief key (preferred)
    blocks = re.findall(r"```yaml\n(.*?)```", raw, re.DOTALL)
    log.debug("extract_tactical_brief: found %d YAML blocks", len(blocks))
    for i, block in enumerate(blocks):
        try:
            doc = yaml.safe_load(block)
            candidate = ((doc or {}).get("tactical_brief") or "").strip()
            if candidate:
                log.debug("extract_tactical_brief: brief found in block %d (%d chars)", i, len(candidate))
                return candidate
        except Exception as exc:
            log.debug("extract_tactical_brief: block %d parse error: %s", i, exc)

    # Pass 2: section-header fallback — locate ## N.N Tactical Brief heading
    section_match = re.search(
        r"##\s+[\d.]+\s+Tactical Brief.*?\n(.*?)(?=\n##\s|\Z)",
        raw, re.DOTALL | re.IGNORECASE,
    )
    if section_match:
        section_body = section_match.group(1)
        fence_match = re.search(r"```[^\n]*\n(.*?)```", section_body, re.DOTALL)
        if fence_match:
            candidate = fence_match.group(1).strip()
            if candidate:
                log.warning(
                    "extract_tactical_brief: YAML tactical_brief key not found — "
                    "using fenced block under section header (%d chars). "
                    "Author \u00a78.0 as a ```yaml block with tactical_brief: as root key.",
                    len(candidate),
                )
                return candidate

    log.warning(
        "extract_tactical_brief: no tactical_brief found in %d YAML blocks and no "
        "section-header fallback matched — falling back to raw document. "
        "Author \u00a78.0 as a ```yaml block with tactical_brief: as root key.",
        len(blocks),
    )
    return ""


def extract_reasoning(message, content: str, log: logging.Logger) -> tuple[str, str]:
    """
    Extract model reasoning from response message.
    Checks reasoning_content attribute first (some providers), then
    <think>...</think> tags embedded in content (Mistral/Devstral).
    Returns (reasoning, content_without_think_tags).
    """
    reasoning = getattr(message, "reasoning_content", None) or ""
    if not reasoning and content:
        think_match = re.search(r"<think>(.*?)</think>", content, re.DOTALL)
        if think_match:
            reasoning = think_match.group(1).strip()
            content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
            log.debug("extracted <think> block (%d chars)", len(reasoning))
    return reasoning, content


def format_tool_signatures(tools: list[dict]) -> str:
    """
    Render tool names with their parameter signatures for injection
    into the recipe system prompt via {{TOOLS}}.

    Format per tool:
        - tool_name(param: type [required], param: type)

    Grounded in the live MCP schema so the model cannot hallucinate
    argument names. Descriptions are omitted to keep prompt compact.
    """
    lines = []
    for t in tools:
        fn = t.get("function", {})
        name = fn.get("name", "")
        params_schema = fn.get("parameters", {})
        props = params_schema.get("properties", {})
        required = set(params_schema.get("required", []))
        args = []
        for p, schema in props.items():
            req = " [required]" if p in required else ""
            args.append(f"{p}: {schema.get('type', 'any')}{req}")
        lines.append(f"  - {name}({', '.join(args)})")
    return "\n".join(lines)


async def run_phase(
    client: AsyncOpenAI,
    mcp: MCPClient,
    model: str,
    recipe: dict,
    task: str,
    max_iterations: int,
    state_dir: str,
    log: logging.Logger,
    phase_label: str = "",
    context_window: int | None = None,
    budget_warn_pct: float = 0.80,
    budget_abort_pct: float = 0.95,
    mcp_error_threshold: int = 3,
    max_tool_calls_per_iter: int = 10,
) -> int:
    """
    Single phase (worker or reviewer): inject tools, send completions,
    dispatch tool calls, loop until no tool calls remain.
    Returns 0 on success, 1 on failure.
    """
    tools = mcp.get_openai_tools()

    # Build real tool name list and inject into recipe system prompt
    tool_list = format_tool_signatures(tools)
    system_prompt = recipe.get("instructions", "").replace("{{TOOLS}}", tool_list)

    messages: list[dict] = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": task},
    ]

    mcp_error_count = 0
    _read_counts: dict[str, int] = {}  # P3: duplicate read tracking

    label = f"{phase_label} " if phase_label else ""
    console.rule(f"[blue]{label or 'AEL'} — {escape(model)}[/blue]", style="blue")
    console.print(f"[blue][ael] tools:  {len(tools)}[/blue]")
    console.print(f"[blue][ael] task:   {escape(task[:80])}{'...' if len(task) > 80 else ''}[/blue]")
    log.info("phase start phase=%s model=%s tools=%d task=%s", phase_label or "?", model, len(tools), task)

    for iteration in range(1, max_iterations + 1):
        iter_label = f"{phase_label}  " if phase_label else ""
        console.rule(f"[blue dim]{iter_label}iteration {iteration}/{max_iterations}[/blue dim]", style="blue dim")
        log.debug("iteration %d/%d phase=%s", iteration, max_iterations, phase_label or "?")

        # Context budget check before API call
        if context_window is not None:
            estimated = estimate_tokens(messages)
            status, fraction = check_context_budget(
                estimated, context_window, budget_warn_pct, budget_abort_pct
            )
            pct_str = f"{fraction*100:.1f}%"
            if status == "abort":
                console.print(_ctx_bar(estimated, context_window, status))
                console.print("[red]  budget exceeded — aborting phase[/red]")
                log.error("context budget abort: %d / %d tokens (%.1f%%)",
                          estimated, context_window, fraction * 100)
                return 1
            elif status == "warn":
                console.print(_ctx_bar(estimated, context_window, status))
                log.warning("context budget warn: %d / %d tokens (%.1f%%)",
                            estimated, context_window, fraction * 100)
            else:
                console.print(_ctx_bar(estimated, context_window, status))
                log.debug("context budget ok: %d / %d tokens (%.1f%%)",
                          estimated, context_window, fraction * 100)

        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools or None,
            stream=False,
        )

        message = response.choices[0].message
        content = message.content or ""
        log.debug("iteration %d model response:\n%s", iteration, content)

        # Extract and display reasoning if present
        reasoning, content = extract_reasoning(message, content, log)
        if reasoning:
            log.debug("model reasoning:\n%s", reasoning)
            console.print(Panel(escape(reasoning), title="[dim cyan]think[/dim cyan]", border_style="dim cyan", expand=False))

        tool_calls: list[dict] = []

        if message.tool_calls:
            # OpenAI-format tool_calls in API response
            for tc in message.tool_calls:
                try:
                    arguments = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    arguments = {}
                tool_calls.append({"id": tc.id, "name": tc.function.name, "arguments": arguments})
            messages.append({
                "role": "assistant",
                "content": content,
                "tool_calls": [
                    {"id": tc["id"], "type": "function",
                     "function": {"name": tc["name"], "arguments": json.dumps(tc["arguments"])}}
                    for tc in tool_calls
                ],
            })
        else:
            # Mistral plain-text format — parse from content
            parsed = parse_tool_calls(content)
            if parsed:
                for tc in parsed:
                    tc["id"] = f"call_{uuid.uuid4().hex[:8]}"
                tool_calls = parsed
                messages.append({
                    "role": "assistant",
                    "content": content,
                    "tool_calls": [
                        {"id": tc["id"], "type": "function",
                         "function": {"name": tc["name"], "arguments": json.dumps(tc["arguments"])}}
                        for tc in tool_calls
                    ],
                })
            else:
                # No tool calls — final response
                messages.append({"role": "assistant", "content": content})

        # P2a: enforce per-iteration tool call cap
        if tool_calls and len(tool_calls) > max_tool_calls_per_iter:
            log.warning(
                "iteration %d: %d tool calls exceeds cap %d — truncating",
                iteration, len(tool_calls), max_tool_calls_per_iter,
            )
            console.print(f"[yellow][ael] tool call cap ({max_tool_calls_per_iter}) exceeded "
                          f"({len(tool_calls)} calls) — truncating[/yellow]")
            tool_calls = tool_calls[:max_tool_calls_per_iter]

        if not tool_calls:
            # P1b: guard against malformed final response
            if "[TOOL_CALLS]" in content or _is_mcp_error(content):
                blocked_msg = (
                    "# RALPH-BLOCKED\n\n"
                    "Worker final response is malformed "
                    "(contains tool call markers or error text).\n\n"
                    f"Content preview:\n\n    {content[:400]}\n"
                )
                write_state(state_dir, "RALPH-BLOCKED.md", blocked_msg)
                log.error("BLOCKED: worker final response malformed")
                console.print("[red][ael] BLOCKED: worker final response malformed[/red]")
                return 1
            console.print(Panel(escape(content), title="[green]response[/green]", border_style="green"))
            write_state(state_dir, "work-summary.txt", content)
            return 0

        # Dispatch tool calls and inject results
        for tc in tool_calls:
            console.print(f"[yellow]  call →[/yellow]  [bold]{escape(tc['name'])}[/bold]({escape(json.dumps(tc['arguments']))})") 
            log.debug("tool call: %s args=%s", tc["name"], json.dumps(tc["arguments"]))
            result = await mcp.call_tool(tc["name"], tc["arguments"])
            log.debug("tool result: %s", result)
            preview = result[:200] + ("..." if len(result) > 200 else "")
            console.print(f"[dim]  result ← {escape(preview)}[/dim]")
            # P3: duplicate read tracking
            if tc["name"] in ("read", "read_file", "read_text_file"):
                _path = tc["arguments"].get("path", "")
                if _path:
                    _read_counts[_path] = _read_counts.get(_path, 0) + 1
                    if _read_counts[_path] > 1:
                        log.warning("duplicate read (count=%d): %s",
                                    _read_counts[_path], _path)

            # Corrective guidance is embedded in the tool result content rather
            # than injected as a separate user message.  A standalone user message
            # after a tool message is rejected by the Mistral/oMLX API as an
            # invalid conversation structure, causing an unhandled exception.
            _corrective = ""
            _tool_result_appended = False

            # P1c: edit pattern-not-found — targeted file-read instruction
            _edit_pattern_failed = (
                tc["name"] in ("edit", "edit_file")
                and any(s in result for s in _EDIT_PATTERN_ERRORS)
            )
            if _edit_pattern_failed:
                _ep_path = tc["arguments"].get("path", "")
                log.warning("edit pattern mismatch tool=%s path=%s", tc["name"], _ep_path)
                console.print(
                    f"[yellow][ael] edit pattern mismatch: {escape(tc['name'])}: "
                    f"{escape(result[:200])}[/yellow]"
                )
                _ep_msg = (
                    f"\n\nThe edit failed because the old_text pattern was not found in "
                    f"{_ep_path or 'the target file'}. "
                    "Read the file first to get its exact current content, "
                    "then construct your edit pattern from what you observe."
                )
                if _ep_path and _ep_path.endswith(".py"):
                    _ep_proc = subprocess.run(
                        ["python", "-m", "py_compile", _ep_path],
                        capture_output=True,
                        text=True,
                    )
                    if _ep_proc.returncode != 0:
                        _ep_msg += (
                            f"\n\nAdditional: syntax error detected:\n\n"
                            f"{_ep_proc.stderr.strip()}"
                        )
                _corrective = _ep_msg
            # P1a: MCP error handling (extended pattern match)
            elif _is_mcp_error(result):
                mcp_error_count += 1
                console.print(
                    f"[red][ael] MCP error "
                    f"({mcp_error_count}/{mcp_error_threshold}): "
                    f"{escape(tc['name'])}: {escape(result[:200])}[/red]"
                )
                log.warning(
                    "MCP error %d/%d tool=%s error=%s",
                    mcp_error_count, mcp_error_threshold, tc["name"], result,
                )
                _corrective = (
                    "\n\nThe previous tool call failed with a validation error. "
                    "Review the required parameters for the tool and reissue "
                    "the call with all required arguments correctly specified."
                )
                messages.append({"role": "tool", "content": result + _corrective,
                                  "tool_call_id": tc["id"]})
                _tool_result_appended = True
                if mcp_error_count >= mcp_error_threshold:
                    blocked_msg = (
                        f"# RALPH-BLOCKED\n\n"
                        f"MCP validation error threshold reached "
                        f"({mcp_error_count} consecutive errors).\n\n"
                        f"Last error:\n\n    {result}\n\n"
                        f"Tool: {tc['name']}\n"
                    )
                    write_state(state_dir, "RALPH-BLOCKED.md", blocked_msg)
                    log.error(
                        "BLOCKED: MCP error threshold %d reached", mcp_error_threshold
                    )
                    console.print(
                        f"[red][ael] BLOCKED: MCP error threshold "
                        f"({mcp_error_threshold}) reached[/red]"
                    )
                    return 1
            else:
                mcp_error_count = 0
                # P4: post-write Python syntax check
                if tc["name"] in ("write", "edit", "write_file", "create_file"):
                    _py_path = tc["arguments"].get("path", "")
                    if _py_path and _py_path.endswith(".py"):
                        proc = subprocess.run(
                            ["python", "-m", "py_compile", _py_path],
                            capture_output=True,
                            text=True,
                        )
                        if proc.returncode != 0:
                            err = proc.stderr.strip()
                            log.warning("syntax error in %s: %s", _py_path, err)
                            console.print(
                                f"[red][ael] syntax error: {escape(_py_path)}: "
                                f"{escape(err[:200])}[/red]"
                            )
                            _corrective = (
                                f"\n\nSyntax error detected in {_py_path}:\n\n"
                                f"{err}\n\n"
                                "Correct the file before continuing."
                            )

            # Append tool result with any corrective guidance embedded.
            # P1a appends directly (before threshold check); skip here for that path.
            if not _tool_result_appended:
                messages.append({"role": "tool", "content": result + _corrective,
                                  "tool_call_id": tc["id"]})

        # Check for work-complete signal written by the model via MCP
        if os.path.exists(os.path.join(state_dir, "work-complete.txt")):
            log.info("work-complete.txt detected — phase complete")
            console.print()
            console.print("[green][ael] work-complete detected[/green]")
            return 0

    console.print(f"\n[red][ael] max iterations ({max_iterations}) reached[/red]")
    log.warning("max iterations %d reached", max_iterations)
    return 1


def run_preflight_check(task: str, log: logging.Logger) -> str:
    """
    Evaluate deterministic success criteria from the task document before
    the first worker iteration.

    Attempts two extraction strategies:
      Pass 1: YAML block containing a 'success_criteria' list.
      Pass 2: plain list under a '## N.0 Success Criteria' section heading.

    For each criterion, deterministic checks are applied where possible:
      - File path + grep string:  run grep; mark satisfied/unsatisfied.
      - .py file + 'no syntax':   run py_compile; mark satisfied/unsatisfied.
      - Otherwise:                mark as 'unchecked'.

    Returns a [PRE-FLIGHT] summary string to prepend to the worker task,
    or an empty string if no criteria block is found.
    """
    criteria: list[str] = []

    # Pass 1: YAML block with success_criteria key
    blocks = re.findall(r"```yaml\n(.*?)```", task, re.DOTALL)
    for block in blocks:
        try:
            doc = yaml.safe_load(block)
            raw = (doc or {}).get("success_criteria")
            if isinstance(raw, list) and raw:
                criteria = [str(c).strip() for c in raw if str(c).strip()]
                log.debug("preflight: found %d criteria in YAML block", len(criteria))
                break
        except Exception:
            pass

    # Pass 2: plain list under ## N.0 Success Criteria heading
    if not criteria:
        section = re.search(
            r"##\s+[\d.]+\s+Success Criteria.*?\n(.*?)(?=\n##\s|\Z)",
            task, re.DOTALL | re.IGNORECASE,
        )
        if section:
            for line in section.group(1).splitlines():
                item = re.sub(r"^\s*[-*\d.]+\s*", "", line).strip()
                if item:
                    criteria.append(item)
            log.debug("preflight: found %d criteria in section heading", len(criteria))

    if not criteria:
        log.debug("preflight: no success_criteria found — skipping")
        return ""

    lines = []
    satisfied = 0
    unchecked = 0
    for i, criterion in enumerate(criteria, 1):
        # Grep check: criterion mentions a file path and a quoted string
        grep_match = re.search(
            r"([\w./\-]+\.\w+).*?(?:contains?|has)\s+[\'\"]([^\'\"]+)[\'\"]",
            criterion, re.IGNORECASE,
        )
        # py_compile check: criterion mentions a .py file and 'no syntax'
        syntax_match = re.search(
            r"([\w./\-]+\.py).*?no\s+syntax",
            criterion, re.IGNORECASE,
        )
        if syntax_match:
            path = syntax_match.group(1)
            try:
                proc = subprocess.run(
                    ["python", "-m", "py_compile", path],
                    capture_output=True, text=True,
                )
                if proc.returncode == 0:
                    lines.append(f"  [{i}] SATISFIED  {criterion}")
                    satisfied += 1
                else:
                    lines.append(f"  [{i}] REMAINING  {criterion}")
                    lines.append(f"       syntax: {proc.stderr.strip()[:120]}")
            except Exception as exc:
                lines.append(f"  [{i}] UNCHECKED  {criterion} (error: {exc})")
                unchecked += 1
        elif grep_match:
            path, pattern = grep_match.group(1), grep_match.group(2)
            try:
                proc = subprocess.run(
                    ["grep", "-qF", pattern, path],
                    capture_output=True,
                )
                if proc.returncode == 0:
                    lines.append(f"  [{i}] SATISFIED  {criterion}")
                    satisfied += 1
                else:
                    lines.append(f"  [{i}] REMAINING  {criterion}")
            except Exception as exc:
                lines.append(f"  [{i}] UNCHECKED  {criterion} (error: {exc})")
                unchecked += 1
        else:
            lines.append(f"  [{i}] UNCHECKED  {criterion}")
            unchecked += 1

    remaining = len(criteria) - satisfied - unchecked
    summary = (
        f"[PRE-FLIGHT]\n"
        f"Success criteria: {len(criteria)} total, "
        f"{satisfied} satisfied, {remaining} remaining, {unchecked} unchecked.\n"
        + "\n".join(lines)
        + "\n[END PRE-FLIGHT]"
    )
    log.info("preflight: %d criteria, %d satisfied, %d remaining, %d unchecked",
             len(criteria), satisfied, remaining, unchecked)
    console.print(
        f"[dim][ael] pre-flight: {len(criteria)} criteria — "
        f"{satisfied} satisfied, {remaining} remaining, {unchecked} unchecked[/dim]"
    )
    return summary


async def run_loop(
    client: AsyncOpenAI,
    mcp: MCPClient,
    worker_model: str,
    reviewer_model: str,
    work_recipe: dict,
    review_recipe: dict,
    task: str,
    max_iterations: int,
    phase_max_iterations: int,
    state_dir: str,
    log: logging.Logger,
    context_window: int | None = None,
    budget_warn_pct: float = 0.80,
    budget_abort_pct: float = 0.95,
    mcp_error_threshold: int = 3,
    max_tool_calls_per_iter: int = 10,
    preflight_check: bool = False,
) -> int:
    """Full Ralph Loop: worker/reviewer cycle until SHIP or max_iterations."""
    ctx_line = f"  context:  {context_window:,} tokens\n" if context_window else ""
    console.print(Panel(
        f"  worker:   {escape(worker_model)}\n"
        f"  reviewer: {escape(reviewer_model)}\n"
        f"{ctx_line}"
        f"  task:     {escape(task[:60])}{'...' if len(task) > 60 else ''}",
        title="[bold blue]Ralph Loop — AEL[/bold blue]",
        border_style="blue",
    ))
    log.info("loop start worker=%s reviewer=%s task=%s", worker_model, reviewer_model, task)

    clear_state(state_dir,
                "review-result.txt", "review-feedback.txt",
                "work-complete.txt", "work-summary.txt", ".ralph-complete")

    # Pre-flight success criteria check (opt-in)
    if preflight_check:
        preflight_summary = run_preflight_check(task, log)
        if preflight_summary:
            task = preflight_summary + "\n\n" + task

    i = 0
    _extra = 0
    while True:
        i += 1
        if i > max_iterations + _extra:
            console.print(f"\n[red]✗ max iterations ({max_iterations + _extra}) reached without SHIP[/red]")
            log.warning("max iterations %d reached without SHIP", max_iterations + _extra)
            try:
                console.print(f"[yellow][ael] Continue for another {max_iterations} iteration(s)? [y/N]: [/yellow]", end="")
                answer = input().strip().lower()
            except (EOFError, KeyboardInterrupt):
                answer = "n"
            if answer != "y":
                return 1
            _extra += max_iterations
            log.info("user elected to continue: %d total additional iterations", _extra)
            continue
        console.rule(f"[bold blue]loop iteration {i} / {max_iterations + _extra}[/bold blue]", style="blue")

        write_state(state_dir, "iteration.txt", str(i))
        log.info("loop iteration %d/%d", i, max_iterations + _extra)

        # Work phase
        console.print("\n[bold yellow]▶ WORK PHASE[/bold yellow]")
        rc = await run_phase(client, mcp, worker_model, work_recipe,
                             task, phase_max_iterations, state_dir, log,
                             phase_label="WORKER",
                             context_window=context_window,
                             budget_warn_pct=budget_warn_pct,
                             budget_abort_pct=budget_abort_pct,
                             mcp_error_threshold=mcp_error_threshold,
                             max_tool_calls_per_iter=max_tool_calls_per_iter)
        log.info("work phase rc=%d", rc)
        if rc != 0:
            console.print("[red]✗ WORK PHASE FAILED[/red]")
            return 1

        blocked = os.path.join(state_dir, "RALPH-BLOCKED.md")
        if os.path.exists(blocked):
            blocked_content = open(blocked).read()
            log.warning("BLOCKED:\n%s", blocked_content)
            console.print(Panel(escape(blocked_content), title="[red]✗ BLOCKED[/red]", border_style="red"))
            return 1

        # Review phase — clear worker signal before reviewer starts
        clear_state(state_dir, "work-complete.txt")
        console.print("\n[bold yellow]▶ REVIEW PHASE[/bold yellow]")
        review_task = f"Review the work in state directory '{state_dir}'."
        rc = await run_phase(client, mcp, reviewer_model, review_recipe,
                             review_task, phase_max_iterations, state_dir, log,
                             phase_label="REVIEWER",
                             context_window=context_window,
                             budget_warn_pct=budget_warn_pct,
                             budget_abort_pct=budget_abort_pct,
                             mcp_error_threshold=mcp_error_threshold,
                             max_tool_calls_per_iter=max_tool_calls_per_iter)
        log.info("review phase rc=%d", rc)
        if rc != 0:
            console.print("[red]✗ REVIEW PHASE FAILED[/red]")
            return 1

        result = read_state(state_dir, "review-result.txt")
        if result == "SHIP":
            console.print(Panel(
                f"[bold]✓ SHIPPED[/bold] after {i} loop iteration(s)",
                border_style="green",
            ))
            log.info("SHIPPED iteration=%d", i)
            write_state(state_dir, ".ralph-complete", f"COMPLETE: iteration {i}")
            return 0

        feedback = read_state(state_dir, "review-feedback.txt")
        if feedback:
            log.debug("review feedback:\n%s", feedback)
            console.print(Panel(escape(feedback), title="[yellow]↻ REVISE[/yellow]", border_style="yellow"))
        else:
            console.print("[yellow]↻ REVISE[/yellow]")

        clear_state(state_dir, "work-complete.txt", "review-result.txt")


async def main_async(args: argparse.Namespace) -> int:
    config    = load_yaml(args.config)
    state_dir = os.path.abspath(config["loop"]["state_dir"])

    # Reset mode — no model or MCP connection required
    if args.mode == "reset":
        return reset_state(state_dir)

    # Warn if a prior SHIP is present and not yet cleared
    if os.path.exists(os.path.join(state_dir, ".ralph-complete")):
        console.print(f"[yellow][ael] warning: prior SHIP detected in {state_dir}[/yellow]")
        console.print("[yellow][ael]          run --mode reset after human acceptance to clear[/yellow]")

    omlx_cfg       = config["omlx"]
    max_iter          = args.max_iterations or config["loop"]["max_iterations"]
    phase_max_iter    = config["loop"].get("phase_max_iterations", max_iter)
    mcp_error_thresh      = config["loop"].get("mcp_error_threshold", 3)
    max_tool_calls        = config["loop"].get("max_tool_calls_per_iteration", 10)
    do_preflight          = config["loop"].get("preflight_check", False)
    model          = args.model or omlx_cfg["default_model"]

    # Resolve context budget config
    ctx_cfg        = config.get("context", {})
    models_dir     = ctx_cfg.get("models_dir", "")
    budget_warn    = ctx_cfg.get("budget_warn_pct", 0.80)
    budget_abort   = ctx_cfg.get("budget_abort_pct", 0.95)

    log = setup_logging(state_dir)
    log.info("AEL start mode=%s model=%s state_dir=%s", args.mode, model, state_dir)

    recipe_dir  = os.path.join(os.path.dirname(__file__), "..", "recipes")
    work_recipe = load_yaml(os.path.join(recipe_dir, "ralph-work.yaml"))
    rev_recipe  = load_yaml(os.path.join(recipe_dir, "ralph-review.yaml"))

    client = AsyncOpenAI(base_url=omlx_cfg["base_url"], api_key=omlx_cfg["api_key"])

    readiness = config.get("readiness", {})
    await await_model_ready(
        client,
        model,
        timeout=readiness.get("timeout_seconds", 60.0),
        interval=readiness.get("poll_interval_seconds", 2.0),
    )

    # Resolve context window
    context_window = resolve_context_window(
        model, models_dir, ctx_cfg.get("context_window"), log
    )
    if context_window:
        console.print(f"[blue][ael] context window: {context_window:,} tokens ({escape(model)})[/blue]")
    else:
        console.print("[yellow][ael] context window: unknown — budget tracking disabled[/yellow]")

    mcp = MCPClient(config.get("mcp_servers", {}))
    await mcp.connect()

    # Resolve task
    if args.task and os.path.exists(args.task):
        raw = open(args.task).read()
        brief = extract_tactical_brief(raw, log)
        task = brief if brief and not brief.startswith("#") else raw
    else:
        task = args.task or read_state(state_dir, "task.md")

    if not task:
        console.print(f"[red][ael] error: no task provided (--task or {state_dir}/task.md)[/red]")
        await mcp.close()
        return 1

    # Resolve placeholders and prepend runtime context
    project_root = os.getcwd()
    task = task.replace("{STATE_DIR}", state_dir).replace("{PROJECT_ROOT}", project_root)
    runtime_header = (
        f"[AEL RUNTIME CONTEXT]\n"
        f"state_dir (full absolute path): {state_dir}\n"
        f"project_root (full absolute path): {project_root}\n"
        f"Do not use 'state_dir' or 'project_root' as literal path components.\n"
        f"[END RUNTIME CONTEXT]\n\n"
    )
    task = runtime_header + task

    os.makedirs(state_dir, exist_ok=True)
    write_state(state_dir, "task.md", task)

    # Write context budget report for Strategic Domain
    initial_tokens = estimate_tokens([
        {"role": "system", "content": ""},  # system prompt estimated separately
        {"role": "user",   "content": task},
    ])
    write_context_report(
        state_dir, model, context_window,
        initial_tokens, budget_warn, budget_abort
    )
    if context_window:
        pct = (initial_tokens / context_window) * 100
        console.print(f"[blue][ael] initial task: ~{initial_tokens:,} tokens ({pct:.1f}% of window)[/blue]")
        console.print(f"[dim][ael] context report: {state_dir}/context-budget.md[/dim]")

    rc = 1  # default: failure — ensures rc is defined even on unexpected exception
    try:
        if args.mode == "worker":
            rc = await run_phase(client, mcp, model, work_recipe, task, phase_max_iter,
                                 state_dir, log, phase_label="WORKER",
                                 context_window=context_window,
                                 budget_warn_pct=budget_warn,
                                 budget_abort_pct=budget_abort,
                                 mcp_error_threshold=mcp_error_thresh,
                                 max_tool_calls_per_iter=max_tool_calls)
        elif args.mode == "reviewer":
            rc = await run_phase(client, mcp, model, rev_recipe, task, phase_max_iter,
                                 state_dir, log, phase_label="REVIEWER",
                                 context_window=context_window,
                                 budget_warn_pct=budget_warn,
                                 budget_abort_pct=budget_abort,
                                 mcp_error_threshold=mcp_error_thresh,
                                 max_tool_calls_per_iter=max_tool_calls)
        else:  # loop
            worker_model   = args.worker_model   or model
            reviewer_model = args.reviewer_model or model
            rc = await run_loop(client, mcp, worker_model, reviewer_model,
                                work_recipe, rev_recipe, task, max_iter, phase_max_iter,
                                state_dir, log,
                                context_window=context_window,
                                budget_warn_pct=budget_warn,
                                budget_abort_pct=budget_abort,
                                mcp_error_threshold=mcp_error_thresh,
                                max_tool_calls_per_iter=max_tool_calls,
                                preflight_check=do_preflight)
    finally:
        log.info("AEL end rc=%d", rc)
        await mcp.close()

    return rc


def main() -> None:
    default_config = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    p = argparse.ArgumentParser(description="AEL Orchestrator — Ralph Loop")
    p.add_argument("--config",          default=default_config,
                   help="Path to config.yaml")
    p.add_argument("--mode",            choices=["worker", "reviewer", "loop", "reset"],
                   default="loop",      help="Execution mode (default: loop)")
    p.add_argument("--task",            help="Task string or path to task file")
    p.add_argument("--model",           help="Model for all phases (overrides config default)")
    p.add_argument("--worker-model",    help="Model for work phase (loop mode only)")
    p.add_argument("--reviewer-model",  help="Model for review phase (loop mode only)")
    p.add_argument("--max-iterations",  type=int,
                   help="Iteration limit override")
    args = p.parse_args()
    rc = asyncio.run(main_async(args))
    # os._exit bypasses asyncio teardown, preventing MCP stdio subprocess hang
    for h in logging.getLogger("ael").handlers:
        h.flush()
    os._exit(rc)


if __name__ == "__main__":
    main()
