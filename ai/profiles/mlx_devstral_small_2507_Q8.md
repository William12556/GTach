Created: 2026 March 06

# Implementation Profile: Apple Silicon + MLX

---

## Table of Contents

- [Overview](<#overview>)
- [Placeholder Mappings](<#placeholder mappings>)
- [Strategic Domain](<#strategic domain>)
- [Tactical Domain](<#tactical domain>)
- [Tool-Calling Behaviour](<#tool-calling behaviour>)
- [Autonomous Execution Loop](<#autonomous execution loop>)
- [Model Selection](<#model selection>)
- [Project Setup](<#project setup>)
- [Version History](<#version history>)

---

## Overview

This profile maps governance abstract placeholders to Apple Silicon MLX-based local model tooling. It requires Apple M-series hardware.

| Concern | Implementation |
|---|---|
| Strategic Domain | Claude Desktop (preferred) |
| Tactical Domain | Devstral Q8 via oMLX + AEL |
| AEL mechanism | AEL orchestrator / Ralph Loop |

[Return to Table of Contents](<#table of contents>)

---

## Placeholder Mappings

| Placeholder | Resolved Value |
|---|---|
| `<tactical_config>/` | `ai/ael/` |
| `<skills_dir>/` | `ai/ael/recipes/` |
| `<tactical_context>` | `CLAUDE.md` or `AGENTS.md` |
| Local context file | Not applicable |

[Return to Table of Contents](<#table of contents>)

---

## Strategic Domain

**Preferred implementation:** Claude Desktop

Any frontier model with sufficient reasoning capability may substitute. The Strategic Domain role requires: planning, governance interpretation, design creation, prompt authoring, and validation.

[Return to Table of Contents](<#table of contents>)

---

## Tactical Domain

**Implementation:** Devstral Small 2507 Q8 via oMLX + AEL orchestrator

**Hardware requirement:** Apple M-series chip; 24 GB unified memory minimum (Q8 quantisation).

**Inference server:**

```bash
omlx serve --model-dir /path/to/ai-models
```

The server exposes an OpenAI-compatible endpoint at `http://localhost:8000/v1`.

Note: The HuggingFace repository name contains a typo (`Devstral-Samll-2507-8bit`). Use the exact string shown above.

**Model download:**

```python
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id="mlx-community/Devstral-Samll-2507-8bit",
    local_dir="/path/to/ai-models/mlx-community/devstral-q8"
)
```

Use Python 3.11+. The `huggingface-cli` may be unreliable on some macOS configurations.

**AEL config** (`ai/ael/config.yaml`):

```yaml
omlx:
  base_url: http://127.0.0.1:8000/v1
  api_key: local
  default_model: Devstral-Small-2-24B-Instruct-2512
```

[Return to Table of Contents](<#table of contents>)

---

## Tool-Calling Behaviour

Devstral Small 2507 Q8 via oMLX supports tool calling. The AEL orchestrator owns the full tool dispatch loop; tool calls are parsed from model output and dispatched directly via the Python MCP SDK.

**Prompt guidance — imperative phrasing:**

| Avoid | Prefer |
|---|---|
| `You can use the grep tool to search` | `Use the mcp-grep__grep tool to search` |
| `Search for X in the directory` | `Call mcp-grep__grep with pattern X and path Y` |

Name tools explicitly in recipe prompts.

[Return to Table of Contents](<#table of contents>)

---

## Autonomous Execution Loop

**Implementation:** AEL orchestrator / Ralph Loop

State directory: `.ael/ralph/` (ephemeral, per-task)

**Prerequisites:**
- oMLX running on `localhost:8000`
- AEL dependencies installed: `pip install -r ai/ael/requirements.txt`
- `ai/ael/config.yaml` configured

**Invocation:**

```bash
python ai/ael/src/orchestrator.py --mode loop --task workspace/prompt/prompt-<uuid>-<n>.md
```

Worker and reviewer roles are differentiated by prompt engineering within the same model, not by separate model binaries.

[Return to Table of Contents](<#table of contents>)

---

## Model Selection

| Role | Model | Quantisation | Approx. VRAM |
|---|---|---|---|
| Worker | Devstral Small 2507 | Q8 | ~24 GB |
| Reviewer | Devstral Small 2507 | Q8 | ~24 GB |

BF16 may be used on hardware with 48 GB+ unified memory for higher fidelity.

[Return to Table of Contents](<#table of contents>)

---

## Project Setup

**.gitignore additions:**

```
# MLX profile - Tactical Domain
.ael/ralph/
```

**Setup guide:** See `framework/ai/doc/examples/` and [Apple Silicon + MLX Setup Guide](../../../docs/setup-apple-silicon-mlx.md).

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-03-06 | Initial document |
| 1.1 | 2026-03-06 | Replaced mlx_lm.server with oMLX as primary inference server; updated port references to 8000 |
| 1.2 | 2026-03-06 | Corrected API key values: oMLX requires authentication for all requests; updated api_key and OPENAI_API_KEY to `local` |
| 1.3 | 2026-03-11 | Replaced Goose with AEL orchestrator throughout; updated Tactical Domain, Placeholder Mappings, AEL section, Project Setup; removed OLLama cross-reference |

---

Copyright (c) 2025 William Watson. This work is licensed under the MIT License.
