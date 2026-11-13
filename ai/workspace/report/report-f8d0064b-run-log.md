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
| WP4 | Design documents | Done | `efc785e`, `91e8033`, `d232eb3` | Retired 4 (`d4e5f6a7`, `c3d4e5f6`, `g1h2i3j4`, `e1f2a3b4`); merged 2 pairs (`f6a7b8c9` into `a6b7c8d9`; `e5f6a7b8` into `f5a6b7c8`, carrying its §6.3); 19 documents rewritten or refreshed against the source, including the four status-line documents, which had drifted beyond the status line; `b4c5d6e7` and `f8a9b0c1` link conversion only; `a3b4c5d6` unchanged. Traceability matrix v2.0. `report-71ab3751-design-review` moved to `report/closed/`; row removed. Three rows added to `ai/task.md` (D7, D8, requirements review) |
| WP7 | Release-readiness audit `bce0d69a` | Done | `55e6f5d`, `0bc4871` | 14 findings: 0 critical, 1 high, 3 medium, 10 low. Follow-up pass done; audit closed and moved to `audit/closed/` |
| WP7-T1 | Triple `c41037ea` — update check orders pre-release versions (H01) | Done | `206fb25`, `97aef4d`, `cfbf605`, `d0dac7c` | Review: REVISE (cycle 1), SHIP (cycle 2). Approvals `686b945`, `322c990`, `26f7ea6`. Closed |
| WP7-T2 | Trivial change P04.12 — odd hex digit count in the 010C reply (L01) | Done | `b2077e6` | Regression test added |
| WP7-D | Document and `bin/` remediation (M01, M02, M03, L02, L03, L05, L09) | Done | `55bdbd1` | `LICENSE` added: copyright line needs the owner's confirmation |
| WP8 | Release preparation | Done | (WP8 commit) | Version `1.0.0rc1` (D1). `releases/RELEASE_NOTES_v1.0.0.md`. README v2.8. Suite 818 passed on Python 3.13.18 and 3.9.25; mypy clean; lint clean on changed files. `python -m build`: sdist and wheel. Wheel installed in a clean Python 3.9.25 venv: `gtach --version` → `GTach 1.0.0rc1`; `--validate-config` and `--validate-dependencies` exit 0; `pip check` clean. Headless run `gtach --transport simtcp --debug` for 14 s: start, splash, acknowledgement screen, SIGUSR1 dump, SIGTERM shutdown in 0.2 s with 3 of 3 threads stopped. No tag, no release, no deployment |
| Final | Final report and pull request | Pending | | |

[Return to Table of Contents](#table-of-contents)

---

## 4.0 Notes

- WP1: mypy 1.20 and newer require Python 3.10 to run, so the marker leaves a Python 3.9 development interpreter without mypy. The check is run from a 3.10 or newer interpreter against the 3.9 target.
- WP3: `pygame/pkgdata.py` imports `pkg_resources` inside `try/except ImportError` and falls back to its own stubs, so a missing `pkg_resources` does not break `import pygame`. Verified with pygame 2.6.1: (a) Python 3.9.25 venv with setuptools 82.0.1 (`pkg_resources` absent): `import pygame`, `pygame.init()` and `pygame.font.Font(None, 20)` succeed; (b) Python 3.13 venv with no setuptools: the same, with warnings as errors, and the full suite passes. `bin/install.sh` and `bin/pi-install.sh` create the venv with `python3 -m venv` and never upgrade setuptools; the version that Debian 11 bundles was not measured (no device access) and does not matter given (a) and (b). `src/gtach/` does not use `pkg_resources`.
- WP4: each refreshed design was written after reading the corresponding source module; the body of every retired and merged document was read first. Layout coordinates and font sizes were copied from the source as constants and not re-derived. Not verified: Mermaid rendering on GitHub (no renderer in this environment); internal links were checked by script (25 files, 0 broken).
- WP8: the headless run logged two WARNING records for the framebuffer geometry query (`/dev/fb0` in the cloud container is not a framebuffer device); platform-related, recorded and not changed. The gauge was not drawn in that run, because the acknowledgement screen waits for a tap.
- WP8: full git history was fetched (`git fetch --unshallow`) to write the release notes; 419 commits since the v0.2.67 release notes.
- WP7: suite after remediation 818 passed (Python 3.13.18); mypy 1.20.2 clean with the 3.9 target; flake8 and black clean on the changed files. Deferred findings are rows in `ai/task.md`.
- WP4 defect candidates noted for WP7: `utils/updater.py` cannot parse a pre-release version such as `1.0.0rc1` (D1), which makes the update check return nothing while a release candidate is installed.

[Return to Table of Contents](#table-of-contents)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-13 | WP0 and WP1 |
| 1.1 | 2026-11-13 | WP2, WP3 and WP5 |
| 1.2 | 2026-11-13 | WP4 |
| 1.3 | 2026-11-13 | WP7 |
| 1.4 | 2026-11-13 | WP8 |

---

Copyright (c) 2026 William Watson. MIT License.
