# Report — Autonomous Release Run to v1.0.0 (f8d0064b)

Created: 2026 November 13

## Table of Contents

- [1.0 Summary](#10-summary)
- [2.0 Release Gate](#20-release-gate)
- [3.0 Work Packages](#30-work-packages)
- [4.0 Triples and Other Source Changes](#40-triples-and-other-source-changes)
- [5.0 Task Register](#50-task-register)
- [6.0 Owner Checklist](#60-owner-checklist)
- [7.0 Items for the Owner's Decision](#70-items-for-the-owners-decision)
- [8.0 Limits of This Run](#80-limits-of-this-run)
- [Version History](#version-history)

---

## 1.0 Summary

- **Plan:** `ai/workspace/proposal/proposal-f8d0064b-v1-release-autonomous-run.md`. **Step record:** `report-f8d0064b-run-log.md`.
- **Result:** the release gate (§2.0) is met. The repository is at release candidate `1.0.0rc1` on branch `claude/gtach-v1-release-run-g0106d`. Nothing was tagged, released or deployed.
- **Not done by design:** all testing on the Pi. The release candidate has not run on the device (§6.0).
- **Task register:** the seven starting rows are disposed of; eleven rows remain, all `Deferred` with a reason and an owner action (§5.0).
- **Source changes:** one triple (`c41037ea`) and one trivial change (P04.12), both from the release-readiness audit.
- **Interruptions:** the session was restarted once (usage limit) and resumed from the run log; no step was repeated.

[Return to Table of Contents](#table-of-contents)

---

## 2.0 Release Gate

| # | Check | Result | Evidence |
|---|---|---|---|
| G1 | Full `pytest tests/` passes; no new xfail or skip without a reason | Met | 818 passed on Python 3.13.18 and on Python 3.9.25 (baseline 780; 38 tests added). One conditional skip was added, in `tests/test_release_script.py`, when `bash` is absent; it did not trigger |
| G2 | `python -m mypy src/` clean with `python_version = "3.9"` | Met | mypy 1.20.2: no issues in 60 source files, without the "3.9 not supported" message |
| G3 | No new `flake8` or `black` finding in changed files | Met | `flake8` and `black --check` clean on every Python file changed since `2f32b45`; `src/` clean for flake8, black and isort |
| G4 | No active issue, change or prompt T-Doc | Met | `ai/workspace/{issues,change,prompt}/` hold only `README.md` and `closed/`; no triple awaits device verification |
| G5 | Every `ai/task.md` row removed with an outcome, or `Deferred`/`Parked` with reason and owner action | Met | §5.0 |
| G6 | Release-readiness audit closed, no open critical or high finding | Met | `ai/workspace/audit/closed/audit-bce0d69a-release-readiness.md` |
| G7 | Wheel and sdist build; wheel installs in a clean venv; `gtach --version` reports the new version | Met | `gtach-1.0.0rc1-py3-none-any.whl`, `gtach-1.0.0rc1.tar.gz`; clean Python 3.9.25 venv; `GTach 1.0.0rc1`; `--validate-config`, `--validate-dependencies` exit 0; `pip check` clean |
| G8 | Release notes, README and version agree | Met | `pyproject.toml` `1.0.0rc1`; `releases/RELEASE_NOTES_v1.0.0.md`; README Version History 2.8 |

Headless run of the installed wheel (`gtach --transport simtcp --debug`, 14 s, `SDL_VIDEODRIVER=dummy`): start-up, splash, acknowledgement screen, `SIGUSR1` thread dump, shutdown on `SIGTERM` in 0.2 s with 3 of 3 threads stopped. The gauge was not drawn, because the acknowledgement screen waits for a tap. Two WARNING records concern the framebuffer of the cloud container and are platform-related.

[Return to Table of Contents](#table-of-contents)

---

## 3.0 Work Packages

| WP | Outcome | Commits |
|---|---|---|
| WP0 Baseline | 780 passed (3.13 and 3.9). mypy 2.4.1 rejected the 3.9 target; mypy 1.19.1 on 3.9 reported 3 typeshed errors. Lint findings only in `tests/` | `904bf8f` |
| WP1 mypy | `mypy>=1.20,<2.0; python_version >= '3.10'`. 1.20 is the first release whose typeshed has the Linux Bluetooth socket constants; 2.0 dropped the 3.9 target. A Python 3.9 development interpreter gets no mypy | `904bf8f` |
| WP2 Render rows | `821919ce` and `9ed1c77e` dropped (D6); both were closed and not implemented | `874df8e` |
| WP3 `pkg_resources` | No guard needed. pygame 2.6.1 imports `pkg_resources` inside `try/except ImportError`; verified with setuptools 82.0.1 on Python 3.9 and with no setuptools on 3.13. Row dropped | `874df8e` |
| WP5 Bluetooth recovery | Row kept as `Deferred — after 1.0` (D3) | `874df8e` |
| WP4 Designs | 4 retired, 2 pairs merged, 19 rewritten or refreshed against the source, 2 link conversions; traceability matrix v2.0; design review report closed | `efc785e`, `91e8033`, `d232eb3` |
| WP7 Audit | `audit-bce0d69a`: 14 findings (0 critical, 1 high, 3 medium, 10 low); 9 resolved or resolved in part, 5 deferred; follow-up pass; closed | `55e6f5d`, `0bc4871` |
| WP8 Release preparation | Version `1.0.0rc1`, release notes, README, build and install test | `3b7b552` |

Notes on WP4:

- The four documents listed for a status-line correction (`b1c2d3e4`, `c2d3e4f5`, `d3e4f5a6`, `e4f5a6b7`) had drifted well beyond the status line (abstract-method interface, a macOS branch, different exception names). They were rewritten, which is more than the review report proposed.
- `e5f6a7b8` (the older OBD design) carried the newest content, the vehicle silent state. It was folded into `f5a6b7c8` before retirement.
- Refreshed documents are shorter than their predecessors; the 2025 text remains in git history and in `design/closed/` for the retired ones.

[Return to Table of Contents](#table-of-contents)

---

## 4.0 Triples and Other Source Changes

| ID | Type | Subject | Review | Status |
|---|---|---|---|---|
| `c41037ea` | Issue, change, prompt | The update check could not parse a pre-release version. With `1.0.0rc1` installed, "Check for updates" found nothing; a staged `1.0.0rc1` wheel was never offered. `utils/updater.py` now orders `a`, `b` and `rc` versions below their final release | Subagent, fresh context: REVISE (an oversized digit string raised instead of returning `None`), then SHIP | Closed; report `report-c41037ea-update-version-ordering.md`; approvals `686b945`, `322c990`, `26f7ea6` |
| `b2077e6` | Trivial change (P04.12) | `OBDProtocol._request_rpm`: a reply with an odd number of hexadecimal digits is dropped instead of raising inside the handler and logging an ERROR with traceback per poll | Not reviewed by a subagent (two-line delta; regression test fails without it) | Commit is the record |

Non-source remediation of the audit (`55bdbd1`): `LICENSE` added; `bin/release.sh` publishes a non X.Y.Z version with `--prerelease`; `ai/context.md`, `README.md`, `docs/GTach_cli_cmds.md` and `DISCLAIMER.md` corrected; `build` removed from `build-system.requires`.

New test modules: `tests/test_update_version_ordering.py` (26), `tests/test_rpm_reply_decoding.py` (5), `tests/test_release_script.py` (7).

[Return to Table of Contents](#table-of-contents)

---

## 5.0 Task Register

### 5.1 Starting rows

| Row | Outcome |
|---|---|
| mypy `python_version = "3.9"` | Removed; mypy pinned (WP1) |
| `821919ce` render caching | Removed; explicit drop |
| `9ed1c77e` conditional render | Removed; explicit drop |
| In-car normal use | Kept, `Deferred`; owner action after 1.0 (D2) |
| Stuck Bluetooth recovery | Kept, `Deferred — after 1.0`; needs an owner design decision and device reproduction (D3) |
| Design review | Removed; applied (WP4) |
| pygame `pkg_resources` | Removed; no fault (WP3) |

### 5.2 Rows added in this run (all `Deferred`)

| Row | Owner action |
|---|---|
| Lint debt in `tests/` (D7) | One mechanical formatting change after 1.0 |
| Validation hook not provisioned (D8) | Provision an adapted hook, or record a standing exemption |
| `requirements-gtach-master.md` predates the source | Requirements review; then populate the requirement rows of the traceability matrix |
| `src/devop.md` stale (audit L04) | Delete, or move to `docs/` |
| `issue-<pending>` comments and a wrong log text in `display/manager.py` (L06) | Cosmetic change after 1.0 |
| Paths fixed under `/opt/gtach` (L07) | Change together with `gtach-preflight.sh` |
| No tests for `utils/ack_state.py` (L08) | Add tests after 1.0 |
| `build.sh` version prompt; README §3.1 update command (L09) | After 1.0 |
| `pyproject.toml` license metadata deprecated; status classifier (L05, L10) | SPDX form before 2027-02-18; classifier at 1.0.0 |

[Return to Table of Contents](#table-of-contents)

---

## 6.0 Owner Checklist

All on the Pi, in one session, after merging the pull request (proposal §9.0).

1. **Deploy:** `./bin/deploy.sh`. At the `build.sh` prompt press Enter to keep `1.0.0rc1` (the prompt accepts only X.Y.Z).
2. **Splash:** the version text `v1.0.0rc1` is 251 px wide at its position (calculated; the chord there is 387 px). Confirm that it is not clipped on the panel.
3. **Bench test with `ELM327-Emulator.local`:** start-up, acknowledgement, connection, live RPM, link loss and restore, DISCONNECTED cause text, Engine off, setup flow, OPTIONS pages, palette toggle, Reset.
4. **Update path (triple `c41037ea`):** with `1.0.0rc1` installed, stage a higher version (`./bin/deploy.sh --stage`, for example the `1.0.0` build of step 7), run "Check for updates", confirm that the version is offered, install, and confirm the restart and that `/opt/gtach/.update-probation` is removed.
5. **Logs:** `error.log` free of unexpected ERROR records; no `RPM request error` records.
6. **`LICENSE`:** confirm the copyright line (§7.0).
7. **Release:** set `version = "1.0.0"`, update the release date in `releases/RELEASE_NOTES_v1.0.0.md`, rebuild, push, run `./bin/release.sh`. For a version that is not X.Y.Z the script now publishes a pre-release; it was not run in this session.
8. **In-car test:** after 1.0 (D2).

[Return to Table of Contents](#table-of-contents)

---

## 7.0 Items for the Owner's Decision

1. **`LICENSE` (new file).** The repository had no license file, although the source headers and `DISCLAIMER.md` refer to one and `pyproject.toml` declares MIT. The standard MIT text was added with the line `Copyright (c) 2025-2026 William Watson`. The year range and the holder's name are my reading of the source headers; confirm or correct them.
2. **Audit closure and delegated approvals.** The audit and the triple were closed under the delegation of proposal §3.0. The pull request is the owner's review of those closures.
3. **Design refresh depth.** WP4 rewrote most design documents instead of patching them (§3.0). If the earlier, longer form is preferred for any document, it can be restored from git history.
4. **`mypy` marker.** A Python 3.9 development interpreter installs no mypy with the new pin. If type checking under a 3.9 interpreter is wanted, the alternative is mypy 1.19.1 with three `type: ignore[attr-defined]` comments on the Bluetooth socket constants.
5. **Status classifier.** `Development Status :: 4 - Beta` was left unchanged.

[Return to Table of Contents](#table-of-contents)

---

## 8.0 Limits of This Run

- **No device.** No statement in this report was verified on the Pi, with a Bluetooth adapter, or in a vehicle. The Python 3.9 interpreter used here has no `socket.AF_BLUETOOTH`.
- **Audit depth.** `src/gtach/` was not re-read in full; the audit relied on `audit-71ab3751` for modules unchanged since then and read the changed and release-relevant modules in full (audit §2.2). Confidence that no high finding remains in the unread parts is moderate; it rests on the earlier audit and the 818 tests.
- **Scripts.** `bin/` scripts were read and syntax-checked, not executed; `release.sh` in particular was not run against GitHub.
- **Diagrams.** Mermaid diagrams in the refreshed designs were not rendered; internal links were checked by script.
- **Reviewer independence.** The review subagents ran the same model as the worker; the owner's review of the pull request is the independent check.
- **Release notes.** The summary since v0.2.67 was written from commit subjects and closed reports, not from a re-read of each change.

[Return to Table of Contents](#table-of-contents)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-13 | Final report of run f8d0064b |

---

Copyright (c) 2026 William Watson. MIT License.
