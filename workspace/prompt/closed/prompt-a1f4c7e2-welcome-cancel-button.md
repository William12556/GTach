Created: 2026 May 29

```yaml
prompt_info:
  id: "prompt-a1f4c7e2"
  task_type: "code_generation"
  source_ref: "change-a1f4c7e2"
  date: "2026-05-29"
  iteration: 1
  coupled_docs:
    change_ref: "change-a1f4c7e2"
    change_iteration: 1

context:
  purpose: >
    Add a conditional Cancel button to the setup WELCOME screen so users can
    abort setup and return to an already-configured device.
  integration: >
    Two files modified: app.py (GTachApplication) and setup.py
    (SetupDisplayManager). No new screens, enums, or classes.
  constraints:
    - "Do not add new SetupScreen enum values."
    - "Do not modify any screen other than WELCOME."
    - "Cancel must only render when DeviceStore().get_primary_device() is not None."
    - "WELCOME is in the static render cache — cache invalidation is handled by existing _invalidate_render_cache logic; no additional changes needed."

specification:
  description: >
    Two targeted code edits to enable WELCOME screen cancel when a stored device exists.
  requirements:
    functional:
      - "Cancel button absent on WELCOME when no device is stored."
      - "Cancel button present on WELCOME when a device is stored."
      - "Tapping Cancel invokes self._on_complete() and exits setup."
      - "_re_enter_setup() no longer deletes the stored device before entering setup."
    technical:
      language: "Python"
      version: "3.11"
      standards:
        - "Thread-safe touch region updates via _update_touch_regions_safe()"
        - "Existing error handling and logging patterns"

design:
  architecture: "Minimal targeted edits — no structural changes."
  components:
    - name: "GTachApplication._re_enter_setup"
      type: "function"
      purpose: "Remove premature device deletion."
      logic:
        - "Delete the block: device = self._device_store.get_primary_device() / if device: / self._device_store.remove_device(device.mac_address)"
        - "Leave all other logic intact."

    - name: "SetupDisplayManager._render_welcome_screen"
      type: "function"
      purpose: "Conditional two-button layout when device exists."
      logic:
        - "After rendering the description text, check DeviceStore().get_primary_device()."
        - "If no device: render single 'Start Setup' button at pygame.Rect(110, 330, 260, 90) — unchanged."
        - "If device exists: render 'Start Setup' at pygame.Rect(110, 270, 260, 75) using colors['primary']."
        - "If device exists: render 'Cancel' at pygame.Rect(110, 360, 260, 75) using colors['border']."
        - "Append ('cancel_setup', cancel_btn) to new_regions when device exists."

    - name: "SetupDisplayManager._handle_touch_action"
      type: "function"
      purpose: "Handle cancel_setup touch action."
      logic:
        - "Add elif action == 'cancel_setup': block."
        - "Log: self.logger.info('Setup cancelled — returning to stored device')"
        - "Call self._on_complete() if self._on_complete is not None."
        - "Return SetupAction.COMPLETE."

    - name: "SetupDisplayManager._update_cached_screen_touch_regions"
      type: "function"
      purpose: "Restore correct touch regions when WELCOME is served from cache."
      logic:
        - "Existing block handles SetupScreen.WELCOME with only start_btn."
        - "Extend: also check DeviceStore().get_primary_device(); if present, include cancel_btn rect pygame.Rect(110, 360, 260, 75) in the region list as ('cancel_setup', cancel_btn)."

  dependencies:
    internal:
      - "src/gtach/comm/device_store.py — DeviceStore"
      - "src/gtach/display/setup_models.py — SetupAction"

deliverable:
  format_requirements:
    - "Edit files in place using filesystem tools."
  files:
    - path: "src/gtach/app.py"
      content: "Remove device deletion block from _re_enter_setup()."
    - path: "src/gtach/display/setup.py"
      content: "Conditional Cancel button in _render_welcome_screen, handler in _handle_touch_action, updated _update_cached_screen_touch_regions."

success_criteria:
  - "No device stored: WELCOME renders single Start Setup button (unchanged)."
  - "Device stored: WELCOME renders Start Setup + Cancel buttons."
  - "Cancel tap exits setup and invokes on_complete callback."
  - "Start Setup tap proceeds to DISCOVERY as before."
  - "No regressions in first-run setup or New Setup flow."

notes: ""
```

```yaml
tactical_brief: |
  Modify two files to add a conditional Cancel button to the setup WELCOME screen.

  FILE 1: src/gtach/app.py
  Function: _re_enter_setup()
  Remove the following block (do not touch anything else in the function):
      # Clear stored device
      if hasattr(self, '_device_store'):
          device = self._device_store.get_primary_device()
          if device:
              self._device_store.remove_device(device.mac_address)

  FILE 2: src/gtach/display/setup.py
  Three function edits:

  (a) _render_welcome_screen()
  After rendering description text, check `DeviceStore().get_primary_device()`.
  If None: existing single Start Setup button unchanged at Rect(110, 330, 260, 90).
  If device exists:
    - Start Setup button: pygame.Rect(110, 270, 260, 75), color colors['primary']
    - Cancel button:      pygame.Rect(110, 360, 260, 75), color colors['border']
    - Label: "Cancel", btn_font, white text
    - Append ("cancel_setup", cancel_btn) to new_regions
  DeviceStore import is already present inline in other methods; use same pattern:
    from ..comm.device_store import DeviceStore

  (b) _handle_touch_action()
  Add after the existing "cancel" elif block:
      elif action == "cancel_setup":
          self.logger.info("Setup cancelled — returning to stored device")
          if self._on_complete:
              self._on_complete()
          return SetupAction.COMPLETE

  (c) _update_cached_screen_touch_regions()
  Existing block:
      if state.current_screen == SetupScreen.WELCOME:
          start_btn = pygame.Rect(110, 330, 260, 90)
          self._update_touch_regions_safe([("start", start_btn)])
  Replace with:
      if state.current_screen == SetupScreen.WELCOME:
          from ..comm.device_store import DeviceStore
          has_device = DeviceStore().get_primary_device() is not None
          if has_device:
              start_btn = pygame.Rect(110, 270, 260, 75)
              cancel_btn = pygame.Rect(110, 360, 260, 75)
              self._update_touch_regions_safe([("start", start_btn), ("cancel_setup", cancel_btn)])
          else:
              start_btn = pygame.Rect(110, 330, 260, 90)
              self._update_touch_regions_safe([("start", start_btn)])
```

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-05-29 | Initial prompt document. |

---

Copyright (c) 2026 William Watson. MIT License.
