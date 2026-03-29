Created: 2026 March 12

# Implementation Profile: Apple Silicon + MLX (Devstral Small 2 2512)

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

This profile maps governance abstract placeholders to Apple Silicon MLX-based local model tooling using Devstral Small 2 (December 2025 release). It requires Apple M-series hardware.

| Concern | Implementation |
|---|---|
| Strategic Domain | Claude Desktop (preferred) |
| Tactical Domain | Devstral Small 2 2512 Q8 via oMLX + AEL |
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

**Implementation:** Devstral Small 2 2512 Q8 via oMLX + AEL orchestrator

**Hardware requirement:** Apple M-series chip; 24 GB unified memory minimum (Q8 quantisation).

**Inference server:**

```bash
omlx serve --model-dir /path/to/ai-models
```

The server exposes an OpenAI-compatible endpoint at `http://localhost:8000/v1`.

**Model download:**

```python
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id="mlx-community/mistralai_Devstral-Small-2-24B-Instruct-2512-MLX-8Bit",
    local_dir="/path/to/ai-models/mlx-community/devstral-small-2-q8"
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

Devstral Small 2 2512 Q8 via oMLX supports tool calling. The AEL orchestrator owns the full tool dispatch loop; tool calls are parsed from model output and dispatched directly via the Python MCP SDK.

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

| Role | Model | Quantisation | Approx. Memory |
|---|---|---|---|
| Worker | Devstral Small 2 2512 | Q8 | ~24 GB |
| Reviewer | Devstral Small 2 2512 | Q8 | ~24 GB |

[Return to Table of Contents](<#table of contents>)

---

## Project Setup

**.gitignore additions:**

```
# MLX profile - Tactical Domain
.ael/ralph/
```

**Setup guide:** [Apple Silicon + MLX Setup Guide](../../../docs/setup-apple-silicon-mlx.md).

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-03-12 | Initial document |

---

Copyright (c) 2025 William Watson. This work is licensed under the MIT License.
