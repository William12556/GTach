Created: 2026 February 18

# Implementation Profiles

---

## Table of Contents

- [1.0 Purpose](<#1.0 purpose>)
- [2.0 Abstract Placeholders](<#2.0 abstract placeholders>)
- [3.0 Profile Selection](<#3.0 profile selection>)
- [4.0 Available Profiles](<#4.0 available profiles>)
- [Version History](<#version history>)

---

## 1.0 Purpose

Implementation profiles map abstract governance placeholders to concrete tooling for a specific execution environment. The governance framework (`ai/governance.md`) is model-agnostic. Profiles resolve the implementation details without modifying governance rules.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Abstract Placeholders

`<tactical_config>/`, `<skills_dir>/`, and `<tactical_context>` are governance placeholders resolved by each profile. Not all placeholders apply to every profile.

| Placeholder | Meaning | Applies to |
|---|---|---|
| `<tactical_config>/` | Tactical Domain configuration directory | Claude Code profiles only |
| `<skills_dir>/` | Skills and workflow recipes directory | Claude Code profiles only |
| `<tactical_context>` | Tactical Domain project context file | All profiles |

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Profile Selection

Select one profile per project. Copy the profile-specific `.gitignore` additions into the project `.gitignore`. Apply all placeholder mappings consistently across the project.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Available Profiles

| Profile | Domain | File |
|---|---|---|
| Claude Desktop | Strategic Domain | [claude-desktop-instructions.md](../../../docs/claude/claude-desktop-instructions.md) |
| Claude Code (optional) | Tactical Domain | [claude.md](claude.md) |
| claude-omlx | Tactical Domain | [claude-omlx.md](claude-omlx.md) |
| Apple Silicon + MLX (Devstral Small 2 2512) | Tactical Domain | [mlx_devstral_small_2_2512_6bit.md](mlx_devstral_small_2_2512_6bit.md) |
| Apple Silicon + MLX (Heterogeneous: Devstral worker / Magistral reviewer) | Tactical Domain | [mlx_devstral_magistral_heterogeneous.md](mlx_devstral_magistral_heterogeneous.md) |

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
| 1.6 | 2026-04-30 | Added claude-omlx.md profile |
| 1.7 | 2026-06-16 | Updated Claude Desktop link: framework/ai/doc/ → docs/claude/ |
| 1.8 | 2026-06-16 | Abstract Placeholders: added Applies to column; noted <tactical_config>/ and <skills_dir>/ apply to Claude Code profiles only |
| 1.9 | 2026-06-16 | Updated §4.0 link: mlx_devstral_small_2_2512_Q8.md → mlx_devstral_small_2_2512_6bit.md; added section numbering throughout |
| 1.10 | 2026-07-16 | Added heterogeneous Devstral/Magistral profile to §4.0 Available Profiles |

---

Copyright (c) 2026 William Watson. MIT License.
