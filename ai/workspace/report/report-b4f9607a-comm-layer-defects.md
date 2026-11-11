Created: 2026 November 11

# Report: Communication Layer Corrections

---

## Table of Contents

1. [Summary](<#1. summary>)
2. [Changes by Edit](<#2. changes by edit>)
3. [Comment Rule](<#3. comment rule>)
4. [Tests](<#4. tests>)
5. [Success Criteria](<#5. success criteria>)
6. [Deviations and Notes for the Planner](<#6. deviations and notes for the planner>)
7. [Version History](<#version history>)

---

## 1. Summary

prompt-b4f9607a (change-b4f9607a, issue-b4f9607a; run 2 of proposal-71ab3751) was implemented in one commit on branch `claude/comm-layer-defects-prompt-93kn4j`. EDITS A to J and the COMMENT RULE were applied. The issue and change T-Docs remain active pending test results. The prompt T-Doc was closed and moved to `ai/workspace/prompt/closed/`.

- pytest `tests/`: 619 passed (589 before, plus 30 in the new module).
- mypy `src/`: no issues. No `type: ignore` was added; the one at `BluetoothDevice.last_connected` was removed.
- black, isort and flake8 report nothing in the touched files.
- `git diff` touches only `src/gtach/comm/`, `tests/` and the T-Docs under `ai/workspace/`.

[Return to Table of Contents](<#table of contents>)

---

## 2. Changes by Edit

| Edit | File | Change |
|---|---|---|
| A (A01) | `transport.py` | `connect()` tests `_shutdown` under `_lock` after `_open()` returns. If it is set, the handle is not assigned, the state is set to DISCONNECTED, and the method returns False. The handle is then closed with `self._close` outside the lock, with `_IO_ERRORS` suppressed, the same way `_discard_handle_locked` does it. `disconnect()` is unchanged. |
| B (A03) | `transport.py` | The connect cause is classified before the counter. A cause equal to `_CONNECT_FAULT_CAUSES[ECONNREFUSED]` does not increment `_consecutive_connect_failures`. The existing refused-connect guard in the wedge test is kept. |
| B (A04) | `transport.py` | The `_IO_ERRORS` handler in `send_command` classifies the error outside the lock. It then sets `_last_failure_cause` under `_lock`, together with the state change. |
| C (A02) | `serial_transport.py` | `_IO_ERRORS = (serial.SerialException, OSError)`. `_discard_input` was already not catching OSError; its docstring now says so. |
| D (A05) | `obd.py` | A 0100 reply without `4100` calls `_report_no_vehicle` and returns False. Nothing is raised. That method logs a WARNING without `exc_info` on the first occurrence, then at most once per `_NO_VEHICLE_LOG_INTERVAL_S` (60 s, `time.monotonic`). The state is held on the instance and only the protocol thread touches it. A successful initialisation that follows a missing reply logs one INFO record and resets the state. Other initialisation failures still log at ERROR with `exc_info`. |
| D (B06) | `obd.py` | `stop(timeout: float = 5.0)` calls `_signal_stop()` and then joins for `timeout` seconds; 0 means it signals only. `_signal_stop()` sets `_adapter_initialised` to False and sets `shutdown_event`, without joining. It is the registered stop function. |
| E (A06) | `pairing.py` | The class constants are `DISCOVERY_CHUNK_S = 4` and `CHUNK_WAIT_MARGIN_S = 1`. `scan_duration` is computed once and passed to the back end, and `chunk_wait = scan_duration * 2 + 5 + 1` is derived from it. |
| E (A07) | `system_bluetooth.py` | `discover_devices` logs hcitool's return code and the first stderr line at WARNING when the code is not 0. The module-level `discover_devices` reuses one manager from `_get_manager()`. The manager is created lazily, and its construction (a subprocess) runs outside `_manager_lock`. |
| F | `pairing.py` | With `show_all_devices=False`, named UNKNOWN devices go into `fallback` in the classifying loop. They are deduplicated by MAC through `BluetoothDevice.__eq__`, as the main list is. After the last chunk, the method checks three conditions: the scan was not cancelled, `devices` is empty and `fallback` is not empty. When all three hold, it logs one INFO record, calls `device_found_callback` for each fallback device and returns that list. Device construction was moved into `_make_device` so that both lists use it. The signature is unchanged. |
| G (X01) | `pairing.py` | `pair_device` tests `_cancel_pairing` before `sock.connect` and again after it returns. When the flag is set, it returns False without a further status call; the existing `finally` closes the socket. After a cancel, `discover_elm327_devices` ignores the current chunk's results and returns without the fallback or the final progress call. |
| H (A09) | `device_store.py` | `_save_device_locked` and `_remove_device_locked` take a `copy.deepcopy` of `self.config`, change `self.config`, and restore the copy if `_save_config()` returns False or an exception occurs. `_save_config`'s signature is unchanged. `remove_device` returns False when the device is absent or the save fails. The docstrings state this return contract. |
| I (A10) | `device_store.py` | `set_device_store_path(path)` sets `_shared_path` under `_shared_lock` and discards `_shared`; it constructs nothing. `get_device_store()` calls `DeviceStore()` when the path is None and `DeviceStore(path)` otherwise, so tests that patch the class with a no-argument callable still work. |
| J (A11) | `sim_transport.py` | `connect()` no longer clears `_shutdown`. The two stale comments now give the 60 s period and the start at the midpoint (3650 RPM). |
| J (A12) | `transport.py` | The discard site in `send_command` records the known limit: a reply that arrives after the discard is read as the current command's reply, and the caller's PID check rejects a reply for another PID. |
| J (last_connected) | `models.py` | The str conversion and its `type: ignore` / TODO markers were removed from `__post_init__`. `from_dict` already parsed the string and remains the conversion point; it now has a Google-style docstring. |
| J (F03) | `tests/test_sim_transport.py` | The wall-clock step test samples at t = 15 s and asserts `'41 0C 65 90'` (6500 RPM). |

[Return to Table of Contents](<#table of contents>)

---

## 3. Comment Rule

History-narrating comments were reduced to the current behaviour plus at most one reference in these files:

- `transport.py`: the module constants, `_bluetooth_adapter_present`, the `OBDTransport` docstring, `__init__`, `_acquire_handle`, `drop_link`, `send_command`, `reconnect_indefinitely` and `select_transport`.
- `obd.py`: the queue-full handler.
- `serial_transport.py`: the class docstring.
- `device_store.py`: `_normalise_config`, `_save_device_locked` and the shared-instance comment.
- `sim_transport.py`: `drop_link`.

`pairing.py`, `system_bluetooth.py` and `models.py` had no such comments beyond those replaced by the edits.

[Return to Table of Contents](<#table of contents>)

---

## 4. Tests

The new module `tests/test_comm_layer_defects.py` has 30 tests. It covers every scenario in the change's `testing_requirements` and the prompt's edge cases.

| Class | Covers |
|---|---|
| `TestConnectAfterDisconnect` | A01: disconnect during a blocking `_open`; disconnect before connect; normal connect keeps the handle. |
| `TestFailureCauses` | A03: six refusals and then a timeout give "connection timed out", not the wedge cause. A control case shows that six timeouts still give the wedge cause. A04: a `ConnectionResetError` on write gives DISCONNECTED and a non-empty cause. |
| `TestSerialOSError` | A02: OSError is in `_IO_ERRORS`. An `in_waiting` that raises EIO drops the link and closes the port, with no "Unexpected error" record. |
| `TestNoVehicleLogging` | A05: three NO DATA replies and then a valid reply give one WARNING without `exc_info`, no ERROR and one INFO. A second WARNING appears only after 60 s on a patched monotonic clock. |
| `TestNonJoiningStop` | B06: with a real ThreadManager, `stop_thread('obd_protocol', timeout=0.5)` returns in under 1.5 s while the loop ignores the event for 2 s. A direct `stop()` joins; `stop(timeout=0)` signals only. |
| `TestChunkWait` | A06: a scan that takes `chunk_duration + 6` s is simulated by a future that times out when the wait is shorter than that. Its devices are used and one scan is submitted. |
| `TestHcitoolDiagnostics` | A07: return code 1 gives an empty list and a WARNING naming the code and the first stderr line. Two module-level calls construct one manager. |
| `TestDiscoveryFallback` | 'Phone' and 'Speaker' (one duplicated, plus one unnamed device) give two UNKNOWN devices, two callbacks and one INFO record. 'OBDII' and 'Phone' give only OBDII. An empty scan gives an empty list. A cancel gives no devices, no callback and no final progress call. |
| `TestPairingCancellation` | X01: a cancel during the initial status callback means no connect, the socket closed and no further status call. A cancel during connect means no communication test, the socket closed and no further status call. |
| `TestStoreResults` | A09: a failed save or remove returns False and leaves memory unchanged; removing an absent device returns False; a successful remove returns True. |
| `TestStorePath` | A10: the shared instance is replaced, the temporary file is written, the default file is unchanged, and `None` restores the default path. |
| `TestSimTransportShutdown` | A11: after `disconnect()` and `connect()`, `_shutdown` stays set. |
| `TestLastConnected` | `from_dict` with an ISO string, with the key absent and with an invalid string gives a datetime, None and None. |

Regression scope: the full `tests/` suite passed, 619 tests. That includes `test_sim_transport.py`, `test_lifecycle_sim.py`, `test_medium_defects.py` and the transport, pairing and device-store tests. The new module was run three more times in isolation and passed each time.

Against the unmodified `src/`, the new module fails at collection because `set_device_store_path` does not exist. The individual tests were therefore not run against the old code.

[Return to Table of Contents](<#table of contents>)

---

## 5. Success Criteria

| Criterion | Result |
|---|---|
| `connect()` never leaves an open handle when `_shutdown` is set | Met (EDIT A; `TestConnectAfterDisconnect`). |
| OSError in `SerialTransport._IO_ERRORS` | Met. |
| A missing 4100 reply produces no ERROR record and no traceback | Met. |
| `stop_thread('obd_protocol', timeout=t)` is bounded by t | Met. |
| UNKNOWN devices are returned only when no ELM327-like device was found and the scan was not cancelled | Met. |
| `pair_device` honours `_cancel_pairing` | Met. |
| `save_device` and `remove_device` return False, with memory unchanged, when the save fails | Met. |
| `set_device_store_path` exists and `get_device_store()` honours it | Met. |
| No `type: ignore` at `BluetoothDevice.last_connected` | Met. |
| `git diff` touches only `src/gtach/comm` and `tests/` | Met for source; the T-Doc move and this report are under `ai/workspace/`. |
| pytest passes; mypy reports no issues | Met. |

[Return to Table of Contents](<#table of contents>)

---

## 6. Deviations and Notes for the Planner

1. **EDIT G, test expectation.** `pair_device` still clears `_cancel_pairing` on entry and calls `status_callback(CONNECTING, "Connecting to device...")` before the first check. The change states that a cancelled pairing returns "without calling status_callback". This was read as "no status call after the cancel". The X01 tests therefore assert exactly one call, the initial CONNECTING. Keeping the entry `clear()` means a cancel made before `pair_device` is called has no effect. Run 4 should call `cancel_pairing()` while pairing is in progress. Removing the `clear()` would make a stale cancel abort every later pairing.
2. **EDIT G, discovery.** After a cancel, the results of the chunk in flight are discarded and not processed. This is needed so that no `device_found_callback` follows the cancel.
3. **EDIT A.** `_open()` still runs when `_shutdown` is already set, because the prompt places the test after `_open()`. The edge case "disconnect() before connect()" holds: False is returned and the handle is closed.
4. **EDIT D.** The INFO record on recovery is logged only when a missing-4100 reply preceded the success. The first success in a session logs nothing new.
5. **EDIT E.** Only the module-level `discover_devices` reuses the shared manager, as specified. `lookup_name` still constructs a manager per call. It has no caller in `src/`, so it was left unchanged.
6. **Out of scope, for run 3.** The comment at `app.py` `_re_enter_setup` still says the obd_protocol stop function is `OBDProtocol.stop`; it is now `_signal_stop`. Behaviour is as the comment intends: the call sets `shutdown_event`, and the bound is now `stop_thread`'s timeout.
7. **Out of scope, for run 3.** `reset_device_store()` does not reset the path set by `set_device_store_path`. A test that sets a path must restore it with `set_device_store_path(None)`, as `TestStorePath` does.
8. **Design updates pending (planner).** design-a6b7c8d9 needs the return contract and `set_device_store_path`. design-b1c2d3e4 needs the shutdown test in `connect()`, the refused-connect counter rule and the send-time cause.
9. **Device session A** (human) remains to be done: the A01 procedure, link loss and reconnect, and the EBUSY re-test. The A02 unplug test also remains if hardware is available.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-11 | Implementation report for prompt-b4f9607a. |

---

Copyright (c) 2026 William Watson. MIT License.
