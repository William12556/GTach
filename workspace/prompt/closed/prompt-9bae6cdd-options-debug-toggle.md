Created: 2026 June 12

```yaml
prompt_info:
  id: "prompt-9bae6cdd"
  task_type: "code_generation"
  source_ref: "change-9bae6cdd"
  date: "2026-06-12"
  iteration: 1
  coupled_docs:
    change_ref: "change-9bae6cdd"
    change_iteration: 1

context:
  purpose: >
    Add a third OPTIONS-screen button that toggles debug logging at runtime,
    wired to GTachApplication.toggle_debug_logging() via a callback.
  integration: >
    Two files modified: src/gtach/display/manager.py (DisplayManager) and
    src/gtach/app.py (GTachApplication). Executor: Claude Code (no AEL).
  constraints:
    - "Reuse the existing callback pattern (_setup_entry_callback) — do not pass the app instance to DisplayManager."
    - "The debug handler does not exist on non-Linux; toggle_debug_logging already no-ops there. Do not add platform guards in the UI."
    - "Do not modify the Clear settings or Bluetooth/Simulation buttons' behaviour."
    - "Do not modify long-press navigation."
    - "Keep all three buttons within the circular safe radius."

specification:
  description: "Callback wiring plus one new toggle button with state label."
  requirements:
    functional:
      - "OPTIONS shows three buttons: Clear settings, Bluetooth/Simulation, Debug."
      - "Debug button label is 'Debug: On' or 'Debug: Off' per current state."
      - "Tapping Debug flips state, calls the callback, and updates the label."
      - "Initial debug state reflects the launch --debug flag."
    technical:
      language: "Python"
      version: "3.11"
      standards:
        - "Existing logging and error-handling patterns."

design:
  architecture: "Callback pattern consistent with _setup_entry_callback."
  components:
    - name: "DisplayManager.__init__"
      type: "function"
      purpose: "Initialise debug callback and state."
      logic:
        - "After the existing 'self._sim_mode = False' line, add: self._debug_toggle_callback = None and self._debug_logging_on = False."

    - name: "DisplayManager._draw_options_mode"
      type: "function"
      purpose: "Render three buttons including the Debug toggle."
      logic:
        - "Replace the two-button geometry and rendering with the three-button block in deliverable file 1b."

    - name: "DisplayManager._on_debug_toggle"
      type: "function"
      purpose: "Flip debug state and invoke the callback."
      logic:
        - "Add the method in deliverable file 1c, immediately after _on_simulation_mode()."

    - name: "GTachApplication wiring"
      type: "function"
      purpose: "Set callback and initial state at both DisplayManager sites."
      logic:
        - "At both lines where 'self._display._setup_entry_callback = self._re_enter_setup' appears, add the two wiring lines in deliverable file 2."

  dependencies:
    internal:
      - "GTachApplication.toggle_debug_logging (bd8f95b7)"

deliverable:
  format_requirements:
    - "Edit both files in place."
  files:
    - path: "src/gtach/display/manager.py"
      content: |
        EDIT 1a — DisplayManager.__init__:

        After the line:
            self._sim_mode = False  # Session-only simulation mode flag
        Add:
            self._debug_toggle_callback = None  # Set by app.py: Callable[[bool], None]
            self._debug_logging_on = False      # Reflects current debug logging state

        EDIT 1b — _draw_options_mode:

        Replace the block that begins at:
            # Draw two centred button rectangles
            button_width = 300
            button_height = 80
            center_x = 240
        and continues through the registration of "clear_settings" and
        "simulation_mode" regions (i.e. everything from "# Draw two centred button
        rectangles" up to and including the simulation_mode register_button_region
        call), with:

            # Draw three centred button rectangles (tightened for circular fit)
            button_width = 300
            button_height = 75
            center_x = 240

            clear_btn_y = 120
            sim_btn_y = 210
            debug_btn_y = 300

            self._options_btn_clear = pygame.Rect(
                center_x - button_width // 2, clear_btn_y, button_width, button_height
            )
            self._options_btn_sim = pygame.Rect(
                center_x - button_width // 2, sim_btn_y, button_width, button_height
            )
            self._options_btn_debug = pygame.Rect(
                center_x - button_width // 2, debug_btn_y, button_width, button_height
            )

            for _btn in (self._options_btn_clear, self._options_btn_sim, self._options_btn_debug):
                self.rendering_engine.draw_rect(
                    RenderTarget.BACK_BUFFER,
                    (80, 80, 100),
                    (_btn.x, _btn.y, _btn.width, _btn.height)
                )

            button_font = self._get_cached_font(28)
            if button_font:
                self.rendering_engine.render_text(
                    RenderTarget.BACK_BUFFER, "Clear settings", button_font,
                    (255, 255, 255), (center_x, clear_btn_y + button_height // 2), center=True
                )
                sim_label = "Simulation mode" if self._sim_mode else "Bluetooth"
                self.rendering_engine.render_text(
                    RenderTarget.BACK_BUFFER, sim_label, button_font,
                    (255, 255, 255), (center_x, sim_btn_y + button_height // 2), center=True
                )
                debug_label = "Debug: On" if self._debug_logging_on else "Debug: Off"
                self.rendering_engine.render_text(
                    RenderTarget.BACK_BUFFER, debug_label, button_font,
                    (255, 255, 255), (center_x, debug_btn_y + button_height // 2), center=True
                )

            self.touch_coordinator.register_button_region(
                "clear_settings", self._options_btn_clear,
                TouchAction.SETTINGS_CHANGE, lambda pos: self._on_clear_settings()
            )
            self.touch_coordinator.register_button_region(
                "simulation_mode", self._options_btn_sim,
                TouchAction.SETTINGS_CHANGE, lambda pos: self._on_simulation_mode()
            )
            self.touch_coordinator.register_button_region(
                "debug_toggle", self._options_btn_debug,
                TouchAction.SETTINGS_CHANGE, lambda pos: self._on_debug_toggle()
            )

        The existing "# Draw button backgrounds", "# Draw button labels", and the
        original two register_button_region calls are entirely replaced by the
        block above. The title, border, and instructions ("Long press to return")
        remain unchanged.

        EDIT 1c — add method after _on_simulation_mode():

            def _on_debug_toggle(self) -> None:
                """Toggle runtime debug logging via the application callback."""
                try:
                    self._debug_logging_on = not self._debug_logging_on
                    self.logger.info(f"Debug logging toggle -> {'on' if self._debug_logging_on else 'off'}")
                    if self._debug_toggle_callback is not None:
                        self._debug_toggle_callback(self._debug_logging_on)
                    else:
                        self.logger.warning("debug_toggle_callback not registered")
                except Exception as e:
                    self.logger.error(f"Debug toggle error: {e}", exc_info=True)

    - path: "src/gtach/app.py"
      content: |
        EDIT 2a — store the debug flag. GTachApplication.__init__ receives `debug`
        but does not currently store it. In __init__, after the line:
            self._args = args or argparse.Namespace()
        add:
            self._debug = debug

        EDIT 2b — at BOTH locations where this line appears:
            self._display._setup_entry_callback = self._re_enter_setup

        Add immediately after it (same indentation):
            self._display._debug_toggle_callback = self.toggle_debug_logging
            self._display._debug_logging_on = self._debug

        Note: there are two such sites — in _start_setup_mode() and in
        _start_normal_mode(). Apply the addition at both.

success_criteria:
  - "python -m py_compile src/gtach/display/manager.py passes."
  - "python -m py_compile src/gtach/app.py passes."
  - "DisplayManager.__init__ defines _debug_toggle_callback and _debug_logging_on."
  - "_draw_options_mode renders three buttons and registers a 'debug_toggle' region."
  - "_on_debug_toggle() exists and invokes the callback."
  - "Both app.py DisplayManager sites set the callback and initial flag."
  - "GTachApplication.__init__ stores self._debug = debug."
  - "Clear settings and Bluetooth/Simulation buttons are functionally unchanged."

notes: >
  Executor is Claude Code (no AEL). Invoke from the project root:
  implement workspace/prompt/prompt-9bae6cdd-options-debug-toggle.md
```

```yaml
tactical_brief: |
  Executor: Claude Code. Implement change-9bae6cdd: OPTIONS debug toggle.

  FILE 1: src/gtach/display/manager.py

  1a) In DisplayManager.__init__, after:
        self._sim_mode = False  # Session-only simulation mode flag
      add:
        self._debug_toggle_callback = None
        self._debug_logging_on = False

  1b) In _draw_options_mode, replace the two-button geometry/render/register block
      (from "# Draw two centred button rectangles" through the simulation_mode
      register_button_region call) with the three-button block in deliverable
      file "src/gtach/display/manager.py" EDIT 1b. Buttons at y=120/210/300,
      height 75. Third button labelled "Debug: On"/"Debug: Off" per
      self._debug_logging_on; registers region "debug_toggle" ->
      self._on_debug_toggle. Title, border, and "Long press to return" unchanged.

  1c) Add after _on_simulation_mode():

        def _on_debug_toggle(self) -> None:
            """Toggle runtime debug logging via the application callback."""
            try:
                self._debug_logging_on = not self._debug_logging_on
                self.logger.info(f"Debug logging toggle -> {'on' if self._debug_logging_on else 'off'}")
                if self._debug_toggle_callback is not None:
                    self._debug_toggle_callback(self._debug_logging_on)
                else:
                    self.logger.warning("debug_toggle_callback not registered")
            except Exception as e:
                self.logger.error(f"Debug toggle error: {e}", exc_info=True)

  FILE 2: src/gtach/app.py

  2a) In GTachApplication.__init__, after:
        self._args = args or argparse.Namespace()
      add:
        self._debug = debug

  2b) At BOTH sites where this line appears (in _start_setup_mode and
  _start_normal_mode):
        self._display._setup_entry_callback = self._re_enter_setup
  add immediately after, same indentation:
        self._display._debug_toggle_callback = self.toggle_debug_logging
        self._display._debug_logging_on = self._debug

  Verify: python -m py_compile src/gtach/display/manager.py &&
          python -m py_compile src/gtach/app.py
```

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-06-12 | Initial prompt document. |

---

Copyright (c) 2026 William Watson. MIT License.
