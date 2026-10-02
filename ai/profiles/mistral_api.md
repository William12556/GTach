Created: 2026 October 02

# Implementation Profile: Mistral API (Mistral Medium 3.5 Worker and Reviewer)

---

## Table of Contents

- [1.0 Overview](<#1.0 overview>)
- [2.0 Placeholder Mappings](<#2.0 placeholder mappings>)
- [3.0 Planner](<#3.0 planner>)
- [4.0 Worker and Reviewer](<#4.0 worker and reviewer>)
- [5.0 Tool-Calling Behaviour](<#5.0 tool-calling behaviour>)
- [6.0 Engine](<#6.0 engine>)
- [7.0 Model Selection](<#7.0 model selection>)
- [8.0 Project Setup](<#8.0 project setup>)
- [References](<#references>)
- [Version History](<#version history>)

---

## 1.0 Overview

This profile maps governance abstract placeholders to the hosted Mistral API. Mistral Medium 3.5 fulfils both the worker and reviewer roles, driven by the engine orchestrator through the `openai_compatible` provider kind (change-53c6f252). No local inference server or Apple Silicon hardware is required.

| Concern          | Implementation                              |
| ---------------- | ------------------------------------------- |
| Planner          | Claude Desktop (preferred)                  |
| Worker           | Mistral Medium 3.5 via Mistral API + engine |
| Reviewer         | Mistral Medium 3.5 via Mistral API + engine |
| Engine mechanism | Engine orchestrator / loop                  |

Worker and reviewer use the same model; roles differ by prompt engineering only. Source content read by the engine is transmitted to the Mistral API.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Placeholder Mappings

| Placeholder | Resolved Value |
|---|---|
| `<tactical_context>` | `ai/context.md` |

`<tactical_config>/` and `<skills_dir>/` do not apply to this profile. Engine configuration is in `ai/config.yaml`; recipes are in `ai/engine/recipes/` and `ai/governance/<model>/recipes/`, mapped by the model's `manifest.yaml`.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Planner

**Preferred implementation:** Claude Desktop

Any frontier model with sufficient reasoning capability may substitute. The planner role requires: planning, governance interpretation, design creation, prompt authoring, and validation.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Worker and Reviewer

**Worker:** Mistral Medium 3.5 via Mistral API + engine orchestrator
**Reviewer:** Mistral Medium 3.5 via Mistral API + engine orchestrator

**Prerequisites:**
- Mistral API account and API key [1]
- Network access to `https://api.mistral.ai`
- Engine dependencies installed: `pip install -r ai/engine/requirements.txt`

**API key:** the engine reads the key from the environment variable named in `api_key_env`. A literal `api_key` is rejected for non-local endpoints. The engine has no native Keychain support; on macOS, store the key in the login Keychain and inject it per invocation.

1. Store the key (once). With no value after `-w`, `security` prompts for it, so the key is not written to shell history. Add `-U` to replace an existing entry.

```bash
security add-generic-password -a "$USER" -s MISTRAL_API_KEY -w
```

2. Invoke the engine with the key scoped to that process only:

```bash
MISTRAL_API_KEY="$(security find-generic-password -a "$USER" -s MISTRAL_API_KEY -w)" \
  python ai/engine/src/orchestrator.py --mode loop --task ai/workspace/prompt/prompt-<uuid>-<n>.md
```

Notes:
- The command-prefix assignment does not export the variable to the shell. A global `MISTRAL_API_KEY` overrides Mistral Vibe's own key (`ai/engine/config.template.yaml`).
- On first read, macOS prompts for Keychain access. "Always Allow" grants `/usr/bin/security` unprompted access, which any process running as the same user can then use to read the key.
- In SSH or other non-GUI sessions the login Keychain may be locked; run `security unlock-keychain` first.
- Engine runs started through `engine-mcp` (`start_engine`) inherit the environment of the `engine-mcp` server process, not of the invoking shell; the step-2 prefix does not apply to that path.

**Model id verification:** for kind `openai_compatible`, the engine readiness check requires the configured model id to be listed by the endpoint. Confirm the id before the first run:

```bash
curl -s -H "Authorization: Bearer $MISTRAL_API_KEY" \
  https://api.mistral.ai/v1/models | grep -o '"id":"mistral-medium[^"]*"'
```

**Engine config** (`ai/config.yaml`):

```yaml
providers:
  mistral:
    kind: openai_compatible
    base_url: "https://api.mistral.ai/v1"
    api_key_env: MISTRAL_API_KEY

roles:
  worker:   { provider: mistral, model: "mistral-medium-2604" }
  reviewer: { provider: mistral, model: "mistral-medium-2604" }

context:
  model_context_windows:
    mistral-medium-2604: 262144
```

With `roles:` present, the legacy `omlx:` block is not used for role binding. Per-role precedence is: CLI flag (`--worker-model` / `--reviewer-model`) > `--model` > `roles.<role>.model`. Use the pinned model id, not a `-latest` alias.

Reference template: `ai/engine/config.template.yaml`. Operations guide: `ai/engine/doc/guide-engine-operations.md` §3.0.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Tool-Calling Behaviour

The Mistral API returns native structured `tool_calls` on the chat completions endpoint. The `openai_compatible` provider (`ai/engine/src/providers.py`) consumes these directly; the Mistral-format text parser (`ai/engine/src/parser.py`) remains as a fallback when no structured calls are returned. The orchestrator owns the tool dispatch loop and dispatches via the Python MCP SDK.

Reviewer verdict parsing (leading `SHIP` / `REVISE` token) and reviewer tool-calling are unverified for Mistral Medium 3.5 and should be confirmed on the first real review phase.

Name tools explicitly in recipe prompts; use imperative phrasing.

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Engine

**Implementation:** engine orchestrator / loop

State directory: `ai/state/` (ephemeral, per-task)

**Prerequisites:**
- `MISTRAL_API_KEY` set in the engine process environment
- `ai/config.yaml` configured with the `providers:` and `roles:` blocks in §4.0
- `context.model_context_windows` entry for the model (no live context query exists for API models)

**Invocation:**

```bash
python ai/engine/src/orchestrator.py --mode loop --task ai/workspace/prompt/prompt-<uuid>-<n>.md
```

The worker and reviewer models are resolved from config; no per-run model flags are required. Variables named by `api_key_env` are scrubbed from the environment of engine-launched subprocesses.

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Model Selection

| Role | Model | API id | Context Window |
|---|---|---|---|
| Worker | Mistral Medium 3.5 (v26.04) | `mistral-medium-2604` | 256k (262144) |
| Reviewer | Mistral Medium 3.5 (v26.04) | `mistral-medium-2604` | 256k (262144) |

Selection notes:
- Devstral and Magistral API endpoints (`devstral-2512`, `magistral-medium-2509`, and earlier) are listed as deprecated by Mistral [2].
- Mistral documentation lists the endpoint as `mistral-medium-3-5-26-04`; third-party catalogues list `mistral-medium-2604` [3]. The id must match the `/v1/models` listing exactly (§4.0).
- Pricing at time of writing: USD 1.5 per million input tokens, USD 7.5 per million output tokens [3]. Loop runs bill every iteration of both roles.

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Project Setup

**.gitignore additions:**

```
# Mistral API profile - Worker and Reviewer
ai/state/
```

The API key is not stored in `ai/config.yaml` or any tracked file.

[Return to Table of Contents](<#table of contents>)

---

## References

[1] MISTRAL AI, 2026. *Models overview* [online]. Available from: https://docs.mistral.ai/getting-started/models/ [Accessed 2 October 2026].

[2] MISTRAL AI, 2026. *Models overview: deprecated models* [online]. Available from: https://docs.mistral.ai/getting-started/models/models_overview/ [Accessed 2 October 2026].

[3] MISTRAL AI, 2026. *Mistral Medium 3.5* [online]. Available from: https://docs.mistral.ai/models/mistral-medium-3-5-26-04 [Accessed 2 October 2026].

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-02 | Initial document; Mistral API profile with Mistral Medium 3.5 as worker and reviewer via engine `openai_compatible` provider |
| 1.1 | 2026-10-02 | §4.0: macOS Keychain storage and per-invocation key injection |

---

Copyright (c) 2026 William Watson. MIT License.
