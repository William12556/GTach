Created: 2026 May 06

# Knowledge: Display Restoration Roadmap

---

## Table of Contents

- [1.0 Purpose](<#1.0 purpose>)
- [2.0 Status Summary](<#2.0 status summary>)
- [3.0 Restoration Tasks](<#3.0 restoration tasks>)
- [4.0 Enhancement Tasks](<#4.0 enhancement tasks>)
- [5.0 Sequencing](<#5.0 sequencing>)
- [6.0 Verification](<#6.0 verification>)
- [Version History](<#version history>)

---

## 1.0 Purpose

This document records all confirmed UI/display changes that were applied in previous
sessions and are now absent from the repository due to file corruption. It provides
a sequenced restoration path back to the last known-good display state, plus the
pending sim mode enhancement.

Source of truth for confirmed changes: conversation `83922674` (2026-04-23).

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Status Summary

All confirmed lost changes are in three source files:

| File | Status |
|---|---|
| `src/gtach/display/typography.py` | ❌ All changes lost |
| `src/gtach/display/manager.py` | ❌ All changes lost |
| `src/gtach/display/splash.py` | ❌ All changes lost |
| `src/gtach/comm/sim_transport.py` | ❌ Not yet created (enhancement) |
| `src/gtach/comm/sim_bluetooth.py` | ❌ Not yet created (enhancement) |
| `src/gtach/comm/transport.py` | ❌ Not yet modified (enhancement) |
| `src/gtach/main.py` | ❌ Not yet modified (enhancement) |
| `src/gtach/display/setup_components/bluetooth/interface.py` | ❌ Not yet modified (enhancement) |
| `src/gtach/app.py` | ❌ Not yet modified (enhancement) |
| `src/gtach/display/setup.py` | ❌ Not yet modified (enhancement) |

Prompt `prompt-d4e8f2a1-restore-display.md` covers `typography.py` and `manager.py`
only. `splash.py` was omitted and must be covered separately (see §3.3).

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Restoration Tasks

### 3.1 typography.py — Constants and Michroma Font

**File:** `src/gtach/display/typography.py`

**Status:** ❌ Not yet applied. Covered by `prompt-d4e8f2a1-restore-display.md`.

Changes required:

1. `TypographyConstants.FONT_RPM_LARGE`: `96` → `180`
2. `TypographyConstants.MAX_FONT_SIZE`: `96` → `180`
   - These two must always be changed together. `MAX_FONT_SIZE` silently clips any
     font larger than itself; if only `FONT_RPM_LARGE` is raised the RPM display
     stays at 96px.
3. `FontManager.__init__`: resolve `Michroma-Regular.ttf` path at init via
   `os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'assets', 'fonts', 'Michroma-Regular.ttf'))`.
   Store as `self._michroma_path`; set `None` if file absent.
4. `FontManager.get_font()`: load `pygame.font.Font(self._michroma_path, size)` when
   `_michroma_path` is set; fall back to `pygame.font.Font(None, size)`.

Font file location (already on disk): `src/gtach/assets/fonts/Michroma-Regular.ttf`

[Return to Table of Contents](<#table of contents>)

---

### 3.2 manager.py — Circular Border and RPM Format

**File:** `src/gtach/display/manager.py`

**Status:** ❌ Not yet applied. Covered by `prompt-d4e8f2a1-restore-display.md`.

Changes required:

1. Add `_draw_circular_border(self)` method:
   - Get back-buffer surface from `self.rendering_engine.get_surface(RenderTarget.BACK_BUFFER)`
   - Call `pygame.draw.circle(surface, (200, 0, 0), (240, 240), 238, 4)`
   - Wrap in try/except; log ERROR on failure.
2. `_draw_digital_mode()`:
   - RPM format: `f"{int(rpm)}"` → `f"{rpm/1000:.1f}"`
   - RPM value Y position: `220` → `215`
   - `"RPM × 1000"` label Y position: `365` → `390`
   - Call `self._draw_circular_border()` at end of method, before `except`.
3. `_draw_gauge_mode()`:
   - Call `self._draw_circular_border()` after center hub circles, before `except`.
4. `_draw_settings_mode()`:
   - Call `self._draw_circular_border()` after instructions `render_text`, before `except`.
5. `_draw_setup_mode_fallback()`:
   - Remove yellow `draw_rect` border call.
   - Replace with `self._draw_circular_border()`.

[Return to Table of Contents](<#table of contents>)

---

### 3.3 splash.py — Title, Font, Border, Subtitle

**File:** `src/gtach/display/splash.py`

**Status:** ❌ Not yet applied. **NOT covered by any existing prompt.** Needs new prompt
or trivial-exemption direct edit.

Current state (confirmed by source inspection):
- Subtitle `"Bluetooth OBD-II Monitor"` still rendered in automotive mode (line 389)
- Title Y: `center_y - 65` (needs `center_y - 115`)
- Progress Y: `center_y + 40` (needs `center_y + 20`)
- Version Y: `center_y + 90` (needs `center_y + 105`)
- `_draw_title_text`: uses typography cache / fallback 48px (needs direct 72px Michroma)
- `_draw_version_text`: uses typography cache / fallback 20px (needs direct 40px Michroma)
- `_draw_border`: draws grey rectangle (needs red circle r=238, thickness=4, colour (200,0,0))

Changes required (automotive mode render path only):

1. Remove `self._draw_subtitle_text(surface, center_x, center_y - 40)` from automotive
   mode block (line 389). The method and `_subtitle` field remain intact for text_only
   and minimal modes.
2. Title Y: `center_y - 65` → `center_y - 115`
3. Progress Y: `center_y + 40` → `center_y + 20`
4. Version Y: `center_y + 90` → `center_y + 105`
5. `_draw_title_text`: bypass typography cache; load Michroma at 72px directly:
   ```python
   import os
   _fp = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'assets', 'fonts', 'Michroma-Regular.ttf'))
   font_large = pygame.font.Font(_fp, 72) if os.path.exists(_fp) else pygame.font.Font(None, 72)
   ```
6. `_draw_version_text`: same pattern, size 40px.
7. `_draw_border`: replace `pygame.draw.rect` with:
   ```python
   pygame.draw.circle(surface, (200, 0, 0), (width // 2, height // 2), min(width, height) // 2 - 2, 4)
   ```
   On a 480×480 surface this produces r=238, matching the `_draw_circular_border()` ring
   in manager.py.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Enhancement Tasks

### 4.1 Sim Mode (c7e2f1a9)

**Status:** ❌ Not yet implemented. Prompt `prompt-c7e2f1a9-sim-mode.md` is complete.

Two new files plus six existing-file modifications to add `--transport simtcp` and
`--transport simbt` flags. Full specification is in the prompt document. No dependencies
on restoration tasks — can be executed independently.

Files:
- CREATE `src/gtach/comm/sim_transport.py`
- CREATE `src/gtach/comm/sim_bluetooth.py`
- MODIFY `src/gtach/comm/transport.py`
- MODIFY `src/gtach/main.py`
- MODIFY `src/gtach/app.py`
- MODIFY `src/gtach/display/setup_components/bluetooth/interface.py`
- MODIFY `src/gtach/display/setup.py`

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Sequencing

Execute in this order. Each step must pass its syntax/visual checks before proceeding.

```
Step 1 — typography.py + manager.py
         Prompt: workspace/prompt/prompt-d4e8f2a1-restore-display.md
         Claude Code command: implement workspace/prompt/prompt-d4e8f2a1-restore-display.md
         Verify: §6.1

Step 2 — splash.py
         Prompt: workspace/prompt/prompt-e3f1b7c2-restore-splash.md  (to be created)
         Claude Code command: implement workspace/prompt/prompt-e3f1b7c2-restore-splash.md
         Verify: §6.2

Step 3 — macOS visual confirmation
         Command: python -m gtach --macos --debug 2>&1 | tee gtach.log
         Confirm: §6.3

Step 4 — Pi deploy
         Commands: §6.4

Step 5 — Sim mode
         Prompt: workspace/prompt/prompt-c7e2f1a9-sim-mode.md
         Claude Code command: implement workspace/prompt/prompt-c7e2f1a9-sim-mode.md
         Verify: §6.5
```

Rationale: typography.py must be correct before splash.py is tested, as splash.py
imports from typography. Sim mode has no display dependencies and can be deferred
until display is confirmed stable.

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Verification

### 6.1 After Step 1 (typography.py + manager.py)

```bash
cd /Users/williamwatson/Documents/GitHub/GTach

# Syntax
python -c "import ast; ast.parse(open('src/gtach/display/typography.py').read()) or print('OK')"
python -c "import ast; ast.parse(open('src/gtach/display/manager.py').read()) or print('OK')"

# Constants
python -c "
from src.gtach.display.typography import TypographyConstants
assert TypographyConstants.FONT_RPM_LARGE == 180
assert TypographyConstants.MAX_FONT_SIZE == 180
print('Constants OK')
"
```

### 6.2 After Step 2 (splash.py)

```bash
python -c "import ast; ast.parse(open('src/gtach/display/splash.py').read()) or print('OK')"
```

### 6.3 macOS Visual Confirmation

```bash
cd /Users/williamwatson/Documents/GitHub/GTach
python -m gtach --macos --debug 2>&1 | tee gtach.log
```

Confirm visually:
- Splash: "GTach" title large, no subtitle, Michroma font, red circular border
- Splash: Version text larger, positioned below centre
- Digital mode: RPM shows `x.x` format (e.g. `0.0`), `RPM × 1000` label visible below
- Digital mode: Red circular border
- Gauge mode: Red circular border (swipe to check)
- Settings mode: Red circular border (long-press to check)

### 6.4 Pi Deploy

```bash
# Build (from activated venv on Mac)
cd /Users/williamwatson/Documents/GitHub/GTach
./build.sh

# Transfer and install
scp dist/*.whl root@gtach.local:/tmp/
ssh root@gtach.local '/opt/gtach/install.sh'

# Run
ssh root@gtach.local 'gtach --debug 2>&1 | tee /opt/gtach/gtach-debug.log'
```

### 6.5 After Step 5 (Sim Mode)

```bash
cd /Users/williamwatson/Documents/GitHub/GTach
python -m gtach --transport simtcp --debug    # must start, RPM sweeps 800-6500
python -m gtach --transport simbt --debug     # must enter setup wizard
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-05-06 | Initial document — full restoration roadmap from conversation audit |

---

Copyright (c) 2026 William Watson. MIT License.
