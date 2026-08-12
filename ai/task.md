Created: 2026 July 29

# Task List

Open work only. Completed and deferred items are removed once their
governance documents (`ai/workspace/{issues,change,prompt}/closed/`)
record the outcome.

| ID         | Item                                                                                                                                                                                                           | Status                                                                                        | References                                            |
| ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- | ----------------------------------------------------- |
| —          | `faulthandler` output not captured in app-owned log files under systemd (`app.py:42-44` targets `sys.stderr`, which systemd routes to the journal, not `debug.log`/`start.log`)                                | Open                                                                                          | —                                                     |
| —          | OBD response stream desynchronises during initialisation (`0100` timeout during ELM327 protocol search leaves an undrained late response, offsetting reads by one command until steady-state polling recovers) | Open, not yet raised as a T03                                                                 | Related: `issue-a3f1d8e2` (closed, same defect class) |
| `2ac1c602` | Display goes blank after startup, reported to correlate with absence of an active Emulator/Bluetooth OBD connection; root cause not yet determined, no `--debug` log evidence captured yet                     | Open, investigation pending on-target reproduction with `--debug`                             | `issue-2ac1c602`                                       |
| `821919ce` | Render caching                                                                                                                                                                                                 | Deferred — own withdrawal condition met (frames complete well inside budget); not implemented | `issue-821919ce`, `change-821919ce`                   |
| `9ed1c77e` | Conditional render (Part 3 only — `fps_limit` reduction and import/f-string housekeeping already shipped)                                                                                                      | Deferred — same basis as `821919ce`; not implemented                                          | `issue-9ed1c77e`, `change-9ed1c77e`                   |


---

Copyright (c) 2026 William Watson. MIT License.
