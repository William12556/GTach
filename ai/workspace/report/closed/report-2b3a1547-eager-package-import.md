Created: 2026 October 09

# Report: Lazy Package Import

---

## Table of Contents

1. [Summary](<#1. summary>)
2. [Files Changed](<#2. files changed>)
3. [Tests and Result](<#3. tests and result>)
4. [Success Criteria](<#4. success criteria>)
5. [Deviations](<#5. deviations>)
6. [Items Kept](<#6. items kept>)
7. [On-Device Verification Outstanding](<#7. on-device verification outstanding>)
8. [Version History](<#version history>)

---

## 1. Summary

prompt-2b3a1547 (change-2b3a1547, issue-2b3a1547) is implemented. `src/gtach/__init__.py` no longer imports `GTachApplication` or `main`; `__all__` is `["__version__"]`. Importing `gtach` or `gtach.main` no longer imports `gtach.app` or pygame.

[Return to Table of Contents](<#table of contents>)

---

## 2. Files Changed

| File | Change |
|---|---|
| `src/gtach/__init__.py` | Removed `from .app import GTachApplication` and `from .main import main`; `__all__ = ["__version__"]`; comment citing issue-2b3a1547. `__version__` and `__author__` kept. |
| `tests/test_stack_dump_toggle.py` | Comment only: `gtach.main` is the submodule. |
| `tests/test_stacks_log_rotation.py` | Docstring text only: `gtach.main` is the submodule. |
| `tests/test_package_import.py` | New: 3 subprocess tests. |

[Return to Table of Contents](<#table of contents>)

---

## 3. Tests and Result

New tests (fresh interpreter via `sys.executable`): `import gtach.main` leaves `pygame` and `gtach.app` out of `sys.modules`; `gtach.__version__` prints a non-empty value; `python -m gtach --version` exits 0.

- Before: 556 passed.
- After: 559 passed. Against the old `__init__.py`, the import-cost test fails.
- mypy error count unchanged (338).

[Return to Table of Contents](<#table of contents>)

---

## 4. Success Criteria

| Criterion | Result |
|---|---|
| No `from .app` / `from .main` in `__init__.py` | Met |
| Three subprocess tests pass | Met |
| `pytest tests/` passes | Met |

[Return to Table of Contents](<#table of contents>)

---

## 5. Deviations

None.

[Return to Table of Contents](<#table of contents>)

---

## 6. Items Kept

- The `sys.modules["gtach.main"]` lookups in both test files are unchanged.
- `tests/test_stacks_log_rotation.py` already fails `black --check` on an untouched line (a `monkeypatch.setattr` call in a test body). It was not reformatted, per the rule against reformatting unchanged code.
- No grep hits remain for `gtach.GTachApplication` or `from gtach import main` in `src`, `tests` or `bin`.

[Return to Table of Contents](<#table of contents>)

---

## 7. On-Device Verification Outstanding

- On the Pi, after deploy: `systemctl status gtach` shows the service running and the display starts.
- `/opt/gtach/venv/bin/gtach --validate-config` runs and exits 0 on a valid file.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-09 | Initial report for prompt-2b3a1547. |

---

Copyright (c) 2026 William Watson. MIT License.
