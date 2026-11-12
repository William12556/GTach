Created: 2026 July 29

# Task List

All open work: open triples, items not yet raised as a triple, and
deferred or parked items (governance P00.20). A row is removed once its
outcome is recorded (a closed triple, or an explicit drop).

| ID | Item | Status | References |
| --- | --- | --- | --- |
| `76ef5387` | Task register fixes: "Not saved" text; simulated devices classified; EBADF on a planned close and a failed pairing no longer ERROR; ECONNABORTED mapped; `gtach.service` ordered after `hciuart.service`; "adapter not reachable" excluded from the wedge diagnosis | Open — triple raised; T03 awaiting approval | `issue-76ef5387`, `change-76ef5387`, `prompt-76ef5387` |
| — | `[tool.mypy] python_version = "3.9"` is not selectable in the installed mypy release; the device runs Python 3.9. Decide: pin an older mypy, or raise the value | Open — owner decision | `change-042dd7ff` notes (closed); `pyproject.toml` |
| `821919ce` | Render caching | Deferred — own withdrawal condition met (frames complete well inside budget); not implemented. Re-evaluate with measured frame times | `issue-821919ce`, `change-821919ce` |
| `9ed1c77e` | Conditional render (Part 3 only — `fps_limit` reduction and import/f-string housekeeping already shipped) | Deferred — same basis as `821919ce`; not implemented | `issue-9ed1c77e`, `change-9ed1c77e` |
| — | In-car normal use (audit-36b6ea95 Session I); vehicle not yet prepared. General regression check on version 0.5.0 or later | Deferred (2026-11-12) — in-car tests not possible yet | `ai/workspace/test/closed/test-36b6ea95-on-device-verification.md` §4.9 |
| — | New work: automatic recovery from the stuck Bluetooth state. After an out-of-range link loss (2026-10-08 13:45) every reconnect failed with EBUSY ('Device or resource busy') for 2.5 min, including after the adapter was back in range; GTach correctly reported 'bluetooth wedged - reset required', but only a Pi reset restored the link. Scope (e.g. controller reset via btmgmt/hciconfig, or RFCOMM/ACL release, before falling back to operator reset) to be decided | Open — not reproduced in device sessions A and B (2026-11-12); T03 not yet raised. The misleading "wedged" cause for an adapter whose radio is off is addressed by `change-76ef5387` EDIT G | `comm/transport.py`, `comm/rfcomm.py`; related `issue-5e7a03c4`; evidence `logs/error.log` 2026-10-08 13:45–13:48 |
| — | Review `ai/workspace/design/` for stale designs and decide per document whether to update, merge or retire it | Open — triage written; per-document decisions pending | `ai/workspace/report/report-71ab3751-design-review.md` |
| — | pygame 2.6.1 imports the deprecated `pkg_resources`; setuptools 81 or newer may break the import | Open — monitor; pin `setuptools<81` or upgrade pygame if it breaks | `pyproject.toml` |

---

Copyright (c) 2026 William Watson. MIT License.
