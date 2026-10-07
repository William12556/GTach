Created: 2026 October 07

# Report: Reconnect-Path Corrections

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

prompt-907de6de (change-907de6de, issue-907de6de; audit-36b6ea95 A02, A03, A04, A05, A06 and A19) was implemented in commit `41dd663da6e046be30d1d7a9d4f5b7003752a4ae`.

- **EDIT A:** `_initialize_protocol` succeeds only if the 0100 reply contains `4100` after whitespace is removed and the text is upper-cased. NO DATA, '?', 7F and empty replies now fail.
- **EDIT B:** after a failed initialisation, `_protocol_loop` sends a heartbeat and then waits `_INIT_RETRY_DELAY_S` (2.0 s) on `shutdown_event` before retrying.
- **EDIT C:** an EOF read calls `drop_link(cause=_PEER_CLOSED_CAUSE)`, which closes the handle and records 'adapter closed the connection'.
- **EDIT D:** the new `_ADAPTER_CHECKS` flag defaults to False on `OBDTransport` and is True on `RFCOMMTransport`. Only an opted-in transport reports 'no bluetooth controller' or the wedge cause.
- **EDIT E:** on a non-EOF transport (serial), an empty read with nothing buffered counts as a timeout. A partial response is still returned.
- **EDIT F:** `_request_rpm` decodes only replies of at least four bytes whose first byte is 0x41 and second byte is 0x0C.

[Return to Table of Contents](<#table of contents>)

---

## 2. Files Changed

| File | Change |
|---|---|
| `src/gtach/comm/obd.py` | EDITS A, B (`_INIT_RETRY_DELAY_S`) and F. |
| `src/gtach/comm/transport.py` | EDITS C (`_PEER_CLOSED_CAUSE`), D (`_ADAPTER_CHECKS`, both checks) and E. |
| `src/gtach/comm/rfcomm.py` | EDIT D: `_ADAPTER_CHECKS = True`. |
| `tests/test_reconnect_path.py` | New: 16 tests. |
| `tests/test_connect_error_classification.py` | `_StubTransport._ADAPTER_CHECKS = True`, with a comment that it models RFCOMM. No other change. |

[Return to Table of Contents](<#table of contents>)

---

## 3. Tests Added and Result

`tests/test_reconnect_path.py` has 16 tests, covering every prompt scenario and the edge case:

- **Init validation:**
  - three positive 0100 forms are accepted (spaced, unspaced, after SEARCHING...);
  - NO DATA, UNABLE TO CONNECT, '?', '7F 01 12' and None are rejected.
- **Back-off:** two failures and then shutdown → `wait(2.0)` at least twice, and the loop exits.
- **Peer close:** None is returned, the handle is closed, `is_connected()` is False, and the cause is 'adapter closed the connection'.
- **Adapter checks:**
  - opted out, six refused connects never report 'no bluetooth controller' or the wedge cause;
  - opted in, the cause is 'no bluetooth controller';
  - class defaults: RFCOMM True; OBDTransport, TCP and serial False.
- **Serial:**
  - five silent commands → `drop_link` exactly once, and the link is down;
  - `b'41 0C 1A F8'` followed by `b''` → '41 0C 1A F8'.
- **PID check:** '41 0D 1A F8' → None; '41 0C 1A F8' → `data == b'\x1a\xf8'`.

Nine of the 16 tests fail on the pre-change code.

pytest after this commit: 355 passed (339 before the commit).

[Return to Table of Contents](<#table of contents>)

---

## 4. Success Criteria

| Criterion | How checked | Result |
|---|---|---|
| `startswith('7F')` gone from obd.py; '4100' validation present | `grep`; `TestInitValidation` | Pass |
| `_INIT_RETRY_DELAY_S == 2.0`; the loop waits on `shutdown_event` after init failure | Code review; `TestInitBackOff` | Pass |
| The EOF branch calls `drop_link(cause=_PEER_CLOSED_CAUSE)` | Code review; `TestPeerClose` | Pass |
| `OBDTransport._ADAPTER_CHECKS` False; `RFCOMMTransport._ADAPTER_CHECKS` True | `test_class_defaults` | Pass |
| `pytest tests/` passes | Full run | 355 passed |

[Return to Table of Contents](<#table of contents>)

---

## 5. Deviations

- In the EOF branch, `drop_link` is called where the removed lock block was, so it now runs before the kept "Connection closed by device" error log. The two lines previously ran in the opposite order.
- The test module has one test beyond the prompt's scenarios: a class-defaults test for the edge case.

[Return to Table of Contents](<#table of contents>)

---

## 6. On-Device Verification Outstanding

With the ELM327 emulator:

1. With the vehicle off (0100 → NO DATA), the log must not show init success, and init must be retried every 2 s.
2. Stop the emulator so that it closes the socket. The DISCONNECTED screen must show 'adapter closed the connection'.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-07 | Initial implementation report for prompt-907de6de. |

---

Copyright (c) 2026 William Watson. MIT License.
