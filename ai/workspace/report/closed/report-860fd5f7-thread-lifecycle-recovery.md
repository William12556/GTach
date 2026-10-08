Created: 2026 October 07

# Report: Process-Restart Recovery and Bounded OBD Heartbeat Gaps

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

prompt-860fd5f7 (change-860fd5f7, issue-860fd5f7; audit-36b6ea95 A01/B02, B01, B05 and B03) was implemented in commit `f5d58f524eec17374c9cda9cad449616e4f65ba9`.

- **EDIT A:** `ThreadManager._restart_thread` and `handle_thread_failure` are deleted. `stop_thread` calls the registered `stop_func` after releasing `_state_lock` and before the join. `register_thread` replaces an entry whose thread is not alive.
- **EDIT B:** `WatchdogMonitor`:
  - `critical_threads` is `{'display', 'obd_protocol'}`;
  - `_attempt_hard_recovery` is deleted; a second recovery-tier failure logs an ERROR; a non-critical critical-tier timeout logs its ERROR line only;
  - a started thread that has exited while RUNNING or STARTING is marked STOPPED, and if it is critical, graceful shutdown follows. Registered-but-unstarted threads (`ident is None`) are not affected.
- **EDIT C:** the `OBDProtocol` inner loop also tests `shutdown_event`. `_send_command` refreshes the `obd_protocol` heartbeat on every command.
- **EDIT D:** in `OBDTransport.send_command`, the timeout is applied before the write. The read loop is bounded by a monotonic deadline of `timeout + _READ_DEADLINE_MARGIN_S` (1.0 s). The timeout path is extracted into `_record_timeout`.
- **EDIT E:** `SimTransport.is_connected` and `state` report the real connection flag.
- **EDIT F:** `transport` is registered with `stop_func=self._transport.disconnect`. `_re_enter_setup` stops `transport` and then `obd_protocol` through `stop_thread`.

[Return to Table of Contents](<#table of contents>)

---

## 2. Files Changed

| File | Change |
|---|---|
| `src/gtach/core/thread.py` | EDIT A. |
| `src/gtach/core/watchdog.py` | EDIT B; class docstring escalation list updated. |
| `src/gtach/comm/obd.py` | EDIT C. |
| `src/gtach/comm/transport.py` | EDIT D; `import time` added. |
| `src/gtach/comm/sim_transport.py` | EDIT E. |
| `src/gtach/app.py` | EDIT F (both `register_thread('transport', ...)` calls; `_re_enter_setup`). |
| `tests/test_thread_lifecycle.py` | New: 15 tests. |
| `tests/test_watchdog_process_termination.py` | `TestAdvisoryTier.test_membership` asserts `{'display', 'obd_protocol'}`; the class docstring is updated to match. |

[Return to Table of Contents](<#table of contents>)

---

## 3. Tests Added and Result

`tests/test_thread_lifecycle.py` has 15 tests, covering every prompt scenario and both edge cases:

- **Watchdog:**
  - a stale unstarted `obd_protocol` → shutdown once;
  - a stale non-critical `worker` over three checks → ERROR records, the original thread object kept, no shutdown;
  - an exited critical `display` → STOPPED and shutdown;
  - an exited non-critical thread → STOPPED, INFO and no shutdown;
  - an unstarted `display` with a fresh heartbeat → unchanged.
- **`stop_thread`:**
  - `stop_func` is called once, with `_state_lock` acquirable from a helper thread, and the call returns True;
  - a raising `stop_func` still joins.
- **`register_thread`:** a dead entry is replaced; a live entry is kept and a warning logged.
- **OBD protocol:**
  - with SimTransport, `stop()` while connected ends the thread within 2 s;
  - `_send_command(b'ATE0')` → one `update_heartbeat('obd_protocol')`.
- **SimTransport:** the state is reported in both directions.
- **`send_command`:**
  - endless `SEARCHING` returns None in under 1.7 s with `_consecutive_timeouts == 1`;
  - `_set_timeout` precedes `_write`, and a one-read response is unchanged.
- **`_re_enter_setup`:** `stop_thread('transport', 2.0)` then `('obd_protocol', 2.0)`, and no direct `disconnect` or `stop` call.

Against the pre-change sources the module does not complete (the OBD stop test never ends under the old inner loop with an always-connected SimTransport); the run was ended by its timeout.

pytest after this commit: 336 passed (321 before the commit).

[Return to Table of Contents](<#table of contents>)

---

## 4. Success Criteria

| Criterion | How checked | Result |
|---|---|---|
| `grep -rn '_restart_thread\|handle_thread_failure\|_attempt_hard_recovery' src/` returns nothing | Ran the grep (backup files excluded by the `grep -v _backup` filter; neither backup file matches) | No matches |
| `critical_threads == {'display', 'obd_protocol'}` | Interpreter check; `test_membership` | Pass |
| The dead-thread rule tests `thread.ident is not None` | Code review; `test_registered_but_not_started_is_left_alone` | Pass |
| `stop_func` called after releasing `_state_lock` and before join | Code review; `test_stop_func_runs_unlocked_before_join` | Pass |
| `_re_enter_setup` has no direct `self._obd.stop()` or `self._transport.disconnect()` | `grep` matches only in `shutdown()` (lines 553, 555) | Pass |
| `_set_timeout` precedes `_write`; the read loop is bounded by a monotonic deadline | Code review; `TestSendCommandDeadline` | Pass |
| `OBDProtocol._send_command` calls `update_heartbeat('obd_protocol')` | `test_every_command_refreshes_heartbeat` | Pass |
| `SimTransport.is_connected` returns the connection flag | `test_reports_real_state` | Pass |
| `pytest tests/` passes | Full run | 336 passed |

[Return to Table of Contents](<#table of contents>)

---

## 5. Deviations

- The `TestAdvisoryTier` class docstring in `tests/test_watchdog_process_termination.py` was updated with the assertion, so that it does not state the old membership.
- As the constraints require, the `RecoveryLevel.HARD_RECOVERY` member and the `RecoveryStats` hard-recovery fields are kept although nothing sets them now (Phase 5).

[Return to Table of Contents](<#table of contents>)

---

## 6. On-Device Verification Outstanding

1. On the development host, run `gtach --transport simtcp`, send SIGTERM, and confirm that it exits within a few seconds.
2. On the Pi, run a soak test of several hours with link losses, adapter power cycles and emulator restarts. Afterwards `/opt/gtach/error.log` must contain no 'appears unresponsive' warning for `obd_protocol` and no unexpected shutdown.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-07 | Initial implementation report for prompt-860fd5f7. |

---

Copyright (c) 2026 William Watson. MIT License.
