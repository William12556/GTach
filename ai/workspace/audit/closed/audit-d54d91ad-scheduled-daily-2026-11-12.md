Created: 2026 November 12
# GTach Scheduled Daily Audit — 2026-11-12 (audit-d54d91ad)

> **Status: Closed (2026-11-12).** F1: executable bit restored on both scripts. F2: check C4 counts "Vehicle not answering" instead of "No valid 0100". The observation on `adapter_reset_in_session` was resolved by change-34781bfe.

---

## Table of Contents

- [1.0 Purpose](<#1.0 purpose>)
- [2.0 Method](<#2.0 method>)
- [3.0 Activity Summary](<#3.0 activity summary>)
- [4.0 Finding F1: Executable Bit Removed from Two bin Scripts](<#4.0 finding f1: executable bit removed from two bin scripts>)
- [5.0 Finding F2: Verification Script Patterns No Longer Match the OBD Initialisation Log](<#5.0 finding f2: verification script patterns no longer match the obd initialisation log>)
- [6.0 Observations](<#6.0 observations>)
- [7.0 Changes Reviewed Without Finding](<#7.0 changes reviewed without finding>)
- [8.0 Recommendations](<#8.0 recommendations>)
- [Version History](<#version history>)

---

## 1.0 Purpose

This report records the scheduled review of commits on the default branch of William12556/GTach whose commit date falls between 2026-11-11 02:05 UTC and 2026-11-12 02:05 UTC (03:05 Europe/Berlin run start).

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Method

- The GitHub MCP route was used for commit listing, commit metadata, file statistics, tags, file contents at HEAD (121775e) and code search.
- `get_commit` returned file statistics but no patch text for any commit. The patches of the four code-bearing commits were therefore read in full with the local-clone fallback `git_show`: d9311c4, f89dc2f, 963fd0f and 2cffdae. The commit SHAs are identical to the remote, so the local patches are the remote patches.
- Files reviewed via fallback: `bin/gtach-preflight.sh`, `bin/gtach-verify-36b6ea95.sh`, `pyproject.toml`, and every `src/gtach/**/*.py` and `tests/*.py` file changed in f89dc2f, 963fd0f and 2cffdae.
- Context files read at HEAD with `get_file_contents`: `bin/gtach.service`, `bin/install.sh`, `bin/gtach-verify-36b6ea95.sh`, `src/gtach/app.py`, `src/gtach/comm/pairing.py`, `src/gtach/comm/models.py`, `src/gtach/comm/system_bluetooth.py`, `src/gtach/utils/home.py`, `src/gtach/display/setup_components/bluetooth/interface.py`.
- Removed symbols were checked for orphaned references with `search_code`: `YAML_AVAILABLE`, `TOUCH_HANDLER_AVAILABLE`, `GestureType`, `show_all_devices`, `log_platform_info`, `manual_entry`, `run_platform_test`, `check_gpio_availability`, `record_render_operation`, `register_slider_region`, `PlatformError`, `adapter_reset_in_session`. No orphaned reference was found.
- Documentation (`*.md`) was counted, not reviewed. `list_issues` and `list_pull_requests` were not called.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Activity Summary

| Metric | Value |
|---|---|
| Commits in window | 30 (29 non-merge, 1 merge) |
| File changes (non-merge, summed per commit) | 117 |
| Insertions (non-merge) | 7578 |
| Deletions (non-merge) | 3405 |
| New tags | None |

| SHA | Author | Date (UTC) | Subject |
|---|---|---|---|
| 121775e | William12556 | 2026-11-11 16:17 | docs: record run 3 implemented; device session A procedure (71ab3751) |
| 2cffdae | Claude | 2026-11-11 15:01 | fix: lifecycle, logging and utility corrections (change-042dd7ff) |
| f2d4e52 | William12556 | 2026-11-11 14:10 | docs: record run 2 implemented (b4f9607a) |
| 2035679 | William12556 | 2026-11-11 14:09 | Merge run 2 (change-b4f9607a) (merge; excluded from totals) |
| 963fd0f | Claude | 2026-11-11 14:02 | fix: communication layer corrections (change-b4f9607a) |
| 3fdc159 | William12556 | 2026-11-11 13:59 | docs: record run 1 implemented and the D3 deviation (cfa4e617) |
| f89dc2f | Claude | 2026-11-11 11:44 | refactor: remove unused code and configuration keys (change-cfa4e617) |
| 6cc83f4 | William12556 | 2026-11-11 10:55 | docs: mark five remediation changes approved (71ab3751) |
| fb7d111 … bd4238d | William12556 | 2026-11-11 10:37–10:55 | 15 "approve:" commits, one line each in `ai/approvals.yaml` |
| 1483946 | William12556 | 2026-11-11 10:19 | docs: five remediation T-Doc sets, setup design v2.0 and design review (71ab3751) |
| d9311c4 | William12556 | 2026-11-11 10:19 | fix(bin): preflight rollback state and verify --since argument loop |
| dcb6344 | William12556 | 2026-11-11 06:17 | chore: untrack ai-local/ (now gitignored) |
| 4f92682 | William12556 | 2026-11-11 06:03 | Update scheduled-audit-log.txt |
| 9747223 | William12556 | 2026-11-11 06:01 | docs: add remediation proposal for audit-71ab3751 (v1.1) |
| cc67d07 | William12556 | 2026-11-11 06:01 | chore: track ai/workspace/proposal in git |
| c461fb9 | William12556 | 2026-11-11 05:30 | docs: add session report for audit-71ab3751 |

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Finding F1: Executable Bit Removed from Two bin Scripts

- Classification: Confirmed. Severity: Low.
- Commit: d9311c4. Files: `bin/gtach-preflight.sh`, `bin/gtach-verify-36b6ea95.sh`.
- Evidence from the patch:

```
diff --git a/bin/gtach-preflight.sh b/bin/gtach-preflight.sh
old mode 100755
new mode 100644
...
diff --git a/bin/gtach-verify-36b6ea95.sh b/bin/gtach-verify-36b6ea95.sh
old mode 100755
new mode 100644
```

- The commit message describes content fixes only (G02, G03); the mode change is unintended.
- Impact is limited on the documented paths. `bin/install.sh` installs the preflight with `install -m 0755`, and the verify script is documented as `bash /tmp/gtach-verify-36b6ea95.sh`. Any direct execution from a checkout (`./bin/gtach-preflight.sh`) now fails with "Permission denied".
- `bin/gtach.service` runs `ExecStartPre=-/opt/gtach/gtach-preflight.sh`. The `-` prefix ignores a failure, so a non-executable preflight would be skipped silently, disabling update installation and rollback. That outcome requires a deployment path that copies the file without setting the mode; none was identified.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Finding F2: Verification Script Patterns No Longer Match the OBD Initialisation Log

- Classification: Confirmed. Severity: Low.
- Commit: 963fd0f (`src/gtach/comm/obd.py`). Affected tool: `bin/gtach-verify-36b6ea95.sh` check C4.
- Evidence from the patch: a missing 4100 reply no longer raises, so the ERROR record "Initialization failed: No valid 0100 response …" is no longer written for this condition. It is replaced by a WARNING with different text:

```
-                raise Exception(f"No valid 0100 response: {response!r}")
+                self._report_no_vehicle(response)
+                return False
...
+        self.logger.warning(
+            f"Vehicle not answering: no valid 0100 response ({response!r})"
+        )
```

- The verify script at HEAD counts these case-sensitive patterns:

```
for p in "Initialization failed" "No valid 0100" "adapter closed the connection" \
```

- "No valid 0100" no longer matches ("no valid 0100" is lower case), and "Initialization failed" is no longer logged for a silent vehicle. Check C4 reports 0 for both on a device where the vehicle is not answering, which misrepresents the evidence the operator judges manually.

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Observations

- `app.py` (2cffdae) derives `adapter_pre_initialised` from `getattr(manager, "adapter_reset_in_session", False)`. `search_code` finds this attribute only in `app.py`, tests and the change-34781bfe documents, not in `SetupDisplayManager`. Until run 4 (change-34781bfe) defines it, ATZ initialisation always runs after setup. This is conservative behaviour and not a defect. Classification: Speculative, because it rests on `search_code`.
- `set_runtime_log_level` (2cffdae) sets the root logger to WARNING once startup completes. With debug off, INFO records after startup (setup-mode pairing, link events) reach no handler. This matches the stated design; it reduces what `error.log` and the verify script can observe without Debug enabled.
- `get_commit` did not return patch text for any commit in this window; every code patch was read through the local fallback.

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Changes Reviewed Without Finding

- d9311c4 `gtach-preflight.sh`: `restore_previous()` updates `installed.whl` after a successful reinstall, independent of `pip check`, and logs the no-previous-wheel case. The `--since` loop fix (`shift; [ $# -gt 0 ] && shift`) terminates on a trailing option.
- 963fd0f `transport.py`: a handle opened after `disconnect()` is closed outside the lock and not published. Refused connects no longer count towards the wedge diagnosis. Send-time I/O errors record a cause.
- 963fd0f `device_store.py`: save and remove restore a deep copy of `config` on failure. `set_device_store_path()` resets the shared instance under its lock.
- 963fd0f `obd.py`: the registered stop function signals without joining. `stop(timeout)` keeps the join for direct callers. The missing-4100 WARNING is rate-limited, with an INFO record on recovery.
- 963fd0f `pairing.py`: the chunk wait covers the hcitool limit (`d * 2 + 5`). Cancellation is checked after each chunk and on both sides of the RFCOMM connect; the socket is closed in `finally`. The fallback list is returned only when no ELM327-like device was found.
- 963fd0f `system_bluetooth.py`, `serial_transport.py`, `sim_transport.py`, `models.py`: shared manager with double-checked creation; `OSError` treated as link loss; `SimTransport.connect` no longer clears `_shutdown`; `from_dict` parses `last_connected`. The corrected sine expectation (`41 0C 65 90` at t = 15 s) is arithmetically correct.
- 2cffdae `app.py`: `run()` returns 1 on runtime error and watchdog exit, and 0 on signal or requested restart. Shutdown steps are isolated per component. `_obd_started` is cleared when `_start_obd` raises. The pairing factory is retained for re-entry.
- 2cffdae `main.py`: log paths are derived from `gtach_home()` before handlers are opened. Validation commands run before `setup_logging` and open no log file.
- 2cffdae `config.py`: `_typed_value` gives load and validate one type rule. `save()` is serialised by `_save_lock`. Engine profiles resolve through `files("gtach")` with a path fallback.
- 2cffdae `watchdog.py`, `pi_reset.py`, `terminal.py`, `dependencies.py`, `ack_state.py`: rate-limited non-critical warning, reset on recovery; negative reboot return codes treated as reboot in progress; missing or closed stdin tolerated; `find_spec` errors caught; non-mapping state rejected.
- f89dc2f: the removal is subtractive. `PerformanceMetrics()` is still constructible without `dirty_regions_count`. `start_discovery` keeps a `show_all_devices=False` default. No orphaned reference to a removed symbol was found.
- dcb6344 untracks `ai-local/` (1357 deletions, including `ai-local/src/overwatch.py`); the local copy is kept by design.

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Recommendations

1. Restore the executable bit with `git update-index --chmod=+x bin/gtach-preflight.sh bin/gtach-verify-36b6ea95.sh` and commit. Check that the editing tool used for d9311c4 does not drop file modes.
2. Update check C4 in `bin/gtach-verify-36b6ea95.sh` to count "Vehicle not answering" (or use `grep -ciE "no valid 0100"`), and drop or relabel the "Initialization failed" counter for this condition.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-12 | Initial scheduled daily audit. |
| 1.1 | 2026-11-12 | F1 and F2 fixed by direct `bin/` edits; closed and moved to audit/closed/. |

---

Copyright (c) 2026 William Watson. MIT License.
