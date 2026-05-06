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
| `src/gtach/display/splash.py` | ✅ Restored — Michroma direct-load, layout positions, red border, no subtitle |
| `src/gtach/display/splash.py` | ✅ Version text removed from automotive mode (f1a3c5e7) |
| `pyproject.toml` | ✅ Font package-data added — Michroma now included in wheel (d7f2b4e6) |
| `src/gtach/display/manager.py` | ❌ Framebuffer clear on splash complete NOT applied (b2d4f6a8) |
| `src/gtach/display/manager.py` | ❌ macOS gesture queue / beach ball fix NOT applied (c3e5a7b9) |
| `src/gtach/app.py` | ❌ SIGINT pygame.QUIT injection NOT applied (c3e5a7b9) |
| `src/gtach/core/watchdog.py` | ❌ Self-join RuntimeError in stop() on Darwin (e4a6c8f2) |
| `src/gtach/display/setup.py` | ❌ WELCOME render cache stale layout — new defect discovered |
| `src/gtach/comm/sim_transport.py` | ❌ Not yet created (enhancement c7e2f1a9) |
| `src/gtach/comm/sim_bluetooth.py` | ❌ Not yet created (enhancement c7e2f1a9) |
| `src/gtach/comm/transport.py` | ❌ Not yet modified (enhancement c7e2f1a9) |
| `src/gtach/main.py` | ❌ Not yet modified (enhancement c7e2f1a9) |
| `src/gtach/display/setup_components/bluetooth/interface.py` | ❌ Not yet modified (enhancement c7e2f1a9) |
| `src/gtach/app.py` | ❌ Not yet modified (enhancement c7e2f1a9) |
| `src/gtach/display/setup.py` | ❌ Not yet modified (enhancement c7e2f1a9) |

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Completed Tasks

### 3.1 typography.py — Constants and Michroma Font ✅

`FONT_RPM_LARGE` and `MAX_FONT_SIZE` both set to 180. `FontManager.__init__` resolves
Michroma path at init; `get_font()` loads Michroma with pygame default fallback.
Confirmed by source inspection and Pi log (no WARNING on second test run).

**Coupling rule:** `MAX_FONT_SIZE` must always equal `FONT_RPM_LARGE`. If only one
is changed, font rendering silently clips at the lower value.

### 3.2 manager.py — Circular Border and RPM Format ✅

`_draw_circular_border()` added. Called from all four display mode methods.
Digital mode renders RPM as `rpm/1000:.1f` with label "RPM × 1000" at Y=390.
Yellow rect border removed from `_draw_setup_mode_fallback`.

### 3.3 splash.py — Title, Font, Border, No Subtitle, No Version ✅

Automotive mode: Michroma loaded directly at 72px (title) and 40px (version, method
retained for other modes). Layout: title at `center_y-115`, progress at `center_y+20`.
Red circular border. Subtitle call removed. Version text call removed (f1a3c5e7).

### 3.4 pyproject.toml — Font Package Data ✅

```toml
[tool.setuptools.package-data]
"gtach" = ["assets/fonts/*.ttf", "assets/fonts/*.otf"]
```

Pi log on second test shows no `FontManager WARNING Michroma font not found`.
Font is now included in wheel.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Open Tasks

### 4.1 Pi Welcome Screen — Framebuffer Clear on Splash Complete ❌

**Issue:** `issue-b2d4f6a8`  
**Change:** `change-b2d4f6a8`  
**Prompt:** `workspace/prompt/prompt-b2d4f6a8-pi-clear-framebuffer-on-splash.md`

**Not applied** — second Pi test still shows splash ghost. Claude Code did not
implement this change. Re-run prompt.

Fix location: `DisplayManager._draw_splash_mode()` in `src/gtach/display/manager.py`.  
Insert before `_splash_screen.reset()` call, inside `is_complete()` branch:
```python
self.rendering_engine.clear_surface(RenderTarget.BACK_BUFFER)
self.rendering_engine.swap_buffers()
```

### 4.2 Pi Welcome Screen — Stale Render Cache (Alternating Layout) ❌

**New defect discovered on second Pi test.** The WELCOME screen alternates between
old font sizes/positions and new ones. Root cause: `SetupDisplayManager._screen_render_cache`
persists a WELCOME surface that was built before the typography/font restoration was
deployed. On cache hit it blits the stale surface; on cache miss it re-renders with
current fonts. The alternation is the cache invalidation bouncing.

**Fix:** Invalidate `_screen_render_cache` on startup, or clear it when
`SetupDisplayManager` is first instantiated rather than preserving across sessions.
The cache is in-memory only (not persisted to disk), so this should not occur between
separate process invocations. The alternation may indicate the cache is being populated
from the old `setup_original_backup.py` render path vs the new `setup.py` path on
alternate render cycles.

**Investigation needed:** Check whether `setup_original_backup.py` is being imported
or used at runtime — it contains a separate `_render_welcome_screen` implementation
with the old font sizes. If both code paths are active, the cache will contain
surfaces from whichever rendered last.

**Prompt to create:** New issue + change + prompt for this defect.

### 4.3 macOS Beach Ball and Ctrl+C Deadlock ❌

**Issue:** `issue-c3e5a7b9`  
**Change:** `change-c3e5a7b9`  
**Prompt:** `workspace/prompt/prompt-c3e5a7b9-macos-gesture-queue-sigint-fix.md`

**Not applied** — second Mac test still shows beach ball and requires force quit.
WatchdogMonitor fires at ~16s timeout as before. Shutdown path still hits
`RuntimeError: cannot join current thread` from `watchdog.stop()` attempting to
join its own thread.

Two distinct problems confirmed:

1. **Beach ball**: gesture dispatch is synchronous on the Cocoa main thread.
2. **Cannot join current thread**: `GTachApplication.shutdown()` calls
   `self._watchdog.stop()` which calls `self._thread.join()`. When shutdown is
   triggered by the watchdog thread itself (via its own callback), this is a
   self-join. Fix must guard against this: `if threading.current_thread() is not self._thread: self._thread.join(...)`.

**Additional finding from log:** The watchdog also attempts a soft recovery at 31.7s
before the critical shutdown at 42.7s. The soft recovery calls `_trigger_display_refresh`
which may itself try to write to the display surface from the watchdog thread — a
thread-safety violation on macOS.

Re-run prompt for `c3e5a7b9`. Also file a separate trivial-exemption fix for the
self-join in `watchdog.py`.

### 4.4 Watchdog Self-Join on Darwin (e4a6c8f2) ❌

**Issue:** `issue-e4a6c8f2`  
**Trivial exemption applies** (§1.4.12) — single function, net delta ~3 lines, no interface change.

Fix location: `WatchdogMonitor.stop()` in `src/gtach/core/watchdog.py`.  
Guard the join call to prevent self-join when shutdown is triggered by the watchdog thread itself:
```python
if threading.current_thread() is not self._thread:
    self._thread.join(timeout=5.0)
    if self._thread.is_alive():
        self.logger.warning("Watchdog monitor thread did not stop cleanly")
```
The existing unconditional `self._thread.join(timeout=5.0)` and the `is_alive()` warning block
both need to move inside this guard.

### 4.5 Sim Mode (c7e2f1a9) ❌

Prompt `prompt-c7e2f1a9-sim-mode.md` complete and ready. No dependency on items
4.1–4.4. Can be implemented independently once the display issues are stable.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Known Failures and Learnings

### 5.1 Claude Code Partial Application (2026-05-06, second run)

The combined implement command applied only the two simplest changes:
- `f1a3c5e7` (splash version text — 1-line deletion) ✅
- `d7f2b4e6` (pyproject.toml package-data — 2-line insertion) ✅

The more complex changes were not applied:
- `b2d4f6a8` (framebuffer clear — 2 lines in `_draw_splash_mode`) ❌
- `c3e5a7b9` (gesture queue + SIGINT fix — ~25 lines across 2 files) ❌

**Learning:** When issuing multiple prompts as a combined command, Claude Code may
silently skip changes it cannot locate precisely. The `manager.py` changes require
exact context matching inside `_draw_splash_mode()`. The `app.py` SIGINT change
requires locating `_signal_handler`. Run these prompts individually to confirm
application.

### 5.2 Stale Welcome Cache on Pi

The WELCOME screen render cache (`_screen_render_cache[SetupScreen.WELCOME]`) was
populated before the new font sizes were available. On Pi, the old surface was cached
from a previous run's state. In-memory caches should not persist across process
restarts — this alternation indicates a code path is populating the cache from a
stale source within the same run. Likely cause: `setup_original_backup.py` being
imported at runtime alongside `setup.py`.

### 5.3 Watchdog Self-Join on Darwin

`WatchdogMonitor.stop()` always calls `self._thread.join()`. When the watchdog fires
its own shutdown callback, it is calling join from within its own thread.
`threading.join()` raises `RuntimeError: cannot join current thread` in this case.
Fix: guard with `if threading.current_thread() is not self._thread`.

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Sequencing

Current state requires these steps in order:

```
Step 1 — Investigate setup_original_backup.py import
         Determine if it is imported at runtime and contributing the stale
         WELCOME render. If so, file trivial-exemption removal or rename.
         Verify: §7.1

Step 2 — Pi framebuffer clear (b2d4f6a8)
         Prompt: workspace/prompt/prompt-b2d4f6a8-pi-clear-framebuffer-on-splash.md
         Run individually: implement workspace/prompt/prompt-b2d4f6a8-pi-clear-framebuffer-on-splash.md
         Verify: §7.2

Step 3 — macOS gesture queue + SIGINT fix (c3e5a7b9)
         Prompt: workspace/prompt/prompt-c3e5a7b9-macos-gesture-queue-sigint-fix.md
         Run individually: implement workspace/prompt/prompt-c3e5a7b9-macos-gesture-queue-sigint-fix.md
         Verify: §7.3

Step 4 — Watchdog self-join fix (e4a6c8f2, trivial exemption)
         Issue: workspace/issues/issue-e4a6c8f2-watchdog-self-join-darwin.md
         File: src/gtach/core/watchdog.py — WatchdogMonitor.stop()
         Guard self-join: if threading.current_thread() is not self._thread
         Verify: §7.4

Step 5 — Pi visual confirmation
         Deploy and confirm: no splash ghost, stable WELCOME layout
         Commands: §7.5

Step 6 — Mac visual confirmation
         Confirm: no beach ball, Ctrl+C exits cleanly
         Commands: §7.6

Step 7 — Sim mode (c7e2f1a9)
         Prompt: workspace/prompt/prompt-c7e2f1a9-sim-mode.md
         Only after Steps 1–6 confirmed stable.
```

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Verification

### 7.1 setup_original_backup.py Import Check

```bash
cd /Users/williamwatson/Documents/GitHub/GTach
grep -r "setup_original_backup" src/gtach/ --include="*.py"
```

Expected: no results. If any file imports it, that import is the source of stale renders.

### 7.2 Pi Framebuffer Clear

After applying `b2d4f6a8`:
```bash
python -c "import ast; ast.parse(open('src/gtach/display/manager.py').read())"
grep -A5 "is_complete" src/gtach/display/manager.py | grep "clear_surface"
```

Expected: `clear_surface` found in the `is_complete()` branch.

### 7.3 macOS Gesture Queue

After applying `c3e5a7b9`:
```bash
python -c "import ast; ast.parse(open('src/gtach/display/manager.py').read())"
python -c "import ast; ast.parse(open('src/gtach/app.py').read())"
grep "_mouse_event_queue\|_gesture_worker" src/gtach/display/manager.py
```

Expected: both symbols present.

### 7.4 Watchdog Self-Join

```bash
grep -n "current_thread\|join" src/gtach/core/watchdog.py
```

Expected: `threading.current_thread() is not self._thread` guard before `join` call.

### 7.5 Pi Visual Confirmation

```bash
./build.sh
scp dist/*.whl root@gtach.local:/tmp/
ssh root@gtach.local '/opt/gtach/install.sh'
ssh root@gtach.local 'gtach --debug 2>&1 | tee /opt/gtach/gtach-debug.log'
```

Confirm: no splash ghost on transition, stable WELCOME layout (no alternation).

### 7.6 Mac Visual Confirmation

```bash
cd /Users/williamwatson/Documents/GitHub/GTach
python -m gtach --macos --debug 2>&1 | tee gtach.log
```

Confirm: no beach ball on window click, Ctrl+C exits cleanly from terminal.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-05-06 | Initial document — full restoration roadmap from conversation audit |
| 0.2 | 2026-05-06 | Updated after second visual test — recorded completions, failures, new defects, learnings |
| 0.3 | 2026-05-06 | Added task §4.4 watchdog self-join fix (e4a6c8f2); issue filed |

---

Copyright (c) 2026 William Watson. MIT License.
