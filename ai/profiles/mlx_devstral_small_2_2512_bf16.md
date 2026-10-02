Created: 2026 October 02

# Implementation Profile: Apple Silicon + MLX (Devstral Small 2 2512 BF16)

---

## Table of Contents

- [1.0 Overview](<#1.0 overview>)
- [2.0 Placeholder Mappings](<#2.0 placeholder mappings>)
- [3.0 Planner](<#3.0 planner>)
- [4.0 Worker and Reviewer](<#4.0 worker and reviewer>)
- [5.0 Tool-Calling Behaviour](<#5.0 tool-calling behaviour>)
- [6.0 Engine](<#6.0 engine>)
- [7.0 Model Selection](<#7.0 model selection>)
- [8.0 Project Setup](<#8.0 project setup>)
- [9.0 Verification Status](<#9.0 verification status>)
- [Version History](<#version history>)

---

## 1.0 Overview

This profile maps governance abstract placeholders to Apple Silicon MLX-based local model tooling using Devstral Small 2 (December 2025 release) at full BF16 precision. It is the unquantised counterpart of [mlx_devstral_small_2_2512_6bit.md](mlx_devstral_small_2_2512_6bit.md). It requires Apple M-series hardware. This profile is provisional; see [9.0 Verification Status](<#9.0 verification status>).

| Concern | Implementation |
|---|---|
| Planner | Claude Desktop (preferred) |
| Worker and reviewer | Devstral Small 2 2512 BF16 via oMLX + engine |
| Engine mechanism | Engine orchestrator / loop |

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Placeholder Mappings

| Placeholder | Resolved Value |
|---|---|
| `<tactical_context>` | `ai/context.md` |

`<tactical_config>/` and `<skills_dir>/` do not apply to this profile. Engine configuration is in `ai/config.yaml`; recipes are in `ai/engine/recipes/` and `ai/governance/<model>/recipes/`, mapped by the model's `manifest.yaml`.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Planner

**Preferred implementation:** Claude Desktop

Any frontier model with sufficient reasoning capability may substitute. The planner role requires: planning, governance interpretation, design creation, prompt authoring, and validation.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Worker and Reviewer

**Implementation:** Devstral Small 2 2512 BF16 via oMLX + engine orchestrator

**Architecture:** `mistral3` (oMLX `config_model_type`); 24B parameters; dense.

**Hardware requirement:** Apple M-series chip; 64 GB unified memory minimum (~44 GB resident at BF16 per oMLX).

**Inference server:**

```bash
omlx serve --model-dir /path/to/ai-models
```

The server exposes an OpenAI-compatible endpoint at `http://localhost:8000/v1`.

**Model location:**

Resident at `ai-models/mistralai_Devstral-Small-2-24B-Instruct-2512-MLX-BF16`. To re-acquire:

```python
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id="mlx-community/mistralai_Devstral-Small-2-24B-Instruct-2512-MLX-BF16",
    local_dir="/path/to/ai-models/mistralai_Devstral-Small-2-24B-Instruct-2512-MLX-BF16"
)
```

Use Python 3.11+. The `huggingface-cli` may be unreliable on some macOS configurations.

**Engine config** (`ai/config.yaml`):

```yaml
omlx:
  base_url: http://127.0.0.1:8000/v1
  api_key: local
  default_model: mistralai_Devstral-Small-2-24B-Instruct-2512-MLX-BF16
```

The model ID must match the id reported by oMLX `/v1/models` exactly. The verified served id is `mistralai_Devstral-Small-2-24B-Instruct-2512-MLX-BF16` (uppercase `BF16`).

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Tool-Calling Behaviour

Devstral Small 2 2512 BF16 uses the same Mistral tool-call format as the 6bit profile. The engine orchestrator owns the full tool dispatch loop; tool calls are parsed from model output and dispatched directly via the Python MCP SDK.

Thinking is disabled in oMLX per-model settings (`enable_thinking: false`). Devstral is not a reasoning model; keep thinking disabled for engine use.

**Prompt guidance — imperative phrasing:**

| Avoid | Prefer |
|---|---|
| `You can use the grep tool to search` | `Use the mcp-ripgrep__search tool to search` |
| `Search for X in the directory` | `Call mcp-ripgrep__search with pattern X and path Y` |

Name tools explicitly in recipe prompts.

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Engine

**Implementation:** engine orchestrator / loop

State directory: `ai/state/` (ephemeral, per-task)

**Prerequisites:**
- oMLX running on `localhost:8000`
- Engine dependencies installed: `pip install -r ai/engine/requirements.txt`
- `ai/config.yaml` configured with `default_model: mistralai_Devstral-Small-2-24B-Instruct-2512-MLX-BF16`

**Invocation:**

```bash
python ai/engine/src/orchestrator.py --mode loop --task ai/workspace/prompt/prompt-<uuid>-<n>.md
```

T03 prompts use `prompt_info.target_profile: engine`. Worker and reviewer roles are differentiated by prompt engineering within the same model, not by separate model binaries.

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Model Selection

| Role | Model | Quantisation | Approx. Memory |
|---|---|---|---|
| Worker | Devstral Small 2 2512 | BF16 | ~44 GB |
| Reviewer | Devstral Small 2 2512 | BF16 | ~44 GB |

**oMLX settings (as configured on 2026-10-02):**

| Setting | Value |
|---|---|
| Model context length (config) | 393,216 tokens |
| `max_context_window` (oMLX cap) | 40,960 tokens |
| `max_tokens` | 16,384 |
| `temperature` | 0.15 |
| `min_p` | 0.01 |
| `enable_thinking` | false |

The oMLX cap of 40,960 tokens governs the effective context and is lower than the 6bit model's served `max_model_len` (393,216). KV-cache memory grows with context and is additional to the resident weights.

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Project Setup

**.gitignore additions:**

```
# MLX profile - Worker and Reviewer
ai/state/
```

**Setup guide:** [Apple Silicon + MLX Setup Guide](../../docs/setup-apple-silicon-mlx.md).

[Return to Table of Contents](<#table of contents>)

---

## 9.0 Verification Status

This profile is provisional pending evaluation. Open items:

| Item | Status |
|---|---|
| oMLX served id matches `default_model` | Verified (`mistralai_Devstral-Small-2-24B-Instruct-2512-MLX-BF16`) |
| Resident memory footprint | Verified (44.00 GB actual, oMLX admin endpoint) |
| Hugging Face source repository exists | Verified (`mlx-community/mistralai_Devstral-Small-2-24B-Instruct-2512-MLX-BF16`) |
| Engine parser handles tool calls at BF16 | Unverified (expected identical to 6bit) |
| Thinking disabled in oMLX settings | Verified (`enable_thinking: false`, oMLX admin endpoint) |
| Throughput acceptable for engine loop at BF16 | Unverified |
| Measurable quality gain over 6bit profile | Unverified |

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-10-02 | Initial draft; provisional BF16 profile derived from mlx_devstral_small_2_2512_6bit.md 1.11. Facts verified against oMLX /v1/models, oMLX admin endpoint and Hugging Face model search |
| 0.2 | 2026-10-02 | Thinking disabled in oMLX: §5.0 note revised; §7.0 enable_thinking row added; §9.0 thinking item verified |

---

Copyright (c) 2026 William Watson. MIT License.
