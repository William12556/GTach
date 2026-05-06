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
| `setup_original_backup.py` import check | ✅ Confirmed not imported at runtime — not a factor |
| `src/gtach/display/manager.py` | ✅ Framebuffer clear on splash complete — fix present in source; Pi requires redeploy |
| `src/gtach/display/manager.py` | ❌ macOS gesture queue / beach ball fix NOT applied (c3e5a7b9) |
| `src/gtach/app.py` | ❌ SIGINT pygame.QUIT injection NOT applied (c3e5a7b9) |
| `src/gtach/core/watchdog.py` | ❌ Self-join RuntimeError in stop() on Darwin (e4a6c8f2) |
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

### 3.5 setup_original_backup.py Import Investigation ✅

`grep -r "setup_original_backup" src/gtach/ --include="*.py"` returns no results.
The file exists on disk but is not imported at runtime. Not a factor in any visual
defect. §4.2 stale cache diagnosis revised accordingly (see §5.4).

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Open Tasks

### 4.1 Pi — Framebuffer Clear on Splash Complete ✅ (source only)

**Issue:** `issue-b2d4f6a8`  
**Change:** `change-b2d4f6a8`  

Fix is already present in `src/gtach/display/manager.py` — `clear_surface` and
`swap_buffers` are called after the mode-transition block and before
`_splash_screen.reset()`. Pi was running a stale wheel; no code change required.

**Action:** rebuild and redeploy.
```bash
./build.sh
scp dist/*.whl root@gtach.local:/tmp/
ssh root@gtach.local '/opt/gtach/install.sh'
```

### 4.2 macOS Beach Ball and Ctrl+C Deadlock ❌

**Issue:** `issue-c3e5a7b9`  
**Change:** `change-c3e5a7b9`  
**Prompt:** `workspace/prompt/prompt-c3e5a7b9-macos-gesture-queue-sigint-fix.md`

**Not applied.** Mac log (2026-05-06) confirms app is stuck on WELCOME, blocked on
click. Two distinct problems:

1. **Beach ball on click**: gesture dispatch is synchronous on the Cocoa main thread.
2. **Cannot join current thread**: `GTachApplication.shutdown()` calls
   `self._watchdog.stop()` → `self._thread.join()`. When shutdown is triggered by
   the watchdog thread itself, this is a self-join. Fix: guard with
   `if threading.current_thread() is not self._thread`.

Re-run prompt individually:
```
implement workspace/prompt/prompt-c3e5a7b9-macos-gesture-queue-sigint-fix.md
```

### 4.3 Watchdog Self-Join on Darwin ❌

**Issue:** `issue-e4a6c8f2`  
**Trivial exemption applies** (§1.4.12) — single function, net delta ~3 lines,
no interface change.

Fix location: `WatchdogMonitor.stop()` in `src/gtach/core/watchdog.py`.  
Guard the join call to prevent self-join when shutdown is triggered by the
watchdog thread itself:
```python
if threading.current_thread() is not self._thread:
    self._thread.join(timeout=5.0)
    if self._thread.is_alive():
        self.logger.warning("Watchdog monitor thread did not stop cleanly")
```
The existing unconditional `self._thread.join(timeout=5.0)` and the `is_alive()`
warning block both need to move inside this guard.

### 4.4 Sim Mode ❌

Prompt `prompt-c7e2f1a9-sim-mode.md` complete and ready. No dependency on items
4.1–4.3. Can be implemented independently once the display issues are stable.

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
silently skip changes it cannot locate precisely. Run these prompts individually.

### 5.2 Pi Splash/Welcome Alternation — Root Cause

The splash/welcome alternation observed visually on the Pi is caused by the
framebuffer double-buffer not being cleared at splash completion (b2d4f6a8).
The "old welcome" seen alternating with the new welcome is the splash frame
persisting in the back buffer. This is NOT a render cache issue.

Confirmed by log analysis (2026-05-06 gtach-debug_PI.log): the WELCOME render
cache is populated correctly from current fonts on the first post-splash render
(`FontManager Created and cached font size 20`). All subsequent renders are
cache hits serving the correct (new) surface.

### 5.3 Watchdog Self-Join on Darwin

`WatchdogMonitor.stop()` always calls `self._thread.join()`. When the watchdog
fires its own shutdown callback, it is calling join from within its own thread.
`threading.join()` raises `RuntimeError: cannot join current thread`. Fix: guard
with `if threading.current_thread() is not self._thread`.

### 5.4 §4.2 Stale Render Cache — Diagnosis Revised

Original diagnosis (stale cache from `setup_original_backup.py`) was incorrect.
`setup_original_backup.py` is not imported at runtime (confirmed §3.5).
The render cache in `setup.py` operates correctly: first post-splash render
populates the cache with current fonts; all subsequent renders are cache hits
from that correct surface. The alternation is the framebuffer issue (§5.2).

### 5.5 Mac WELCOME Screen Hang — Log Analysis (2026-05-06)

Mac log confirms: app reaches WELCOME, FontManager initialises, font size 20
created on first WELCOME render (12:28:16,266), cache populated, all subsequent
renders are cache hits. Session ended cleanly (Ctrl+C or red ball). No click
event captured in log. Beach ball is a Cocoa main-thread block — not logged,
only observable. Prompt c3e5a7b9 must be applied to fix.

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Sequencing

```
Step 1 — setup_original_backup.py import check    ✅ COMPLETE
         grep confirmed: not imported at runtime.

Step 2 — Pi framebuffer clear (b2d4f6a8)    ✅ fix in source
         No code change needed. Rebuild and redeploy to Pi.
         ./build.sh && scp dist/*.whl root@gtach.local:/tmp/
         ssh root@gtach.local '/opt/gtach/install.sh'
         Verify: §7.1

Step 3 — macOS gesture queue + SIGINT fix (c3e5a7b9)
         Prompt: workspace/prompt/prompt-c3e5a7b9-macos-gesture-queue-sigint-fix.md
         Run: implement workspace/prompt/prompt-c3e5a7b9-macos-gesture-queue-sigint-fix.md
         Verify: §7.2

Step 4 — Watchdog self-join fix (e4a6c8f2, trivial exemption)
         File: src/gtach/core/watchdog.py — WatchdogMonitor.stop()
         Guard: if threading.current_thread() is not self._thread
         Verify: §7.3

Step 5 — Pi visual confirmation
         Deploy and confirm: no splash ghost, stable WELCOME layout
         Commands: §7.4

Step 6 — Mac visual confirmation
         Confirm: no beach ball on click, Ctrl+C exits cleanly
         Commands: §7.5

Step 7 — Sim mode (c7e2f1a9)
         Prompt: workspace/prompt/prompt-c7e2f1a9-sim-mode.md
         Only after Steps 2–6 confirmed stable.
```

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Verification

### 7.1 Pi Framebuffer Clear

After applying `b2d4f6a8`:
```bash
python -c "import ast; ast.parse(open('src/gtach/display/manager.py').read())"
grep -A5 "is_complete" src/gtach/display/manager.py | grep "clear_surface"
```

Expected: `clear_surface` found in the `is_complete()` branch.

### 7.2 macOS Gesture Queue

After applying `c3e5a7b9`:
```bash
python -c "import ast; ast.parse(open('src/gtach/display/manager.py').read())"
python -c "import ast; ast.parse(open('src/gtach/app.py').read())"
grep "_mouse_event_queue\|_gesture_worker" src/gtach/display/manager.py
```

Expected: both symbols present.

### 7.3 Watchdog Self-Join

```bash
grep -n "current_thread\|join" src/gtach/core/watchdog.py
```

Expected: `threading.current_thread() is not self._thread` guard before `join` call.

### 7.4 Pi Visual Confirmation

```bash
./build.sh
scp dist/*.whl root@gtach.local:/tmp/
ssh root@gtach.local '/opt/gtach/install.sh'
ssh root@gtach.local 'gtach --debug 2>&1 | tee /opt/gtach/gtach-debug.log'
```

Confirm: no splash ghost on transition, stable WELCOME layout.

### 7.5 Mac Visual Confirmation

```bash
cd /Users/williamwatson/Documents/GitHub/GTach
python -m gtach --macos --debug 2>&1 | tee gtach.log
```

Confirm: no beach ball on window click, Ctrl+C exits cleanly.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-05-06 | Initial document — full restoration roadmap from conversation audit |
| 0.2 | 2026-05-06 | Updated after second visual test — recorded completions, failures, new defects, learnings |
| 0.3 | 2026-05-06 | Added task §4.4 watchdog self-join fix (e4a6c8f2); issue filed |
| 0.4 | 2026-05-06 | Log analysis (gtach-debug_Mac.log, gtach-debug_PI.log): confirmed setup_original_backup.py not imported; revised §4.2 stale cache diagnosis; Pi alternation attributed to framebuffer double-buffer (b2d4f6a8); §4.2 removed as separate task; §5.4–5.5 added; Step 1 marked complete; task list renumbered |
| 0.5 | 2026-05-06 | b2d4f6a8 fix confirmed present in source (manager.py); Pi running stale wheel; §4.1 updated to ✅ source-only; §6.0 Step 2 updated — deploy only, no code change |

---

Copyright (c) 2026 William Watson. MIT License.
