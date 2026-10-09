Created: 2026 October 09

# Report: Bounded EBUSY Retry in Post-Pairing OBD Verify

---

## Table of Contents

1. [Summary](<#1. summary>)
2. [Files Changed](<#2. files changed>)
3. [Tests and Results](<#3. tests and results>)
4. [Success Criteria](<#4. success criteria>)
5. [Deviations](<#5. deviations>)
6. [Human Decisions and On-Device Verification](<#6. human decisions and on-device verification>)
7. [Version History](<#version history>)

---

## 1. Summary

prompt-d26ca557 (change-d26ca557, issue-d26ca557) was implemented in the commit that adds this report. It was applied after prompt-4f671d09 (commit `07bb8e5`), as required.

`verify_obd_connection` now loops over one `RFCOMMTransport` instance for up to `_VERIFY_BUSY_ATTEMPTS` (3) connect attempts. It retries only while `transport.last_failure_cause == LINK_BUSY_CAUSE`, sleeping `_VERIFY_BUSY_RETRY_DELAY_S` (1.0 s) between attempts and logging each retry at INFO. Any other failure, or a busy failure on the last attempt, logs the existing WARNING `OBD verify: RFCOMM connect failed` and returns False. The ATZ probe and the `disconnect()` in `finally` are unchanged.

`transport.py` gains the public constant `LINK_BUSY_CAUSE`, which the EBUSY entry of `_CONNECT_FAULT_CAUSES` now uses. The value is unchanged. `start_device_probe`, the pairing-success callback and `RFCOMMTransport` were not changed.

[Return to Table of Contents](<#table of contents>)

---

## 2. Files Changed

| File | Change |
|---|---|
| `src/gtach/comm/transport.py` | `LINK_BUSY_CAUSE` added above `_CONNECT_FAULT_CAUSES`, with a comment citing issue-d26ca557. The EBUSY entry uses it. |
| `src/gtach/display/setup_components/bluetooth/interface.py` | `import time`; import of `LINK_BUSY_CAUSE`; class constants `_VERIFY_BUSY_ATTEMPTS`, `_VERIFY_BUSY_RETRY_DELAY_S` with a comment citing issue-d26ca557; bounded retry loop in `verify_obd_connection`. |
| `tests/test_obd_verify_busy_retry.py` | New: 4 tests. |

[Return to Table of Contents](<#table of contents>)

---

## 3. Tests and Results

`tests/test_obd_verify_busy_retry.py` follows the prompt's edge cases. It sets `socket.AF_BLUETOOTH` with `raising=False` and builds the interface with `__new__`, setting `logger`, a `device_store` stub and `_pairing_factory = None`. It patches `gtach.comm.rfcomm.RFCOMMTransport` with a scripted fake and patches `time.sleep` globally with a recorder.

- `test_busy_then_success`: True; 2 connects; sleeps `[1.0]`; 1 disconnect.
- `test_other_failure_is_not_retried`: `connection timed out` gives False; 1 connect; no sleep.
- `test_busy_three_times_gives_up`: False; 3 connects; 2 sleeps.
- `test_link_busy_cause_matches_mapping`: `LINK_BUSY_CAUSE == _CONNECT_FAULT_CAUSES[errno.EBUSY]`.

Before `verify_obd_connection` was changed, with `LINK_BUSY_CAUSE` already added so the module imports:

- `test_busy_then_success` failed (`assert False is True`), as the prompt requires.
- `test_busy_three_times_gives_up` failed (`assert 1 == 3`).
- The other two passed. The non-busy path and the constant need no behaviour change.

After implementation:

| Check | Result |
|---|---|
| `tests/test_obd_verify_busy_retry.py` | 4 passed |
| `pytest tests/` before this change (after 4f671d09) | 573 passed |
| `pytest tests/` after | 577 passed |
| `mypy src/` | 0 errors in 60 source files |
| `black --check`, `isort --check-only`, `flake8` on changed files | Clean |

[Return to Table of Contents](<#table of contents>)

---

## 4. Success Criteria

| Criterion | Result |
|---|---|
| The four tests pass; busy-then-success fails on the old source | Pass; failed before as recorded in §3 |
| `pytest tests/` passes; `mypy src/` 0 errors | 577 passed; 0 errors |
| `transport.py`: no edit beyond the constant | `git diff` shows only `LINK_BUSY_CAUSE`, its comment and the mapping entry |

[Return to Table of Contents](<#table of contents>)

---

## 5. Deviations

None in substance. One interpretation:

- In the log text `OBD verify: link busy, retrying (attempt n/3)`, `n` is the attempt about to run. Three busy failures log `attempt 2/3` and `attempt 3/3`. If `n` should instead be the attempt that just failed (1/3, 2/3), change `attempt + 1` to `attempt` in the `logger.info` call.

[Return to Table of Contents](<#table of contents>)

---

## 6. Human Decisions and On-Device Verification

- Confirm the `n` interpretation in §5.
- On gtach.local: re-pair the ELM327 emulator several times. Setup should complete without Retry. `error.log` may still show one EBUSY line per busy attempt; that is out of scope.
- If the link stays busy longer than about 2 s, tune `_VERIFY_BUSY_ATTEMPTS` or `_VERIFY_BUSY_RETRY_DELAY_S`. Keep the attempt count below the transport's six-failure wedge escalation.
- The issue and change T-Docs remain active pending that result.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-09 | Initial report for prompt-d26ca557. |

---

Copyright (c) 2026 William Watson. MIT License.
