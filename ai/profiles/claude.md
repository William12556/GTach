Created: 2026 March 31

# Implementation Profile: Claude Code (Optional)

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

This profile maps governance abstract placeholders to Claude Code tooling. It is an optional alternative to the MLX/Devstral profile, intended for use when the local inference stack is unavailable.

Claude Code fulfils both the worker and reviewer roles in a single manual pass. There is no automated AEL loop; the human operator controls the workflow and performs the review gate.

| Concern | Implementation |
|---|---|
| Strategic Domain | Claude Desktop (preferred) |
| Tactical Domain | Claude Code |
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

**Implementation:** Claude Code

Configuration directory: `.claude/`

Context file: `CLAUDE.md` at project root (checked into git).

Local context file: `CLAUDE.local.md` at project root (`.gitignore`'d).

**Prerequisites:**
- Anthropic API key configured
- Claude Code installed: `npm install -g @anthropic-ai/claude-code`

[Return to Table of Contents](<#table of contents>)

---

## Invocation

Claude Code fulfils both the worker and reviewer roles in a single manual pass. There is no worker/reviewer cycle; the human operator performs the review gate.

**Procedure:**

1. Strategic Domain authors and approves the T04 prompt per the standard workflow.
2. Open Claude Code in the project root.
3. Issue the following instruction, substituting the actual T04 file path:

```
implement workspace/prompt/prompt-<uuid>-<n>.md
```

4. Claude Code reads the T04 prompt from disk and implements the task.
5. The human operator reviews the result and accepts or requests changes.

[Return to Table of Contents](<#table of contents>)

---

## Project Setup

**.gitignore additions:**

```
# Claude Code profile - Tactical Domain
CLAUDE.local.md
.claude/settings.json
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
| 1.0 | 2026-03-31 | Initial document; Claude Code as optional alternative to MLX/Devstral profile; manual single-pass invocation via T04 file path |

---

Copyright (c) 2025 William Watson. This work is licensed under the MIT License.
