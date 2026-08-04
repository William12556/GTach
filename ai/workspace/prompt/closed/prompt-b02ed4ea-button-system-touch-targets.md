Created: 2026 August 04

# Prompt: Give Button Geometry One Owner and Put a Confirmation in Front of Clear Settings

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [Version History](<#version history>)

---

## 1.0 Document Information

```yaml
prompt_info:
  id: "prompt-b02ed4ea"
  task_type: "implementation"
  source_ref: "change-b02ed4ea"
  target_profile: "claude_code"
  date: "2026-08-04"
  iteration: 1
  coupled_docs:
    change_ref: "change-b02ed4ea"
    change_iteration: 1

context:
  purpose: >
    Every touch target in the main UI is below the comfortable minimum
    for a panel operated by hand in a moving vehicle, and the four
    options-menu items are separated by 10 px — with Clear settings,
    which erases the paired device, sitting directly above Simulation
    mode with no confirmation. Separately, TypographyConstants declares
    a button design system that DisplayManager applies nowhere, so the
    declared corner radius and 8 px touch expansion have no effect and
    button geometry is duplicated across four register methods.
  integration: >
    Two files: src/gtach/display/manager.py and
    src/gtach/display/typography.py. Executor is Claude Code; AEL is not
    used.

    READ THIS FIRST — WHAT 44bca479 ALREADY DID. Touch registration was
    moved out of the render path into a mode-entry hook by change-
    44bca479, which has shipped. _display_loop (manager.py:435-444)
    calls _register_view_regions (manager.py:1038) only when
    _current_view_key() (manager.py:1002) changes. The four per-view
    register methods own the geometry and store rects on self; the
    render methods draw from those rects. That structure is the
    subject of display recommendation 20 and MUST NOT be undone. In
    particular: do not register a touch region from any _draw_ method.

    The consequence for this task: the "single helper" of
    recommendation 27 is TWO helpers — a geometry-and-registration
    helper called from the register methods, and a draw helper called
    from the render methods. One helper doing both would put
    registration back in the render path.

    LINE NUMBERS. The display report cites manager.py:911-921 and
    1345-1346 for this geometry. Those predate 44bca479. The current
    locations are manager.py:1087-1105 (options), 1107-1134 (update),
    1146-1179 (disconnected). The report's *values* are all correct.
  knowledge_references: []
  constraints:
    - "Modify only src/gtach/display/manager.py and src/gtach/display/typography.py."
    - "Do NOT modify src/gtach/display/input/touch_coordinator.py. The touch expansion is applied by the caller, because register_button_region is also called by the setup subsystem and enlarging every region in the application is out of scope."
    - "Do NOT register any touch region from a _draw_ method. That would regress recommendation 20 (change-44bca479)."
    - "Do NOT add a new DisplayMode. The confirmation is a sub-view expressed through the existing self._options_view field, exactly as 'update' already is."
    - "Do NOT change _register_acknowledgement_regions (manager.py:1136-1144). Its region is the full 480 x 480 screen."
    - "Do NOT change the early return for setup mode at manager.py:1054-1055. The setup subsystem owns its own regions."
    - "Do NOT alter any existing TypographyConstants value. Add three; change none. BUTTON_FLOATING stays 44 x 44 — it is used by typography.py's own helpers, which are out of scope."
    - "Do NOT touch _render_mode_selector (manager.py:1423), _register_rpm_sliders (1463), _render_slider_visuals (1489) or _register_save_button (1519). They are unreachable dead code and belong to task 7.3.10."
    - "Do NOT change the body of _on_clear_settings (manager.py:1333). Only its invoker moves."
    - "Type hints preserved; Google-style docstrings; PEP 8."

specification:
  description: >
    Add a button geometry helper and a button draw helper to
    DisplayManager, both driven by TypographyConstants. Re-lay the
    options menu to three targets of height >= 72 px separated by
    >= 16 px, move Clear settings behind a confirmation sub-view, and
    bring the update and disconnected views to the same minimum. Apply
    the declared corner radius, border width and touch expansion at
    every one of those sites.
  requirements:
    functional:
      - "TypographyConstants declares BUTTON_MIN_TOUCH_HEIGHT = 72, BUTTON_MIN_SEPARATION = 16 and VIEWPORT_RADIUS = 238."
      - "_button_column returns visual rects and registers touch rects inflated by BUTTON_TOUCH_EXPANSION on each axis."
      - "_button_column refuses to produce a target below BUTTON_MIN_TOUCH_HEIGHT or a separation below max(BUTTON_MIN_SEPARATION, 2 * BUTTON_TOUCH_EXPANSION)."
      - "_button_column logs at ERROR, naming the region, if any corner of any rect falls outside the r=238 viewport centred on (240, 240)."
      - "_draw_button draws with border_radius = BUTTON_CORNER_RADIUS and a BUTTON_BORDER_WIDTH outline, label centred on the rect."
      - "The options menu registers exactly three regions: simulation_mode, debug_toggle, check_updates."
      - "clear_settings is not registered on the options menu."
      - "A third _options_view value 'confirm_clear' presents two controls: confirm and cancel."
      - "The confirm control invokes the existing _on_clear_settings; the cancel control returns _options_view to 'menu' and invokes nothing else."
      - "The update view and the disconnected view register targets of height >= 72 px with separation >= 16 px."
      - "Every button in the options, confirm, update and disconnected views is drawn through _draw_button."
      - "Touch registration still happens only from _register_view_regions."
    technical:
      language: "Python"
      version: "3.9+ (target runtime 3.11)"
      standards:
        - "Thread-safe if concurrent access"
        - "Comprehensive error handling"
        - "Debug logging with traceback"
        - "Professional docstrings"
  performance:
    - target: "No measurable change. Registration runs on view change, not per frame; drawing adds a border stroke per button on screens that are not the RPM path"
      metric: "time"

design:
  architecture: >
    One method owns where a button is and how large it is. One method
    owns how it looks. The register methods call the first, the render
    methods call the second, and neither crosses into the other's
    responsibility — which is what keeps registration out of the render
    path.

    A destructive control is not reachable in one tap. The confirmation
    is a sub-view of an existing mode rather than a mode of its own,
    because the view-key mechanism already distinguishes sub-views and
    adding a DisplayMode would require every consumer of that enum to
    account for a screen that is not a display mode in any meaningful
    sense.
  components:
    - name: "TypographyConstants"
      type: "class"
      purpose: "Hold the ergonomic minimum next to the sizes it governs."
      logic:
        - "Add BUTTON_MIN_TOUCH_HEIGHT = 72 with a comment recording that 72 px = 8.0 mm at 229 ppi."
        - "Add BUTTON_MIN_SEPARATION = 16."
        - "Add VIEWPORT_RADIUS = 238."
    - name: "DisplayManager._button_column"
      type: "function"
      purpose: "Compute, validate and register a centred vertical stack of buttons."
      interface:
        inputs:
          - name: "specs"
            type: "Sequence[Tuple[str, TouchAction, Callable]]"
            description: "region_id, action type, callback — one per button, top to bottom."
          - name: "width"
            type: "int"
            description: "Button width in pixels."
          - name: "top"
            type: "int"
            description: "y of the first button's top edge."
          - name: "height"
            type: "Optional[int]"
            description: "Defaults to BUTTON_MIN_TOUCH_HEIGHT."
          - name: "separation"
            type: "Optional[int]"
            description: "Defaults to max(BUTTON_MIN_SEPARATION, 2 * BUTTON_TOUCH_EXPANSION)."
        outputs:
          type: "List[pygame.Rect]"
          description: "The VISUAL rects, in the order given. Not the registered rects."
        raises:
          - "None. Constraint violations are clamped and logged; viewport violations are logged at ERROR."
      logic:
        - "Clamp height up to BUTTON_MIN_TOUCH_HEIGHT and separation up to its floor, logging a WARNING if either was raised."
        - "Build each rect centred on x = 240: pygame.Rect(240 - width // 2, top + i * (height + separation), width, height)."
        - "For each rect, test all four corners against (x - 240)^2 + (y - 240)^2 <= VIEWPORT_RADIUS^2; log at ERROR naming the region_id on failure. Do not raise — an off-viewport control is a layout fault to be seen in the log, not a crash on the vehicle."
        - "Register each with rect.inflate(BUTTON_TOUCH_EXPANSION * 2, BUTTON_TOUCH_EXPANSION * 2)."
        - "Return the visual rects."
    - name: "DisplayManager._draw_button"
      type: "function"
      purpose: "Draw one button in the declared style."
      interface:
        inputs:
          - name: "rect"
            type: "pygame.Rect"
            description: "The visual rect, as returned by _button_column."
          - name: "label"
            type: "str"
          - name: "fill"
            type: "Tuple[int, int, int]"
          - name: "font"
            type: "Optional[pygame.font.Font]"
        outputs:
          type: "None"
      logic:
        - "pygame.draw.rect fill with border_radius=TypographyConstants.BUTTON_CORNER_RADIUS."
        - "pygame.draw.rect outline with width=BUTTON_BORDER_WIDTH and the same border_radius."
        - "Centre the label on rect.center."
        - "Do NOT apply BUTTON_PRESS_SCALE. No pressed state is tracked; adding one is out of scope."
    - name: "DisplayManager._register_options_menu_regions"
      type: "function"
      purpose: "Three targets instead of four."
      logic:
        - "Call _button_column with three specs: simulation_mode, debug_toggle, check_updates."
        - "width 300, top 110. Three 72 px buttons with 16 px separation span 110 to 358, inside the 55-425 usable band."
        - "Store the returned rects as self._options_btn_sim, _options_btn_debug, _options_btn_update."
        - "Set self._options_btn_clear = None, so any stale reference is a visible None rather than an old rect."
    - name: "DisplayManager._register_confirm_view_regions"
      type: "function"
      purpose: "The confirmation's two targets."
      logic:
        - "Call _button_column with two specs: confirm_clear_yes -> self._on_clear_settings, confirm_clear_no -> a lambda returning _options_view to 'menu'."
        - "width 300, top 250, leaving room above for the consequence text."
        - "Store as self._confirm_btn_yes and self._confirm_btn_no."
    - name: "DisplayManager._draw_confirm_view"
      type: "function"
      purpose: "State the consequence, then offer the two controls."
      logic:
        - "Same background and border treatment as _draw_options_menu."
        - "Title 'Clear settings?' near y 100."
        - "Two lines of body text stating that the paired device will be erased and that setup will run at next start. Plain words; no jargon."
        - "Draw both controls through _draw_button. The confirming control is visually distinct — use (140, 40, 40) fill against (80, 80, 100) for cancel."
    - name: "DisplayManager._register_view_regions"
      type: "function"
      purpose: "Dispatch the new sub-view."
      logic:
        - "In the OPTIONS branch at manager.py:1074-1078, add: elif self._options_view == 'confirm_clear': self._register_confirm_view_regions()."
        - "Keep the existing 'update' branch and the else-branch to the menu."
    - name: "DisplayManager._draw_options_mode"
      type: "function"
      purpose: "Dispatch the new sub-view for rendering."
      logic:
        - "At manager.py:992-1000, add the matching 'confirm_clear' branch calling _draw_confirm_view."
    - name: "DisplayManager._on_clear_settings_requested"
      type: "function"
      purpose: "Enter the confirmation rather than acting."
      logic:
        - "Set self._options_view = 'confirm_clear'. Nothing else. It must not touch DeviceStore."
  dependencies:
    internal:
      - "TouchEventCoordinator.register_button_region — touch_coordinator.py:144. Called with the inflated rect. Not modified."
      - "_on_clear_settings — manager.py:1333. Body unchanged; reached only from the confirmation."
      - "_current_view_key — manager.py:1002. Already includes _options_view, so no change is needed. Verify this rather than assuming it."
    external:
      - "pygame.draw.rect border_radius — already used by typography.py:454-459."

error_handling:
  strategy: >
    Layout faults are logged and survivable, not fatal. A control that
    would fall outside the circular viewport is the same class of fault
    as the status indicator in display §8.1, which was invisible for as
    long as it took a review to find it — so it is logged at ERROR
    where it will be seen, and the frame still renders.
  exceptions:
    - exception: "None raised by the new code."
      condition: "Constraint violations."
      handling: "Clamp and log WARNING for height and separation; log ERROR for viewport violations."
    - exception: "Exception"
      condition: "Anything raised inside _register_view_regions."
      handling: "Unchanged from today — logged with a traceback and re-raised at manager.py:1083-1085, so _display_loop leaves _registered_view unchanged and retries the next frame."
  logging:
    level: "ERROR for viewport violations, WARNING for clamped geometry"
    format: "self.logger.error(f'Button {region_id} falls outside the circular viewport: {rect}')"

testing:
  unit_tests:
    - scenario: "_button_column with three specs, width 300, top 110."
      expected: "Three rects at y 110, 198, 286; all height 72; all x 90; width 300."
    - scenario: "The registered rects for the same call."
      expected: "Each is the visual rect inflated by 8 on each side — x 82, width 316, height 88."
    - scenario: "Adjacent registered rects in that column."
      expected: "They touch but do not overlap: 16 px separation less 8 px expansion each side."
    - scenario: "_button_column asked for height 55."
      expected: "72 is used and a WARNING is logged."
    - scenario: "_button_column asked for a column extending past y 425."
      expected: "An ERROR naming the region is logged; rects are still returned."
    - scenario: "All four corners of every rect in every view."
      expected: "(x-240)^2 + (y-240)^2 <= 238^2 holds for all."
    - scenario: "_register_options_menu_regions."
      expected: "Three regions registered; 'clear_settings' absent; self._options_btn_clear is None."
    - scenario: "_on_clear_settings_requested."
      expected: "_options_view becomes 'confirm_clear'; DeviceStore is not constructed or called."
    - scenario: "_current_view_key before and after that call."
      expected: "The key differs, so _display_loop re-registers."
    - scenario: "_register_confirm_view_regions."
      expected: "Two regions, both height 72, separation 16, both inside the viewport."
    - scenario: "The cancel callback."
      expected: "_options_view returns to 'menu'; DeviceStore is not called."
    - scenario: "The confirm callback."
      expected: "The existing _on_clear_settings runs — assert against the same mock it is asserted against today."
    - scenario: "_register_update_view_regions with _update_status 'available'."
      expected: "Two regions, height >= 72, separation >= 16, inside the viewport."
    - scenario: "_register_update_view_regions with _update_status 'checking'."
      expected: "No regions, unchanged from today."
    - scenario: "_register_disconnected_regions."
      expected: "Two regions, height >= 72, inside the viewport."
    - scenario: "Every _draw_button call, via a mocked rendering engine."
      expected: "border_radius == 6 passed on both the fill and the outline."
    - scenario: "_register_view_regions while _in_setup_mode is True."
      expected: "Returns immediately; clear_regions is not called."
    - scenario: "_register_acknowledgement_regions."
      expected: "One 480 x 480 region, not routed through _button_column."
  edge_cases:
    - "A width wide enough that the column's corners leave the viewport even at a legal height — the corner check is on the rect, not on the centre line, so a 460 px wide button fails at any y away from the centre. This is why the check exists."
    - "_options_view left at 'confirm_clear' when the mode changes away from OPTIONS: _current_view_key includes the mode, so the regions are replaced. Reset _options_view to 'menu' in the long-press handler that leaves OPTIONS (manager.py:202-205) so the confirmation is not waiting on the next entry."
    - "A callback that raises: register_button_region stores it and the coordinator invokes it; behaviour on raise is unchanged by this task."
    - "specs shorter than one entry — return an empty list without registering anything."
  validation:
    - "grep confirms no integer literal for button width, height or y remains inside any _draw_ method."
    - "git diff confirms touch_coordinator.py is unmodified."
    - "grep confirms register_button_region is not called from any method whose name begins with _draw_ or _render_."

deliverable:
  format_requirements:
    - "Edit the two files in place. Create no new file."
    - "Preserve the existing docstring style and the existing comment convention of citing the review section that motivated a change."
  files:
    - path: "src/gtach/display/typography.py"
      content: |
        Add three constants to TypographyConstants, immediately after the
        existing block at typography.py:114-117:

            # Minimum comfortable touch target for a panel operated by
            # hand in a moving vehicle. 72 px = 8.0 mm at the HyperPixel
            # 2.1 Round's 229 ppi. The four measured elements in the
            # display review all fell below this
            # (display review §7.3, recommendation 24).
            BUTTON_MIN_TOUCH_HEIGHT = 72
            BUTTON_MIN_SEPARATION = 16

            # The circular viewport. A control outside it is invisible
            # but still touch-sensitive — see display review §8.1.
            VIEWPORT_RADIUS = 238

        Change no existing constant. BUTTON_FLOATING remains (44, 44):
        it is consumed by this module's own button helpers at
        typography.py:352-365 and altering it is outside this task.
    - path: "src/gtach/display/manager.py"
      content: |
        SEVEN EDITS.

        EDIT 1 — add _button_column, near the other registration
        helpers and above _register_options_menu_regions
        (manager.py:1087). It computes, validates and registers; it does
        not draw.

        Signature:

            def _button_column(
                self,
                specs: Sequence[Tuple[str, TouchAction, Callable]],
                width: int,
                top: int,
                height: Optional[int] = None,
                separation: Optional[int] = None,
            ) -> List[pygame.Rect]:

        Body, in order:
          - height defaults to TypographyConstants.BUTTON_MIN_TOUCH_HEIGHT;
            separation defaults to max(BUTTON_MIN_SEPARATION,
            2 * BUTTON_TOUCH_EXPANSION).
          - Clamp both upward to those floors; log a WARNING naming the
            requested and the used value if either was raised.
          - For each (region_id, action, callback) at index i:
              rect = pygame.Rect(240 - width // 2,
                                 top + i * (height + separation),
                                 width, height)
          - Corner check per rect, against VIEWPORT_RADIUS about
            (240, 240), over rect.topleft, rect.topright,
            rect.bottomleft, rect.bottomright. On failure:
              self.logger.error(
                  f"Button {region_id} falls outside the circular "
                  f"viewport: {rect}"
              )
            Do not raise. Continue.
          - Register:
              expansion = TypographyConstants.BUTTON_TOUCH_EXPANSION
              self.touch_coordinator.register_button_region(
                  region_id,
                  rect.inflate(expansion * 2, expansion * 2),
                  action,
                  callback,
              )
          - Return the list of VISUAL rects.

        Document in the docstring that the returned rects are the visual
        ones and the registered ones are larger, because a future reader
        drawing the registered rect would draw a button 16 px wider than
        the one that was designed.

        EDIT 2 — add _draw_button, near _draw_options_menu:

            def _draw_button(self, rect, label, fill, font,
                             text_colour=(255, 255, 255)) -> None:

        Body:
          - surface = self.rendering_engine.get_surface(
                RenderTarget.BACK_BUFFER)
            and return if it is None, matching the guard style at
            manager.py:813-815.
          - pygame.draw.rect(surface, fill, rect,
                border_radius=TypographyConstants.BUTTON_CORNER_RADIUS)
          - pygame.draw.rect(surface, (140, 140, 160), rect,
                TypographyConstants.BUTTON_BORDER_WIDTH,
                border_radius=TypographyConstants.BUTTON_CORNER_RADIUS)
          - If font: render label centred on rect.center through
            self.rendering_engine.render_text with center=True.
          - Do NOT apply BUTTON_PRESS_SCALE.

        EDIT 3 — replace the body of _register_options_menu_regions
        (manager.py:1087-1105) with a three-item column:

            self._options_btn_clear = None
            rects = self._button_column(
                (
                    ("simulation_mode", TouchAction.SETTINGS_CHANGE,
                     lambda pos: self._on_simulation_mode()),
                    ("debug_toggle", TouchAction.SETTINGS_CHANGE,
                     lambda pos: self._on_debug_toggle()),
                    ("check_updates", TouchAction.SETTINGS_CHANGE,
                     lambda pos: self._on_check_updates()),
                ),
                width=300,
                top=110,
            )
            (self._options_btn_sim,
             self._options_btn_debug,
             self._options_btn_update) = rects

        Three 72 px buttons separated by 16 px span y 110 to 358, inside
        the 55-425 band a 300 px wide control has within the circular
        viewport. Clear settings is deliberately absent — it moves to
        the confirmation view in EDIT 5.

        EDIT 4 — rewrite the drawing loop in _draw_options_menu
        (manager.py:1203-1219) to iterate three rects and call
        _draw_button. Keep the title at y 55 and the "Long press to
        return" footer at y 400. Keep the existing sim_label and
        debug_label logic at manager.py:1200-1201 unchanged. Add a
        fourth control to neither the loop nor the screen.

        EDIT 5 — add the confirmation sub-view.

        (a) _on_clear_settings_requested — sets
            self._options_view = 'confirm_clear' and nothing else. This
            is the callback the options menu would have bound to Clear
            settings; it is now unbound there, so this method is
            reached only from the confirmation flow's entry point. Bind
            it wherever Clear settings is offered in future.

            NOTE: because Clear settings is no longer on the top-level
            menu, the only route into the confirmation is this method.
            Bind it to nothing in this change and record in the
            docstring that the entry point is deliberately open pending
            the §7.7 options re-layout (ai/task.md §7.3.15). If that is
            unacceptable, the alternative is to keep a fourth item and
            fail the geometry requirement — do not do that. Raise it
            instead.

        (b) _register_confirm_view_regions:

            rects = self._button_column(
                (
                    ("confirm_clear_yes", TouchAction.SETTINGS_CHANGE,
                     lambda pos: self._on_clear_settings()),
                    ("confirm_clear_no", TouchAction.SETTINGS_CHANGE,
                     lambda pos: self._on_cancel_clear()),
                ),
                width=300,
                top=250,
            )
            self._confirm_btn_yes, self._confirm_btn_no = rects

        (c) _on_cancel_clear — sets self._options_view = 'menu'. It must
            not call DeviceStore or _on_clear_settings.

        (d) _draw_confirm_view — background (40, 40, 50) and the red
            shift border, as _draw_options_menu does at
            manager.py:1183-1184. Title "Clear settings?" at (240, 100).
            Two body lines at (240, 170) and (240, 205) stating that the
            paired device will be erased and setup will run at the next
            start. Draw the two controls through _draw_button, the
            confirming one filled (140, 40, 40) and the cancel one
            (80, 80, 100).

        EDIT 6 — wire the sub-view in at both dispatch points.

        In _register_view_regions, the OPTIONS branch at
        manager.py:1074-1078 becomes:

            if self.config.mode == DisplayMode.OPTIONS:
                if self._options_view == 'update':
                    self._register_update_view_regions()
                elif self._options_view == 'confirm_clear':
                    self._register_confirm_view_regions()
                else:
                    self._register_options_menu_regions()

        In _draw_options_mode (manager.py:992-1000), add the matching
        'confirm_clear' branch calling _draw_confirm_view.

        In _handle_long_press (manager.py:202-205), where OPTIONS is
        left, also reset self._options_view = 'menu', so a confirmation
        abandoned by long press is not waiting on the next entry.

        EDIT 7 — bring the remaining two views to the minimum.

        _register_update_view_regions (manager.py:1107-1134): replace
        the two literal-y branches with _button_column calls. For
        'available', two specs — update_install then update_cancel —
        width 280, top 240. For 'none' and 'error', one spec,
        update_back, width 280, top 300. Keep the _update_btn_install /
        _update_btn_cancel attribute names and keep setting both to None
        at the top, because _draw_update_view guards on them.

        _register_disconnected_regions (manager.py:1146-1179): one
        _button_column call, two specs — disconnected_setup then
        disconnected_simulate — width 240, top 240. Separation rises
        from 20 to the default; confirm the column still ends inside the
        viewport, since a 240 px wide control has a wider usable band
        than a 300 px one.

        Then update _draw_update_view and _render_disconnected to draw
        their buttons through _draw_button rather than through bare
        draw_rect calls. Do not change what those methods decide to
        draw — only how a button is drawn.

success_criteria:
  - "python -m py_compile src/gtach/display/manager.py src/gtach/display/typography.py passes."
  - "pytest tests/ passes with no new failures."
  - "TypographyConstants declares BUTTON_MIN_TOUCH_HEIGHT = 72, BUTTON_MIN_SEPARATION = 16 and VIEWPORT_RADIUS = 238, and no pre-existing constant in that class has changed value."
  - "_button_column exists, returns visual rects, and registers rects inflated by BUTTON_TOUCH_EXPANSION on each axis."
  - "_draw_button exists and passes border_radius on both the fill and the outline."
  - "Every region registered by the options, confirm, update and disconnected views has height >= 72."
  - "Adjacent registered regions within any one view do not overlap."
  - "The options menu registers exactly three regions and 'clear_settings' is not among them."
  - "_options_view supports 'confirm_clear', and both _register_view_regions and _draw_options_mode dispatch on it."
  - "The cancel path does not reach DeviceStore."
  - "The confirm path invokes the unmodified _on_clear_settings."
  - "No call to register_button_region appears in any method whose name begins with _draw_ or _render_."
  - "src/gtach/display/input/touch_coordinator.py is byte-identical to its current text."
  - "_render_mode_selector, _register_rpm_sliders, _render_slider_visuals and _register_save_button are byte-identical to their current text."
  - "_on_clear_settings' body is byte-identical to its current text."
  - "_register_acknowledgement_regions is byte-identical to its current text."
  - "No file other than src/gtach/display/manager.py and src/gtach/display/typography.py is modified."

element_registry:
  source: ""
  entries:
    modules:
      - name: "manager"
        path: "src/gtach/display/manager.py"
      - name: "typography"
        path: "src/gtach/display/typography.py"
      - name: "touch_coordinator"
        path: "src/gtach/display/input/touch_coordinator.py"
    classes:
      - name: "DisplayManager"
        module: "gtach.display.manager"
      - name: "TypographyConstants"
        module: "gtach.display.typography"
      - name: "TouchEventCoordinator"
        module: "gtach.display.input.touch_coordinator"
    functions:
      - name: "_button_column"
        module: "gtach.display.manager"
        signature: "_button_column(self, specs, width: int, top: int, height: Optional[int] = None, separation: Optional[int] = None) -> List[pygame.Rect]"
      - name: "_draw_button"
        module: "gtach.display.manager"
        signature: "_draw_button(self, rect: pygame.Rect, label: str, fill: Tuple[int, int, int], font, text_colour: Tuple[int, int, int] = (255, 255, 255)) -> None"
      - name: "_register_confirm_view_regions"
        module: "gtach.display.manager"
        signature: "_register_confirm_view_regions(self) -> None"
      - name: "_draw_confirm_view"
        module: "gtach.display.manager"
        signature: "_draw_confirm_view(self) -> None"
      - name: "_on_clear_settings_requested"
        module: "gtach.display.manager"
        signature: "_on_clear_settings_requested(self) -> None"
      - name: "_on_cancel_clear"
        module: "gtach.display.manager"
        signature: "_on_cancel_clear(self) -> None"
    constants:
      - name: "BUTTON_MIN_TOUCH_HEIGHT"
        module: "gtach.display.typography"
      - name: "BUTTON_MIN_SEPARATION"
        module: "gtach.display.typography"
      - name: "VIEWPORT_RADIUS"
        module: "gtach.display.typography"

notes: >
  Executor is Claude Code; AEL is not used, so no tactical_brief is
  required (ai/task.md §7.2, governance P09 §1.10.2). Invoke from the
  project root:
  implement ai/workspace/prompt/prompt-b02ed4ea-button-system-touch-targets.md
  and close the prompt T-Doc when finished. Leave the issue and change
  T-Docs active pending test results (ai/task.md §8.2.1).

  ONE OPEN POINT, FLAGGED RATHER THAN DECIDED. EDIT 5(a) leaves the
  confirmation view without an entry point on the top-level menu,
  because the three-item budget has no room for a fourth control. The
  options screen therefore offers no route to Clear settings after this
  change. That is a deliberate consequence of recommendation 24 as
  written, and display report §7.7 — the circular options re-layout
  deferred to a P10 cycle in ai/task.md §7.3.15 — is where the recovered
  space would come from. If an entry point is required in v0.4.0, that
  is a scope extension to be agreed before this prompt is executed, not
  a decision for the executor. Do not resolve it by adding a fourth
  button.

  This change is visible on the panel and ships in v0.4.0 with the other
  appearance-changing triples (ai/task.md §8.5). The on-target step is
  ai/task.md §7.3.15's revisit: observe whether the three-item layout
  weakens §7.7's corner-region argument.
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-04 | Initial prompt document coupled to change-b02ed4ea. |

---

Copyright (c) 2026 William Watson. MIT License.
