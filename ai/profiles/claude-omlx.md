Created: 2026 April 30

# Implementation Profile: claude-omlx

---

## Table of Contents

- [Overview](<#overview>)
- [Placeholder Mappings](<#placeholder mappings>)
- [Strategic Domain](<#strategic domain>)
- [Tactical Domain](<#tactical domain>)
- [Invocation](<#invocation>)
- [Project Setup](<#project setup>)
- [Version History](<#version history>)

---

## Overview

This profile routes Claude Code CLI through the local oMLX inference server instead of the Anthropic API. It provides Claude Code tooling and invocation UX with Devstral as the underlying model.

Claude Code fulfils both the worker and reviewer roles in a single manual pass. There is no automated AEL loop; the human operator controls the workflow and performs the review gate.

| Concern | Implementation |
|---|---|
| Strategic Domain | Claude Desktop (preferred) |
| Tactical Domain | Claude Code CLI → oMLX → Devstral |
| AEL mechanism | Manual — human invokes Claude Code per task |

[Return to Table of Contents](<#table of contents>)

---

## Placeholder Mappings

| Placeholder | Resolved Value |
|---|---|
| `<tactical_config>/` | `.claude/` |
| `<skills_dir>/` | `.claude/` |
| `<tactical_context>` | `CLAUDE.md` |
| Local context file | `CLAUDE.local.md` |

[Return to Table of Contents](<#table of contents>)

---

## Strategic Domain

**Preferred implementation:** Claude Desktop

Any frontier model with sufficient reasoning capability may substitute. The Strategic Domain role requires: planning, governance interpretation, design creation, prompt authoring, and validation.

[Return to Table of Contents](<#table of contents>)

---

## Tactical Domain

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

## Invocation

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
  claude "implement workspace/prompt/prompt-<uuid>-<n>.md"
```

5. Claude Code reads the T04 prompt from disk and implements the task via Devstral.
6. The human operator reviews the result and accepts or requests changes.

[Return to Table of Contents](<#table of contents>)

---

## Project Setup

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

---

Copyright (c) 2026 William Watson. MIT License.
