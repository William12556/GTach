Created: 2026 August 05

# Prompt: Two Pages, Wrapping, and Clear Settings Reachable Again

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [Version History](<#version history>)

---

## 1.0 Document Information

```yaml
prompt_info:
  id: "prompt-8c5a1e73"
  task_type: "implementation"
  source_ref: "change-8c5a1e73"
  target_profile: "claude_code"
  date: "2026-08-05"
  iteration: 1
  coupled_docs:
    change_ref: "change-8c5a1e73"
    change_iteration: 1

context:
  purpose: >
    Clear settings, its confirmation view and its cancel path are all
    implemented and none can be reached. change-b02ed4ea evicted the
    control to meet the 72 px touch minimum — four targets do not fit
    the circular viewport — built the confirmation that recommendation
    24 also required, and left the entry point unbound because supplying
    one was a scope decision. The operator has taken it: page the
    options screen with a horizontal swipe.
  integration: >
    Two files: src/gtach/display/manager.py and
    src/gtach/display/touch.py. Executor is Claude Code; AEL is not
    used.

    PAGE CONTENTS, as specified by the operator on 2026-08-05:

      page 0 — Bluetooth / Simulation mode, Debug
      page 1 — Clear settings, Check for updates

    Wrapping in both directions.

    HOW GESTURES ARE DELIVERED HERE. The touch coordinator's
    register_gesture_callback mechanism does not dispatch —
    handle_touch_up and handle_touch_move are called by nothing
    (issue-2b6f4d91). Every gesture that works in this application is
    wired by direct call from TouchHandler:

      vertical swipes  touch.py:202-209  -> _handle_swipe_down/_up
      long press       touch.py          -> _handle_long_press

    Wire the horizontal swipes the same way. Do NOT register them with
    the coordinator; it will look correct, log "Registered callback for
    SWIPE_LEFT", and never fire.
  knowledge_references: []
  constraints:
    - "Modify only src/gtach/display/manager.py and src/gtach/display/touch.py."
    - "Do NOT modify src/gtach/display/input/."
    - "Do NOT register the horizontal swipes with the touch coordinator. See above."
    - "Do NOT bind any menu region directly to _on_clear_settings. Page 1 binds _on_clear_settings_requested, which enters the confirmation. A one-tap destructive action is the finding recommendation 24 exists to prevent."
    - "Do NOT modify _on_clear_settings, _on_clear_settings_requested, _on_cancel_clear, _register_confirm_view_regions or _draw_confirm_view. All are change-b02ed4ea's and all are correct."
    - "Do NOT modify _button_column or _draw_button."
    - "Do NOT apply paging to the 'update' or 'confirm_clear' sub-views. The menu only."
    - "Do NOT put more than three targets on any page. Two is the design; three is the hard maximum."
    - "Do NOT disturb the vertical-swipe delegation at touch.py:202-209 or the long-press delegation. Both are working features."
    - "Type hints preserved; Google-style docstrings; PEP 8."

specification:
  description: >
    Add a page index to the options menu, carry it in the view key,
    register and draw per page, add a page indicator, and page with
    wrapping horizontal swipes delivered from TouchHandler.
  requirements:
    functional:
      - "_current_view_key includes _options_page."
      - "Page 0 registers exactly simulation_mode and debug_toggle."
      - "Page 1 registers exactly clear_settings and check_updates."
      - "clear_settings invokes _on_clear_settings_requested."
      - "A horizontal swipe changes page, wrapping in both directions."
      - "Horizontal swipes act only in OPTIONS with _options_view 'menu' and not in setup mode."
      - "A page indicator shows which of the two pages is displayed."
      - "Entering OPTIONS always shows page 0."
      - "All targets on both pages are >= 72 px high, >= 16 px apart, inside the r=238 viewport."
      - "Vertical swipes and the long-press palette toggle are unaffected."
    technical:
      language: "Python"
      version: "3.9+ (target runtime 3.9)"
      standards:
        - "Thread-safe if concurrent access"
        - "Comprehensive error handling"
        - "Debug logging with traceback"
        - "Professional docstrings"
  performance:
    - target: "None. Registration fires on view change; drawing adds two small circles"
      metric: "time"

design:
  architecture: >
    Registration follows the view key. A page is view state, so it goes
    in the key — otherwise the regions of one page are registered while
    another is drawn, and the controls are in the wrong places. That is
    a worse fault than the missing control this change restores.
  components:
    - name: "DisplayManager._options_page"
      type: "attribute"
      purpose: "Which options page is displayed."
      logic:
        - "int, 0 or 1. Initialised 0 in __init__. Session state; not persisted."
    - name: "DisplayManager._current_view_key"
      type: "function"
      purpose: "Carry the page."
      logic:
        - "Append self._options_page to the returned tuple."
        - "Extend the docstring's list of members to say why it is there."
    - name: "DisplayManager._register_options_menu_regions"
      type: "function"
      purpose: "Register the current page's two controls."
      logic:
        - "Set all four rect attributes to None first, so an off-page reference is a visible None."
        - "Select specs by self._options_page."
        - "One _button_column call, width 300, top 140, two specs."
        - "Assign the returned rects to the two attributes for that page."
    - name: "DisplayManager._draw_options_menu"
      type: "function"
      purpose: "Draw the current page and the indicator."
      logic:
        - "Draw the two rects for the current page through _draw_button."
        - "Draw two dots at y 350, centres x 230 and 250; the active page filled, the other outlined."
        - "Read self._palette once for the dot colours."
    - name: "DisplayManager._handle_swipe_left / _handle_swipe_right"
      type: "function"
      purpose: "Page, with wrapping."
      interface:
        inputs:
          - name: "start_pos"
            type: "Tuple[int, int]"
          - name: "end_pos"
            type: "Tuple[int, int]"
        outputs:
          type: "TouchAction"
      logic:
        - "Return NONE if _in_setup_mode, if mode is not OPTIONS, or if _options_view is not 'menu'."
        - "left: (page + 1) % 2. right: (page - 1) % 2. Modulo gives the wrapping."
        - "Return NAVIGATION."
    - name: "TouchHandler._handle_short_press"
      type: "function"
      purpose: "Deliver whichever swipe dominates."
      logic:
        - "Compute dx and dy. If the larger exceeds the threshold, dispatch to that axis."
        - "MUST be tested before the OPTIONS early return."
  dependencies:
    internal:
      - "change-b02ed4ea — supplies _button_column and the confirmation view. Read-only."
      - "change-3e8b1d72 — the vertical swipes and the early-return ordering constraint."
      - "change-5012004e — the palette the indicator reads."
    external: []

error_handling:
  strategy: >
    Follows the existing gesture handlers: catch, log at ERROR, return
    NONE. A paging failure must not propagate onto the touch thread.
  exceptions:
    - exception: "Exception"
      condition: "Anything in either paging handler."
      handling: "Log at ERROR and return TouchAction.NONE."
    - exception: "Exception"
      condition: "Anything in _register_options_menu_regions."
      handling: "Existing handler in _register_view_regions logs and re-raises, so _display_loop retries next frame. Unchanged."
  logging:
    level: "DEBUG on a page change so the sequence is diagnosable from a log"
    format: "self.logger.debug(f'Options page -> {self._options_page}')"

testing:
  unit_tests:
    - scenario: "THE PRINCIPAL TEST. _current_view_key with _options_page 0, then 1."
      expected: "The two tuples differ. If this fails, every other test in this list can pass while the screen shows the wrong controls."
    - scenario: "_register_options_menu_regions with _options_page 0."
      expected: "Registered ids are exactly {simulation_mode, debug_toggle}."
    - scenario: "The same with _options_page 1."
      expected: "Exactly {clear_settings, check_updates}."
    - scenario: "The four rect attributes after registering page 0."
      expected: "The two page-1 attributes are None."
    - scenario: "The clear_settings callback."
      expected: "_on_clear_settings_requested — _options_view becomes 'confirm_clear'. DeviceStore not constructed or called."
    - scenario: "grep the registration method for _on_clear_settings."
      expected: "Not present. Only _on_clear_settings_requested appears."
    - scenario: "_handle_swipe_left twice from page 0."
      expected: "Page 1, then page 0."
    - scenario: "_handle_swipe_right twice from page 0."
      expected: "Page 1, then page 0."
    - scenario: "Either handler with mode RADIAL, with _options_view 'update', with 'confirm_clear', and with _in_setup_mode True."
      expected: "No page change; NONE returned; four separate assertions."
    - scenario: "All four corners of every rect on both pages."
      expected: "(x-240)^2 + (y-240)^2 <= 238^2; height >= 72; separation >= 16."
    - scenario: "TouchHandler._handle_short_press, dx 150 dy 10, mode OPTIONS, sub-view menu."
      expected: "Page changes."
    - scenario: "The same with dx 10 dy 150."
      expected: "Leaves OPTIONS; page unchanged."
    - scenario: "Diagonal, dx 120 dy 100."
      expected: "Pages — horizontal dominates. State the expected outcome in the test name."
    - scenario: "Diagonal, dx 100 dy 120."
      expected: "Leaves OPTIONS — vertical dominates."
    - scenario: "Small dx and dy inside OPTIONS."
      expected: "Routed to _handle_options_touch; a button tap still works."
    - scenario: "Horizontal swipe with mode RADIAL."
      expected: "Nothing; no exception."
    - scenario: "_handle_swipe_down into OPTIONS with _options_page left at 1."
      expected: "_options_page is 0."
    - scenario: "The page indicator."
      expected: "Two dots; the filled index equals _options_page."
    - scenario: "Long press in RADIAL after the change."
      expected: "Still toggles the palette."
  edge_cases:
    - "THE EARLY-RETURN ORDERING, again. _handle_short_press returns early for setup mode and then for OPTIONS. Both swipe tests must sit between those two returns — after setup, before OPTIONS — or a swipe inside OPTIONS never reaches a handler. change-3e8b1d72 met this for the vertical case; the horizontal case has exactly the same shape."
    - "A pure diagonal, abs(dx) == abs(dy). Pick one deterministically — prefer vertical, since leaving OPTIONS is the more recoverable outcome — and state the choice in a comment."
    - "The page count is 2. Use a named constant or len() of a page table rather than a literal 2 in the modulo, so a third page is a data change."
    - "_options_page is session state and must NOT be added to _save_config. An operator returning to OPTIONS after a restart should see page 0."
    - "The indicator is drawn, not registered. It must not appear in the touch region set."
    - "If _button_column is called with two specs at top 140: rects at y 140 and y 228, both 300x72. Verify the corners against the viewport rather than assuming — a 300 px width has a narrower usable band than the 240 px controls elsewhere."
  validation:
    - "grep confirms _options_page appears in _current_view_key."
    - "grep confirms no register_gesture_callback call for SWIPE_LEFT or SWIPE_RIGHT."
    - "git diff confirms display/input/ and the confirmation-view methods are untouched."

deliverable:
  format_requirements:
    - "Edit the two files in place. Create no new file."
    - "One commit."
  files:
    - path: "src/gtach/display/manager.py"
      content: |
        SIX EDITS. Do EDIT 2 first and test it before the rest.

        EDIT 1 — state. In __init__, beside _pre_options_mode:

            # Which options page is displayed. Session state; not
            # persisted, so OPTIONS always opens on page 0
            # (change-8c5a1e73).
            self._options_page = 0

        EDIT 2 — THE KEY. In _current_view_key, add self._options_page
        to the returned tuple, and add to the docstring's list of
        members:

            - _options_page: the menu pages its controls, so the page
              is part of what determines which regions exist. Omitting
              it would register one page's regions and draw the
              other's.

        Write the key test now and confirm it passes before continuing.
        Everything below is inert without this edit.

        EDIT 3 — registration. Replace the body of
        _register_options_menu_regions:

            self._options_btn_clear = None
            self._options_btn_sim = None
            self._options_btn_debug = None
            self._options_btn_update = None

            if self._options_page == 0:
                specs = (
                    ("simulation_mode", TouchAction.SETTINGS_CHANGE,
                     lambda pos: self._on_simulation_mode()),
                    ("debug_toggle", TouchAction.SETTINGS_CHANGE,
                     lambda pos: self._on_debug_toggle()),
                )
            else:
                specs = (
                    ("clear_settings", TouchAction.SETTINGS_CHANGE,
                     lambda pos: self._on_clear_settings_requested()),
                    ("check_updates", TouchAction.SETTINGS_CHANGE,
                     lambda pos: self._on_check_updates()),
                )

            rects = self._button_column(specs, width=300, top=140)

            if self._options_page == 0:
                self._options_btn_sim, self._options_btn_debug = rects
            else:
                self._options_btn_clear, self._options_btn_update = rects

        Note clear_settings binds _on_clear_settings_requested, NOT
        _on_clear_settings. The confirmation is the point.

        EDIT 4 — drawing. In _draw_options_menu, draw the current
        page's two controls through _draw_button, then the indicator:

            palette = self._palette
            for i in range(2):
                cx = 230 + i * 20
                if i == self._options_page:
                    pygame.draw.circle(surface, palette.tick, (cx, 350), 4)
                else:
                    pygame.draw.circle(surface, palette.tick, (cx, 350), 4, 1)

        Keep the title and the "Swipe up to return" footer. The
        indicator is drawn only; it must not be registered.

        EDIT 5 — the paging handlers, beside _handle_swipe_up:

            def _handle_swipe_left(self, start_pos, end_pos) -> TouchAction:
                """Page forward through the options menu, wrapping."""
                return self._page_options(+1)

            def _handle_swipe_right(self, start_pos, end_pos) -> TouchAction:
                """Page back through the options menu, wrapping."""
                return self._page_options(-1)

            def _page_options(self, delta: int) -> TouchAction:
                try:
                    if self._in_setup_mode:
                        return TouchAction.NONE
                    if self.config.mode != DisplayMode.OPTIONS:
                        return TouchAction.NONE
                    if self._options_view != 'menu':
                        return TouchAction.NONE
                    self._options_page = (
                        self._options_page + delta
                    ) % OPTIONS_PAGE_COUNT
                    self.logger.debug(
                        f'Options page -> {self._options_page}'
                    )
                    return TouchAction.NAVIGATION
                except Exception as e:
                    self.logger.error(f'Options paging error: {e}')
                    return TouchAction.NONE

        Define OPTIONS_PAGE_COUNT = 2 as a class constant rather than a
        literal, so a third page is a data change.

        EDIT 6 — reset on entry. In _handle_swipe_down, beside the
        existing self._options_view = 'menu':

            self._options_page = 0
    - path: "src/gtach/display/touch.py"
      content: |
        EDIT 7 — deliver the horizontal swipe.

        READ _handle_short_press IN FULL FIRST. It returns early for
        setup mode and then for OPTIONS. change-3e8b1d72 placed the
        vertical test between those two returns for a reason: a test
        after the OPTIONS return never runs inside OPTIONS. The
        horizontal test has the same requirement and goes in the same
        place.

        Replace the existing vertical-only block with a
        dominant-axis dispatch:

                # Vertical swipes move between the gauge and OPTIONS
                # (change-3e8b1d72); horizontal swipes page within the
                # options menu (change-8c5a1e73). Tested before the
                # OPTIONS early return below, or neither would reach a
                # handler from inside OPTIONS. The dominant axis wins;
                # an exact diagonal is treated as vertical, leaving
                # OPTIONS being the more recoverable outcome.
                dx = x - start_x
                dy = y - start_y
                if max(abs(dx), abs(dy)) >= 100:
                    if abs(dx) > abs(dy):
                        if dx < 0:
                            self.display_manager._handle_swipe_left(
                                (start_x, start_y), (x, y)
                            )
                        else:
                            self.display_manager._handle_swipe_right(
                                (start_x, start_y), (x, y)
                            )
                    else:
                        if dy > 0:
                            self.display_manager._handle_swipe_down(
                                (start_x, start_y), (x, y)
                            )
                        else:
                            self.display_manager._handle_swipe_up(
                                (start_x, start_y), (x, y)
                            )
                    return

        Keep the threshold consistent with whatever the current
        vertical block uses — read it rather than assuming 100, and say
        in the commit message which value was found.

        Leave the setup and OPTIONS early returns exactly as they are.

success_criteria:
  - "python -m py_compile src/gtach/display/manager.py src/gtach/display/touch.py passes."
  - "pytest tests/ passes with no new failures."
  - "_current_view_key returns a different tuple for _options_page 0 and 1."
  - "Page 0 registers exactly simulation_mode and debug_toggle; page 1 exactly clear_settings and check_updates."
  - "The off-page rect attributes are None."
  - "clear_settings invokes _on_clear_settings_requested; no menu region binds _on_clear_settings."
  - "_handle_swipe_left and _handle_swipe_right wrap in both directions."
  - "Neither pages outside OPTIONS, outside the 'menu' sub-view, or in setup mode."
  - "Every rect on both pages is >= 72 px high, >= 16 px apart, and wholly inside r=238 about (240, 240)."
  - "TouchHandler dispatches to the dominant axis and both tests precede the OPTIONS early return."
  - "_handle_swipe_down resets _options_page to 0."
  - "OPTIONS_PAGE_COUNT is a named constant, not a literal in the modulo."
  - "_options_page is not written by _save_config."
  - "No register_gesture_callback call exists for SWIPE_LEFT or SWIPE_RIGHT."
  - "src/gtach/display/input/ is byte-identical."
  - "_on_clear_settings, _on_clear_settings_requested, _on_cancel_clear, _register_confirm_view_regions and _draw_confirm_view are byte-identical."
  - "The vertical-swipe and long-press delegations still function."
  - "No file other than the two named above is modified."

element_registry:
  source: ""
  entries:
    modules:
      - name: "manager"
        path: "src/gtach/display/manager.py"
      - name: "touch"
        path: "src/gtach/display/touch.py"
    classes:
      - name: "DisplayManager"
        module: "gtach.display.manager"
      - name: "TouchHandler"
        module: "gtach.display.touch"
    functions:
      - name: "_current_view_key"
        module: "gtach.display.manager"
        signature: "_current_view_key(self) -> tuple"
      - name: "_register_options_menu_regions"
        module: "gtach.display.manager"
        signature: "_register_options_menu_regions(self) -> None"
      - name: "_draw_options_menu"
        module: "gtach.display.manager"
        signature: "_draw_options_menu(self) -> None"
      - name: "_handle_swipe_left"
        module: "gtach.display.manager"
        signature: "_handle_swipe_left(self, start_pos, end_pos) -> TouchAction"
      - name: "_handle_swipe_right"
        module: "gtach.display.manager"
        signature: "_handle_swipe_right(self, start_pos, end_pos) -> TouchAction"
      - name: "_page_options"
        module: "gtach.display.manager"
        signature: "_page_options(self, delta: int) -> TouchAction"
      - name: "_handle_short_press"
        module: "gtach.display.touch"
        signature: "_handle_short_press(self, x: int, y: int, start_x: int, start_y: int) -> None"
    constants:
      - name: "OPTIONS_PAGE_COUNT"
        module: "gtach.display.manager"

notes: >
  Executor is Claude Code; AEL is not used, so no tactical_brief is
  required (ai/task.md §7.2, governance P09 §1.10.2). Invoke from the
  project root:
  implement ai/workspace/prompt/prompt-8c5a1e73-options-page-navigation.md
  and close the prompt T-Doc when finished. Leave the issue and change
  T-Docs active pending test results. Then, once you are finished, write
  a report of what you have done in the ai/workspace/report folder.

  Do EDIT 2 first and prove it. A page index without a matching view-key
  member registers one page's regions and draws the other's — controls
  in the wrong places, which is a worse fault than the missing control
  this change restores, and it will look like a rendering bug rather
  than a registration one.

  Two other ways to get this wrong, both of which compile:

    - registering the horizontal swipes with the touch coordinator.
      It logs a successful registration and never fires
      (issue-2b6f4d91);
    - putting the swipe test after the OPTIONS early return in
      _handle_short_press, which makes paging unreachable from inside
      the very screen it pages.

  On the panel afterwards, judge whether the two-item pages weaken
  display report §7.7's corner-region argument. ai/task.md §7.3.15
  defers §7.7 to a P10 cycle with the revisit conditioned on observing
  the reduced layout; this change reduces it further, and §7.7 may be
  closable rather than deferred.
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-05 | Initial prompt document coupled to change-8c5a1e73. |

---

Copyright (c) 2026 William Watson. MIT License.
