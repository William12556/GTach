Created: 2026 August 19

# Prompt: Focused-index Device List Rendering

---

## 1.0 Table of Contents

- [1.0 Table of Contents](<#1.0 table of contents>)
- [2.0 Prompt Record](<#2.0 prompt record>)
- [Version History](<#version history>)

---

## 2.0 Prompt Record

```yaml
prompt_info:
  id: "prompt-479b2e51"
  task_type: "refactor"
  source_ref: "change-479b2e51"
  target_profile: "claude_code"
  date: "2026-08-19"
  iteration: 1
  coupled_docs:
    change_ref: "change-479b2e51"
    change_iteration: 1

context:
  purpose: >
    Replace the unbounded Device List (Select Device) screen with a
    fixed 3-slot, focused-index layout: only the centred slot is
    selectable, empty slots render as outlined frames, and swipe
    gestures shift focus by one device.
  integration: >
    Setup mode display flow (SetupDisplayManager, HyperPixel 2.1
    Round 480x480 framebuffer, SDL_VIDEODRIVER=dummy). Runs on
    Debian GNU/Linux 11 (Bullseye), Python 3.11, pygame 2.6.1.
  knowledge_references:
    - "ai/workspace/design/design-a3b4c5d6-component_display_setup_manager.md"
    - "ai/workspace/issues/issue-479b2e51-device-list-pagination.md"
    - "ai/workspace/change/change-479b2e51-device-list-pagination.md"
  constraints:
    - "Must run within existing component architecture (SetupDisplayManager, CircularPositioningEngine, DeviceSurfaceRenderer, SetupStateCoordinator) — no new top-level modules."
    - "scroll_offset/max_scroll fields in SetupStateCoordinator are confirmed to have no consumers outside that class (mcp-ripgrep verified 2026-08-19); safe to repurpose as focused_index semantics, field name may be kept or renamed at implementer's discretion."
    - "All slot positions (populated and empty) must remain within the circular safe area already enforced by CircularPositioningEngine.validate_circular_bounds."
    - "Do not alter WELCOME, DISCOVERY, PAIRING, COMPLETE, CURRENT_DEVICE, or manual-entry screens."
    - "Do not alter device discovery, filtering, or pairing logic."
    - "Background/text colours for the Device List screen (pale dusty-yellow background, black text) must be unchanged outside the new slot indicators."

specification:
  description: >
    Modify the DEVICE_LIST screen so that exactly 3 vertical slot
    positions are always rendered, centred on the display
    (display_center = (240, 240)). A single focused_index (0-based
    into state.discovered_devices) determines slot contents: middle
    slot = discovered_devices[focused_index]; top slot =
    discovered_devices[focused_index - 1] if it exists, else an
    empty outlined frame; bottom slot =
    discovered_devices[focused_index + 1] if it exists, else an
    empty outlined frame. Only the middle slot is a registered touch
    region and is rendered with an accent border plus background
    tint distinguishing it as selectable. A vertical swipe on the
    DEVICE_LIST screen shifts focused_index by ±1, clamped to
    [0, len(discovered_devices) - 1]. An up-arrow glyph is drawn
    above the slot column when focused_index > 0; a down-arrow glyph
    is drawn below when focused_index < len(discovered_devices) - 1.
    With 0 discovered devices, retain the existing "No devices
    found" message and draw no slots or arrows.
  requirements:
    functional:
      - "Exactly 3 slot positions are always computed for DEVICE_LIST, independent of discovered device count."
      - "Only the middle slot is touch-selectable; tapping it triggers the existing SELECT_DEVICE action flow (SetupAction.SELECT_DEVICE / start_pairing), unchanged."
      - "Top and bottom slots are display-only; no touch region is registered for them."
      - "Empty slots (no device at that relative position) render as an outlined frame, matching the populated slot's footprint."
      - "The middle slot carries a border plus background tint distinguishing it from top/bottom slots, whether populated or empty."
      - "A vertical swipe gesture on DEVICE_LIST shifts focused_index by exactly 1 per swipe, clamped to [0, len(discovered_devices) - 1]; swipes beyond either bound are no-ops."
      - "Horizontal swipes and long-press on DEVICE_LIST retain their existing (no-op / unhandled) behaviour — do not introduce new handling for them."
      - "Up-arrow shown iff focused_index > 0; down-arrow shown iff focused_index < len(discovered_devices) - 1; both hidden when discovered_devices is empty."
      - "focused_index resets to 0 whenever reset_discovery() runs or the screen is (re-)entered via transition_to_screen(DEVICE_LIST)."
      - "Back and Retry buttons on DEVICE_LIST keep their current position, size, and behaviour."
    technical:
      language: "Python"
      version: "3.11"
      standards:
        - "Thread-safe if concurrent access"
        - "Comprehensive error handling"
        - "Debug logging with traceback"
        - "Professional docstrings"
  performance:
    - target: "Render frame time for DEVICE_LIST"
      metric: "No regression versus current unbounded-list render time"

design:
  architecture: >
    Extend the existing component-delegation pattern
    (SetupDisplayManager delegates layout to CircularPositioningEngine
    and device surface creation to DeviceSurfaceRenderer, state to
    SetupStateCoordinator). No new classes required; extend existing
    methods and add narrowly-scoped new ones.
  components:
    - name: "SetupStateCoordinator"
      type: "class"
      purpose: "Track and clamp the focused device index for DEVICE_LIST"
      interface:
        inputs:
          - name: "offset"
            type: "int"
            description: "Requested focused index shift target (existing update_scroll_offset signature, semantics repurposed)"
        outputs:
          type: "None"
          description: "Updates internal focused-index state, clamped to valid range"
        raises: []
      logic:
        - "On transition_to_screen(DEVICE_LIST) and on reset_discovery(), clamp/reset focused index to 0 (or to len(discovered_devices)-1 if that is less)."
        - "Provide a method to shift focused index by a signed delta (e.g. +1/-1), clamped to [0, max(0, len(discovered_devices)-1)]."
        - "Existing get_scroll_info() may be extended or repurposed to expose the focused index and whether prev/next devices exist."
    - name: "CircularPositioningEngine"
      type: "class"
      purpose: "Compute 3 fixed slot rects centred on display_center"
      interface:
        inputs:
          - name: "item_height"
            type: "int"
            description: "Slot height, consistent with existing curved-list item sizing"
        outputs:
          type: "List[Dict[str, Any]]"
          description: "3 slot layout entries (top, middle, bottom) with x, y, width, height, and any scale/opacity fields consumed downstream"
        raises: []
      logic:
        - "Add a method (or adapt calculate_curved_list_layout) that always returns exactly 3 positions, vertically centred on display_center, independent of discovered_devices length."
        - "Middle slot's vertical centre must align with display_center[1] (240)."
        - "Preserve existing curved x-offset/width-narrowing behaviour used elsewhere on this screen, applied identically to all 3 slots regardless of which are populated."
    - name: "DeviceSurfaceRenderer"
      type: "class"
      purpose: "Render a populated device slot with an optional selected-state indicator, or an empty outlined frame"
      interface:
        inputs:
          - name: "device"
            type: "Optional[BluetoothDevice]"
            description: "Device to render, or None for an empty slot"
          - name: "layout_item"
            type: "Dict[str, Any]"
            description: "Slot rect/scale data from CircularPositioningEngine"
          - name: "selected"
            type: "bool"
            description: "True only for the middle slot; adds border + background tint"
        outputs:
          type: "Tuple[pygame.Surface, Optional[pygame.Rect]]"
          description: "Rendered surface and its touch rect (None touch rect for non-selectable slots, i.e. any slot where selected is False)"
        raises: []
      logic:
        - "When device is None, render an outlined empty frame matching the slot footprint; no device text/signal content."
        - "When device is provided and selected is True, render existing device content plus an accent border and background tint."
        - "When device is provided and selected is False, render existing device content with no selection indicator and no touch rect."
    - name: "SetupDisplayManager._render_device_list_screen"
      type: "function"
      purpose: "Orchestrate the 3-slot render and touch region registration for DEVICE_LIST"
      interface:
        inputs:
          - name: "surface"
            type: "pygame.Surface"
            description: "Target render surface"
          - name: "state"
            type: "SetupState"
            description: "Current setup state, including discovered_devices"
        outputs:
          type: "None"
          description: "Renders to surface and updates touch regions via _update_touch_regions_safe"
        raises: []
      logic:
        - "Retrieve focused_index and discovered_devices from state/coordinator."
        - "Compute the 3 slot layout via the CircularPositioningEngine method above."
        - "For each slot, resolve device-or-None (focused_index-1, focused_index, focused_index+1) and call DeviceSurfaceRenderer with selected=True only for the middle slot."
        - "Register a touch region only for the middle slot, mirroring the existing (\"device\", touch_rect, device) tuple shape consumed by _handle_touch_action."
        - "Draw up-arrow glyph when focused_index > 0; down-arrow when focused_index < len(discovered_devices) - 1; suppress both when discovered_devices is empty."
        - "Preserve existing 'No devices found' message path when discovered_devices is empty."
        - "Preserve existing Back/Retry button rendering and touch regions unchanged."
    - name: "SetupDisplayManager (new swipe handler)"
      type: "function"
      purpose: "Shift focused_index by ±1 in response to a vertical swipe on DEVICE_LIST"
      interface:
        inputs:
          - name: "direction"
            type: "int"
            description: "+1 for swipe down (advance focus), -1 for swipe up (retreat focus)"
        outputs:
          type: "None"
          description: "Updates focused index via SetupStateCoordinator and invalidates the DEVICE_LIST render cache"
        raises: []
      logic:
        - "No-op if current screen is not DEVICE_LIST."
        - "Delegate clamped index shift to SetupStateCoordinator."
        - "Invalidate render cache for DEVICE_LIST so the next render reflects the new focus."
    - name: "TouchHandler._process_touch / _handle_setup_touch"
      type: "function"
      purpose: "Detect vertical swipe distance on DEVICE_LIST before falling through to tap dispatch"
      interface:
        inputs:
          - name: "x, y, start_x, start_y"
            type: "int"
            description: "Touch end and start coordinates, as already captured by _process_touch"
        outputs:
          type: "Optional[SetupAction]"
          description: "None when a swipe was consumed; otherwise existing tap-dispatch return value"
        raises: []
      logic:
        - "When display_manager.is_in_setup_mode() and the current setup screen is DEVICE_LIST, compute dy (and dx) between start and end position before calling handle_touch_event."
        - "Use the same swipe distance threshold convention as the non-setup path (TouchHandler._handle_short_press's swipe_threshold lookup) for consistency."
        - "If |dy| >= threshold and |dy| >= |dx| (dominant vertical movement), call the new SetupDisplayManager swipe handler with direction sign(dy) instead of dispatching a tap, and return without calling handle_touch_event."
        - "Otherwise, fall through to the existing tap dispatch (handle_touch_event) unchanged."
        - "Do not alter behaviour for any other setup screen (WELCOME, DISCOVERY, PAIRING, COMPLETE, CURRENT_DEVICE, manual entry)."
  dependencies:
    internal:
      - "src/gtach/display/setup_models.py (SetupScreen, SetupState, BluetoothDevice — no changes expected)"
    external: []

data_schema:
  entities: []

error_handling:
  strategy: >
    Match existing SetupDisplayManager/TouchHandler convention:
    wrap render and touch-handling logic in try/except, log via
    self.logger.error with exc_info where applicable, and fail safe
    (e.g. treat malformed focus state as focused_index=0) rather than
    raising into the render/touch loop.
  exceptions:
    - exception: "IndexError"
      condition: "focused_index out of range of discovered_devices due to a race with device list mutation"
      handling: "Clamp defensively before indexing; log a warning if clamping was required"
  logging:
    level: "DEBUG"
    format: "Match existing logger.debug/info/warning/error usage in setup.py and touch.py"

testing:
  unit_tests:
    - scenario: "0 discovered devices"
      expected: "'No devices found' message; no slots, no arrows, no touch regions besides Back/Retry"
    - scenario: "1 discovered device"
      expected: "Middle slot populated and selected-indicated; top and bottom are empty frames; no arrows"
    - scenario: "2 discovered devices, focused_index=0"
      expected: "Middle=device0 (selected), bottom=device1, top=empty frame; down-arrow only"
    - scenario: "Swipe down at focused_index=0 with 2 devices"
      expected: "focused_index becomes 1; middle=device1 (selected), top=device0, bottom=empty frame; up-arrow only"
    - scenario: "5 discovered devices, focused_index=2"
      expected: "Middle=device2 (selected), top=device1, bottom=device3; both arrows shown"
    - scenario: "Swipe up at focused_index=0"
      expected: "No change (clamped)"
    - scenario: "Swipe down at focused_index=len(devices)-1"
      expected: "No change (clamped)"
    - scenario: "Tap middle slot"
      expected: "SELECT_DEVICE action fires for the focused device; pairing proceeds as today"
    - scenario: "Tap top or bottom slot position"
      expected: "No action (no touch region registered there)"
  edge_cases:
    - "discovered_devices mutates (new device found) while focused_index would go out of range — must clamp rather than raise"
    - "Rapid successive swipes near a bound"
  validation:
    - "All rendered slot rects (populated or empty) pass CircularPositioningEngine.validate_circular_bounds"
    - "Exactly one entry with a non-None touch rect exists in touch_regions for DEVICE_LIST when discovered_devices is non-empty"

deliverable:
  format_requirements:
    - "Save generated code directly to specified paths"
    - "Execute pytest suite for affected test paths on completion; report pass/fail summary"
  files:
    - path: "src/gtach/display/setup.py"
      content: "Modified _render_device_list_screen; new swipe-focus handler method"
    - path: "src/gtach/display/setup_components/layout/circular_positioning.py"
      content: "New or adapted method computing 3 fixed, display-centred slot positions"
    - path: "src/gtach/display/setup_components/rendering/device_surfaces.py"
      content: "Selected-state border/tint rendering and empty-frame rendering path"
    - path: "src/gtach/display/setup_components/state/coordinator.py"
      content: "Focused-index tracking, repurposing scroll_offset/max_scroll; clamp on DEVICE_LIST entry and reset_discovery()"
    - path: "src/gtach/display/touch.py"
      content: "Swipe-distance detection scoped to DEVICE_LIST in setup mode, prior to tap dispatch"

success_criteria:
  - "DEVICE_LIST always renders exactly 3 slot positions, centred on the display, regardless of discovered device count (0 excepted, which retains the existing message)."
  - "Only the middle slot is touch-selectable and is visually distinguished by border plus tint."
  - "Empty slots render as outlined frames of the same footprint as populated slots."
  - "A vertical swipe on DEVICE_LIST shifts focus by exactly 1 device, clamped correctly at both bounds."
  - "Arrow glyphs appear/disappear strictly according to whether a previous/next device exists, not a fixed count threshold."
  - "No change in behaviour on WELCOME, DISCOVERY, PAIRING, COMPLETE, CURRENT_DEVICE, or manual-entry screens."
  - "No change in Back/Retry button behaviour on DEVICE_LIST."
  - "All slot layouts, populated or empty, remain within the circular safe area."
  - "Existing pytest suite passes; any new tests for the above scenarios pass."

notes: >
  target_profile is claude_code; tactical_brief is not required and is
  omitted. William executes this prompt directly via Claude Code.
  Verification of final pixel positioning and touch-region accuracy
  must be performed on-device at root@gtach.local
  (/opt/gtach/venv/bin/python3, SDL_VIDEODRIVER=dummy), not on macOS,
  per project convention.

version_history:
  - version: "1.0"
    date: "2026-08-19"
    author: "Claude"
    changes:
      - "Initial prompt creation from change-479b2e51 (focused-index model, iteration 1)"

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.11"
  schema_type: "t04_prompt"
```

[Return to Table of Contents](<#1.0 table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-19 | Initial prompt creation |

---

Copyright (c) 2026 William Watson. MIT License.
