Created: 2026 July 29

# Task List

All open work: open triples, items not yet raised as a triple, and
deferred or parked items (governance P00.20). A row is removed once its
outcome is recorded (a closed triple, or an explicit drop).

| ID | Item | Status | References |
| --- | --- | --- | --- |
| — | In-car normal use (audit-36b6ea95 Session I); vehicle not yet prepared. General regression check on version 0.5.0 or later | Deferred (2026-11-12) — in-car tests not possible yet | `ai/workspace/test/closed/test-36b6ea95-on-device-verification.md` §4.9 |
| — | New work: automatic recovery from the stuck Bluetooth state. After an out-of-range link loss (2026-10-08 13:45) every reconnect failed with EBUSY ('Device or resource busy') for 2.5 min, including after the adapter was back in range; GTach correctly reported 'bluetooth wedged - reset required', but only a Pi reset restored the link. Scope (e.g. controller reset via btmgmt/hciconfig, or RFCOMM/ACL release, before falling back to operator reset) to be decided | Deferred — after 1.0; reverses the issue-5e7a03c4 host-action constraint; needs owner design decision and device reproduction (proposal-f8d0064b D3). Not reproduced in device sessions A and B (2026-11-12). An adapter whose radio is off no longer escalates to "wedged" (`change-76ef5387`, closed) | `comm/transport.py`, `comm/rfcomm.py`; related `issue-5e7a03c4`; evidence `logs/error.log` 2026-10-08 13:45–13:48 |
| — | Existing `black`, `isort` and `flake8` findings in `tests/` (3 files to reformat, 1 import order, 5 × F401, 1 × E731); `src/` is clean | Deferred — after 1.0; out of scope of run f8d0064b (D7); one mechanical formatting change | `report-f8d0064b-run-log` §2.0 |
| — | Validation hook (governance P00.18) is not provisioned: `.claude/settings.json` and `.claude/hooks/run-tests.sh` do not exist; the canonical hook assumes `tests/<component>/`, GTach tests are flat | Deferred — owner decision (D8): provision an adapted hook, or record a standing exemption. Progressive validation (P15.15) is run manually meanwhile | `proposal-f8d0064b` D8 |
| — | `requirements-gtach-master.md` predates the source in places (macOS development mode, layout switching by swipe, BluetoothManager-era wording); the traceability matrix therefore has no requirement rows | Deferred — after 1.0; owner review of the requirements baseline (P11.6), then populate matrix §2.0 and §3.0 | `ai/workspace/trace/trace-traceability-matrix-master.md` §1.0 |

---

Copyright (c) 2026 William Watson. MIT License.
