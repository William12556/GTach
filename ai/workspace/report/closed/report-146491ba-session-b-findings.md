Created: 2026 November 12

# Report: Session B Findings — Reset Retry, Notice Text, Lost-Link Record

---

## Table of Contents

1. [Summary](<#1. summary>)
2. [EDIT A: Reset Retry](<#2. edit a: reset retry>)
3. [EDIT B: Fallback Notice](<#3. edit b: fallback notice>)
4. [EDIT C: Lost Link During Initialisation](<#4. edit c: lost link during initialisation>)
5. [Tests](<#5. tests>)
6. [Success Criteria](<#6. success criteria>)
7. [Deviations and Notes for the Planner](<#7. deviations and notes for the planner>)
8. [Version History](<#version history>)

---

## 1. Summary

prompt-146491ba (change-146491ba, issue-146491ba) was implemented in one commit on branch `claude/nice-cannon-4x2xfo`. EDITS A to C were applied. As instructed, the issue, change and prompt T-Docs all remain in place and active. None was closed or moved.

- pytest `tests/`: 733 passed, 1 xfailed (the xfail is `DEVICE_NOT_SAVED_TEXT`; see section 3).
- mypy `src/`: no issues.
- flake8, black and isort: no findings in the five touched Python files.
- Changed files: `src/gtach/comm/transport.py`, `src/gtach/comm/obd.py`, `src/gtach/display/setup_components/bluetooth/interface.py`, `tests/test_obd_verify_busy_retry.py`, `tests/test_session_b_findings.py` (new), and this report.

[Return to Table of Contents](<#table of contents>)

---

## 2. EDIT A: Reset Retry

**transport.py.** The changes are as follows:

- `LINK_RESET_CAUSE = "connection reset by adapter"` (27 characters) is added after `LINK_BUSY_CAUSE`, with a comment that cites issue-146491ba.
- The entry `_errno.ECONNRESET: LINK_RESET_CAUSE` is added to `_CONNECT_FAULT_CAUSES`.

The file has no other edit. The mapping is used only by `_classify_connect_error`, so the one effect is the cause text of an ECONNRESET connect failure. That text was `ECONNRESET` and is now `connection reset by adapter`. The refused-connect and wedge logic compare only against the ECONNREFUSED entry and `"no bluetooth controller"`, so they are not affected.

**interface.py.** The changes are as follows:

- `LINK_RESET_CAUSE` is imported.
- The class constant `_VERIFY_RETRIED_CAUSES: Tuple[str, ...] = (LINK_BUSY_CAUSE, LINK_RESET_CAUSE)` is added. `Tuple` is added to the `typing` import.
- The loop condition tests `cause not in self._VERIFY_RETRIED_CAUSES`.
- The INFO record reads `f"OBD verify: {cause}, retrying (attempt {n}/{N})"`.
- The class comment names both errnos and cites issue-146491ba.

`_VERIFY_BUSY_ATTEMPTS = 3` and `_VERIFY_BUSY_RETRY_DELAY_S = 1.0` are unchanged.

[Return to Table of Contents](<#table of contents>)

---

## 3. EDIT B: Fallback Notice

Widths were measured with `get_label_small_font()` (Michroma-Regular.ttf, loaded from `src/gtach/assets/fonts/`) under `SDL_VIDEODRIVER=dummy`. The environment was pygame 2.6.1 with SDL 2.28.4.

| Text | Width (px) | ≤ 220 |
|---|---|---|
| `No ELM327 found` | 243 | no |
| `No ELM327` | 163 | yes |
| `No ELM327 found - showing all devices` (previous) | 506 | no |
| `Scan failed` (`SCAN_FAILED_TEXT`) | 139 | yes |
| `Device not saved` (`DEVICE_NOT_SAVED_TEXT`) | 221 | **no** |
| `OBD check failed` (`OBD_CHECK_FAILED_TEXT`) | 217 | yes |

`No ELM327 found` exceeds 220 px. `FALLBACK_LIST_TEXT` is therefore set to `"No ELM327"`. The 217 px for `OBD check failed` matches report-d38362aa section 8.0, which supports the measurement.

**xfail case.** `DEVICE_NOT_SAVED_TEXT` measures 221 px, 1 px over the bound. Per the constraint, it was not changed. Its parametrised case is marked `xfail(strict=True)` with reason "measured 221 px". Because the mark is strict, the test fails if the text or the font later changes so that it fits, and the mark is then reviewed. On the device, `_fit_text` shortens this text when it is shown.

[Return to Table of Contents](<#table of contents>)

---

## 4. EDIT C: Lost Link During Initialisation

In `OBDProtocol._initialize_protocol`, a new check immediately follows the 0100 send:

```python
if response is None and not self.transport.is_connected():
    # A lost link is not a silent vehicle (issue-146491ba).
    self.logger.debug("Link lost during initialisation")
    return False
```

The check precedes the existing 4100 check. `_report_no_vehicle` is not called, so `_vehicle_silent` and `_no_vehicle_logged_at` are left as they were. Every other path is unchanged:

- A `None` reply with the transport still connected (timeout) still reaches `_report_no_vehicle`.
- A non-`None` reply without 4100 also still reaches `_report_no_vehicle`.

[Return to Table of Contents](<#table of contents>)

---

## 5. Tests

**tests/test_obd_verify_busy_retry.py** (extended; the four existing tests are kept unchanged). The new tests are as follows:

| Test | Scenario | Asserts |
|---|---|---|
| `test_reset_then_success` | reset, success | True; 2 connects; sleeps `[1.0]`; 1 disconnect |
| `test_reset_then_busy_then_success` | reset, busy, success | True; 3 connects; sleeps `[1.0, 1.0]` |
| `test_reset_three_times_gives_up` | reset ×3 | False; 3 connects; 2 sleeps |
| `test_refused_is_not_retried` | `connection refused by adapter` | False; 1 connect; no sleep |
| `test_retry_record_names_the_cause` | reset, success | INFO `OBD verify: connection reset by adapter, retrying (attempt 2/3)` |
| `test_link_reset_cause_matches_mapping` | — | `LINK_RESET_CAUSE == _CONNECT_FAULT_CAUSES[errno.ECONNRESET]`; length ≤ 40 |

The existing `test_other_failure_is_not_retried` (`connection timed out`) is kept.

**tests/test_session_b_findings.py** (new). The tests are as follows:

| Test | Scenario | Asserts |
|---|---|---|
| `test_error_line_text_fits[…]` (×4) | each DEVICE_LIST error-line constant | width ≤ 220 px; `DEVICE_NOT_SAVED_TEXT` strict xfail |
| `test_lost_link_is_not_a_silent_vehicle` | transport drops after the ATSP0 send, before 0100 | False; no WARNING or higher; one DEBUG `Link lost during initialisation`; `_vehicle_silent` False; `_no_vehicle_logged_at` None; 0100 not sent |
| `test_lost_link_leaves_silent_state_unchanged` | same, with `_vehicle_silent=True` and a timestamp set beforehand | both left unchanged; no WARNING |
| `test_timeout_with_link_up_is_reported` | 0100 returns None with the link up | False; one WARNING `Vehicle not answering: no valid 0100 response (None)`; `_vehicle_silent` True; no lost-link record |

**Results.** `pytest tests/` produced 733 passed and 1 xfailed in 55.8 s. `mypy src/` reported no issues in 60 source files. The run used Python 3.13 in a local venv. mypy warns that the `python_version = 3.9` setting in `pyproject.toml` is unsupported by the installed mypy; this warning predates the change and is not caused by it.

[Return to Table of Contents](<#table of contents>)

---

## 6. Success Criteria

| Criterion | Result |
|---|---|
| Verify retries `LINK_BUSY_CAUSE` and `LINK_RESET_CAUSE` only, at most 3 attempts, 1.0 s apart | Met |
| `LINK_RESET_CAUSE == _CONNECT_FAULT_CAUSES[errno.ECONNRESET]`, ≤ 40 characters | Met (27) |
| `FALLBACK_LIST_TEXT` renders at ≤ 220 px | Met (163 px) |
| A None 0100 reply with the transport disconnected produces no WARNING and leaves `_vehicle_silent` unchanged | Met |
| Diff touches only the three source files, the two test modules and the report | Met |
| pytest passes; mypy clean | Met |

[Return to Table of Contents](<#table of contents>)

---

## 7. Deviations and Notes for the Planner

1. **Prompt task versus CLAUDE.md task text.** Per the operator's instruction, no T-Doc was closed or moved. The prompt T-Doc remains in `ai/workspace/prompt/`.
2. **DEVICE_NOT_SAVED_TEXT is 221 px.** It is 1 px over the error line. This is a candidate for a follow-up text change, for example `Not saved`, which is outside this change's scope.
3. **Design update pending.** The fallback notice text in design-a3b4c5d6 section 4.0 should now read `No ELM327` (traceability item for the planner).
4. **Constant naming.** The retried set is a class constant, `_VERIFY_RETRIED_CAUSES`, placed next to the existing `_VERIFY_BUSY_*` constants. The `_VERIFY_BUSY_*` names were kept because the prompt fixes them, although they now bound both causes.
5. **Extra test.** `test_refused_is_not_retried` adds the change document's "connection refused" scenario next to the kept timed-out test. `test_lost_link_leaves_silent_state_unchanged` covers the "unchanged" wording when the prior state is silent.
6. **Human verification outstanding.** The following device checks remain:
   - three setups with the emulator;
   - the fallback notice with no ELM327 in range.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-12 | Initial report for prompt-146491ba. |

---

Copyright (c) 2026 William Watson. MIT License.
