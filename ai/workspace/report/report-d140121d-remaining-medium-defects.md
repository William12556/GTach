Created: 2026 October 07

# Report: Bounded Pairing, Coordinated Setup State, Complete Shutdown

---

## Table of Contents

1. [Summary](<#1. summary>)
2. [Files Changed](<#2. files changed>)
3. [Tests Added and Result](<#3. tests added and result>)
4. [Success Criteria](<#4. success criteria>)
5. [Deviations](<#5. deviations>)
6. [On-Device Verification Outstanding](<#6. on-device verification outstanding>)
7. [Version History](<#version history>)

---

## 1. Summary

prompt-d140121d (change-d140121d, issue-d140121d; audit-36b6ea95 A07, A08, A17, C14, D04, D05, X02) was implemented in commit `69eb605f2b086d666248bb39a4046032f9eb94d8`.

- **EDIT A:** `BluetoothSocket.connect` applies a timeout set earlier before connecting.
- **EDIT B:**
  - `BluetoothPairing.shutdown` sets both cancel events, then calls `shutdown(wait=False, cancel_futures=True)`;
  - the discovery chunk duration uses the effective timeout.
- **EDIT C:**
  - `get_state()` returns a copy, including a new `discovered_devices` list;
  - `add_discovered_device()` de-duplicates by MAC and notifies after releasing the lock.
- **EDIT D:**
  - all 26 state writes in interface.py go through `_set_state()`, and discovered devices through `_add_device()`. Both write through the coordinator, or to the passed object when there is no coordinator;
  - `_active_operations` is guarded by `_ops_lock`, with async_manager calls made after release;
  - new `has_active_operation()`, used by setup.py;
  - new `shutdown()`.
- **EDIT E:**
  - `_arm_exit_backstop()` is idempotent and called first in `shutdown()` and in `_watchdog_shutdown()`;
  - `shutdown()` calls `shutdown_async_manager()` after `stop_setup`;
  - `stop_setup` calls `bluetooth_interface.shutdown()`;
  - `DisplayManager.stop` stops the touch handler.

[Return to Table of Contents](<#table of contents>)

---

## 2. Files Changed

| File | Change |
|---|---|
| `src/gtach/comm/system_bluetooth.py` | EDIT A. |
| `src/gtach/comm/pairing.py` | EDIT B. |
| `src/gtach/display/setup_components/state/coordinator.py` | EDIT C. |
| `src/gtach/display/setup_components/bluetooth/interface.py` | EDIT D. |
| `src/gtach/display/setup.py` | EDIT D(2) caller; EDIT E(3). |
| `src/gtach/app.py` | EDIT E(1), E(2). |
| `src/gtach/display/manager.py` | EDIT E(4). |
| `tests/test_medium_defects.py` | New: 10 tests. |
| `tests/test_callbacks_outside_locks.py`, `tests/test_setup_and_gauge.py` | Test hosts gain `_ops_lock` and a `shutdown` stub (see Deviations). |

[Return to Table of Contents](<#table of contents>)

---

## 3. Tests Added and Result

`tests/test_medium_defects.py` has 10 tests, covering every change test case and the edge case:

- **Socket:** the timeout is set before connect.
- **Pairing shutdown:** `wait=False`, `cancel_futures=True`; both events set.
- **Coordinator:**
  - `get_state` copies are independent;
  - `add_discovered_device` gives True then False, with one entry and one notification.
- **Interface:**
  - with a coordinator, handler writes land in the coordinator and the passed copy is untouched;
  - without one, the writes land on the passed state.
- **Concurrency:** readers and a writer on `_active_operations`, 1,000 iterations, no exception.
- **app.shutdown:** order backstop → watchdog → setup → async → display → transport → obd → thread manager.
- **Backstop:** armed once across `_watchdog_shutdown` and two `shutdown` calls.
- **DisplayManager.stop:** `touch_handler.stop` called once.

pytest after this commit: 436 passed (426 before the commit).

[Return to Table of Contents](<#table of contents>)

---

## 4. Success Criteria

| Criterion | How checked | Result |
|---|---|---|
| BluetoothSocket.connect applies self.timeout before connect | `TestBluetoothSocketTimeout` | Pass |
| BluetoothPairing.shutdown uses wait=False and cancel_futures=True | `TestPairingShutdown` | Pass |
| get_state returns a copy; add_discovered_device exists | `TestCoordinatorOwnsState` | Pass |
| interface.py has no `state.<attr> =` and no `.discovered_devices.append` outside the helpers | `grep`: the only `discovered_devices.append` is inside `_add_device`'s fallback | Pass |
| `_active_operations` accessed only under `_ops_lock`; setup.py uses has_active_operation | Code review; `grep` shows no other reader | Pass |
| app.shutdown arms the backstop first and calls shutdown_async_manager; DisplayManager.stop stops the touch handler | `TestShutdown`, `TestDisplayManagerStop` | Pass |
| `pytest tests/` passes | Full run | 436 passed |

[Return to Table of Contents](<#table of contents>)

---

## 5. Deviations

- **Test helpers adjusted:** two existing test helpers needed the new attributes. `tests/test_callbacks_outside_locks.py` (`_ops_lock`) and `tests/test_setup_and_gauge.py` (a `shutdown` stub) build their hosts without `__init__`. No assertion changed.
- **Missing flag:** `_arm_exit_backstop` reads the flag with `getattr`, so an instance built without `__init__` does not raise.
- **Backstop on normal exit:** the backstop is now also armed on a normal (atexit) shutdown. It is a daemon timer, so a normal exit is not delayed.

[Return to Table of Contents](<#table of contents>)

---

## 6. On-Device Verification Outstanding

On the Pi: a full pairing works, and `time systemctl stop gtach` during discovery stays well under 30 s.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-07 | Initial implementation report for prompt-d140121d. |

---

Copyright (c) 2026 William Watson. MIT License.
