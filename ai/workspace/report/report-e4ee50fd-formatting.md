Created: 2026 October 07

# Report: black and isort at 88 Columns

---

## Table of Contents

1. [Summary](<#1. summary>)
2. [Files Changed](<#2. files changed>)
3. [Tests Added and Result](<#3. tests added and result>)
4. [Success Criteria](<#4. success criteria>)
5. [Deviations](<#5. deviations>)
6. [On-Device Verification Outstanding](<#6. on-device verification outstanding>)
7. [Version History](<#version history>)

---

## 1. Summary

prompt-e4ee50fd (change-e4ee50fd, issue-e4ee50fd; audit-36b6ea95 G05) was implemented in commit `d44dca9b0d42de3358427f7851abae2336762557`.

- **EDIT A:** `.flake8`: `max-line-length = 88`; `extend-ignore = E203, W503`; excludes `bin/vendor`.
- **EDIT B:** CLAUDE.md §7 line length is 88 for black, isort and flake8; Version History 1.7.
- **EDIT C:** `isort`, then `black`, over src, tests and bin/*.py: 83 files reformatted, one unchanged.
  - The 68 E501 lines that black could not split were long strings, comments and docstrings. They were wrapped by hand, or by a script, without changing meaning: string literals as implicit concatenations, comments as two comment lines, docstrings re-wrapped.
  - Four E226 findings inside f-string placeholders were given spaces.

[Return to Table of Contents](<#table of contents>)

---

## 2. Files Changed

| File | Change |
|---|---|
| `.flake8` | New (EDIT A). |
| `CLAUDE.md` | EDIT B. |
| `src/gtach/**/*.py`, `tests/**/*.py`, `bin/gen_splash.py` | EDIT C. |

[Return to Table of Contents](<#table of contents>)

---

## 3. Tests Added and Result

No tests added.
- **pytest:** 447 passed before and after formatting (unchanged count).
- **AST comparison:** every one of the 83 changed Python files was compared with HEAD. Imports were compared as a sorted set and docstrings masked; apart from import order (isort) and re-wrapped docstrings, no file's AST changed.
- **flake8 before** (src, tests, bin/*.py; whole set): W293 1323, E501 473, E128 76, W291 69, E302 57, W292 34, E261 7, W391 6, E303 6, F401 5, E129 5, E305 3, E116 2, E114 2, F841 1, E731 1.
- **flake8 after:** F401 5, F841 1, E731 1, all in tests or naming, outside the selected codes.

[Return to Table of Contents](<#table of contents>)

---

## 4. Success Criteria

| Criterion | How checked | Result |
|---|---|---|
| `black --check src tests bin/*.py` passes | Ran it | 84 files unchanged |
| `isort --check-only src tests bin/*.py` passes | Ran it | Pass |
| `flake8 --select E1,E2,E3,E5,W2,W3 src tests` reports nothing | Ran it | Clean |
| pytest pass count identical before and after | Full runs | 447 / 447 |

[Return to Table of Contents](<#table of contents>)

---

## 5. Deviations

- **E226 spacing:** the four E226 fixes add spaces inside f-string placeholders, for example `{chunk + 1}`. This is a whitespace-only edit beyond line wrapping; black does not reach inside f-strings.
- **Docstrings:** several one-line docstrings over 88 columns became a summary line plus detail. Two docstrings were reworded slightly to fit: the `select_transport` summary and an internal progress callback.

[Return to Table of Contents](<#table of contents>)

---

## 6. On-Device Verification Outstanding

None required.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-07 | Initial implementation report for prompt-e4ee50fd. |

---

Copyright (c) 2026 William Watson. MIT License.
