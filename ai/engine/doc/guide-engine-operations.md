Created: 2026 June 02

# Engine Operations — Planner Reference

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

This document is an operational reference for the planner when working with the engine orchestrator in a downstream project. It covers state files, configuration, CLI arguments, termination conditions, context budget management, recipes, and common failure modes.

Authoritative governance reference: `ai/governance/software-engineering/governance.md` P00.11 and P13.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 State Files

State files reside in `ai/state/` (configured via `loop.state_dir` in `config.yaml`). This directory is ephemeral and excluded from git.

### 2.1 Standard loop

| File | Written by | Purpose |
|---|---|---|
| `task.md` | Orchestrator | Task loaded from T03 prompt at startup |
| `iteration.txt` | Orchestrator | Current outer loop cycle number |
| `work-summary.txt` | Worker | Summary of work done this iteration |
| `work-complete.txt` | Worker | Signals worker phase is complete |
| `review-result.txt` | Orchestrator | Cleared before each review phase and not read; the verdict is the reviewer's final response (`SHIP` or `REVISE`) |
| `review-feedback.txt` | Orchestrator | Feedback for the next worker iteration, from the reviewer's final response or a gate |
| `.complete` | Orchestrator | Completion marker (see §5.0 for content variants) |
| `BLOCKED.md` | Worker | Unrecoverable failure details; seeds T06 issue |
| `context-budget.md` | Orchestrator | Context window sizing report for planner |
| `engine_<timestamp>.LOG` | Orchestrator | Full debug log; preserved across reset |

The worker may write `work-summary.txt`, `work-complete.txt` and `BLOCKED.md` only; writes to the other engine files are refused (change-82dbf16a).

### 2.2 Audit Loop additions

| File | Written by | Purpose |
|---|---|---|
| `audit-index.md` | Planner | Ordered list of items to audit; worker marks `[x]` per item |
| `audit-report.md` | Worker | Append-only findings accumulator |
| `audit-uml.md` | Planner | Optional structural map of target codebase |

### 2.3 Reset behaviour

`--mode reset` removes all standard state files except `engine_*.LOG` and `context-budget.md`. Audit files (`audit-index.md`, `audit-report.md`, `audit-uml.md`) are also preserved — archive them to `ai/workspace/audit/` before resetting.

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
      - "@j0hanz/filesystem-mcp@2.5.0"
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
  max_iterations: 5         # outer loop cycles (work+review pairs)
  phase_max_iterations: 20  # inner tool-call iterations per phase
  mcp_error_threshold: 3    # consecutive MCP errors before BLOCKED
  max_tool_calls_per_iteration: 10  # tool call cap per inner iteration
  preflight_check: false    # evaluate success criteria before first worker pass
  state_dir: "ai/state"   # state directory path (relative to project root)

# Execution controls (opt-in, default disabled)
execution:
  max_completion_tokens: null   # cap output tokens when set; null = model default
  max_tool_result_chars: null   # head/tail-truncate large tool results when set; null = none
  strict_tactical_brief: false  # true + engine profile: fail fast on missing tactical_brief

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

`max_iterations` controls outer loop cycles (one work phase + one review phase per cycle). `phase_max_iterations` controls how many times the model is called within a single phase before the phase exits. These are independent — do not conflate them in T03 notes.

For audit runs, set `max_iterations` to at least the number of items in `audit-index.md`.

**Role-to-model binding (change-53c6f252):** without a `roles:` block, both roles use the `omlx:` block above. With `roles:`, each role names a provider from `providers:` and a model. Provider kinds are `omlx`, `openai_compatible` (for example the Mistral API) and `anthropic`. Remote providers read their key from the variable named in `api_key_env`. Set it for the engine process only. Context windows are resolved per role; API models need an entry under `context.model_context_windows`. `ai/engine/config.template.yaml` holds a commented example. CLI precedence with `roles:`: `--worker-model` / `--reviewer-model`, then `--model`, then `roles.<role>.model`. Without `roles:` (legacy `omlx:` block): `--worker-model` / `--reviewer-model`, then `omlx.worker_model` / `omlx.reviewer_model`, then `--model`, then `omlx.default_model`.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 CLI Reference

All arguments to `orchestrator.py`:

| Argument | Type | Default | Purpose |
|---|---|---|---|
| `--mode` | choice | `loop` | `worker` \| `reviewer` \| `loop` \| `reset` |
| `--task` | string | — | Task string or path to T03 prompt file |
| `--config` | path | `ai/config.yaml` | Path to config.yaml |
| `--model` | string | config default | Model for all phases |
| `--worker-model` | string | `--model` | Model for work phase only (loop mode) |
| `--reviewer-model` | string | `--model` | Model for review phase only (loop mode) |
| `--max-iterations` | int | config value | Outer loop cycle limit override |
| `--duration` | float | None | Wall-clock time limit in hours |

Standard invocation after T03 approval:

```bash
python ai/engine/src/orchestrator.py --mode loop \
  --task ai/workspace/prompt/prompt-<uuid>-<n>.md
```

Audit invocation:

```bash
python ai/engine/src/orchestrator.py --mode loop \
  --task ai/workspace/prompt/<uuid>-audit.md \
  --duration 12
```

Reset after human acceptance:

```bash
python ai/engine/src/orchestrator.py --mode reset
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Termination Conditions

| Condition | `.complete` content | Action for planner |
|---|---|---|
| Reviewer issued SHIP | `COMPLETE: iteration N` | Review `work-summary.txt`; proceed to P15 test |
| Duration limit reached | `DURATION_LIMIT: iteration N` | Review `audit-report.md`; archive and reset |
| BLOCKED | Not written | Read `BLOCKED.md`; create T06 issue via P03 |
| `max_iterations` exhausted | Not written | Review partial state; extend or retry |
| Context budget abort | Not written | Reduce `tactical_brief`; run `--mode reset`; retry |
| Unclean exit (crash/signal) | Not written | Check `.LOG` for `engine end rc=N` line; absence indicates unclean exit |
| Pre-run check failed (exit 3) | Not written | Provide the listed documents or record the approvals; rerun |

The `engine end rc=N` line is always written to the `.LOG` file on any clean exit. `.complete`, `review-result.txt`, `review-feedback.txt` and `awaiting-approval.md` are cleared after the gates and before every review phase, also when a gate cannot run and whatever their type (file, symlink, directory), so only the engine's SHIP path leaves `.complete`. An entry that cannot be removed ends the run BLOCKED naming it; `--mode reset` then returns 1. `engine_status` reports `shipped` only for a regular `.complete` file. Gate commands run worker-written code with the operator's permissions (design DI-06): confirm a SHIP reported by `engine_status` with `SHIPPED` and `engine end rc=0` in the log. If this line is absent from the log, the process terminated abnormally.

**Stage tracking and approvals (change-ee5357ec).** A T03 prompt inside `ai/workspace/` is a tracked work item. The engine derives its stage from its documents and from the approvals committed in `ai/approvals.yaml`. Before a `loop` or `worker` run it checks every earlier stage on the work item's path (SE: issue, change, prompt); when evidence or an approval is missing it lists what is missing and exits with code 3, before any state change. Record an approval from the project root:

```bash
python ai/engine/src/approve.py <uuid> <stage>   # e.g. approve.py 1a2b3c4d prompt
```

The command appends the entry and commits `ai/approvals.yaml` alone. Uncommitted edits to the file are ignored. The entry records the git blob hash of each document of the approved stage, keyed by its path under `ai/workspace/` (change-82dbf16a). When a document of an approved stage is edited, or another document with the same UUID is added, the pre-run check reports that the approval no longer matches; review the documents and run `approve.py` again. Record an approval after the document is final, including its status field. The task passed to the engine must be the approved prompt itself: one of the work item's active documents in `ai/workspace/prompt/` as `stages.py` lists them, named by its own file name (no symlink under another work item's name). The engine reads the task file once, before the check, and runs exactly those bytes; they must equal the approved content, so an edit made during start-up cannot reach the run. A tracked task that cannot be read is refused (exit 3). Any other file for a tracked work item is refused (exit 3; engine-mcp refuses it before starting). Free-text tasks and prompt files outside `ai/workspace/` are not tracked.

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Context Budget Management

### 6.1 Initial setup

`context-budget.md` is written automatically by the orchestrator at every startup (`write_context_report()`, run before the first phase). No separate invocation is required; a standalone `budget.py` script previously performed this role and has been retired (change-d42e64a9). Read `ai/state/context-budget.md` after the first run following any config or model change, before authoring any engine-targeted T03 prompt (P13.2).

### 6.2 Budget thresholds

The orchestrator tracks estimated token count per phase iteration. At each threshold:

| Threshold | Default | Behaviour |
|---|---|---|
| `budget_warn_pct` | 80% | Yellow warning bar in TUI; logged |
| `budget_abort_pct` | 95% | Phase aborted; loop exits with error |

### 6.3 Tactical_brief sizing (engine-targeted prompts only)

Applies only when the T03 prompt's `prompt_info.target_profile` is `engine`; `claude_code` and `claude_omlx` profiles do not use `tactical_brief`.

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

Recipes are YAML files. The `instructions` field is injected as the system prompt for each inference call. `{{TOOLS}}` is replaced at runtime with the live MCP tool signatures.

| Recipe | Role | Use |
|---|---|---|
| `loop-work.yaml` | Worker | Standard code generation tasks |
| `loop-review.yaml` | Reviewer | Standard task review — SHIP/REVISE |
| `audit-work.yaml` | Audit worker | Read-only codebase analysis |
| `audit-review.yaml` | Audit reviewer | Coverage check and finding quality |

The governance model's `manifest.yaml` maps each run type (`loop`, `audit`) to a recipe pair. A recipe path resolves against the model folder first (`ai/governance/<model>/`), then `ai/engine/recipes/`. The loop recipes are in `ai/engine/recipes/`; the SE audit recipes are in `ai/governance/software-engineering/recipes/`. The orchestrator selects the `audit` run type when `audit-index.md` is present in the state directory, otherwise `loop`.

Gates: the loop stage's gates come from the manifest (SE: `syntax`, `pytest`, `reviewer`). Each result is logged as `gate=<name> type=<type> result=<result>`. A failing command gate overrides SHIP. A command gate that cannot run (`UNCHECKED`, for example a wrong `gates.python`) ends the run BLOCKED and `BLOCKED.md` names the gate. A gate with nothing to check is not applicable and is listed in `awaiting-approval.md` (change-82dbf16a). Override a command gate or the interpreter for `{python}` under `gates:` in `ai/config.yaml` (see the template). After SHIP the engine writes `awaiting-approval.md`; for a T03 prompt task that ends BLOCKED, `BLOCKED.md` names the stage to return to (change-e58fd295).

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Common Failure Modes

### 8.1 BLOCKED — MCP error threshold

**Symptom:** `BLOCKED.md` written; message references MCP validation errors.

**Cause:** The worker issued malformed tool calls (wrong argument names or types) three consecutive times.

**Remediation:** Read `BLOCKED.md` for the failing tool call. Verify tool parameter names against the live MCP schema. If the brief is ambiguous about file paths, clarify. Create T06 issue if the block recurs.

### 8.2 Max iterations exhausted without SHIP

**Symptom:** Loop exits after N iterations; no `.complete`.

**Cause:** Task complexity exceeds configured iteration budget.

**Remediation:** Review `work-summary.txt` to assess progress. Either increase `max_iterations` in `config.yaml` or decompose the task into smaller T03 prompts.

### 8.3 Worker loop — malformed final response

**Symptom:** `BLOCKED.md` with message "Worker final response is malformed".

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

### 8.7 Write outside the declared scope

**Symptom:** Worker TUI shows "scope violation: write outside the declared scope: <path>"; the log has `write rejected tool=… path=… reason=…`.

**Cause:** For a T03 prompt task the worker may write only the prompt's `deliverable.files`, the governance model's `writable_paths` (SE: `tests/`) and the state directory (change-bdc6820f). Free-text tasks keep project-root containment only.

**Remediation:** If the file is a genuine deliverable, add it to `deliverable.files` in the prompt and rerun. Directory creation on the way to a declared file is allowed. The reviewer receives the deliverables as absolute paths in a `[DELIVERABLES]` block.

Related refusals (change-82dbf16a): `write refused: … is or contains an engine signal file` (the worker targeted an engine-owned state file, or a directory holding one; compared case-insensitively); `write refused: tool '…' was called without a recognised path argument`; `tool refused tool=… reason=…` in the log (a tool not offered to the phase, or any write tool in the review phase). Paths are compared after symlink resolution.

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
| 1.5 | 2026-09-25 | change-5bcd46ad: layout and terminology migration (engine and governance paths; AEL → engine, Ralph Loop → loop, ael-mcp → engine-mcp) |
| 1.6 | 2026-10-01 | §3.0: role-to-model binding note (providers:, roles:, api_key_env, per-role context window; change-53c6f252) |
| 1.7 | 2026-10-01 | §7.0: recipes resolved through manifest run types; gates, awaiting-approval.md and BLOCKED return stage (change-e58fd295) |
| 1.8 | 2026-10-01 | §8.7: write outside the declared scope (change-bdc6820f) |
| 1.9 | 2026-10-01 | §5.0: pre-run check (exit 3), stage tracking and approve.py (change-ee5357ec) |
| 1.10 | 2026-10-01 | Terminology: Strategic Domain → planner, Tactical Domain → worker and reviewer (change-155cc014) |
| 1.11 | 2026-10-01 | §2.1 state file writers, §3.0 legacy model precedence, §5.0 content-bound approvals, §7.0 UNCHECKED and not-applicable gates, §8.7 refusals (change-82dbf16a; audit-14e05e35 H-01, H-02, H-03, M-01, M-02, L-06, L-07) |
| 1.12 | 2026-10-01 | §2.1 review-result.txt not read; §5.0 blob keys and task file rule; §8.7 directory and case refusals (change-82dbf16a iteration 2; follow-up F-01 to F-06) |
| 1.13 | 2026-10-01 | §5.0: signal files cleared after the gates, SHIP confirmation, task file must be a listed prompt document (change-82dbf16a iteration 3; second follow-up F2-01 to F2-04) |
| 1.14 | 2026-10-01 | §5.0: clear also on a gate that cannot run; task read once and bound to the approved content (change-82dbf16a iteration 4; third follow-up F3-01, F3-02) |
| 1.15 | 2026-10-01 | §5.0: non-regular state entries, reset exit code, regular .complete for shipped, unread tracked task refused (change-82dbf16a iteration 5; fourth follow-up F4-01, F4-02) |

---

Copyright (c) 2026 William Watson. MIT License.
