Created: 2026 May 29

# Change: Reset display mode to post-splash target on setup exit

---

## Table of Contents

- [1.0 Change Information](<#1.0 change information>)
- [2.0 Source](<#2.0 source>)
- [3.0 Scope](<#3.0 scope>)
- [4.0 Rationale](<#4.0 rationale>)
- [5.0 Technical Details](<#5.0 technical details>)
- [6.0 Testing Requirements](<#6.0 testing requirements>)
- [Version History](<#version history>)

---

## 1.0 Change Information

```yaml
change_info:
  id: "change-c84ffe6f"
  title: "Reset display mode to post-splash target on setup exit"
  date: "2026-05-29"
  author: "William Watson"
  status: "approved"
  priority: "high"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-c84ffe6f"
    issue_iteration: 1
```

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Source

```yaml
source:
  type: "issue"
  reference: "issue-c84ffe6f"
  description: >
    Resolves Finding A (symptom S2) from audit-ui-navigation-logic-report.md:
    a stale OPTIONS display mode persists through in-process setup re-entry,
    causing the OPTIONS screen to render after re-pairing.
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Scope

```yaml
scope:
  summary: >
    On exit from setup mode, restore config.mode to the normal post-splash target
    (_post_splash_mode) so the connected display renders after setup completes.

  affected_components:
    - name: "DisplayManager.exit_setup_mode"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"

  affected_designs:
    - design_ref: "design-b8c9d0e1-component_display_manager.md"
      sections: ["5.1"]

  out_of_scope:
    - "Changes to the splash or acknowledgement transition logic"
    - "Changes to _re_enter_setup or _start_obd in app.py"
    - "Persisting OPTIONS or any transient mode"
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Rationale

```yaml
rational:
  problem_statement: >
    exit_setup_mode() clears the setup flag but leaves config.mode unchanged. When
    setup is re-entered from the OPTIONS screen, config.mode remains OPTIONS, and the
    normal-mode dispatcher renders the OPTIONS screen after setup completes.

  proposed_solution: >
    Set config.mode = self._post_splash_mode at the end of exit_setup_mode().
    _post_splash_mode is already maintained as the intended normal display mode and
    is local to DisplayManager, requiring no cross-component access.

  alternatives_considered:
    - option: "Reset config.mode in GTachApplication._on_setup_complete (app.py)"
      reason_rejected: >
        Requires reaching into the private _post_splash_mode attribute from the
        application layer; exit_setup_mode is the single owner of the transition.

  benefits:
    - "Connected display renders after re-pairing via the clear-settings workflow"
    - "Single-site fix at the owner of the setup-exit transition"

  risks:
    - risk: "OBD thread not yet RUNNING immediately after _start_obd"
      mitigation: >
        Expected and correct: _render_normal_modes shows DISCONNECTED until the
        thread reports RUNNING, then RADIAL/DIGITAL — no regression.
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Technical Details

```yaml
technical_details:
  current_behavior: >
    exit_setup_mode() sets _in_setup_mode=False and _setup_manager=None only.
    config.mode retains whatever value it held before setup (OPTIONS when entered
    via 'Clear settings'). The OPTIONS screen renders after setup completes.

  proposed_behavior: >
    exit_setup_mode() additionally sets config.mode = self._post_splash_mode, so the
    normal-mode dispatcher renders the connected RADIAL/DIGITAL screen after setup.

  implementation_approach: >
    Add a single assignment in DisplayManager.exit_setup_mode() before the log line:
    self.config.mode = self._post_splash_mode.

  code_changes:
    - component: "DisplayManager"
      file: "src/gtach/display/manager.py"
      change_summary: >
        In exit_setup_mode(), set self.config.mode = self._post_splash_mode after
        clearing _in_setup_mode and _setup_manager.
      functions_affected:
        - "exit_setup_mode"

  interface_changes:
    - interface: "DisplayManager.exit_setup_mode"
      change_type: "contract"
      details: "No signature change; post-condition now restores normal display mode."
      backward_compatible: "yes"
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Testing Requirements

```yaml
testing_requirements:
  test_approach: "Manual on-device verification on gtach.local after deployment."

  test_cases:
    - scenario: "Clear settings from OPTIONS, then re-pair and tap Continue"
      expected_result: "Connected RADIAL/DIGITAL screen renders; OPTIONS screen not shown"
    - scenario: "Re-pair completes while OBD thread still starting"
      expected_result: "DISCONNECTED briefly, then RADIAL/DIGITAL once RUNNING"
    - scenario: "Normal setup on first run (no prior device)"
      expected_result: "Connected screen renders after setup; no regression"

  regression_scope:
    - "First-run setup completion path"
    - "DISCONNECTED → Setup → re-pair path"

  validation_criteria:
    - "gtach-debug.log shows Radial/Digital render markers immediately after 'Exited setup mode'"
    - "No manual long-press required to reach the connected screen after re-pairing"
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.0 | 2026-05-29 | Initial change document. |

---

Copyright (c) 2026 William Watson. MIT License.
