Created: 2026 June 02

# AEL Operations — Strategic Domain Reference

---

## Table of Contents

[1.0 Purpose](<#1.0 purpose>)
[2.0 State Files](<#2.0 state files>)
[3.0 config.yaml Reference](<#3.0 config.yaml reference>)
[4.0 CLI Reference](<#4.0 cli reference>)
[5.0 Termination Conditions](<#5.0 termination conditions>)
[6.0 Context Budget Management](<#6.0 context budget management>)
[7.0 Recipes](<#7.0 recipes>)
[8.0 Common Failure Modes](<#8.0 common failure modes>)
[Version History](<#version history>)

---

## 1.0 Purpose

This document is an operational reference for the Strategic Domain when working with the AEL orchestrator in a downstream project. It covers state files, configuration, CLI arguments, termination conditions, context budget management, recipes, and common failure modes.

Authoritative governance reference: `ai/governance.md` P00 §1.1.11 and P09.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 State Files

State files reside in `ai/state/ralph/` (configured via `loop.state_dir` in `config.yaml`). This directory is ephemeral and excluded from git.

### 2.1 Standard Ralph Loop

| File | Written by | Purpose |
|---|---|---|
| `task.md` | Orchestrator | Task loaded from T04 prompt at startup |
| `iteration.txt` | Orchestrator | Current outer loop cycle number |
| `work-summary.txt` | Worker | Summary of work done this iteration |
| `work-complete.txt` | Worker | Signals worker phase is complete |
| `review-result.txt` | Reviewer | `SHIP` or `REVISE` |
| `review-feedback.txt` | Reviewer | Specific feedback for next worker iteration |
| `.ralph-complete` | Orchestrator | Completion marker (see §5.0 for content variants) |
| `RALPH-BLOCKED.md` | Worker | Unrecoverable failure details; seeds T03 issue |
| `context-budget.md` | Orchestrator | Context window sizing report for Strategic Domain |
| `ael_<timestamp>.LOG` | Orchestrator | Full debug log; preserved across reset |

### 2.2 Audit Loop additions

| File | Written by | Purpose |
|---|---|---|
| `audit-index.md` | Strategic Domain | Ordered list of items to audit; worker marks `[x]` per item |
| `audit-report.md` | Worker | Append-only findings accumulator |
| `audit-uml.md` | Strategic Domain | Optional structural map of target codebase |

### 2.3 Reset behaviour

`--mode reset` removes all standard state files except `ael_*.LOG` and `context-budget.md`. Audit files (`audit-index.md`, `audit-report.md`, `audit-uml.md`) are also preserved — archive them to `ai/workspace/audit/` before resetting.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 config.yaml Reference

Full configuration file with all fields:

```yaml
# Inference endpoint
omlx:
  base_url: "http://127.0.0.1:8000/v1"  # oMLX API base URL
  api_key: "local"                        # oMLX bearer token
  default_model: "<worker-model-id>"     # worker/base model ID as reported by /v1/models
  reviewer_model: "<reviewer-model-id>"  # optional; reviewer-phase model (falls back to default_model)

# MCP server definitions
mcp_servers:
  filesystem:
    command: "/usr/local/bin/npx"
    args:
      - "-y"
      - "@j0hanz/filesystem-mcp@latest"
      - "<allowed-root-path>"
    env:
      PATH: "/opt/homebrew/opt/node@24/bin:/usr/local/bin:/usr/bin:/bin"
  mcp-ripgrep:
    command: "<path-to-mcp-ripgrep>"

# Endpoint readiness polling
readiness:
  timeout_seconds: 60       # wait up to this long for oMLX to respond
  poll_interval_seconds: 2  # polling interval

# Loop control
loop:
  max_iterations: 5         # outer Ralph cycles (work+review pairs)
  phase_max_iterations: 20  # inner tool-call iterations per phase
  mcp_error_threshold: 3    # consecutive MCP errors before BLOCKED
  max_tool_calls_per_iteration: 10  # tool call cap per inner iteration
  preflight_check: false    # evaluate success criteria before first worker pass
  state_dir: "ai/state/ralph"   # state directory path (relative to project root)

# Execution controls (opt-in, default disabled)
execution:
  max_completion_tokens: null   # cap output tokens when set; null = model default
  max_tool_result_chars: null   # head/tail-truncate large tool results when set; null = none
  strict_tactical_brief: false  # true + ael profile: fail fast on missing tactical_brief

# Context budget
context:
  context_window: null    # null = try live oMLX query, then per-model override below
  budget_warn_pct: 0.80   # warn at this fraction of context window
  budget_abort_pct: 0.95  # abort phase at this fraction
  model_context_windows:  # tier-3 per-model overrides (used when the live query returns null)
    "<worker-model-id>": 262144
    "<reviewer-model-id>": 131072
```

**Key distinctions:**

`max_iterations` controls outer Ralph Loop cycles (one work phase + one review phase per cycle). `phase_max_iterations` controls how many times the model is called within a single phase before the phase exits. These are independent — do not conflate them in T04 notes.

For audit runs, set `max_iterations` to at least the number of items in `audit-index.md`.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 CLI Reference

All arguments to `orchestrator.py`:

| Argument | Type | Default | Purpose |
|---|---|---|---|
| `--mode` | choice | `loop` | `worker` \| `reviewer` \| `loop` \| `reset` |
| `--task` | string | — | Task string or path to T04 prompt file |
| `--config` | path | `ai/ael/config.yaml` | Path to config.yaml |
| `--model` | string | config default | Model for all phases |
| `--worker-model` | string | `--model` | Model for work phase only (loop mode) |
| `--reviewer-model` | string | `--model` | Model for review phase only (loop mode) |
| `--max-iterations` | int | config value | Outer Ralph cycle limit override |
| `--duration` | float | None | Wall-clock time limit in hours |

Standard invocation after T04 approval:

```bash
python ai/ael/src/orchestrator.py --mode loop \
  --task ai/workspace/prompt/prompt-<uuid>-<n>.md
```

Audit invocation:

```bash
python ai/ael/src/orchestrator.py --mode loop \
  --task ai/workspace/prompt/<uuid>-audit.md \
  --duration 12
```

Reset after human acceptance:

```bash
python ai/ael/src/orchestrator.py --mode reset
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Termination Conditions

| Condition | `.ralph-complete` content | Action for Strategic Domain |
|---|---|---|
| Reviewer issued SHIP | `COMPLETE: iteration N` | Review `work-summary.txt`; proceed to P06 test |
| Duration limit reached | `DURATION_LIMIT: iteration N` | Review `audit-report.md`; archive and reset |
| RALPH-BLOCKED | Not written | Read `RALPH-BLOCKED.md`; create T03 issue via P04 |
| `max_iterations` exhausted | Not written | Review partial state; extend or retry |
| Context budget abort | Not written | Reduce `tactical_brief`; run `--mode reset`; retry |
| Unclean exit (crash/signal) | Not written | Check `.LOG` for `AEL end rc=N` line; absence indicates unclean exit |

The `AEL end rc=N` line is always written to the `.LOG` file on any clean exit. If this line is absent from the log, the process terminated abnormally.

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Context Budget Management

### 6.1 Initial setup

`context-budget.md` is written automatically by the orchestrator at every startup (`write_context_report()`, run before the first phase). No separate invocation is required; a standalone `budget.py` script previously performed this role and has been retired (change-d42e64a9). Read `ai/state/ralph/context-budget.md` after the first run following any config or model change, before authoring any AEL-targeted T04 prompt (P09 §1.10.2).

### 6.2 Budget thresholds

The orchestrator tracks estimated token count per phase iteration. At each threshold:

| Threshold | Default | Behaviour |
|---|---|---|
| `budget_warn_pct` | 80% | Yellow warning bar in TUI; logged |
| `budget_abort_pct` | 95% | Phase aborted; loop exits with error |

### 6.3 Tactical_brief sizing (AEL-targeted prompts only)

Applies only when the T04 prompt's `prompt_info.target_profile` is `ael`; `claude_code` and `claude_omlx` profiles do not use `tactical_brief`.

Keep the `tactical_brief` to approximately 200–400 tokens (~800–1,600 characters), hard ceiling 1,000 tokens. The brief should contain only: file(s) to modify, hard constraints, implementation steps, deliverables, success criteria. Do not embed design documents or code blocks.

### 6.4 Context pressure symptoms

If the model exhibits any of the following, context pressure is the likely cause:

- Repeated tool calls to the same file
- Verbose, circular responses
- Failure to progress despite apparent effort

Remediation: reduce brief size, run `--mode reset`, retry.

### 6.5 Devstral context window

Devstral Small 2 (2512) reports `max_context_window: 393216` via oMLX, but that figure is an unvalidated RoPE-scaling ceiling; the vendor-validated value is 262144. The orchestrator resolves the window through the four-tier chain (live oMLX query, then the per-model `context.model_context_windows` override) — `models_dir` and on-disk `config.json` reading were retired (change-d42e64a9). This project forces 262144 for the Devstral worker and 131072 for the Magistral reviewer via `model_context_windows`. Magistral does not expose a live `max_context_window`, so its override is required. For audit runs with per-iteration bounded context, this window is rarely a practical constraint.

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Recipes

Recipes are YAML files in `ai/ael/recipes/`. The `instructions` field is injected as the system prompt for each inference call. `{{TOOLS}}` is replaced at runtime with the live MCP tool signatures.

| Recipe | Role | Use |
|---|---|---|
| `ralph-work.yaml` | Worker | Standard code generation tasks |
| `ralph-review.yaml` | Reviewer | Standard task review — SHIP/REVISE |
| `audit-work.yaml` | Audit worker | Read-only codebase analysis |
| `audit-review.yaml` | Audit reviewer | Coverage check and finding quality |

The orchestrator selects recipes from `ai/ael/recipes/` relative to `orchestrator.py`. Custom recipes may be placed in the same directory and referenced by modifying the recipe load path in `main_async()`.

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Common Failure Modes

### 8.1 RALPH-BLOCKED — MCP error threshold

**Symptom:** `RALPH-BLOCKED.md` written; message references MCP validation errors.

**Cause:** The worker issued malformed tool calls (wrong argument names or types) three consecutive times.

**Remediation:** Read `RALPH-BLOCKED.md` for the failing tool call. Verify tool parameter names against the live MCP schema. If the brief is ambiguous about file paths, clarify. Create T03 issue if the block recurs.

### 8.2 Max iterations exhausted without SHIP

**Symptom:** Loop exits after N iterations; no `.ralph-complete`.

**Cause:** Task complexity exceeds configured iteration budget.

**Remediation:** Review `work-summary.txt` to assess progress. Either increase `max_iterations` in `config.yaml` or decompose the task into smaller T04 prompts.

### 8.3 Worker loop — malformed final response

**Symptom:** `RALPH-BLOCKED.md` with message "Worker final response is malformed".

**Cause:** Worker emitted `[TOOL_CALLS]` markers in its final response text, or the response contained MCP error text.

**Remediation:** Reset and retry. If recurs, reduce `phase_max_iterations` to force earlier finalisation.

### 8.4 Context budget abort

**Symptom:** Phase aborts mid-run; TUI shows red budget bar.

**Cause:** Accumulated message history exceeded `budget_abort_pct` of the context window.

**Remediation:** Reduce `tactical_brief` size. Run `--mode reset`. The next run refreshes `context-budget.md` automatically.

### 8.5 oMLX model not loading

**Symptom:** Orchestrator waits at "waiting for endpoint"; times out after 60 seconds.

**Cause:** oMLX is not running, or the model ID in `config.yaml` does not match the loaded model.

**Remediation:**
```bash
# Check oMLX status
curl -s http://localhost:8000/v1/models -H "Authorization: Bearer local"
# Verify model ID matches config.yaml default_model
```

### 8.6 Edit pattern mismatch

**Symptom:** Worker TUI shows yellow "edit pattern mismatch" warning; corrective guidance injected.

**Cause:** Worker attempted to edit a file using text that does not exactly match the file's current content.

**Remediation:** Orchestrator automatically injects a read instruction. If mismatch recurs across iterations, the brief may be referencing stale content. Reset and update the brief.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-06-02 | Initial document |
| 1.1 | 2026-06-14 | Relocated state to ai/state/ralph/ (config.yaml example, prose); workspace/ → ai/workspace/ |
| 1.2 | 2026-07-02 | Rescoped §6.1 and §6.3 to AEL-targeted T04 prompts only; reconciled tactical_brief size guidance with orchestrator.py hard ceiling (issue-713437bc) |
| 1.3 | 2026-07-16 | §3.0 config example: added reviewer_model, execution.* opt-in controls, model_context_windows; removed retired models_dir; corrected context_window comment. §6.5: corrected Devstral window to the 262144 vendor value and the tiered resolver; added the Magistral reviewer window (b5e9d240, a7d3f8b1) |
| 1.4 | 2026-07-16 | §2.1: context-budget.md writer corrected budget.py → Orchestrator. §3.0: mcp-grep example → mcp-ripgrep. §6.1 and §8.4: removed retired standalone budget.py invocation; context-budget.md is written automatically at orchestrator startup |

---

Copyright (c) 2026 William Watson. MIT License.
