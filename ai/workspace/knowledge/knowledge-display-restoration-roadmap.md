Created: 2026 May 06

# Knowledge: Display Restoration Roadmap

---

## Table of Contents

- [1.0 Purpose](<#1.0 purpose>)
- [2.0 Status Summary](<#2.0 status summary>)
- [3.0 Completed Tasks](<#3.0 completed tasks>)
- [4.0 Open Tasks](<#4.0 open tasks>)
- [5.0 Known Failures and Learnings](<#5.0 known failures and learnings>)
- [6.0 Sequencing](<#6.0 sequencing>)
- [7.0 Verification](<#7.0 verification>)
- [Version History](<#version history>)

---

## 1.0 Purpose

Records confirmed UI/display changes, their implementation state, and lessons
learned from visual testing. Provides a sequenced path to a stable display state.

Source of truth for original confirmed changes: conversation `83922674` (2026-04-23).

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Status Summary

| File | Status |
|---|---|
| `src/gtach/display/typography.py` | ✅ Restored — Michroma path, FONT_RPM_LARGE=180, MAX_FONT_SIZE=180 |
| `src/gtach/display/manager.py` | ✅ Restored — circular border, RPM format, Y positions |
| `src/gtach/display/splash.py` | ✅ Restored — Michroma direct-load, layout positions, red border, no subtitle, no version |
| `pyproject.toml` | ✅ Font package-data added — Michroma in wheel (d7f2b4e6) |
| `src/gtach/display/manager.py` | ✅ Framebuffer clear on splash complete — present in source |
| `src/gtach/core/watchdog.py` | ✅ Self-join guard applied (e4a6c8f2) |
| `src/gtach/display/setup_models.py` | ✅ SetupAction.START_DISCOVERY and COMPLETE added |
| All macOS runtime code | ✅ Removed (f3a1c9e2) — Pi is sole runtime target |
| Pi — visual confirmation | ✅ Confirmed — 2026-05-07 gtach-debug_PI.log |
| `src/gtach/comm/sim_transport.py` | ✅ Created (c7e2f1a9) |
| `src/gtach/comm/sim_bluetooth.py` | ✅ Created (c7e2f1a9) |

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Completed Tasks

### 3.1 typography.py — Constants and Michroma Font ✅

`FONT_RPM_LARGE` and `MAX_FONT_SIZE` both set to 180. `FontManager.__init__` resolves
Michroma path at init; `get_font()` loads Michroma with pygame default fallback.

**Coupling rule:** `MAX_FONT_SIZE` must always equal `FONT_RPM_LARGE`.

### 3.2 manager.py — Circular Border and RPM Format ✅

`_draw_circular_border()` added. Digital mode renders RPM as `rpm/1000:.1f`
with label "RPM × 1000" at Y=390.

### 3.3 splash.py — Title, Font, Border, No Subtitle, No Version ✅

Michroma at 72px, red circular border, subtitle removed, version text removed.

### 3.4 pyproject.toml — Font Package Data ✅

`"gtach" = ["assets/fonts/*.ttf", "assets/fonts/*.otf"]` — Michroma in wheel.

### 3.5 manager.py — Framebuffer Clear on Splash Complete ✅

`clear_surface` + `swap_buffers` present in `_draw_splash_mode()` inside the
`is_complete()` branch. Fix was already in source; Pi needed redeploy only.

### 3.6 watchdog.py — Self-Join Guard ✅

`WatchdogMonitor.stop()` guards join:
`if threading.current_thread() is not self._thread and self._thread.is_alive()`.
Resolved crash on watchdog-initiated shutdown (e4a6c8f2).

### 3.7 setup_models.py — SetupAction Enum Additions ✅

`START_DISCOVERY` and `COMPLETE` added to `SetupAction`. Resolved
`AttributeError` on every WELCOME screen tap (Pi and Mac).

### 3.8 macOS Runtime Removal ✅

All Darwin/macOS runtime paths removed across 13 source files (f3a1c9e2).
`start-gtach-macos-tcp.sh` deleted. README updated.
Mac is build host only. Pi is sole runtime target.
Issues `c3e5a7b9` and related macOS tasks are superseded.

### 3.9 Display Loop — Non-Blocking Event Handling ✅

`pygame.event.get()` replaced with `pygame.event.pump()` + `pygame.event.poll()`
loop (subsequently `pump()` removed — it blocked on macOS). Final state: `poll()`
loop only. `pygame.time.Clock.tick()` replaced with `time.sleep()` for frame pacing.

### 3.10 Pi Visual Confirmation ✅

Confirmed 2026-05-07 via `gtach-debug_PI.log`:
- Splash completes after 4.00s, transitions to WELCOME
- Michroma font loaded without WARNING
- WELCOME cache hits at ~56 FPS, 16.6ms frame, 41.7MB mem
- Tap at (246, 361) → `START_DISCOVERY` → `WELCOME → DISCOVERY` — no errors
- Bluetooth discovery runs cleanly (0 devices found — ELM327 not present, expected)
- Cancel tap → `DISCOVERY → WELCOME` clean
- No splash ghost, no alternation, no crashes

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Open Tasks


[Return to Table of Contents](<#table of contents>)

---

## 5.0 Known Failures and Learnings

### 5.1 macOS Runtime — Unresolvable

macOS pygame (2.6.1 / SDL 2.28.4 / Apple Silicon) blocks on `SDL_PollEvent`
when a mouse button is held. No viable fix within the pygame/SDL2 stack.
All macOS runtime code removed. Mac is build host only.

### 5.2 Pi Splash/Welcome Alternation — Root Cause

Caused by framebuffer double-buffer not cleared at splash completion.
Fix present in source (`clear_surface` + `swap_buffers` in `is_complete()` branch).
Resolved by redeploy.

### 5.3 SetupAction.START_DISCOVERY — Missing Enum Value

Every WELCOME screen tap raised `AttributeError: START_DISCOVERY`.
Fixed by adding `START_DISCOVERY` and `COMPLETE` to `SetupAction` in
`setup_models.py`. Affected both Pi and Mac.

### 5.4 pygame.event.pump() Blocks on macOS

`pygame.event.pump()` calls into the Cocoa run loop and can stall for seconds
on SDL 2.28.4 / Apple Silicon. Removed from the display loop.
`pygame.event.poll()` alone is used — returns `NOEVENT` immediately when empty.

### 5.5 pygame.time.Clock.tick() Blocks on macOS

`Clock.tick()` uses `SDL_Delay` which yields to the OS scheduler.
On macOS with a pending Cocoa event this never returns.
Replaced with `time.sleep()` calculated from `time.monotonic()`.

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Sequencing

```
Step 1 — setup_original_backup.py import check    ✅ COMPLETE
Step 2 — Pi framebuffer clear (b2d4f6a8)          ✅ COMPLETE (fix in source)
Step 3 — macOS gesture queue (c3e5a7b9)           ✅ SUPERSEDED (macOS removed)
Step 4 — Watchdog self-join (e4a6c8f2)            ✅ COMPLETE
Step 5 — SetupAction enum additions               ✅ COMPLETE
Step 6 — macOS runtime removal (f3a1c9e2)         ✅ COMPLETE

Step 7 — Pi visual confirmation                   ✅ COMPLETE
         Confirmed 2026-05-07 via gtach-debug_PI.log.
         See §3.10.

Step 8 — Sim mode (c7e2f1a9)                      ✅ COMPLETE
         Confirmed 2026-05-07 via gtach-simbt.log.
         SimTransport cycling 010C RPM at ~9Hz after full setup wizard flow.
```

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Verification

### 7.1 Pi Visual Confirmation

```bash
./build.sh
scp dist/*.whl root@gtach.local:/tmp/
ssh root@gtach.local '/opt/gtach/install.sh'
ssh root@gtach.local 'gtach --debug 2>&1 | tee /opt/gtach/gtach-debug.log'
```

Expected in log:
- `Splash completed - entering setup mode`
- `FontManager Created and cached font size 20`
- `Using cached render for WELCOME` (repeating)
- Touch tap produces `Touch event at (x, y)` then screen transition to DISCOVERY

### 7.2 Source Integrity

```bash
grep -r Darwin src/gtach/ --include="*.py"   # expect no matches
grep START_DISCOVERY src/gtach/display/setup_models.py  # expect match
grep "current_thread" src/gtach/core/watchdog.py        # expect match
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-05-06 | Initial document |
| 0.2 | 2026-05-06 | Updated after second visual test |
| 0.3 | 2026-05-06 | Added e4a6c8f2 watchdog self-join task |
| 0.4 | 2026-05-06 | Log analysis; revised stale cache diagnosis; Pi alternation attributed to framebuffer |
| 0.5 | 2026-05-06 | b2d4f6a8 confirmed in source; Pi deploy only |
| 0.6 | 2026-05-07 | Major update: macOS removed; SetupAction enum fixed; watchdog guard applied; display loop fixed; all closed items marked complete; roadmap reduced to two remaining items |
| 0.7 | 2026-05-07 | Step 7 closed: Pi visual confirmation passed via gtach-debug_PI.log; sim mode now NEXT |
| 0.8 | 2026-05-07 | Step 8 closed: sim mode confirmed via gtach-simbt.log; all steps complete |}

---

Copyright (c) 2026 William Watson. MIT License.
