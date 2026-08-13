Created: 2026 August 13

# Prompt: Extend the DISCONNECTED Colour Scheme to OPTIONS, ACKNOWLEDGEMENT, SETUP and SPLASH

---

## Table of Contents

- [1. Prompt](<#1. prompt>)
- [2. Version History](<#2. version history>)

---

## 1. Prompt

```yaml
prompt_info:
  id: "prompt-ba2d5de2"
  task_type: "refactor"
  source_ref: "change-ba2d5de2"
  target_profile: "claude_code"
  date: "2026-08-13"
  iteration: 1
  coupled_docs:
    change_ref: "change-ba2d5de2"
    change_iteration: 1

context:
  purpose: >
    DISCONNECTED's background/text colours were changed to a pale
    dusty-yellow background, (216, 200, 146), with black text,
    (0, 0, 0), for readability. Apply the same background, text and
    border treatment to OPTIONS (all three sub-views), ACKNOWLEDGEMENT,
    SETUP and SPLASH, leaving RADIAL, DISCONNECTED itself, button
    fills/labels, and every semantic or status colour untouched.
  integration: >
    Four edits in three files: manager.py (OPTIONS's three sub-views
    and ACKNOWLEDGEMENT), splash.py (SplashScreen), setup.py
    (SetupDisplayManager). No new files, no interface changes.
  knowledge_references:
    - "ai/workspace/issues/issue-ba2d5de2-nondisconnected-screen-colours.md"
    - "ai/workspace/change/change-ba2d5de2-nondisconnected-screen-colours.md"
  constraints:
    - "Do NOT modify RADIAL rendering (_draw_radial_mode, _get_shift_cue, _get_band_colour) or DAY_PALETTE / NIGHT_PALETTE in models.py. Excluded by explicit instruction."
    - "Do NOT modify _render_disconnected, _register_disconnected_regions, _draw_reconnect_spinner, or _DISCONNECTED_BG_COLOUR / _DISCONNECTED_TEXT_COLOUR themselves. DISCONNECTED is the reference, not a target."
    - "Do NOT change any button fill colour or button label colour in manager.py, splash.py or setup.py. This includes the (80, 80, 100) / (140, 40, 40) / (0, 120, 0) button fills in OPTIONS's sub-views and every button colour in setup.py's welcome/discovery/device-list/pairing/current-device screens."
    - "Do NOT change SetupDisplayManager.colors['primary'], ['success'], ['warning'], ['danger'] or ['border']. These are semantic accents, not the background/text pair in scope."
    - "Do NOT change graphics/splash_graphics.py or its SPLASH_COLORS dict. The automotive-gauge progress indicator keeps its own palette."
    - "Do NOT change ConnectionStatus or its colour values in models.py, and do not change any call to _draw_status_indicator."
    - "Do NOT change any touch region, button rect, geometry, timing, or control-flow logic in any of the three files. Every edit is a colour value only."
    - "Do NOT introduce any new colour constant, dict key, or method. Reuse DisplayManager._DISCONNECTED_BG_COLOUR and _DISCONNECTED_TEXT_COLOUR by reference in manager.py; use the literal RGB tuples (216, 200, 146) and (0, 0, 0) in splash.py and setup.py, since those files do not import DisplayManager."
    - "Python 3.11. PEP 8. No docstring rewrites beyond what is needed to describe the new colour if an existing docstring names the old one explicitly (e.g. splash.py's 'professional dark theme' comment)."

specification:
  description: "Apply edits A, B, C and D exactly as specified; no other file or line changes."
  requirements:
    functional:
      - "OPTIONS menu, update sub-view and confirm-clear sub-view render background (216, 200, 146), border (216, 200, 146), and all text (0, 0, 0)."
      - "ACKNOWLEDGEMENT renders background (216, 200, 146), border (216, 200, 146), and all text (0, 0, 0)."
      - "SPLASH renders background (216, 200, 146), the circular border (216, 200, 146), primary_text and secondary_text both (0, 0, 0), and a progress_bg that remains visibly distinct from both the background and the (64, 150, 255) progress_fill."
      - "SETUP renders background (216, 200, 146), the circular border (216, 200, 146), and text/text_dim both (0, 0, 0)."
      - "RADIAL and DISCONNECTED render exactly as before this change."
      - "Every button fill and button label colour in all three files is identical to before this change."
      - "SETUP's primary/success/warning/danger/border accent colours are identical to before this change."
    technical:
      language: "Python"
      version: "3.11"
      standards:
        - "No new functions, classes, or dict keys"
        - "Professional docstrings only where an existing one names a colour this change replaces"

design:
  architecture: >
    Literal colour substitution at existing draw calls and colour
    dictionaries. No new abstraction, no shared colour module — each
    of the three files keeps its own values, matching how the codebase
    already handles per-screen colour today.
  components:
    - name: "EDIT A — manager.py: OPTIONS's three sub-views"
      type: "function"
      purpose: "Match DISCONNECTED's background, border and text treatment."
      logic:
        - "In _draw_options_menu: change `self.rendering_engine.clear_surface(RenderTarget.BACK_BUFFER, (40, 40, 50))` to use `self._DISCONNECTED_BG_COLOUR` in place of the literal tuple."
        - "In the same method: change `self._draw_shift_border((200, 0, 0))` to `self._draw_shift_border(self._DISCONNECTED_BG_COLOUR)`."
        - "In the same method: change the 'Options' title render call's colour argument from `(255, 255, 255)` to `self._DISCONNECTED_TEXT_COLOUR`."
        - "In the same method: change the 'Swipe up to return' hint text colour from `(150, 150, 150)` to `self._DISCONNECTED_TEXT_COLOUR`."
        - "Do NOT touch the page-indicator dots (they read `palette.tick`, part of the day/night palette system, unrelated to this change) or the button fill/label colours passed to `_draw_button`."
        - "In _draw_confirm_view: change the clear_surface fill from `(40, 40, 50)` to `self._DISCONNECTED_BG_COLOUR`; change `self._draw_shift_border((200, 0, 0))` to `self._draw_shift_border(self._DISCONNECTED_BG_COLOUR)`; change the 'Clear settings?' title colour from `(255, 255, 255)` to `self._DISCONNECTED_TEXT_COLOUR`; change the two body-line colour `(200, 200, 200)` to `self._DISCONNECTED_TEXT_COLOUR`."
        - "Do NOT touch the Clear/Cancel button fills, (140, 40, 40) and (80, 80, 100), or their white labels."
        - "In _draw_update_view: change the clear_surface fill from `(40, 40, 50)` to `self._DISCONNECTED_BG_COLOUR`; change `self._draw_shift_border((200, 0, 0))` to `self._draw_shift_border(self._DISCONNECTED_BG_COLOUR)`; change the 'Update' title colour and the status-message colour, both `(255, 255, 255)`, to `self._DISCONNECTED_TEXT_COLOUR`; change the 'Swipe up to return' hint colour `(150, 150, 150)` to `self._DISCONNECTED_TEXT_COLOUR`."
        - "Do NOT touch the Install/Cancel/Back button fills, (0, 120, 0) and (80, 80, 100), their white labels, or the spinner's dot colours in _draw_update_spinner (they are functional progress indication, out of scope)."
    - name: "EDIT B — manager.py: _draw_acknowledgement_mode"
      type: "function"
      purpose: "Match DISCONNECTED's background, border and text treatment."
      logic:
        - "Change `self.rendering_engine.clear_surface(RenderTarget.BACK_BUFFER, (0, 0, 0))` to use `self._DISCONNECTED_BG_COLOUR`."
        - "Change `self._draw_shift_border((200, 0, 0))` to `self._draw_shift_border(self._DISCONNECTED_BG_COLOUR)`."
        - "Change the 'GTach' title colour `(255, 255, 255)` to `self._DISCONNECTED_TEXT_COLOUR`."
        - "Change the body warning-text colour `(200, 200, 200)` to `self._DISCONNECTED_TEXT_COLOUR`."
        - "Change the instruction-text colour `(150, 150, 150)` to `self._DISCONNECTED_TEXT_COLOUR`."
    - name: "EDIT C — splash.py: SplashScreen"
      type: "class"
      purpose: "Match DISCONNECTED's background/text treatment for the startup screen."
      logic:
        - "In `self._colors` (in `__init__`): change `'background': (15, 20, 25)` to `'background': (216, 200, 146)`."
        - "Change `'primary_text': (255, 255, 255)` to `'primary_text': (0, 0, 0)`."
        - "Change `'secondary_text': (180, 190, 200)` to `'secondary_text': (0, 0, 0)`."
        - "Change `'progress_bg': (40, 45, 50)` to a tone that is visibly distinct from both `(216, 200, 146)` and `(64, 150, 255)` — a muted mid-brown/olive derived from darkening the new background is appropriate, e.g. in the range `(150, 135, 90)` to `(170, 150, 100)`; pick one value and use it consistently. Do not leave it at a dark tone designed for the old background."
        - "Do NOT change `'accent'` `(64, 150, 255)` or `'progress_fill'` `(64, 150, 255)` — both are functional/status colours (the OBD connection icon and the progress fill)."
        - "`'border'` `(80, 90, 100)` is currently unread by any method (`_draw_border` hard-codes its own colour). Leave the dict entry as-is; do not remove it and do not wire it up."
        - "In `_draw_border`: change the hard-coded `pygame.draw.circle(surface, (200, 0, 0), ...)` colour argument to `self._colors['background']`."
        - "The comment above `self._colors = {` reads 'Color scheme - professional dark theme'; update it to describe the new scheme (e.g. 'Color scheme - matches the DISCONNECTED screen') since it now names the wrong theme."
    - name: "EDIT D — setup.py: SetupDisplayManager"
      type: "class"
      purpose: "Match DISCONNECTED's background/text treatment for the pairing wizard."
      logic:
        - "In `self.colors` (in `__init__`): change `'background': (20, 20, 30)` to `'background': (216, 200, 146)`."
        - "Change `'text': (255, 255, 255)` to `'text': (0, 0, 0)`."
        - "Change `'text_dim': (180, 180, 180)` to `'text_dim': (0, 0, 0)`."
        - "Do NOT change `'surface'`, `'primary'`, `'success'`, `'warning'`, `'danger'` or `'border'`."
        - "In `_draw_circular_border`: change the hard-coded `pygame.draw.circle(surface, (200, 0, 0), ...)` colour argument to `self.colors['background']`."

data_schema:
  entities: []

error_handling:
  strategy: "None required; no new failure modes are introduced by a colour-literal change."
  exceptions: []
  logging:
    level: "No logging changes."
    format: "No format change."

testing:
  unit_tests: []
  edge_cases: []
  validation:
    - "grep -n 'clear_surface(RenderTarget.BACK_BUFFER, (40, 40, 50))' src/gtach/display/manager.py returns no match."
    - "grep -n \"clear_surface(RenderTarget.BACK_BUFFER, (0, 0, 0))\" src/gtach/display/manager.py — the only remaining match is inside _render_disconnected (which fills black before drawing its own background-coloured border) and _draw_radial_mode's corner fill; none remain in _draw_acknowledgement_mode."
    - "grep -n '_draw_shift_border((200, 0, 0))' src/gtach/display/manager.py returns no match."
    - "grep -n '(15, 20, 25)' src/gtach/display/splash.py returns no match."
    - "grep -n '(20, 20, 30)' src/gtach/display/setup.py returns no match."
    - "grep -n '(200, 0, 0)' src/gtach/display/splash.py and src/gtach/display/setup.py returns no match at the circular-border call sites."
    - "pytest tests/ passes."

deliverable:
  format_requirements:
    - "Edit the three files in place; no new files."
  files:
    - path: "src/gtach/display/manager.py"
      content: "EDIT A, EDIT B"
    - path: "src/gtach/display/splash.py"
      content: "EDIT C"
    - path: "src/gtach/display/setup.py"
      content: "EDIT D"

success_criteria:
  - "_draw_options_menu, _draw_confirm_view and _draw_update_view in src/gtach/display/manager.py fill the background and border with DisplayManager._DISCONNECTED_BG_COLOUR and render all text in _DISCONNECTED_TEXT_COLOUR, verified by reading the three methods."
  - "_draw_acknowledgement_mode in the same file does the same."
  - "grep -n '(40, 40, 50)' src/gtach/display/manager.py, restricted to _draw_options_menu, _draw_confirm_view and _draw_update_view, returns no match."
  - "grep -n '_draw_shift_border((200, 0, 0))' src/gtach/display/manager.py returns no match."
  - "Button fill colours (80, 80, 100), (140, 40, 40), (0, 120, 0) and their white labels are byte-identical to before this change, verified by reading _draw_options_menu, _draw_confirm_view and _draw_update_view."
  - "src/gtach/display/splash.py's self._colors['background'] is (216, 200, 146), ['primary_text'] and ['secondary_text'] are both (0, 0, 0), ['accent'] and ['progress_fill'] are unchanged at (64, 150, 255), and _draw_border reads self._colors['background'] rather than a hard-coded tuple."
  - "src/gtach/display/setup.py's self.colors['background'] is (216, 200, 146), ['text'] and ['text_dim'] are both (0, 0, 0), ['primary']/['success']/['warning']/['danger']/['border'] are unchanged, and _draw_circular_border reads self.colors['background'] rather than a hard-coded tuple."
  - "_draw_radial_mode, _get_shift_cue, _get_band_colour, DAY_PALETTE and NIGHT_PALETTE in src/gtach/display/manager.py and src/gtach/display/models.py are byte-identical to before this change."
  - "_render_disconnected, _register_disconnected_regions, _draw_reconnect_spinner, _DISCONNECTED_BG_COLOUR and _DISCONNECTED_TEXT_COLOUR in src/gtach/display/manager.py are byte-identical to before this change."
  - "src/gtach/display/graphics/splash_graphics.py is byte-identical to before this change."
  - "pytest tests/ passes."

element_registry:
  source: ""
  entries:
    modules:
      - name: "manager"
        path: "src/gtach/display/manager.py"
      - name: "splash"
        path: "src/gtach/display/splash.py"
      - name: "setup"
        path: "src/gtach/display/setup.py"
    classes:
      - name: "DisplayManager"
        module: "gtach.display.manager"
      - name: "SplashScreen"
        module: "gtach.display.splash"
      - name: "SetupDisplayManager"
        module: "gtach.display.setup"
    functions:
      - name: "_draw_options_menu"
        module: "gtach.display.manager"
        signature: "(self) -> None"
      - name: "_draw_confirm_view"
        module: "gtach.display.manager"
        signature: "(self) -> None"
      - name: "_draw_update_view"
        module: "gtach.display.manager"
        signature: "(self) -> None"
      - name: "_draw_acknowledgement_mode"
        module: "gtach.display.manager"
        signature: "(self) -> None"
      - name: "_draw_border"
        module: "gtach.display.splash"
        signature: "(self, surface, width: int, height: int) -> None"
      - name: "_draw_circular_border"
        module: "gtach.display.setup"
        signature: "(self, surface) -> None"
    constants:
      - name: "_DISCONNECTED_BG_COLOUR"
        module: "gtach.display.manager"
        type: "Tuple[int, int, int]"
      - name: "_DISCONNECTED_TEXT_COLOUR"
        module: "gtach.display.manager"
        type: "Tuple[int, int, int]"

notes: >
  On-target verification is a human step (William): swipe down to
  OPTIONS and page through both pages, open Check for updates, open
  Clear settings, trigger ACKNOWLEDGEMENT, run Setup end to end
  (Welcome through Complete), and observe SPLASH at startup. Confirm
  RADIAL and DISCONNECTED are visually unchanged. Confirm the SPLASH
  progress bar track remains visible against both the new background
  and its blue fill — the one value in this prompt without a literal
  DISCONNECTED-derived RGB to match, per change-ba2d5de2's risk entry.

  The three files are edited independently and share no colour
  constant across module boundaries except within manager.py, where
  _DISCONNECTED_BG_COLOUR / _DISCONNECTED_TEXT_COLOUR are referenced
  by name rather than restated as literals. splash.py and setup.py
  each hold their own literal copies of (216, 200, 146) and (0, 0, 0).
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-13 | Initial prompt implementing change-ba2d5de2 iteration 1. Four edits across manager.py (OPTIONS's three sub-views, ACKNOWLEDGEMENT), splash.py and setup.py, each a literal colour substitution. Target profile claude_code. |

---

Copyright (c) 2026 William Watson. MIT License.
