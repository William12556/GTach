Created: 2026 August 14

# Prompt: Add Entry Gate for DisplayMode.ACKNOWLEDGEMENT

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [Version History](<#version history>)

---

## 1.0 Document Information

```yaml
prompt_info:
  id: "prompt-e22142da"
  task_type: "debug"
  source_ref: "change-e22142da"
  target_profile: "claude_code"
  date: "2026-08-14"
  iteration: 1
  coupled_docs:
    change_ref: "change-e22142da"
    change_iteration: 1

context:
  purpose: >
    DisplayMode.ACKNOWLEDGEMENT is fully rendered, hit-tested, and
    dismissed by existing code, but no code path ever assigns it to
    self.config.mode, so the acknowledgement notice can never appear.
    Add the missing entry gate.
  integration: >
    Six sites in DisplayManager (src/gtach/display/manager.py)
    unconditionally assign self.config.mode = self._post_splash_mode
    when transitioning out of a transient state into normal operation:
    two in start_splash(), three in _draw_splash_mode(), one in
    exit_setup_mode(). A seventh and eighth occurrence of the identical
    line, inside _on_acknowledgement_dismissed(), is the exit path from
    ACKNOWLEDGEMENT and is explicitly excluded from this change. Add
    one new method, _enter_post_splash_mode(), and call it from the six
    included sites in place of the direct assignment.
  constraints:
    - "Do not modify _on_acknowledgement_dismissed() in any way. Its two 'self.config.mode = self._post_splash_mode' assignments (one in its try block, one in its except fallback) must remain exactly as they are — this is the exit path from ACKNOWLEDGEMENT, and gating it would prevent dismissal from ever completing, or could re-trigger the notice it is in the middle of dismissing."
    - "Do not modify AcknowledgementStateManager (src/gtach/utils/ack_state.py) — it is complete and already used correctly by _on_acknowledgement_dismissed(). This prompt adds its first call to is_acknowledged() only."
    - "Do not add any mechanism to detect RPM-threshold or engine-profile changes at runtime (e.g. polling, a config file watcher). No UI control exists in this codebase for changing engine_profile while running; the gate only needs to run at the six existing entry points into normal operation, where the current config is already being read."
    - "Do not change DisplayMode, SetupScreen, or any other enum in src/gtach/display/models.py or setup_models.py."

specification:
  description: >
    Add DisplayManager._enter_post_splash_mode() to
    src/gtach/display/manager.py. It resolves self.config.mode to
    either DisplayMode.ACKNOWLEDGEMENT or self._post_splash_mode based
    on AcknowledgementStateManager.is_acknowledged(), and is called
    from the six sites listed below in place of the direct assignment
    they currently perform.
  requirements:
    functional:
      - "self._enter_post_splash_mode() calls self._ack_state_manager.is_acknowledged(self.config.rpm_bands, self.config.engine_profile)."
      - "When is_acknowledged() returns False, self.config.mode is set to DisplayMode.ACKNOWLEDGEMENT."
      - "When is_acknowledged() returns True, self.config.mode is set to self._post_splash_mode, exactly as every current call site does today."
      - "When is_acknowledged() raises any exception, the exception is caught, logged at ERROR with exc_info=True, and self.config.mode is set to DisplayMode.ACKNOWLEDGEMENT (fail toward showing the notice, not skipping it)."
      - "When self._ack_state_manager does not exist as an attribute on self (component initialisation failed before it was set), self.config.mode is set to self._post_splash_mode with no exception raised and no attribute error — this is the one branch that does NOT fail toward ACKNOWLEDGEMENT, because without a state manager present, a later dismissal could not persist its result either."
      - "start_splash()'s no-splash-screen branch and its exception handler both call self._enter_post_splash_mode() instead of assigning self.config.mode directly."
      - "_draw_splash_mode()'s no-splash-screen branch, its splash-complete branch, and its exception handler all call self._enter_post_splash_mode() instead of assigning self.config.mode directly."
      - "exit_setup_mode() calls self._enter_post_splash_mode() instead of assigning self.config.mode directly."
      - "The log line in _draw_splash_mode()'s splash-complete branch — currently f\"Splash completed - transitioning to {self._post_splash_mode.name}\" — is changed to read the mode actually entered: f\"Splash completed - transitioning to {self.config.mode.name}\", read AFTER the call to self._enter_post_splash_mode() so it reports ACKNOWLEDGEMENT when that is what was entered."
      - "_on_acknowledgement_dismissed() is not modified in any way."
    technical:
      language: "Python"
      version: "3.11"
      standards:
        - "Match the existing docstring and try/except-with-logging style used throughout DisplayManager (see _toggle_palette, _handle_swipe_down for examples of the established pattern)."
        - "No new imports required — DisplayMode and AcknowledgementStateManager are already imported in manager.py."

design:
  architecture: "One new private method on DisplayManager, called from six existing call sites in place of a direct assignment; no new components, no new state."
  components:
    - name: "DisplayManager._enter_post_splash_mode"
      type: "method"
      purpose: >
        Resolve and assign self.config.mode when transitioning from a
        transient state (SPLASH or SETUP) into normal operation, gating
        on acknowledgement state.
      interface:
        inputs: []
        outputs:
          type: "None"
          description: "Sets self.config.mode as its sole side effect."
        raises: []
      logic:
        - >
          Insert immediately after _draw_splash_mode() and before
          _render_setup_mode() (or any position adjacent to the splash/
          setup transition methods — exact placement within the class
          is not load-bearing).
        - >
          Method body:
          "def _enter_post_splash_mode(self) -> None:" followed by a
          docstring stating that it gates entry into normal operation
          on acknowledgement state, that it is called from
          start_splash(), _draw_splash_mode(), and exit_setup_mode(),
          and that _on_acknowledgement_dismissed() is the only path
          back out and is intentionally not gated.
        - >
          try: read ack_manager = getattr(self, '_ack_state_manager',
          None). If ack_manager is None, set
          self.config.mode = self._post_splash_mode and return.
        - >
          Otherwise call
          ack_manager.is_acknowledged(self.config.rpm_bands,
          self.config.engine_profile) inside the same try block. If it
          returns False, set self.config.mode =
          DisplayMode.ACKNOWLEDGEMENT and return. If it returns True,
          fall through to the final assignment below.
        - >
          except Exception as e: log at ERROR with exc_info=True
          ("Acknowledgement state check failed: {e}" or equivalent),
          set self.config.mode = DisplayMode.ACKNOWLEDGEMENT, and
          return.
        - >
          After the try/except, if execution reaches this point (only
          possible on the True-return path with no exception), set
          self.config.mode = self._post_splash_mode.
    - name: "DisplayManager.start_splash"
      type: "method"
      purpose: "Existing method. Replace two direct assignments with calls to the new gate."
      logic:
        - >
          In the else branch ("No splash screen available - skipping
          to normal mode"), replace
          "self.config.mode = self._post_splash_mode" with
          "self._enter_post_splash_mode()".
        - >
          In the except Exception as e branch, replace
          "self.config.mode = self._post_splash_mode" with
          "self._enter_post_splash_mode()".
    - name: "DisplayManager._draw_splash_mode"
      type: "method"
      purpose: "Existing method. Replace three direct assignments with calls to the new gate, and correct the splash-complete log line."
      logic:
        - >
          In the "if not self._splash_screen:" early-return branch,
          replace "self.config.mode = self._post_splash_mode" with
          "self._enter_post_splash_mode()"; the "return" that follows
          is unchanged.
        - >
          In the "if self._splash_screen.is_complete():" branch,
          replace "self.config.mode = self._post_splash_mode" with
          "self._enter_post_splash_mode()", called BEFORE the log line
          immediately below it. Change that log line from
          f"Splash completed - transitioning to
          {self._post_splash_mode.name}" to f"Splash completed -
          transitioning to {self.config.mode.name}", so it reads the
          mode the gate actually chose.
        - >
          In the outer "except Exception as e:" handler, replace
          "self.config.mode = self._post_splash_mode" with
          "self._enter_post_splash_mode()".
    - name: "DisplayManager.exit_setup_mode"
      type: "method"
      purpose: "Existing method. Replace its one direct assignment with a call to the new gate."
      logic:
        - >
          Replace "self.config.mode = self._post_splash_mode" with
          "self._enter_post_splash_mode()". The two lines above it
          (_in_setup_mode = False, _setup_manager = None) and the log
          line below it are unchanged.
    - name: "DisplayManager._on_acknowledgement_dismissed"
      type: "method"
      purpose: >
        NOT MODIFIED. Listed here only to state explicitly that its two
        "self.config.mode = self._post_splash_mode" assignments (main
        path and exception fallback) are out of scope and must be
        left exactly as they are.
  dependencies:
    internal:
      - "DisplayManager._enter_post_splash_mode calls self._ack_state_manager.is_acknowledged(), previously uncalled from anywhere."
    external: []

error_handling:
  strategy: >
    _enter_post_splash_mode() catches any exception from
    is_acknowledged() and resolves toward showing the notice
    (DisplayMode.ACKNOWLEDGEMENT), not toward skipping it — the
    established asymmetry in this codebase (see _link_lost()'s
    docstring: "EVERY FAILURE PATH RETURNS True"). The one exception is
    a missing self._ack_state_manager attribute, which is not caught as
    an exception (it is checked explicitly via getattr) and resolves to
    self._post_splash_mode, since a state manager that does not exist
    cannot later persist a dismissal either.
  exceptions:
    - exception: "Exception (broad, matching existing handlers in this class)"
      condition: "AcknowledgementStateManager.is_acknowledged() raises"
      handling: "Log at ERROR with exc_info=True; set self.config.mode = DisplayMode.ACKNOWLEDGEMENT."
  logging:
    level: "ERROR"
    format: "Match existing DisplayManager style, e.g. self.logger.error(f'Acknowledgement state check failed: {e}', exc_info=True)"

testing:
  unit_tests:
    - scenario: "self._ack_state_manager.is_acknowledged() returns False"
      expected: "self.config.mode == DisplayMode.ACKNOWLEDGEMENT after _enter_post_splash_mode() returns."
    - scenario: "self._ack_state_manager.is_acknowledged() returns True"
      expected: "self.config.mode == self._post_splash_mode after _enter_post_splash_mode() returns."
    - scenario: "self._ack_state_manager.is_acknowledged() raises an exception"
      expected: "self.config.mode == DisplayMode.ACKNOWLEDGEMENT after _enter_post_splash_mode() returns; no exception propagates out of the method."
    - scenario: "self._ack_state_manager attribute does not exist on self"
      expected: "self.config.mode == self._post_splash_mode after _enter_post_splash_mode() returns; no AttributeError propagates out of the method."
  edge_cases:
    - "_post_splash_mode itself equal to DisplayMode.ACKNOWLEDGEMENT is impossible by construction — _load_config() already excludes ACKNOWLEDGEMENT from the set of values _post_splash_mode can take (the _transient tuple check) — so this method never needs to guard against gating into a target that is already ACKNOWLEDGEMENT."
  validation:
    - "Full pytest suite run after the edits; no new failures relative to the pre-change baseline."
    - "Manual on-device verification per change-e22142da §testing_requirements.test_cases, since no automated harness currently exercises the splash/setup-completion transition."

deliverable:
  format_requirements:
    - "Edit src/gtach/display/manager.py in place; no new files."
  files:
    - path: "src/gtach/display/manager.py"
      content: "Modified per design section above: one new method, six call-site substitutions, one log-line correction."

success_criteria:
  - "grep -n '_enter_post_splash_mode' src/gtach/display/manager.py returns exactly one 'def _enter_post_splash_mode' and six call sites reading 'self._enter_post_splash_mode()' (two in start_splash, three in _draw_splash_mode, one in exit_setup_mode) — seven matches total in src/gtach/display/manager.py."
  - "grep -n 'self\\.config\\.mode = self\\._post_splash_mode' src/gtach/display/manager.py returns exactly two matches, both inside _on_acknowledgement_dismissed() (its try block and its except fallback), and the one inside the newly added _enter_post_splash_mode() itself — three matches total, none of them at any of the six replaced call sites."
  - "grep -n 'transitioning to {self.config.mode.name}' src/gtach/display/manager.py matches the corrected splash-complete log line; grep -n 'transitioning to {self._post_splash_mode.name}' src/gtach/display/manager.py returns no match anywhere in the file."
  - "_on_acknowledgement_dismissed() is byte-for-byte unchanged from its state before this prompt was executed."
  - "python -m py_compile src/gtach/display/manager.py succeeds."
  - "Full pytest suite (pytest tests/) passes with no new failures relative to the pre-change baseline."

element_registry:
  source: ""
  entries:
    methods:
      - name: "_enter_post_splash_mode"
        module: "src/gtach/display/manager.py"
        signature: "def _enter_post_splash_mode(self) -> None"

notes: >
  This prompt implements change-e22142da / issue-e22142da. No
  tactical_brief is required — target_profile is claude_code, not ael.
  The success criteria's exact match counts assume no other occurrence
  of 'self.config.mode = self._post_splash_mode' exists in the file
  before this prompt runs beyond the eight already accounted for
  (six replaced, two in the untouched dismiss handler); if the
  executing agent finds a different count present before editing, it
  should stop and report the discrepancy rather than proceed on a
  mismatched assumption.

version_history:
  - version: "1.0"
    date: "2026-08-14"
    author: "William Watson"
    changes:
      - "Initial prompt creation."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.11"
  schema_type: "t04_prompt"
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date       | Changes           |
|---------|------------|--------------------|
| 1.0     | 2026-08-14 | Initial creation   |

---

Copyright (c) 2026 William Watson. MIT License.
