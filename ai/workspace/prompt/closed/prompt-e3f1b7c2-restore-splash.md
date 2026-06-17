Created: 2026 May 06

# Prompt: Restore Splash — Font, Border, Layout

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
  id: "prompt-e3f1b7c2"
  task_type: "code_generation"
  source_ref: "change-e3f1b7c2"
  date: "2026-05-06"
  iteration: 1
  coupled_docs:
    change_ref: "change-e3f1b7c2"
    change_iteration: 1
```

---

## 1.0 Prompt Information

Restore splash.py display changes lost due to file corruption. Seven targeted
modifications within the automotive mode render path only. No new files. No
interface changes. No modifications to text_only or minimal mode paths.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Context

```yaml
context:
  purpose: >
    Restore seven splash.py changes that were lost from the repository:
      1. Remove subtitle call from automotive mode block (line ~389)
      2. Title Y position: center_y - 65 -> center_y - 115
      3. Progress indicator Y: center_y + 40 -> center_y + 20
      4. Version text Y: center_y + 90 -> center_y + 105
      5. _draw_title_text: bypass typography cache; load Michroma-Regular.ttf at 72px directly
      6. _draw_version_text: same Michroma pattern at 40px
      7. _draw_border: replace grey pygame.draw.rect with red circle r=238, thickness=4

  integration: >
    splash.py renders three mode paths: automotive, text_only, minimal.
    All seven changes are confined to the automotive mode path and the two
    private draw helpers (_draw_title_text, _draw_version_text, _draw_border).
    The _draw_subtitle_text method and _subtitle field must NOT be removed —
    they are called by text_only and minimal mode paths.
    Michroma-Regular.ttf is already present at:
      src/gtach/assets/fonts/Michroma-Regular.ttf
    The red circle r=238 matches the _draw_circular_border() ring in manager.py.

  constraints:
    - "Python 3.9+ — no walrus operator"
    - "Modify only src/gtach/display/splash.py"
    - "Do not change any public method signatures"
    - "Do not remove _draw_subtitle_text method or _subtitle field"
    - "Do not modify text_only or minimal mode render paths"
    - "Michroma font path resolved relative to splash.py using os.path"
    - "Fallback: if Michroma file not found, use pygame.font.Font(None, size)"
    - "All logging via logging.getLogger(__name__) — no print statements"
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Specification

```yaml
specification:
  description: >
    Seven targeted changes to one file. Automotive mode render path and two
    private draw helpers only. No new files. No interface changes.

  requirements:
    functional:
      - "Remove self._draw_subtitle_text(...) call from automotive mode block; method itself remains"
      - "Title render Y: center_y - 65 -> center_y - 115"
      - "Progress indicator Y: center_y + 40 -> center_y + 20"
      - "Version text Y: center_y + 90 -> center_y + 105"
      - "_draw_title_text: resolve Michroma path via os.path; load pygame.font.Font(_fp, 72); fallback to Font(None, 72)"
      - "_draw_version_text: same Michroma pattern; size 40px; fallback to Font(None, 40)"
      - "_draw_border: replace pygame.draw.rect with pygame.draw.circle(surface, (200,0,0), (w//2, h//2), min(w,h)//2 - 2, 4)"

    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "PEP 8"
        - "Preserve all existing docstrings and copyright headers"
        - "No new imports beyond os (add import os if not already present)"
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Design

```yaml
design:
  architecture: >
    All changes are surgical edits to existing methods within one file.
    No structural changes to class hierarchy or public interfaces.

  components:

    - name: "automotive mode render block (modify)"
      type: "code block"
      purpose: "Remove subtitle render call from automotive path"
      logic:
        - "Locate the else block that handles automotive display mode"
        - "Remove the line: self._draw_subtitle_text(surface, center_x, center_y - 40)"
        - "Do NOT remove the _draw_subtitle_text method definition"
        - "Do NOT modify the text_only or minimal mode blocks"

    - name: "automotive mode title Y (modify)"
      type: "code expression"
      purpose: "Move title upward to create space for version text"
      logic:
        - "In automotive mode block, locate call to self._draw_title_text(...)"
        - "Change Y argument from center_y - 65 to center_y - 115"

    - name: "automotive mode progress Y (modify)"
      type: "code expression"
      purpose: "Adjust progress indicator position"
      logic:
        - "In automotive mode block, locate the progress bar/indicator Y argument"
        - "Change from center_y + 40 to center_y + 20"

    - name: "automotive mode version Y (modify)"
      type: "code expression"
      purpose: "Move version text lower"
      logic:
        - "In automotive mode block, locate call to self._draw_version_text(...)"
        - "Change Y argument from center_y + 90 to center_y + 105"

    - name: "_draw_title_text (modify)"
      type: "method"
      purpose: "Load Michroma at 72px, bypassing typography cache"
      logic:
        - "Add at start of method (or before font usage):"
        - "  import os"
        - "  _fp = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'assets', 'fonts', 'Michroma-Regular.ttf'))"
        - "  font_large = pygame.font.Font(_fp, 72) if os.path.exists(_fp) else pygame.font.Font(None, 72)"
        - "Use font_large for rendering the title text instead of any cached font"

    - name: "_draw_version_text (modify)"
      type: "method"
      purpose: "Load Michroma at 40px, bypassing typography cache"
      logic:
        - "Add at start of method (or before font usage):"
        - "  import os"
        - "  _fp = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'assets', 'fonts', 'Michroma-Regular.ttf'))"
        - "  font_ver = pygame.font.Font(_fp, 40) if os.path.exists(_fp) else pygame.font.Font(None, 40)"
        - "Use font_ver for rendering the version text instead of any cached font"

    - name: "_draw_border (modify)"
      type: "method"
      purpose: "Replace grey rect border with red circular border matching manager.py ring"
      logic:
        - "Remove existing pygame.draw.rect call (grey rectangle border)"
        - "Replace with:"
        - "  width, height = surface.get_size()"
        - "  pygame.draw.circle(surface, (200, 0, 0), (width // 2, height // 2), min(width, height) // 2 - 2, 4)"
        - "On a 480x480 surface: r = 238, matching _draw_circular_border() in manager.py"

  dependencies:
    internal:
      - "src/gtach/display/splash.py — SplashScreen class"
      - "src/gtach/assets/fonts/Michroma-Regular.ttf — must exist on disk"
    external:
      - "pygame — pygame.font.Font, pygame.draw.circle"
      - "os — os.path.normpath, os.path.join, os.path.dirname, os.path.exists"
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Error Handling

```yaml
error_handling:
  strategy: >
    Michroma load is non-fatal; fallback to pygame default font on any failure.
    All changes operate inside existing try/except blocks in the render path.

  exceptions:
    - exception: "FileNotFoundError / Exception"
      condition: "Michroma TTF file not found or unreadable"
      handling: "os.path.exists guard prevents load; fallback pygame.font.Font(None, size) used"
    - exception: "Exception"
      condition: "Any error in _draw_border circle draw"
      handling: "Caught by existing try/except in render method; logged if handler present"

  logging:
    level: "WARNING for font fallback; existing error handling otherwise unchanged"
    format: "%(asctime)s %(name)s %(levelname)s %(message)s"
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Deliverables

```yaml
deliverable:
  format_requirements:
    - "Modify only src/gtach/display/splash.py"
    - "Verify syntax: python -c \"import ast; ast.parse(open('src/gtach/display/splash.py').read())\""
    - "Do not alter file structure beyond the specified edits"

  files:
    - path: "src/gtach/display/splash.py"
      content: >
        Remove subtitle call from automotive mode; adjust three Y positions;
        modify _draw_title_text (Michroma 72px); modify _draw_version_text
        (Michroma 40px); modify _draw_border (red circle r=238).
```

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Success Criteria

```yaml
success_criteria:
  - "python -c \"import ast; ast.parse(open('src/gtach/display/splash.py').read())\" exits 0"
  - "Automotive mode does NOT call _draw_subtitle_text"
  - "_draw_subtitle_text method still present in class (not deleted)"
  - "_draw_title_text loads Michroma at 72px with os.path fallback guard"
  - "_draw_version_text loads Michroma at 40px with os.path fallback guard"
  - "_draw_border calls pygame.draw.circle with colour (200,0,0) and radius min(w,h)//2-2"
  - "_draw_border does NOT contain a pygame.draw.rect call"
  - "Title Y in automotive block is center_y - 115"
  - "Progress Y in automotive block is center_y + 20"
  - "Version Y in automotive block is center_y + 105"
```

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Tactical Brief

```yaml
tactical_brief: |
  Task: restore lost splash.py display changes in GTach (e3f1b7c2).

  FILE: src/gtach/display/splash.py

  CHANGE 1 — automotive mode block:
    Remove: self._draw_subtitle_text(surface, center_x, center_y - 40)
    DO NOT remove the _draw_subtitle_text method definition.
    DO NOT touch text_only or minimal mode paths.

  CHANGE 2 — automotive mode title Y:
    Change Y argument of self._draw_title_text call from:
      center_y - 65  ->  center_y - 115

  CHANGE 3 — automotive mode progress Y:
    Change Y argument of progress indicator render call from:
      center_y + 40  ->  center_y + 20

  CHANGE 4 — automotive mode version Y:
    Change Y argument of self._draw_version_text call from:
      center_y + 90  ->  center_y + 105

  CHANGE 5 — _draw_title_text method:
    At start of method (before existing font usage), add:
      import os
      _fp = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'assets', 'fonts', 'Michroma-Regular.ttf'))
      font_large = pygame.font.Font(_fp, 72) if os.path.exists(_fp) else pygame.font.Font(None, 72)
    Use font_large for title rendering (replace any existing font variable in that method).

  CHANGE 6 — _draw_version_text method:
    At start of method (before existing font usage), add:
      import os
      _fp = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'assets', 'fonts', 'Michroma-Regular.ttf'))
      font_ver = pygame.font.Font(_fp, 40) if os.path.exists(_fp) else pygame.font.Font(None, 40)
    Use font_ver for version text rendering (replace any existing font variable in that method).

  CHANGE 7 — _draw_border method:
    Remove existing pygame.draw.rect call (grey border).
    Replace with:
      width, height = surface.get_size()
      pygame.draw.circle(surface, (200, 0, 0), (width // 2, height // 2), min(width, height) // 2 - 2, 4)

  VERIFY:
    python -c "import ast; ast.parse(open('src/gtach/display/splash.py').read())"
```

[Return to Table of Contents](<#table of contents>)

---

## 9.0 Verification Commands

```bash
cd /Users/williamwatson/Documents/GitHub/GTach

# Syntax check
python -c "import ast; ast.parse(open('src/gtach/display/splash.py').read()) or print('splash.py OK')"

# Visual check
python -m gtach --macos --debug 2>&1 | tee gtach.log
```

Confirm visually:
- Splash: "GTach" title large, no subtitle, Michroma font, red circular border
- Splash: Version text visible and larger, positioned below centre
- Splash: Progress indicator visible near centre

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-05-06 | Initial document |

---

Copyright (c) 2026 William Watson. MIT License.
