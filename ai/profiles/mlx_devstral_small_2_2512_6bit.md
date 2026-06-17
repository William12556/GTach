Created: 2026 March 12

# Implementation Profile: Apple Silicon + MLX (Devstral Small 2 2512)

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

This profile maps governance abstract placeholders to Apple Silicon MLX-based local model tooling using Devstral Small 2 (December 2025 release). It requires Apple M-series hardware.

| Concern | Implementation |
|---|---|
| Strategic Domain | Claude Desktop (preferred) |
| Tactical Domain | Devstral Small 2 2512 6bit via oMLX + AEL |
| AEL mechanism | AEL orchestrator / Ralph Loop |

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Placeholder Mappings

| Placeholder | Resolved Value |
|---|---|
| `<tactical_context>` | `CLAUDE.md` |

`<tactical_config>/` and `<skills_dir>/` do not apply to this profile. AEL configuration is in `ai/ael/config.yaml`; recipes are in `ai/ael/recipes/`.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Strategic Domain

**Preferred implementation:** Claude Desktop

Any frontier model with sufficient reasoning capability may substitute. The Strategic Domain role requires: planning, governance interpretation, design creation, prompt authoring, and validation.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Tactical Domain

**Implementation:** Devstral Small 2 2512 6bit via oMLX + AEL orchestrator

**Hardware requirement:** Apple M-series chip; 24 GB unified memory minimum (6bit quantisation).

**Inference server:**

```bash
omlx serve --model-dir /path/to/ai-models
```

The server exposes an OpenAI-compatible endpoint at `http://localhost:8000/v1`.

**Model download:**

```python
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id="mlx-community/mistralai_Devstral-Small-2-24B-Instruct-2512-MLX-6Bit",
    local_dir="/path/to/ai-models/mistralai_Devstral-Small-2-24B-Instruct-2512-MLX-6Bit"
)
```

Use Python 3.11+. The `huggingface-cli` may be unreliable on some macOS configurations.

**AEL config** (`ai/ael/config.yaml`):

```yaml
omlx:
  base_url: http://127.0.0.1:8000/v1
  api_key: local
  default_model: mistralai_Devstral-Small-2-24B-Instruct-2512-MLX-6Bit
```

The model ID must match the id reported by oMLX `/v1/models` exactly, including the `mistralai_` prefix and `-MLX-6Bit` suffix.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Tool-Calling Behaviour

Devstral Small 2 2512 6bit via oMLX supports tool calling. The AEL orchestrator owns the full tool dispatch loop; tool calls are parsed from model output and dispatched directly via the Python MCP SDK.

**Prompt guidance — imperative phrasing:**

| Avoid | Prefer |
|---|---|
| `You can use the grep tool to search` | `Use the mcp-grep__grep tool to search` |
| `Search for X in the directory` | `Call mcp-grep__grep with pattern X and path Y` |

Name tools explicitly in recipe prompts.

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Autonomous Execution Loop

**Implementation:** AEL orchestrator / Ralph Loop

State directory: `ai/state/ralph/` (ephemeral, per-task)

**Prerequisites:**
- oMLX running on `localhost:8000`
- AEL dependencies installed: `pip install -r ai/ael/requirements.txt`
- `ai/ael/config.yaml` configured

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
| Worker | Devstral Small 2 2512 | 6bit | ~18 GB |
| Reviewer | Devstral Small 2 2512 | 6bit | ~18 GB |

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

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-03-12 | Initial document |
| 1.1 | 2026-06-14 | Relocated paths under ai/: state ai/state/ralph/, workspace/ → ai/workspace/, .gitignore additions |
| 1.2 | 2026-06-16 | Updated Q8 → 6bit throughout; corrected model download repo and local dir |
| 1.3 | 2026-06-16 | Placeholder Mappings: removed non-applicable <tactical_config>/ and <skills_dir>/ rows |
| 1.4 | 2026-06-16 | Renamed file Q8 → 6bit to match document content; removed AGENTS.md from Placeholder Mappings (unsupported elsewhere); corrected AEL config example to full model id verified against oMLX /v1/models (mistralai_Devstral-Small-2-24B-Instruct-2512-MLX-6Bit); corrected model download local_dir to match actual on-disk path convention; added section numbering |

---

Copyright (c) 2026 William Watson. MIT License.
