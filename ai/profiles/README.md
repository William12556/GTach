Created: 2026 February 18

# Implementation Profiles

---

## Table of Contents

- [Purpose](<#purpose>)
- [Abstract Placeholders](<#abstract placeholders>)
- [Profile Selection](<#profile selection>)
- [Available Profiles](<#available profiles>)
- [Version History](<#version history>)

---

## Purpose

Implementation profiles map abstract governance placeholders to concrete tooling for a specific execution environment. The governance framework (`ai/governance.md`) is model-agnostic. Profiles resolve the implementation details without modifying governance rules.

[Return to Table of Contents](<#table of contents>)

---

## Abstract Placeholders

| Placeholder | Meaning |
|---|---|
| `<tactical_config>/` | Tactical Domain configuration directory |
| `<skills_dir>/` | Skills and workflow recipes directory |
| `<tactical_context>` | Tactical Domain project context file |

[Return to Table of Contents](<#table of contents>)

---

## Profile Selection

Select one profile per project. Copy the profile-specific `.gitignore` additions into the project `.gitignore`. Apply all placeholder mappings consistently across the project.

[Return to Table of Contents](<#table of contents>)

---

## Available Profiles

| Profile | Domain | File |
|---|---|---|
| Claude Desktop | Strategic Domain | [claude-desktop.md](framework/ai/doc/claude-desktop-instructions.md) |
| Claude Code (optional) | Tactical Domain | [claude.md](claude.md) |
| Apple Silicon + MLX (Devstral Small 2 2512) | Tactical Domain | [mlx_devstral_small_2_2512_Q8.md](mlx_devstral_small_2_2512_Q8.md) |

Strategic Domain is not prescribed. Any frontier model with sufficient reasoning capability is suitable. Claude Desktop is the preferred Strategic Domain implementation.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-02-18 | Initial document |
| 1.1 | 2026-02-18 | Added profile-claude-desktop.md to Available Profiles table |
| 1.2 | 2026-03-04 | Renamed folder to profiles/; renamed profile-*.md files to claude-desktop.md, claude.md, ollama.md |
| 1.3 | 2026-03-11 | Replaced OLLama profile with Apple Silicon + MLX profile; deprecated ollama.md to deprecated/ |
| 1.4 | 2026-03-12 | Added mlx_devstral_small_2_2512_Q8.md to Available Profiles |
| 1.5 | 2026-03-31 | Deprecated mlx_devstral_small_2507_Q8.md; reinstated claude.md as optional Claude Code profile |

---

Copyright (c) 2025 William Watson. This work is licensed under the MIT License.
