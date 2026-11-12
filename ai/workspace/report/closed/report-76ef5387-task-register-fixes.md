# Report: Task Register Fixes — Texts, Simulation, Log Levels, Connect Causes

Created: 2026 November 12

## Table of Contents

- [1.0 Summary](#10-summary)
- [2.0 Changes by Edit](#20-changes-by-edit)
- [3.0 Tests](#30-tests)
- [4.0 Success Criteria](#40-success-criteria)
- [5.0 Deviations and Notes](#50-deviations-and-notes)
- [6.0 Device Verification](#60-device-verification)
- [Version History](#version-history)

---

## 1.0 Summary

prompt-76ef5387 (change-76ef5387, issue-76ef5387) was implemented in one commit on branch `claude/friendly-cerf-egri96`. EDITS A to G were applied. The issue and change T-Docs remain active pending test results. The prompt T-Doc was closed and moved to `ai/workspace/prompt/closed/`.

- pytest `tests/`: 780 passed, 0 failed.
- mypy `src/` (`python -m mypy src/`): no issues in 60 source files.
- black, isort and flake8 report nothing in the touched files.
- `git diff` touches only `transport.py`, `sim_bluetooth.py`, `interface.py`, `bin/gtach.service`, the three test modules, this report and the prompt move.

[Return to Table of Contents](#table-of-contents)

---

## 2.0 Changes by Edit

| Edit | File | Change |
|---|---|---|
| A (F1) | `display/setup_components/bluetooth/interface.py` | `DEVICE_NOT_SAVED_TEXT = "Not saved"`. Measured in `get_label_small_font()`: 135 px (was 221 px for "Device not saved"); limit 220 px. |
| A (F1) | `tests/test_session_b_findings.py` | The strict-xfail `pytest.param` replaced by plain `DEVICE_NOT_SAVED_TEXT`; module docstring cites change-76ef5387. |
| B (F2) | `comm/sim_bluetooth.py` | Imports `DeviceType`. The three `device_type="ELM327"` devices carry `DeviceType.HIGHLY_LIKELY_ELM327`; "Generic BT Adapter" (`"Compatible"`) carries `DeviceType.POSSIBLY_COMPATIBLE`. The comment above `_FAKE_DEVICES` cites issue-76ef5387. |
| C (F3) | `comm/transport.py` | `send_command`, `_IO_ERRORS` handler: if `self._acquire_handle() is not handle`, logs DEBUG `Command %r ended by link close: %s` and returns None without touching state, `_last_failure_cause` or the handle. Otherwise the existing ERROR record, classification, state change and discard run unchanged. The timeout and generic handlers are unchanged. |
| D (F4) | `comm/transport.py` | `_errno.ECONNABORTED: LINK_RESET_CAUSE` added to `_CONNECT_FAULT_CAUSES`; the `LINK_RESET_CAUSE` comment names ECONNRESET and ECONNABORTED. |
| E (F5) | `bin/gtach.service` | `hciuart.service` appended to `After=`, preceded by a one-line comment (ordering only; issue-76ef5387). `Wants=` unchanged; no `Requires=`. |
| F | `display/setup_components/bluetooth/interface.py` | `on_pairing_complete`: a COMPLETED operation with a falsy result logs "Failed to pair with device: ..." at WARNING. The exception branch ("Pairing operation failed") stays at ERROR. |
| G (F6) | `comm/transport.py` | New module tuple `_CONTROLLER_WORKING_CAUSES: Tuple[str, ...]` = ECONNREFUSED's and EHOSTDOWN's causes. `connect()` uses `controller_working = cause in _CONTROLLER_WORKING_CAUSES` to skip the counter increment, and `cause not in _CONTROLLER_WORKING_CAUSES` in the escalation condition. Comments updated. `Tuple` added to the `typing` import. |

Unchanged as required: retry intervals, `_MAX_CONSECUTIVE_CONNECT_FAILURES` (6), `_MAX_CONSECUTIVE_TIMEOUTS` (5), the verify retry bound and delay.

[Return to Table of Contents](#table-of-contents)

---

## 3.0 Tests

| Module | Tests added | Covers |
|---|---|---|
| `tests/test_session_b_findings.py` | xfail removed | A: "Not saved" fits 220 px. |
| `tests/test_connect_error_classification.py` | `TestPlannedCloseIsNotAnError` (3) | C: `disconnect()` during the read; `drop_link(cause="planned")` during the read (cause kept); EBADF on the current handle still logs ERROR and records `EBADF`. |
| | `TestConnAbortedIsALinkReset` (1) | D. |
| | `TestWorkingControllerCausesDoNotEscalate` (4) | G: eight EHOSTDOWN never escalate (counter stays 0); eight EHOSTDOWN then EBUSY gives `LINK_BUSY_CAUSE`; five alternating EHOSTDOWN/EBUSY pairs count 5, no wedge; six EBUSY still escalate. |
| `tests/test_task_register_fixes.py` (new) | 5 | B: no fake device UNKNOWN; classification matches `device_type`; a `SimBluetoothPairing` scan fed through the setup flow sets no error line. F: result False logs WARNING and no ERROR; a FAILED operation still logs ERROR. |

Results:

- Affected modules (`test_task_register_fixes.py`, `test_connect_error_classification.py`, `test_session_b_findings.py`): 71 passed.
- Full suite `pytest tests/` (run with `-o addopts=""`, i.e. without coverage): 780 passed, 0 failed, 1 warning (pygame `pkg_resources` deprecation).
- Regression scope of the change (`test_comm_layer_defects.py`, `test_reconnect_path.py`, `test_setup_flow.py`, `test_obd_verify_busy_retry.py`) is included in the full run.

[Return to Table of Contents](#table-of-contents)

---

## 4.0 Success Criteria

| Criterion | Result |
|---|---|
| `DEVICE_NOT_SAVED_TEXT == 'Not saved'`, ≤ 220 px, no xfail | Met (135 px). |
| No fake device UNKNOWN; simbt scan sets no error line | Met. |
| Planned close: no ERROR, `last_failure_cause` unchanged | Met. |
| `_CONNECT_FAULT_CAUSES[ECONNABORTED] == LINK_RESET_CAUSE` | Met. |
| `After=` contains `hciuart.service`; `Wants=` unchanged | Met. |
| Pairing returning False logged at WARNING | Met. |
| EHOSTDOWN / ECONNREFUSED never wedge; six EBUSY do | Met. |
| Diff limited to the listed files | Met (plus the prompt move to `closed/`). |
| pytest and mypy clean | Met. |

[Return to Table of Contents](#table-of-contents)

---

## 5.0 Deviations and Notes

1. `tests/test_task_register_fixes.py` imports `_Env`, `_op` and `_device` from `test_setup_flow` (the same cross-module import pattern as `test_gauge_display_touch.py`) rather than duplicating the setup harness. It defines its own module-scoped `pygame.init()` fixture.
2. The `_IO_ERRORS` handler's existing `logger.error("Error communicating with device: %s", e)` has no `exc_info=True`. It is a narrow handler, and the prompt requires its ERROR path unchanged, so it was left as is.
3. mypy: the `mypy` on PATH in this container is an isolated tool install without pygame or stubs and reports 20 import errors, identically before and after the change. `python -m mypy src/` with `types-PyYAML` and `types-psutil` installed in the environment (not added to the project) reports no issues.
4. `black --check .` and `isort --check .` repo-wide report pre-existing failures in untouched files (`ai/engine/`, `tests/test_sim_transport.py`); the touched files pass.
5. EDIT C also covers a reconnect that installed a new handle while the old read was pending: the stale handle is not current, so it logs DEBUG.
6. EDIT G compares cause strings, as specified. EHOSTUNREACH maps to the same "adapter not reachable" string as EHOSTDOWN, so EHOSTUNREACH failures are also excluded from the wedge counter and escalation. No test asserts this; the planner may confirm it is intended.
7. Device verification (owner): `systemctl show hciuart -p Type,ActiveState`; `systemd-analyze critical-chain gtach.service`; reboot with the adapter in range; service stop while connected; adapter radio off for 2 min; one setup with the emulator. EDIT E needs the service file redeployed and `systemctl daemon-reload`.

[Return to Table of Contents](#table-of-contents)

---

## 6.0 Device Verification

Planner-guided check on the Pi with GTach 0.5.0 plus c717048, 2026-11-12. Logs pulled to `logs/`.

| Edit | Check | Result |
|---|---|---|
| A | Not triggerable on the device (needs a failed device save) | Unit test only (135 px). |
| B | — | Unit tests only. |
| C | Service stopped while connected (reboot 13:36; `systemctl stop` about 13:42) | No ERROR record. The last 'Bad file descriptor' is 13:21:21, the stop of the previous version for deployment. |
| D | Setup with the emulator, 13:50 | The first main-transport connect after setup failed with ECONNABORTED, shown as '(connection reset by adapter)'; the retry connected. The post-pairing verify met ECONNRESET at 13:50:04 and passed on its retry (first on-device run of the issue-146491ba reset retry). |
| E | Reboot 13:36 with the adapter in range | Ordering applied (hciuart 13:36:28.49 to 34.94, GTach started 35.72), but the first connect still failed once (EACCES, cause not identified) and the retry connected. bluetooth.service is skipped at boot until hciuart attaches the controller. Display start about 7 s later for no gain: reverted (change-76ef5387 v1.1 notes). |
| F | — | Unit tests only. |
| G | Emulator radio off, 13:46:05 to 13:47:26 | Nine consecutive EHOSTDOWN failures, all 'adapter not reachable'; no 'wedged'. After power on, the 13:50 setup paired and connected. |

[Return to Table of Contents](#table-of-contents)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-12 | Initial report for prompt-76ef5387. |
| 1.1 | 2026-11-12 | Layout aligned with project conventions (title, flat ToC, GFM slugs, numbered sections); added 6.0 Device Verification. |

---

Copyright (c) 2026 William Watson. MIT License.
