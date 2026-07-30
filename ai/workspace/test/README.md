# Test

Test documentation per P06.

## `test/` is not `tests/`

Two different locations, one letter apart. This folder holds **documents**;
the executable tests live at the project root.

| Path | Contents | Governance |
|---|---|---|
| `ai/workspace/test/` — here | T05 test **documents**: markdown specifications of what to test and why | P06 §1.7.2 |
| `tests/` — project root | **pytest files** (`test_*.py`) generated from those documents | P06 §1.7.3 |

`pyproject.toml` sets `testpaths = ["tests"]`, so `pytest` collects only
from the project root `tests/` directory. A `.py` file placed in this
folder is **silently ignored** — it will not run and nothing will warn
you. The same setting is why the AEL framework's own tests under
`ai/ael/tests/` are not swept into the project suite.

Workflow: T05 document here → generate `tests/<component>/test_*.py` →
execute → T06 result in `result/`.

## Structure

| Folder | Purpose |
|--------|---------|
| result/ | Test result documents |
| closed/ | Closed test documents |

## Naming Convention

- Test: `test-<uuid>-<n>.md`
- Result: `result-<uuid>-<n>.md`

Each T05 document names its generated pytest path in its `notes` field.

---

Copyright (c) 2025 William Watson. This work is licensed under the MIT License.
