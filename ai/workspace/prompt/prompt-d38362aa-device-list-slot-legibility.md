Created: 2026 October 16

# Prompt: DEVICE_LIST Slot Column Enlargement and Signal Bar Legibility

---

## Table of Contents

- [1. Prompt](<#1. prompt>)
- [2. Version History](<#2. version history>)

---

## 1. Prompt

```yaml
prompt_info:
  id: "prompt-d38362aa"
  task_type: "code_generation"
  source_ref: "change-d38362aa"
  target_profile: "claude_code"
  date: "2026-10-16"
  iteration: 1
  coupled_docs:
    change_ref: "change-d38362aa"
    change_iteration: 1

context:
  purpose: "Make DEVICE_LIST slot text and signal bars fully legible and use the unused band below the title."
  integration: "Three source files and one test module; single caller per changed function."
  knowledge_references:
    - "ai/workspace/issues/issue-d38362aa-device-list-slot-legibility.md"
    - "ai/workspace/change/change-d38362aa-device-list-slot-legibility.md (section 2 holds every target value)"
  constraints:
    - "CRITICAL: use exactly the values in change-d38362aa section 2. They were validated by an on-device render; do not re-derive or tune them."
    - "Do not change Back/Retry, the title, the down arrow, slot colours, borders, selection tint, empty-slot frame style, focus/swipe/touch behaviour, get_signal_bars thresholds or typography constants."
    - "Do not touch any other setup screen."
    - "Python 3.9+; PEP 8; formatted with black."

specification:
  description: "Resize and reposition the three-slot column and redesign the slot interior."
  requirements:
    functional:
      - "calculate_focused_slot_layout() with defaults returns slots at y=118, 188, 258, height 60, scale 1.0, opacity 1.0; middle centre y=218."
      - "Each slot surface shows name (24 px) and type (20 px) without clipping, and four signal bars on the right."
      - "No dBm text is rendered."
      - "Up arrow occupies y=102-114; DEVICE_LIST error line is centred at y=84 and fitted to 220 px."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Docstrings and comments updated to the new geometry, citing change-d38362aa."
  performance:
    - target: "DEVICE_LIST slot render time"
      metric: "No regression; the interior no longer allocates per-element alpha surfaces for scaled text."

design:
  architecture: "Unchanged component structure."
  components:
    - name: "CircularPositioningEngine.calculate_focused_slot_layout"
      type: "method"
      purpose: "Fixed three-slot geometry."
      logic:
        - "Signature: calculate_focused_slot_layout(self, item_height: int = 60, item_spacing: int = 10, column_centre_y: int = 218)."
        - "middle_y = column_centre_y - item_height // 2; slots at middle_y - pitch, middle_y, middle_y + pitch."
        - "Width and x still come from _calculate_curved_geometry (measured against display_center); after that call set layout_item['scale'] = 1.0 and layout_item['opacity'] = 1.0."
        - "The exception fallback uses the same column_centre_y and scale/opacity 1.0."
        - "Docstring: replace 'middle slot centred on the display' with the column centre rationale (column moved up into the band below the title)."
    - name: "DeviceSurfaceRenderer.create_curved_device_surface"
      type: "method"
      purpose: "Slot interior per change-d38362aa section 2."
      logic:
        - "Add class constants for the interior: TEXT_LEFT=24, NAME_Y=0, TYPE_Y=27, TYPE_DOT_X=14, TYPE_DOT_RADIUS=6, NAME_RIGHT_RESERVE=79, BAR_COUNT=4, BAR_WIDTH=5, BAR_GAP=3, BAR_BASE_HEIGHT=8, BAR_STEP=6, BAR_RIGHT_INSET=14."
        - "Add colour keys 'signal_lit': (220, 220, 220) and 'signal_unlit': (110, 110, 125)."
        - "Background and selected border: unchanged (bg rect height = surface height - 2)."
        - "Type dot at (TYPE_DOT_X, bg_height // 2)."
        - "Name: FONT_BODY via get_font_manager().get_font, truncated to item_width - NAME_RIGHT_RESERVE, colour colors['text'], blit at (TEXT_LEFT, NAME_Y)."
        - "Type: FONT_SMALL_TEXT, colour colors['text_dim'], blit at (TEXT_LEFT, TYPE_Y)."
        - "Bars (only when signal_strength is not None): block width = 4*5 + 3*3 = 29; left x = item_width - BAR_RIGHT_INSET - 29; bottom y = bg_height // 2 + 13; bar i height = 8 + 6*i, x = left + i*(BAR_WIDTH + BAR_GAP); lit when i < get_signal_bars(rssi)."
        - "Delete the dBm text block."
        - "scale_factor and opacity_factor are 1.0 for DEVICE_LIST; remove scaling arithmetic that no longer has a caller, keeping the cache key and touch-rect behaviour."
    - name: "SetupDisplayManager"
      type: "class"
      purpose: "Arrow band and error line."
      logic:
        - "_ARROW_UP_BASE_Y = 114 (was 154); _ARROW_DOWN_BASE_Y unchanged (322); update the constants comment block (column y=118-318)."
        - "_render_device_list_screen: error text = self._fit_text(font_minimal, state.error_message, max_width=220); centre (240, 84); update its comment."

data_schema:
  entities: []

error_handling:
  strategy: "Unchanged; existing try/except and fallback surfaces retained."
  exceptions: []
  logging:
    level: "Unchanged"
    format: "Unchanged"

testing:
  unit_tests:
    - scenario: "tests/test_device_list_focus.py: replace test_middle_slot_is_centred_on_the_display with a test that the middle slot centre is y=218 (default column_centre_y)."
      expected: "Pass."
    - scenario: "New: slots have y=(118, 188, 258), height 60, scale 1.0, opacity 1.0."
      expected: "Pass."
    - scenario: "TestArrowGlyphs.UP_POINT becomes (240, 108); DOWN_POINT stays (240, 328)."
      expected: "Pass."
    - scenario: "test_the_region_rect_covers_the_middle_slot: assert rect.centery approx 218 (abs = height // 2)."
      expected: "Pass."
    - scenario: "New: a strong-signal device (RSSI -35) slot surface contains signal_lit pixels in the bar block; a -90 device contains signal_unlit and no signal_lit pixels there."
      expected: "Pass."
    - scenario: "New: the slot surface height equals 60 and the type label's rendered height fits (TYPE_Y + font height of FONT_SMALL_TEXT ≤ surface height)."
      expected: "Pass."
    - scenario: "Module docstring updated: slots no longer centred on the display."
      expected: "n/a"
  edge_cases:
    - "Device with signal_strength None: no bars drawn, no error."
    - "Empty slot frames keep the populated footprint (existing test)."
  validation:
    - "pytest tests/ passes; report pass/fail counts."
    - "git diff --stat lists only the three source files and tests/test_device_list_focus.py."

deliverable:
  format_requirements:
    - "Edit files in place."
    - "Write a companion report to ai/workspace/report/report-d38362aa-device-list-slot-legibility.md."
  files:
    - path: "src/gtach/display/setup_components/layout/circular_positioning.py"
      content: "calculate_focused_slot_layout changes"
    - path: "src/gtach/display/setup_components/rendering/device_surfaces.py"
      content: "Slot interior redesign"
    - path: "src/gtach/display/setup.py"
      content: "Arrow constant, error line"
    - path: "tests/test_device_list_focus.py"
      content: "Updated and new tests"

success_criteria:
  - "All change-d38362aa section 2 values are present in source."
  - "grep -n 'dBm' src/gtach/display/setup_components/rendering/device_surfaces.py returns nothing."
  - "pytest tests/ passes."
  - "Human verification on the Pi passes (see notes)."

element_registry:
  source: ""
  entries:
    modules: []
    classes:
      - name: "DeviceSurfaceRenderer"
        module: "gtach.display.setup_components.rendering.device_surfaces"
    functions:
      - name: "calculate_focused_slot_layout"
        module: "gtach.display.setup_components.layout.circular_positioning.CircularPositioningEngine"
        signature: "calculate_focused_slot_layout(self, item_height: int = 60, item_spacing: int = 10, column_centre_y: int = 218) -> List[Dict[str, Any]]"
      - name: "create_curved_device_surface"
        module: "gtach.display.setup_components.rendering.device_surfaces.DeviceSurfaceRenderer"
        signature: "unchanged"
    constants:
      - name: "SetupDisplayManager._ARROW_UP_BASE_Y"
        value: "114"

notes: >
  Human verification on the Pi: with the emulator and at least one other
  device discovered, name and type are fully visible in all three slots;
  lit and unlit bars are distinguishable in selected and unselected
  slots; no dBm text; trigger 'OBD check failed' and confirm the error
  line sits between the title and the up arrow.
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-16 | Initial prompt implementing change-d38362aa iteration 1. Target profile claude_code. |

---

Copyright (c) 2026 William Watson. MIT License.
