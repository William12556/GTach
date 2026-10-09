Created: 2026 October 09

# Report: SimTransport Observes drop_link

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

prompt-50bf25ad (change-50bf25ad, issue-50bf25ad) is implemented. `SimTransport.drop_link` clears `_connected` under `self._lock`, releases the lock, then calls `OBDTransport.drop_link(cause)`. `_shutdown` is not touched, so `reconnect_indefinitely` reconnects.

[Return to Table of Contents](<#table of contents>)

---

## 2. Files Changed

| File | Change |
|---|---|
| `src/gtach/comm/sim_transport.py` | New method `SimTransport.drop_link(cause=None)`. |
| `tests/test_lifecycle_sim.py` | Strict xfail removed from `TestLinkLoss.test_drop_is_observed_and_link_reconnects`. |
| `tests/test_sim_transport.py` | New: 4 unit tests. |

`src/gtach/comm/transport.py` is unchanged.

[Return to Table of Contents](<#table of contents>)

---

## 3. Tests and Result

New tests: drop with a cause (state, cause, `_shutdown` clear); drop without a cause (`_SILENT_LINK_CAUSE`); connect after drop; drop before any connect.

- Before: 539 passed, 2 xfailed.
- After: 544 passed, 1 xfailed (4 new tests; the link-loss lifecycle test now passes). The remaining xfail is `TestWatchdogQuiet`, removed by change-04c18cda.
- mypy error count unchanged (338).

[Return to Table of Contents](<#table of contents>)

---

## 4. Success Criteria

| Criterion | Result |
|---|---|
| One `def drop_link` in `sim_transport.py` | Met |
| Link-loss test passes without xfail | Met |
| No diff to `transport.py` | Met |
| `pytest tests/` passes | Met |

[Return to Table of Contents](<#table of contents>)

---

## 5. Deviations

None.

[Return to Table of Contents](<#table of contents>)

---

## 6. Items Kept

- The `TestWatchdogQuiet` xfail, as the prompt directs (change-04c18cda scope).
- `connect`, `disconnect`, `is_connected` and `state` are unchanged, per the constraints.

[Return to Table of Contents](<#table of contents>)

---

## 7. On-Device Verification Outstanding

None: simulation only. Optional desk check: `gtach --transport simbt --debug`, trigger a link drop, and confirm `debug.log` shows the "dropped - will attempt to reconnect" line followed by a reconnect and resumed RPM samples.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-09 | Initial report for prompt-50bf25ad. |

---

Copyright (c) 2026 William Watson. MIT License.
