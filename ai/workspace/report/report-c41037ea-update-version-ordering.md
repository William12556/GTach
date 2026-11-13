# Report — Update Version Ordering (c41037ea)

Created: 2026 November 13

## Table of Contents

- [1.0 Summary](#10-summary)
- [2.0 Changes](#20-changes)
- [3.0 Validation](#30-validation)
- [4.0 Review](#40-review)
- [5.0 Deviations and Limits](#50-deviations-and-limits)
- [6.0 Document Status](#60-document-status)
- [Version History](#version-history)

---

## 1.0 Summary

- Implements `prompt-c41037ea` (change-c41037ea, issue-c41037ea; finding H01 of audit-bce0d69a).
- The update check now reads PEP 440 pre-release versions (`a`, `b`, `rc`) and orders them below their final release.
- Commits: `97aef4d` (implementation), `cfbf605` (review cycle 1 correction).
- Authority: delegated approval, `proposal-f8d0064b` §3.0; approvals recorded by `approve.py` (`686b945`, `322c990`).

[Return to Table of Contents](#table-of-contents)

---

## 2.0 Changes

| Edit | File | Change |
|---|---|---|
| A | `src/gtach/utils/updater.py` | `_parse_version_str` matches `N(.N)*[{a,b,rc}N]` and returns an order key: release padded to three components, phase rank (`a` −3, `b` −2, `rc` −1, final 0), pre-release number. Other forms return `None`. Constants `_VERSION_RE`, `_PRE_RELEASE_RANK`, `_MIN_RELEASE_PARTS` |
| B | `src/gtach/utils/updater.py` | `find_available_update` logs a WARNING when the installed version is not recognised and a DEBUG record for a wheel with an unrecognised version |
| Tests | `tests/test_update_version_ordering.py` | 26 tests (new module) |

Examples: `1.0.0rc1` → `(1, 0, 0, -1, 1)`; `1.0.0` → `(1, 0, 0, 0, 0)`; `1.0` equals `1.0.0`.

[Return to Table of Contents](#table-of-contents)

---

## 3.0 Validation

Progressive validation (P15.15), run manually (decision D8):

| Stage | Command | Result |
|---|---|---|
| Targeted | `pytest tests/test_update_version_ordering.py` | 26 passed (Python 3.13.18 and 3.9.25) |
| Integration | `tests/test_lifecycle_logging_utils.py`, `tests/test_gauge_display_touch.py` with the new module | 85 passed (before the cycle 1 correction: 23 + 62) |
| Regression | `pytest tests/` | 806 passed (Python 3.13.18); 803 passed on Python 3.9.25 before the cycle 1 correction, which added 3 tests that pass on 3.9 |
| Types | `python -m mypy src/` (1.20.2, target 3.9) | No issues in 60 source files |
| Lint | `flake8`, `black --check`, `isort` on the two changed files | Clean |

The reviewer confirmed that 11 of the first 23 tests fail against the previous source.

[Return to Table of Contents](#table-of-contents)

---

## 4.0 Review

Separate review subagents with a fresh context, given the change document and the diff.

| Cycle | Verdict | Finding | Action |
|---|---|---|---|
| 1 | REVISE | `_parse_version_str` raised `ValueError` for a digit string beyond the interpreter's integer conversion limit (`"9" * 5000`); the previous code returned `None` | `int()` conversions moved inside a `ValueError` handler; three test cases added; the single-WARNING test now asserts exactly one record (`cfbf605`) |
| 2 | SHIP | No defect | — |

Optional reviewer remarks, not acted on: `\d` also matches non-ASCII digits and leading zeros are accepted (both as before the change); the digit-limit tests depend on the interpreter enforcing the limit (Python 3.9.14 and newer do).

[Return to Table of Contents](#table-of-contents)

---

## 5.0 Deviations and Limits

- **Deviation from the prompt:** none in behaviour. The implementation computes the rank and number in one handler instead of two return statements.
- **Limit:** a release with four or more components and trailing zeros (`1.0.0.0`) does not equal `1.0.0`. GTach versions have three components.
- **Limit:** development, post-release, local and epoch versions are still not recognised; such a wheel is skipped, now with a DEBUG record.
- **Not verified on the device:** the staged-update path from an installed release candidate (owner's device session; `report-f8d0064b-v1-release-run` checklist).

[Return to Table of Contents](#table-of-contents)

---

## 6.0 Document Status

- Prompt, issue and change closed and moved to `closed/`. The fix is verified by unit tests; the device check above is a confirmation of the unchanged end-to-end path, not a condition of closure.
- Design updated: `design-9a1f3c7e-domain_utils` §4.3 (v2.1).
- Traceability matrix §8.0 updated.

[Return to Table of Contents](#table-of-contents)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-13 | Implementation report |

---

Copyright (c) 2026 William Watson. MIT License.
