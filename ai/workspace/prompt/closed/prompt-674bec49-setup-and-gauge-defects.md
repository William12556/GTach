Created: 2026 October 07

# Prompt: Setup Lifecycle, Gauge Range, Cached Device Presence, Persistent Errors

---

## Table of Contents

- [1. Prompt](<#1. prompt>)
- [2. Version History](<#2. version history>)

---

## 1. Prompt

```yaml
prompt_info:
  id: "prompt-674bec49"
  task_type: "debug"
  source_ref: "change-674bec49"
  target_profile: "claude_code"
  date: "2026-10-07"
  iteration: 1
  coupled_docs:
    change_ref: "change-674bec49"
    change_iteration: 1

context:
  purpose: >
    Stop setup threads when setup ends, size the gauge to the configured
    redline, remove per-frame devices.yaml reads, and keep setup error
    messages visible and accurate.
  integration: "src/gtach/display/setup.py, src/gtach/app.py, src/gtach/display/manager.py; tests."
  knowledge_references:
    - "ai/workspace/issues/issue-674bec49-setup-and-gauge-defects.md"
    - "ai/workspace/change/change-674bec49-setup-and-gauge-defects.md"
    - "CLAUDE.md §4 rule 8"
  constraints:
    - "CRITICAL: stop_setup must never join threading.current_thread(); on_complete runs on the setup thread."
    - "CRITICAL: with the abarth_595_turismo profile (redline 6000) the gauge must be pixel-identical to before: max_rpm 7000, same ticks."
    - "No call-outs under a lock (CLAUDE.md rule 8). Clear error_message after releasing _touch_regions_lock."
    - "Do not change arc geometry, colours, palettes or band logic in manager.py."
    - "Do not change DeviceStore, SetupStateCoordinator or interface.py."
    - "Do not modify src/gtach/display/manager_backup.py or setup_original_backup.py."
    - "Every logger .error/.critical in a broad handler passes exc_info=True."
    - "Python 3.9+ compatible. PEP 8. Type hints on public interfaces. Google-style docstrings."

specification:
  description: "Apply EDITS A to D of change-674bec49 and add tests/test_setup_and_gauge.py."
  requirements:
    functional:
      - "Setup completion, Cancel on WELCOME, and setup re-entry each stop the active SetupDisplayManager."
      - "max_rpm = min(9000, max(7000, ceil((redline + 500) / 1000) * 1000))."
      - "WELCOME uses a cached device-presence flag refreshed on entry to WELCOME and at start_setup."
      - "Setup error messages persist until the next tap on a region and show their own text on WELCOME, fitted to 400 px."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Thread-safe if concurrent access"
        - "Professional docstrings"
  performance:
    - target: "No file I/O per frame on WELCOME"
      metric: "calls"

design:
  architecture: "Local corrections."
  components:
    - name: "EDIT A — setup lifecycle"
      type: "function"
      purpose: "No leaked setup threads."
      logic:
        - "setup.py stop_setup: replace the join with `if self._setup_thread and self._setup_thread is not threading.current_thread(): self._setup_thread.join(timeout=5.0)`."
        - "app.py _on_setup_complete: after the `_obd_started` guard and assignment, before `self._display.exit_setup_mode()`: `manager = getattr(self, '_setup_manager', None)`; if manager: try manager.stop_setup() except Exception as e: self.logger.error(f'Stopping setup manager failed: {e}', exc_info=True)."
        - "app.py _start_setup_mode: immediately before `self._setup_manager = SetupDisplayManager(...)`, the same guarded stop of any existing manager."
    - name: "EDIT B — gauge range"
      type: "function"
      purpose: "Cover the configured redline."
      logic:
        - "Add `def _gauge_max_rpm(self) -> int:` to DisplayManager with a docstring stating the rule and that redline 6000 yields 7000. Read `self.config.rpm_bands.redline_rpm` inside try/except (fallback 6000). Use math.ceil."
        - "In _draw_radial_mode: `max_rpm = self._gauge_max_rpm()` before the clamp; replace `min(7000, rpm)` with `min(max_rpm, rpm)`; remove the later `max_rpm = 7000` assignment; change the tick loop to `range(1000, max_rpm + 1, 1000)` and drop the now-redundant `if rpm_tick <= max_rpm` only if behaviour is identical; update the '1000-7000 RPM' and 'clamped to 7000' comments."
    - name: "EDIT C — cached device presence"
      type: "function"
      purpose: "No per-frame file reads."
      logic:
        - "In __init__: `self._has_device = False`."
        - "Add `def _refresh_has_device(self) -> None:` reading `DeviceStore().get_primary_device() is not None` in try/except (False on error, logged with exc_info=True)."
        - "start_setup: call _refresh_has_device() and use self._has_device for the WELCOME/CURRENT_DEVICE choice."
        - "_on_screen_transition: if new_screen == SetupScreen.WELCOME: self._refresh_has_device() before _invalidate_render_cache."
        - "_render_welcome_screen and _update_cached_screen_touch_regions: use self._has_device; remove the DeviceStore import and construction from both."
    - name: "EDIT D — persistent errors"
      type: "function"
      purpose: "Visible, accurate error messages."
      logic:
        - "_render_device_list_screen: delete `self.state_coordinator.update_state(error_message=None)` and its comment."
        - "handle_touch_event: after the with-block, `if hit is not None:` first `if self.state_coordinator.get_state().error_message: self.state_coordinator.update_state(error_message=None)`, then dispatch."
        - "_render_welcome_screen: render `state.error_message` with get_label_small_font() in self.colors['warning'] at the existing position. Add a helper `_fit_text(font, text, max_width=400) -> str` implementing: full text if it fits; else text up to and including the first '. ' stop (strip the trailing space) if it fits; else drop characters from the end and append '…' until it fits."

data_schema:
  entities: []

error_handling:
  strategy: "New code guarded; errors logged with exc_info=True."
  exceptions: []
  logging:
    level: "Unchanged"
    format: "Unchanged"

testing:
  unit_tests:
    - scenario: "SetupDisplayManager-like host with stop_setup bound; a thread whose target calls stop_setup on the host where _setup_thread is that thread."
      expected: "No exception; thread finishes."
    - scenario: "stop_setup twice from the main thread with a finished _setup_thread."
      expected: "No exception."
    - scenario: "GTachApplication via object.__new__ with stub _setup_manager, _display and patched _start_obd; call _on_setup_complete twice."
      expected: "stop_setup called once, before exit_setup_mode; _start_obd once."
    - scenario: "GTachApplication via object.__new__ with stub old _setup_manager; _start_setup_mode with SetupDisplayManager and DisplayManager patched."
      expected: "Old manager's stop_setup called before the new manager is constructed."
    - scenario: "_gauge_max_rpm with config.rpm_bands.redline_rpm 6000, 7000, 7500, 8500, 9000, 12000."
      expected: "7000, 8000, 8000, 9000, 9000, 9000."
    - scenario: "_update_cached_screen_touch_regions on WELCOME with DeviceStore patched to raise on construction, _has_device True then False."
      expected: "Two-button regions then one-button regions; no construction."
    - scenario: "transition_to_screen(WELCOME) on a real coordinator wired to a host with _refresh_has_device recorded."
      expected: "Recorded once."
    - scenario: "_render_device_list_screen (as in tests/test_device_list_focus.py) with error_message 'OBD check failed'."
      expected: "error_message unchanged after render."
    - scenario: "handle_touch_event with error_message set and _handle_touch_action patched to record the coordinator's error_message."
      expected: "Recorded None."
    - scenario: "_fit_text with a real pygame font for 'Device not available' and 'No devices found. Ensure your ELM327 adapter is powered on and discoverable.'"
      expected: "First unchanged; second 'No devices found.'; both render ≤ 400 px."
  edge_cases:
    - "_gauge_max_rpm when config or rpm_bands is missing: 7000."
  validation:
    - "pytest tests/ passes."

deliverable:
  format_requirements:
    - "Edit existing files in place; add one test module."
  files:
    - path: "src/gtach/display/setup.py"
      content: "EDITS A(1), C, D"
    - path: "src/gtach/app.py"
      content: "EDIT A(2), A(3)"
    - path: "src/gtach/display/manager.py"
      content: "EDIT B"
    - path: "tests/test_setup_and_gauge.py"
      content: "testing.unit_tests"

success_criteria:
  - "stop_setup guards against joining the current thread."
  - "_on_setup_complete and _start_setup_mode stop an existing setup manager."
  - "'min(7000' and 'max_rpm = 7000' no longer appear in manager.py; _gauge_max_rpm exists."
  - "_update_cached_screen_touch_regions and _render_welcome_screen construct no DeviceStore."
  - "_render_device_list_screen no longer clears error_message."
  - "The fixed string 'No devices found' is no longer used for error_message on WELCOME."
  - "pytest tests/ passes."

element_registry:
  source: ""
  entries:
    modules:
      - name: "setup"
        path: "src/gtach/display/setup.py"
      - name: "app"
        path: "src/gtach/app.py"
      - name: "manager"
        path: "src/gtach/display/manager.py"
    classes:
      - name: "SetupDisplayManager"
        module: "gtach.display.setup"
      - name: "GTachApplication"
        module: "gtach.app"
      - name: "DisplayManager"
        module: "gtach.display.manager"
    functions:
      - name: "_gauge_max_rpm"
        module: "gtach.display.manager"
        signature: "(self) -> int"
      - name: "_refresh_has_device"
        module: "gtach.display.setup"
        signature: "(self) -> None"
      - name: "_fit_text"
        module: "gtach.display.setup"
        signature: "(self, font, text: str, max_width: int = 400) -> str"
    constants: []

notes: >
  Human verification on the Pi: the gauge looks unchanged with the
  current profile; after Cancel on WELCOME and after DISCONNECTED →
  Setup, stacks.log (debug on) shows at most one SetupManager thread; a
  failed Continue probe shows 'Device not available' on WELCOME until
  the next tap.
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-07 | Initial prompt implementing change-674bec49 iteration 1. Target profile claude_code. |
| 1.1 | 2026-10-07 | Implemented; closed |

---

Copyright (c) 2026 William Watson. MIT License.
