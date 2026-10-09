Created: 2026 October 09

# Report: ConfigStore Save Keeps Unknown Keys

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

prompt-ae65fa10 (change-ae65fa10, issue-ae65fa10) is implemented. `ConfigStore.save` reads the current file before taking the lock and takes its unknown keys from it; the retained set is used only when the file is missing, unreadable, invalid YAML or not a mapping. A read failure logs a WARNING and the save proceeds. A module-level `_unknown_keys` helper is shared by `load` and `save`.

[Return to Table of Contents](<#table of contents>)

---

## 2. Files Changed

| File | Change |
|---|---|
| `src/gtach/utils/config.py` | New `_unknown_keys(data)`; `ConfigStore.load` uses it; `ConfigStore.save` reads the file first; class and `save` docstrings updated. |
| `tests/test_config_store.py` | 5 tests added to `TestSave`; `CONFIG_KEYS` imported. |

[Return to Table of Contents](<#table of contents>)

---

## 3. Tests and Result

New tests: save without load keeps `foo: 1`; key appended after load is kept; missing file writes exactly `CONFIG_KEYS`; invalid YAML returns True, writes the known keys and logs a WARNING; a YAML list contributes no unknown keys.

- Before: 548 passed.
- After: 553 passed. Against the old `config.py`, 3 of the 5 new tests fail (the other two cover behaviour that was already correct).
- mypy error count unchanged (338).

[Return to Table of Contents](<#table of contents>)

---

## 4. Success Criteria

| Criterion | Result |
|---|---|
| The four regression tests pass | Met (plus the list edge case) |
| `pytest tests/` passes | Met |

[Return to Table of Contents](<#table of contents>)

---

## 5. Deviations

None. File reads and the WARNING happen before the lock; the lock covers only the `_unknown` update and snapshot.

[Return to Table of Contents](<#table of contents>)

---

## 6. Items Kept

- `load()` validation, `CONFIG_KEYS` and the atomic write sequence are unchanged.
- An empty file (`safe_load` → None) is not a mapping, so the retained set is used, as the prompt's `isinstance(data, dict)` logic specifies.

[Return to Table of Contents](<#table of contents>)

---

## 7. On-Device Verification Outstanding

None required. Optional: add an unknown key to `/opt/gtach/config.yaml`, change the palette from the options screen, and confirm the key is still in the file.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-09 | Initial report for prompt-ae65fa10. |

---

Copyright (c) 2026 William Watson. MIT License.
