Created: 2026 October 23

# Core Component

---

## Table of Contents

[1.0 Purpose](#10-purpose)
[2.0 Rules](#20-rules)
[Version History](#version-history)

---

## 1.0 Purpose

`ai/core/` is reserved for code shared between framework components (`ai/engine/`, `ai/webui/`). It holds no source yet. Code moves here only when more than one component needs it.

[Return to Table of Contents](#table-of-contents)

---

## 2.0 Rules

1. Layout follows the other components: `src/`, optional `doc/`, `requirements.txt`, tests in `tests/core/`.
2. `core` imports no other framework component. `engine` and `webui` may import `core`.

[Return to Table of Contents](#table-of-contents)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-23 | Initial document: folder reserved (change-14cf601f) |

---

Copyright (c) 2026 William Watson. MIT License.
