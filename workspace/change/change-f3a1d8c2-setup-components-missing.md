Created: 2026 May 06

# Change: Create setup_components Subpackage Implementations

---

## Table of Contents

- [1.0 Change Info](<#1.0 change info>)
- [2.0 Source](<#2.0 source>)
- [3.0 Scope](<#3.0 scope>)
- [4.0 Rationale](<#4.0 rationale>)
- [5.0 Technical Details](<#5.0 technical details>)
- [6.0 Testing Requirements](<#6.0 testing requirements>)
- [7.0 Verification](<#7.0 verification>)
- [Version History](<#version history>)

---

## 1.0 Change Info

```yaml
change_info:
  id: "change-f3a1d8c2"
  title: "Create setup_components subpackage implementations"
  date: "2026-05-06"
  author: "William Watson"
  status: "approved"
  priority: "critical"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-f3a1d8c2"
    issue_iteration: 1
```

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Source

```yaml
source:
  type: "issue"
  reference: "issue-f3a1d8c2"
  description: >
    Four component module files referenced by setup.py do not
    exist. ModuleNotFoundError prevents application startup.
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Scope

```yaml
scope:
  summary: >
    Create nine new files: four subpackage __init__.py files
    and four component implementation files under
    src/gtach/display/setup_components/.
  affected_components:
    - name: "bluetooth package"
      file_path: "src/gtach/display/setup_components/bluetooth/__init__.py"
      change_type: "add"
    - name: "BluetoothSetupInterface"
      file_path: "src/gtach/display/setup_components/bluetooth/interface.py"
      change_type: "add"
    - name: "layout package"
      file_path: "src/gtach/display/setup_components/layout/__init__.py"
      change_type: "add"
    - name: "CircularPositioningEngine"
      file_path: "src/gtach/display/setup_components/layout/circular_positioning.py"
      change_type: "add"
    - name: "rendering package"
      file_path: "src/gtach/display/setup_components/rendering/__init__.py"
      change_type: "add"
    - name: "DeviceSurfaceRenderer"
      file_path: "src/gtach/display/setup_components/rendering/device_surfaces.py"
      change_type: "add"
    - name: "state package"
      file_path: "src/gtach/display/setup_components/state/__init__.py"
      change_type: "add"
    - name: "SetupStateCoordinator"
      file_path: "src/gtach/display/setup_components/state/coordinator.py"
      change_type: "add"
  out_of_scope:
    - "setup.py — no changes required"
    - "app.py — no changes required"
    - "setup_original_backup.py — not modified or removed"
    - "RPM colour bands, sim mode, watchdog fixes"
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Rationale

```yaml
rational:
  problem_statement: >
    setup.py imports BluetoothSetupInterface, CircularPositioningEngine,
    DeviceSurfaceRenderer, and SetupStateCoordinator from setup_components/
    subpackages that have no implementation files. The application
    cannot start in setup mode.
  proposed_solution: >
    Create the four component files with implementations that satisfy
    the interface contracts consumed by setup.py. Implementations
    must be functional — not stubs — so that setup mode renders
    correctly on both macOS and Pi.
  benefits:
    - "Unblocks setup mode entry"
    - "Unblocks all downstream roadmap steps (4.1–4.4)"
    - "Preserves the refactored component architecture of setup.py"
  risks:
    - risk: "Component implementations diverge from what setup.py expects"
      mitigation: >
        Interface contracts are fully specified in issue-f3a1d8c2
        analysis.technical_notes. Claude Code must implement exactly
        those signatures and return types.
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Technical Details

```yaml
technical_details:
  current_behavior: >
    ImportError / ModuleNotFoundError at startup. setup_components/
    contains only __init__.py.
  proposed_behavior: >
    All four components importable. SetupDisplayManager initialises
    and renders WELCOME screen. Setup flow (WELCOME → DISCOVERY →
    DEVICE_LIST → PAIRING → COMPLETE) operates correctly.
  implementation_approach: >
    Each component is a single class in its own module.
    BluetoothSetupInterface wraps the existing system_bluetooth /
    pairing subsystem (or pairing_factory if provided).
    CircularPositioningEngine provides layout geometry for the
    curved device list. DeviceSurfaceRenderer creates pygame
    surfaces for individual device list items.
    SetupStateCoordinator manages SetupState, screen transitions,
    callbacks, and animation timing.

  code_changes:
    - component: "BluetoothSetupInterface"
      file: "src/gtach/display/setup_components/bluetooth/interface.py"
      change_summary: >
        Class with pairing_factory constructor parameter.
        Wraps async Bluetooth discovery and pairing operations.
        Delegates to pairing_factory() if provided, otherwise
        uses system Bluetooth (pairing.py / system_bluetooth.py).
      functions_affected:
        - "__init__(self, pairing_factory=None)"
        - "cancel_operations(self) -> None"
        - "get_active_operation_progress(self) -> dict"
        - "start_discovery(self, state, show_all_devices=False) -> None"
        - "start_pairing(self, device, state) -> None"

    - component: "CircularPositioningEngine"
      file: "src/gtach/display/setup_components/layout/circular_positioning.py"
      change_summary: >
        Pure geometry class. calculate_curved_list_layout returns
        a list of dicts describing position and scale for each
        item in a vertically-scrolling curved list on a 480x480
        circular display.
      functions_affected:
        - "__init__(self)"
        - "calculate_curved_list_layout(self, count: int, start_y: int) -> list"

    - component: "DeviceSurfaceRenderer"
      file: "src/gtach/display/setup_components/rendering/device_surfaces.py"
      change_summary: >
        Renders a single Bluetooth device entry as a pygame Surface
        suitable for blitting into the device list screen.
      functions_affected:
        - "__init__(self)"
        - "create_curved_device_surface(self, device, layout_item, index) -> Tuple[pygame.Surface | None, pygame.Rect]"

    - component: "SetupStateCoordinator"
      file: "src/gtach/display/setup_components/state/coordinator.py"
      change_summary: >
        Owns SetupState. Manages screen transitions, state change
        callbacks, animation time, and action dispatch.
      functions_affected:
        - "__init__(self)"
        - "register_screen_transition_callback(self, cb) -> None"
        - "register_state_change_callback(self, cb) -> None"
        - "get_state(self) -> SetupState"
        - "transition_to_screen(self, screen: SetupScreen) -> None"
        - "handle_setup_action(self, action: SetupAction, **kwargs) -> None"
        - "update_animation(self, dt: float) -> None"
        - "register_interaction(self) -> None"
      classes_affected:
        - "SetupStateCoordinator"
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Testing Requirements

```yaml
testing_requirements:
  test_approach: "Import verification then runtime smoke test"
  test_cases:
    - scenario: "Import all four component classes"
      expected_result: "No ImportError or ModuleNotFoundError"
    - scenario: "Instantiate SetupDisplayManager"
      expected_result: "No exception during __init__"
    - scenario: "Run gtach --macos --debug with no paired device"
      expected_result: "WELCOME screen renders; no crash"
  validation_criteria:
    - "python -c \"from gtach.display.setup import SetupDisplayManager\" exits 0"
    - "python -m gtach --macos --debug reaches WELCOME screen"
```

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Verification

```yaml
verification:
  implemented_date: ""
  implemented_by: ""
  verification_date: ""
  verified_by: ""
  test_results: ""
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-05-06 | Initial filing |

---

Copyright (c) 2026 William Watson. MIT License.
