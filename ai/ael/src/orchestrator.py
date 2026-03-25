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

Terminal output legend:
    [ael] call →   tool_name(args)       outbound tool call to MCP server
    [ael] result ← preview               MCP result returned (truncated 200 chars)
    [ael] context: N / M tokens (X%)     token budget status each iteration
    ── WORKER iteration N/M ──           phase-level LLM call counter (M = phase_max_iterations)
    ── REVIEWER iteration N/M ──         same, for reviewer phase
    loop iteration i / N  (banner)       loop-level cycle counter (N = max_iterations)
    ▶ WORK PHASE / ▶ REVIEW PHASE        which loop half is active
    [think] ...                          model reasoning / thinking output
    ↻ REVISE                             reviewer wrote REVISE; feedback follows
    ✓ SHIPPED                            reviewer wrote SHIP; loop exits
"""

import argparse
import asyncio
import datetime
import glob
import json
import logging
import os
import re
import sys
import time
import uuid

import yaml
from openai import AsyncOpenAI

sys.path.insert(0, os.path.dirname(__file__))
from mcp_client import MCPClient
from parser import parse_tool_calls

# ANSI colours
RED    = "\033[0;31m"
GREEN  = "\033[0;32m"
YELLOW = "\033[1;33m"
BLUE   = "\033[0;34m"
CYAN   = "\033[0;36m"
DIM    = "\033[2m"
NC     = "\033[0m"

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
        print(f"{YELLOW}[ael] reset: state directory not found: {state_dir}{NC}")
        return 1
    removed = []
    for name in _RESET_FILES:
        path = os.path.join(state_dir, name)
        if os.path.exists(path):
            os.remove(path)
            removed.append(name)
    if removed:
        print(f"{GREEN}[ael] reset: removed {len(removed)} state file(s){NC}")
        for name in removed:
            print(f"{DIM}  {name}{NC}")
    else:
        print(f"{YELLOW}[ael] reset: state directory already clean{NC}")
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
    """Poll until model endpoint is reachable."""
    deadline = time.monotonic() + timeout
    attempt = 0
    while True:
        attempt += 1
        try:
            models = await client.models.list()
            ids = [m.id for m in models.data]
            if model in ids:
                print(f"{GREEN}[ael] model ready: {model}{NC}")
                return
            print(f"{YELLOW}[ael] endpoint ready; '{model}' not listed — proceeding{NC}")
            return
        except Exception as e:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(
                    f"[ael] inference endpoint not reachable after {timeout}s: {e}"
                ) from e
            print(
                f"{YELLOW}[ael] waiting for endpoint "
                f"(attempt {attempt}, {remaining:.0f}s remaining): {e}{NC}"
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
    Search all fenced YAML blocks in raw for a non-empty tactical_brief key.
    Returns the brief string, or empty string if not found.
    """
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
    log.debug("extract_tactical_brief: no tactical_brief found — using raw document")
    return ""


def extract_reasoning(message, content: str, log: logging.Logger) -> tuple[str, str]:
    """Extract model reasoning from <think> tags or reasoning_content attribute."""
    reasoning = getattr(message, "reasoning_content", None) or ""
    if not reasoning and content:
        think_match = re.search(r"<think>(.*?)</think>", content, re.DOTALL)
        if think_match:
            reasoning = think_match.group(1).strip()
            content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
            log.debug("extracted <think> block (%d chars)", len(reasoning))
    return reasoning, content


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
) -> int:
    """
    Single phase (worker or reviewer): inject tools, send completions,
    dispatch tool calls, loop until no tool calls remain.
    Returns 0 on success, 1 on failure.
    """
    tools = mcp.get_openai_tools()

    # Inject real tool names into recipe system prompt
    tool_list = "\n".join(f"  - {t['function']['name']}" for t in tools)
    system_prompt = recipe.get("instructions", "").replace("{{TOOLS}}", tool_list)

    messages: list[dict] = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": task},
    ]

    label = f"{phase_label} " if phase_label else ""
    print(f"{BLUE}[ael] {label}model:  {model}{NC}")
    print(f"{BLUE}[ael] {label}tools:  {len(tools)}{NC}")
    print(f"{BLUE}[ael] {label}task:   {task[:80]}{'...' if len(task) > 80 else ''}{NC}")
    log.info("phase start phase=%s model=%s tools=%d", phase_label or "?", model, len(tools))

    for iteration in range(1, max_iterations + 1):
        iter_label = f"{phase_label}  " if phase_label else ""
        print(f"\n{BLUE}[ael] ── {iter_label}iteration {iteration}/{max_iterations} ──{NC}")
        log.debug("iteration %d/%d phase=%s", iteration, max_iterations, phase_label or "?")

        # Context budget check
        if context_window is not None:
            estimated = estimate_tokens(messages)
            status, fraction = check_context_budget(
                estimated, context_window, budget_warn_pct, budget_abort_pct
            )
            pct_str = f"{fraction*100:.1f}%"
            if status == "abort":
                print(f"{RED}[ael] context: {estimated:,} / {context_window:,} tokens "
                      f"({pct_str}) — budget exceeded, aborting phase{NC}")
                log.error("context budget abort: %d / %d tokens", estimated, context_window)
                return 1
            elif status == "warn":
                print(f"{YELLOW}[ael] context: {estimated:,} / {context_window:,} tokens "
                      f"({pct_str}) — approaching budget{NC}")
                log.warning("context budget warn: %d / %d tokens", estimated, context_window)
            else:
                print(f"{DIM}[ael] context: {estimated:,} / {context_window:,} tokens ({pct_str}){NC}")

        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools or None,
            stream=False,
        )

        message = response.choices[0].message
        content = message.content or ""
        log.debug("iteration %d response:\n%s", iteration, content)

        # Extract reasoning
        reasoning, content = extract_reasoning(message, content, log)
        if reasoning:
            log.debug("model reasoning:\n%s", reasoning)
            print(f"{DIM}{CYAN}[think] {reasoning}{NC}")

        tool_calls: list[dict] = []

        if message.tool_calls:
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
                messages.append({"role": "assistant", "content": content})

        if not tool_calls:
            print(f"\n{GREEN}[ael] response:{NC}\n{content}")
            write_state(state_dir, "work-summary.txt", content)
            return 0

        for tc in tool_calls:
            print(f"{YELLOW}[ael] call → {tc['name']}({json.dumps(tc['arguments'])}){NC}")
            log.debug("tool call: %s args=%s", tc["name"], json.dumps(tc["arguments"]))
            result = await mcp.call_tool(tc["name"], tc["arguments"])
            log.debug("tool result: %s", result)
            preview = result[:200] + ("..." if len(result) > 200 else "")
            print(f"{DIM}[ael] result ← {preview}{NC}")
            messages.append({"role": "tool", "content": result, "tool_call_id": tc["id"]})

        # Check for work-complete signal
        if os.path.exists(os.path.join(state_dir, "work-complete.txt")):
            log.info("work-complete.txt detected — phase complete")
            print(f"\n{GREEN}[ael] work-complete detected{NC}")
            return 0

    print(f"\n{RED}[ael] max iterations ({max_iterations}) reached{NC}")
    log.warning("max iterations %d reached", max_iterations)
    return 1


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
) -> int:
    """Full Ralph Loop: worker/reviewer cycle until SHIP or max_iterations."""
    print(f"{BLUE}{'═' * 63}{NC}")
    print(f"{BLUE}  Ralph Loop — AEL{NC}")
    print(f"{BLUE}{'═' * 63}{NC}")
    print(f"  worker:   {worker_model}")
    print(f"  reviewer: {reviewer_model}")
    if context_window:
        print(f"  context:  {context_window:,} tokens")
    print(f"  task:     {task[:60]}{'...' if len(task) > 60 else ''}\n")
    log.info("loop start worker=%s reviewer=%s", worker_model, reviewer_model)

    clear_state(state_dir,
                "review-result.txt", "review-feedback.txt",
                "work-complete.txt", "work-summary.txt", ".ralph-complete")

    i = 0
    _extra = 0
    while True:
        i += 1
        if i > max_iterations + _extra:
            print(f"\n{RED}✗ max iterations ({max_iterations + _extra}) reached without SHIP{NC}")
            log.warning("max iterations %d reached without SHIP", max_iterations + _extra)
            try:
                print(f"{YELLOW}[ael] Continue for another {max_iterations} iteration(s)? [y/N]: {NC}",
                      end="", flush=True)
                answer = input().strip().lower()
            except (EOFError, KeyboardInterrupt):
                answer = "n"
            if answer != "y":
                return 1
            _extra += max_iterations
            log.info("user elected to continue: %d total additional iterations", _extra)
            continue

        print(f"{BLUE}{'─' * 63}{NC}")
        print(f"{BLUE}  loop iteration {i} / {max_iterations + _extra}{NC}")
        print(f"{BLUE}{'─' * 63}{NC}")

        write_state(state_dir, "iteration.txt", str(i))
        log.info("loop iteration %d/%d", i, max_iterations + _extra)

        print(f"\n{YELLOW}▶ WORK PHASE{NC}")
        rc = await run_phase(client, mcp, worker_model, work_recipe,
                             task, phase_max_iterations, state_dir, log,
                             phase_label="WORKER",
                             context_window=context_window,
                             budget_warn_pct=budget_warn_pct,
                             budget_abort_pct=budget_abort_pct)
        log.info("work phase rc=%d", rc)
        if rc != 0:
            print(f"{RED}✗ WORK PHASE FAILED{NC}")
            return 1

        blocked = os.path.join(state_dir, "RALPH-BLOCKED.md")
        if os.path.exists(blocked):
            blocked_content = open(blocked).read()
            log.warning("BLOCKED:\n%s", blocked_content)
            print(f"\n{RED}✗ BLOCKED{NC}")
            print(blocked_content)
            return 1

        clear_state(state_dir, "work-complete.txt")
        print(f"\n{YELLOW}▶ REVIEW PHASE{NC}")
        review_task = f"Review the work in state directory '{state_dir}'."
        rc = await run_phase(client, mcp, reviewer_model, review_recipe,
                             review_task, phase_max_iterations, state_dir, log,
                             phase_label="REVIEWER",
                             context_window=context_window,
                             budget_warn_pct=budget_warn_pct,
                             budget_abort_pct=budget_abort_pct)
        log.info("review phase rc=%d", rc)
        if rc != 0:
            print(f"{RED}✗ REVIEW PHASE FAILED{NC}")
            return 1

        result = read_state(state_dir, "review-result.txt")
        if result == "SHIP":
            print(f"\n{GREEN}{'═' * 63}{NC}")
            print(f"{GREEN}  ✓ SHIPPED after {i} loop iteration(s){NC}")
            print(f"{GREEN}{'═' * 63}{NC}")
            log.info("SHIPPED iteration=%d", i)
            write_state(state_dir, ".ralph-complete", f"COMPLETE: iteration {i}")
            return 0

        print(f"\n{YELLOW}↻ REVISE — feedback for next iteration:{NC}")
        feedback = read_state(state_dir, "review-feedback.txt")
        if feedback:
            log.debug("review feedback:\n%s", feedback)
            print(feedback)

        clear_state(state_dir, "work-complete.txt", "review-result.txt")


async def main_async(args: argparse.Namespace) -> int:
    config    = load_yaml(args.config)
    state_dir = os.path.abspath(config["loop"]["state_dir"])

    if args.mode == "reset":
        return reset_state(state_dir)

    if os.path.exists(os.path.join(state_dir, ".ralph-complete")):
        print(f"{YELLOW}[ael] warning: prior SHIP detected in {state_dir}{NC}")
        print(f"{YELLOW}[ael]          run --mode reset after human acceptance to clear{NC}")

    omlx_cfg       = config["omlx"]
    max_iter       = args.max_iterations or config["loop"]["max_iterations"]
    phase_max_iter = config["loop"].get("phase_max_iterations", max_iter)
    model          = args.model or omlx_cfg["default_model"]

    ctx_cfg      = config.get("context", {})
    models_dir   = ctx_cfg.get("models_dir", "")
    budget_warn  = ctx_cfg.get("budget_warn_pct", 0.80)
    budget_abort = ctx_cfg.get("budget_abort_pct", 0.95)

    log = setup_logging(state_dir)
    log.info("AEL start mode=%s model=%s state_dir=%s", args.mode, model, state_dir)

    recipe_dir  = os.path.join(os.path.dirname(__file__), "..", "recipes")
    work_recipe = load_yaml(os.path.join(recipe_dir, "ralph-work.yaml"))
    rev_recipe  = load_yaml(os.path.join(recipe_dir, "ralph-review.yaml"))

    client = AsyncOpenAI(base_url=omlx_cfg["base_url"], api_key=omlx_cfg["api_key"])

    readiness = config.get("readiness", {})
    await await_model_ready(
        client, model,
        timeout=readiness.get("timeout_seconds", 60.0),
        interval=readiness.get("poll_interval_seconds", 2.0),
    )

    context_window = resolve_context_window(
        model, models_dir, ctx_cfg.get("context_window"), log
    )
    if context_window:
        print(f"{BLUE}[ael] context window: {context_window:,} tokens ({model}){NC}")
    else:
        print(f"{YELLOW}[ael] context window: unknown — budget tracking disabled{NC}")

    mcp = MCPClient(config.get("mcp_servers", {}))
    await mcp.connect()

    if args.task and os.path.exists(args.task):
        raw = open(args.task).read()
        brief = extract_tactical_brief(raw, log)
        task = brief if brief and not brief.startswith("#") else raw
    else:
        task = args.task or read_state(state_dir, "task.md")

    if not task:
        print(f"{RED}[ael] error: no task provided (--task or {state_dir}/task.md){NC}")
        await mcp.close()
        return 1

    project_root = os.getcwd()
    task = task.replace("{STATE_DIR}", state_dir).replace("{PROJECT_ROOT}", project_root)
    runtime_header = (
        f"[AEL RUNTIME CONTEXT]\n"
        f"STATE_DIR: {state_dir}\n"
        f"PROJECT_ROOT: {project_root}\n"
        f"[END RUNTIME CONTEXT]\n\n"
    )
    task = runtime_header + task

    os.makedirs(state_dir, exist_ok=True)
    write_state(state_dir, "task.md", task)

    initial_tokens = estimate_tokens([
        {"role": "system", "content": ""},
        {"role": "user",   "content": task},
    ])
    write_context_report(
        state_dir, model, context_window,
        initial_tokens, budget_warn, budget_abort
    )
    if context_window:
        pct = (initial_tokens / context_window) * 100
        print(f"{BLUE}[ael] initial task: ~{initial_tokens:,} tokens ({pct:.1f}% of window){NC}")
        print(f"{DIM}[ael] context report: {state_dir}/context-budget.md{NC}")

    try:
        if args.mode == "worker":
            rc = await run_phase(client, mcp, model, work_recipe, task, phase_max_iter,
                                 state_dir, log, phase_label="WORKER",
                                 context_window=context_window,
                                 budget_warn_pct=budget_warn,
                                 budget_abort_pct=budget_abort)
        elif args.mode == "reviewer":
            rc = await run_phase(client, mcp, model, rev_recipe, task, phase_max_iter,
                                 state_dir, log, phase_label="REVIEWER",
                                 context_window=context_window,
                                 budget_warn_pct=budget_warn,
                                 budget_abort_pct=budget_abort)
        else:
            worker_model   = args.worker_model   or model
            reviewer_model = args.reviewer_model or model
            rc = await run_loop(client, mcp, worker_model, reviewer_model,
                                work_recipe, rev_recipe, task, max_iter, phase_max_iter,
                                state_dir, log,
                                context_window=context_window,
                                budget_warn_pct=budget_warn,
                                budget_abort_pct=budget_abort)
    finally:
        await mcp.close()

    return rc


def main() -> None:
    default_config = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    p = argparse.ArgumentParser(description="AEL Orchestrator — Ralph Loop")
    p.add_argument("--config",          default=default_config)
    p.add_argument("--mode",            choices=["worker", "reviewer", "loop", "reset"],
                   default="loop")
    p.add_argument("--task",            help="Task string or path to task file")
    p.add_argument("--model",           help="Model override")
    p.add_argument("--worker-model",    help="Worker model (loop mode)")
    p.add_argument("--reviewer-model",  help="Reviewer model (loop mode)")
    p.add_argument("--max-iterations",  type=int, help="Outer loop iteration limit override")
    args = p.parse_args()
    rc = asyncio.run(main_async(args))
    os._exit(rc)


if __name__ == "__main__":
    main()
