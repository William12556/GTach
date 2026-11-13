Created: 2026 July 29

# Task List

All open work: open triples, items not yet raised as a triple, and
deferred or parked items (governance P00.20). A row is removed once its
outcome is recorded (a closed triple, or an explicit drop).

| ID | Item | Status | References |
| --- | --- | --- | --- |
| — | In-car normal use (audit-36b6ea95 Session I); vehicle not yet prepared. General regression check on version 0.5.0 or later | Deferred (2026-11-12) — in-car tests not possible yet | `ai/workspace/test/closed/test-36b6ea95-on-device-verification.md` §4.9 |
| — | New work: automatic recovery from the stuck Bluetooth state. After an out-of-range link loss (2026-10-08 13:45) every reconnect failed with EBUSY ('Device or resource busy') for 2.5 min, including after the adapter was back in range; GTach correctly reported 'bluetooth wedged - reset required', but only a Pi reset restored the link. Scope (e.g. controller reset via btmgmt/hciconfig, or RFCOMM/ACL release, before falling back to operator reset) to be decided | Deferred — after 1.0; reverses the issue-5e7a03c4 host-action constraint; needs owner design decision and device reproduction (proposal-f8d0064b D3). Not reproduced in device sessions A and B (2026-11-12). An adapter whose radio is off no longer escalates to "wedged" (`change-76ef5387`, closed) | `comm/transport.py`, `comm/rfcomm.py`; related `issue-5e7a03c4`; evidence `logs/error.log` 2026-10-08 13:45–13:48 |
| — | Review `ai/workspace/design/` for stale designs and decide per document whether to update, merge or retire it | Open — triage written; per-document decisions pending | `ai/workspace/report/report-71ab3751-design-review.md` |

---

Copyright (c) 2026 William Watson. MIT License.
