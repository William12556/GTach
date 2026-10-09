Created: 2026 October 09

# Report: OBD Settle Without Heartbeat Gap

---

## Table of Contents

1. [Summary](<#1. summary>)
2. [Files Changed](<#2. files changed>)
3. [Tests and Result](<#3. tests and result>)
4. [Success Criteria](<#4. success criteria>)
5. [Deviations](<#5. deviations>)
6. [Items Kept](<#6. items kept>)
7. [On-Device Verification Outstanding](<#7. on-device verification outstanding>)
8. [Version History](<#version history>)

---

## 1. Summary

prompt-04c18cda (change-04c18cda, issue-04c18cda) is implemented. The pre-initialised branch of `OBDProtocol._initialize_protocol` no longer calls `time.sleep(1.5)`. It waits on `shutdown_event` in slices of at most 0.5 s against a `time.monotonic()` deadline of 1.5 s, sends a heartbeat after each slice, and returns False within one slice when a stop is requested.

[Return to Table of Contents](<#table of contents>)

---

## 2. Files Changed

| File | Change |
|---|---|
| `src/gtach/comm/obd.py` | Class constants `_PRE_INIT_SETTLE_S = 1.5`, `_SETTLE_SLICE_S = 0.5`; settle loop in `_initialize_protocol`. |
| `tests/test_lifecycle_sim.py` | Strict xfail removed from `TestWatchdogQuiet.test_no_obd_unresponsive_warning`. |
| `tests/test_obd_settle.py` | New: 3 tests. |

[Return to Table of Contents](<#table of contents>)

---

## 3. Tests and Result

New tests: heartbeat gap ≤ 0.6 s and duration ≥ 1.4 s; stop set at 0.2 s returns False within 0.7 s with no `ATE0` sent; stop already set returns False immediately with no command sent.

- Before: 544 passed, 1 xfailed.
- After: 548 passed, 0 xfailed.
- mypy error count unchanged (338).

[Return to Table of Contents](<#table of contents>)

---

## 4. Success Criteria

| Criterion | Result |
|---|---|
| No `time.sleep(1.5)` in `obd.py` | Met |
| No xfail marker in `test_lifecycle_sim.py` | Met |
| `pytest tests/` passes | Met |

[Return to Table of Contents](<#table of contents>)

---

## 5. Deviations

- The DEBUG message is split over two string literals to stay within 88 columns; the rendered text is as specified.

[Return to Table of Contents](<#table of contents>)

---

## 6. Items Kept

- The full-init (ATZ) branch and the existing try/except are unchanged, per the scope constraint.

[Return to Table of Contents](<#table of contents>)

---

## 7. On-Device Verification Outstanding

- On the Pi, after setup completes, the first OBD connection initialises and RPM appears.
- `error.log` shows no `obd_protocol` unresponsive warning during that first connection.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-09 | Initial report for prompt-04c18cda. |

---

Copyright (c) 2026 William Watson. MIT License.
