Created: 2026 May 06

# Issue: setup_components Subpackage Files Missing

---

## Table of Contents

- [1.0 Issue Info](<#1.0 issue info>)
- [2.0 Source](<#2.0 source>)
- [3.0 Affected Scope](<#3.0 affected scope>)
- [4.0 Reproduction](<#4.0 reproduction>)
- [5.0 Behavior](<#5.0 behavior>)
- [6.0 Environment](<#6.0 environment>)
- [7.0 Analysis](<#7.0 analysis>)
- [8.0 Resolution](<#8.0 resolution>)
- [9.0 Verification](<#9.0 verification>)
- [Version History](<#version history>)

---

## 1.0 Issue Info

```yaml
issue_info:
  id: "issue-f3a1d8c2"
  title: "setup_components subpackage files missing — ImportError on setup mode entry"
  date: "2026-05-06"
  reporter: "William Watson"
  status: "open"
  severity: "critical"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-f3a1d8c2"
    change_iteration: 1
```

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Source

```yaml
source:
  origin: "code_review"
  description: >
    Discovered during Step 1 of display restoration roadmap
    (knowledge-display-restoration-roadmap.md §6.0).
    setup.py imports four component classes from setup_components/
    subpackages that do not exist on disk. app.py imports
    SetupDisplayManager from setup.py at module level, causing
    ImportError whenever setup mode is entered.
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Affected Scope

```yaml
affected_scope:
  components:
    - name: "SetupDisplayManager"
      file_path: "src/gtach/display/setup.py"
    - name: "BluetoothSetupInterface (missing)"
      file_path: "src/gtach/display/setup_components/bluetooth/interface.py"
    - name: "CircularPositioningEngine (missing)"
      file_path: "src/gtach/display/setup_components/layout/circular_positioning.py"
    - name: "DeviceSurfaceRenderer (missing)"
      file_path: "src/gtach/display/setup_components/rendering/device_surfaces.py"
    - name: "SetupStateCoordinator (missing)"
      file_path: "src/gtach/display/setup_components/state/coordinator.py"
    - name: "GTachApplication"
      file_path: "src/gtach/app.py"
  version: "current"
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Reproduction

```yaml
reproduction:
  prerequisites: "GTach installed from wheel or run from source"
  steps:
    - "Run: python -m gtach --macos --debug"
    - "Application enters setup mode (no paired device present)"
  frequency: "always"
  reproducibility_conditions: >
    Occurs on every startup where setup mode is required.
    Also occurs on any startup because app.py imports
    SetupDisplayManager at module level — the ImportError
    fires before main() is reached.
  error_output: |
    ModuleNotFoundError: No module named
    'gtach.display.setup_components.bluetooth'
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Behavior

```yaml
behavior:
  expected: >
    setup_components/ subpackages exist and are importable.
    SetupDisplayManager initialises successfully. Setup mode
    renders the WELCOME screen.
  actual: >
    Four subpackage module files are absent. Only
    setup_components/__init__.py exists. Import fails at
    app.py module load time with ModuleNotFoundError.
  impact: >
    Setup mode is completely non-functional. Any startup
    requiring setup (no paired device) crashes at import.
  workaround: "None — import failure is fatal at module load."
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Environment

```yaml
environment:
  python_version: "3.11"
  os: "macOS (development), Raspberry Pi OS (deployment)"
  dependencies:
    - library: "pygame"
      version: "2.6.1"
```

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Analysis

```yaml
analysis:
  root_cause: >
    setup.py was refactored to a component-based architecture.
    The four component implementation files were never created.
    setup_original_backup.py is the prior implementation but
    also references missing files (under .setup.bluetooth.*
    paths) and cannot serve as a drop-in replacement.
    Both files require the same four component classes;
    only the import path prefix differs.
  technical_notes: >
    Required components and their consumed interfaces as called
    by setup.py:

    BluetoothSetupInterface(pairing_factory=None):
      - cancel_operations() -> None
      - get_active_operation_progress() -> dict with keys:
          has_active_operations: bool
          progress: float (0.0–1.0)
          message: str
      - start_discovery(state, show_all_devices=False) -> None
      - start_pairing(device, state) -> None

    CircularPositioningEngine():
      - calculate_curved_list_layout(count, start_y) -> list of dicts:
          each dict: {x, y, width, height, scale}

    DeviceSurfaceRenderer():
      - create_curved_device_surface(device, layout_item, index)
          -> Tuple[pygame.Surface | None, pygame.Rect]

    SetupStateCoordinator():
      - register_screen_transition_callback(cb) -> None
      - register_state_change_callback(cb) -> None
      - get_state() -> SetupState
      - transition_to_screen(screen: SetupScreen) -> None
      - handle_setup_action(action: SetupAction, **kwargs) -> None
      - update_animation(dt: float) -> None
      - register_interaction() -> None
      - animation_time: float  (attribute)
      - show_all_devices: bool  (attribute)
      - manual_entry_mode: bool  (attribute)

    SetupStateCoordinator callbacks fired:
      _on_screen_transition(old_screen, new_screen)
      _on_state_change(changed_fields: List[str])

    SetupState fields used by setup.py render methods:
      current_screen: SetupScreen
      pairing_status: PairingStatus
      discovered_devices: list
      selected_device: BluetoothDevice | None
      error_message: str | None
      setup_complete: bool
  related_issues: []
```

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Resolution

```yaml
resolution:
  assigned_to: "Claude Code"
  approach: >
    Create the four missing component files under
    setup_components/ with implementations sufficient for
    setup.py to import and operate correctly.
    Also create __init__.py files for each new subpackage.
  change_ref: "change-f3a1d8c2"
```

[Return to Table of Contents](<#table of contents>)

---

## 9.0 Verification

```yaml
verification_enhanced:
  verification_steps:
    - "python -c \"import sys; sys.path.insert(0,'src'); import gtach.display.setup; print('OK')\""
    - "python -c \"import sys; sys.path.insert(0,'src'); from gtach.display.setup import SetupDisplayManager; print('OK')\""
    - "python -m gtach --macos --debug  # confirm no ImportError at startup"
  verification_results: ""
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-05-06 | Initial filing |

---

Copyright (c) 2026 William Watson. MIT License.
