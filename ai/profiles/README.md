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
| Claude Desktop | Strategic Domain | [claude-desktop.md](claude-desktop.md) |
| Apple Silicon + MLX (Devstral Small 2 2512) | Tactical Domain | [mlx_devstral_small_2_2512_Q8.md](mlx_devstral_small_2_2512_Q8.md) |

Strategic Domain is not prescribed. Any frontier model with sufficient reasoning capability is suitable. Claude Desktop is the preferred Strategic Domain implementation.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-02-18 | Initial document |
| 1.1 | 2026-03-13 | GTach initialisation: active profiles are Claude Desktop (Strategic) and MLX Devstral Small 2 2512 (Tactical) |

---

Copyright (c) 2025 William Watson. This work is licensed under the MIT License.
