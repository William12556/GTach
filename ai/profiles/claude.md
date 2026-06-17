Created: 2026 March 31

# Implementation Profile: Claude Code (Optional)

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

This profile maps governance abstract placeholders to Claude Code tooling. It is an optional alternative to the MLX/Devstral profile, intended for use when the local inference stack is unavailable.

Claude Code fulfils both the worker and reviewer roles in a single manual pass. There is no automated AEL loop; the human operator controls the workflow and performs the review gate.

| Concern | Implementation |
|---|---|
| Strategic Domain | Claude Desktop (preferred) |
| Tactical Domain | Claude Code |
| AEL mechanism | Manual — human invokes Claude Code per task |

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Placeholder Mappings

| Placeholder | Resolved Value |
|---|---|
| `<tactical_context>` | `CLAUDE.md` |
| Local context file | `CLAUDE.local.md` |

`.claude/` is the native Claude Code configuration directory; it is not a framework placeholder.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Strategic Domain

**Preferred implementation:** Claude Desktop

Any frontier model with sufficient reasoning capability may substitute. The Strategic Domain role requires: planning, governance interpretation, design creation, prompt authoring, and validation.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Tactical Domain

**Implementation:** Claude Code

Configuration directory: `.claude/`

Context file: `CLAUDE.md` at project root (checked into git).

Local context file: `CLAUDE.local.md` at project root (`.gitignore`'d).

**Prerequisites:**
- Anthropic API key configured
- Claude Code installed: `npm install -g @anthropic-ai/claude-code`

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Invocation

Claude Code fulfils both the worker and reviewer roles in a single manual pass. There is no worker/reviewer cycle; the human operator performs the review gate.

**Procedure:**

1. Strategic Domain authors and approves the T04 prompt per the standard workflow.
2. Open Claude Code in the project root.
3. Issue the following instruction, substituting the actual T04 file path:

```
implement ai/workspace/prompt/prompt-<uuid>-<n>.md
```

4. Claude Code reads the T04 prompt from disk and implements the task.
5. The human operator reviews the result and accepts or requests changes.

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Project Setup

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
| 1.1 | 2026-06-14 | workspace/ → ai/workspace/ in invocation example |
| 1.2 | 2026-06-16 | Added section numbering throughout |
| 1.3 | 2026-06-17 | Removed <tactical_config>/ and <skills_dir>/ placeholder rows from §2.0; added note that .claude/ is a native Claude Code directory |

---

Copyright (c) 2026 William Watson. MIT License.
