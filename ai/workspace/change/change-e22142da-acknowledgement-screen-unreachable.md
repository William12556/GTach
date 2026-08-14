Created: 2026 August 14

# Change: Gate Entry to Normal Operation on Acknowledgement State

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [Version History](<#version history>)

---

## 1.0 Document Information

```yaml
change_info:
  id: "change-e22142da"
  title: "Add entry gate for DisplayMode.ACKNOWLEDGEMENT at the six normal-operation entry points"
  date: "2026-08-14"
  author: "William Watson"
  status: "proposed"
  priority: "high"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-e22142da"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-e22142da"
  description: >
    DisplayMode.ACKNOWLEDGEMENT is fully rendered and dismissed but has
    no entry trigger anywhere in src/gtach/. Add one.

scope:
  summary: >
    Add a new DisplayManager method, _enter_post_splash_mode(), that
    checks AcknowledgementStateManager.is_acknowledged() against the
    current RPM bands and engine profile and assigns
    DisplayMode.ACKNOWLEDGEMENT instead of self._post_splash_mode when
    not acknowledged. Replace the six existing unconditional
    "self.config.mode = self._post_splash_mode" assignments — two in
    start_splash(), three in _draw_splash_mode(), one in
    exit_setup_mode() — with calls to this method.
  affected_components:
    - name: "DisplayManager"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
  out_of_scope:
    - "_on_acknowledgement_dismissed() — its two 'self.config.mode = self._post_splash_mode' assignments are the exit path from ACKNOWLEDGEMENT and must remain unconditional. Gating them would mean dismissal could re-trigger the notice it is dismissing."
    - "Runtime engine-profile or RPM-threshold change detection — no UI control exists for changing engine_profile at runtime; this change gates the six existing entry points only, not a new change-detection channel."
    - "SetupScreen.DEVICE_MANAGEMENT / SetupScreen.CONFIRMATION — vestigial enum members noted as Findings B and C in the same report. Unrelated root cause; not addressed here."
    - "AcknowledgementStateManager itself (src/gtach/utils/ack_state.py) — complete and correct; this change adds its first caller, nothing else."

rational:
  problem_statement: >
    The acknowledgement notice cannot appear under any configuration,
    because nothing ever checks whether it is owed.
  proposed_solution: >
    Centralise the check in one new method and call it from every site
    that currently transitions into normal operation unconditionally.
  alternatives_considered:
    - option: "Gate only in _draw_splash_mode()'s splash-complete branch, the once-per-boot path."
      reason_rejected: >
        exit_setup_mode() is also a first-run entry into normal
        operation — the most important one, since first-time Bluetooth
        setup is exactly when the operator has never seen the notice —
        and start_splash()'s two branches are the same transition under
        different circumstances (no splash screen configured, or splash
        initialisation failing). Leaving any of the six ungated
        reopens the same class of gap for that specific path.
    - option: "Check is_acknowledged() once in _load_config() and cache the result on self."
      reason_rejected: >
        The six sites are the only places DisplayManager actually
        assigns a normal-operation mode value; gating at the point of
        assignment is simpler than threading a cached flag through six
        call sites and keeps the check co-located with its one
        consequence.
  benefits:
    - "Closes the safety-notice gap identified in issue-e22142da."
    - "Single new method, six one-line call-site edits; no new state, no new configuration."
    - "Fail-safe behaviour on error is symmetric with the existing pattern in _link_lost() — 'every failure path returns True' there, 'every failure path shows the notice' here."
  risks:
    - risk: >
        AcknowledgementStateManager.is_acknowledged() raising, or
        self._ack_state_manager being unset, could resolve toward
        always-showing or always-skipping the notice depending on which
        branch is chosen.
      mitigation: >
        The new method fails toward DisplayMode.ACKNOWLEDGEMENT on any
        exception from is_acknowledged() — a spurious extra tap costs
        less than a skipped safety notice, matching the risk asymmetry
        _link_lost() already documents for a different failure. Only a
        missing self._ack_state_manager attribute (meaning component
        initialisation itself failed) falls back to
        self._post_splash_mode, since without a state manager present
        dismissal could not persist its result either.
    - risk: >
        The log line in _draw_splash_mode()'s splash-complete branch
        currently reads self._post_splash_mode.name, which would
        misreport the destination once entry can resolve to
        ACKNOWLEDGEMENT instead.
      mitigation: "Prompt instructs the log line to read self.config.mode.name after the helper call runs, not self._post_splash_mode.name."

technical_details:
  current_behavior: >
    Six sites in DisplayManager assign
    self.config.mode = self._post_splash_mode unconditionally:
    start_splash() (no-splash-screen branch, exception handler),
    _draw_splash_mode() (no-splash-screen branch, splash-complete
    branch, exception handler), and exit_setup_mode(). No code path
    calls AcknowledgementStateManager.is_acknowledged().
  proposed_behavior: >
    All six sites call a new self._enter_post_splash_mode() instead.
    That method calls self._ack_state_manager.is_acknowledged() with
    the current self.config.rpm_bands and self.config.engine_profile;
    when it returns False, or raises, self.config.mode is set to
    DisplayMode.ACKNOWLEDGEMENT; otherwise to self._post_splash_mode,
    exactly as today. _on_acknowledgement_dismissed(), the only path
    back out of ACKNOWLEDGEMENT, is unchanged and remains unconditional.
  implementation_approach: >
    Single-file change confined to src/gtach/display/manager.py: one
    new ~15-line method, six one-line call-site substitutions, and one
    log-line correction.
  code_changes:
    - component: "DisplayManager"
      file: "src/gtach/display/manager.py"
      change_summary: >
        Add _enter_post_splash_mode(). Replace the six unconditional
        "self.config.mode = self._post_splash_mode" assignments in
        start_splash() and _draw_splash_mode() and exit_setup_mode()
        with calls to it. Correct the splash-complete log line to read
        the mode actually entered.
      functions_affected:
        - "_enter_post_splash_mode"
        - "start_splash"
        - "_draw_splash_mode"
        - "exit_setup_mode"
      classes_affected:
        - "DisplayManager"
  interface_changes:
    - interface: "DisplayManager._enter_post_splash_mode"
      change_type: "signature"
      details: "New private method; no existing interface altered."
      backward_compatible: "yes"

dependencies:
  internal:
    - component: "AcknowledgementStateManager"
      impact: "Gains its first caller (is_acknowledged()); no change to the class itself."
  required_changes: []

testing_requirements:
  test_approach: >
    Manual verification on device — no automated harness currently
    exercises the splash/setup-completion transition. Existing pytest
    suite must continue to pass; no test currently asserts on
    DisplayMode.ACKNOWLEDGEMENT entry, so none is expected to change
    behaviour incidentally.
  test_cases:
    - scenario: "Fresh install, no ~/.config/gtach/ack_state.yaml, first boot"
      expected_result: "After splash, ACKNOWLEDGEMENT shows; tap transitions to self._post_splash_mode."
    - scenario: "ack_state.yaml present, stored hash matches current rpm_bands and engine_profile"
      expected_result: "After splash, transitions directly to self._post_splash_mode; ACKNOWLEDGEMENT does not appear."
    - scenario: "engine_profile changed in config.yaml since the stored acknowledgement (hash mismatch)"
      expected_result: "ACKNOWLEDGEMENT reappears on the next boot."
    - scenario: "First-time Bluetooth setup completes (exit_setup_mode path), no prior acknowledgement"
      expected_result: "ACKNOWLEDGEMENT shows before the operator reaches the gauge."
    - scenario: "Dismiss ACKNOWLEDGEMENT by tapping"
      expected_result: "Transitions to self._post_splash_mode; state is persisted; does not reappear until acknowledgement state changes. _on_acknowledgement_dismissed() behaviour is unchanged by this change."
  regression_scope:
    - "src/gtach/display/manager.py — every route into normal operation from SPLASH or SETUP"
  validation_criteria:
    - "grep -n 'self\\.config\\.mode = self\\._post_splash_mode' src/gtach/display/manager.py matches only the two occurrences inside _on_acknowledgement_dismissed()."
    - "grep -n '_enter_post_splash_mode' src/gtach/display/manager.py shows one definition and six call sites."

implementation:
  rollback_procedure: "git revert the commit; no data migration involved."
  deployment_notes: >
    Deploy via existing bin/deploy.sh. No config.yaml schema change; the
    ack_state.yaml format AcknowledgementStateManager already defines is
    unchanged.

verification:
  implemented_date: ""
  implemented_by: ""
  verification_date: ""
  verified_by: ""
  test_results: ""

traceability:
  related_issues:
    - issue_ref: "issue-e22142da"
      relationship: "source"
    - issue_ref: "issue-f3a7c2e1"
      relationship: "related"

notes: >
  issue-f3a7c2e1 implemented the exit half of this screen (render,
  dismiss, persistence). This change adds the entry half that was never
  authored alongside it.

version_history:
  - version: "1.0"
    date: "2026-08-14"
    author: "William Watson"
    changes:
      - "Initial change creation."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.4"
  schema_type: "t02_change"
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date       | Changes           |
|---------|------------|--------------------|
| 1.0     | 2026-08-14 | Initial creation   |

---

Copyright (c) 2026 William Watson. MIT License.
