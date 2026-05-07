Created: 2026 May 06

# Prompt: Create setup_components Subpackage Implementations

---

## Table of Contents

- [1.0 Prompt Info](<#1.0 prompt info>)
- [2.0 Context](<#2.0 context>)
- [3.0 Specification](<#3.0 specification>)
- [4.0 Design](<#4.0 design>)
- [5.0 Deliverables](<#5.0 deliverables>)
- [6.0 Success Criteria](<#6.0 success criteria>)
- [7.0 Element Registry](<#7.0 element registry>)
- [8.0 Tactical Brief](<#8.0 tactical brief>)
- [Version History](<#version history>)

---

## 1.0 Prompt Info

```yaml
prompt_info:
  id: "prompt-f3a1d8c2"
  task_type: "code_generation"
  source_ref: "change-f3a1d8c2"
  date: "2026-05-06"
  iteration: 1
  coupled_docs:
    change_ref: "change-f3a1d8c2"
    change_iteration: 1
```

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Context

```yaml
context:
  purpose: >
    Create four missing component implementation files under
    src/gtach/display/setup_components/ so that SetupDisplayManager
    in setup.py can import and function correctly.
  integration: >
    setup.py imports these four classes at module level.
    app.py imports SetupDisplayManager from setup.py at module level.
    The application cannot start until these files exist.
    No changes to setup.py or app.py are required.
  knowledge_references:
    - "workspace/knowledge/knowledge-display-restoration-roadmap.md"
  constraints:
    - "Do not modify setup.py, app.py, or any existing file"
    - "Implement exactly the interface contracts specified in §4.0"
    - "All shared state must be protected by threading.Lock"
    - "Conditional pygame import: try/except ImportError"
    - "Python 3.9+ compatible"
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Specification

```yaml
specification:
  description: >
    Create nine files: four subpackage __init__.py files and four
    component implementation files. Each component is a single class.
  requirements:
    functional:
      - "BluetoothSetupInterface wraps BluetoothPairing with async threading"
      - "BluetoothSetupInterface accepts optional pairing_factory constructor param"
      - "CircularPositioningEngine calculates layout geometry for 480x480 display"
      - "DeviceSurfaceRenderer creates pygame Surfaces for device list items"
      - "SetupStateCoordinator owns and manages SetupState lifecycle"
      - "SetupStateCoordinator fires screen_transition and state_change callbacks"
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Thread-safe if concurrent access"
        - "Comprehensive error handling with logger.error(msg, exc_info=True)"
        - "Google-style docstrings"
        - "PEP 8, type hints on public interfaces"
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Design

```yaml
design:
  architecture: "Component pattern — one class per module"

  components:

    - name: "BluetoothSetupInterface"
      type: "class"
      purpose: >
        Wraps async Bluetooth discovery and pairing. If pairing_factory
        is provided (callable returning a pairing object), uses that;
        otherwise instantiates BluetoothPairing from comm/pairing.py.
      interface:
        inputs:
          - name: "pairing_factory"
            type: "Optional[Callable]"
            description: "Factory returning pairing object; None = use BluetoothPairing"
        methods:
          - "cancel_operations(self) -> None"
          - "get_active_operation_progress(self) -> dict"
          - "start_discovery(self, state: SetupState, show_all_devices: bool = False) -> None"
          - "start_pairing(self, device: BluetoothDevice, state: SetupState) -> None"
      logic:
        - "cancel_operations: set cancel event, join any running threads"
        - >
          get_active_operation_progress: return dict with keys
          has_active_operations (bool), progress (float 0.0-1.0),
          message (str). Return has_active_operations=False when idle.
        - >
          start_discovery: spawn daemon thread; call pairing object
          discover_devices(); populate state.discovered_devices;
          update state.pairing_status DISCOVERING -> IDLE on complete;
          update state.discovery_progress periodically.
        - >
          start_pairing: spawn daemon thread; call pairing object
          pair_device(device); set state.pairing_status to PAIRING,
          then SUCCESS or FAILED; set state.error_message on failure.

    - name: "CircularPositioningEngine"
      type: "class"
      purpose: "Pure geometry — layout positions for curved device list"
      interface:
        methods:
          - "calculate_curved_list_layout(self, count: int, start_y: int) -> List[dict]"
      logic:
        - >
          Return a list of dicts, one per item, each containing:
          x (int), y (int), width (int), height (int), scale (float).
          Display is 480x480. Items are centred horizontally.
          Items near list centre have scale=1.0; items at edges
          have scale reduced toward 0.8 to give curved perspective.
          Item height=50, width=300. Vertical spacing=60.
          x = (480 - width*scale) / 2, y = start_y + i*60.

    - name: "DeviceSurfaceRenderer"
      type: "class"
      purpose: "Renders a single device entry as a pygame Surface"
      interface:
        methods:
          - "create_curved_device_surface(self, device: BluetoothDevice, layout_item: dict, index: int) -> Tuple[Optional[pygame.Surface], pygame.Rect]"
      logic:
        - "Return (None, pygame.Rect(0,0,0,0)) if pygame unavailable"
        - >
          Create Surface of size (layout_item['width'], layout_item['height']).
          Fill with dark background (40,40,50). Draw border rect.
          Render device.name left-aligned; device.mac_address smaller,
          right-aligned. Apply scale via pygame.transform.scale if
          layout_item['scale'] < 1.0. Return (surface, touch_rect)
          where touch_rect covers the final blit position based on
          layout_item x/y/width/height.

    - name: "SetupStateCoordinator"
      type: "class"
      purpose: "Owns SetupState; manages transitions, callbacks, animation"
      interface:
        attributes:
          - "animation_time: float  (cumulative seconds, updated by update_animation)"
          - "show_all_devices: bool  (default False)"
          - "manual_entry_mode: bool  (default False)"
        methods:
          - "register_screen_transition_callback(self, cb: Callable) -> None"
          - "register_state_change_callback(self, cb: Callable) -> None"
          - "get_state(self) -> SetupState"
          - "transition_to_screen(self, screen: SetupScreen) -> None"
          - "handle_setup_action(self, action: SetupAction, **kwargs) -> None"
          - "update_animation(self, dt: float) -> None"
          - "register_interaction(self) -> None"
      logic:
        - >
          __init__: initialise SetupState(
            current_screen=SetupScreen.WELCOME,
            discovered_devices=[],
            selected_device=None,
            pairing_status=PairingStatus.IDLE,
            setup_complete=False
          ). animation_time=0.0, show_all_devices=False,
          manual_entry_mode=False. _state_lock = threading.Lock().
        - >
          transition_to_screen: under lock, record old screen,
          set state.current_screen = screen, fire all
          screen_transition callbacks(old, new).
        - >
          handle_setup_action dispatches on SetupAction enum:
          START_DISCOVERY -> transition_to_screen(DISCOVERY)
          SELECT_DEVICE(device=) -> set state.selected_device,
            transition_to_screen(PAIRING)
          NEXT -> advance to next logical screen
          BACK -> return to previous screen
          RETRY -> re-enter DISCOVERY
          CANCEL -> transition to WELCOME
          COMPLETE -> set state.setup_complete=True,
            transition_to_screen(COMPLETE)
        - "update_animation: animation_time += dt"
        - "register_interaction: no-op for now (hook for future idle timeout)"

  dependencies:
    internal:
      - "src/gtach/display/setup_models.py (SetupScreen, SetupState, SetupAction, PairingStatus, BluetoothDevice)"
      - "src/gtach/comm/pairing.py (BluetoothPairing)"
    external:
      - "pygame (conditional import)"
      - "threading (stdlib)"
      - "logging (stdlib)"
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Deliverables

```yaml
deliverable:
  format_requirements:
    - "Save generated code directly to specified paths"
    - "Create all parent directories as needed"
  files:
    - path: "src/gtach/display/setup_components/bluetooth/__init__.py"
      content: "Empty package init with copyright header"
    - path: "src/gtach/display/setup_components/bluetooth/interface.py"
      content: "BluetoothSetupInterface class"
    - path: "src/gtach/display/setup_components/layout/__init__.py"
      content: "Empty package init with copyright header"
    - path: "src/gtach/display/setup_components/layout/circular_positioning.py"
      content: "CircularPositioningEngine class"
    - path: "src/gtach/display/setup_components/rendering/__init__.py"
      content: "Empty package init with copyright header"
    - path: "src/gtach/display/setup_components/rendering/device_surfaces.py"
      content: "DeviceSurfaceRenderer class"
    - path: "src/gtach/display/setup_components/state/__init__.py"
      content: "Empty package init with copyright header"
    - path: "src/gtach/display/setup_components/state/coordinator.py"
      content: "SetupStateCoordinator class"
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Success Criteria

```yaml
success_criteria:
  - "All nine files exist on disk after implementation"
  - "python -c \"import sys; sys.path.insert(0,'src'); from gtach.display.setup import SetupDisplayManager; print('OK')\" exits 0 with no errors"
  - "python -c \"import ast; ast.parse(open('src/gtach/display/setup_components/bluetooth/interface.py').read())\" exits 0"
  - "python -c \"import ast; ast.parse(open('src/gtach/display/setup_components/layout/circular_positioning.py').read())\" exits 0"
  - "python -c \"import ast; ast.parse(open('src/gtach/display/setup_components/rendering/device_surfaces.py').read())\" exits 0"
  - "python -c \"import ast; ast.parse(open('src/gtach/display/setup_components/state/coordinator.py').read())\" exits 0"
```

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Element Registry

```yaml
element_registry:
  source: "N/A — new components, no prior registry entries"
  entries:
    modules:
      - name: "interface"
        path: "src/gtach/display/setup_components/bluetooth/interface.py"
      - name: "circular_positioning"
        path: "src/gtach/display/setup_components/layout/circular_positioning.py"
      - name: "device_surfaces"
        path: "src/gtach/display/setup_components/rendering/device_surfaces.py"
      - name: "coordinator"
        path: "src/gtach/display/setup_components/state/coordinator.py"
    classes:
      - name: "BluetoothSetupInterface"
        module: "interface"
      - name: "CircularPositioningEngine"
        module: "circular_positioning"
      - name: "DeviceSurfaceRenderer"
        module: "device_surfaces"
      - name: "SetupStateCoordinator"
        module: "coordinator"
```

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Tactical Brief

```yaml
tactical_brief: |
  Create 9 files under src/gtach/display/setup_components/.

  CONSTRAINT: Do not modify any existing file.

  FILES TO CREATE:
  1. bluetooth/__init__.py — empty, copyright header
  2. bluetooth/interface.py — BluetoothSetupInterface class
  3. layout/__init__.py — empty, copyright header
  4. layout/circular_positioning.py — CircularPositioningEngine class
  5. rendering/__init__.py — empty, copyright header
  6. rendering/device_surfaces.py — DeviceSurfaceRenderer class
  7. state/__init__.py — empty, copyright header
  8. state/coordinator.py — SetupStateCoordinator class

  INTERFACE CONTRACTS (must match exactly):

  BluetoothSetupInterface(pairing_factory=None):
    cancel_operations(self) -> None
    get_active_operation_progress(self) -> dict
      # keys: has_active_operations:bool, progress:float, message:str
    start_discovery(self, state, show_all_devices=False) -> None
    start_pairing(self, device, state) -> None
    # If pairing_factory provided, call pairing_factory() to get pairing obj
    # else instantiate BluetoothPairing from gtach.comm.pairing

  CircularPositioningEngine():
    calculate_curved_list_layout(self, count:int, start_y:int) -> List[dict]
      # each dict: {x:int, y:int, width:int, height:int, scale:float}
      # width=300, height=50, spacing=60, scale 1.0 at centre -> 0.8 at edges

  DeviceSurfaceRenderer():
    create_curved_device_surface(self, device, layout_item, index)
      -> Tuple[Optional[pygame.Surface], pygame.Rect]
      # Return (None, Rect(0,0,0,0)) if pygame unavailable
      # Surface: filled dark bg, device.name + mac_address text

  SetupStateCoordinator():
    # attributes: animation_time:float, show_all_devices:bool, manual_entry_mode:bool
    register_screen_transition_callback(self, cb) -> None
    register_state_change_callback(self, cb) -> None
    get_state(self) -> SetupState
    transition_to_screen(self, screen:SetupScreen) -> None
      # fires screen_transition callbacks(old, new)
    handle_setup_action(self, action:SetupAction, **kwargs) -> None
      # START_DISCOVERY->DISCOVERY, SELECT_DEVICE->PAIRING,
      # NEXT->advance, BACK->previous, RETRY->DISCOVERY,
      # CANCEL->WELCOME, COMPLETE->set setup_complete=True, ->COMPLETE
    update_animation(self, dt:float) -> None  # animation_time += dt
    register_interaction(self) -> None  # no-op

  IMPORTS needed:
    from gtach.display.setup_models import (
        SetupScreen, SetupState, SetupAction, PairingStatus,
        BluetoothDevice, DeviceType)
    from gtach.comm.pairing import BluetoothPairing
    # pygame: conditional try/except ImportError

  VERIFY after each file:
    python -c "import ast; ast.parse(open('<path>').read())"

  FINAL VERIFY:
    cd /Users/williamwatson/Documents/GitHub/GTach
    python -c "import sys; sys.path.insert(0,'src'); from gtach.display.setup import SetupDisplayManager; print('OK')"
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-05-06 | Initial filing |

---

Copyright (c) 2026 William Watson. MIT License.
