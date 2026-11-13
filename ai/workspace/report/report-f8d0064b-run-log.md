# Run Log — Autonomous Release Run to v1.0.0 (f8d0064b)

Created: 2026 November 13

## Table of Contents

- [1.0 Purpose](#10-purpose)
- [2.0 Baseline](#20-baseline)
- [3.0 Steps](#30-steps)
- [4.0 Notes](#40-notes)
- [Version History](#version-history)

---

## 1.0 Purpose

Step record of the run defined in `ai/workspace/proposal/proposal-f8d0064b-v1-release-autonomous-run.md` (§5.3). On resumption, continue from the first row of §3.0 whose status is not `Done`.

[Return to Table of Contents](#table-of-contents)

---

## 2.0 Baseline

Measured 2026-11-13 at commit `2f32b45`, branch `claude/gtach-v1-release-run-g0106d`.

| Check | Python 3.13.18 | Python 3.9.25 |
|---|---|---|
| `pytest tests/` | 780 passed | 780 passed, 1 warning (pygame imports `pkg_resources`) |
| `python -m mypy src/` | mypy 2.4.1: no issues in 60 files, but `python_version = "3.9"` rejected ("must be 3.10 or higher") | mypy 1.19.1: 3 errors (typeshed lacks `AF_BLUETOOTH` and `BTPROTO_RFCOMM` on Linux) |
| `flake8 src tests` | 6 findings, all in `tests/` (5 × F401, 1 × E731) | not run |
| `black --check src tests` | 3 files in `tests/` would be reformatted | not run |
| `isort --check src tests` | 1 file in `tests/` | not run |

- The Python 3.9 interpreter was obtained with `uv python install 3.9` (CPython 3.9.25, python-build-standalone) and used in a venv outside the repository. This build has no `socket.AF_BLUETOOTH`, so the suite ran the non-Bluetooth paths, as on the 3.13 interpreter.
- `src/` has no `flake8`, `black` or `isort` finding. The findings in `tests/` are existing debt (D7).

[Return to Table of Contents](#table-of-contents)

---

## 3.0 Steps

| Step | Item | Status | Commit | Notes |
|---|---|---|---|---|
| WP0 | Environment and baseline | Done | `904bf8f` | §2.0 |
| WP1 | mypy target | Done | `904bf8f` | `mypy>=1.20,<2.0; python_version >= '3.10'`. mypy 1.20.2 with the 3.9 target: no issues in 60 files. Tested 1.14.1 to 1.19.1 (3 to 7 errors, typeshed and older checker), 1.20.0 and 1.20.2 (clean), 2.0.0 (target rejected). Row removed from `ai/task.md` |
| WP2 | Rows `821919ce`, `9ed1c77e` | Done | `874df8e` | Explicit drop (D6). Both triples were already closed and not implemented; both withdrawal conditions are met (frames complete inside budget). Re-evaluation needs on-device frame times and a new issue |
| WP3 | setuptools and `pkg_resources` | Done | `874df8e` | No guard needed; row dropped. Evidence in §4.0 |
| WP5 | Stuck Bluetooth recovery | Done | `874df8e` | Row kept, Status `Deferred — after 1.0` (D3) |
| WP4 | Design documents | Done | (WP4 commits) | Retired 4 (`d4e5f6a7`, `c3d4e5f6`, `g1h2i3j4`, `e1f2a3b4`); merged 2 pairs (`f6a7b8c9` into `a6b7c8d9`; `e5f6a7b8` into `f5a6b7c8`, carrying its §6.3); 19 documents rewritten or refreshed against the source, including the four status-line documents, which had drifted beyond the status line; `b4c5d6e7` and `f8a9b0c1` link conversion only; `a3b4c5d6` unchanged. Traceability matrix v2.0. `report-71ab3751-design-review` moved to `report/closed/`; row removed. Three rows added to `ai/task.md` (D7, D8, requirements review) |
| WP7 | Release-readiness audit | Pending | | |
| WP8 | Release preparation | Pending | | |
| Final | Final report and pull request | Pending | | |

[Return to Table of Contents](#table-of-contents)

---

## 4.0 Notes

- WP1: mypy 1.20 and newer require Python 3.10 to run, so the marker leaves a Python 3.9 development interpreter without mypy. The check is run from a 3.10 or newer interpreter against the 3.9 target.
- WP3: `pygame/pkgdata.py` imports `pkg_resources` inside `try/except ImportError` and falls back to its own stubs, so a missing `pkg_resources` does not break `import pygame`. Verified with pygame 2.6.1: (a) Python 3.9.25 venv with setuptools 82.0.1 (`pkg_resources` absent): `import pygame`, `pygame.init()` and `pygame.font.Font(None, 20)` succeed; (b) Python 3.13 venv with no setuptools: the same, with warnings as errors, and the full suite passes. `bin/install.sh` and `bin/pi-install.sh` create the venv with `python3 -m venv` and never upgrade setuptools; the version that Debian 11 bundles was not measured (no device access) and does not matter given (a) and (b). `src/gtach/` does not use `pkg_resources`.
- WP4: each refreshed design was written after reading the corresponding source module; the body of every retired and merged document was read first. Layout coordinates and font sizes were copied from the source as constants and not re-derived. Not verified: Mermaid rendering on GitHub (no renderer in this environment); internal links were checked by script (25 files, 0 broken).
- WP4 defect candidates noted for WP7: `utils/updater.py` cannot parse a pre-release version such as `1.0.0rc1` (D1), which makes the update check return nothing while a release candidate is installed.

[Return to Table of Contents](#table-of-contents)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-13 | WP0 and WP1 |
| 1.1 | 2026-11-13 | WP2, WP3 and WP5 |
| 1.2 | 2026-11-13 | WP4 |

---

Copyright (c) 2026 William Watson. MIT License.
