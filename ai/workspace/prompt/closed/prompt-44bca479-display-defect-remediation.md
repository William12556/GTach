Created: 2026 July 30

# Prompt: Indicator Inside the Viewport, Regions Registered per View, Dead Poll Removed

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [Version History](<#version history>)

---

## 1.0 Document Information

```yaml
prompt_info:
  id: "prompt-44bca479"
  task_type: "code_generation"
  source_ref: "change-44bca479"
  target_profile: "claude_code"
  date: "2026-07-30"
  iteration: 1
  coupled_docs:
    change_ref: "change-44bca479"
    change_iteration: 1

context:
  purpose: >
    Correct three defects in the display layer. The connection status
    indicator is drawn 73 px outside the circular panel and cannot be
    seen. Touch regions are cleared and rebuilt from the render path 60
    times a second, so a touch arriving in that window on the input
    thread finds an empty region set and is silently discarded. The SDL
    event poll cannot fire under the dummy driver and its comment
    describes a platform the project no longer supports.
  integration: >
    One file: src/gtach/display/manager.py. Five edits. Executor is
    Claude Code; AEL is not used. Task 7.3.9 depends on this: its button
    helper must register through the hook this change introduces rather
    than from the render path.
  knowledge_references: []
  constraints:
    - "Modify only src/gtach/display/manager.py."
    - "Do NOT modify src/gtach/display/input/touch_coordinator.py. Its API and RLock are correct; only the calling pattern changes."
    - "Do NOT modify _render_mode_selector (manager.py:1170). It is unreachable and task 7.3.10 proposes removing it."
    - "Do NOT modify _register_save_button (manager.py:1266). It belongs to the setup flow."
    - "Do NOT remove the clear_regions call at manager.py:1375. It runs on acknowledgement dismissal and is correct."
    - "Do NOT change button sizes, positions or the TypographyConstants design system. That is task 7.3.9."
    - "Do NOT change the indicator's 5 px radius or its colour mapping. Only its coordinate moves."
    - "Keep every drawing call in the four render methods. Only registration leaves them."
    - "Type hints on all new methods; Google-style docstrings; PEP 8."

specification:
  description: >
    Relocate the status indicator inside the viewport; register touch
    regions once per view via a detected view key; remove the unreachable
    event poll.
  requirements:
    functional:
      - "The status indicator is drawn at (240, 60), 180 px from the viewport centre."
      - "A view key of (config.mode, _options_view, _update_status, disconnected, _in_setup_mode) is evaluated each frame before rendering."
      - "The key includes the derived disconnected condition, because DISCONNECTED is not a DisplayMode."
      - "When the key changes, regions are cleared and re-registered exactly once."
      - "Registration is skipped entirely while in setup mode, so the setup subsystem's own regions survive."
      - "The four affected render methods contain no clear_regions and no register_button_region call."
      - "Button rectangles are computed in the registration function and read by the render methods."
      - "pygame.event.poll does not appear in manager.py."
      - "Shutdown continues to be driven solely by _shutdown_event."
    technical:
      language: "Python"
      version: "3.9+ (target runtime 3.11)"
      standards:
        - "Thread-safe if concurrent access"
        - "Comprehensive error handling"
        - "Debug logging with traceback"
        - "Professional docstrings"
  performance:
    - target: "Registration work removed from the frame path for every static screen"
      metric: "time"

design:
  architecture: >
    Rendering and input registration are separated. The render path draws
    only. Registration is driven by a change in the view key, so it runs
    once per transition rather than once per frame, and the input thread
    never observes a partially rebuilt region set.
  components:
    - name: "DisplayManager._current_view_key"
      type: "function"
      purpose: "Identify the view whose controls should be registered."
      interface:
        inputs: []
        outputs:
          type: "Tuple"
          description: "(config.mode, _options_view, _update_status)."
        raises:
          - "None."
      logic:
        - "Return the three values as a tuple."
        - "The docstring must state that any render method branching on further state requires that state to join this key."
    - name: "DisplayManager._register_view_regions"
      type: "function"
      purpose: "Clear and register the controls for the current view, once."
      interface:
        inputs: []
        outputs:
          type: "None"
          description: "Populates the coordinator and the rect attributes."
        raises:
          - "None. Wrapped; logs at ERROR with exc_info."
      logic:
        - "Call touch_coordinator.clear_regions() once."
        - "Dispatch on config.mode and, within OPTIONS, on _options_view and _update_status."
        - "Compute each rectangle, store it on self, and register it with the same callback the render method previously used."
        - "For modes with no controls — DIGITAL, RADIAL, SPLASH — clear and register nothing."
    - name: "DisplayManager._display_loop"
      type: "function"
      purpose: "Drive registration on view change; no longer poll for events."
      logic:
        - "Remove the pygame.event.poll block entirely, including its macOS comment."
        - "Before the render dispatch, evaluate _current_view_key(); if it differs from self._registered_view, call _register_view_regions() and store the key."
    - name: "DisplayManager._draw_status_indicator"
      type: "function"
      purpose: "Draw the connection dot where it can be seen."
      logic:
        - "Change the centre from (20, 20) to (240, 60)."
        - "Leave the thread-status lookup, the colour mapping, the 5 px radius and the exception handler unchanged."
  dependencies:
    internal:
      - "TouchEventCoordinator — clear_regions and register_button_region called from a new site; not modified."
      - "DisplayManager._run_update_check — writes _update_status from a worker thread; that write now drives re-registration through the key."
    external: []

error_handling:
  strategy: >
    Registration is wrapped so a failure cannot stop the display loop.
    Render methods guard against a rect not yet computed, degrading to
    not drawing that control rather than raising.
  exceptions:
    - exception: "Exception"
      condition: "Any failure inside _register_view_regions."
      handling: "logger.error with exc_info; do not update self._registered_view, so registration is retried next frame."
    - exception: "AttributeError"
      condition: "A render method reads a rect before registration computed it."
      handling: "Prevented: rects are initialised to None in __init__ and each render site guards."
  logging:
    level: "ERROR"
    format: "self.logger.error(f'...: {e}', exc_info=True)"

testing:
  unit_tests:
    - scenario: "Distance of (240, 60) from (240, 240)."
      expected: "180, less than the 238 px viewport radius. (20, 20) was 311."
    - scenario: "Fifty frames with an unchanged view key."
      expected: "_register_view_regions called once."
    - scenario: "_update_status 'checking' to 'available' between frames."
      expected: "Re-registration on the next frame; install and cancel regions present."
    - scenario: "_options_view 'menu' to 'update'."
      expected: "Re-registration; the four menu regions replaced."
    - scenario: "config.mode OPTIONS to RADIAL."
      expected: "Re-registration; no button regions remain."
    - scenario: "obd_protocol thread status changes from RUNNING to STOPPED with _sim_mode False."
      expected: "The key changes; the Setup and Simulate regions of the disconnected screen are registered."
    - scenario: "Same transition with _sim_mode True."
      expected: "The key does not change on that account; the disconnected screen is not shown and its regions are not registered."
    - scenario: "Enter setup mode with _setup_manager set."
      expected: "_register_view_regions returns without calling clear_regions, so the setup subsystem's regions survive."
    - scenario: "Leave setup mode."
      expected: "The key changes; the normal view's regions are registered."
    - scenario: "Second thread reads the region set continuously while the OPTIONS menu renders."
      expected: "Never observed empty or partial after the first registration."
    - scenario: "Render the OPTIONS menu with rects still None."
      expected: "Guards hold; nothing drawn for those controls; no AttributeError."
    - scenario: "_register_view_regions raises."
      expected: "Logged at ERROR; _registered_view unchanged so the next frame retries."
    - scenario: "Set _shutdown_event."
      expected: "The loop exits."
  edge_cases:
    - "First frame after start — _registered_view is None so registration runs once."
    - "Mode changed twice within one frame interval — only the final key is registered, which is correct."
    - "_update_status changed by the worker during _register_view_regions — the key is re-evaluated next frame and converges."
    - "Acknowledgement dismissal, which clears regions at manager.py:1375 — the key changes with the mode, so registration follows normally."
  validation:
    - "grep confirms no register_button_region inside the four render methods."
    - "grep confirms pygame.event.poll is absent."

deliverable:
  format_requirements:
    - "Edit src/gtach/display/manager.py in place. Create no new file."
    - "Apply the five edits below. Change nothing else."
  files:
    - path: "src/gtach/display/manager.py"
      content: |
        EDIT 1 — __init__

        Add alongside the existing display state:

                # Touch-region registration is driven by a change in this key
                # rather than by the render path (display review §8.2,
                # recommendation 20).
                self._registered_view = None

                # Populated by _register_view_regions; read by the render
                # methods. None until the first registration pass.
                self._options_btn_clear = None
                self._options_btn_sim = None
                self._options_btn_debug = None
                self._options_btn_update = None
                self._update_btn_install = None
                self._update_btn_cancel = None

        If _render_disconnected and _draw_acknowledgement_mode use named
        rect attributes, initialise those to None here as well. If they
        build rects as locals, give them attributes following the same
        naming pattern so the registration function can populate them.

        EDIT 2 — _draw_status_indicator (draw call currently at
        manager.py:1524-1525)

        Replace:

                    self.rendering_engine.draw_circle(RenderTarget.BACK_BUFFER, 
                                                    (color.r, color.g, color.b), (20, 20), 5)

        with:

                    # (20, 20) is 311 px from the viewport centre (240, 240),
                    # which has radius 238 — the dot was drawn 73 px beyond the
                    # edge of the circular panel and could never be seen. This
                    # position is 180 px out, clear of the DIGITAL numeral and
                    # outside the RADIAL centre disc (display review §8.1,
                    # recommendation 19).
                    self.rendering_engine.draw_circle(RenderTarget.BACK_BUFFER,
                                                    (color.r, color.g, color.b), (240, 60), 5)

        Change nothing else in the method.

        EDIT 3 — add _current_view_key and _register_view_regions

        Place them immediately before _draw_options_menu.

            def _current_view_key(self) -> tuple:
                """Identify the view whose touch regions should be registered.

                Every piece of state a render method branches on when deciding
                which controls exist MUST appear here.

                  - _update_status: _draw_update_view branches on it, and a
                    worker thread writes it in _run_update_check. Omitting it
                    would leave stale regions after an asynchronous change.
                  - _options_view: selects menu or update sub-view.
                  - disconnected: DISCONNECTED is NOT a DisplayMode. It is a
                    derived condition — _render_normal_modes shows that screen
                    when the obd_protocol thread is not RUNNING and simulation
                    mode is off. Omitting it would mean the Setup and Simulate
                    buttons were never registered when the transport drops.
                  - _in_setup_mode: the setup subsystem owns its own regions.
                    It is in the key so that leaving setup re-registers the
                    normal view.

                Returns:
                    (mode, options sub-view, update status, disconnected,
                    in setup mode).
                """
                disconnected = (
                    self.thread_manager.get_thread_status('obd_protocol')
                    != ThreadStatus.RUNNING
                    and not self._sim_mode
                )
                return (
                    self.config.mode,
                    self._options_view,
                    self._update_status,
                    disconnected,
                    self._in_setup_mode,
                )

            def _register_view_regions(self) -> None:
                """Clear and register the touch regions for the current view.

                Called once when the view key changes, not per frame. The
                previous arrangement cleared and rebuilt the region map from
                inside the render path at 60 Hz; a touch acquiring the
                coordinator's lock in that window observed an empty or partial
                map and was discarded (display review §8.2).

                Also computes the button rectangles and stores them on self,
                so the render methods draw from the same geometry that was
                registered.
                """
                try:
                    # The setup subsystem registers and owns its own regions.
                    # Clearing here would destroy them.
                    if self._in_setup_mode and self._setup_manager:
                        return

                    self.touch_coordinator.clear_regions()

                    if self.config.mode == DisplayMode.SPLASH:
                        return  # no controls

                    # DISCONNECTED is a derived condition, not a DisplayMode,
                    # and _render_normal_modes gives it precedence over the
                    # mode. The dispatch must mirror that order exactly.
                    disconnected = (
                        self.thread_manager.get_thread_status('obd_protocol')
                        != ThreadStatus.RUNNING
                        and not self._sim_mode
                    )
                    if disconnected:
                        self._register_disconnected_regions()
                        return

                    if self.config.mode == DisplayMode.OPTIONS:
                        if self._options_view == 'update':
                            self._register_update_view_regions()
                        else:
                            self._register_options_menu_regions()
                    elif self.config.mode == DisplayMode.ACKNOWLEDGEMENT:
                        self._register_acknowledgement_regions()
                    # DIGITAL and RADIAL register nothing.

                except Exception as e:
                    self.logger.error(f"Touch region registration error: {e}", exc_info=True)
                    raise

        Add the four private helpers alongside. Each computes the same
        rectangles the corresponding render method computes today, assigns
        them to the attributes from EDIT 1, and issues the identical
        register_button_region calls with the identical region names,
        TouchAction values and lambdas. Move them verbatim; do not alter
        any geometry, name or callback.

        For _register_update_view_regions, reproduce the existing
        conditional structure: register install and cancel when
        _update_status is 'available'; register the back region when it is
        'none' or 'error'; register nothing for 'checking', 'pending' or
        'idle'.

        EDIT 4 — _display_loop

        Remove this block entirely, including the comment:

                        # Process pygame events — poll() is non-blocking unlike pump().
                        # pump() calls into the Cocoa run loop and can block on macOS;
                        # poll() drains one event at a time and returns NOEVENT immediately
                        # when the queue is empty.
                        while True:
                            event = pygame.event.poll()
                            if event.type == pygame.NOEVENT:
                                break
                            if event.type == pygame.QUIT:
                                self._shutdown_event.set()
                                break

        Replace it with:

                        # No event handling. SDL_VIDEODRIVER is 'dummy' and
                        # set_mode is never called, so no window exists and no
                        # window events are generated — the previous poll loop
                        # and its QUIT path were unreachable (display review
                        # §8.4, recommendation 22). Shutdown is driven entirely
                        # by _shutdown_event. Reinstating a real SDL video
                        # driver would require reinstating event handling.

                        # Register touch regions once per view rather than per
                        # frame (recommendation 20).
                        _view = self._current_view_key()
                        if _view != self._registered_view:
                            try:
                                self._register_view_regions()
                                self._registered_view = _view
                            except Exception:
                                # Logged in _register_view_regions. Leave
                                # _registered_view unchanged so the next frame
                                # retries rather than rendering unregistered.
                                pass

        Leave the rest of the loop — the frame counter, record_frame_start,
        the heartbeat, the render dispatch, the framebuffer write, the
        pacing sleep and the periodic logging — exactly as they are.

        EDIT 5 — strip registration from the four render methods

        From each of _draw_options_menu, _draw_update_view,
        _draw_acknowledgement_mode and _render_disconnected:

          - delete the leading self.touch_coordinator.clear_regions() call
          - delete every self.touch_coordinator.register_button_region call
          - delete the rect construction lines, since the registration
            helpers now own them
          - keep every drawing call, and read each rect from self

        Where a drawing call uses a rect, guard it. For example in
        _draw_options_menu:

                for _btn in (self._options_btn_clear, self._options_btn_sim,
                             self._options_btn_debug, self._options_btn_update):
                    if _btn is None:
                        continue
                    self.rendering_engine.draw_rect(
                        RenderTarget.BACK_BUFFER, (80, 80, 100),
                        (_btn.x, _btn.y, _btn.width, _btn.height)
                    )

        Apply the same guard pattern wherever a rect is dereferenced,
        including the conditional install/cancel/back rects in
        _draw_update_view. Text positions derived from the rect geometry
        must move inside the guard with it.

        Do NOT remove the clear_regions call at manager.py:1375. It runs on
        acknowledgement dismissal, which is a genuine transition.

success_criteria:
  - "python -m py_compile src/gtach/display/manager.py passes."
  - "pytest tests/ passes with no new failures."
  - "The status indicator is drawn at (240, 60)."
  - "_current_view_key returns a five-element tuple including _update_status, the derived disconnected condition and _in_setup_mode."
  - "DisplayMode.DISCONNECTED is NOT referenced — no such member exists."
  - "_register_view_regions returns early, without clearing, when _in_setup_mode and _setup_manager are set."
  - "_register_view_regions gives the disconnected condition precedence over config.mode, mirroring _render_normal_modes."
  - "_register_view_regions calls clear_regions at most once per invocation."
  - "_draw_options_menu, _draw_update_view, _draw_acknowledgement_mode and _render_disconnected contain no clear_regions call."
  - "Those four methods contain no register_button_region call."
  - "_display_loop evaluates the view key before the render dispatch."
  - "pygame.event.poll does not appear anywhere in manager.py."
  - "The clear_regions call on acknowledgement dismissal is still present."
  - "_render_mode_selector and _register_save_button are byte-identical to their current text."
  - "Every region name, TouchAction and callback is unchanged from the current registrations."
  - "src/gtach/display/input/touch_coordinator.py is unmodified."
  - "No file other than src/gtach/display/manager.py is modified."

element_registry:
  source: ""
  entries:
    modules:
      - name: "manager"
        path: "src/gtach/display/manager.py"
      - name: "touch_coordinator"
        path: "src/gtach/display/input/touch_coordinator.py"
    classes:
      - name: "DisplayManager"
        module: "gtach.display.manager"
      - name: "TouchEventCoordinator"
        module: "gtach.display.input.touch_coordinator"
      - name: "DisplayMode"
        module: "gtach.display.models"
      - name: "TouchAction"
        module: "gtach.display.input.touch_coordinator"
      - name: "ConnectionStatus"
        module: "gtach.display.models"
    functions:
      - name: "_current_view_key"
        module: "gtach.display.manager"
        signature: "_current_view_key(self) -> tuple"
      - name: "_register_view_regions"
        module: "gtach.display.manager"
        signature: "_register_view_regions(self) -> None"
      - name: "_draw_status_indicator"
        module: "gtach.display.manager"
        signature: "_draw_status_indicator(self) -> None"
      - name: "_display_loop"
        module: "gtach.display.manager"
        signature: "_display_loop(self) -> None"
    constants: []

notes: >
  Executor is Claude Code; AEL is not used, so no tactical_brief is
  required (ai/task.md §7.2, governance P09 §1.10.2). Invoke from the
  project root:
  implement ai/workspace/prompt/prompt-44bca479-display-defect-remediation.md
  and close the prompt when finished. Leave the issue and change active
  pending test results (ai/task.md §8.2.1).

  Two of the three corrections are visible on the panel, so on-target
  confirmation is quick: the status dot should appear near the top of the
  circle and change colour with the transport state, and every control on
  OPTIONS, the update view, DISCONNECTED and the acknowledgement screen
  should respond to every tap.

  If the dot collides with RADIAL tick marks or numerals at (240, 60),
  the recorded alternative is (240, 300) — inside the inert bottom arc —
  and the correction is a single coordinate. It was not chosen first
  because the DIGITAL numeral is rendered at 180 px centred on (240, 215)
  and extends to roughly y = 280.

  Task 7.3.9 depends on this change. When it routes button drawing
  through a single helper, that helper must register through
  _register_view_regions rather than from the render path, or this
  correction is undone.
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-07-30 | Initial prompt document coupled to change-44bca479. |
| 1.1 | 2026-07-31 | Executed by Claude Code. All five edits applied and all seventeen success criteria met, with no departure from the prompt's text required. 88 assertions against a real DisplayManager and a real TouchEventCoordinator, all passing; pytest tests/ 11 passed. The region-set race was measured rather than argued: rendering the options menu while a second thread sampled get_active_regions, the pre-change code showed an empty region set in 235,321,813 of 245,707,350 samples and a partial set in 2,832,945 more, against 0 empty and 0 partial in 150,725,081 samples afterwards. Recorded in change-44bca479. Closed per P00 §1.1.14.4 and moved to ai/workspace/prompt/closed/; the issue and change remain active pending on-target results per ai/task.md §8.2.1. |

---

Copyright (c) 2026 William Watson. MIT License.
