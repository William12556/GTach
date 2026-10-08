Created: 2026 October 07

# Report: Low-Severity Corrections

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

prompt-4005360c (change-4005360c, issue-4005360c; audit-36b6ea95 A12, A13, A16, A18, B07, B09, B10, B12, C10, C13, C15, C16, D08, D11) was implemented in commit `2ade5a3769ce5396447b6526328a9b153af90182`.

- **A12:** `TCPTransport._open` closes the socket when connect fails and re-raises.
- **A13:** SimBluetoothPairing clears its cancel event at the start of each discovery and each pairing.
- **A16:** `ConnectionError`/`TimeoutError` in transport.py are renamed `TransportConnectionError`/`TransportTimeoutError`; nothing else referenced them.
- **A18:** bluetoothctl children are reaped after kill or terminate; the reader's dict is locked and a copy is returned.
- **B07:** watchdog's bare `except:` is now `except Exception:`.
- **B09:** `OBDTransport.retry_delay` property; app.py passes it to `reconnect_indefinitely` at both thread creations.
- **B10:** `Optional` annotations in main.py and app.py; `run() -> None`.
- **B12:** `_obd_lock` guards the `_obd_started` check-and-set and its reset.
- **C10:** an out-of-range `fps_limit` or `touch_long_press` falls back to its default with a warning.
- **C13:** splash `_font_render_times` is a `deque(maxlen=100)`; the progress log is rate-limited to 0.5 s at DEBUG; a zero duration counts as complete.
- **C15:** `FontManager.get_bold_font()` gives the RPM font its own cached bold object; the touch-event log is at DEBUG.
- **C16:** monotonic time for durations (listed in Deviations).
- **D08:** device surfaces read `signal_strength`.
- **D11:** engine `cleanup()` resets `fb` and `fb_dev` to None.
- **Rule 8:** CLAUDE.md file-lock clarification; Version History 1.6.

[Return to Table of Contents](<#table of contents>)

---

## 2. Files Changed

| File | Change |
|---|---|
| `src/gtach/comm/tcp_transport.py` | A12. |
| `src/gtach/comm/sim_bluetooth.py` | A13. |
| `src/gtach/comm/transport.py` | A16, B09. |
| `src/gtach/comm/system_bluetooth.py` | A18. |
| `src/gtach/core/watchdog.py` | B07. |
| `src/gtach/app.py` | B09 (and the two retry-arc comments), B10, B12. |
| `src/gtach/main.py` | B10. |
| `src/gtach/utils/config.py` | C10. |
| `src/gtach/display/splash.py` | C13, C16. |
| `src/gtach/display/typography.py`, `src/gtach/display/manager.py` | C15. |
| `src/gtach/display/touch.py`, `touch_interface.py`, `input/touch_coordinator.py`, `setup_components/state/coordinator.py`, `async_operations.py` | C16. |
| `src/gtach/display/setup_components/rendering/device_surfaces.py` | D08. |
| `src/gtach/display/rendering/engine.py` | D11. |
| `CLAUDE.md` | Rule 8 clarification. |
| `tests/test_low_defects.py` | New: 10 tests. |
| `tests/test_setup_and_gauge.py`, `tests/test_thread_lifecycle.py` | Test app hosts gain `_obd_lock`. |

[Return to Table of Contents](<#table of contents>)

---

## 3. Tests Added and Result

`tests/test_low_defects.py` has 10 tests, one per changed behaviour:

- **A12:** close and re-raise.
- **A13:** discovery after a cancel reports devices.
- **A16:** no shadowing names; the new names subclass `TransportError`.
- **B09:** `retry_delay == 7.0`.
- **B12:** two threads → `_start_obd` once.
- **C10:** 0 and 9 give the defaults, with warnings.
- **C13:** duration 0 → progress 1.0.
- **C15:** the base font is unchanged and the bold font is its own object.
- **D08:** `get_signal_bars(-60)`.
- **D11:** `fb` and `fb_dev` are None.

Nine of the ten fail on the pre-change code. The D08 test was later retargeted from `render_compact_device_item` to `create_slot_surface`, when change-cd5ec050 removed the former.

pytest after this commit: 446 passed (436 before the commit).

[Return to Table of Contents](<#table of contents>)

---

## 4. Success Criteria

| Criterion | How checked | Result |
|---|---|---|
| transport.py defines no ConnectionError/TimeoutError classes | `grep`; `TestTransportExceptionNames` | Pass |
| No bare `except:` in watchdog.py | `grep` | Pass |
| get_rpm_large_font sets bold on no cached shared font | Code review; `TestRpmFontNotShared` | Pass |
| device_surfaces.py contains no `.rssi` | `grep '\.rssi'` | No matches |
| CLAUDE.md rule 8 contains the file-lock clarification | Read the file | Pass |
| `pytest tests/` passes | Full run | 446 passed |

[Return to Table of Contents](<#table of contents>)

---

## 5. Deviations

- **C16, sites changed to `time.monotonic()`:**
  - `touch.py` `_process_touch` fallback;
  - `TouchEvent.__post_init__`, whose docstring was updated;
  - `touch_coordinator` touch down and up;
  - `SetupStateCoordinator` interaction times (3);
  - `AsyncOperation.start_time` default and `end_time` (3), plus the cleanup age;
  - all 11 timing sites in `splash.py`.
- **C16, sites deliberately kept on `time.time()`:**
  - the `manager.py` simulation sine and the `'timestamp'` in its debug info;
  - `obd.py` `OBDResponse.timestamp`;
  - `sim_transport.py` (seed);
  - `thread.py` `creation_time` (hash identity);
  - modules the change does not list, even where the value is a duration: `device_surfaces.py`, `circular_positioning.py`, `rendering/engine.py`, `performance/monitor.py`, `navigation_gestures.py` (removed later) and `utils/platform.py`.
- **C15 font method:** a `get_bold_font()` method on FontManager, with a separate cache cleared by `clear_cache()`, was the chosen form of the separately cached bold font.
- **B09 comments:** the two retry-arc comments in app.py, which said the value "yields None today", were updated.
- **Test helpers:** two existing test app hosts needed `_obd_lock`.
- **Dead branch:** `splash.get_performance_report`'s `[-50:]` trim is now unreachable, because the deque never exceeds 100. It is harmless and was not in change-cd5ec050's list.

[Return to Table of Contents](<#table of contents>)

---

## 6. On-Device Verification Outstanding

On the Pi: signal bars show on DEVICE_LIST, and simbt discovery works after a Cancel.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-07 | Initial implementation report for prompt-4005360c. |

---

Copyright (c) 2026 William Watson. MIT License.
