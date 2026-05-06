Created: 2026 May 06

# Prompt: Restore Display — Font, Border, RPM Format

---

## Table of Contents

- [1.0 Prompt Information](<#1.0 prompt information>)
- [2.0 Context](<#2.0 context>)
- [3.0 Specification](<#3.0 specification>)
- [4.0 Design](<#4.0 design>)
- [5.0 Error Handling](<#5.0 error handling>)
- [6.0 Deliverables](<#6.0 deliverables>)
- [7.0 Success Criteria](<#7.0 success criteria>)
- [8.0 Tactical Brief](<#8.0 tactical brief>)
- [9.0 Verification Commands](<#9.0 verification commands>)
- [Version History](<#version history>)

---

```yaml
prompt_info:
  id: "prompt-d4e8f2a1"
  task_type: "code_generation"
  source_ref: "change-d4e8f2a1"
  date: "2026-05-06"
  iteration: 1
  coupled_docs:
    change_ref: "change-d4e8f2a1"
    change_iteration: 1
```

---

## 1.0 Prompt Information

Restore display changes that were lost due to file corruption. Four targeted modifications
to two source files. No new modules. No interface changes. All changes are restorations
of previously confirmed working UI behaviour.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Context

```yaml
context:
  purpose: >
    Restore four display changes that were lost from the repository:
      1. FONT_RPM_LARGE and MAX_FONT_SIZE raised from 96 to 180 in typography.py
      2. Michroma-Regular.ttf loaded in FontManager.get_font() with fallback to pygame default
      3. _draw_circular_border() helper added to manager.py (red ring, r=238, 4px)
      4. Circular border applied to all four display modes in manager.py
      5. Digital mode RPM value formatted as RPM/1000 (one decimal) with "RPM × 1000" label
      6. RPM value Y position 215, label Y position 390 in _draw_digital_mode

  integration: >
    typography.py: FontManager is a singleton used throughout the display subsystem.
    Michroma font is at src/gtach/assets/fonts/Michroma-Regular.ttf (already present on disk).
    manager.py: _draw_circular_border() is a private helper called at the end of four
    existing render methods.

  constraints:
    - "Python 3.9+ — no walrus operator"
    - "Do not modify any file not listed in deliverables"
    - "Do not change any public method signatures"
    - "Michroma font path: resolve relative to typography.py using os.path"
    - "Fallback: if Michroma file not found, use pygame.font.Font(None, size)"
    - "All logging via logging.getLogger(__name__) — no print statements"
    - "MAX_FONT_SIZE must equal FONT_RPM_LARGE — both set to 180"
    - "pygame.draw.circle must be called directly on the pygame surface from the rendering engine"
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Specification

```yaml
specification:
  description: >
    Six targeted changes across two files. No new files. No interface changes.

  requirements:
    functional:
      - "TypographyConstants.FONT_RPM_LARGE = 180 (was 96)"
      - "TypographyConstants.MAX_FONT_SIZE = 180 (was 96)"
      - "FontManager.get_font() loads Michroma-Regular.ttf when file exists; falls back to pygame.font.Font(None, size)"
      - "Michroma font path resolved at FontManager.__init__ via os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'assets', 'fonts', 'Michroma-Regular.ttf'))"
      - "DisplayManager._draw_circular_border(): draw red circle outline, colour (200,0,0), radius 238, thickness 4, centred at (240,240), directly on the pygame back-buffer surface"
      - "_draw_digital_mode: call _draw_circular_border() at end of method (after label render)"
      - "_draw_gauge_mode: call _draw_circular_border() at end of method (after center hub)"
      - "_draw_settings_mode: call _draw_circular_border() at end of method (after instructions text)"
      - "_draw_setup_mode_fallback: replace existing yellow draw_rect border call with _draw_circular_border()"
      - "_draw_digital_mode: RPM value rendered as f'{rpm/1000:.1f}' (not int(rpm))"
      - "_draw_digital_mode: RPM value Y position = 215"
      - "_draw_digital_mode: 'RPM \u00d7 1000' label Y position = 390"

    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "PEP 8"
        - "Preserve all existing docstrings and copyright headers"
        - "No new imports beyond os (already imported in manager.py)"
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Design

```yaml
design:
  architecture: >
    All changes are surgical edits to existing methods. No structural changes.

  components:

    - name: "TypographyConstants (modify)"
      type: "class"
      purpose: "Raise RPM font size constants"
      logic:
        - "FONT_RPM_LARGE = 180  # was 96"
        - "MAX_FONT_SIZE = 180   # was 96 — must equal FONT_RPM_LARGE"

    - name: "FontManager.__init__ (modify)"
      type: "method"
      purpose: "Resolve Michroma font path at init time"
      logic:
        - "Add after self._initialized = False:"
        - "  import os as _os"
        - "  _font_dir = _os.path.normpath(_os.path.join(_os.path.dirname(__file__), '..', 'assets', 'fonts'))"
        - "  self._michroma_path = _os.path.join(_font_dir, 'Michroma-Regular.ttf')"
        - "  if not _os.path.exists(self._michroma_path):"
        - "    self.logger.warning(f'Michroma font not found at {self._michroma_path}, using default')"
        - "    self._michroma_path = None"

    - name: "FontManager.get_font (modify)"
      type: "method"
      purpose: "Load Michroma when available; fallback to pygame default"
      logic:
        - "In the font creation block, replace:"
        - "  font = pygame.font.Font(None, validated_size)"
        - "With:"
        - "  if self._michroma_path:"
        - "    try:"
        - "      font = pygame.font.Font(self._michroma_path, validated_size)"
        - "    except Exception:"
        - "      font = pygame.font.Font(None, validated_size)"
        - "  else:"
        - "    font = pygame.font.Font(None, validated_size)"

    - name: "DisplayManager._draw_circular_border (add)"
      type: "method"
      purpose: "Draw red circular border on current back-buffer surface"
      logic:
        - "def _draw_circular_border(self) -> None:"
        - "  try:"
        - "    surface = self.rendering_engine.get_surface(RenderTarget.BACK_BUFFER)"
        - "    if surface:"
        - "      pygame.draw.circle(surface, (200, 0, 0), (240, 240), 238, 4)"
        - "  except Exception as e:"
        - "    self.logger.error(f'Circular border error: {e}')"

    - name: "_draw_digital_mode (modify)"
      type: "method"
      purpose: "Fix RPM format, fix Y positions, add border call"
      logic:
        - "RPM text: change f'{int(rpm)}' to f'{rpm/1000:.1f}'"
        - "RPM render position: change (240, 220) to (240, 215)"
        - "Label render position: change (240, 365) to (240, 390)"
        - "After label render block, before the except: call self._draw_circular_border()"

    - name: "_draw_gauge_mode (modify)"
      type: "method"
      purpose: "Add border call"
      logic:
        - "After center hub draw_circle calls, before the except: call self._draw_circular_border()"

    - name: "_draw_settings_mode (modify)"
      type: "method"
      purpose: "Add border call"
      logic:
        - "After the instructions render_text call, before the except: call self._draw_circular_border()"

    - name: "_draw_setup_mode_fallback (modify)"
      type: "method"
      purpose: "Replace yellow rect border with circular border"
      logic:
        - "Remove: self.rendering_engine.draw_rect(RenderTarget.BACK_BUFFER, (255, 255, 0), (0, 0, 480, 480), width=3)"
        - "Replace with: self._draw_circular_border()"

  dependencies:
    internal:
      - "src/gtach/display/typography.py — TypographyConstants, FontManager"
      - "src/gtach/display/manager.py — DisplayManager, RenderTarget"
      - "src/gtach/assets/fonts/Michroma-Regular.ttf — must exist on disk"
    external: []
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Error Handling

```yaml
error_handling:
  strategy: >
    All changes wrapped in existing try/except blocks. Michroma load failure is
    non-fatal — fallback to pygame default font. Border draw failure is logged
    and silently skipped.

  exceptions:
    - exception: "FileNotFoundError / Exception"
      condition: "Michroma font file not found or unreadable"
      handling: "Log WARNING; set self._michroma_path = None; use pygame.font.Font(None, size)"
    - exception: "Exception"
      condition: "pygame.draw.circle fails in _draw_circular_border"
      handling: "Log ERROR; no-op"

  logging:
    level: "WARNING for font fallback; ERROR for border failure"
    format: "%(asctime)s %(name)s %(levelname)s %(message)s"
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Deliverables

```yaml
deliverable:
  format_requirements:
    - "Modify only the two files listed below"
    - "Verify syntax: python -c \"import ast; ast.parse(open('<path>').read())\""
    - "Do not alter file structure beyond the specified edits"

  files:
    - path: "src/gtach/display/typography.py"
      content: "Modify TypographyConstants (2 constants), FontManager.__init__ (path resolution), FontManager.get_font (Michroma load)"
    - path: "src/gtach/display/manager.py"
      content: "Add _draw_circular_border(), modify _draw_digital_mode, _draw_gauge_mode, _draw_settings_mode, _draw_setup_mode_fallback"
```

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Success Criteria

```yaml
success_criteria:
  - "python -c \"import ast; ast.parse(open('src/gtach/display/typography.py').read())\" exits 0"
  - "python -c \"import ast; ast.parse(open('src/gtach/display/manager.py').read())\" exits 0"
  - "TypographyConstants.FONT_RPM_LARGE == 180"
  - "TypographyConstants.MAX_FONT_SIZE == 180"
  - "FontManager has _michroma_path attribute after init"
  - "DisplayManager has _draw_circular_border method"
  - "_draw_digital_mode renders RPM as x/1000 format with label at Y=390"
  - "All four mode-draw methods call _draw_circular_border()"
  - "_draw_setup_mode_fallback does NOT contain a yellow draw_rect border call"
  - "python -m gtach --macos --debug starts and displays splash without error"
```

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Tactical Brief

```yaml
tactical_brief: |
  Task: restore lost display changes in GTach (d4e8f2a1).

  FILE 1: src/gtach/display/typography.py

  CHANGE 1 — TypographyConstants:
    FONT_RPM_LARGE = 180   # was 96
    MAX_FONT_SIZE = 180    # was 96

  CHANGE 2 — FontManager.__init__:
    After self._initialized = False, add:
      import os as _os
      _font_dir = _os.path.normpath(_os.path.join(_os.path.dirname(__file__), '..', 'assets', 'fonts'))
      self._michroma_path = _os.path.join(_font_dir, 'Michroma-Regular.ttf')
      if not _os.path.exists(self._michroma_path):
          self.logger.warning(f'Michroma font not found at {self._michroma_path}')
          self._michroma_path = None

  CHANGE 3 — FontManager.get_font(), inside the 'if validated_size not in self._font_cache:' block:
    Replace:
      font = pygame.font.Font(None, validated_size)
    With:
      if self._michroma_path:
          try:
              font = pygame.font.Font(self._michroma_path, validated_size)
          except Exception:
              font = pygame.font.Font(None, validated_size)
      else:
          font = pygame.font.Font(None, validated_size)

  FILE 2: src/gtach/display/manager.py

  CHANGE 4 — Add new method _draw_circular_border(self) to DisplayManager:
    def _draw_circular_border(self) -> None:
        try:
            surface = self.rendering_engine.get_surface(RenderTarget.BACK_BUFFER)
            if surface:
                pygame.draw.circle(surface, (200, 0, 0), (240, 240), 238, 4)
        except Exception as e:
            self.logger.error(f'Circular border error: {e}')

  CHANGE 5 — _draw_digital_mode():
    a) RPM text: f'{int(rpm)}' -> f'{rpm/1000:.1f}'
    b) RPM render position: (240, 220) -> (240, 215)
    c) Label 'RPM × 1000' position: (240, 365) -> (240, 390)
    d) After label render block, before except: add self._draw_circular_border()

  CHANGE 6 — _draw_gauge_mode():
    After the two draw_circle calls for center hub, before except:
    add self._draw_circular_border()

  CHANGE 7 — _draw_settings_mode():
    After render_text for instructions text, before except:
    add self._draw_circular_border()

  CHANGE 8 — _draw_setup_mode_fallback():
    Remove:
      self.rendering_engine.draw_rect(RenderTarget.BACK_BUFFER, (255, 255, 0),
                                      (0, 0, 480, 480), width=3)
    Replace with:
      self._draw_circular_border()

  VERIFY:
    python -c "import ast; ast.parse(open('src/gtach/display/typography.py').read())"
    python -c "import ast; ast.parse(open('src/gtach/display/manager.py').read())"
```

[Return to Table of Contents](<#table of contents>)

---

## 9.0 Verification Commands

After Claude Code completes, run these commands to confirm the changes and test the application.

### 9.1 Syntax Check

```bash
cd /Users/williamwatson/Documents/GitHub/GTach
python -c "import ast; ast.parse(open('src/gtach/display/typography.py').read()) or print('typography.py OK')"
python -c "import ast; ast.parse(open('src/gtach/display/manager.py').read()) or print('manager.py OK')"
```

### 9.2 Constant Check

```bash
cd /Users/williamwatson/Documents/GitHub/GTach
python -c "
from src.gtach.display.typography import TypographyConstants
assert TypographyConstants.FONT_RPM_LARGE == 180, f'FONT_RPM_LARGE={TypographyConstants.FONT_RPM_LARGE}'
assert TypographyConstants.MAX_FONT_SIZE == 180, f'MAX_FONT_SIZE={TypographyConstants.MAX_FONT_SIZE}'
print('Constants OK')
"
```

### 9.3 macOS Run

```bash
cd /Users/williamwatson/Documents/GitHub/GTach
python -m gtach --macos --debug 2>&1 | tee gtach.log
```

Confirm visually:
- Michroma font applied (or warning logged if TTF missing)
- RPM display shows `x.x` format (e.g. `0.0`) not raw integer
- `RPM × 1000` label visible below RPM value
- Red circular border visible on digital display
- Red circular border visible on gauge display (swipe to check)
- Red circular border visible on settings display (long-press to check)

### 9.4 Pi Deploy

```bash
# 1. Build wheel (from activated venv on Mac)
cd /Users/williamwatson/Documents/GitHub/GTach
./build.sh

# 2. Transfer to Pi
scp dist/*.whl root@gtach.local:/tmp/

# 3. Install on Pi
ssh root@gtach.local '/opt/gtach/install.sh'

# 4. Run on Pi
ssh root@gtach.local 'gtach --debug 2>&1 | tee /opt/gtach/gtach-debug.log'
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-05-06 | Initial document |

---

Copyright (c) 2026 William Watson. MIT License.
