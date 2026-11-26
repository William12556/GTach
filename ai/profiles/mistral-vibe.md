Created: 2026 November 14

# Implementation Profile: Mistral Vibe (Optional)

---

## Table of Contents

- [1.0 Overview](#10-overview)
- [2.0 Placeholder Mappings](#20-placeholder-mappings)
- [3.0 Planner](#30-planner)
- [4.0 Worker and Reviewer](#40-worker-and-reviewer)
- [5.0 Vibe Task Invocation](#50-vibe-task-invocation)
- [6.0 Project Setup](#60-project-setup)
- [7.0 Verification Status](#70-verification-status)
- [References](#references)
- [Version History](#version-history)

---

## 1.0 Overview

This profile maps governance abstract placeholders to Mistral Vibe, the command-line coding agent of Mistral AI [1]. It is a manual worker/reviewer option alongside `claude-code.md` and the engine profiles; providers carry equal weight and none is preferred (proposal-5bcd46ad D-16).

Vibe fulfils both the worker and reviewer roles in a single manual pass. There is no automated engine loop; the human operator controls the workflow and performs the review gate.

| Concern | Implementation |
|---|---|
| Planner | Not prescribed (§3.0) |
| Worker and reviewer | Mistral Vibe |
| Execution | Manual — human invokes Vibe per task; no engine loop |

This profile is written from the Vibe documentation and has not been run against a project (§7.0).

[Return to Table of Contents](#table-of-contents)

---

## 2.0 Placeholder Mappings

| Placeholder | Resolved Value |
|---|---|
| `<tactical_context>` | `AGENTS.md` at the project root |
| Local context file | `~/.vibe/AGENTS.md` (applies to every project of the user) |

`.vibe/` is the native Vibe configuration directory of a project; it is not a framework placeholder.

[Return to Table of Contents](#table-of-contents)

---

## 3.0 Planner

Not prescribed. Any frontier model with sufficient reasoning capability may act as planner; the role requires planning, governance interpretation, design creation, prompt authoring and validation. Claude Desktop is the planner that the framework has been used with. Vibe as a planner client is not covered by this profile.

[Return to Table of Contents](#table-of-contents)

---

## 4.0 Worker and Reviewer

**Implementation:** Mistral Vibe

Configuration directory: `.vibe/` (project) and `~/.vibe/` (user; another location with the `VIBE_HOME` environment variable) [2].

Context file: `AGENTS.md` at the project root (checked into git). At start Vibe loads `~/.vibe/AGENTS.md` and each `AGENTS.md` from the project root up through the trusted folders [2].

**Prerequisites:**

- Vibe installed. macOS and Linux: `curl -LsSf https://mistral.ai/vibe/install.sh | bash`. Any platform with uv: `uv tool install mistral-vibe`. Vibe needs Python 3.12 or later [1], [3].
- A Mistral account or an API key. On the first run of `vibe` in the project, sign in with the Mistral account or enter an API key [1]. A key is read from the `MISTRAL_API_KEY` environment variable or from `~/.vibe/.env` [2].
- The engine's API profile asks that `MISTRAL_API_KEY` is not exported globally (`mistral_api.md` §4.0): a global value overrides Vibe's own key. Keep Vibe's key in `~/.vibe/.env`.

**Model and provider:** Vibe uses its default Mistral model unless `active_model` in `config.toml` names a model alias. Another provider, for example a local OpenAI-compatible server such as oMLX, is declared in `config.toml` [2]:

```toml
active_model = "local-devstral"

[[providers]]
name = "omlx"
api_base = "http://127.0.0.1:8000/v1"
api_key_env_var = ""

[[models]]
name = "<model id served by the local server>"
provider = "omlx"
alias = "local-devstral"
```

A project `.vibe/config.toml` overrides the user's `~/.vibe/config.toml` and is read only in a trusted folder. `vibe config schema` prints the accepted keys [2].

**MCP servers:** the worker needs no MCP server for this profile; Vibe reads and edits files in the project with its own tools. Vibe can use MCP servers declared as `[[mcp_servers]]` tables in `config.toml` (`name`, `transport`, and `command` with `args` for a stdio server or `url` for an HTTP server) [2]. Check the keys with `vibe config schema` before use.

[Return to Table of Contents](#table-of-contents)

---

## 5.0 Vibe Task Invocation

Vibe fulfils both the worker and reviewer roles in a single manual pass. There is no worker/reviewer cycle; the human operator performs the review gate.

**Procedure:**

1. The planner authors and the human approves the T03 prompt per the standard workflow. Set `target_profile: mistral_vibe` (governance P13.2). A `tactical_brief` is not required.
2. Open a terminal in the project root and run `vibe`.
3. Issue the following instruction, substituting the actual T03 file path:

```text
Implement ai/workspace/prompt/prompt-<uuid>-<name>.md and close the prompt T-Doc
when finished. Leave the issue and change T-Docs active pending test results.
Then, once finished, write a report of what you have done in
ai/workspace/report/report-<uuid>-<name>.md.
```

4. Vibe reads the T03 prompt from disk and implements the task. It asks before an action that needs approval, according to the selected agent mode and the tool permissions in `config.toml` [1], [2].
5. Run the project's tests for the modified components (governance P15.15). This profile installs no automatic test hook (§6.0).
6. The human operator reviews the result and accepts or requests changes.

Reference: `ai/governance/software-engineering/governance.md` P13.3 Option C, which names the Claude Code profiles; the procedure is the same.

[Return to Table of Contents](#table-of-contents)

---

## 6.0 Project Setup

**.gitignore additions:**

```
# Mistral Vibe profile - Worker and Reviewer
.vibe/
```

Remove the `.vibe/` line if the project shares a `.vibe/config.toml` between its developers.

**Directory structure additions (within project root):**

```
├── .vibe/
│   └── config.toml           # optional project configuration; read in a trusted folder
└── AGENTS.md                 # worker and reviewer context file; git-tracked
```

**Context file:** create `AGENTS.md` with the content that governance P00.19 specifies for the worker/reviewer context file (project overview, commands, code style, repository conventions, governance location).

**Validation skill (P00.18):** the mandatory skill `skills/validation/run-tests.md` is defined for the Claude Code profiles and installs a Claude Code hook. It does not apply to Vibe. Vibe has its own hook files (`~/.vibe/hooks.toml` and `.vibe/hooks.toml`) [2]; this profile does not define a hook for them. The operator runs pytest after the task (§5.0 step 5).

[Return to Table of Contents](#table-of-contents)

---

## 7.0 Verification Status

| Item | Status |
|---|---|
| Installation commands, Python requirement, licence (Apache-2.0) | Read from the project README and the PyPI page on 2026-11-14 (version 3.1.2, released 2026-11-10) [1], [3] |
| Configuration locations, `AGENTS.md` loading, `[[providers]]` and `[[models]]` keys, `active_model`, key locations | Read from the documentation shipped in the Vibe repository on 2026-11-14 [2] |
| `[[mcp_servers]]` keys, hook files | Taken from a summary of the same document, not from its full text; check with `vibe config schema` |
| A task run with this profile on a project | Not performed |
| Vibe with a local server (oMLX) | Not performed; the `api_base`, the empty `api_key_env_var` and the model id above are examples |

The Mistral documentation site was not reachable from the session that wrote this profile; its configuration reference [4] is listed for the reader.

[Return to Table of Contents](#table-of-contents)

---

## References

[1] MISTRAL AI, 2026. *Mistral Vibe: README* [online]. Available from: https://github.com/mistralai/mistral-vibe/blob/main/README.md [Accessed 14 November 2026].

[2] MISTRAL AI, 2026. *Mistral Vibe: built-in skill documentation (SKILL.md)* [online]. Available from: https://github.com/mistralai/mistral-vibe/blob/main/vibe/plugins/builtins/vibe/skills/vibe/SKILL.md [Accessed 14 November 2026].

[3] MISTRAL AI, 2026. *mistral-vibe 3.1.2* [online]. Python Package Index. Available from: https://pypi.org/project/mistral-vibe/ [Accessed 14 November 2026].

[4] MISTRAL AI, 2026. *Configuration reference — Mistral Vibe* [online]. Available from: https://docs.mistral.ai/vibe/code/cli/configuration-reference [Not accessed; listed for reference].

[Return to Table of Contents](#table-of-contents)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-14 | Initial document (dev/task.md work item 7b; proposal-5bcd46ad OQ-01, D-16). Written from the Vibe documentation; not run against a project |
| 1.1 | 2026-11-14 | §7.0: the empty `api_key_env_var` of the local-server example named as an example value (review remark) |
| 1.2 | 2026-11-25 | §5.0 step 1: `target_profile: mistral_vibe` replaces `claude_code` (governance 12.14; report-b80f9e6e F-01) |

---

Copyright (c) 2026 William Watson. MIT License.
