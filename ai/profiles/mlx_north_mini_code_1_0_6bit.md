Created: 2026 June 26

# Implementation Profile: Apple Silicon + MLX (North Mini Code 1.0)

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
- [9.0 Verification Status](<#9.0 verification status>)
- [Version History](<#version history>)

---

## 1.0 Overview

This profile maps governance abstract placeholders to Apple Silicon MLX-based local model tooling using North Mini Code 1.0 (Cohere2 mixture-of-experts architecture; 30B total parameters, 3B active). It requires Apple M-series hardware. Licence: Apache 2.0. This profile is provisional; the model is under evaluation as a Tactical Domain. See [9.0 Verification Status](<#9.0 verification status>).

| Concern | Implementation |
|---|---|
| Strategic Domain | Claude Desktop (preferred) |
| Tactical Domain | North Mini Code 1.0 6bit via oMLX + AEL |
| AEL mechanism | AEL orchestrator / Ralph Loop |

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

**Implementation:** North Mini Code 1.0 6bit via oMLX + AEL orchestrator

**Architecture:** Cohere2 mixture-of-experts (`cohere2_moe`); 30B total parameters, 3B active; 128 experts, 8 active per token.

**Licence:** Apache 2.0 (Cohere). Official model card: `CohereLabs/North-Mini-Code-1.0`. The on-disk 6bit weights are a community MLX conversion.

**Hardware requirement:** Apple M-series chip; 32 GB unified memory minimum (~25 GB resident at 6bit per oMLX estimate).

**Inference server:**

```bash
omlx serve --model-dir /path/to/ai-models
```

The server exposes an OpenAI-compatible endpoint at `http://localhost:8000/v1`.

**Model location:**

Resident at `ai-models/mlx-community/North-Mini-Code-1.0-6bit`. To re-acquire:

```python
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id="mlx-community/North-Mini-Code-1.0-6bit",
    local_dir="/path/to/ai-models/mlx-community/North-Mini-Code-1.0-6bit"
)
```

Use Python 3.11+. The `huggingface-cli` may be unreliable on some macOS configurations.

**AEL config** (`ai/ael/config.yaml`):

```yaml
omlx:
  base_url: http://127.0.0.1:8000/v1
  api_key: local
  default_model: North-Mini-Code-1.0-6bit
```

The model ID must match the id reported by oMLX `/v1/models` exactly. The verified served id is `North-Mini-Code-1.0-6bit`.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Tool-Calling Behaviour

North Mini Code 1.0 emits tool calls in the Cohere action format — `<|START_ACTION|>` / `<|END_ACTION|>` blocks containing a JSON array of objects with `tool_name` and `parameters` keys. This differs from the Mistral/Devstral tool-call format the AEL orchestrator parser was validated against.

The model also emits reasoning output in `<|START_THINKING|>` / `<|END_THINKING|>` blocks; thinking is enabled by default (`enable_thinking: true`). The orchestrator must separate thinking output from action blocks.

Parser compatibility is **unverified** for this profile. Confirm that the orchestrator correctly parses Cohere-format action blocks and ignores thinking blocks before relying on this profile for execution. See [9.0 Verification Status](<#9.0 verification status>).

**Prompt guidance — imperative phrasing** (as for all tactical profiles):

| Avoid | Prefer |
|---|---|
| `You can use the grep tool to search` | `Use the mcp-ripgrep__search tool to search` |
| `Search for X in the directory` | `Call mcp-ripgrep__search with pattern X and path Y` |

Name tools explicitly in recipe prompts.

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Autonomous Execution Loop

**Implementation:** AEL orchestrator / Ralph Loop

State directory: `ai/state/ralph/` (ephemeral, per-task)

**Prerequisites:**
- oMLX running on `localhost:8000`
- AEL dependencies installed: `pip install -r ai/ael/requirements.txt`
- `ai/ael/config.yaml` configured with `default_model: North-Mini-Code-1.0-6bit`

**Invocation:**

```bash
python ai/ael/src/orchestrator.py --mode loop --task ai/workspace/prompt/prompt-<uuid>-<n>.md
```

Worker and reviewer roles are differentiated by prompt engineering within the same model, not by separate model binaries.

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Model Selection

| Role | Model | Quantisation | Approx. Memory |
|---|---|---|---|
| Worker | North Mini Code 1.0 | 6bit | ~25 GB |
| Reviewer | North Mini Code 1.0 | 6bit | ~25 GB |

Context window: 256K tokens (Cohere specification; 64K maximum generation). The model `config.json` reports `max_position_embeddings` 500000, and oMLX sets no explicit context cap; 256K is the supported figure.

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Project Setup

**.gitignore additions:**

```
# MLX profile - Tactical Domain
ai/state/ralph/
```

**Setup guide:** [Apple Silicon + MLX Setup Guide](../../../docs/setup-apple-silicon-mlx.md).

[Return to Table of Contents](<#table of contents>)

---

## 9.0 Verification Status

This profile is provisional pending evaluation. Open items:

| Item | Status |
|---|---|
| oMLX served id matches `default_model` | Verified (`North-Mini-Code-1.0-6bit`) |
| Resident memory footprint | Verified (~25 GB, oMLX estimate) |
| Licence | Verified (Apache 2.0, Cohere blog 2026-06-09) |
| AEL parser handles Cohere action-block tool calls | Unverified |
| Orchestrator separates thinking blocks from action blocks | Unverified |
| Worker/reviewer prompt engineering effective with this model | Unverified |
| `vlm` engine path behaviour under AEL load | Unverified |

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-06-26 | Initial draft; provisional profile for North Mini Code 1.0 6bit under evaluation as Tactical Domain. Facts verified against oMLX admin endpoint and on-disk model config |
| 0.2 | 2026-06-26 | Added Apache 2.0 licence, 30B/3B parameter figures, official CohereLabs card reference; corrected context 500K → 256K per Cohere specification |
| 0.3 | 2026-07-16 | Tool-guidance example: mcp-grep__grep → mcp-ripgrep__search |

---

Copyright (c) 2026 William Watson. MIT License.
