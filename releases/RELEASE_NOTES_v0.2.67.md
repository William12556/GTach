Created: 2026 July 30

# GTach Release Notes — v0.2.67

**Release Date**: 2026-07-30
**Status**: Alpha
**Previous Release**: v0.2.64

---

## Table of Contents

[1.0 Summary](<#1.0 summary>)
[2.0 Operator-Visible Changes](<#2.0 operator-visible changes>)
[3.0 Corrections by Area](<#3.0 corrections by area>)
[4.0 Changed Meaning of Existing Telemetry](<#4.0 changed meaning of existing telemetry>)
[5.0 Not in This Release](<#5.0 not in this release>)
[6.0 Verification Status](<#6.0 verification status>)
[7.0 Observations Outstanding on Target](<#7.0 observations outstanding on target>)
[8.0 Upgrade Notes](<#8.0 upgrade notes>)
[9.0 Commit Manifest](<#9.0 commit manifest>)
[Version History](<#version history>)

---

## 1.0 Summary

Six corrections arising from the two static code reviews completed on
2026-07-30: `core-comm-utils-code-review.md` and
`display-ui-graphics-review.md`. This is the first release of the §7.0
remediation programme recorded in `ai/task.md`.

All six are defect corrections or measurement fixes. No new functionality
is added, and no interface used outside the package changes.

Four of the six are internal and have no visible effect. One changes what
the display shows. One changes what an existing log line means.

Version numbers 0.2.65 and 0.2.66 were consumed during build iteration
and were never released.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Operator-Visible Changes

All from `display/manager.py`.

| Change | Effect |
|---|---|
| Exponential smoothing on the displayed RPM, τ ≈ 150 ms | The numeral no longer alternates between adjacent values when the engine holds steady near a rounding boundary. Introduces approximately 150 ms of display lag on the numeral |
| Band transition hysteresis, ±75 RPM | The background no longer alternates between two band colours when the engine holds steady near a band threshold. Applies at all five boundaries |
| Torque-approach band text colour changed from black to white | The numeral is legible on the blue band. WCAG 2.1 contrast rises from 2.44:1 to 8.59:1 |
| Shift-cue flash phase derived from a frame counter rather than wall-clock time | The 2 Hz flash above `caution_start` now has equal on and off intervals. Previously the duty cycle was unstable because the phase was sampled at an irregular frame rate |

The smoothing applies to the displayed figure only. The raw RPM value is
unchanged in the OBD path, in `get_status()` and in all logging.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Corrections by Area

### 3.1 Display

**RPM signal conditioning** — `display/manager.py`
Addresses display review §4.2 (band colour thrash), §4.3 (displayed value
churn), §4.4 (unstable flash duty cycle) and §7.1 (blue band contrast
failure). Recommendations 1, 5 and 23. See §2.0 for the visible effects.

Governance: `issue-4c038bed` / `change-4c038bed` / `prompt-4c038bed`.

**Performance instrumentation** — `display/performance/monitor.py`,
`display/manager.py`
`record_frame_end` is now called before the frame-pacing sleep rather than
after it, so the recorded interval measures rendering rather than the loop
period. Frame identifiers changed from per-frame UUID allocations to a
monotonic integer. The periodic-logging decision moved inside the monitor,
removing a full metrics construction — and with it a `psutil` `/proc` read
— from every frame. Process memory is now sampled at 1 Hz rather than at
the frame rate. The stale-frame expiry scan is skipped in the steady
state.

Addresses display review §6.1 and §6.2, recommendations 15 to 18. See §4.0
for the consequence.

Governance: `issue-0b00759c` / `change-0b00759c` / `prompt-0b00759c`, with
`c5dedd71` correcting the resulting interface annotation drift in
`display/performance/interfaces.py`.

### 3.2 Core

**Watchdog lock discipline** — `core/watchdog.py`
`_attempt_soft_recovery` held `ThreadManager`'s state lock across a
one-second sleep while waiting to observe whether a thread's heartbeat
advanced. That lock is the one `update_heartbeat` must acquire, so the
check was structurally unable to observe what it was testing for, and it
stalled every other thread's registration and heartbeat for the duration.
The observation is now split across two short critical sections with the
sleep between them.

`_check_thread_health` traversed the thread table under the same lock and
dispatched recovery — including its sleeps — from inside that traversal. It
now collects the required actions under the lock and dispatches after
releasing it.

Addresses core review §3.3 and §4.1, recommendation #2. `core/thread.py`
is unmodified.

Governance: `issue-5a9dc15e` / `change-5a9dc15e` / `prompt-5a9dc15e`.

**Expected effect under fault:** soft recovery can now succeed where it
previously always escalated to a thread restart. A fall in hard-recovery
attempts is the intended outcome.

### 3.3 Utilities

**Hardware revision parsing and platform detection** —
`utils/platform.py`, `utils/dependencies.py`
`str.lstrip('1000')` was used to strip the overvoltage flag from the
Raspberry Pi revision code. `lstrip` removes every leading character in
the given set, not a literal prefix, so a base code beginning with `0` or
`1` was over-stripped — losing the highest-confidence detection method
entirely. The flag bits are now cleared numerically by masking the low 24
bits.

`DependencyValidator` re-implemented Raspberry Pi detection as a substring
test on `/proc/cpuinfo`, independently of the weighted multi-method
`PlatformDetector`. The two could disagree, so `--validate-dependencies`
could validate a different dependency set than the application's own
detection implied. It now calls `PlatformDetector`, retaining the inline
test only as an import fallback.

Addresses core review §3.2 and §4.4, recommendation #3.

Governance: `issue-11be4865` / `change-11be4865` / `prompt-11be4865`.

**Reader-writer lock notification** — `utils/config.py`
`RWLock._release_read` notified only `_write_ready`. A writer that had
passed the first stage of `_acquire_write` and was waiting in the second
stage on `_read_ready` was therefore never woken by a departing reader,
and with a single writer would wait indefinitely. The lock guards
`ConfigManager.load_config` and `save_config`, which run on every
application start, so this was an unbounded wait on the live configuration
path rather than in dead code. A departing final reader now signals both
conditions, and the reader-count decrement no longer holds
`_readers_lock` across a condition acquisition.

Addresses core review §3.1, recommendation #1 (correction branch).

Governance: `issue-1143427b` / `change-1143427b` / `prompt-1143427b`.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Changed Meaning of Existing Telemetry

**This affects how the periodic performance log line should be read.**

The line has the form:

```
Performance: N FPS, N.Nms frame, N.NMB mem
```

Before this release, `frame_time_ms` was recorded after the frame-pacing
sleep, so it measured the loop period and converged on the frame target —
approximately 16.7 ms at `fps_limit: 60` — regardless of actual rendering
cost. It is now recorded before the sleep and measures rendering only.

Two consequences:

1. **Figures recorded before and after this release are not comparable.**
   Do not chart across the changeover.
2. **The dropped-frame counter will rise.** The test
   `frame_time > frame_time_target * 1.5` now sees real render times and
   can fire on genuine overruns. This is the intended outcome, not a
   regression.

Reported FPS is derived from frame-history timestamps rather than from
frame time and remains a true rate.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Not in This Release

Sixteen further triples from the §7.0 remediation are outstanding. In
particular, none of the following is included:

- Framebuffer write-path efficiency, vsync and page flipping —
  display recommendations 2, 3, 4, 6, 7, 8, 21
- Static-layer and text caching, frame pacing — recommendations 9 to 14
- Touch-target geometry, radial centre readout, annular band indicator,
  night palette, update-view progress — recommendations 19, 20, 22, 24 to 29
- `ConfigManager` device-persistence retirement, `DeviceStore` robustness,
  transport consolidation, thread shutdown budgeting

The full plan is `ai/task.md` §7.0 and the release sequencing is §8.0.

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Verification Status

Stated plainly rather than implied.

| Item | Status |
|---|---|
| Compile checks on every modified file | Pass |
| Source-order and structural checks against each prompt's success criteria | Pass |
| `tests/utils/test_rwlock.py` — 11 unit tests for `RWLock` | Pass. Four cases confirmed to fail against the pre-fix source, so the suite discriminates |
| Automated tests for the other five corrections | **Not yet written.** T05 specifications exist in `ai/workspace/test/`; the pytest files are outstanding |
| Target-platform verification | **This release is the first on-target exercise of all six changes** |

The `tests/` suite was empty before this release. `test_rwlock.py` is the
first automated test in the project. Verification of the other five
corrections was by compile check, structural assertion and hand-executed
cases on the development platform, recorded in each change document's
`verification` block.

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Observations Outstanding on Target

Recorded in `ai/task.md` §7.5. One is now resolved.

**§7.5.1 framebuffer geometry — RESOLVED 2026-07-30.** Read on
`gtach.local`:

```
bits_per_pixel  32
stride          1920
geometry        480 480 480 480 32
LineLength      1920
Size            921600
YPanStep        1
```

The rendering engine assumes `width × height × 4` and a stride equal to
`width × 4`. Both hold exactly: 480 × 480 × 4 = 921,600 bytes, and
480 × 4 = 1920. **Display review §8.3 is therefore not an active fault on
this hardware.** `YPanStep: 1` confirms the driver supports
`FBIOPAN_DISPLAY`, so page flipping remains viable; `yres_virtual` is
currently 480 and would need doubling for a second buffer.

Still outstanding:

| Item | Observation |
|---|---|
| §7.5.2 | Characterise the flicker against display review §10.3, then run the simulation-mode sweep of §10.4 |
| §7.5.3 | Read `frame_time_ms` from the periodic log line and record it as the render-cost baseline |
| §7.5.5 | Reproduce the transport race — concurrent `disconnect()` and `send_command()` |
| §7.5.6 | Record the hardware revision string; retrospective confirmation for the `11be4865` correction |

**On flicker attribution.** Of the six changes in this release, only the
RPM signal conditioning alters what is drawn. If the flicker persists,
band thrash and value churn are excluded and display review §4.1 —
unsynchronised framebuffer writes producing a tear seam — becomes the
leading candidate. Simulation mode sweeps every band boundary once per
6.28 s and requires no code change; flicker in bursts synchronised with
those crossings would indicate band thrash, continuous flicker points at
tearing.

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Upgrade Notes

- No configuration change is required. No configuration file format
  changed.
- No data migration. `config/devices.yaml` is untouched.
- No new or changed dependency.
- Rollback is by reinstalling the previous wheel; no state is written that
  the earlier version cannot read.
- The smoothing time constant (150 ms) and band hysteresis margin
  (±75 RPM) are module constants in this release. Promoting them to
  `config.yaml` is deferred pending on-vehicle observation.

```bash
# Full deploy
./bin/deploy.sh

# Or stage for the in-app OPTIONS update flow
./bin/deploy.sh --stage
```

[Return to Table of Contents](<#table of contents>)

---

## 9.0 Commit Manifest

Application changes since `v0.2.64`:

| Commit | Triple | Subject |
|---|---|---|
| `7365aec` | `0b00759c` | perf(display): measure render time, not loop period; cut per-frame instrumentation |
| `ddbd6c5` | `c5dedd71` | fix(display): align PerformanceMonitorInterface frame-ID annotations with int |
| `91cbc72` | `4c038bed` | fix(display): condition the RPM signal on the display path |
| `6d3ce60` | `5a9dc15e` | fix(core): keep blocking calls out of ThreadManager's state lock |
| `33e7017` | `11be4865` | fix(utils): mask revision flag bits; give Pi detection one source |
| `33c751d` | `1143427b` | fix(utils): wake a stage-two writer when the last reader departs |

Files changed in `src/`:

```
src/gtach/core/watchdog.py                  114 +++++-------
src/gtach/display/manager.py                149 ++++++++++-------
src/gtach/display/performance/interfaces.py  24 ++-
src/gtach/display/performance/monitor.py    106 +++++++-----
src/gtach/utils/config.py                    27 ++-
src/gtach/utils/dependencies.py              35 ++--
src/gtach/utils/platform.py                  14 +-
7 files changed, 348 insertions(+), 121 deletions(-)
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-07-30 | Initial release notes for v0.2.67. |

---

Copyright (c) 2026 William Watson. MIT License.
