Created: 2026 August 07

# Prompt: Present the Page-Flip Pan Immediately, Not on the Next Vblank

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [Version History](<#version history>)

---

## 1.0 Document Information

```yaml
prompt_info:
  id: "prompt-e7a92c4f"
  task_type: "debug"
  source_ref: "change-e7a92c4f"
  target_profile: "claude_code"
  date: "2026-08-07"
  iteration: 1
  coupled_docs:
    change_ref: "change-e7a92c4f"
    change_iteration: 1

context:
  purpose: >
    _pan_display asks the driver to defer the page-flip pan to the next
    vertical-blanking interval (FB_ACTIVATE_VBL). On this target that
    ioctl is suspected to block indefinitely, hanging the display thread
    roughly 15 seconds into every session and silencing the watchdog
    heartbeat, which eventually shuts the whole application down after
    a 439-second timeout. _pan_display's own docstring already argues no
    synchronisation wait is needed in page-flip mode. Use FB_ACTIVATE_NOW
    instead, and add a diagnostic log bracket so a recurrence is
    immediately attributable.
  integration: >
    One file: src/gtach/display/rendering/engine.py. One method,
    _pan_display, two edits. Executor is Claude Code; AEL is not used.
  knowledge_references: []
  constraints:
    - "Modify only src/gtach/display/rendering/engine.py, and only within _pan_display."
    - "Do not change _setup_page_flip, _wait_for_vsync, write_to_framebuffer, cleanup, or any other method."
    - "Do not remove the FB_ACTIVATE_VBL or FB_ACTIVATE_NOW module-level constant definitions — both remain defined; only which one _pan_display uses changes."
    - "The log bracket must be guarded by self.logger.isEnabledFor(logging.DEBUG), matching the existing pattern at the end of _draw_radial_mode-equivalent DEBUG lines elsewhere in this codebase, so it costs nothing when debug logging is off."
    - "Do not change _pan_display's signature, return type, or exception handling — the existing try/except and _pan_failed_logged guard remain exactly as they are."
    - "Type hints and Google-style docstrings on any changed signature — none are expected to change here, but the docstring body must be updated to describe the new rationale."

specification:
  description: >
    In _pan_display, change the activation flag from FB_ACTIVATE_VBL to
    FB_ACTIVATE_NOW, update the surrounding comment to explain why, and
    add a DEBUG-guarded log line immediately before and after the
    FBIOPAN_DISPLAY ioctl call.
  requirements:
    functional:
      - "var[FB_VAR_ACTIVATE] is set to FB_ACTIVATE_NOW, not FB_ACTIVATE_VBL."
      - "A DEBUG-guarded log line is emitted immediately before the fcntl.ioctl(..., FBIOPAN_DISPLAY, ...) call, identifying the target index."
      - "A second DEBUG-guarded log line is emitted immediately after the ioctl call returns successfully, so a hang inside the call is visible as an unmatched entry with no exit in the log."
      - "The existing exception handler, _pan_failed_logged guard, and return values (True/False) are unchanged."
      - "The method's docstring is updated to state that FB_ACTIVATE_NOW is used because nothing reads the off-screen half, and that FB_ACTIVATE_VBL was found to risk blocking indefinitely on this driver (issue-e7a92c4f)."
    technical:
      language: "Python"
      version: "3.9+ (target runtime 3.11)"
      standards:
        - "Comprehensive error handling — unchanged from current implementation."
        - "Debug logging with traceback — the existing exception path already does this; unchanged."
        - "Professional docstrings"
  performance:
    - target: "No additional cost when debug logging is disabled"
      metric: "time"

design:
  architecture: >
    No architectural change. This is a single value substitution plus a
    diagnostic logging addition within an existing method.
  components:
    - name: "DisplayRenderingEngine._pan_display"
      type: "function"
      purpose: "Present a framebuffer half by moving the scan-out origin, applied immediately rather than deferred to the next vblank."
      interface:
        inputs:
          - name: "index"
            type: "int"
            description: "0 or 1 — which half to display."
        outputs:
          type: "bool"
          description: "True if the pan succeeded. Unchanged."
        raises:
          - "None. Unchanged — all exceptions remain caught internally."
      logic:
        - "Unchanged: guard on _fb_dev_usable() and self._panning_var is not None."
        - "Unchanged: unpack self._panning_var, set FB_VAR_YOFFSET to index * yres."
        - "CHANGED: set FB_VAR_ACTIVATE to FB_ACTIVATE_NOW instead of FB_ACTIVATE_VBL."
        - "NEW: if self.logger.isEnabledFor(logging.DEBUG), log 'Panning to buffer {index}' before the ioctl call."
        - "Unchanged: issue fcntl.ioctl(self.fb_dev.fileno(), FBIOPAN_DISPLAY, struct.pack(FB_VAR_STRUCT, *var))."
        - "NEW: if self.logger.isEnabledFor(logging.DEBUG), log 'Panned to buffer {index}' immediately after the ioctl call returns, before the return True."
        - "Unchanged: on exception, log once via _pan_failed_logged and return False."
  dependencies:
    internal:
      - "issue-e7a92c4f — this prompt implements its resolution.approach."
      - "change-49b21ace — introduced _pan_display; this prompt modifies code that change established."
    external: []

data_schema:
  entities:
    - name: "fb_var_screeninfo"
      attributes:
        - name: "activate"
          type: "__u32"
          constraints: "Index 21 (FB_VAR_ACTIVATE). Set to FB_ACTIVATE_NOW (0), not FB_ACTIVATE_VBL (16), by this change."
      validation:
        - "The struct is still read from self._panning_var, modified, and written back whole, exactly as before. Only the activate field's value changes."

error_handling:
  strategy: >
    Unchanged. The existing try/except around the ioctl call remains
    exactly as written; the new log lines sit inside the try block,
    around the ioctl call, and must not themselves be capable of raising
    in a way that changes the method's return-value contract (an
    isEnabledFor + logger.debug call does not raise under normal
    operation, so no additional guard is needed around the log calls
    themselves).
  exceptions:
    - exception: "OSError"
      condition: "FBIOPAN_DISPLAY fails at runtime — unchanged condition."
      handling: >
        Unchanged: _pan_failed_logged guard, one INFO log, return False.
        The new DEBUG entry log will have fired before the ioctl; the
        new DEBUG exit log will not fire, since the exception path
        returns before reaching it. This is intentional and is what
        makes an unmatched entry log diagnostic.
  logging:
    level: "DEBUG for the new bracket lines; existing INFO/ERROR handling for failures is unchanged."
    format: "Match the existing f-string DEBUG pattern used elsewhere in this file and in manager.py (e.g. the isEnabledFor(logging.DEBUG) guard before the 'Radial mode: RPM=' line in manager.py)."

testing:
  unit_tests:
    - scenario: "_pan_display succeeds with debug logging enabled."
      expected: "Both DEBUG log lines are emitted, in order; FB_VAR_ACTIVATE in the packed struct passed to the mocked ioctl is FB_ACTIVATE_NOW; method returns True."
    - scenario: "_pan_display succeeds with debug logging disabled."
      expected: "No log calls are made (isEnabledFor returns False); method returns True; behaviour otherwise identical."
    - scenario: "FBIOPAN_DISPLAY raises OSError."
      expected: "The entry DEBUG log fired; the exit DEBUG log did not; _pan_failed_logged is set; one INFO log emitted; method returns False. Identical to current behaviour except for the DEBUG entry log."
  edge_cases:
    - "self._panning_var is None — existing guard returns False before reaching either new log line or the activate-flag change. No behaviour change."
    - "Repeated calls — _pan_failed_logged must still suppress repeated INFO logging on repeated failures, unaffected by the new DEBUG lines."
  validation:
    - "grep -n 'FB_ACTIVATE_VBL' src/gtach/display/rendering/engine.py shows the constant definition remains, but no executable reference within _pan_display's body."
    - "grep -n 'FB_ACTIVATE_NOW' src/gtach/display/rendering/engine.py shows a reference within _pan_display that did not exist there before."

deliverable:
  format_requirements:
    - "Edit src/gtach/display/rendering/engine.py in place. Create no new file."
    - "Change only _pan_display's body (the activate-flag line, its surrounding comment, the docstring, and the two new log lines). Nothing else in the file changes."
  files:
    - path: "src/gtach/display/rendering/engine.py"
      content: |
        Locate the existing _pan_display method:

            def _pan_display(self, index: int) -> bool:
                """Present a framebuffer half by moving the scan-out origin.

                Args:
                    index: 0 or 1 — which half to display.

                Returns:
                    True if the pan succeeded.
                """
                if not self._fb_dev_usable() or self._panning_var is None:
                    return False

                try:
                    var = list(struct.unpack(FB_VAR_STRUCT, self._panning_var))
                    var[FB_VAR_YOFFSET] = index * var[FB_VAR_YRES]
                    # Asks the driver to latch at the next blanking interval.
                    # Not all drivers honour it; correctness does not depend on it.
                    var[FB_VAR_ACTIVATE] = FB_ACTIVATE_VBL
                    fcntl.ioctl(self.fb_dev.fileno(), FBIOPAN_DISPLAY,
                                struct.pack(FB_VAR_STRUCT, *var))
                    return True
                except Exception as e:
                    if not self._pan_failed_logged:
                        self._pan_failed_logged = True
                        self.logger.info(f"Page flip failed, reverting to direct write: {e}")
                    return False

        Replace it with:

            def _pan_display(self, index: int) -> bool:
                """Present a framebuffer half by moving the scan-out origin.

                Uses FB_ACTIVATE_NOW rather than FB_ACTIVATE_VBL. Page
                flipping's correctness does not depend on waiting for the
                next blanking interval — nothing reads the off-screen half
                being panned to — and FB_ACTIVATE_VBL was found to risk
                blocking this ioctl indefinitely on this target's driver,
                hanging the display thread with no exception and no way for
                the caller to detect or recover (issue-e7a92c4f).

                Args:
                    index: 0 or 1 — which half to display.

                Returns:
                    True if the pan succeeded.
                """
                if not self._fb_dev_usable() or self._panning_var is None:
                    return False

                try:
                    var = list(struct.unpack(FB_VAR_STRUCT, self._panning_var))
                    var[FB_VAR_YOFFSET] = index * var[FB_VAR_YRES]
                    # Applied immediately. FB_ACTIVATE_VBL asked the driver
                    # to defer to the next blanking interval for a benefit
                    # this design does not need, and was found to risk
                    # blocking indefinitely on this target (issue-e7a92c4f).
                    var[FB_VAR_ACTIVATE] = FB_ACTIVATE_NOW
                    if self.logger.isEnabledFor(logging.DEBUG):
                        self.logger.debug(f"Panning to buffer {index}")
                    fcntl.ioctl(self.fb_dev.fileno(), FBIOPAN_DISPLAY,
                                struct.pack(FB_VAR_STRUCT, *var))
                    if self.logger.isEnabledFor(logging.DEBUG):
                        self.logger.debug(f"Panned to buffer {index}")
                    return True
                except Exception as e:
                    if not self._pan_failed_logged:
                        self._pan_failed_logged = True
                        self.logger.info(f"Page flip failed, reverting to direct write: {e}")
                    return False

        Do not change the FB_ACTIVATE_VBL or FB_ACTIVATE_NOW constant
        definitions near the top of the file. Do not change any other
        method.

# Each criterion must be satisfiable by a correct execution of THIS
# prompt, checked against its own file constraints and deliverable text.
success_criteria:
  - "python -m py_compile src/gtach/display/rendering/engine.py passes."
  - "pytest tests/ passes with no new failures."
  - "grep -n 'var\\[FB_VAR_ACTIVATE\\] = FB_ACTIVATE_NOW' src/gtach/display/rendering/engine.py matches exactly once, inside _pan_display."
  - "grep -n 'var\\[FB_VAR_ACTIVATE\\] = FB_ACTIVATE_VBL' src/gtach/display/rendering/engine.py matches zero times in the file (the constant's own definition uses '=' in an assignment statement elsewhere at module scope, not this exact indented form, so this search is scoped to _pan_display's executable body by the exact indentation and left-hand side shown)."
  - "_pan_display's docstring mentions issue-e7a92c4f."
  - "Two new self.logger.debug(...) calls, both guarded by isEnabledFor(logging.DEBUG), appear inside _pan_display: one immediately before the fcntl.ioctl(..., FBIOPAN_DISPLAY, ...) call and one immediately after it."
  - "No file other than src/gtach/display/rendering/engine.py is modified."
  - "No method other than _pan_display is modified within engine.py."

element_registry:
  source: ""
  entries:
    modules:
      - name: "engine"
        path: "src/gtach/display/rendering/engine.py"
    classes:
      - name: "DisplayRenderingEngine"
        module: "gtach.display.rendering.engine"
    functions:
      - name: "_pan_display"
        module: "gtach.display.rendering.engine"
        signature: "_pan_display(self, index: int) -> bool"
    constants:
      - name: "FB_ACTIVATE_NOW"
        module: "gtach.display.rendering.engine"
        type: "int"
      - name: "FB_ACTIVATE_VBL"
        module: "gtach.display.rendering.engine"
        type: "int"

notes: >
  Executor is Claude Code; AEL is not used, so no tactical_brief is
  required (ai/task.md §7.2, governance P09 §1.10.2). Invoke from the
  project root:
  implement ai/workspace/prompt/prompt-e7a92c4f-pageflip-pan-hang.md
  and close the prompt when finished. Leave the issue and change active
  pending on-target results (ai/task.md §8.2.1) — this is a hypothesis-
  driven fix, not a confirmed one; issue-e7a92c4f's verification_enhanced
  steps require an extended on-target run gtach.local alone can provide.

  The root cause is suspected, not proven. If the extended on-target run
  in issue-e7a92c4f still hangs after this change, the new bracket log
  lines will show whether execution stopped inside FBIOPAN_DISPLAY
  (ruling this fix insufficient but confirming the location) or
  elsewhere entirely (ruling out this hypothesis and redirecting the
  investigation to the remainder of write_to_framebuffer or to
  _wait_for_vsync, which is not used while page_flip is True but would
  become relevant if page_flip is disabled by a failed pan).
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-07 | Initial prompt document coupled to change-e7a92c4f. |

---

Copyright (c) 2026 William Watson. MIT License.
