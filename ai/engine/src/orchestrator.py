"""
Engine orchestrator — worker/reviewer loop.

Standalone tool loop: connects directly to MCP servers, sends tool
definitions to the worker and reviewer providers (providers.py: oMLX,
OpenAI-compatible APIs, Anthropic), dispatches tool calls, injects results,
iterates until no tool calls remain.

Modes:
    worker   — single work phase pass
    reviewer — single review phase pass
    loop     — full worker/reviewer loop cycle
    reset    — clear state directory after human acceptance

Usage:
    python orchestrator.py --mode worker   --task ai/workspace/prompt/prompt-abc123.md
    python orchestrator.py --mode reviewer --task ai/workspace/prompt/prompt-abc123.md
    python orchestrator.py --mode loop     --task ai/workspace/prompt/prompt-abc123.md
    python orchestrator.py --mode loop     --task "implement the login module"
    python orchestrator.py --mode reset

Terminal output legend (rich TUI):
    ╔ engine loop ╗ panel            startup banner with worker/reviewer/task
    ── loop iteration N/M ──  rule      loop-level cycle counter (N = max_iterations)
    ▶ WORK PHASE / ▶ REVIEW PHASE       which loop half is active
    ── WORKER iteration N/M ──  rule    phase-level LLM call counter
    ████░░  X%  N / M tokens            context budget bar (dim/yellow/red by status)
    ╔ think ╗ panel                     model reasoning output (tagged: reasoning_content / <think>)
    ╔ narration ╗ panel                 untagged model commentary preceding a tool call (F20)
      call →  tool_name(args)           outbound tool call to MCP server
      result ← preview                  MCP result returned (truncated 200 chars)
    ╔ response ╗ panel                  worker final response
    ╔ ✓ SHIPPED ╗ panel                 reviewer wrote SHIP; loop exits
    ╔ ↻ REVISE ╗ panel                  reviewer feedback for next iteration
    ╔ ✗ BLOCKED ╗ panel                 loop blocked; content is BLOCKED.md body
"""

import argparse
import asyncio
import datetime
import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import time
import traceback

import yaml

# Project root derived from working directory, consistent with _archive_audit_artifacts() precedent.
PROJECT_ROOT: str = os.getcwd()
from typing import Any, Callable

sys.path.insert(0, os.path.dirname(__file__))
from mcp_client import MCPClient
from providers import (ConfigError, ProviderError, as_provider, build_role_bindings,
                       query_omlx_context_window as _query_omlx_context_window)
import gates as G
import scope as S
import stages as ST
from manifest import ManifestError, load_manifest, locate_manifest
from scope import is_write_tool, written_targets as _written_targets

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

# F7: MCP error detection uses prefix matching only to avoid false positives.
# A benign result containing these strings mid-text will not be misclassified.
_MCP_ERROR_PREFIXES = (
    "Error:",
    "Error calling",
    "MCP error",
)

_EDIT_PATTERN_ERRORS = (
    "edits failed to match",
    "E_INVALID_INPUT",
)

# F12: Stall detection — consecutive identical REVISE feedback threshold
_DEFAULT_STALL_THRESHOLD = 3

# F14: Completion call retry settings
_COMPLETION_MAX_RETRIES = 3
_COMPLETION_INITIAL_BACKOFF = 2.0  # seconds
_COMPLETION_BACKOFF_MULTIPLIER = 2.0


def _validate_write_scope(tool_name: str, arguments: dict, project_root: str,
                          write_scope: "S.WriteScope | None" = None) -> str | None:
    """
    F4 / change-bdc6820f: pre-dispatch write check (scope.check). Returns None
    when allowed or not a write tool, otherwise the error message for the
    worker. Without write_scope only project-root containment applies.
    """
    violation = S.check(tool_name, arguments, project_root, write_scope)
    return violation.message if violation else None


_TASK_FILE_SUFFIXES = (".md", ".yaml", ".yml", ".txt")


def _looks_like_task_path(value: str) -> bool:
    """
    change-c37198be (D2): True when a --task value reads as a file path rather
    than task text: a single token (no whitespace) that ends in a task-file
    suffix or contains a path separator. A missing file named this way must
    stop the run; used as text, it becomes an unscoped task.
    """
    if not value or any(ch.isspace() for ch in value):
        return False
    return value.lower().endswith(_TASK_FILE_SUFFIXES) or "/" in value or os.sep in value


def _select_recipe_set(state_dir: str) -> str:
    """
    Recipe selection: audit-index.md in the state directory selects the audit
    recipe pair; otherwise the standard loop pair. Same signal the audit
    scope/SHIP/archive logic keys on — mode detection is single-sourced.
    Extracted from main_async under change-c37198be so it can be tested.
    """
    return "audit" if os.path.exists(os.path.join(state_dir, "audit-index.md")) else "loop"


def _synthesize_work_summary(
    state_dir: str,
    written_paths: set[str],
    reason: str,
    log: logging.Logger,
) -> bool:
    """
    change-a2f9c4d1: reconstruct work-summary.txt from observed write operations
    when a worker phase terminated without producing one.

    loop-work.yaml PROCEDURE step 6 instructs the worker to write this file, but
    only the final-response exit (F13) persists it as a fallback. A phase that
    exits on the wall-clock cap, the work-complete signal, or iteration
    exhaustion leaves deliverables on disk with no manifest — and since
    _extract_deliverables reads this file, the read-evidence, syntax and pytest
    gates then pass vacuously.

    Synthesis is deliberately conservative:
      - never overwrites an existing work-summary.txt
      - writes nothing when no successful write landed outside state_dir, so a
        phase that genuinely produced nothing still presents no manifest
      - labels itself plainly, so the reviewer does not mistake it for the
        worker's own account of its reasoning

    Returns True if a summary was written.
    """
    summary_path = os.path.join(state_dir, "work-summary.txt")
    if os.path.exists(summary_path):
        return False
    if not written_paths:
        log.debug("work-summary synthesis: no observed writes — skipping")
        return False

    state_dir_abs = os.path.abspath(state_dir)
    deliverables = sorted(
        p for p in written_paths
        if not p.startswith(state_dir_abs + os.sep) and os.path.isfile(p)
    )
    if not deliverables:
        log.debug("work-summary synthesis: no deliverables outside state_dir — skipping")
        return False

    body = (
        "ORCHESTRATOR-GENERATED SUMMARY\n\n"
        f"The worker phase ended ({reason}) without writing work-summary.txt.\n"
        "This manifest was reconstructed from write operations observed during\n"
        "the phase. It records what was written, not why.\n\n"
        "Files written:\n"
        + "".join(f"  {p}\n" for p in deliverables)
    )
    write_state(state_dir, "work-summary.txt", body)
    log.warning(
        "work-summary synthesized from %d observed write(s) (%s)",
        len(deliverables), reason,
    )
    return True


def _append_observed_manifest(
    state_dir: str,
    written_paths: set[str],
    content: str,
    log: logging.Logger,
) -> bool:
    """
    change-d1f4a83b (N1): append an observed-write manifest to work-summary.txt
    when the worker's own final response names none of the files it wrote.

    F13 persists the worker's final message verbatim as work-summary.txt on the
    normal-completion path, on the assumption that a worker which finishes
    deliberately has written the manifest loop-work.yaml PROCEDURE step 6 asks
    for. That assumption does not hold: a final message may be a single
    narrating sentence. _extract_deliverables then returns the empty set and the
    syntax, pytest and read-evidence gates all no-op — the vacuous-pass
    condition change-a2f9c4d1 set out to close, reached by the one exit that
    change did not touch. Live-confirmed, run 8c2040d3 cycle 1.

    The worker's own account is never overwritten, only extended, and only when
    it names none of the observed deliverables. A worker that did write a proper
    manifest is left untouched.

    Returns True if a manifest section was appended.
    """
    state_dir_abs = os.path.abspath(state_dir)
    deliverables = sorted(
        p for p in written_paths
        if not p.startswith(state_dir_abs + os.sep) and os.path.isfile(p)
    )
    if not deliverables:
        return False
    if any(os.path.basename(p) in content for p in deliverables):
        log.debug("work-summary: final response already names a deliverable — no append")
        return False

    summary_path = os.path.join(state_dir, "work-summary.txt")
    try:
        with open(summary_path, "a") as fh:
            fh.write(
                "\n\nORCHESTRATOR-APPENDED MANIFEST\n\n"
                "The worker's final response named none of the files it wrote\n"
                "during this phase. This list was recorded from observed write\n"
                "operations so that the review gates adjudicate this cycle's\n"
                "actual output. It records what was written, not why.\n\n"
                "Files written:\n"
                + "".join(f"  {p}\n" for p in deliverables)
            )
    except OSError as exc:
        log.warning("work-summary manifest append failed: %s", exc)
        return False

    log.warning(
        "work-summary manifest appended from %d observed write(s) "
        "(worker final response named none)", len(deliverables),
    )
    return True


def _validate_audit_report_write(tool_name: str, arguments: dict, state_dir: str) -> str | None:
    """
    F21: Block writes to audit-report.md that would discard prior findings.

    audit-report.md is append-only across a 25-item audit run. A write/write_file/
    create_file call (overwrite semantics) whose content omits the file's existing
    content would silently destroy previously recorded findings. edit/edit_file
    calls (patch semantics) are not affected.

    Returns None if safe (not a write tool, not this file, file absent/empty,
    or existing content is preserved in the new content). Returns an error
    message string otherwise.
    """
    if tool_name not in ("write", "write_file", "create_file", "create"):
        return None
    # change-c37198be (D3): filesystem-mcp 2.x `create` batches files[{path, content}].
    writes = [(arguments.get("path") or arguments.get("file_path") or "", arguments.get("content"))]
    writes += [(f.get("path") or f.get("file_path") or "", f.get("content"))
               for f in arguments.get("files") or [] if isinstance(f, dict)]
    report_path = os.path.join(state_dir, "audit-report.md")
    if not os.path.exists(report_path):
        return None
    existing = open(report_path).read().strip()
    if not existing:
        return None
    if all(os.path.basename(t) != "audit-report.md" or existing in (c or "").strip()
           for t, c in writes):
        return None
    return (
        f"Error: This write would discard {len(existing)} characters of existing "
        "audit-report.md findings. audit-report.md is append-only \u2014 use the edit "
        "tool to append, or include the full existing content before your new entry."
    )


def _is_mcp_error(result: str) -> bool:
    """
    F7: Return True if result string indicates an MCP tool error.

    Uses prefix matching only to avoid false positives — a benign result
    containing error-like text mid-string will not be misclassified.
    """
    return any(result.startswith(p) for p in _MCP_ERROR_PREFIXES)


def _is_verdict_line(line: str) -> str | None:
    """
    Return 'SHIP' or 'REVISE' if a line consists solely of that verdict token,
    otherwise None.

    A line qualifies when stripping every non-alphabetic character leaves
    exactly the token. This admits the decorations models actually emit —
    '**SHIP**', 'SHIP.', '### REVISE', '- REVISE:' — while rejecting any line
    that also carries prose, so a verdict word occurring inside a sentence is
    never mistaken for a declaration.
    """
    token = re.sub(r"[^A-Za-z]", "", line).upper()
    return token if token in ("SHIP", "REVISE") else None


def _normalize_verdict(text: str) -> str:
    """
    Normalize a review verdict string to SHIP or REVISE.

    change-3b9e6d72: two passes, applied in order:

      1. Isolated-line scan. Any line that is nothing but a verdict token is a
         verdict declaration; the LAST such line wins. This is the pass that
         matters in practice — a reviewer which explains its reasoning before
         concluding places its verdict at the end, and under the previous
         leading-token-only rule such a review could never ship.
      2. Leading-token fallback. Preserves the original contract for the
         'SHIP: the code looks good...' single-line form, where the verdict
         opens the message and prose follows on the same line.

    Handles decorated forms in both passes: 'SHIP', 'ship', 'SHIP.',
    '**SHIP**', 'SHIP!' -> 'SHIP'.

    Returns 'REVISE' unless a pass positively identifies SHIP — an
    unparseable verdict must never ship.
    """
    if not text:
        return "REVISE"

    # Pass 1: isolated verdict token on its own line; last occurrence wins.
    trailing: str | None = None
    for line in text.splitlines():
        found = _is_verdict_line(line)
        if found:
            trailing = found
    if trailing:
        return trailing

    # Pass 2: leading token of the message.
    tokens = text.strip().split()
    if not tokens:
        return "REVISE"

    # Normalize: uppercase, strip non-alphabetics
    normalized = re.sub(r'[^A-Za-z]', '', tokens[0]).upper()

    # SHIP set: exact match only
    if normalized == "SHIP":
        return "SHIP"

    return "REVISE"


def _strip_verdict(text: str) -> str:
    """
    Return the reviewer's message with its verdict declaration removed, for use
    as REVISE feedback body.

    Removes every isolated verdict line (the form _normalize_verdict pass 1
    reads). If none is present, falls back to dropping the leading token, which
    is the form pass 2 reads.
    """
    lines = text.splitlines()
    kept = [ln for ln in lines if not _is_verdict_line(ln)]
    if len(kept) != len(lines):
        return "\n".join(kept).strip()

    tokens = text.strip().split(None, 1)
    if not tokens:
        return ""
    # change-d1f4a83b (N3): drop the leading token only when it is itself a
    # verdict. A reviewer message carrying no verdict anywhere still reaches
    # this path, because _normalize_verdict defaults to REVISE; dropping its
    # first word then removes an ordinary word of prose from the feedback the
    # next worker reads.
    if _is_verdict_line(tokens[0]) is None:
        return text.strip()
    return tokens[1].strip() if len(tokens) > 1 else ""


# State files cleared by reset (logs and context report excluded)
_RESET_FILES = [
    "task.md",
    "iteration.txt",
    "work-summary.txt",
    "work-complete.txt",
    "review-result.txt",
    "review-feedback.txt",
    ".complete",
    ".timeout",  # F10: duration-limit sentinel
    "BLOCKED.md",
    "audit-index.md",
    "audit-report.md",
]


def _hash_feedback(feedback: str) -> str:
    """F12: Return a short hash of feedback content for stall detection."""
    return hashlib.sha256(feedback.encode()).hexdigest()[:16] if feedback else ""


def _truncate_tool_result(content: str, max_chars: int) -> str:
    """
    Truncate a tool result to max_chars using head/tail with an elision marker.

    When content exceeds max_chars, returns a head portion + elision marker
    stating the omitted character count + tail portion. The marker and both
    portions together fit within max_chars.

    Args:
        content: The full tool result content.
        max_chars: Maximum allowed character length.

    Returns:
        The original content if within limit, otherwise truncated with marker.
    """
    if len(content) <= max_chars:
        return content

    # Reserve space for the elision marker (estimate ~60 chars for the message)
    omitted = len(content) - max_chars
    marker = f"\n\n... [{omitted:,} characters omitted] ...\n\n"

    # Split remaining budget between head and tail (60/40 split favors head)
    available = max_chars - len(marker)
    if available <= 0:
        # Edge case: max_chars too small even for marker
        return content[:max_chars]

    head_len = int(available * 0.6)
    tail_len = available - head_len

    return content[:head_len] + marker + content[-tail_len:]


async def _completion_with_retry(
    provider,
    model: str,
    messages: list[dict],
    tools: list[dict] | None,
    log: logging.Logger,
    state_dir: str,
    max_retries: int = _COMPLETION_MAX_RETRIES,
    initial_backoff: float = _COMPLETION_INITIAL_BACKOFF,
    backoff_multiplier: float = _COMPLETION_BACKOFF_MULTIPLIER,
    max_completion_tokens: int | None = None,
):
    """
    F14: Bounded retry with exponential backoff around the completion call.

    On persistent failure after max_retries, writes BLOCKED.md and raises
    a RuntimeError to signal clean termination (no uncaught exception).

    Args:
        provider: A providers.py provider; returns a normalised Completion.
        max_completion_tokens: When non-null, passed as max_tokens to the completion
            call to cap output length. When null, the provider default applies.
    """
    backoff = initial_backoff
    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            return await provider.complete(model, messages, tools, max_completion_tokens)
        except Exception as e:
            last_error = e
            log.warning(
                "completion call failed (attempt %d/%d): %s",
                attempt, max_retries, e,
            )
            if attempt < max_retries:
                console.print(
                    f"[yellow][engine] completion error (attempt {attempt}/{max_retries}), "
                    f"retrying in {backoff:.1f}s: {e}[/yellow]"
                )
                await asyncio.sleep(backoff)
                backoff *= backoff_multiplier
            else:
                # Persistent failure — BLOCK cleanly
                tb = traceback.format_exc()
                log.error("completion call persistent failure:\n%s", tb)
                blocked_msg = (
                    "# BLOCKED\n\n"
                    f"Completion call failed after {max_retries} attempts.\n\n"
                    f"Last error: {last_error}\n\n"
                    f"Traceback:\n```\n{tb}\n```\n"
                )
                write_state(state_dir, "BLOCKED.md", blocked_msg)
                console.print(
                    f"[red][engine] BLOCKED: completion call failed after {max_retries} attempts[/red]"
                )
                raise RuntimeError(f"Completion call failed: {last_error}") from last_error

    # Should not reach here, but satisfy type checker
    raise RuntimeError("Unexpected: completion retry loop exited without return or raise")


def _archive_audit_artifacts(state_dir: str, task_path: str | None, log: logging.Logger) -> None:
    """
    Copy audit-index.md and audit-report.md from state_dir to ai/workspace/audit/
    with canonical naming: audit-<uuid>-index.md and audit-<uuid>-report.md.
    Called after a successful audit loop SHIP. No-op if audit-report.md is absent.
    UUID is extracted from the task file path basename (first 8-hex substring).
    Falls back to yyyymmdd timestamp if UUID cannot be determined.
    """
    report_src = os.path.join(state_dir, "audit-report.md")
    if not os.path.exists(report_src):
        return  # not an audit run

    index_src = os.path.join(state_dir, "audit-index.md")

    uid = None
    if task_path:
        m = re.search(r"[0-9a-f]{8}", os.path.basename(task_path))
        uid = m.group(0) if m else None
    if not uid:
        uid = datetime.datetime.now().strftime("%Y%m%d")
        log.warning("archive audit: UUID not found in task path — using date fallback: %s", uid)

    output_dir = os.path.join(os.getcwd(), "ai", "workspace", "audit")
    os.makedirs(output_dir, exist_ok=True)

    archived = 0
    for src, suffix in [(index_src, "index"), (report_src, "report")]:
        if os.path.exists(src):
            dst = os.path.join(output_dir, f"audit-{uid}-{suffix}.md")
            shutil.copy2(src, dst)
            archived += 1
            log.info("archive audit: %s -> %s", src, dst)
            console.print(f"[green][engine] audit archived: {escape(dst)}[/green]")
        else:
            log.warning("archive audit: %s not found — skipping", src)

    if archived:
        console.print(
            f"[green][engine] {archived} audit artifact(s) archived to {escape(output_dir)}[/green]"
        )


def load_yaml(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def _substitute_project_root(config: dict) -> dict:
    """
    Substitute the literal string '{PROJECT_ROOT}' with PROJECT_ROOT in mcp_servers.

    Walks config['mcp_servers'] and for every server definition, replaces
    '{PROJECT_ROOT}' in the 'command' string and each string in the 'args' list.
    The 'env' dict values are also processed if they contain the placeholder.

    Args:
        config: The parsed config.yaml contents (modified in place)

    Returns:
        The same config dict (for chaining convenience)
    """
    mcp_servers = config.get("mcp_servers", {})
    placeholder = "{PROJECT_ROOT}"

    for server_name, server_def in mcp_servers.items():
        if not isinstance(server_def, dict):
            continue

        # Substitute in 'command'
        cmd = server_def.get("command")
        if isinstance(cmd, str) and placeholder in cmd:
            server_def["command"] = cmd.replace(placeholder, PROJECT_ROOT)

        # Substitute in 'args' list
        args = server_def.get("args")
        if isinstance(args, list):
            server_def["args"] = [
                arg.replace(placeholder, PROJECT_ROOT) if isinstance(arg, str) and placeholder in arg else arg
                for arg in args
            ]

        # Substitute in 'env' dict values
        env = server_def.get("env")
        if isinstance(env, dict):
            server_def["env"] = {
                k: v.replace(placeholder, PROJECT_ROOT) if isinstance(v, str) and placeholder in v else v
                for k, v in env.items()
            }

    return config


def read_state(state_dir: str, filename: str) -> str:
    path = os.path.join(state_dir, filename)
    return open(path).read().strip() if os.path.exists(path) else ""


def write_state(state_dir: str, filename: str, content: str) -> None:
    os.makedirs(state_dir, exist_ok=True)
    with open(os.path.join(state_dir, filename), "w") as f:
        f.write(content)


def reset_state(state_dir: str) -> int:
    """
    Remove all loop state files from state_dir.
    Log files (engine_*.LOG) and context-budget.md are preserved.
    Returns 0 unless an entry cannot be removed (change-82dbf16a iteration 5);
    reset is idempotent.

    change-f5c28a04 (2.3): an absent state directory previously returned 1.
    Reset is idempotent by intent — resetting nothing is the requested outcome
    already obtaining, not a failure. The non-zero code surfaced through
    engine-mcp's reset_engine as a spurious error on any project that had not yet run.
    """
    if not os.path.isdir(state_dir):
        console.print(f"[yellow][engine] reset: state directory not present: {state_dir}[/yellow]")
        console.print("[green][engine] reset: nothing to clear[/green]")
        return 0
    removed, failed = [], []
    for name in _RESET_FILES:
        path = os.path.join(state_dir, name)
        if os.path.lexists(path):  # change-82dbf16a iteration 5 (F4-01): symlinks and directories too
            (removed if _remove_state_path(path) else failed).append(name)
    if failed:
        console.print(f"[red][engine] reset: could not remove: {escape(', '.join(failed))}[/red]")
        return 1
    if removed:
        console.print(f"[green][engine] reset: removed {len(removed)} state file(s)[/green]")
        for name in removed:
            console.print(f"[dim]  {name}[/dim]")
    else:
        console.print("[yellow][engine] reset: state directory already clean[/yellow]")
    return 0


_LEGACY_LIVE_QUERY = object()


def resolve_context_window(model_name: str, config: dict,
                           live_query: Callable[[str], int | None] | None | object = _LEGACY_LIVE_QUERY,
                           ) -> int | None:
    """
    Resolve the model context window in tokens using a four-tier chain.

    Tier 1: config['context']['context_window'] if not null (explicit global override)
    Tier 2: Live query (oMLX admin endpoint for settings.max_context_window)
    Tier 3: config['context']['model_context_windows'][model_name] if present
    Tier 4: Return None (context window unknown)

    Args:
        model_name: The model id bound to the role being resolved (FR-04-05)
        config: The parsed config.yaml contents
        live_query: The role provider's live_context_window, or None to skip
            tier 2. Omitted: query the legacy omlx.base_url, as before.

    Returns:
        Context window size in tokens, or None if unresolved at every tier.
    """
    log = logging.getLogger("engine")
    ctx_cfg = config.get("context", {})
    tiers_tried = []

    # Tier 1: Explicit global override
    override = ctx_cfg.get("context_window")
    if override is not None:
        log.info("context window: %d (tier 1: config global override)", override)
        return int(override)
    tiers_tried.append("tier 1 (global override): null")

    # Tier 2: Live query (oMLX only)
    if live_query is _LEGACY_LIVE_QUERY:
        base_url = (config.get("omlx") or {}).get("base_url", "")
        live_query = (lambda m: _query_omlx_context_window(m, base_url)) if base_url else None
    if live_query is not None:
        live_ctx = live_query(model_name)
        if live_ctx is not None:
            log.info("context window: %d (tier 2: live oMLX admin query)", live_ctx)
            return live_ctx
        tiers_tried.append("tier 2 (live oMLX query): null or failed")
    else:
        tiers_tried.append("tier 2 (live query): not available for this provider")

    # Tier 3: Per-model override from config
    model_overrides = ctx_cfg.get("model_context_windows", {})
    if model_name in model_overrides:
        ctx = model_overrides[model_name]
        log.info("context window: %d (tier 3: config per-model override for '%s')", ctx, model_name)
        return int(ctx)
    tiers_tried.append(f"tier 3 (per-model override): no entry for '{model_name}'")

    # Tier 4: Unresolved
    log.warning(
        "context window: unresolved for '%s' — %s",
        model_name,
        "; ".join(tiers_tried),
    )
    return None


def estimate_tokens(messages: list[dict], tools: list[dict] | None = None) -> int:
    """
    Approximate token count for a list of chat messages plus optional tool schema.

    F8: Includes both message content and serialized tool-schema length.
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

    # F8: Include serialized tool schema in token estimate
    if tools:
        total += len(json.dumps(tools)) // 4

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
    Write context-budget.md to state_dir for planner consumption.
    This file informs the planner of available context headroom
    before authoring the next tactical_brief or T03 prompt.
    """
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if context_window is None:
        report = (
            f"# Engine Context Budget Report\n\n"
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

    report = f"""# Engine Context Budget Report

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

## Guidance for Planner
When authoring the next tactical_brief or T03 prompt:

- Current initial load is {initial_pct:.1f}% of context window
- Each loop phase iteration accumulates ~{est_per_iter} tokens
- Recommended tactical_brief size: ~200-400 tokens (hard ceiling: 1,000 tokens)
- Avoid embedding large design documents or code blocks in the brief
- Context pressure symptoms: duplicate tool calls, repeated reads, verbose responses
- If symptoms appear, reduce brief size and restart with --mode reset
"""
    write_state(state_dir, "context-budget.md", report)


def _remove_state_path(path: str) -> bool:
    """
    change-82dbf16a iteration 5 (audit F4-01): remove a state entry whatever
    its type: a file or symlink (dangling or not) is unlinked, a directory is
    removed with its content (symlinks inside are not followed). True when the
    name no longer exists.
    """
    try:
        if os.path.isdir(path) and not os.path.islink(path):
            shutil.rmtree(path)
        elif os.path.lexists(path):
            os.unlink(path)
    except OSError:
        pass
    return not os.path.lexists(path)


def clear_state(state_dir: str, *filenames: str) -> list[str]:
    """Remove the named state entries; returns the names that could not be removed."""
    return [name for name in filenames
            if not _remove_state_path(os.path.join(state_dir, name))]


def archive_prior_logs(state_dir: str, archive_dir: str | None) -> int:
    """
    change-f5c28a04 (3.1): copy run logs out of state_dir before a new run.

    Run logs are written into state_dir, which is transient by design: it is
    gitignored downstream, cleared by the smoke harness, and re-propagated over.
    Logs cited as evidence in one session were therefore no longer present in
    the next. The .gitignore '*.log' pattern additionally matches 'engine_*.LOG' on
    a case-insensitive filesystem, so nothing recovers them from version
    control either.

    Opt-in: when archive_dir is null (the default) this is a no-op and behaviour
    is unchanged, so downstream projects are unaffected until they configure it.
    Existing archived files are never overwritten — the timestamped filenames
    are already unique, and a collision would indicate a name reused rather than
    a log superseded.

    Returns the number of files copied.
    """
    if not archive_dir or not os.path.isdir(state_dir):
        return 0

    os.makedirs(archive_dir, exist_ok=True)
    copied = 0
    for name in sorted(os.listdir(state_dir)):
        if not name.lower().endswith(".log"):
            continue
        src = os.path.join(state_dir, name)
        dst = os.path.join(archive_dir, name)
        if not os.path.isfile(src) or os.path.exists(dst):
            continue
        try:
            shutil.copy2(src, dst)
            copied += 1
        except Exception as exc:
            console.print(f"[yellow][engine] log archive: could not copy {escape(name)}: {escape(str(exc))}[/yellow]")

    if copied:
        console.print(f"[dim][engine] log archive: {copied} prior log(s) -> {escape(archive_dir)}[/dim]")
    return copied


def setup_logging(state_dir: str) -> logging.Logger:
    os.makedirs(state_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    log_path = os.path.join(state_dir, f"engine_{timestamp}.LOG")
    logger = logging.getLogger("engine")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False  # F19: prevent duplicate console output via root logger's default handler
    if not logger.handlers:
        fh = logging.FileHandler(log_path)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(fh)
    return logger


def extract_target_profile(raw: str, log: logging.Logger) -> str | None:
    """
    Extract target_profile from a T03 prompt document's YAML block.

    Returns the target_profile value if found, or None if absent.
    Used by strict_tactical_brief mode to determine if brief enforcement applies.
    """
    blocks = re.findall(r"```yaml\n(.*?)```", raw, re.DOTALL)
    for block in blocks:
        try:
            doc = yaml.safe_load(block)
            if doc:
                # Check top-level or nested under prompt_info
                profile = doc.get("target_profile") or (doc.get("prompt_info") or {}).get("target_profile")
                if profile:
                    log.debug("extract_target_profile: found '%s'", profile)
                    return str(profile)
        except Exception:
            pass
    log.debug("extract_target_profile: no target_profile found")
    return None


def extract_tactical_brief(raw: str, log: logging.Logger) -> str:
    """
    Extract tactical_brief from a T03 prompt document.

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
    <think>...</think> tags (Mistral/Devstral), then Cohere's
    <|START_THINKING|>...<|END_THINKING|> blocks (North-Mini-Code-1.0 / cohere2_moe).
    Returns (reasoning, content_without_reasoning_tags).
    """
    reasoning = getattr(message, "reasoning_content", None) or ""
    if not reasoning and content:
        think_match = re.search(r"<think>(.*?)</think>", content, re.DOTALL)
        if think_match:
            reasoning = think_match.group(1).strip()
            content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
            log.debug("extracted <think> block (%d chars)", len(reasoning))
        else:
            # F23: Cohere thinking-block (North-Mini-Code-1.0 / cohere2_moe via oMLX)
            cohere_match = re.search(r"<\|START_THINKING\|>(.*?)<\|END_THINKING\|>", content, re.DOTALL)
            if cohere_match:
                reasoning = cohere_match.group(1).strip()
                content = re.sub(r"<\|START_THINKING\|>.*?<\|END_THINKING\|>", "", content, flags=re.DOTALL).strip()
                log.debug("extracted <|START_THINKING|> block (%d chars)", len(reasoning))
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


def _dispatch_refusal(name: str, offered: set[str], is_worker_phase: bool) -> str | None:
    """
    change-82dbf16a (H-03): a tool call is dispatched only when the tool was
    offered to this phase; a review phase never dispatches a write tool.
    """
    if name not in offered:
        return f"tool '{name}' is not available in this phase"
    if not is_worker_phase and is_write_tool(name):
        return f"tool '{name}' writes; the review phase is read-only"
    return None


async def run_phase(
    client: Any,
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
    project_root: str = "",
    phase_duration_seconds: float | None = None,
    max_completion_tokens: int | None = None,
    max_tool_result_chars: int | None = None,
    write_scope: "S.WriteScope | None" = None,
) -> tuple[int, str, set[str]]:
    """
    Single phase (worker or reviewer): inject tools, send completions,
    dispatch tool calls, loop until no tool calls remain.
    Returns (exit_code, final_message, read_paths) where:
      - exit_code: 0 on success, 1 on failure
      - final_message: the terminal assistant response text (empty on failure or tool exit)
      - read_paths: set of abspath-normalized file paths read via read/read_file/read_text_file
                    (populated for review phase; empty for worker phase)
    """
    provider = as_provider(client)  # change-53c6f252: raw OpenAI-style clients are wrapped
    is_worker_phase = "REVIEW" not in phase_label.upper()
    # F5: review phase gets read-only tool subset; worker gets full toolset
    tools = mcp.get_openai_tools(readonly=not is_worker_phase)
    # change-82dbf16a (H-03): only offered tools are dispatched; (H-01) the
    # worker never writes engine signal files.
    _offered = {t["function"]["name"] for t in tools}
    _protected = S.signal_files(state_dir) if is_worker_phase else frozenset()

    # Build real tool name list and inject into recipe system prompt
    tool_list = format_tool_signatures(tools)
    system_prompt = recipe.get("instructions", "").replace("{{TOOLS}}", tool_list)

    # Static iteration budget note (replaces F25 per-iteration mutation for oMLX prefix cache compatibility)
    system_prompt += f"\n\n[ITERATION BUDGET] This phase has a budget of {max_iterations} iteration(s)."

    # F24: for audit runs, inject the next unchecked item directly into the
    # work-phase task so the model doesn't have to re-derive it each iteration
    # by reading and parsing the full audit-index.md / audit-uml.md.
    if is_worker_phase:
        _audit_index_path = os.path.join(state_dir, "audit-index.md")
        if os.path.exists(_audit_index_path):
            _next_item = next(
                (text for checked, text in _parse_audit_items(_audit_index_path) if not checked),
                None,
            )
            if _next_item:
                task = f"[NEXT AUDIT ITEM]\n{_next_item}\n[END NEXT AUDIT ITEM]\n\n" + task

    messages: list[dict] = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": task},
    ]

    mcp_error_count = 0
    _read_counts: dict[str, int] = {}  # P3: duplicate read tracking
    _written_paths: set[str] = set()  # change-a2f9c4d1: successful write targets
    # change-f5c28a04 (F1): whether THIS phase produced work-summary.txt, by the
    # worker's own hand. Tracked explicitly because file existence cannot
    # distinguish a manifest written this cycle from one left by a prior cycle.
    _manifest_written: bool = False
    _failed_call_sigs: dict[str, int] = {}  # F27: repeated identical failed call tracking

    label = f"{phase_label} " if phase_label else ""
    console.rule(f"[blue]{label or 'engine'} — {escape(model)}[/blue]", style="blue")
    console.print(f"[blue][engine] tools:  {len(tools)}[/blue]")
    console.print(f"[blue][engine] task:   {escape(task[:80])}{'...' if len(task) > 80 else ''}[/blue]")
    log.info("phase start phase=%s model=%s tools=%d task=%s", phase_label or "?", model, len(tools), task)

    _phase_start = time.monotonic()  # F28: phase wall-clock cap

    for iteration in range(1, max_iterations + 1):
        iter_label = f"{phase_label}  " if phase_label else ""
        console.rule(f"[blue dim]{iter_label}iteration {iteration}/{max_iterations}[/blue dim]", style="blue dim")
        log.debug("iteration %d/%d phase=%s", iteration, max_iterations, phase_label or "?")

        # F28: phase wall-clock cap (Option A, soft) — bounds a single item's
        # cost so a stuck item cannot consume the whole run's --duration
        # budget. Ends the phase as if complete; the item stays unchecked,
        # the reviewer issues REVISE, and the next loop iteration retries it
        # under a fresh cap rather than aborting the entire run.
        if phase_duration_seconds is not None and (time.monotonic() - _phase_start) > phase_duration_seconds:
            console.print(f"\n[yellow][engine] phase wall-clock cap ({phase_duration_seconds/60:.0f} min) reached[/yellow]")
            log.warning("phase wall-clock cap (%.0fs) reached at iteration %d", phase_duration_seconds, iteration)
            # change-a2f9c4d1: persist a deliverable manifest before returning
            if is_worker_phase:
                _synthesize_work_summary(state_dir, _written_paths, "wall-clock cap reached", log)
            return 0, "", set(_read_counts.keys()) if not is_worker_phase else set()

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
                return 1, "", set()
            elif status == "warn":
                console.print(_ctx_bar(estimated, context_window, status))
                log.warning("context budget warn: %d / %d tokens (%.1f%%)",
                            estimated, context_window, fraction * 100)
            else:
                console.print(_ctx_bar(estimated, context_window, status))
                log.debug("context budget ok: %d / %d tokens (%.1f%%)",
                          estimated, context_window, fraction * 100)

        # F14: Use bounded retry with backoff for transient endpoint errors
        try:
            completion = await _completion_with_retry(
                provider, model, messages, tools, log, state_dir,
                max_completion_tokens=max_completion_tokens,
            )
        except RuntimeError:
            # Persistent failure — BLOCKED.md already written
            return 1, "", set()

        content = completion.text or ""
        log.debug("iteration %d model response:\n%s", iteration, content)

        # Extract and display reasoning if present
        reasoning, content = extract_reasoning(completion, content, log)
        if reasoning:
            log.debug("model reasoning:\n%s", reasoning)
            console.print(Panel(escape(reasoning), title="[dim cyan]think[/dim cyan]", border_style="dim cyan", expand=False))
        else:
            # F20: surface untagged model commentary that precedes a tool call.
            # Some models (e.g. Devstral) interleave narrative text with tool
            # calls instead of using a dedicated reasoning_content/<think> channel.
            # Without this, that text is logged but never reaches the console.
            # Strip any plain-text [TOOL_CALLS] marker — that syntax is shown
            # separately via the 'call ->' line once parsed below.
            _narration = content.split("[TOOL_CALLS]")[0].strip()
            if _narration and (completion.tool_calls or "[TOOL_CALLS]" in content):
                log.debug("untagged narration (%d chars)", len(_narration))
                console.print(Panel(escape(_narration), title="[dim magenta]narration[/dim magenta]", border_style="dim magenta", expand=False))

        # change-53c6f252: native and plain-text tool calls are normalised by the provider
        tool_calls: list[dict] = [
            {"id": tc.id, "name": tc.name, "arguments": tc.arguments}
            for tc in completion.tool_calls
        ]

        # F3: Apply tool call cap BEFORE building assistant message to avoid orphaned IDs.
        # The assistant message must only reference tool_calls that will have matching results.
        if tool_calls and len(tool_calls) > max_tool_calls_per_iter:
            log.warning(
                "iteration %d: %d tool calls exceeds cap %d — truncating",
                iteration, len(tool_calls), max_tool_calls_per_iter,
            )
            console.print(f"[yellow][engine] tool call cap ({max_tool_calls_per_iter}) exceeded "
                          f"({len(tool_calls)} calls) — truncating[/yellow]")
            tool_calls = tool_calls[:max_tool_calls_per_iter]

        # Build assistant message with (possibly truncated) tool_calls
        if tool_calls:
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

        if not tool_calls:
            # F7: Guard against malformed final response using structured signals.
            # Check for unparsed tool call markers (model tried to emit calls but parser failed).
            # Do NOT use substring scans for error patterns — a summary may legitimately
            # contain such text without indicating a malformed response.
            _has_unparsed_tool_marker = "[TOOL_CALLS]" in content
            if _has_unparsed_tool_marker:
                blocked_msg = (
                    "# BLOCKED\n\n"
                    "Worker final response contains unparsed tool call markers.\n\n"
                    f"Content preview:\n\n    {content[:400]}\n"
                )
                write_state(state_dir, "BLOCKED.md", blocked_msg)
                log.error("BLOCKED: worker final response contains unparsed tool markers")
                console.print("[red][engine] BLOCKED: worker final response malformed[/red]")
                return 1, "", set()
            console.print(Panel(escape(content), title="[green]response[/green]", border_style="green"))
            # F13: only worker phase writes work-summary.txt; review phase preserves it
            if is_worker_phase:
                write_state(state_dir, "work-summary.txt", content)
                _manifest_written = True
                # change-d1f4a83b (N1): a final response is not necessarily a
                # manifest. Append the observed deliverables when it names none,
                # so the gates receive this cycle's actual output.
                _append_observed_manifest(state_dir, _written_paths, content, log)
            # Return normalized read paths for review phase (empty for worker)
            _read_paths = {os.path.abspath(p) for p in _read_counts.keys()} if not is_worker_phase else set()
            return 0, content, _read_paths

        # Dispatch tool calls and inject results
        for tc in tool_calls:
            console.print(f"[yellow]  call →[/yellow]  [bold]{escape(tc['name'])}[/bold][dim]({escape(json.dumps(tc['arguments']))})[/dim]")
            log.debug("tool call: %s args=%s", tc["name"], json.dumps(tc["arguments"]))

            # change-82dbf16a (H-03): refuse tools not offered to this phase and
            # every write tool in a review phase, before any other check.
            _refusal = _dispatch_refusal(tc["name"], _offered, is_worker_phase)
            if _refusal:
                log.warning("tool refused tool=%s phase=%s reason=%s",
                            tc["name"], phase_label or "-", _refusal)
            # F4 / change-bdc6820f: pre-dispatch write scope validation (FR-05-01, FR-05-04)
            _violation = (S.check(tc["name"], tc["arguments"], project_root, write_scope, _protected)
                          if project_root and not _refusal else None)
            _scope_err = _violation.message if _violation else None
            if _violation:
                log.warning("write rejected tool=%s path=%s reason=%s",
                            tc["name"], _violation.path, _violation.reason)
            # F21: Pre-dispatch audit-report.md append-only validation
            _report_err = (_validate_audit_report_write(tc["name"], tc["arguments"], state_dir)
                           if not _refusal else None)
            if _refusal:
                console.print(f"[red][engine] tool refused: {escape(_refusal[:200])}[/red]")
                result = f"Error: {_refusal}"
                _scope_err = _refusal
            elif _scope_err:
                log.warning("scope violation: %s", _scope_err)
                console.print(f"[red][engine] scope violation: {escape(_scope_err[:200])}[/red]")
                result = f"Error: {_scope_err}"
            elif _report_err:
                log.warning("audit-report.md overwrite blocked: %s", _report_err)
                console.print(f"[red][engine] audit-report.md overwrite blocked[/red]")
                result = _report_err
            else:
                result = await mcp.call_tool(tc["name"], tc["arguments"])

            # Truncate tool result if max_tool_result_chars is configured
            if max_tool_result_chars is not None and len(result) > max_tool_result_chars:
                _original_len = len(result)
                result = _truncate_tool_result(result, max_tool_result_chars)
                log.debug("tool result truncated: %d -> %d chars", _original_len, len(result))

            log.debug("tool result: %s", result)
            preview = result[:200] + ("..." if len(result) > 200 else "")
            console.print(f"[cyan]  result ←[/cyan]  [dim]{escape(preview)}[/dim]")
            # P3: duplicate read tracking
            if tc["name"] in ("read", "read_file", "read_text_file"):
                # change-c37198be (D3): filesystem-mcp 2.x `read` also takes paths[].
                _rpaths = [tc["arguments"].get("path", "")]
                _rpaths += [p for p in tc["arguments"].get("paths") or [] if isinstance(p, str)]
                for _path in _rpaths:
                    if not _path:
                        continue
                    _read_counts[_path] = _read_counts.get(_path, 0) + 1
                    if _read_counts[_path] > 1:
                        log.warning("duplicate read (count=%d): %s",
                                    _read_counts[_path], _path)

            # change-a2f9c4d1: record successful write targets for work-summary
            # synthesis. Only calls that raised no scope error, no audit-report
            # error and no MCP error are treated as writes that actually landed.
            if (is_write_tool(tc["name"])
                    and not _scope_err and not _report_err
                    and not _is_mcp_error(result)):
                # change-f5c28a04 (F3): for move/rename the deliverable ends up
                # at the destination, so that is what the manifest must record.
                # The source-first ordering below was inherited from
                # _validate_write_scope, where the source is the correct subject
                # for scope enforcement but the wrong one for manifest
                # construction: a file created by move_file was recorded at its
                # pre-move path, failed the isfile filter at synthesis, and was
                # dropped from the manifest entirely.
                # change-c37198be (D3): _written_targets also reads the
                # batched files/moves lists of filesystem-mcp 2.x.
                for _wpath in _written_targets(tc["name"], tc["arguments"]):
                    _wabs = os.path.abspath(_wpath)
                    _written_paths.add(_wabs)
                    # F1: record that the worker supplied its own manifest.
                    if _wabs == os.path.abspath(os.path.join(state_dir, "work-summary.txt")):
                        _manifest_written = True

            # F27: repeated identical failed call tracking. Diagnostic calls
            # (stat/grep/read) commonly intervene between retries, defeating a
            # simple consecutive-call counter, so failures are counted per
            # unique (tool, arguments) signature across the whole phase.
            if _scope_err or _report_err or _is_mcp_error(result):
                _call_sig = f"{tc['name']}:{json.dumps(tc['arguments'], sort_keys=True)}"
                _failed_call_sigs[_call_sig] = _failed_call_sigs.get(_call_sig, 0) + 1
                _fail_n = _failed_call_sigs[_call_sig]
                if _fail_n == 2:
                    log.warning("repeated identical failed call (count=%d): %s",
                                _fail_n, _call_sig[:150])
                    result += (
                        "\n\nYou have called this exact tool with identical "
                        "arguments before and it failed. Do not repeat it — "
                        "use a different tool or approach."
                    )
                elif _fail_n >= 4:
                    blocked_msg = (
                        "# BLOCKED\n\n"
                        f"Repeated identical failed call: {_fail_n} attempts.\n\n"
                        f"Call: {_call_sig[:300]}\n\n"
                        f"Last result: {result[:300]}\n"
                    )
                    write_state(state_dir, "BLOCKED.md", blocked_msg)
                    log.error("BLOCKED: repeated identical failed call (%d attempts)", _fail_n)
                    console.print(
                        f"[red][engine] BLOCKED: repeated identical failed call "
                        f"({_fail_n} attempts)[/red]"
                    )
                    return 1, "", set()

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
                    f"[yellow][engine] edit pattern mismatch: {escape(tc['name'])}: "
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
                        [sys.executable, "-m", "py_compile", _ep_path],
                        capture_output=True,
                        text=True,
                    )
                    if _ep_proc.returncode != 0:
                        _ep_msg += (
                            f"\n\nAdditional: syntax error detected:\n\n"
                            f"{_ep_proc.stderr.strip()}"
                        )
                _corrective = _ep_msg
            # F26: audit-report.md append-guard-specific corrective. _report_err
            # messages start with "Error:" and would otherwise be misrouted into
            # the generic MCP-error branch below, which tells the model to
            # "review required parameters" — wrong advice for an overwrite
            # rejection, and observed to reinforce blind write-retries instead
            # of steering the model toward edit/edit_file as F21 intends.
            elif _report_err:
                _corrective = (
                    "\n\nDo not retry write/write_file/create_file on this file. "
                    "Call edit or edit_file instead: set old_text to the exact "
                    "final line(s) currently in the file (read the tail first "
                    "if unsure), and new_text to those same line(s) followed by "
                    "your new entry."
                )
            elif _is_mcp_error(result):
                mcp_error_count += 1
                console.print(
                    f"[red][engine] MCP error "
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
                        f"# BLOCKED\n\n"
                        f"MCP validation error threshold reached "
                        f"({mcp_error_count} consecutive errors).\n\n"
                        f"Last error:\n\n    {result}\n\n"
                        f"Tool: {tc['name']}\n"
                    )
                    write_state(state_dir, "BLOCKED.md", blocked_msg)
                    log.error(
                        "BLOCKED: MCP error threshold %d reached", mcp_error_threshold
                    )
                    console.print(
                        f"[red][engine] BLOCKED: MCP error threshold "
                        f"({mcp_error_threshold}) reached[/red]"
                    )
                    return 1, "", set()
            else:
                mcp_error_count = 0
                # P4: post-write Python syntax check
                # change-c37198be (D3): every file a write call leaves, incl. 2.x batches.
                _py_paths = (_written_targets(tc["name"], tc["arguments"])
                             if is_write_tool(tc["name"]) else [])
                for _py_path in _py_paths:
                    if _py_path.endswith(".py") and os.path.isfile(_py_path):
                        proc = subprocess.run(
                            [sys.executable, "-m", "py_compile", _py_path],
                            capture_output=True,
                            text=True,
                        )
                        if proc.returncode != 0:
                            err = proc.stderr.strip()
                            log.warning("syntax error in %s: %s", _py_path, err)
                            console.print(
                                f"[red][engine] syntax error: {escape(_py_path)}: "
                                f"{escape(err[:200])}[/red]"
                            )
                            _corrective += (
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
            console.print("[green][engine] work-complete detected[/green]")
            # change-a2f9c4d1: persist a deliverable manifest before returning
            if is_worker_phase:
                _synthesize_work_summary(state_dir, _written_paths, "work-complete signal", log)
            _read_paths = {os.path.abspath(p) for p in _read_counts.keys()} if not is_worker_phase else set()
            return 0, "", _read_paths

    console.print(f"\n[red][engine] max iterations ({max_iterations}) reached[/red]")
    log.warning("max iterations %d reached", max_iterations)
    _read_paths = {os.path.abspath(p) for p in _read_counts.keys()} if not is_worker_phase else set()
    # change-a2f9c4d1: iteration exhaustion is a budget boundary, not a failure.
    # Synthesise a manifest and let the reviewer adjudicate when the phase
    # produced deliverables; retain rc=1 only when it produced nothing.
    #
    # change-f5c28a04 (F1): the decision is made on THIS phase's own outcome —
    # whether synthesis wrote a manifest now, or the worker wrote one during
    # this phase — not on whether work-summary.txt exists on disk. The former
    # test cannot distinguish a manifest produced this cycle from one left
    # behind by a prior cycle, so a worker that wrote nothing in cycle 2+ still
    # returned rc=0 and presented the previous cycle's deliverables to the
    # gates.
    if is_worker_phase:
        _synthesized = _synthesize_work_summary(
            state_dir, _written_paths, "iteration budget exhausted", log
        )
        if _synthesized or _manifest_written:
            log.info("exhausted phase has a deliverable manifest — proceeding to review")
            return 0, "", _read_paths
        log.warning("exhausted phase produced no deliverable manifest — rc=1")
    return 1, "", _read_paths


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
                    [sys.executable, "-m", "py_compile", path],
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
            # F9: Guard grep availability before use
            if not shutil.which("grep"):
                lines.append(f"  [{i}] UNCHECKED  {criterion} (grep not available)")
                unchecked += 1
            else:
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
        f"[dim][engine] pre-flight: {len(criteria)} criteria — "
        f"{satisfied} satisfied, {remaining} remaining, {unchecked} unchecked[/dim]"
    )
    return summary


def _run_syntax_gate(state_dir: str, log: logging.Logger) -> str:
    """
    F6: Built-in syntax gate (gates.syntax_check). Returns a [SYNTAX GATE]
    block for the reviewer task, or '' when no .py deliverable exists.
    """
    block, count = G.syntax_check(state_dir, log)
    if block:
        status = G.gate_status(block)
        style = "dim" if status == "PASS" else "yellow"
        console.print(f"[{style}][engine] syntax gate: {status} ({count} files)[/{style}]")
    return block


def _run_pytest_gate(state_dir: str, log: logging.Logger, project_root: str,
                     spec: dict | None = None) -> str:
    """
    F6b: pytest command gate on deliverable-derived targets (gates.pytest_targets).

    spec: {command, python, timeout_seconds} from the manifest and ai/config.yaml
    (change-e58fd295); omitted, the historical command runs with this
    interpreter. Returns a [TEST GATE] block, or '' when no target resolves.
    PASS: exit 0; FAIL: tests failed; UNCHECKED: pytest could not run. In
    run_loop FAIL overrides SHIP and UNCHECKED ends the run BLOCKED
    (change-82dbf16a).
    """
    deliverables = _extract_deliverables(state_dir, log)
    if not deliverables:
        log.debug("pytest gate: no deliverables — gate is no-op")
        return ""
    targets = G.pytest_targets(deliverables, project_root)
    if not targets:
        log.debug("pytest gate: no test-relevant targets resolved — gate is no-op")
        return ""
    log.info("pytest gate: running pytest on %d target(s): %s", len(targets), targets)
    block = G.run_command_gate(G.PYTEST_GATE, spec or {}, targets, project_root, log)
    status = G.gate_status(block)
    if status == "PASS":
        log.info("pytest gate: %d target(s), status=%s", len(targets), status)
        console.print(f"[dim][engine] pytest gate: {status} ({len(targets)} targets)[/dim]")
    else:
        log.warning("pytest gate: %d target(s), status=%s", len(targets), status)
        console.print(f"[yellow][engine] pytest gate: {status} ({len(targets)} targets)[/yellow]")
    return block


def _run_command_gate(name: str, spec: dict, state_dir: str, log: logging.Logger,
                      project_root: str) -> str:
    """
    A declared command gate other than pytest (change-e58fd295). {targets}
    expands to the deliverables of this cycle.
    """
    if not spec.get("command"):
        log.warning("%s gate: no command configured — gate is no-op", name)
        return ""
    targets = sorted(_extract_deliverables(state_dir, log))
    block = G.run_command_gate(name, spec, targets, project_root, log)
    status = G.gate_status(block)
    style = "dim" if status == "PASS" else "yellow"
    console.print(f"[{style}][engine] {escape(name)} gate: {status}[/{style}]")
    return block


def _log_gate(log: logging.Logger, name: str, gate_type: str, result: str) -> None:
    """FR-03-06: one line per gate per iteration."""
    log.info("gate=%s type=%s result=%s", name, gate_type, result)


_DEFAULT_LOOP_GATES = ("syntax", "pytest", "reviewer")


def _parse_audit_items(index_path: str) -> list[tuple[bool, str]]:
    """
    F17: Shared parser for audit-index.md items.

    Returns a list of (checked, item_text) tuples for all audit items.
    An item is any line matching "- [ ]" or "- [x]" (case-insensitive x).
    Returns empty list if file doesn't exist.
    """
    if not os.path.exists(index_path):
        return []

    items = []
    with open(index_path) as f:
        for line in f:
            stripped = line.strip()
            # Match "- [ ]" (unchecked) or "- [x]"/"- [X]" (checked)
            if stripped.startswith("- [ ]"):
                items.append((False, stripped))
            elif stripped.startswith("- [x]") or stripped.startswith("- [X]"):
                items.append((True, stripped))
    return items


def _snapshot_audit_index(state_dir: str, log: logging.Logger) -> int | None:
    """
    Count total items in audit-index.md at loop start.
    Returns the count as the scope snapshot, or None if the file is absent.
    Non-audit runs return None — all scope checks become no-ops.
    """
    index_path = os.path.join(state_dir, "audit-index.md")
    items = _parse_audit_items(index_path)
    if not items:
        return None
    count = len(items)
    log.info("audit scope snapshot: %d items", count)
    return count


def _check_audit_scope(
    state_dir: str, original_count: int | None, log: logging.Logger
) -> str | None:
    """
    Detect unauthorised modifications to audit-index.md item count.
    Compares current total against snapshot taken at loop start.
    Returns an error string if count changed, None if intact or non-audit run.
    """
    if original_count is None:
        return None
    index_path = os.path.join(state_dir, "audit-index.md")
    items = _parse_audit_items(index_path)
    if not items:
        return None
    current = len(items)
    if current == original_count:
        return None
    delta = current - original_count
    verb = "added" if delta > 0 else "removed"
    return (
        f"Scope violation: audit-index.md item count changed from {original_count} "
        f"to {current} ({abs(delta)} item(s) {verb}). "
        f"Do not add or remove items from audit-index.md. "
        f"Only change [ ] to [x]. Restore the original item list and continue."
    )


def _count_unchecked_audit_items(state_dir: str, log: logging.Logger) -> int:
    """
    Count unchecked [ ] items in audit-index.md.
    Returns 0 if the file is absent (non-audit runs unaffected).
    """
    index_path = os.path.join(state_dir, "audit-index.md")
    items = _parse_audit_items(index_path)
    count = sum(1 for checked, _ in items if not checked)
    log.debug("audit SHIP gate: %d unchecked items", count)
    return count


def _extract_deliverables(state_dir: str, log: logging.Logger) -> set[str]:
    """
    Extract file paths from work-summary.txt that exist on disk.

    Returns a set of abspath-normalized paths. Used by the read-evidence SHIP
    gate to validate that the reviewer inspected each deliverable.

    Extraction regex matches path-like tokens (with extensions) in various
    formats: bare paths, quoted paths, backtick-fenced paths.
    """
    summary_path = os.path.join(state_dir, "work-summary.txt")
    if not os.path.exists(summary_path):
        log.debug("_extract_deliverables: work-summary.txt absent")
        return set()

    summary_content = open(summary_path).read()

    # Extract file paths: match patterns like path/to/file.ext, "path/to/file.ext"
    # Similar pattern to _run_syntax_gate but for all file types, not just .py
    path_pattern = r'["\'\`]?([\w./\-]+\.\w+)["\'\`]?'
    candidates = re.findall(path_pattern, summary_content)

    # Deduplicate, normalize, and filter to existing files
    seen: set[str] = set()
    deliverables: set[str] = set()
    for p in candidates:
        if p in seen:
            continue
        seen.add(p)
        if os.path.exists(p):
            deliverables.add(os.path.abspath(p))

    log.debug("_extract_deliverables: %d files from work-summary.txt", len(deliverables))
    return deliverables


def _deliverables_block_for(state_dir: str, log: logging.Logger,
                            declared: "set[str] | frozenset[str]" = frozenset()) -> str:
    """
    [DELIVERABLES] block listing this cycle's deliverables as absolute paths:
    those the worker reported, merged with the prompt's declared deliverable
    files that exist (change-82dbf16a, L-13).
    """
    deliverables = sorted(_extract_deliverables(state_dir, log)
                          | {p for p in declared if os.path.isfile(p)})
    if not deliverables:
        return ""
    lines = "\n".join(f"  - {p}" for p in deliverables)
    return ("[DELIVERABLES]\n"
            "The worker reported these deliverables. Paths are absolute; read each at this path.\n"
            f"{lines}\n"
            "[END DELIVERABLES]\n")


async def run_loop(
    client: Any,
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
    deadline: float | None = None,
    project_root: str = "",
    stall_threshold: int = _DEFAULT_STALL_THRESHOLD,
    phase_duration_seconds: float | None = None,
    max_completion_tokens: int | None = None,
    max_tool_result_chars: int | None = None,
    reviewer_client: Any = None,
    reviewer_context_window: int | None = None,
    gates: list[str] | None = None,
    gate_specs: dict[str, dict] | None = None,
    write_scope: "S.WriteScope | None" = None,
    gate_outcomes: dict[str, str] | None = None,
) -> int:
    """
    Full loop: worker/reviewer cycle until SHIP, max_iterations, or deadline.

    client and context_window serve the worker; reviewer_client and
    reviewer_context_window serve the reviewer and default to the worker's
    (change-53c6f252, FR-04-05). gates lists the loop stage's gates and
    gate_specs the command gate specifications from the manifest and
    ai/config.yaml; omitted, the historical syntax, pytest and reviewer gates
    run (change-e58fd295). gate_outcomes, when given, receives the last
    cycle's status per gate (PASS, FAIL, UNCHECKED or SKIPPED; change-82dbf16a).
    """
    gate_list = list(gates) if gates else list(_DEFAULT_LOOP_GATES)
    gate_specs = gate_specs or {}
    if reviewer_client is None:
        reviewer_client = client
    if reviewer_context_window is None:
        reviewer_context_window = context_window
    ctx_line = f"  context:  {context_window:,} tokens\n" if context_window else ""
    console.print(Panel(
        f"  worker:   {escape(worker_model)}\n"
        f"  reviewer: {escape(reviewer_model)}\n"
        f"{ctx_line}"
        f"  task:     {escape(task[:60])}{'...' if len(task) > 60 else ''}",
        title="[bold blue]engine loop[/bold blue]",
        border_style="blue",
    ))
    log.info("loop start worker=%s reviewer=%s task=%s", worker_model, reviewer_model, task)

    _not_cleared = clear_state(state_dir,
                "review-result.txt", "review-feedback.txt",
                "work-complete.txt", "work-summary.txt", ".complete", ".timeout",
                "awaiting-approval.md")
    if _not_cleared:  # change-82dbf16a iteration 5 (F4-01)
        write_state(state_dir, "BLOCKED.md",
                    "# BLOCKED\n\nState files could not be removed at loop start: "
                    f"{', '.join(_not_cleared)}. Remove them by hand.\n")
        log.error("BLOCKED: state files could not be removed: %s", ", ".join(_not_cleared))
        console.print(f"[red][engine] BLOCKED: state files could not be removed: "
                      f"{escape(', '.join(_not_cleared))}[/red]")
        return 1

    # Audit scope snapshot: record original item count for scope lock enforcement.
    _audit_original_count = _snapshot_audit_index(state_dir, log)

    # F12: Stall detection — track consecutive identical feedback
    _last_feedback_hash = ""
    _stall_count = 0

    # Pre-flight success criteria check (opt-in)
    if preflight_check:
        preflight_summary = run_preflight_check(task, log)
        if preflight_summary:
            task = preflight_summary + "\n\n" + task

    i = 0
    _extra = 0
    while True:
        i += 1
        # F10: Duration-limit exit returns distinct code and writes .timeout
        if deadline and time.monotonic() > deadline:
            console.print("[yellow][engine] duration limit reached — exiting[/yellow]")
            log.info("duration limit reached at loop iteration %d", i)
            write_state(state_dir, ".timeout", f"TIMEOUT: iteration {i}")
            return 2  # Distinct non-zero code for timeout
        if i > max_iterations + _extra:
            console.print(f"\n[red]✗ max iterations ({max_iterations + _extra}) reached without SHIP[/red]")
            log.warning("max iterations %d reached without SHIP", max_iterations + _extra)
            # change-d1f4a83b (N4): only prompt when there is a human at the
            # other end. Launched through engine-mcp the orchestrator is detached
            # and its stdin is neither a terminal nor closed, so input() blocks
            # indefinitely: the run never reaches "engine end", the process stays
            # alive holding its MCP servers, and engine_status reports pid_alive
            # forever. Live-observed, run 8c2040d3. Non-interactive runs take
            # the documented default, which is to decline.
            if not sys.stdin.isatty():
                log.info("max iterations reached, stdin is not a terminal — declining to continue")
                console.print(
                    f"[yellow][engine] Continue for another {max_iterations} iteration(s)? "
                    f"[y/N]: N (non-interactive)[/yellow]"
                )
                answer = "n"
            else:
                try:
                    console.print(f"[yellow][engine] Continue for another {max_iterations} iteration(s)? [y/N]: [/yellow]", end="")
                    answer = input().strip().lower()
                except (EOFError, KeyboardInterrupt):
                    answer = "n"
            if answer != "y":
                return 1
            _extra += max_iterations
            log.info("user elected to continue: %d total additional iterations", _extra)
            # F15: Do NOT continue here — fall through to run iteration i,
            # which is the first of the promised additional cycles.
        console.rule(f"[bold blue]loop iteration {i} / {max_iterations + _extra}[/bold blue]", style="blue")

        write_state(state_dir, "iteration.txt", str(i))
        log.info("loop iteration %d/%d", i, max_iterations + _extra)

        # change-f5c28a04 (F2): clear work-summary.txt per cycle, not only at
        # loop start. Carried over, a prior cycle's manifest is read by
        # _extract_deliverables and therefore by the read-evidence, syntax and
        # pytest gates, which then adjudicate the previous cycle's deliverables
        # as though they were this cycle's. It also suppresses synthesis at the
        # wall-clock and work-complete exits, both of which decline to overwrite
        # an existing manifest.
        #
        # Cleared here, before the work phase, rather than alongside
        # review-feedback.txt before the review phase: the reviewer and all
        # three gates consume this file, so clearing it at that point would
        # remove the very manifest they exist to check.
        clear_state(state_dir, "work-summary.txt")

        # Work phase
        console.print("\n[bold blue]▶ WORK PHASE[/bold blue]")
        rc, _, _ = await run_phase(client, mcp, worker_model, work_recipe,
                                   task, phase_max_iterations, state_dir, log,
                                   phase_label="WORKER",
                                   context_window=context_window,
                                   budget_warn_pct=budget_warn_pct,
                                   budget_abort_pct=budget_abort_pct,
                                   mcp_error_threshold=mcp_error_threshold,
                                   max_tool_calls_per_iter=max_tool_calls_per_iter,
                                   project_root=project_root,
                                   phase_duration_seconds=phase_duration_seconds,
                                   max_completion_tokens=max_completion_tokens,
                                   max_tool_result_chars=max_tool_result_chars,
                                   write_scope=write_scope)
        log.info("work phase rc=%d", rc)
        if rc != 0:
            console.print("[red]✗ WORK PHASE FAILED[/red]")
            return 1

        blocked = os.path.join(state_dir, "BLOCKED.md")
        if os.path.exists(blocked):
            blocked_content = open(blocked).read()
            log.warning("BLOCKED:\n%s", blocked_content)
            console.print(Panel(escape(blocked_content), title="[red]✗ BLOCKED[/red]", border_style="red"))
            return 1

        # Audit scope lock: reject unauthorised modifications to audit-index.md.
        _scope_error = _check_audit_scope(state_dir, _audit_original_count, log)
        if _scope_error:
            log.warning("audit scope lock: %s", _scope_error)
            console.print(
                "[yellow][engine] audit scope lock: item count changed "
                "\u2014 injecting corrective feedback[/yellow]"
            )
            write_state(state_dir, "review-feedback.txt", _scope_error)
            clear_state(state_dir, "work-complete.txt", "review-result.txt")
            continue

        console.print("\n[bold blue]▶ REVIEW PHASE[/bold blue]")

        # F6: syntax gate; F6b and change-e58fd295: declared command gates.
        # Results are injected into the reviewer task.
        _syntax_result = _run_syntax_gate(state_dir, log) if "syntax" in gate_list else ""
        if "syntax" in gate_list:
            _log_gate(log, "syntax", "built_in", G.gate_status(_syntax_result))
        _command_results: list[tuple[str, str]] = []
        for _g in gate_list:
            if _g in ("syntax", "reviewer"):
                continue
            if _g == G.PYTEST_GATE:
                _res = (_run_pytest_gate(state_dir, log, project_root, spec=gate_specs[_g])
                        if _g in gate_specs else _run_pytest_gate(state_dir, log, project_root))
            else:
                _res = _run_command_gate(_g, gate_specs.get(_g, {}), state_dir, log, project_root)
            _log_gate(log, _g, "command", G.gate_status(_res))
            _command_results.append((_g, _res))
        if gate_outcomes is not None:
            gate_outcomes.clear()
            if "syntax" in gate_list:
                gate_outcomes["syntax"] = G.gate_status(_syntax_result)
            gate_outcomes.update((_g, G.gate_status(_res)) for _g, _res in _command_results)

        # Clear signal files after the gates, before the reviewer starts.
        # change-b7e3d5a9: review-feedback.txt is cleared here, per cycle, not only
        # at loop start; the worker has already consumed the prior cycle's feedback.
        # change-82dbf16a iteration 3 (audit F2-03, F2-04): the clear runs after
        # the gates, because gate processes run worker-written code; .complete and
        # awaiting-approval.md are included, so only the engine's own SHIP path
        # can leave them. review-result.txt is not a verdict source (F-01).
        _not_cleared = clear_state(state_dir, "work-complete.txt", "review-feedback.txt",
                                   "review-result.txt", ".complete", "awaiting-approval.md")
        if _not_cleared:  # change-82dbf16a iteration 5 (F4-01)
            write_state(state_dir, "BLOCKED.md",
                        "# BLOCKED\n\nState files could not be removed after the gates: "
                        f"{', '.join(_not_cleared)}. Remove them by hand.\n")
            log.error("BLOCKED: state files could not be removed: %s", ", ".join(_not_cleared))
            console.print(f"[red][engine] BLOCKED: state files could not be removed: "
                          f"{escape(', '.join(_not_cleared))}[/red]")
            return 1

        # change-82dbf16a (M-02, FR-03-02 v1.3): a gate that cannot run ends the
        # run BLOCKED, naming the gate; SHIP is not possible without it.
        _not_run = [(_g, _res) for _g, _res in _command_results if G.gate_status(_res) == "UNCHECKED"]
        # change-82dbf16a iteration 4 (audit F3-01): the clear above runs before
        # this check, so a gate that writes state files and then cannot run
        # leaves none of them.
        if _not_run:
            _names = ", ".join(_g for _g, _ in _not_run)
            write_state(state_dir, "BLOCKED.md",
                        "# BLOCKED\n\n"
                        f"Gate could not run: {_names}. Check the gate command and "
                        "gates.python in ai/config.yaml.\n\n"
                        + "\n".join(_res for _, _res in _not_run))
            log.error("BLOCKED: gate could not run: %s", _names)
            console.print(f"[red][engine] BLOCKED: gate could not run: {escape(_names)}[/red]")
            return 1

        # F16: Prepend [ENGINE RUNTIME CONTEXT] to review_task for consistent framing
        _review_header = (
            f"[ENGINE RUNTIME CONTEXT]\n"
            f"state_dir (full absolute path): {state_dir}\n"
            f"project_root (full absolute path): {project_root}\n"
            f"[END RUNTIME CONTEXT]\n\n"
        )
        review_task = _review_header + f"Review the work in state directory '{state_dir}'."
        # change-bdc6820f (FR-05-03): absolute deliverable paths, so the reviewer
        # does not resolve relative paths against the state directory.
        _deliverables_block = _deliverables_block_for(
            state_dir, log, write_scope.files if write_scope is not None else frozenset())
        if _deliverables_block:
            review_task = _deliverables_block + "\n" + review_task
        # Prepend gate results to review_task (syntax first, then command gates in order)
        for _g, _res in reversed(_command_results):
            if _res:
                review_task = _res + "\n" + review_task
        if _syntax_result:
            review_task = _syntax_result + "\n" + review_task
        rc, reviewer_final_msg, _reviewer_read_paths = await run_phase(
            reviewer_client, mcp, reviewer_model, review_recipe,
            review_task, phase_max_iterations, state_dir, log,
            phase_label="REVIEWER",
            context_window=reviewer_context_window,
            budget_warn_pct=budget_warn_pct,
            budget_abort_pct=budget_abort_pct,
            mcp_error_threshold=mcp_error_threshold,
            max_tool_calls_per_iter=max_tool_calls_per_iter,
            project_root=project_root,
            phase_duration_seconds=phase_duration_seconds,
            max_completion_tokens=max_completion_tokens,
            max_tool_result_chars=max_tool_result_chars,
        )
        log.info("review phase rc=%d", rc)
        if rc != 0:
            console.print("[red]✗ REVIEW PHASE FAILED[/red]")
            return 1

        # change-82dbf16a iteration 2 (audit F-01): the verdict comes from the
        # reviewer's final message only. review-result.txt is no longer read: the
        # review phase cannot write, and gate processes (worker-written test code)
        # run between the clear above and this point.
        if reviewer_final_msg:
            verdict = _normalize_verdict(reviewer_final_msg)
            log.debug("verdict from reviewer final message: '%s' -> '%s'",
                      reviewer_final_msg[:60].replace('\n', ' '), verdict)
        else:
            verdict = "REVISE"
            log.debug("no verdict source — defaulting to REVISE")
        _log_gate(log, "reviewer", "reviewer_verdict", verdict)

        # Persist the REVISE feedback body from the reviewer's final message.
        # Reviewer is read-only (F5) so cannot write review-feedback.txt itself.
        # The file was cleared before the review phase; any content now came from
        # outside the engine (audit F-01), so the reviewer's feedback replaces it.
        if verdict == "REVISE" and reviewer_final_msg:
            # Strip the verdict declaration, whichever form it took. Using
            # _strip_verdict rather than an unconditional leading-token drop
            # keeps the body intact when the verdict was stated on its own
            # line at the end, which is the common case.
            feedback_body = _strip_verdict(reviewer_final_msg)
            if feedback_body:
                write_state(state_dir, "review-feedback.txt", feedback_body)
                log.debug("persisted REVISE feedback (%d chars)", len(feedback_body))

        if verdict == "SHIP":
            # Audit SHIP gate: check scope integrity then coverage before accepting SHIP.
            _gate_scope_err = _check_audit_scope(state_dir, _audit_original_count, log)
            if _gate_scope_err:
                log.warning("audit SHIP gate: scope violation — %s", _gate_scope_err)
                console.print(
                    "[yellow][engine] audit SHIP gate: scope violation "
                    "— overriding SHIP to REVISE[/yellow]"
                )
                write_state(state_dir, "review-feedback.txt", _gate_scope_err)
            else:
                _unchecked = _count_unchecked_audit_items(state_dir, log)
                if _unchecked > 0:
                    log.warning(
                        "audit SHIP gate: reviewer issued SHIP with %d unchecked item(s) — overriding",
                        _unchecked,
                    )
                    console.print(
                        f"[yellow][engine] audit SHIP gate: {_unchecked} unchecked item(s) remain "
                        f"— overriding SHIP to REVISE[/yellow]"
                    )
                    write_state(
                        state_dir, "review-feedback.txt",
                        f"Coverage incomplete: {_unchecked} item(s) in audit-index.md remain unchecked.\n"
                        f"Do not issue SHIP until every item is marked [x].\n"
                        f"Proceed to audit the next unchecked item."
                    )
                else:
                    # Read-evidence SHIP gate: non-audit (loop) path only.
                    # Verify reviewer read each deliverable before accepting SHIP.
                    _read_gate_pass = True
                    if _audit_original_count is None:
                        _deliverables = _extract_deliverables(state_dir, log)
                        if _deliverables:
                            _unread = _deliverables - _reviewer_read_paths
                            if _unread:
                                _read_gate_pass = False
                                log.warning(
                                    "read-evidence SHIP gate: %d unread deliverable(s) — overriding SHIP",
                                    len(_unread),
                                )
                                console.print(
                                    f"[yellow][engine] read-evidence SHIP gate: {len(_unread)} unread deliverable(s) "
                                    f"— overriding SHIP to REVISE[/yellow]"
                                )
                                _unread_list = "\n".join(f"  - {p}" for p in sorted(_unread))
                                write_state(
                                    state_dir, "review-feedback.txt",
                                    f"Read-evidence gate failed: the following deliverable(s) were not read:\n"
                                    f"{_unread_list}\n\n"
                                    f"Read each file before issuing SHIP."
                                )
                        else:
                            log.debug("read-evidence SHIP gate: no deliverables — gate is no-op")

                        # Command SHIP gates: non-audit (loop) path only.
                        # Override SHIP to REVISE if any command gate reported FAIL
                        # (FR-03-02; the pytest gate keeps its historical message).
                        for _g, _res in _command_results:
                            if not _read_gate_pass:
                                break
                            if G.gate_status(_res) != "FAIL":
                                continue
                            _read_gate_pass = False
                            if _g == G.PYTEST_GATE:
                                log.warning("pytest SHIP gate: test failures detected — overriding SHIP")
                                console.print(
                                    "[yellow][engine] pytest SHIP gate: test failures detected "
                                    "— overriding SHIP to REVISE[/yellow]"
                                )
                                write_state(
                                    state_dir, "review-feedback.txt",
                                    f"Pytest gate failed: tests did not pass.\n\n{_res}"
                                )
                            else:
                                log.warning("%s SHIP gate: FAIL — overriding SHIP", _g)
                                console.print(
                                    f"[yellow][engine] {escape(_g)} SHIP gate: FAIL "
                                    f"— overriding SHIP to REVISE[/yellow]"
                                )
                                write_state(state_dir, "review-feedback.txt",
                                            f"{_g} gate failed.\n\n{_res}")

                    if _read_gate_pass:
                        console.print(Panel(
                            f"[bold]✓ SHIPPED[/bold] after {i} loop iteration(s)",
                            border_style="green",
                        ))
                        log.info("SHIPPED iteration=%d", i)
                        write_state(state_dir, ".complete", f"COMPLETE: iteration {i}")
                        return 0

        feedback = read_state(state_dir, "review-feedback.txt")
        if feedback:
            log.debug("review feedback:\n%s", feedback)
            console.print(Panel(escape(feedback), title="[yellow]↻ REVISE[/yellow]", border_style="yellow"))
        else:
            console.print("[yellow]↻ REVISE[/yellow]")

        # F12: Stall detection — check for consecutive identical feedback
        _current_hash = _hash_feedback(feedback)
        if _current_hash and _current_hash == _last_feedback_hash:
            _stall_count += 1
            log.debug("stall detection: identical feedback (count=%d/%d)", _stall_count, stall_threshold)
            if _stall_count >= stall_threshold:
                blocked_msg = (
                    "# BLOCKED\n\n"
                    f"Stall detected: identical REVISE feedback for {stall_threshold} consecutive cycles.\n\n"
                    "The loop is making no progress. Intervention required.\n\n"
                    f"Last feedback:\n\n{feedback[:500]}\n"
                )
                write_state(state_dir, "BLOCKED.md", blocked_msg)
                log.error("BLOCKED: stall detected — %d consecutive identical feedbacks", stall_threshold)
                console.print(
                    f"[red][engine] BLOCKED: stall detected — {stall_threshold} consecutive identical feedbacks[/red]"
                )
                return 1
        else:
            _stall_count = 0
            _last_feedback_hash = _current_hash

        clear_state(state_dir, "work-complete.txt", "review-result.txt")


def _resolve_gate_specs(manifest, config: dict) -> dict[str, dict]:
    """
    Command gate specifications: manifest defaults overridden by gates.<name>
    in ai/config.yaml; gates.python selects {python} (FR-03-03, change-e58fd295).
    """
    gcfg = config.get("gates") or {}
    if not isinstance(gcfg, dict):
        raise ConfigError("gates: must be a mapping")
    unknown = sorted(set(gcfg) - set(manifest.gates) - {"python"})
    if unknown:
        raise ConfigError(f"gates.{unknown[0]}: not declared in the governance model manifest")
    python = gcfg.get("python") or sys.executable
    if os.sep in python and not os.path.isabs(python):
        python = os.path.abspath(python)  # relative to the project root (cwd)
    # change-82dbf16a (M-05): provider key variables are removed from the gate
    # environment, so project tests never see them.
    scrub = sorted({p["api_key_env"] for p in (config.get("providers") or {}).values()
                    if isinstance(p, dict) and isinstance(p.get("api_key_env"), str)})
    specs: dict[str, dict] = {}
    for name, g in manifest.gates.items():
        override = gcfg.get(name) or {}
        if not isinstance(override, dict):
            raise ConfigError(f"gates.{name}: must be a mapping")
        specs[name] = {
            "command": override.get("command") or g["command"],
            "timeout_seconds": override.get("timeout_seconds") or g.get("timeout_seconds", G.DEFAULT_TIMEOUT_SECONDS),
            "python": python,
            "scrub_env": scrub,
        }
    return specs


_PROMPT_UUID_RE = re.compile(r"^prompt-([0-9a-f]{8})-")


def _work_item_uuid(task: str | None) -> str | None:
    """The work-item UUID of a T03 prompt task file (prompt-<uuid>-<name>.md), else None."""
    if not task:
        return None
    m = _PROMPT_UUID_RE.match(os.path.basename(task))
    return m.group(1) if m else None


def _write_awaiting_approval(state_dir: str, manifest, loop_stage_id: str,
                             work_item: str | None, log: logging.Logger,
                             not_applicable: list[str] | None = None) -> None:
    """
    After SHIP: record that operator approval is awaited (FR-03-05). Gates
    that had nothing to check in the final cycle are listed as not applicable
    (change-82dbf16a, M-02).
    """
    stage = manifest.next_approval_stage(loop_stage_id)
    if stage is None:
        return
    item = work_item or "untracked task (no prompt UUID)"
    na = ""
    if not_applicable:
        na = ("\nGates not applicable in the final cycle (nothing to check): "
              f"{', '.join(not_applicable)}\n")
    write_state(state_dir, "awaiting-approval.md",
                "# Awaiting approval\n\n"
                f"Work item: {item}\n"
                f"Stage: {stage.id}\n\n"
                "The loop shipped. The engine does not pass human approval gates; "
                "the operator reviews the result and records the approval.\n" + na)
    log.info("awaiting approval: work item=%s stage=%s", item, stage.id)
    console.print(f"[blue][engine] awaiting operator approval: {escape(item)} → {escape(stage.id)}[/blue]")


def _finish_run(mode: str, rc: int, state_dir: str, manifest, loop_stage, work_item: str | None,
                gate_outcomes: dict[str, str], since: float, log: logging.Logger) -> None:
    """
    After a loop or worker run: SHIP in loop mode records the awaited approval
    with the gates that were not applicable; a failed loop or worker run names
    the stage to return to (change-82dbf16a, M-02 and L-12).
    """
    if mode == "loop" and rc == 0:
        _write_awaiting_approval(state_dir, manifest, loop_stage.id, work_item, log,
                                 [g for g, st in gate_outcomes.items() if st == "SKIPPED"])
    elif mode in ("loop", "worker") and rc != 0:
        _annotate_blocked_return(state_dir, loop_stage, work_item, since, log)


def _annotate_blocked_return(state_dir: str, loop_stage, work_item: str | None,
                             since: float, log: logging.Logger) -> None:
    """On BLOCKED for a tracked work item, name the stage to return to (FR-02-03)."""
    if not work_item or not loop_stage.on_blocked:
        return
    path = os.path.join(state_dir, "BLOCKED.md")
    if not os.path.exists(path) or os.path.getmtime(path) < since:
        return
    with open(path) as fh:
        if "Return to stage:" in fh.read():
            return
    with open(path, "a") as fh:
        fh.write(f"\nReturn to stage: {loop_stage.on_blocked} (work item {work_item})\n")
    log.info("BLOCKED: return to stage %s for work item %s", loop_stage.on_blocked, work_item)


async def main_async(args: argparse.Namespace) -> int:
    config    = load_yaml(args.config)
    state_dir = os.path.abspath(config["loop"]["state_dir"])

    # Reset mode — no model or MCP connection required
    if args.mode == "reset":
        return reset_state(state_dir)

    # change-c37198be (D2): a --task value that names a file must name one that
    # exists. Checked before any state change so a mistyped path cannot start
    # an unscoped run with the literal path as its task text.
    if args.task and not os.path.exists(args.task) and _looks_like_task_path(args.task):
        console.print(f"[red][engine] error: task file not found: {escape(args.task)} (cwd {escape(os.getcwd())})[/red]")
        return 1

    # Warn if a prior SHIP is present and not yet cleared
    if os.path.exists(os.path.join(state_dir, ".complete")):
        console.print(f"[yellow][engine] warning: prior SHIP detected in {state_dir}[/yellow]")
        console.print("[yellow][engine]          run --mode reset after human acceptance to clear[/yellow]")

    # change-53c6f252: role-to-model binding (FR-04-01, FR-04-08). Resolved
    # before any state change so a configuration error stops the run cleanly.
    try:
        bindings = build_role_bindings(config, args)
    except ConfigError as e:
        console.print(f"[red][engine] configuration error ({escape(args.config)}): {escape(str(e))}[/red]")
        return 1
    worker_b, reviewer_b = bindings["worker"], bindings["reviewer"]

    # change-e58fd295: the installed governance model's manifest (FR-01-05)
    try:
        manifest = load_manifest(locate_manifest())
    except ManifestError as e:
        console.print(f"[red][engine] manifest error: {escape(str(e))}[/red]")
        return 1
    try:
        gate_specs = _resolve_gate_specs(manifest, config)
    except ConfigError as e:
        console.print(f"[red][engine] configuration error ({escape(args.config)}): {escape(str(e))}[/red]")
        return 1
    loop_stage = manifest.loop_stage()
    work_item = _work_item_uuid(args.task)

    # change-ee5357ec: pre-run check for tracked work items (FR-08-05). A T03
    # prompt inside ai/workspace/ may enter the loop stage only when its
    # earlier stages have evidence and committed approvals. Checked before any
    # state change; exit code 3.
    # change-82dbf16a iteration 4 (audit F3-02): the task file is read once,
    # here; the pre-run check verifies these bytes and the run uses them.
    _task_bytes: bytes | None = None
    if args.task and os.path.isfile(args.task):
        with open(args.task, "rb") as _fh:
            _task_bytes = _fh.read()
    _tracked = bool(work_item) and ST.is_tracked_task(os.getcwd(), args.task)
    if args.mode in ("loop", "worker") and _tracked:
        # change-82dbf16a iteration 5 (audit F4-02): prerun_missing refuses a
        # tracked task whose content was not read.
        _missing = ST.prerun_missing(os.getcwd(), manifest, work_item, args.task, _task_bytes)
        if _missing:
            console.print(f"[red][engine] work item {escape(work_item)} is not ready for "
                          f"'{escape(loop_stage.id)}'; missing:[/red]")
            for _m in _missing:
                console.print(f"[red]  - {escape(_m)}[/red]")
            return 3
        console.print(f"[blue][engine] work item {escape(work_item)}: prerequisites for "
                      f"'{escape(loop_stage.id)}' met[/blue]")
    elif work_item and not _tracked:
        console.print(f"[yellow][engine] work item {escape(work_item)}: prompt is outside "
                      f"ai/workspace/ — not tracked[/yellow]")
    max_iter          = args.max_iterations or config["loop"]["max_iterations"]
    deadline          = time.monotonic() + args.duration * 3600 if args.duration else None
    phase_max_iter    = config["loop"].get("phase_max_iterations", max_iter)
    mcp_error_thresh      = config["loop"].get("mcp_error_threshold", 3)
    max_tool_calls        = config["loop"].get("max_tool_calls_per_iteration", 10)
    do_preflight          = config["loop"].get("preflight_check", False)
    # F28: phase wall-clock cap (minutes -> seconds; None disables)
    _phase_duration_min   = config["loop"].get("phase_duration_minutes")
    phase_duration_seconds = _phase_duration_min * 60 if _phase_duration_min else None
    model          = worker_b.model  # worker binding; used for banners and the context report

    # Execution controls (opt-in, default disabled)
    exec_cfg = config.get("execution", {})
    max_completion_tokens = exec_cfg.get("max_completion_tokens")  # None = omit max_tokens
    max_tool_result_chars = exec_cfg.get("max_tool_result_chars")  # None = no truncation
    strict_tactical_brief = exec_cfg.get("strict_tactical_brief", False)

    # Resolve context budget config
    ctx_cfg        = config.get("context", {})
    budget_warn    = ctx_cfg.get("budget_warn_pct", 0.80)
    budget_abort   = ctx_cfg.get("budget_abort_pct", 0.95)

    # 3.1: preserve prior run logs before this run begins. Null (default) = no-op.
    _log_archive_rel = config["loop"].get("log_archive_dir")
    _log_archive_dir = os.path.abspath(_log_archive_rel) if _log_archive_rel else None
    archive_prior_logs(state_dir, _log_archive_dir)

    log = setup_logging(state_dir)
    log.info("engine start mode=%s worker=%s:%s reviewer=%s:%s state_dir=%s", args.mode,
             worker_b.provider_name, worker_b.model, reviewer_b.provider_name, reviewer_b.model,
             state_dir)
    if _log_archive_dir:
        log.info("log archive dir: %s", _log_archive_dir)

    # change-e58fd295: recipes come from the manifest's run types (FR-01-03)
    recipe_set  = _select_recipe_set(state_dir)
    try:
        _work_path, _rev_path = manifest.recipe_paths(recipe_set)
    except ManifestError as e:
        console.print(f"[red][engine] manifest error: {escape(str(e))}[/red]")
        return 1
    work_recipe = load_yaml(_work_path)
    rev_recipe  = load_yaml(_rev_path)
    console.print(f"[blue][engine] governance model: {escape(manifest.name)} {escape(manifest.version)}; "
                  f"recipe set: {recipe_set}[/blue]")
    log.info("governance model: %s %s; recipe set: %s (%s, %s)", manifest.name, manifest.version,
             recipe_set, _work_path, _rev_path)

    # F29: initialize audit-report.md as zero-byte at run start (audit runs
    # only, and only if absent) so the worker's first read/find/ls probe on
    # a clean run returns an empty result rather than NOT_FOUND — observed
    # to trigger unnecessary exploratory iterations before the first write.
    # Guarded by file-absence so an in-progress run's findings are never touched.
    if recipe_set == "audit":
        _report_path = os.path.join(state_dir, "audit-report.md")
        if not os.path.exists(_report_path):
            write_state(state_dir, "audit-report.md", "")
            log.info("audit-report.md initialized (zero-byte)")

    # change-53c6f252: readiness and context window per role in use (FR-04-05, FR-04-06)
    roles_in_use = {"worker": [worker_b], "reviewer": [reviewer_b]}.get(args.mode, [worker_b, reviewer_b])
    readiness = config.get("readiness", {})
    _ready: set[tuple[str, str]] = set()
    for b in roles_in_use:
        if (b.provider_name, b.model) in _ready:
            continue
        try:
            await b.provider.await_ready(
                b.model,
                timeout=readiness.get("timeout_seconds", 60.0),
                interval=readiness.get("poll_interval_seconds", 2.0),
                echo=lambda msg, _r=b.role: console.print(f"[blue][engine] {_r}: {escape(msg)}[/blue]"),
            )
        except (TimeoutError, ProviderError) as e:
            write_state(state_dir, "BLOCKED.md",
                        f"# BLOCKED\n\n{b.role} provider '{b.provider_name}' not ready: {e}\n")
            console.print(f"[red][engine] BLOCKED: {b.role} provider '{escape(b.provider_name)}' not ready: {escape(str(e))}[/red]")
            log.error("provider not ready role=%s provider=%s: %s", b.role, b.provider_name, e)
            return 1
        _ready.add((b.provider_name, b.model))

    # Resolve context window per role using the four-tier chain
    context_windows: dict[str, int | None] = {}
    for b in (worker_b, reviewer_b):
        ctx = resolve_context_window(b.model, config, live_query=b.provider.live_context_window)
        context_windows[b.role] = ctx
        if ctx:
            console.print(f"[blue][engine] context window ({b.role}): {ctx:,} tokens ({escape(b.model)})[/blue]")
        else:
            console.print(f"[yellow][engine] context window ({b.role}): unknown — budget tracking disabled[/yellow]")
    context_window = context_windows["worker"]

    # Substitute {PROJECT_ROOT} placeholders in mcp_servers before connection
    _substitute_project_root(config)
    mcp = MCPClient(config.get("mcp_servers", {}))
    await mcp.connect()

    # Resolve task
    if _task_bytes is not None:
        # universal newlines, as the text-mode read did before iteration 4
        raw = _task_bytes.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
        brief = extract_tactical_brief(raw, log)

        # strict_tactical_brief: fail fast when engine profile has no valid brief
        if strict_tactical_brief and not brief:
            target_profile = extract_target_profile(raw, log)
            if target_profile in ("engine", "ael"):  # "ael": legacy value in closed documents
                console.print(
                    "[red][engine] error: strict_tactical_brief enabled and target_profile is 'engine' "
                    "but no valid tactical_brief found in task file[/red]"
                )
                console.print(
                    "[red][engine]        Author a YAML block with 'tactical_brief:' as root key, "
                    "or set strict_tactical_brief: false in config.yaml[/red]"
                )
                log.error(
                    "strict_tactical_brief: target_profile='engine' but no valid tactical_brief in %s",
                    args.task,
                )
                await mcp.close()
                return 1

        task = brief if brief and not brief.startswith("#") else raw
    else:
        task = args.task or read_state(state_dir, "task.md")

    if not task:
        console.print(f"[red][engine] error: no task provided (--task or {state_dir}/task.md)[/red]")
        await mcp.close()
        return 1

    # change-bdc6820f: write scope from the T03 prompt's deliverables (FR-05-01)
    project_root = os.getcwd()
    write_scope = None
    if _task_bytes is not None:
        _deliverables = S.extract_deliverable_paths(raw)
        if _deliverables is not None:
            write_scope = S.build_write_scope(project_root, _deliverables,
                                              manifest.writable_paths, state_dir)
    if write_scope is not None:
        console.print(f"[blue][engine] write scope: {escape(write_scope.describe())}[/blue]")
        log.info("write scope: %s", write_scope.describe())
    else:
        log.info("write scope: project root (task is not a T03 prompt)")

    # Resolve placeholders and prepend runtime context
    task = task.replace("{STATE_DIR}", state_dir).replace("{PROJECT_ROOT}", project_root)
    runtime_header = (
        f"[ENGINE RUNTIME CONTEXT]\n"
        f"state_dir (full absolute path): {state_dir}\n"
        f"project_root (full absolute path): {project_root}\n"
        f"Do not use 'state_dir' or 'project_root' as literal path components.\n"
        f"[END RUNTIME CONTEXT]\n\n"
    )
    task = runtime_header + task

    os.makedirs(state_dir, exist_ok=True)
    write_state(state_dir, "task.md", task)

    # Write context budget report for the planner
    # F8: Include actual system prompt and tool schema in the initial estimate
    _sys_prompt = work_recipe.get("instructions", "")
    _tools = mcp.get_openai_tools()
    initial_tokens = estimate_tokens([
        {"role": "system", "content": _sys_prompt},
        {"role": "user",   "content": task},
    ], tools=_tools)
    write_context_report(
        state_dir, model, context_window,
        initial_tokens, budget_warn, budget_abort
    )
    if context_window:
        pct = (initial_tokens / context_window) * 100
        console.print(f"[blue][engine] initial task: ~{initial_tokens:,} tokens ({pct:.1f}% of window)[/blue]")
        console.print(f"[dim][engine] context report: {state_dir}/context-budget.md[/dim]")

    rc = 1  # default: failure — ensures rc is defined even on unexpected exception
    _run_started = time.time()  # change-e58fd295: BLOCKED.md written by this run
    try:
        if args.mode == "worker":
            # F11: Clear stale phase signals to prevent false completion on iteration 1
            _stale = os.path.join(state_dir, "work-complete.txt")
            if os.path.exists(_stale):
                log.warning("clearing stale work-complete.txt from prior run")
                console.print("[yellow][engine] clearing stale work-complete.txt from prior run[/yellow]")
                os.remove(_stale)
            rc, _, _ = await run_phase(worker_b.provider, mcp, worker_b.model, work_recipe, task, phase_max_iter,
                                       state_dir, log, phase_label="WORKER",
                                       context_window=context_windows["worker"],
                                       budget_warn_pct=budget_warn,
                                       budget_abort_pct=budget_abort,
                                       mcp_error_threshold=mcp_error_thresh,
                                       max_tool_calls_per_iter=max_tool_calls,
                                       project_root=project_root,
                                       max_completion_tokens=max_completion_tokens,
                                       max_tool_result_chars=max_tool_result_chars,
                                       write_scope=write_scope)
        elif args.mode == "reviewer":
            # F11: Clear stale phase signals for single-phase reviewer mode
            _stale = os.path.join(state_dir, "work-complete.txt")
            if os.path.exists(_stale):
                log.warning("clearing stale work-complete.txt from prior run")
                console.print("[yellow][engine] clearing stale work-complete.txt from prior run[/yellow]")
                os.remove(_stale)
            # F16: Use consistent review task with runtime context (not the worker task)
            _review_task = (
                f"[ENGINE RUNTIME CONTEXT]\n"
                f"state_dir (full absolute path): {state_dir}\n"
                f"project_root (full absolute path): {project_root}\n"
                f"[END RUNTIME CONTEXT]\n\n"
                f"Review the work in state directory '{state_dir}'."
            )
            rc, _, _ = await run_phase(reviewer_b.provider, mcp, reviewer_b.model, rev_recipe, _review_task, phase_max_iter,
                                       state_dir, log, phase_label="REVIEWER",
                                       context_window=context_windows["reviewer"],
                                       budget_warn_pct=budget_warn,
                                       budget_abort_pct=budget_abort,
                                       mcp_error_threshold=mcp_error_thresh,
                                       max_tool_calls_per_iter=max_tool_calls,
                                       project_root=project_root,
                                       max_completion_tokens=max_completion_tokens,
                                       max_tool_result_chars=max_tool_result_chars)
        else:  # loop
            _gate_outcomes: dict[str, str] = {}
            rc = await run_loop(worker_b.provider, mcp, worker_b.model, reviewer_b.model,
                                work_recipe, rev_recipe, task, max_iter, phase_max_iter,
                                state_dir, log,
                                context_window=context_windows["worker"],
                                reviewer_client=reviewer_b.provider,
                                reviewer_context_window=context_windows["reviewer"],
                                gates=loop_stage.gates,
                                gate_specs=gate_specs,
                                write_scope=write_scope,
                                gate_outcomes=_gate_outcomes,
                                budget_warn_pct=budget_warn,
                                budget_abort_pct=budget_abort,
                                mcp_error_threshold=mcp_error_thresh,
                                max_tool_calls_per_iter=max_tool_calls,
                                preflight_check=do_preflight,
                                deadline=deadline,
                                project_root=project_root,
                                phase_duration_seconds=phase_duration_seconds,
                                max_completion_tokens=max_completion_tokens,
                                max_tool_result_chars=max_tool_result_chars)
            if rc == 0:
                _archive_audit_artifacts(state_dir, args.task, log)
        _finish_run(args.mode, rc, state_dir, manifest, loop_stage, work_item,
                    _gate_outcomes if args.mode == "loop" else {}, _run_started, log)
    finally:
        log.info("engine end rc=%d", rc)
        await mcp.close()

    return rc


def main() -> None:
    default_config = os.path.join(os.path.dirname(__file__), "..", "..", "config.yaml")  # ai/config.yaml
    p = argparse.ArgumentParser(description="Engine orchestrator — worker/reviewer loop")
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
    p.add_argument("--duration",          type=float, default=None,
                   help="Wall-clock time limit in hours (default: no limit)")
    args = p.parse_args()
    rc = asyncio.run(main_async(args))
    # os._exit bypasses asyncio teardown, preventing MCP stdio subprocess hang
    for h in logging.getLogger("engine").handlers:
        h.flush()
    os._exit(rc)


if __name__ == "__main__":
    main()
