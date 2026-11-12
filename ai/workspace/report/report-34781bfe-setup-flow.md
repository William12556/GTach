Created: 2026 November 12

# Report: Setup Flow — One Operation Rule, Presented Outcomes

---

## Table of Contents

1. [Summary](<#1. summary>)
2. [Preconditions](<#2. preconditions>)
3. [Changes by Edit](<#3. changes by edit>)
4. [Where the Scan Is Started](<#4. where the scan is started>)
5. [Registration Race](<#5. registration race>)
6. [Comment Rule](<#6. comment rule>)
7. [Tests](<#7. tests>)
8. [Success Criteria](<#8. success criteria>)
9. [Deviations and Notes for the Planner](<#9. deviations and notes for the planner>)
10. [Version History](<#version history>)

---

## 1. Summary

prompt-34781bfe (change-34781bfe, issue-34781bfe; run 4 of proposal-71ab3751) was implemented in one commit on branch `claude/vibrant-fermat-cvqit4`. EDITS A to G and the COMMENT RULE were applied. The issue and change T-Docs remain active pending test results. The prompt T-Doc was closed and moved to `ai/workspace/prompt/closed/`.

- pytest `tests/`: 694 passed (654 before; 40 in the new `tests/test_setup_flow.py`).
- mypy `src/`: no issues.
- black and isort report nothing in `src/` or the touched tests. flake8 reports nothing in the touched source files or in `tests/test_setup_flow.py`. Its two findings in `tests/test_medium_defects.py` (F401 unused `pytest`, E731 lambda) and the isort finding in `tests/test_sim_transport.py` exist on the base commit, in lines this change does not touch.
- `git diff` touches `display/setup.py`, `display/setup_components/bluetooth/interface.py`, `display/setup_components/state/coordinator.py`, `display/async_operations.py`, `display/setup_models.py`, one call in `app.py`, `tests/`, and the T-Docs under `ai/workspace/`.
- Python 3.9 was not available on this host (3.13). The code uses no syntax or library call newer than 3.9.

[Return to Table of Contents](<#table of contents>)

---

## 2. Preconditions

Both preconditions were checked before any edit:

- design-a3b4c5d6 is at version 2.1 with status `approved` (2026-11-12, including the D1 same-scan fallback).
- The comm interfaces of change-b4f9607a are present: `BluetoothPairing.discover_elm327_devices` returns the all-UNKNOWN fallback list from the same scan, `pair_device` checks `_cancel_pairing` on both sides of the blocking connect, and `DeviceStore.save_device` returns `bool`.

[Return to Table of Contents](<#table of contents>)

---

## 3. Changes by Edit

| Edit | File | Change |
|---|---|---|
| A(1) | `interface.py` | Module constants `BLUETOOTH_INIT`, `DEVICE_DISCOVERY`, `DEVICE_PAIRING`, `DEVICE_PROBE`. `_active_operations` maps each name to the registration id of the wanted operation; `_submitted_ids` maps the name to the async manager's id. Both are guarded by `_ops_lock`. New `_is_current(name, operation_id) -> bool` reads under the lock. New helpers: `_register` (cancels what the name holds, then registers a new id), `_submit` (submits and records the async id), `_release` (removes the registration only if the caller's id holds it). |
| A(2) | `interface.py` | `on_discovery_complete`, `on_pairing_complete` and `on_probe_complete` return at DEBUG ("Ignoring completion of …") when their id is not current, and remove their own registration in `finally` after acting. The discovery task's progress and device-found callbacks, the pairing `status_callback`, and the discovery task's own writes after the settle delay all check `_is_current` first. `_finish_pairing` checks again after the blocking `save_device` and `verify_obd_connection`, so Back during verification also leaves the state alone. |
| A(3) | `interface.py` | New `cancel_operation(name)`: removes the registration and async id under the lock; then, outside it, calls `async_manager.cancel_operation(id)` and `pairing.cancel_discovery()` or `pairing.cancel_pairing()` by name. It does nothing when no operation is registered under the name. `cancel_operations()` calls it for every registered name. |
| A(4) | `setup.py` | The `cancel` action calls `cancel_operation(DEVICE_DISCOVERY)` before `SetupAction.CANCEL`. The `back` action calls `cancel_operation(DEVICE_PAIRING)` before `SetupAction.BACK` when the screen is PAIRING. `stop_setup` is unchanged: `interface.shutdown()` → `cancel_operations()` → `cancel_operation`. |
| A(5) | `coordinator.py` | `START_DISCOVERY` and `CANCEL` call `reset_discovery()` before `transition_to_screen`, as `RETRY` already did. |
| B(1) | `setup.py` | The `start` action calls `start_discovery` after `START_DISCOVERY`. The `retry` action reads the screen first: from DEVICE_LIST it calls `start_discovery`; from PAIRING, `start_pairing`. `_setup_loop` keeps the heartbeat, the animation tick and the COMPLETE hold; its DISCOVERY branch (start a scan, advance to DEVICE_LIST) is removed. See section 4. |
| B(2) | `interface.py` | New `_present_scan_result`: COMPLETED with devices → DEVICE_LIST with those devices and no error line; COMPLETED with none → DEVICE_LIST, empty list, no error line; FAILED → DEVICE_LIST, empty list, error line `Scan failed`. A non-empty list in which every `device_classification is DeviceType.UNKNOWN` gets the error line `No ELM327 found - showing all devices`. State is written in one `update_state` call (`discovered_devices`, `error_message`, `pairing_status=IDLE`) before the transition. |
| B(3) | `setup.py` | `_render_device_list_screen` already drew "No devices found", the error line and Back and Retry for an empty list; it is now reachable. Only its comment changed. |
| B(4) | `coordinator.py` | `transition_to_screen(DEVICE_LIST)` sets `pairing_status = IDLE`, on every entry. |
| C | `setup.py` | `_render_current_device_screen` neither draws nor registers New Setup while `_probe_in_flight`. `current_continue` invalidates the CURRENT_DEVICE cache after setting the flag, so the next frame is redrawn without it. `new_setup` calls `cancel_operation(DEVICE_PROBE)` and clears `_probe_in_flight` before it removes the stored device. `start_device_probe` registers under `DEVICE_PROBE`; a cancelled probe's result is not delivered. |
| D | `setup.py`, `coordinator.py`, `setup_models.py` | The PAIRING screen draws no Continue button and registers no region on SUCCESS. The `continue` touch action, `SetupAction.NEXT`, its branch in `handle_setup_action` and `_handle_next_navigation` are removed (no reference remained). New `_draw_spinner(surface, center)` draws both spinners; each dot is `background + (primary - background) * factor` per channel, `factor` from 1.0 to 0.2 in seven equal steps. Only RGB colours reach `pygame.draw.circle`. |
| E | `async_operations.py`, `interface.py`, `setup.py` | `submit_operation` evaluates `"progress_callback" in inspect.signature(task_func).parameters` and stores the result in the work item. The worker passes the reporter by keyword only then; the `co_varnames` inspection is gone. After the completion callback has run, the worker removes the operation and its callback from both maps; a cancelled PENDING operation is removed when the worker dequeues it. `cleanup_completed_operations` had no caller and was deleted. `cancel_operation` is unchanged in behaviour. `discovery_task` and `pairing_task` take `progress_callback`. `render()` draws the uncached screens (DISCOVERY, DEVICE_LIST, PAIRING) straight onto the target; the cached screens (WELCOME, COMPLETE, CURRENT_DEVICE) render into a copy that is stored without a second copy. |
| F | `interface.py`, `setup.py` | `_finish_pairing` uses `save_device()`'s result: on False it sets FAILED with error line `Device not saved` and neither verifies nor completes. `verify_obd_connection` sets `_adapter_reset` (under `_ops_lock`) when it sent ATZ and the reply was non-empty; the simulation pass-through returns before that. The interface exposes it as the read-only property `adapter_reset`, and `SetupDisplayManager.adapter_reset_in_session` returns it. The interface is created per manager, so the flag covers that manager's lifetime. The stored-device probe and Cancel never set it. |
| G | `setup.py`, `app.py` | `__init__` takes `Optional["pygame.Surface"]`. `render()` returns before drawing when neither `target_surface` nor `self.surface` is available. The selection uses `is not None`, not `or`. In `app.py` the `type: ignore[arg-type]`, the two `TODO: issue-ac11505d` comments and the `noqa: E501` at the construction were removed; mypy accepts the call. |

[Return to Table of Contents](<#table of contents>)

---

## 4. Where the Scan Is Started

A scan is started in exactly two places, both in `SetupDisplayManager._handle_touch_action`, each immediately after the coordinator action that enters DISCOVERY:

- `start` (WELCOME → DISCOVERY): after `handle_setup_action(START_DISCOVERY)`.
- `retry` on DEVICE_LIST (DEVICE_LIST → DISCOVERY): after `handle_setup_action(RETRY)`.

No other path enters DISCOVERY now that `_handle_next_navigation` has been removed. `_setup_loop` contains no call to `start_discovery` and no transition to DEVICE_LIST. `on_discovery_complete` moves to DEVICE_LIST for every outcome, so the loop's old rescan condition (DISCOVERY + IDLE + no devices) cannot recur.

[Return to Table of Contents](<#table of contents>)

---

## 5. Registration Race

`AsyncOperationManager.submit_operation` does not accept a caller-supplied id. A worker can therefore run the task and invoke the completion callback before `submit_operation` returns. `_SyncAsyncManager` in `tests/test_callbacks_outside_locks.py` relies on exactly that ordering.

Chosen approach: the interface issues its own registration id and keeps the async id separately.

1. `_register(name)` cancels the operation the name holds, then stores a new id `"<name>-<8 hex>"` (from `uuid4`) in `_active_operations[name]` under `_ops_lock`. This happens before the task is submitted.
2. The completion callback and the task's callbacks capture this registration id in their closure, so `_is_current(name, id)` is true from the moment of submission.
3. After `submit_operation` returns, `_submit` records the async id in `_submitted_ids[name]` under `_ops_lock`, but only if the registration is still the caller's. When the completion has already run and released it, nothing is recorded.
4. `cancel_operation` uses `_submitted_ids` to call `async_manager.cancel_operation`. If a cancel falls between steps 1 and 3, the async id is not yet known and the async manager is not asked to cancel. The registration is removed all the same, so the operation's completion is ignored, and the back-end cancel is still sent.

The `element_registry` signature `_is_current(self, name: str, operation_id: str) -> bool` is kept. Its `operation_id` is the registration id, not the async manager's id. This departs from the prompt's wording "capture the operation id returned by submit_operation in the closure" because that id is not known in time; see section 9, item 1.

Tested by `TestCancelDiscovery::test_completion_before_registration_is_stored`: with a manager that runs the task inside `submit_operation`, Start Setup reaches DEVICE_LIST with the devices and leaves no registration or async id behind.

[Return to Table of Contents](<#table of contents>)

---

## 6. Comment Rule

In the files edited, comments that narrate history were reduced to the current behaviour with at most one reference:

- `setup.py`: `_WELCOME_MESSAGE_Y` (the former y=440 position removed); `_COMPLETE_HOLD_S` (the observation narrative reduced to its purpose, issue-d26ca557); the arrow constants (one reference, change-d38362aa); `colors` ("deliberately unchanged" and "was unreadable" removed); the DEVICE_LIST error-line comment ("moved up" removed); `_draw_focus_arrows` docstring ("rather than at a fixed count threshold" removed); "Handle auto-discovery if needed" replaced by the loop's current role.
- `coordinator.py`: `focused_index` ("replaces the former scroll_offset/max_scroll pair" removed).
- `interface.py`: the init callback's "(audit-36b6ea95 D12)" removed; the new completion handlers state the same rule without it.
- `async_operations.py`: the double reference "(CLAUDE.md §4 rule 8, issue-fbe7e98a)" reduced to one.

`app.py` was edited only at the construction call (EDIT G); no other comment there was changed.

[Return to Table of Contents](<#table of contents>)

---

## 7. Tests

New module `tests/test_setup_flow.py` (40 tests). It uses a real `SetupDisplayManager` and `SetupStateCoordinator` on a stub async manager that records submissions and cancels but runs nothing, a stub pairing back end that counts `cancel_discovery` and `cancel_pairing`, and a stub device store. pygame runs without a display. Coverage of the change's `test_cases`:

| Scenario (change-34781bfe) | Test |
|---|---|
| Two ELM327 devices → DEVICE_LIST, no error line | `TestScanOutcomes::test_two_elm327_devices` |
| No device → DEVICE_LIST, "No devices found" drawn, Back and Retry only, no second scan in 2 s of loop cycles | `TestScanOutcomes::test_no_device_reaches_device_list_and_is_not_rescanned` (setup thread running) |
| Failed → `Scan failed`, no second scan | `TestScanOutcomes::test_failed_scan` |
| Only UNKNOWN → listed with `No ELM327 found - showing all devices` | `TestScanOutcomes::test_fallback_devices_are_listed_with_notice`; mixed list has no notice |
| Each entry into DISCOVERY submits exactly one scan | `TestOneScanPerEntry` (Start Setup; Retry from DEVICE_LIST, which also checks that a stale selected device starts no pairing; the loop starts none) |
| Cancel on DISCOVERY, abandoned scan completes with devices / with error | `TestCancelDiscovery::test_abandoned_scan_changes_nothing[devices,error]` |
| Device-found callback from a cancelled scan | `TestCancelDiscovery::test_device_found_from_cancelled_scan_is_not_added` (plus the positive case) |
| Back on PAIRING, pairing then succeeds | `TestCancelPairing::test_back_then_successful_completion`; `test_status_callback_after_back_writes_nothing` |
| New Setup region while the probe runs | `TestProbeGuard::test_new_setup_absent_while_probe_runs` |
| Probe completes after a cancelled registration | `TestProbeGuard::test_probe_after_new_setup_changes_nothing` |
| PAIRING with SUCCESS has no `continue` region | `TestScreens::test_pairing_success_has_no_continue` |
| Spinner at eight phases, no per-pixel alpha, ≥ 3 colours | `TestScreens::test_spinner_fades_without_alpha` (also asserts every colour passed to `pygame.draw.circle` is RGB) |
| Declared `progress_callback` gets progress; undeclared is not passed | `TestAsyncOperationManager::test_declared_progress_callback_receives_progress`, `test_task_without_parameter_is_called_without_it` (the task has a local named `progress_callback`, which the old inspection matched) |
| Ten operations complete → maps empty | `TestAsyncOperationManager::test_finished_operations_are_not_retained` (five succeed, five raise); `test_cancelled_pending_operation_is_dropped` |
| Pairing succeeds, `save_device` False | `TestCancelPairing::test_save_failure` |
| `adapter_reset_in_session`: construction, real verification, simulation, probe → False, True, False, False | `TestAdapterResetInSession` |
| Surface None, `render()` without a target | `TestScreens::test_render_without_surface` |
| START_DISCOVERY and CANCEL with a stale list | `TestDeviceListResetBeforeTransition` (the list is read inside the screen-transition callback; `reset_discovery` sends no state-change notification, so the transition callback is where "before the new screen is announced" can be observed) |

The prompt's edge cases: Cancel tapped twice (`test_cancel_tapped_twice`), Retry on DEVICE_LIST while the previous scan's task still runs (`test_retry_while_previous_scan_still_runs`), `stop_setup` during a scan (`test_stop_setup_during_scan`), and a completion arriving before its registration was stored (`test_completion_before_registration_is_stored`). Also covered: a submit failure shows `Scan failed` or pairing FAILED (`TestSubmitFailure`), the uncached screen is drawn without a surface copy (`test_uncached_screen_draws_on_target`), and an ignored completion is logged at DEBUG with nothing at WARNING or above (`test_logger_is_quiet_for_ignored_completion`).

Mutation check: with the `_is_current` checks removed from `on_discovery_complete` and the device-found callback, six tests in the new module fail. The source was restored afterwards.

Existing tests changed:

- `tests/test_callbacks_outside_locks.py`, `tests/test_medium_defects.py`, `tests/test_obd_verify_busy_retry.py`: helpers that build the interface or manager with `object.__new__` now set `_submitted_ids`, `_adapter_reset` and `_ops_lock`, or the render-cache attributes `current_continue` now uses.
- `tests/test_medium_defects.py::test_fallback_without_coordinator`: an empty scan now has no error line (EDIT B(2)), so the assertion `startswith("No devices found.")` became `is None`.

The full regression scope (`test_medium_defects`, `test_device_list_focus`, `test_setup_and_gauge`, `test_setup_lock_order`, `test_callbacks_outside_locks`, `test_lifecycle_sim`) passes within the 694.

[Return to Table of Contents](<#table of contents>)

---

## 8. Success Criteria

| Criterion | Status |
|---|---|
| Every completion and in-task callback in `interface.py` checks `_is_current` before it writes state or changes screen | Met. The init completion is the exception by design: it records the pairing back end and touches no setup state. |
| Cancel on DISCOVERY and Back on PAIRING call `cancel_operation`; an abandoned completion changes nothing | Met |
| `_setup_loop` has no `start_discovery` and no transition to DEVICE_LIST | Met |
| Empty, failed and fallback scans reach DEVICE_LIST with the stated texts; no automatic rescan | Met |
| New Setup region absent while a probe is in flight | Met (see section 9, item 9) |
| PAIRING screen has no Continue button | Met |
| No RGBA colour passed to `pygame.draw.circle` in the spinners | Met |
| AsyncOperationManager holds no finished operation; no inspection of local-variable names | Met (see section 9, item 8) |
| `on_pairing_complete` uses `save_device`'s result | Met (in `_finish_pairing`) |
| `SetupDisplayManager.adapter_reset_in_session` exists with the stated meaning | Met |
| No `type: ignore` at the `SetupDisplayManager` construction in `app.py` | Met |
| `git diff` touches only the setup flow files, that call in `app.py`, and `tests/` | Met (plus the T-Docs) |
| pytest `tests/` passes; mypy `src/` reports no issues | Met: 694 passed; no issues |

[Return to Table of Contents](<#table of contents>)

---

## 9. Deviations and Notes for the Planner

1. **Registration id instead of the async id (EDIT A).** As section 5 states, the closures hold an id the interface issues before submitting, because `submit_operation` cannot be given an id. The async id is kept in `_submitted_ids` for cancellation and for `get_active_operation_progress`.
2. **Outer `progress_callback` parameters removed.** To stop the shadowing named in EDIT E, `start_discovery` lost its unused `progress_callback` parameter and `start_pairing` lost its unused one; no caller passed either. `device_found_callback` and `show_all_devices` remain.
3. **B(4) is applied on every entry to DEVICE_LIST.** It is implemented in `SetupStateCoordinator.transition_to_screen`, so it also covers Back from PAIRING and a failed OBD verification. The prompt's file list names the coordinator only for A(5) and D.
4. **Retry is decided by screen (B(1)).** The old `retry` action started pairing whenever a selected device existed. That included DEVICE_LIST, where `reset_discovery` leaves `selected_device` set. It now starts a scan on DEVICE_LIST and pairing only on PAIRING.
5. **`cancel_operation` with nothing registered does nothing.** That makes a second Cancel a no-op and satisfies "cancel_discovery called once". Consequence: `cancel_operations()` no longer calls `cancel_discovery()` and `cancel_pairing()` unconditionally. `shutdown()` still calls `pairing.shutdown()`, which sets both back-end cancel events.
6. **The discovery task checks `_is_current` after its 2 s settle delay** and returns an empty list if the scan was cancelled. Without this, a Cancel during the delay would be undone: `discover_elm327_devices` clears `_cancel_discovery` when it starts, so it would run a full scan of about 36 s.
7. **A submit failure is presented.** If `submit_operation` raises, discovery shows DEVICE_LIST with `Scan failed`, and pairing shows FAILED with "Unknown pairing error". Previously only `pairing_status` was set. Neither text is new.
8. **Async manager retention.** `stop()` still marks PENDING operations CANCELLED in place; they remain in the map until the manager is discarded, as `shutdown_async_manager` does. Finished and dequeued-cancelled operations are removed.
9. **New Setup is neither drawn nor registered while the probe runs.** The change asks only that the region not be registered; the design says "not offered". An undrawn button seemed clearer than a button that does nothing. A narrow race remains in the existing render cache: a frame begun before `current_continue` set the flag can be cached just after the invalidation. Until the probe ends that frame shows New Setup, and `new_setup` then cancels the probe as EDIT C requires. `_probe_in_flight` is still an unguarded bool, as before.
10. **simbt shows the fallback notice.** `SimBluetoothPairing`'s `_FAKE_DEVICES` do not set `device_classification`, so all four are UNKNOWN. By the rule of EDIT B(2), DEVICE_LIST in the simbt path therefore shows `No ELM327 found - showing all devices`. Fixing it means classifying the fake devices in `comm/sim_bluetooth.py`, which is outside this change's scope. Device session B will show it.
11. **`complete_setup()` sends no screen-transition notification.** This is existing behaviour, unchanged. The COMPLETE screen still renders because no cache entry exists for it.
12. **Design marks.** design-a3b4c5d6 v2.0 keeps its "(change)" marks until verification, per the change's traceability (planner).

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-12 | Initial report for prompt-34781bfe. |

---

Copyright (c) 2026 William Watson. MIT License.
