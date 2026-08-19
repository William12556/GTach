Created: 2026 July 29

# Task List

Open work only. Completed and deferred items are removed once their
governance documents (`ai/workspace/{issues,change,prompt}/closed/`)
record the outcome.

| ID         | Item                                                                                                                                                                                                           | Status                                                                                        | References                                            |
| ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- | ----------------------------------------------------- |
| —          | `faulthandler` output not captured in app-owned log files under systemd (`app.py:42-44` targets `sys.stderr`, which systemd routes to the journal, not `debug.log`/`start.log`)                                | Open                                                                                          | —                                                     |
| —          | OBD response stream desynchronises during initialisation (`0100` timeout during ELM327 protocol search leaves an undrained late response, offsetting reads by one command until steady-state polling recovers) | Open, not yet raised as a T03                                                                 | Related: `issue-a3f1d8e2` (closed, same defect class) |
| `2ac1c602` | Display freezes permanently after startup when no OBD connection is available; confirmed root cause: WatchdogMonitor's critical-thread shutdown path never terminates the process, so systemd's `Restart=always` never engages (secondary hypothesis under investigation: RFCOMM `connect()` not honouring its socket timeout)          | Investigating — root cause confirmed, fix not yet designed                          | `issue-2ac1c602`                                       |
| `821919ce` | Render caching                                                                                                                                                                                                 | Deferred — own withdrawal condition met (frames complete well inside budget); not implemented | `issue-821919ce`, `change-821919ce`                   |
| `9ed1c77e` | Conditional render (Part 3 only — `fps_limit` reduction and import/f-string housekeeping already shipped)                                                                                                      | Deferred — same basis as `821919ce`; not implemented                                          | `issue-9ed1c77e`, `change-9ed1c77e`                   |
| —          | `device_surfaces.py` contains two apparently duplicate rendering blocks for device name/type/signal text (~lines 160–220 fixed literal sizes; ~lines 295–370 `scale_factor`-derived sizes) — redundancy not yet confirmed | Deferred — investigation of calling context required before scoping                           | —                                                     |
| `479b2e51` | Select Device screen: 3 fixed slots always shown, centred vertically; only the middle (focused) slot selectable and border+tint indicated, empty slots as outlined frames, swipe-only 1-device focus shift, arrows shown per device presence on each side | Proposed — change document revised to focused-index model; T04 prompt not yet drafted | `issue-479b2e51`, `change-479b2e51`                   |


---

Copyright (c) 2026 William Watson. MIT License.
