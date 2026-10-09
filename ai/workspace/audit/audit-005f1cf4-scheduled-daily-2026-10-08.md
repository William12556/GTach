Created: 2026 October 8
# GTach Scheduled Daily Audit — 2026-10-08 (audit-005f1cf4)

---

## Table of Contents

- [1.0 Purpose](<#1.0 purpose>)
- [2.0 Method](<#2.0 method>)
- [3.0 Activity Summary](<#3.0 activity summary>)
- [4.0 Continue Probe Acts After the User Leaves the Screen](<#4.0 continue probe acts after the user leaves the screen>)
- [5.0 Verification Script Overwrites Service Logs](<#5.0 verification script overwrites service logs>)
- [6.0 Discovery Chunk Timeout Shorter Than Scan Timeout](<#6.0 discovery chunk timeout shorter than scan timeout>)
- [7.0 Preflight Restore Path Drops Rollback Protection](<#7.0 preflight restore path drops rollback protection>)
- [8.0 Stop Timeout Not Honoured for obd_protocol](<#8.0 stop timeout not honoured for obd_protocol>)
- [9.0 DeviceStore Memory and Disk Diverge on Save Failure](<#9.0 devicestore memory and disk diverge on save failure>)
- [10.0 ConfigStore Concurrent Saves Share One Temp Path](<#10.0 configstore concurrent saves share one temp path>)
- [11.0 ConfigStore Load Accepts Values Validate Rejects](<#11.0 configstore load accepts values validate rejects>)
- [12.0 Late OBD Reply Accepted Once](<#12.0 late obd reply accepted once>)
- [13.0 Link-Loss Tests Pass Without Exercising Link Loss](<#13.0 link-loss tests pass without exercising link loss>)
- [14.0 Verification Script Loops on Trailing --since](<#14.0 verification script loops on trailing --since>)
- [15.0 Gauge Range Cap Below Permitted Redline](<#15.0 gauge range cap below permitted redline>)
- [16.0 Observations](<#16.0 observations>)
- [17.0 Changes Reviewed Without Finding](<#17.0 changes reviewed without finding>)
- [18.0 Recommendations](<#18.0 recommendations>)
- [Version History](<#version history>)

---

## 1.0 Purpose

This audit reviews code changes committed to William12556/GTach in the 24 hours preceding 2026-10-08 07:45 Europe/Berlin, and reports defects that can be substantiated from source.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Method

- Anonymous blob-filtered clone; window derived from commit timestamps; diff range `e3f2aec^..HEAD` (HEAD `b6a2792`).
- Code-bearing paths (`*.py`, `*.sh`, `*.service`, `*.toml`, `*.yaml`) were reviewed per commit. Documentation changes were counted, not reviewed.
- Commit `d44dca9` (black and isort) was checked mechanically: a normalised AST comparison (docstrings removed, import order and alias order ignored) showed no semantic change in any of its 83 Python files.
- Removed symbols from `f5ab73a` and `f789966` were searched for at HEAD; `compileall` and an import smoke test with hardware libraries stubbed were run. No orphaned references were found.
- Every finding below was re-read at HEAD before inclusion. Line numbers refer to HEAD.
- Tests were not executed; pytest is not installed in the audit container.
- Issues and pull requests were not retrieved; the run was git-only.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Activity Summary

| Repository | Commits | Files | Insertions | Deletions | New tags |
|---|---|---|---|---|---|
| William12556/GTach | 42 | 198 | 27092 | 16440 | none |

- Files by type: 93 `.py`, 84 `.md`, 8 `.sh`, 6 `.txt`, 4 `.yaml`, 1 `.toml`, 1 `.service`, 1 `.flake8`.
- Most changes implement the audit-36b6ea95 remediation (Phases 0–5). `pyproject.toml` moved from 0.4.3 to 0.4.5 without a tag. The Abarth profile `redline_rpm` changed from 6000 to 6500, which remains valid against the profile constraints.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Continue Probe Acts After the User Leaves the Screen

- **Commit:** 523bb21. **Classification:** Confirmed (trigger is timing-dependent). **Severity:** Medium.
- **Location:** `src/gtach/display/setup.py:922-944`, interacting with `:946-954` and `setup_components/state/coordinator.py:177-181`.

```python
def _on_probe_result(ok: bool) -> None:
    self._probe_in_flight = False
    if ok:
        self.state_coordinator.complete_setup()
        return
    ...
    self.state_coordinator.transition_to_screen(SetupScreen.WELCOME)
```

- The device probe now runs asynchronously; the RFCOMM connect may take up to 10 s. The CURRENT_DEVICE screen still offers `new_setup`, which removes the stored device and transitions to WELCOME.
- If the user taps `new_setup` during the probe and the probe then succeeds, `complete_setup()` sets the screen to COMPLETE unconditionally. Setup exits although the stored device has been deleted.
- If the probe fails, the callback forces WELCOME with "Device not available" regardless of the current screen.
- The callback does not check that the screen is still CURRENT_DEVICE.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Verification Script Overwrites Service Logs

- **Commit:** 7f4b370. **Classification:** Confirmed. **Severity:** Medium.
- **Location:** `bin/gtach-verify-36b6ea95.sh:199`, `:210`, `:273-275`; `src/gtach/main.py:83`, `:118`, `:357`.

```bash
OUT=$(timeout 60 "$GTACH" --validate-config 2>&1); RC=$?
...
MS=$(grep -cE "$MOCK_RE" "$APP/start.log" 2>/dev/null)
```

```python
_start_handler = logging.FileHandler(_START_LOG, mode="w", encoding="utf-8")
...
_debug_handler.doRollover()
```

- The script header states it is read-only and makes no edits to `/opt/gtach`.
- `main()` calls `setup_logging()` before handling `--validate-config`. Each `--validate-config` run therefore truncates `/opt/gtach/start.log` and, when `debug.log` is non-empty, rotates the running service's `debug.log`.
- Check C7c then reads `start.log` as the service's startup record. It contains only the `--validate-config` run, so the `start.log` half of C7c cannot detect a mock fallback.

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Discovery Chunk Timeout Shorter Than Scan Timeout

- **Commit:** 69eb605. **Classification:** Confirmed (mismatch); effect Speculative. **Severity:** Medium.
- **Location:** `src/gtach/comm/pairing.py:157`, `:172-178`, `:69`; `src/gtach/comm/system_bluetooth.py:152-157`.

```python
chunk_duration = 4
...
nearby_devices = future.result(timeout=chunk_duration + 5)
```

```python
["hcitool", "scan", "--flush", "--length", str(duration)],
...
timeout=duration * 2 + 5,
```

- Each chunk waits at most 9 s; the fallback `hcitool` scan may run 13 s. On `concurrent.futures.TimeoutError` the loop proceeds while the worker is still scanning.
- With `max_workers=2`, two inquiries can overlap and later chunks queue behind them. Total discovery time is not bounded by the requested timeout.

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Preflight Restore Path Drops Rollback Protection

- **Commit:** f9273e0. **Classification:** Confirmed. **Severity:** Low.
- **Location:** `bin/gtach-preflight.sh:23-29`, `:72-74`.

```bash
log "ERROR: install failed — restoring previous"
[ -f "$PREVIOUS" ] && install_and_check "$PREVIOUS" && cp -f "$PREVIOUS" "$INSTALLED"
rm -f "$PROBATION"
```

- `install_and_check` installs the wheel before running `pip check`. If `pip check` fails and no `previous.whl` exists, the rejected wheel stays installed and the probation marker is removed, so it runs without rollback protection.
- `pip check` evaluates the whole virtual environment. A pre-existing unrelated conflict causes every update and the restore itself to report failure.

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Stop Timeout Not Honoured for obd_protocol

- **Commit:** f5d58f5. **Classification:** Confirmed. **Severity:** Low.
- **Location:** `src/gtach/core/thread.py:183-199`; `src/gtach/comm/obd.py:86-88`; `src/gtach/app.py:468-474`.

```python
stop_func()
...
thread_info.thread.join(timeout=timeout)
```

```python
if self.obd_thread.is_alive():
    self.obd_thread.join(timeout=5.0)
```

- `stop_thread` calls `stop_func` before its own bounded join. For `obd_protocol` the stop function joins for up to 5 s, so `_re_enter_setup`'s `timeout=2.0`, chosen because it runs on a UI callback, can block for about 7 s. The comment at `app.py:470-471` does not hold.
- The transport is disconnected first, so the OBD thread normally exits quickly; 7 s remains below the 15 s watchdog threshold.

[Return to Table of Contents](<#table of contents>)

---

## 9.0 DeviceStore Memory and Disk Diverge on Save Failure

- **Commit:** 3747d2f. **Classification:** Confirmed. **Severity:** Low.
- **Location:** `src/gtach/comm/device_store.py:225-231`, `:307-310`, `:317-320`.

```python
del self.config["paired_devices"]["primary"]
self._save_config()
self.logger.info(f"Removed primary device: {mac_address}")
return True
```

- `_remove_device_locked` ignores the result of `_save_config()` and returns True on a failed write.
- `_save_device_locked` mutates the in-memory config before saving; on failure it returns False, yet `get_primary_device()` reports the device until restart.

[Return to Table of Contents](<#table of contents>)

---

## 10.0 ConfigStore Concurrent Saves Share One Temp Path

- **Commit:** f5ab73a. **Classification:** Confirmed (reproduced in isolation); impact Speculative. **Severity:** Low.
- **Location:** `src/gtach/utils/config.py:341-351`.

```python
with self._lock:
    data = dict(self._unknown)
data.update(asdict(config))
tmp_path = self.path.with_name(f".{self.path.name}.{os.getpid()}.tmp")
```

- The lock covers only the copy of `_unknown`. Concurrent saves in one process write and rename the same temp file. A reproduction with 4 threads × 200 saves produced 298 `FileNotFoundError` failures.
- The only current caller is the palette toggle, so concurrent saves are unlikely.

[Return to Table of Contents](<#table of contents>)

---

## 11.0 ConfigStore Load Accepts Values Validate Rejects

- **Commit:** f5ab73a. **Classification:** Confirmed. **Severity:** Low.
- **Location:** `src/gtach/utils/config.py:303`; `:386-395`.

```python
values[key] = kind(data[key])
```

- Plain type coercion lets `load()` accept values `validate()` rejects: `palette:` (null) becomes `'None'`, `touch_long_press: true` becomes `1.0`, `fps_limit: 30.9` becomes `30`. The boolean and float cases are applied without warning.

[Return to Table of Contents](<#table of contents>)

---

## 12.0 Late OBD Reply Accepted Once

- **Commit:** f227686. **Classification:** Speculative. **Severity:** Low.
- **Location:** `src/gtach/comm/transport.py:523`, `:557`, `:562`.

```python
stale = self._discard_input(handle)
...
if b">" in buf: break
...
prompt = buf.find(b">")
```

- The discard removes only bytes already buffered when the command is sent. A late reply arriving after the discard but before the new reply is returned as the new command's reply; the real reply is discarded at the next command.
- The desync no longer cascades. A stale reply for a different PID is rejected by the PID check at `obd.py:211`; a stale `010C` reply is accepted as a current RPM sample.
- `tests/test_response_alignment.py` covers only pre-buffered stale bytes.

[Return to Table of Contents](<#table of contents>)

---

## 13.0 Link-Loss Tests Pass Without Exercising Link Loss

- **Commit:** 34c1ffd. **Classification:** Confirmed. **Severity:** Low.
- **Location:** `tests/test_lifecycle_sim.py:125-133`, `:144-151`, `:241-252`, `:274`.

```python
def test_samples_flow_after_drop_link(self, harness):
    ...
    harness.transport.drop_link()
    assert _wait_until(harness.transport.is_connected, SAMPLE_WAIT_S)
```

- The strict xfail in the same file records that `drop_link()` never makes `SimTransport.is_connected()` false. `test_samples_flow_after_drop_link` therefore passes immediately, and `test_stop_while_reconnecting` never stops a reconnecting transport. Both pass without testing the scenario they name.
- `assert proc.wait(timeout=10.0) is not None` is always true when it returns; the exit status is not checked.

[Return to Table of Contents](<#table of contents>)

---

## 14.0 Verification Script Loops on Trailing --since

- **Commit:** 7f4b370. **Classification:** Confirmed. **Severity:** Low.
- **Location:** `bin/gtach-verify-36b6ea95.sh:41`.

```bash
--since) SINCE="${2:-boot}"; shift 2 ;;
```

- When `--since` is the last argument, `shift 2` fails without shifting, and the `while [ $# -gt 0 ]` loop never terminates.

[Return to Table of Contents](<#table of contents>)

---

## 15.0 Gauge Range Cap Below Permitted Redline

- **Commit:** 5ea2cfd. **Classification:** Confirmed. **Severity:** Low.
- **Location:** `src/gtach/display/manager.py:1073-1085`, `:1274`; `src/gtach/assets/engine_profiles.yaml:18`.

```python
return min(9000, max(7000, math.ceil((redline + 500) / 1000) * 1000))
```

- The docstring states the configured redline is always on the dial; the profile constraints permit `redline_rpm` up to 15000. A redline above 9000 is off the dial and its band mark is skipped. Current profiles (6000–7500) are unaffected.

[Return to Table of Contents](<#table of contents>)

---

## 16.0 Observations

- `src/gtach/display/input/touch_coordinator.py:317-370` and `:396-398` still invoke callbacks under `self._lock`. Per `manager.py:252-260` these paths are unused, so this is not a live defect.
- `src/gtach/core/watchdog.py:287` logs "initiating emergency" at ERROR every check cycle for a stalled non-critical thread, although the recovery branch was removed in f5d58f5.
- `src/gtach/utils/stack_dump.py` calls `threading.enumerate()` from the SIGUSR1 handler; whether this can self-deadlock depends on the Python version on the device and was not confirmed.
- The `DisplayConfig.gesture_*` fields and a comment at `comm/pairing.py:132` refer to code removed in f789966.

[Return to Table of Contents](<#table of contents>)

---

## 17.0 Changes Reviewed Without Finding

- **29bdebe:** heartbeats, watchdog comparisons and the shutdown budget use `time.monotonic()` consistently; no mixing with `time.time()`.
- **5f3c50b:** always-on `error.log` handler is installed once, degrades to stderr when unopenable; tests assert the intended thresholds.
- **f22640a, 523bb21 (other parts):** cache reads, touch dispatch, state notifications and async-operation callbacks now execute outside locks with correct snapshot semantics.
- **b814ed9:** after a failed pan the frame is rewritten to the displayed half; tests assert the correct seek sequence.
- **41dd663:** peer-close handling drops the link and permits reconnection; init backoff is interruptible; RPM decode checks mode and PID bytes.
- **3747d2f (other parts):** non-reentrant lock usage is deadlock-free; writes use temp file, fsync and `os.replace`.
- **f5ab73a, f789966:** no orphaned references at HEAD; `compileall` and import smoke test clean; no configuration migration is required because the old and new default paths coincide under `WorkingDirectory=/opt/gtach`.
- **f9273e0 (other parts):** `ProtectSystem=full` leaves `/opt/gtach` writable; no `PrivateDevices` or `RestrictAddressFamilies` restricts framebuffer or Bluetooth; `TimeoutStopSec=30` exceeds the 20 s exit backstop; deploy, pull_logs and release script corrections are sound.
- **69eb605, 2ade5a3 (other parts):** shutdown ordering, RFCOMM timeout placement, child-process reaping and exception renames are consistent.
- **f227686 (other parts), e970454:** bounded socket and serial discards; Python-level SIGUSR1 handler avoids logging locks and closes its file.
- **d44dca9:** semantically neutral (Section 2.0).

[Return to Table of Contents](<#table of contents>)

---

## 18.0 Recommendations

1. In `_on_probe_result`, act only if the screen is still CURRENT_DEVICE (Section 4.0).
2. In the verification script, read `start.log` before running `--validate-config`, or have `--validate-config` skip file logging (Section 5.0).
3. Set the chunk future timeout above the scan subprocess timeout, or reduce the subprocess timeout, and bound total discovery time (Section 6.0).
4. In preflight, uninstall or retain probation for a wheel that fails `pip check` when no previous wheel exists (Section 7.0).
5. Pass the caller's timeout through to `OBDProtocol.stop` (Section 8.0).
6. Apply in-memory DeviceStore changes only after a successful save, and propagate the remove result (Section 9.0).
7. Hold the ConfigStore lock for the whole save, or use a unique temp name (Section 10.0).
8. Reject non-matching types in `ConfigStore.load()` rather than coercing (Section 11.0).
9. Correct `SimTransport.drop_link()` so the link-loss tests exercise their scenarios, and assert the subprocess exit code (Section 13.0).
10. Guard `--since` against a missing argument (Section 14.0).
11. Sections 12.0 and 15.0 require no immediate change; document the limits.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-08 | Initial scheduled daily audit. |

Copyright (c) 2026 William Watson. MIT License.
