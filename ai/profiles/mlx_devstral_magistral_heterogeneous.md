Created: 2026 July 16

# Implementation Profile: Apple Silicon + MLX (Heterogeneous — Devstral Worker / Magistral Reviewer)

---

## Table of Contents

- [1.0 Overview](<#1.0 overview>)
- [2.0 Placeholder Mappings](<#2.0 placeholder mappings>)
- [3.0 Strategic Domain](<#3.0 strategic domain>)
- [4.0 Tactical Domain](<#4.0 tactical domain>)
- [5.0 Tool-Calling Behaviour](<#5.0 tool-calling behaviour>)
- [6.0 Autonomous Execution Loop](<#6.0 autonomous execution loop>)
- [7.0 Model Selection](<#7.0 model selection>)
- [8.0 Project Setup](<#8.0 project setup>)
- [Version History](<#version history>)

---

## 1.0 Overview

This profile maps governance abstract placeholders to a heterogeneous Apple Silicon MLX setup: a Devstral worker and a Magistral reviewer, both served locally by oMLX and driven by the AEL orchestrator. It requires Apple M-series hardware with sufficient unified memory to hold both models (see [7.0 Model Selection](<#7.0 model selection>)).

| Concern | Implementation |
|---|---|
| Strategic Domain | Claude Desktop (preferred) |
| Tactical Domain — worker | Devstral Small 2 2512 8bit via oMLX + AEL |
| Tactical Domain — reviewer | Magistral Small 2509 6bit via oMLX + AEL |
| AEL mechanism | AEL orchestrator / Ralph Loop |

Rationale: the worker performs synthesis (code generation, multi-file editing); the reviewer performs verification. Using a distinct reasoning model for review provides heterogeneity without changing the worker. Both models are Mistral-family (`mistral3`), so the AEL parser applies to both.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Placeholder Mappings

| Placeholder | Resolved Value |
|---|---|
| `<tactical_context>` | `ai/context.md` |

`<tactical_config>/` and `<skills_dir>/` do not apply to this profile. AEL configuration is in `ai/ael/config.yaml`; recipes are in `ai/ael/recipes/`.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Strategic Domain

**Preferred implementation:** Claude Desktop

Any frontier model with sufficient reasoning capability may substitute. The Strategic Domain role requires: planning, governance interpretation, design creation, prompt authoring, and validation.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Tactical Domain

**Worker:** Devstral Small 2 2512 8bit via oMLX + AEL orchestrator
**Reviewer:** Magistral Small 2509 6bit via oMLX + AEL orchestrator

**Hardware requirement:** Apple M-series chip. Both models resident require approximately 43 GB; 64 GB unified memory is recommended. On 48 GB, oMLX TTL eviction reloads the inactive model each phase transition, adding reload latency.

**Inference server:**

```bash
omlx serve --model-dir /path/to/ai-models
```

The server exposes an OpenAI-compatible endpoint at `http://localhost:8000/v1`.

**Model downloads:**

```python
from huggingface_hub import snapshot_download
# Worker
snapshot_download(
    repo_id="mlx-community/mistralai_Devstral-Small-2-24B-Instruct-2512-MLX-8Bit",
    local_dir="/path/to/ai-models/mistralai_Devstral-Small-2-24B-Instruct-2512-MLX-8Bit"
)
# Reviewer
snapshot_download(
    repo_id="mlx-community/Magistral-Small-2509-MLX-6bit",
    local_dir="/path/to/ai-models/Magistral-Small-2509-MLX-6bit"
)
```

Use Python 3.11+. Confirm each repo id against the served id reported by oMLX `/v1/models` before relying on it.

**AEL config** (`ai/ael/config.yaml`):

```yaml
omlx:
  base_url: http://127.0.0.1:8000/v1
  api_key: local
  default_model: mistralai_Devstral-Small-2-24B-Instruct-2512-MLX-8Bit
  reviewer_model: Magistral-Small-2509-MLX-6bit

context:
  model_context_windows:
    mistralai_Devstral-Small-2-24B-Instruct-2512-MLX-8Bit: 262144
    Magistral-Small-2509-MLX-6bit: 131072
```

The worker uses `default_model`; the reviewer uses `reviewer_model`. Per-role resolution precedence is: CLI flag (`--worker-model` / `--reviewer-model`) > config key (`worker_model` / `reviewer_model`) > `default_model`. Each model id must match the id reported by oMLX `/v1/models` exactly.

Setup guides: [Devstral](../../../docs/setup-apple-silicon-mlx.md) (worker) and [Magistral](../../../docs/setup-apple-silicon-mlx-magistral.md) (reviewer).

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Tool-Calling Behaviour

Both models are Mistral-family (`mistral3`) and emit Mistral-format tool calls, which the AEL parser (`ai/ael/src/parser.py`) handles. The orchestrator owns the full tool dispatch loop; tool calls are parsed from model output and dispatched directly via the Python MCP SDK.

Reviewer verdict parsing was verified for Magistral (clean `SHIP` / `REVISE` leading token; reasoning not leaked into content despite `enable_thinking: true`). Native reviewer tool-calling (reading files, writing `review-result.txt`) is expected on the `mistral3` family basis and should be confirmed on the first real review phase.

Name tools explicitly in recipe prompts; use imperative phrasing.

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Autonomous Execution Loop

**Implementation:** AEL orchestrator / Ralph Loop

State directory: `ai/state/ralph/` (ephemeral, per-task)

**Prerequisites:**
- oMLX running on `localhost:8000` with both models available
- AEL dependencies installed: `pip install -r ai/ael/requirements.txt`
- `ai/ael/config.yaml` configured with `default_model` and `reviewer_model`

**Invocation:**

```bash
python ai/ael/src/orchestrator.py --mode loop --task ai/workspace/prompt/prompt-<uuid>-<n>.md
```

The worker and reviewer models are resolved from config; no per-run model flags are required. Worker and reviewer roles differ by model here, not only by prompt engineering.

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Model Selection

| Role | Model | Quantisation | Approx. Memory |
|---|---|---|---|
| Worker | Devstral Small 2 2512 | 8bit | ~23.5 GB |
| Reviewer | Magistral Small 2509 | 6bit | ~19.5 GB |
| Both resident | — | — | ~43 GB |

Context windows (forced via `model_context_windows`): Devstral 262144 (vendor-validated; overrides the unvalidated 393216 live RoPE ceiling); Magistral 131072 (model `config.json`).

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Project Setup

**.gitignore additions:**

```
# MLX profile - Tactical Domain
ai/state/ralph/
```

**Setup guides:**
- [Apple Silicon + MLX Setup Guide (Devstral)](../../../docs/setup-apple-silicon-mlx.md)
- [Apple Silicon + MLX Setup Guide (Magistral)](../../../docs/setup-apple-silicon-mlx-magistral.md)

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-07-16 | Initial document; heterogeneous Devstral (worker, 8bit) / Magistral (reviewer, 6bit) profile |

---

Copyright (c) 2026 William Watson. MIT License.
