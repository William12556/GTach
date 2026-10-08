Created: 2026 October 07

# Report: audit-36b6ea95 Full-Codebase Remediation

---

## Table of Contents

1. [Summary](<#1. summary>)
2. [Remediation by Phase](<#2. remediation by phase>)
3. [Finding Disposition](<#3. finding disposition>)
4. [Tests and Tooling](<#4. tests and tooling>)
5. [Open Issues Raised](<#5. open issues raised>)
6. [Deviations](<#6. deviations>)
7. [On-Device Verification Outstanding](<#7. on-device verification>)
8. [Version History](<#version history>)

---

## 1. Summary

The static audit [audit-36b6ea95](../audit/audit-36b6ea95-full-codebase.md) (commit `816f73f`, version 1.7) recorded 85 findings: 1 critical, 6 high, 30 medium and 48 low.

Remediation ran in Phases 0 to 5, with Phase 4 (tests) last. It covered 15 issue/change/prompt sets and two direct commits (F05, E03).

- **Findings with a remediation set:** 74 of the 85, including the critical finding and all high findings. Every set is implemented. Its prompt is closed, and its issue and change documents stay active until on-device verification (Section 7).
- **Findings without one (11):**
  - recorded without change as accepted risks or trust assumptions: C03, D10, E06, G09;
  - fixed directly or under another set: F05, X03;
  - addressed by tests: F02 fully, F01 in part;
  - raised now as new issues: A14 (remaining part), B11 (remaining part), F04.
- **New issues:** nine, for every defect that remains unrepaired (Section 5).
- **Tests:** 287 passed at the start; 454 passed and 2 strict xfails on `34c1ffd`. The two xfails are new issues `50bf25ad` and `04c18cda`.

[Return to Table of Contents](<#table of contents>)

---

## 2. Remediation by Phase

| Phase | Set | Findings | Implementation commit | Report |
|---|---|---|---|---|
| 0 | — (direct) | F05 | `10954e9` | — |
| 0 | `b9ee7428` | B13 | `29bdebe` | report-b9ee7428 |
| 0 | `269871a0` | B04, A11 | `5f3c50b` | report-269871a0 |
| 0 | — (direct, P04.12) | E03 | `afca40b` | — |
| 1 | `e9216e17` | D01 (critical), X01 | `f22640a` | report-e9216e17 |
| 1 | `fbe7e98a` | D03, D06, C04, C02, D12 | `523bb21` | report-fbe7e98a |
| 1 | `860fd5f7` | A01/B02, B01, B05, B03 | `f5d58f5` | report-860fd5f7 |
| 1 | `70789d75` | D02 | `b814ed9` | report-70789d75 |
| 2 | `907de6de` | A02-A06, A19 | `41dd663` | report-907de6de |
| 2 | `674bec49` | C01, C05, C06, C08 | `5ea2cfd` | report-674bec49 |
| 3 | `5fbff586` | E01, E02, E04, E08, G07, X04 | `f5ab73a` | report-5fbff586 |
| 3 | `453f0a80` | A09, A10 | `3747d2f` | report-453f0a80 |
| 5 | `52653cd6` | G01, G02, G03, G04, G06, G08, E05 | `f9273e0` | report-52653cd6 |
| 5 | `d140121d` | A07, A08, A17, C14, D04, D05, X02 | `69eb605` | report-d140121d |
| 5 | `4005360c` | A12, A13, A16, A18, B07, B09, B10, B12, C10, C13, C15, C16, D08, D11 | `2ade5a3` | report-4005360c |
| 5 | `cd5ec050` | A15, B06, B08, C11, C12, C17, D07, D09, E03, E07, F03, F06 | `f789966` | report-cd5ec050 |
| 5 | `e4ee50fd` | G05 | `d44dca9` | report-e4ee50fd |
| 4 | — (tests only, P04.11) | F01 (part) | `34c1ffd` | this report |

Each phase closed with a T-Doc commit: `3b8bea4`, `c9e23cb`, `9eaffa1`, `366b555` and `501a008`.

Notable structural results:
- **Concurrency:** no call-outs under a lock, now CLAUDE.md §4 rule 8.
- **Recovery:** process restart replaces in-process thread restart.
- **Watchdog:** monotonic timing.
- **Logging:** an always-on `error.log`.
- **Configuration:** one ConfigStore and one DeviceStore under GTACH_HOME.
- **Service:** hardened `gtach.service` with bounded stop and start limits.
- **Dead code:** about 10,000 lines of unused code removed: about 1,500 net in Phase 3 and 8,669 in Phase 5.
- **Formatting:** one formatting pass at 88 columns.

[Return to Table of Contents](<#table of contents>)

---

## 3. Finding Disposition

| Disposition | Findings | Count |
|---|---|---|
| Implemented under a remediation set (Section 2) | All findings with an `issue_ref` in the audit YAML | 74 |
| Fixed directly | F05 (`10954e9`) | 1 |
| Resolved by another set | X03 (issue-907de6de) | 1 |
| Addressed by tests | F02 (regression tests, Phases 0-5); F01 in part (lifecycle test `34c1ffd`; coverage not re-measured) | 2 |
| Recorded without change | C03 (accepted risk), D10 (no impact), E06 and G09 (trust assumptions: root-owned `/opt/gtach/updates`; GitHub TLS for provisioning) | 4 |
| Remaining part raised as a new issue | A14 → `c9de5fb0`; B11 → `2b3a1547`; F04 → `8a9022fc` | 3 |
| **Total** | | **85** |

Corrections to the audit text:
- **C01:** it still says "the remaining C01 items are open" (added in version 1.3). change-674bec49 (Phase 2) closed them: setup completion and re-entry now stop the active SetupDisplayManager.
- **A14:** two of its three parts were removed by change-5fbff586 and change-cd5ec050.
- **B11:** its hard-coded version was removed by change-52653cd6.

[Return to Table of Contents](<#table of contents>)

---

## 4. Tests and Tooling

**pytest progression:**

| Point | Result |
|---|---|
| Phase 0 baseline | 287 passed |
| After Phase 0 | 302 passed |
| After Phase 1 | 339 passed |
| After Phase 2 | 372 passed |
| After Phase 3 | 399 passed |
| After Phase 5 | 447 passed |
| After Phase 4 (`34c1ffd`) | 454 passed, 2 xfailed |

**Tooling:**
- **Test isolation:** the suite writes neither to the repository nor to `/opt/gtach`. `GTACH_HOME` is a session temporary directory, and `git status --porcelain` is clean after a run.
- **Phase 4 lifecycle module:** `tests/test_lifecycle_sim.py` runs in about 22.6 s, below its 30 s budget.
- **Formatting:** black and isort pass at 88 columns. `flake8 --select E1,E2,E3,E5,W2,W3` is clean on src and tests, and `--select F401,F841,F811,F402,F541` is clean on `src/gtach`.
- **mypy:** 465 errors in scope at audit time; 333 errors in 38 files at `34c1ffd`. CLAUDE.md §4 rule 2 is still not met (issue `ac11505d`).
- **Measured coverage:** not re-run after the audit.

[Return to Table of Contents](<#table of contents>)

---

## 5. Open Issues Raised

All nine are `open`, with no change documents yet.

| Issue | Severity | Defect | Source |
|---|---|---|---|
| `issue-50bf25ad` | medium | SimTransport inherits `drop_link` but `is_connected` reads `_connected`, so a link drop is never observed with the simulator (`transport.py:416`, `sim_transport.py:61-69`) | Phase 4 strict xfail |
| `issue-04c18cda` | low | `_initialize_protocol` sleeps 1.5 s with `time.sleep` and no heartbeat when the adapter is pre-initialised (`obd.py:148`) | Phase 4 strict xfail |
| `issue-ac11505d` | medium | mypy: 333 errors in 38 files | Audit Section 2 |
| `issue-c9de5fb0` | low | Two BluetoothDevice models converted by hand at two sites | A14 (remaining) |
| `issue-2b3a1547` | low | `import gtach` eagerly imports app, pygame and the transport stack | B11 (remaining) |
| `issue-8a9022fc` | low | `TestSlotContents` asserts against its own copy of the slot rule | F04 |
| `issue-e215a184` | low | Durations and cache ages outside change-4005360c's file list still use `time.time()` | C16 residue, report-4005360c |
| `issue-273ca048` | low | Unreferenced helpers kept by change-cd5ec050, an unreachable splash trim branch, an unused test constant | report-cd5ec050, report-4005360c |
| `issue-ae65fa10` | low | `ConfigStore.save` on a store that never loaded drops unknown keys (latent; no current caller) | report-5fbff586 |

Not raised, because no defect is reachable: `_gauge_max_rpm` would raise on a non-numeric `redline_rpm`, but the value comes only from the packaged engine profiles, which are integers (report-674bec49).

The pre-existing `ai/task.md` rows (faulthandler capture, OBD response desynchronisation, and others) predate the audit and are outside this report.

[Return to Table of Contents](<#table of contents>)

---

## 6. Deviations

Recorded per set in each implementation report. Recurring across phases:

1. **`implemented_by`:** it is "Claude Code" in all change documents, without the requested model identifier, because model identifiers are not written into repository files.
2. **Inserted `issue_ref` fields:** low-severity findings in the audit YAML had no `issue_ref` field. It was inserted where a set addressed them: Phases 2, 3 and 5, 41 fields in all.
3. **Test hosts:** several existing test hosts built without `__init__` gained attributes for later changes (`_has_device`, `_ops_lock`, `_obd_lock`, a `shutdown` stub). No assertion was weakened.
4. **Phase 4 audit note:** the note names the lifecycle commit by its subject line, because a commit cannot contain its own hash. The hash is `34c1ffd`.

[Return to Table of Contents](<#table of contents>)

---

## 7. On-Device Verification

Completed 2026-10-07 to 2026-10-08 on `gtach.local` (0.4.5 to 0.4.9) with `bin/gtach-verify-36b6ea95.sh` and the manual guide [`test-36b6ea95-on-device-verification.md`](../test/test-36b6ea95-on-device-verification.md). Results are recorded in each issue's `verification` block; all 15 remediation issue/change pairs are closed.

- **Passed on device:** `b9ee7428`, `269871a0`, `e9216e17`, `fbe7e98a`, `860fd5f7` (including a 6 h soak), `907de6de` (vehicle-off test with the emulator `engineoff` scenario), `674bec49`, `5fbff586`, `453f0a80`, `52653cd6`, `d140121d`, `4005360c`.
- **Not applicable:** the `907de6de` closed-socket step (TCP only; GTach uses RFCOMM).
- **Covered by automated tests instead of a manual step:** simtcp SIGTERM (`860fd5f7`) and simbt discovery after Cancel (`4005360c`).
- **No on-device step:** `70789d75`, `e4ee50fd`, `cd5ec050` (bench use without regression; in-car use pending vehicle preparation, tracked in `ai/task.md`).
- **Defects found during verification and fixed (all closed):**
  - `dc52c4e4`: OBD initialisation never recovered after a late `0100` reply (regression exposed by `907de6de`);
  - `fe755cfd` and `1a8f40ea`: faulthandler stack dumps (periodic, then SIGUSR1) crashed the process; replaced by a Python-level SIGUSR1 handler;
  - `b0a9cb20`: WELCOME error message unreadable (contrast 1.18:1); now dark red.
- **Open items recorded in `ai/task.md`:** automatic recovery from the stuck Bluetooth (EBUSY) state as new work; small DEVICE_LIST signal bars; in-car use.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-07 | Initial remediation report for audit-36b6ea95, Phases 0-5. |
| 1.1 | 2026-10-08 | Section 7: on-device verification completed; remediation documents closed; follow-up fixes and open items listed. |

---

Copyright (c) 2026 William Watson. MIT License.
