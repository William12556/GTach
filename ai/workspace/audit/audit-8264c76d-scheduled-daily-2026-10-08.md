Created: 2026 October 8
# GTach Scheduled Daily Audit — 2026-10-08 (audit-8264c76d)

---

## Table of Contents

- [1.0 Purpose](<#1.0 purpose>)
- [2.0 Method](<#2.0 method>)
- [3.0 Activity Summary](<#3.0 activity summary>)
- [4.0 Finding F1: Verify Script Hangs on Bare --since](<#4.0 finding f1: verify script hangs on bare --since>)
- [5.0 Finding F2: Region-Registration Test Cannot Fail](<#5.0 finding f2: region-registration test cannot fail>)
- [6.0 Finding F3: Preflight Rollback State After pip check Failure](<#6.0 finding f3: preflight rollback state after pip check failure>)
- [7.0 Observations](<#7.0 observations>)
- [8.0 Changes Reviewed Without Finding](<#8.0 changes reviewed without finding>)
- [9.0 Recommendations](<#9.0 recommendations>)
- [Version History](<#version history>)

---

## 1.0 Purpose

This audit reviews the code-bearing changes committed to William12556/GTach in the 24 hours before 2026-10-08 07:08 Europe/Berlin. Its purpose is to identify defects that require correction.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Method

- The repository was cloned anonymously with `--filter=blob:none`. The diff range was `1865cce^..41ca530`.
- Full diffs of `*.py`, `*.sh`, `*.service`, `*.toml` and `*.yaml` were read commit by commit. Documentation changes were counted but not reviewed.
- Removed symbols from f5ab73a and f789966 were searched for at HEAD to detect orphaned references.
- Commit d44dca9, labelled as formatting only, was compared by AST against its parent.
- Each finding was checked against HEAD. F1 was reproduced in isolation.
- Tests were not executed because pygame and pytest are absent from the container. Issues and pull requests were not retrieved; this run used git only.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Activity Summary

| Repository | Commits | Files | Insertions | Deletions | New tags |
|---|---|---|---|---|---|
| GTach | 43 | 198 | 27346 | 16425 | None (latest: v0.4.0, 2026-08-07) |

File breakdown by extension:
- 93 `.py`
- 84 `.md`
- 8 `.sh`
- 7 `.txt`
- 3 `.yaml`
- 1 `.toml`
- 1 `.service`
- 1 `.flake8`

The `.md` changes account for 14510 insertions and 377 deletions. Most commits implement the remediation phases of audit-36b6ea95.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Finding F1: Verify Script Hangs on Bare --since

- **Classification:** Confirmed.
- **Severity:** Low.
- **Commit:** 7f4b370.
- **Location:** `bin/gtach-verify-36b6ea95.sh:41`.

```bash
set -u
...
while [ $# -gt 0 ]; do
    case "$1" in
        --since) SINCE="${2:-boot}"; shift 2 ;;
```

When `--since` is the last argument, `$#` is 1. Bash then treats `shift 2` as an error and shifts nothing. The script does not use `set -e`, so `$#` stays at 1 and the loop never terminates. The script hangs before it writes its report. An isolated reproduction was terminated by `timeout` with exit status 124.

The `${2:-boot}` default shows that the author intended to tolerate a missing value. The `shift` count does not match that intent.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Finding F2: Region-Registration Test Cannot Fail

- **Classification:** Confirmed.
- **Severity:** Low.
- **Commit:** 523bb21.
- **Location:** `tests/test_callbacks_outside_locks.py:223`, `test_callback_may_register_regions`.

```python
def callback(pos):
    coordinator.register_button_region("c", pygame.Rect(200, 200, 10, 10))
...
assert not worker.is_alive()
```

The callback re-enters the coordinator on the thread that dispatched it. The coordinator lock is reentrant:

```python
self._lock = threading.RLock()   # touch_coordinator.py:36
```

A thread that re-acquires an RLock it already holds never blocks, so this test also passes against the code from before the fix. The fix itself remains covered by `test_callback_runs_with_coordinator_lock_free`, which probes the lock from a second thread. This test therefore adds no regression protection.

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Finding F3: Preflight Rollback State After pip check Failure

- **Classification:** Speculative.
- **Severity:** Low.
- **Commit:** f9273e0.
- **Location:** `bin/gtach-preflight.sh:21-31`, `:47-52`, `:66`.

```bash
install_and_check() {
    install_wheel "$1" || return 1
    ...
    if ! out="$("$VENV/bin/pip" check 2>&1)"; then
        ...
        return 1
...
if [ -f "$PREVIOUS" ] && install_and_check "$PREVIOUS"; then
    cp -f "$PREVIOUS" "$INSTALLED"
else
    log "ERROR: rollback unavailable or failed"
```

`install_and_check` force-reinstalls the wheel before it runs `pip check`. Suppose the venv has a dependency inconsistency unrelated to the previous wheel. In that case:
- The previous wheel is installed.
- The script logs that the rollback failed.
- `installed.whl` is left naming the rejected wheel.

On the next update, line 66 (`cp -f "$INSTALLED" "$PREVIOUS"`) would then save the rejected wheel as the rollback target. This requires an environment that is already inconsistent. The normal path behaves correctly.

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Observations

- **`_probe_in_flight` in setup (523bb21).** `src/gtach/display/setup.py` sets `_probe_in_flight` and clears it only in `_on_probe_result`. A cancelled asynchronous operation never receives its callback, which would leave the Continue button inert. This path cannot be reached at HEAD, because the probe is not registered in `_active_operations` and therefore cannot be cancelled. Any future change that makes probes cancellable would expose it.
- **Setup re-entry stop timeout (f5d58f5).** The comment in `_re_enter_setup` states a 2.0 s stop. However, `stop_thread('obd_protocol', 2.0)` calls `OBDProtocol.stop`, which itself joins for up to 5.0 s. The display thread can therefore block for about 9 s in the worst case. This behaviour existed before the commit and remains below the 15 s watchdog warning. The comment is inaccurate.
- **Formatting commit d44dca9.** The AST comparison shows no code changes beyond import reordering. The commit also contains hand-reworded docstrings in `splash.py`, `bluetooth/interface.py`, `pairing.py`, `transport.py` and one test. This contradicts the "style only" label but has no behavioural effect.
- **Unreferenced default config.** `src/gtach/utils/default-config.txt` still uses the old nested configuration schema and is not referenced anywhere. It was already unreferenced before this window.

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Changes Reviewed Without Finding

- **29bdebe, 2ade5a3: monotonic clock.** Heartbeats, the watchdog, the shutdown budget, touch, async operations and splash all use `time.monotonic()`. No mixed comparisons with `time.time()` remain.
- **5f3c50b: error log.** An always-on rotating `error.log` was added at WARNING level, and `exc_info` was added to broad exception handlers.
- **f22640a, 523bb21: callbacks outside locks.** Callbacks in the setup coordinator, touch coordinator, touch interface and async manager are now invoked after their locks are released. The Continue probe moved to an asynchronous worker.
- **f5d58f5: thread restart removed.** In-process thread restart was removed with no orphaned references. `stop_thread` marks the thread STOPPING before stopping it. The OBD loop observes `shutdown_event` and bounds the gaps between heartbeats.
- **b814ed9: framebuffer pan failure.** After a failed pan, the frame is written to the half that is actually displayed.
- **41dd663: reconnect path.** The 0100 reply is now validated by requiring `4100`. Initialisation retries are interruptible by shutdown. The RPM reply header is checked. EOF now drops the link, and an empty serial read counts as a timeout.
- **5ea2cfd: setup and gauge.**
  - `stop_setup` no longer tries to join its own thread.
  - Gauge full scale derives from the redline, consistently across clamp, ticks and bands.
  - Device presence is cached.
  - Error messages persist until the next tap.
- **f5ab73a: single ConfigStore.** One `ConfigStore` is used under `GTACH_HOME`. Writes are atomic with fsync. No orphaned references remain to `ConfigManager`, `OBDII_HOME` or the other removed symbols.
- **3747d2f: shared DeviceStore.** A process-wide `DeviceStore` is shared under a leaf lock. All call sites were migrated.
- **f9273e0: packaging.**
  - The service hardening (`ProtectSystem=full`, `ProtectHome`, `PrivateTmp`, `NoNewPrivileges`, no `PrivateDevices`) is compatible with the app's writes under `/opt/gtach` and its device access.
  - The version is read from a single source, package metadata.
  - Corrections to `deploy.sh`, `install.sh`, `release.sh` and `pull_logs.sh` were reviewed.
- **69eb605: pairing, setup state, shutdown.**
  - Pairing duration is bounded, and setup state is owned by the coordinator, with copies returned.
  - The forced-exit timer is armed on every exit path.
  - The async manager and touch handler are stopped at shutdown.
- **f789966: dead code removal.** About 8700 lines of dead and backup code were removed. An import and undefined-name check across `src/`, `tests/` and `bin/` found no broken references.
- **f227686, e970454: response alignment and stack dumps.**
  - Stale input is discarded before each command, bounded at 64 non-blocking reads.
  - Replies are truncated at the first prompt.
  - The SIGUSR1 stack-dump handler is installed on the main thread and does not raise. `faulthandler` is not registered on SIGUSR1, so the two do not conflict.
- **10954e9, 34c1ffd: tests.** Test isolation of the home directory, and the SimTransport lifecycle test.

[Return to Table of Contents](<#table of contents>)

---

## 9.0 Recommendations

1. **F1.** In `bin/gtach-verify-36b6ea95.sh`, change the `--since` branch to `SINCE="${2:-boot}"; shift; [ $# -gt 0 ] && shift`, or reject a missing value with exit status 2.
2. **F2.** Either remove `test_callback_may_register_regions`, or have the callback re-enter the coordinator from a second thread so that the test fails when the lock is held.
3. **F3.** Optional. In the rollback branch, set `cp -f "$PREVIOUS" "$INSTALLED"` according to whether `install_wheel` succeeded, independently of the `pip check` result.
4. **Observation on f5d58f5.** Correct the comment in `_re_enter_setup` so that it states the effective stop duration.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-08 | Initial scheduled daily audit. |

Copyright (c) 2026 William Watson. MIT License.
