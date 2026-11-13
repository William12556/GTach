# GTach Release Notes — v1.0.0

Created: 2026 November 13

**Release Date**: not released; release candidate `1.0.0rc1` prepared 2026-11-13
**Status**: Release candidate
**Previous Release Notes**: v0.2.67 (2026-07-30)

## Table of Contents

- [1.0 Summary](#10-summary)
- [2.0 Operator-Visible Changes](#20-operator-visible-changes)
- [3.0 Changes by Area](#30-changes-by-area)
- [4.0 Not in This Release](#40-not-in-this-release)
- [5.0 Verification Status](#50-verification-status)
- [6.0 Upgrade Notes](#60-upgrade-notes)
- [7.0 Change Record](#70-change-record)
- [Version History](#version-history)

---

## 1.0 Summary

- These notes cover the changes since the v0.2.67 release notes: versions 0.3.x, 0.4.x, 0.5.0 and the release candidate `1.0.0rc1` (419 commits, 2026-07-30 to 2026-11-13).
- `pyproject.toml` carries `1.0.0rc1`. The owner sets `1.0.0` and tags after on-device acceptance (`proposal-f8d0064b`, decision D1). Until then nothing is tagged or published.
- The period covers the display rework (radial gauge as the only layout, palettes, framebuffer page flip), link supervision with named failure causes, the single configuration store, watchdog recovery by process restart, the on-device setup rework, and four audit and remediation series.
- This software is experimental. See `DISCLAIMER.md` and `LICENSE`.

[Return to Table of Contents](#table-of-contents)

---

## 2.0 Operator-Visible Changes

| Change | Effect |
|---|---|
| Radial gauge is the only layout | The RPM figure is in the gauge centre; the DIGITAL layout is removed. A stored `mode: DIGITAL` is read as `RADIAL` |
| Day and night palettes | A long press on the gauge toggles the palette; the choice is saved |
| OPTIONS by swipe | Swipe down opens OPTIONS, swipe up returns; swipe left or right pages the menu (Clear settings and Check for updates; Simulation mode and Debug) |
| Clear settings confirmation | Clearing the paired device needs a second tap |
| DISCONNECTED screen | Shows the cause of the failure (for example "adapter not reachable"), a reconnect indicator, and the buttons Setup and Reset (reboots the Pi) |
| Engine off | When the adapter answers and the vehicle does not, the gauge shows 0 RPM with the text "Engine off" instead of DISCONNECTED |
| Acknowledgement screen | The RPM threshold notice is shown until dismissed, and again after the thresholds or the engine profile change |
| Setup | Device list with a focused entry and signal bars; scan outcomes are shown; the adapter is verified after pairing, with a retry when the link is busy |
| Boot | A static boot splash is shown before the application starts; boot text is suppressed |
| Logs | `error.log` records WARNING and above at all times; `debug.log` is rotated at each start; `kill -USR1` writes a thread dump to `stacks.log` |

[Return to Table of Contents](#table-of-contents)

---

## 3.0 Changes by Area

### 3.1 Display

- Frames are presented by framebuffer page flip, with a vertical-blank wait as fallback; the buffer size is taken from the device and a mismatch is reported at ERROR.
- One surface is written directly to the framebuffer; `fps_limit` is 30.
- Button geometry has one owner; touch targets meet a 72 px minimum; touch regions are registered per view.
- Link loss is decided from the transport state and from sample age; recovery needs two samples within 2 s; samples are drained while DISCONNECTED is shown, so the gauge returns.
- Durations and cache ages use the monotonic clock; callbacks are invoked outside locks.
- Removed: the shift rim border, the DIGITAL layout, unused gesture code.

### 3.2 Communication

- The connection skeleton is in `OBDTransport`; RFCOMM, TCP and serial supply handle primitives only. Simulated transports `simtcp` and `simbt`.
- A dead link is detected after five consecutive command timeouts, and the transport reconnects for the life of the process.
- Connect failures are classified by errno into short causes; sustained failure with a controller present is reported as "bluetooth wedged - reset required". Refused and unreachable peers do not count towards that diagnosis.
- Late replies no longer shift the response alignment; a reply for another PID is rejected; a reply with an odd number of hexadecimal digits is dropped.
- The device store is shared, locked, written atomically and located under `GTACH_HOME`.
- A planned close during a command is no longer logged as an error.

### 3.3 Core and Application

- Heartbeats, watchdog intervals and waits use monotonic time and are not affected by a wall-clock step.
- A stalled or exited critical thread ends the process; systemd restarts it. No thread is restarted in process. A 20 s backstop bounds every exit.
- Shutdown runs in a fixed order with each step isolated.

### 3.4 Configuration and Utilities

- One flat `config.yaml` under `GTACH_HOME` (default `/opt/gtach`), owned by `ConfigStore`; unknown keys are kept on save. `gtach --validate-config` checks it.
- The version has one source, `pyproject.toml`.
- The update check orders pre-release versions below their final release (`1.0.0rc1` < `1.0.0`).
- mypy strict settings pass with the Python 3.9 target (mypy pinned to 1.20.x).

### 3.5 Packaging and Installation

- `install.sh` and `pi-install.sh` apply the boot configuration and install the vendored HyperPixel driver; the `.[pi]` extra carries `RPi.GPIO` and `hyperpixel2r`.
- `gtach.service` is hardened (`NoNewPrivileges`, `PrivateTmp`, `ProtectHome`, `ProtectSystem=full`) and limits restarts.
- `gtach-preflight.sh` installs a staged wheel, runs `pip check`, and rolls back an update that fails to start twice.
- `engine_profiles.yaml` and the font are packaged; `psutil` is a declared dependency; a `LICENSE` file is included.
- `release.sh` publishes a version that is not X.Y.Z as a pre-release.

[Return to Table of Contents](#table-of-contents)

---

## 4.0 Not in This Release

- Automatic recovery from a stuck Bluetooth controller. GTach reports the condition and offers Reset; it does not act on the host.
- Render caching and conditional rendering (not needed at the measured frame times).
- The in-car test (vehicle not yet prepared).
- The open rows of `ai/task.md`.

[Return to Table of Contents](#table-of-contents)

---

## 5.0 Verification Status

| Item | Status |
|---|---|
| `pytest tests/` | 818 passed (Python 3.13.18); 818 passed (Python 3.9.25) |
| `python -m mypy src/` (target 3.9) | No issues in 60 source files |
| `flake8`, `black` on `src/` | Clean |
| Build | sdist and wheel `1.0.0rc1` built; wheel installed in a clean environment; `gtach --version` and `gtach --validate-config` run |
| Release-readiness audit `audit-bce0d69a` | Closed; no open critical or high finding |
| Device sessions A and B, engine-off and `76ef5387` checks (2026-11-12) | Passed on version 0.5.0 |
| Release candidate on the device | **Not yet run.** Bench test with the ELM327 emulator by the owner before the tag |
| In-car test | **Not yet run.** Planned after 1.0 (decision D2) |

[Return to Table of Contents](#table-of-contents)

---

## 6.0 Upgrade Notes

- **Configuration:** `config.yaml` is a flat file under `/opt/gtach`. `ConfigStore` reads only the flat keys (`mode`, `palette`, `engine_profile`, `fps_limit`, `touch_long_press`, `rpm_warning`, `rpm_danger`); for a key that is absent the default applies, and other keys are kept unchanged on save. Paired devices are in `/opt/gtach/config/devices.yaml`.
- **Installation:** use the full deploy for the step to this release; it installs the service files, the preflight script and the driver files.
- **Rollback:** reinstall the previous wheel with `install.sh`.

```bash
# Full deploy
./bin/deploy.sh

# Later updates: stage for the OPTIONS update flow
./bin/deploy.sh --stage
```

[Return to Table of Contents](#table-of-contents)

---

## 7.0 Change Record

- Issue, change and prompt documents: `ai/workspace/{issues,change,prompt}/closed/`, one 8-hex UUID per set.
- Audits: `ai/workspace/audit/closed/` (`audit-36b6ea95`, `audit-71ab3751`, scheduled audits, `audit-bce0d69a`).
- Release run: `ai/workspace/report/report-f8d0064b-v1-release-run.md`.
- Commit range: `ed1dea1..HEAD` of the release commit.

[Return to Table of Contents](#table-of-contents)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-13 | Release notes for the release candidate 1.0.0rc1 (proposal-f8d0064b WP8). To be updated with the release date when 1.0.0 is tagged |

---

Copyright (c) 2026 William Watson. MIT License.
