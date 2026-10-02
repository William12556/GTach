Created: 2026 April 30

# Implementation Profile: claude-omlx

---

## Table of Contents

- [1.0 Overview](<#1.0 overview>)
- [2.0 Placeholder Mappings](<#2.0 placeholder mappings>)
- [3.0 Planner](<#3.0 planner>)
- [4.0 Worker and Reviewer](<#4.0 worker and reviewer>)
- [5.0 Invocation](<#5.0 invocation>)
- [6.0 Project Setup](<#6.0 project setup>)
- [References](<#references>)
- [Version History](<#version history>)

---

## 1.0 Overview

This profile routes Claude Code CLI through the local oMLX inference server instead of the Anthropic API. It provides Claude Code tooling and invocation UX with Devstral as the underlying model. It is a manual worker/reviewer option alongside the engine profiles; providers carry equal weight and none is preferred (proposal-5bcd46ad D-16).

Claude Code fulfils both the worker and reviewer roles in a single manual pass. There is no automated engine loop; the human operator controls the workflow and performs the review gate.

| Concern | Implementation |
|---|---|
| Planner | Claude Desktop (preferred) |
| Worker and reviewer | Claude Code CLI → oMLX → Devstral |
| Execution | Manual — human invokes Claude Code per task; no engine loop |

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

## 3.0 Planner

**Preferred implementation:** Claude Desktop

Any frontier model with sufficient reasoning capability may substitute. The planner role requires: planning, governance interpretation, design creation, prompt authoring, and validation.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Worker and Reviewer

**Implementation:** Claude Code CLI redirected to oMLX via `ANTHROPIC_BASE_URL`

Configuration directory: `.claude/`

Context file: `CLAUDE.md` at project root (checked into git).

Local context file: `CLAUDE.local.md` at project root (`.gitignore`'d).

**Prerequisites:**
- oMLX running on `http://127.0.0.1:8000` with Devstral loaded
- Claude Code installed. Recommended (native installer): `curl -fsSL https://claude.ai/install.sh | bash`. Alternatives: `brew install --cask claude-code`, or `npm install -g @anthropic-ai/claude-code` (Node.js 22+) [1]
- No Anthropic account or API key required (local inference only)
- Mandatory validation skill provisioned (§6.0; governance P00.18)

**Note:** Claude Code must be invoked in a clean environment to prevent a persisted claude.ai session token from overriding `ANTHROPIC_BASE_URL`. Use `env -i` as shown in the invocation procedure below.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Invocation

Claude Code fulfils both the worker and reviewer roles in a single manual pass. There is no worker/reviewer cycle; the human operator performs the review gate.

**Procedure:**

1. Ensure oMLX is running with Devstral loaded.
2. Planner authors and approves the T03 prompt per the standard workflow, with `prompt_info.target_profile: claude_omlx`. A `tactical_brief` is not required for this profile.
3. Open a terminal in the project root.
4. Issue the following command, substituting the actual T03 file path:

```bash
env -i HOME="$HOME" PATH="$PATH" \
  ANTHROPIC_BASE_URL=http://127.0.0.1:8000 \
  ANTHROPIC_AUTH_TOKEN=local \
  claude "implement ai/workspace/prompt/prompt-<uuid>-<n>.md"
```

5. Claude Code reads the T03 prompt from disk and implements the task via Devstral.
6. The PostToolUse hook (§6.0) runs pytest for modified components after each edit.
7. The human operator reviews the result and accepts or requests changes.

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Project Setup

**.gitignore additions:**

```
# claude-omlx profile - Worker and Reviewer
CLAUDE.local.md
.claude/settings.local.json
.claude/commands/
```

`.claude/settings.json` is team-shared and git-tracked (governance P10.6).

**Directory structure additions (within project root):**

```
├── .claude/
│   ├── settings.json         # git-tracked; holds the PostToolUse hook
│   ├── settings.local.json   # gitignored
│   ├── hooks/
│   │   └── run-tests.sh      # git-tracked
│   └── validation/           # skill docs provisioned from ai/governance/software-engineering/skills/
├── CLAUDE.md
└── CLAUDE.local.md
```

**Mandatory skill (P00.18):** follow `ai/governance/software-engineering/skills/validation/run-tests.md` §2.0 to install `.claude/hooks/run-tests.sh` and merge its PostToolUse block into `.claude/settings.json`.

[Return to Table of Contents](<#table of contents>)

---

## References

[1] ANTHROPIC, 2026. *Claude Code: Advanced setup* [online]. Available from: https://code.claude.com/docs/en/setup [Accessed 29 September 2026].

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-04-30 | Initial document; claude-omlx as alternative tactical profile; Claude Code CLI routed through oMLX/Devstral; manual single-pass invocation via T04 file path |
| 1.1 | 2026-06-14 | workspace/ → ai/workspace/ in invocation example |
| 1.2 | 2026-06-16 | Added section numbering throughout |
| 1.3 | 2026-06-17 | Removed <tactical_config>/ and <skills_dir>/ placeholder rows from §2.0; added note that .claude/ is a native Claude Code directory |
| 1.4 | 2026-09-25 | change-5bcd46ad: layout and terminology migration (engine and governance paths; AEL → engine, Ralph Loop → loop, ael-mcp → engine-mcp) |
| 1.5 | 2026-09-29 | Aligned with claude-code 1.6: §1.0 D-16 wording and "Execution" row; §4.0 current install methods [1] and validation prerequisite; §5.0 target_profile claude_omlx and validation hook; §6.0 .gitignore corrected to settings.local.json (settings.json is tracked; governance P10.6), hooks/ and validation/ added, mandatory skill step; References added |
| 1.6 | 2026-10-01 | Terminology: Strategic Domain → planner, Tactical Domain → worker and reviewer (change-155cc014) |

---

Copyright (c) 2026 William Watson. MIT License.
