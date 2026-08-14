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
| `950128c0` | Remove rim border and shift-state cue from all screens (no replacement indicator on any channel, per requester)                                                                                                | Open — T-Docs created, prompt not yet executed                                                | `issue-950128c0`, `change-950128c0`, `prompt-950128c0` |
| `4ab5ff88` | Replace DISCONNECTED screen's Bluetooth Reset button (hciconfig reset, unreliable in the field) with a Reset button that reboots the Pi directly via `/sbin/reboot`                                            | Open — prompt ready to execute: `implement ai/workspace/prompt/prompt-4ab5ff88-disconnected-reset-button.md` in Claude Code                | `issue-4ab5ff88`, `change-4ab5ff88`, `prompt-4ab5ff88` |
| `e22142da` | `DisplayMode.ACKNOWLEDGEMENT` is fully rendered/dismissed but has no entry trigger anywhere in `src/gtach/`; add `_enter_post_splash_mode()` gate at the six normal-operation entry points (found via `report-b64d2b77`, §4.0 Finding A) | Open — prompt ready to execute: `implement ai/workspace/prompt/prompt-e22142da-acknowledgement-screen-unreachable.md` in Claude Code | `issue-e22142da`, `change-e22142da`, `prompt-e22142da` |


---

Copyright (c) 2026 William Watson. MIT License.
