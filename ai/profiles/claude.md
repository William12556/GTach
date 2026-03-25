Created: 2026 February 18

# Implementation Profile: Claude

---

## Table of Contents

- [Overview](<#overview>)
- [Placeholder Mappings](<#placeholder mappings>)
- [Strategic Domain](<#strategic domain>)
- [Tactical Domain](<#tactical domain>)
- [Autonomous Execution Loop](<#autonomous execution loop>)
- [Project Setup](<#project setup>)
- [Version History](<#version history>)

---

## Overview

This profile maps governance abstract placeholders to Claude-based tooling.

| Concern | Implementation |
|---|---|
| Strategic Domain | Claude Desktop (preferred) |
| Tactical Domain | Claude Code |
| AEL mechanism | Goose / Ralph Loop |

[Return to Table of Contents](<#table of contents>)

---

## Placeholder Mappings

| Placeholder | Resolved Value |
|---|---|
| `<tactical_config>/` | `.claude/` |
| `<skills_dir>/` | `skills/` (within `.claude/`) |
| `<tactical_context>` | `CLAUDE.md` |
| Local context file | `CLAUDE.local.md` |

[Return to Table of Contents](<#table of contents>)

---

## Strategic Domain

**Preferred implementation:** Claude Desktop

Any frontier model with sufficient reasoning capability may substitute. The Strategic Domain role requires: planning, governance interpretation, design creation, prompt authoring, and validation.

Context file update mechanism: `# key` during Claude Code sessions updates `CLAUDE.md` in place.

[Return to Table of Contents](<#table of contents>)

---

## Tactical Domain

**Implementation:** Claude Code

Configuration directory: `.claude/`

Skills directory: `.claude/skills/`

Context file: `CLAUDE.md` at project root (checked into git).

Local context file: `CLAUDE.local.md` at project root (`.gitignore`'d).

**Prerequisites:**
- Anthropic API key configured
- Claude Code installed: `npm install -g @anthropic-ai/claude-code`

[Return to Table of Contents](<#table of contents>)

---

## Autonomous Execution Loop

**Implementation:** Goose / Ralph Loop

State directory: `.goose/ralph/` (ephemeral, per-task)

**Prerequisites:**
- Goose installed: `pip install goose-ai` or per Goose documentation
- Ralph Loop recipe: `~/.config/goose/recipes/ralph-loop.sh`

**Invocation:**
```bash
~/.config/goose/recipes/ralph-loop.sh ./workspace/prompt/prompt-<uuid>-<n>.md
```

[Return to Table of Contents](<#table of contents>)

---

## Project Setup

**.gitignore additions:**
```
# Claude profile - Tactical Domain
CLAUDE.local.md
.claude/settings.json
.goose/ralph/
```

**Directory structure additions (within `<project name>/`):**
```
├── .claude/
│   ├── skills/
│   │   ├── governance/
│   │   ├── testing/
│   │   ├── validation/
│   │   └── audit/
│   └── commands/
├── CLAUDE.md
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-02-18 | Initial document |

---

Copyright (c) 2025 William Watson. This work is licensed under the MIT License.
