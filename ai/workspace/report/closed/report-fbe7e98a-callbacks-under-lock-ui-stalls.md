Created: 2026 October 07

# Report: Callbacks Outside Locks and Asynchronous Continue Probe

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

prompt-fbe7e98a (change-fbe7e98a, issue-fbe7e98a; audit-36b6ea95 D03, D06, C04, C02 and D12) was implemented in commit `523bb218bead9e868b624d8facca4b233489ce4d`.

- **EDIT A:** `AsyncOperationManager` captures the operation and its callback under `_operations_lock` and invokes the callback after release. This applies in both `_worker_loop` and `_update_operation_progress`.
- **EDIT B:** `on_bluetooth_init_complete`, `on_discovery_complete` and `on_pairing_complete` return at once on PENDING or RUNNING (D12).
- **EDIT C:** `TouchEventCoordinator._handle_button_touch_down` returns `(action, callback)` without invoking the callback. `handle_touch_down` invokes it after leaving the lock.
- **EDIT D:** `TouchInterface._emit_touch_event` reads the callback under the lock and invokes it after release.
- **EDIT E:** the new `BluetoothSetupInterface.start_device_probe(on_result)` runs the RFCOMM reachability check on an async worker. The `'current_continue'` action submits one probe (guarded by `_probe_in_flight`) and returns None. The result handler completes setup, or returns to WELCOME with "Device not available".

[Return to Table of Contents](<#table of contents>)

---

## 2. Files Changed

| File | Change |
|---|---|
| `src/gtach/display/async_operations.py` | EDIT A. |
| `src/gtach/display/setup_components/bluetooth/interface.py` | EDIT B (three guards); EDIT E (`start_device_probe`). |
| `src/gtach/display/input/touch_coordinator.py` | EDIT C. |
| `src/gtach/display/touch_interface.py` | EDIT D. |
| `src/gtach/display/setup.py` | EDIT E caller: `_probe_in_flight` in `__init__`; `'current_continue'` branch replaced; its DeviceStore and RFCOMMTransport imports removed. |
| `tests/test_callbacks_outside_locks.py` | New: 12 tests. |

[Return to Table of Contents](<#table of contents>)

---

## 3. Tests Added and Result

`tests/test_callbacks_outside_locks.py` has 12 tests, covering every prompt scenario and the edge case:

- **Async manager:**
  - progress and completion callbacks both run with `_operations_lock` free;
  - a callback that calls `get_operation_status` completes within 5 s.
- **Completion handlers (parametrised over the three):** a RUNNING update leaves `pairing_status`, `pairing`, `_pairing_ready` and `_active_operations` unchanged.
- **Button callbacks:**
  - a helper thread acquires the coordinator lock from inside the callback, and the action type is returned;
  - a callback that registers a region does not deadlock (the edge case).
- **Touch interface:** the `MockTouchInterface` callback runs with `_lock` free.
- **`start_device_probe`:**
  - simulation (`pairing_factory` set) → True, and RFCOMMTransport is never constructed;
  - an unreachable device → False;
  - a RUNNING update is not reported (additional).
- **`'current_continue'` twice:** one probe; both calls return None.

Against the pre-change sources the module does not complete: the `get_operation_status` test self-deadlocks on the non-reentrant lock and the run was ended by its timeout.

pytest after this commit: 321 passed (309 before the commit).

[Return to Table of Contents](<#table of contents>)

---

## 4. Success Criteria

| Criterion | How checked | Result |
|---|---|---|
| No `progress_callbacks[...](...)` call inside `with self._operations_lock:` | AST walk of every `_operations_lock` with-block in `async_operations.py` | Pass |
| Each completion handler returns early on PENDING or RUNNING | Code review; parametrised test | Pass |
| `_handle_button_touch_down` invokes no callback; `handle_touch_down` invokes the deferred callback after its with-block | AST: the calls in `_handle_button_touch_down` are logging, `metadata.get` and `callable` only; code review of `handle_touch_down` | Pass |
| `_emit_touch_event` invokes the callback after its with-block | AST: its with-block makes no call | Pass |
| `'current_continue'` contains no RFCOMMTransport reference | `grep -n RFCOMMTransport src/gtach/display/setup.py` returns nothing | Pass |
| `start_device_probe` exists with the specified signature | Code review: `(self, on_result: Callable[[bool], None]) -> None` | Pass |
| `pytest tests/` passes | Full run | 321 passed |

[Return to Table of Contents](<#table of contents>)

---

## 5. Deviations

- The "not reachable" warning no longer names the MAC address. setup.py no longer reads the device, and the probe reports only a boolean. The prompt allows omitting the MAC when there is no device; it is now omitted in every case.
- In `handle_touch_down`, the touch statistics are still updated only when no slider or button branch handled the touch. This preserves the behaviour of the former early returns.
- One test was added beyond the prompt's scenarios: a RUNNING update to the probe handler is not reported.

[Return to Table of Contents](<#table of contents>)

---

## 6. On-Device Verification Outstanding

DISCONNECTED → Setup, then a full pairing, then CURRENT_DEVICE → Continue with the adapter powered off. The display must stay responsive throughout.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-07 | Initial implementation report for prompt-fbe7e98a. |

---

Copyright (c) 2026 William Watson. MIT License.
