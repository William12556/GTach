Created: 2026 March 11

# AEL — Autonomous Execution Loop

---

## Table of Contents

- [1.0 Overview](<#1.0 overview>)
- [2.0 Tactical Profiles](<#2.0 tactical profiles>)
- [3.0 Structure](<#3.0 structure>)
- [4.0 Requirements](<#4.0 requirements>)
- [5.0 Installation](<#5.0 installation>)
- [6.0 Configuration](<#6.0 configuration>)
- [7.0 Usage](<#7.0 usage>)
- [8.0 Recipes](<#8.0 recipes>)
- [9.0 Testing](<#9.0 testing>)
- [Version History](<#version history>)

---

## 1.0 Overview

The AEL orchestrator is a standalone Python tool loop implementing the Ralph Loop pattern. It connects directly to MCP servers, sends tool definitions to an oMLX inference endpoint, parses model tool calls in both OpenAI and Mistral plain-text formats, dispatches tools, injects results into message history, and iterates until the model produces a response containing no tool calls.

This component replaces Goose as the Autonomous Execution Loop (AEL) for the oMLX/Devstral stack. It addresses the tool dispatch failure present in oMLX and other inference servers by owning the full tool loop externally.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Tactical Profiles

Three Tactical Domain profiles are available. AEL is the primary profile; the others are manual alternatives.

| Aspect | AEL (Primary) | Claude Code | claude-omlx |
|---|---|---|---|
| Execution | Automated Ralph Loop | Manual, human-directed | Manual, human-directed |
| Worker/Reviewer | Automated cycle | Single pass; human reviews | Single pass; human reviews |
| Inference | oMLX → Devstral (local) | Anthropic API → Claude Sonnet | oMLX → Devstral via Claude Code CLI |
| Loop control | `orchestrator.py` | Human operator | Human operator |
| Context file | `config.yaml` | `CLAUDE.md` | `CLAUDE.md` |
| State directory | `ai/state/ralph/` | `.claude/` | `.claude/` |
| Profile | `mlx_devstral_small_2_2512_6bit.md` | `claude.md` | `claude-omlx.md` |

See `ai/profiles/` for profile documents.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Structure

```
ael/
├── config.yaml           # Inference endpoint, MCP server definitions, loop control
├── requirements.txt      # Python dependencies
├── recipes/
│   ├── ralph-work.yaml   # Standard worker role system prompt
│   ├── ralph-review.yaml # Standard reviewer role system prompt
│   ├── audit-work.yaml   # Audit worker role system prompt (read-only analysis)
│   └── audit-review.yaml # Audit reviewer role system prompt (coverage + quality)
└── src/
    ├── orchestrator.py     # Main loop and CLI entry point (--mode worker|reviewer|loop|reset)
    ├── budget.py           # Context budget calculator (run before authoring T04 prompts)
    ├── mcp_client.py       # MCP stdio connection and tool dispatch
    ├── parser.py           # Mistral [TOOL_CALLS] plain-text parser
    ├── linter.py            # Layer 1 governance linter: static validation of workspace documents (naming, structure, YAML fields, UUID coupling, Obsidian links)
    └── protocol_checker.py  # Layer 2 protocol checker: multi-document workflow invariant validation (UUID chain integrity, bidirectional coupling, one-to-one constraints, status consistency, lifecycle placement, prompt self-containment)
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Requirements

- Python 3.11+
- oMLX running on `http://127.0.0.1:8000`
- MCP servers configured in `config.yaml`
- Model: Devstral Small 2 (6bit) — purpose-built for agentic coding and multi-file editing; the AEL parser (`parser.py`) is tuned to Mistral's tool-call format, which Devstral uses natively

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Installation

Install dependencies into the project virtual environment:

```bash
pip install -r ai/ael/requirements.txt
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Configuration

Edit `ai/ael/config.yaml`:

```yaml
omlx:
  base_url: "http://127.0.0.1:8000/v1"
  api_key: "local"
  default_model: "<model-name>"

mcp_servers:
  filesystem:
    command: "/usr/local/bin/npx"
    args:
      - "-y"
      - "@j0hanz/filesystem-mcp@latest"
      - "<allowed-path>"
    env:
      PATH: "/opt/homebrew/opt/node@24/bin:/usr/local/bin:/usr/bin:/bin"

loop:
  max_iterations: 10
  state_dir: "ai/state/ralph"

context:
  models_dir: "~/ai-models"   # set to your local model storage path
  context_window: null        # null = read from model config.json on disk
  budget_warn_pct: 0.80
  budget_abort_pct: 0.95
```

**`context.models_dir`** must be updated to point to your local model storage directory. `budget.py` searches this directory for the model's `config.json` to determine the context window size. If your model is remote or the path cannot be resolved, set `context.context_window` to an explicit integer value instead.

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Usage

```bash
# Generate context budget report (run once at setup and after model changes)
python ai/ael/src/budget.py

# Single worker pass
python ai/ael/src/orchestrator.py --mode worker --task ai/workspace/prompt/prompt-abc123.md

# Single reviewer pass
python ai/ael/src/orchestrator.py --mode reviewer --task ai/workspace/prompt/prompt-abc123.md

# Full Ralph Loop (worker + reviewer cycle)
python ai/ael/src/orchestrator.py --mode loop --task ai/workspace/prompt/prompt-abc123.md
python ai/ael/src/orchestrator.py --mode loop --task "implement the login module"

# Reset AEL state after human acceptance
python ai/ael/src/orchestrator.py --mode reset
```

| Flag | Purpose |
|---|---|
| `--mode` | `worker` \| `reviewer` \| `loop` \| `reset` (default: `loop`) |
| `--task` | Task string or path to task file |
| `--model` | Model for all phases (overrides config default) |
| `--worker-model` | Model for work phase only (loop mode) |
| `--reviewer-model` | Model for review phase only (loop mode) |
| `--max-iterations` | Outer Ralph cycle limit override |
| `--duration` | Wall-clock time limit in hours (default: no limit) |
| `--config` | Path to config.yaml |

**`budget.py`** reads `config.yaml` and the model's `config.json` from disk to compute context window size, warn/abort thresholds, and recommended `tactical_brief` sizing. It writes `ai/state/ralph/context-budget.md`. The Strategic Domain reads this file before authoring any T04 prompt. If the file is absent, the Strategic Domain will instruct the human to run `budget.py` before proceeding.

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Recipes

Recipes are YAML files providing role-specific system prompts. The `instructions` field is injected as the system prompt for each inference call.

| Recipe | Role | Purpose |
|---|---|---|
| `ralph-work.yaml` | Worker | Makes incremental progress on a code generation task |
| `ralph-review.yaml` | Reviewer | Evaluates work and outputs `SHIP` or `REVISE` |
| `audit-work.yaml` | Audit worker | Read-only codebase analysis; accumulates findings in `audit-report.md` |
| `audit-review.yaml` | Audit reviewer | Checks finding quality and coverage; outputs `SHIP` or `REVISE` |

State files are written to `ai/state/ralph/` in the project root during loop execution. This directory is ephemeral and excluded from git.

[Return to Table of Contents](<#table of contents>)

---

## 9.0 Testing

The `tests/` directory has been removed from the active `ai/ael/` structure. Test source files are retained in `deprecated/skel/ai/ael/tests/` for reference.

To run tests, copy the tests directory from the deprecated skel:

```bash
cp -r deprecated/skel/ai/ael/tests ai/ael/tests
```

Then run:

```bash
# All tests
python3.11 -m pytest ai/ael/tests/ -v

# Unit tests only (no oMLX required)
python3.11 -m pytest ai/ael/tests/test_parser.py -v

# Integration tests only
python3.11 -m pytest ai/ael/tests/test_integration.py -v
```

Integration tests skip automatically if oMLX is not reachable on `127.0.0.1:8000`.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-03-11 | Initial implementation; replaces Goose AEL; direct MCP + oMLX tool loop |
| 1.1 | 2026-03-11 | Merged ralph-loop.sh into orchestrator.py; added --mode worker\|reviewer\|loop; removed shell script |
| 1.2 | 2026-03-11 | Added tests/ directory: test_parser.py (unit), test_integration.py (Layers 2–4); added Testing section |
| 1.3 | 2026-03-20 | Added budget.py; added --mode reset; updated Configuration and Usage sections; context.models_dir note |
| 1.4 | 2026-03-25 | Added `format_tool_signatures()` to orchestrator.py: injects tool parameter signatures into `{{TOOLS}}` system prompt placeholder to prevent model tool-call hallucination |
| 1.5 | 2026-03-25 | Added `mcp-grep` server to `config.yaml` MCP server definitions |
| 1.6 | 2026-03-31 | Added Devstral model requirement with rationale to Requirements section |
| 1.7 | 2026-04-30 | Updated canonical model quantisation from Q8 to 6bit; memory constraints on M4 Mac Mini (64GB) preclude Q8 with adequate KV headroom |
| 1.8 | 2026-04-30 | Added Tactical Profiles section with comparison table |
| 1.9 | 2026-06-02 | Added audit-work.yaml and audit-review.yaml to Structure and Recipes; added `--duration` and `--max-iterations` to CLI flags table |
| 2.0 | 2026-06-14 | Relocated loop state to ai/state/ralph/ (config.yaml, profile table, usage examples); workspace/ → ai/workspace/ in command examples |
| 2.1 | 2026-06-16 | Updated Testing section: removed stale framework/ pytest paths; tests moved to deprecated/skel/; updated Configuration note |
| 2.2 | 2026-06-16 | Added linter.py and protocol_checker.py to §3.0 Structure; updated §2.0 profile filename reference: mlx_devstral_small_2_2512_Q8.md → mlx_devstral_small_2_2512_6bit.md; added section numbering throughout; added Created timestamp |

---

Copyright (c) 2026 William Watson. MIT License.
