Created: 2026 July 29

# Task List

All open work: open triples, items not yet raised as a triple, and
deferred or parked items (governance P00.20). A row is removed once its
outcome is recorded (a closed triple, or an explicit drop).

| ID | Item | Status | References |
| --- | --- | --- | --- |
| `b29cbd71` | New work: "engine off" state. When the adapter is connected but the vehicle does not answer 0100 (ignition off), the display shows DISCONNECTED, because `DisplayManager._link_lost()` also treats missing RPM data as a lost link. Proposed: show the gauge with the needle at zero and an "Engine off" indication instead. Design points: how the protocol reports the state to the display (the transport is connected; `OBDProtocol` knows the vehicle is silent); keeping `_link_lost`'s rule that a stale needle is never shown as live; behaviour when RPM stops mid-drive (engine stalled versus adapter lost) | Open — change approved; awaiting implementation | `issue-b29cbd71`, `change-b29cbd71`, `prompt-b29cbd71`; design-e5f6a7b8 §6.3, design-b8c9d0e1 §5.4; device session A, step A7 (2026-11-12) |
| — | `DEVICE_NOT_SAVED_TEXT` "Device not saved" measures 221 px, 1 px over the DEVICE_LIST error line, so `_fit_text` shortens it. Candidate text "Not saved". The width test marks it strict xfail | Open — small text change; T03 not yet raised | `report-146491ba` §3.0 (closed); `tests/test_session_b_findings.py` |
| — | First normal connect after setup is aborted (`ECONNABORTED`) and recovers about 6 s later | Open — observation | Device session B and the 146491ba device check (2026-11-12); `comm/transport.py` |
| — | "Error communicating with device: [Errno 9] Bad file descriptor" logged at ERROR on every planned disconnect (service stop, Clear settings). Expected for a planned close; should not be ERROR | Open — observation | Device session B (2026-11-12); `comm/` read loop |
| — | First connect after boot fails with `EHOSTUNREACH` ("no bluetooth controller") and succeeds about 5 s later; the controller is not yet up when GTach starts. Related: a simulated pairing failure is logged at ERROR | Open — observation | Device session B (2026-11-12); `bin/gtach.service`; `comm/transport.py` |
| — | Simulated discovery shows the fallback notice: `SimBluetoothPairing._FAKE_DEVICES` set no `device_classification`, so all four are `UNKNOWN` and DEVICE_LIST in a `simbt` session shows "No ELM327". Fix: classify the fake devices (for example the ELM327-named ones as `HIGHLY_LIKELY_ELM327`) so that simulation exercises the normal path; one fake device could stay unclassified to keep the fallback reachable | Open — small change; T03 not yet raised | `report-34781bfe` §9 item 10 (closed); `comm/sim_bluetooth.py` |
| — | `[tool.mypy] python_version = "3.9"` is not selectable in the installed mypy release; the device runs Python 3.9. Decide: pin an older mypy, or raise the value | Open — owner decision | `change-042dd7ff` notes (closed); `pyproject.toml` |
| `821919ce` | Render caching | Deferred — own withdrawal condition met (frames complete well inside budget); not implemented. Re-evaluate with measured frame times | `issue-821919ce`, `change-821919ce` |
| `9ed1c77e` | Conditional render (Part 3 only — `fps_limit` reduction and import/f-string housekeeping already shipped) | Deferred — same basis as `821919ce`; not implemented | `issue-9ed1c77e`, `change-9ed1c77e` |
| — | In-car normal use (audit-36b6ea95 Session I); vehicle not yet prepared. General regression check on version 0.5.0 or later | Deferred (2026-11-12) — in-car tests not possible yet | `ai/workspace/test/closed/test-36b6ea95-on-device-verification.md` §4.9 |
| — | New work: automatic recovery from the stuck Bluetooth state. After an out-of-range link loss (2026-10-08 13:45) every reconnect failed with EBUSY ('Device or resource busy') for 2.5 min, including after the adapter was back in range; GTach correctly reported 'bluetooth wedged - reset required', but only a Pi reset restored the link. Scope (e.g. controller reset via btmgmt/hciconfig, or RFCOMM/ACL release, before falling back to operator reset) to be decided | Open — not reproduced in device sessions A and B (2026-11-12); T03 not yet raised | `comm/transport.py`, `comm/rfcomm.py`; related `issue-5e7a03c4`; evidence `logs/error.log` 2026-10-08 13:45–13:48 |
| — | Review `ai/workspace/design/` for stale designs and decide per document whether to update, merge or retire it | Open — triage written; per-document decisions pending | `ai/workspace/report/report-71ab3751-design-review.md` |
| — | pygame 2.6.1 imports the deprecated `pkg_resources`; setuptools 81 or newer may break the import | Open — monitor; pin `setuptools<81` or upgrade pygame if it breaks | `pyproject.toml` |

---

Copyright (c) 2026 William Watson. MIT License.
