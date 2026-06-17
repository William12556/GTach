Created: 2026 April 30

# Implementation Profile: claude-omlx

---

## Table of Contents

- [1.0 Overview](<#1.0 overview>)
- [2.0 Placeholder Mappings](<#2.0 placeholder mappings>)
- [3.0 Strategic Domain](<#3.0 strategic domain>)
- [4.0 Tactical Domain](<#4.0 tactical domain>)
- [5.0 Invocation](<#5.0 invocation>)
- [6.0 Project Setup](<#6.0 project setup>)
- [Version History](<#version history>)

---

## 1.0 Overview

This profile routes Claude Code CLI through the local oMLX inference server instead of the Anthropic API. It provides Claude Code tooling and invocation UX with Devstral as the underlying model.

Claude Code fulfils both the worker and reviewer roles in a single manual pass. There is no automated AEL loop; the human operator controls the workflow and performs the review gate.

| Concern | Implementation |
|---|---|
| Strategic Domain | Claude Desktop (preferred) |
| Tactical Domain | Claude Code CLI → oMLX → Devstral |
| AEL mechanism | Manual — human invokes Claude Code per task |

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Placeholder Mappings

| Placeholder | Resolved Value |
|---|---|
| `<tactical_config>/` | `.claude/` |
| `<skills_dir>/` | `.claude/` |
| `<tactical_context>` | `CLAUDE.md` |
| Local context file | `CLAUDE.local.md` |

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Strategic Domain

**Preferred implementation:** Claude Desktop

Any frontier model with sufficient reasoning capability may substitute. The Strategic Domain role requires: planning, governance interpretation, design creation, prompt authoring, and validation.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Tactical Domain

**Implementation:** Claude Code CLI redirected to oMLX via `ANTHROPIC_BASE_URL`

Configuration directory: `.claude/`

Context file: `CLAUDE.md` at project root (checked into git).

Local context file: `CLAUDE.local.md` at project root (`.gitignore`'d).

**Prerequisites:**
- oMLX running on `http://127.0.0.1:8000` with Devstral loaded
- Claude Code installed: `npm install -g @anthropic-ai/claude-code`
- No Anthropic API key required (local inference only)

**Note:** Claude Code must be invoked in a clean environment to prevent a persisted claude.ai session token from overriding `ANTHROPIC_BASE_URL`. Use `env -i` as shown in the invocation procedure below.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Invocation

Claude Code fulfils both the worker and reviewer roles in a single manual pass. There is no worker/reviewer cycle; the human operator performs the review gate.

**Procedure:**

1. Ensure oMLX is running with Devstral loaded.
2. Strategic Domain authors and approves the T04 prompt per the standard workflow.
3. Open a terminal in the project root.
4. Issue the following command, substituting the actual T04 file path:

```bash
env -i HOME="$HOME" PATH="$PATH" \
  ANTHROPIC_BASE_URL=http://127.0.0.1:8000 \
  ANTHROPIC_AUTH_TOKEN=local \
  claude "implement ai/workspace/prompt/prompt-<uuid>-<n>.md"
```

5. Claude Code reads the T04 prompt from disk and implements the task via Devstral.
6. The human operator reviews the result and accepts or requests changes.

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Project Setup

**.gitignore additions:**

```
# claude-omlx profile - Tactical Domain
CLAUDE.local.md
.claude/settings.json
.claude/commands/
```

**Directory structure additions (within project root):**

```
├── .claude/
│   └── settings.json
├── CLAUDE.md
└── CLAUDE.local.md
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-04-30 | Initial document; claude-omlx as alternative tactical profile; Claude Code CLI routed through oMLX/Devstral; manual single-pass invocation via T04 file path |
| 1.1 | 2026-06-14 | workspace/ → ai/workspace/ in invocation example |
| 1.2 | 2026-06-16 | Added section numbering throughout |

---

Copyright (c) 2026 William Watson. MIT License.
