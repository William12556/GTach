Created: 2026 May 29

# Prompt: Reset display mode to post-splash target on setup exit

---

## Table of Contents

- [1.0 Prompt Information](<#1.0 prompt information>)
- [2.0 Context](<#2.0 context>)
- [3.0 Specification](<#3.0 specification>)
- [4.0 Design](<#4.0 design>)
- [5.0 Error Handling](<#5.0 error handling>)
- [6.0 Testing](<#6.0 testing>)
- [7.0 Deliverable](<#7.0 deliverable>)
- [8.0 Tactical Brief](<#8.0 tactical brief>)
- [Version History](<#version history>)

---

## 1.0 Prompt Information

```yaml
prompt_info:
  id: "prompt-c84ffe6f"
  task_type: "debug"
  source_ref: "change-c84ffe6f"
  date: "2026-05-29"
  iteration: 1
  status: "closed"
  coupled_docs:
    change_ref: "change-c84ffe6f"
    change_iteration: 1
```

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Context

```yaml
context:
  purpose: >
    Restore the normal display mode when leaving setup, so the connected screen
    renders after re-pairing via the clear-settings workflow.

  integration: >
    Display domain: src/gtach/display/manager.py. Single function change in
    DisplayManager.exit_setup_mode. No other files or domains affected.

  constraints:
    - "Modify only DisplayManager.exit_setup_mode in src/gtach/display/manager.py"
    - "Do not change app.py, splash logic, or _render_normal_modes"
    - "Exclude setup_original_backup.py and any *_backup.py from all changes"
    - "Read manager.py around exit_setup_mode before editing"
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Specification

```yaml
specification:
  description: >
    On setup exit, set config.mode to the post-splash target so the normal-mode
    dispatcher renders the connected RADIAL/DIGITAL screen instead of a stale OPTIONS.

  requirements:
    functional:
      - "exit_setup_mode() sets self.config.mode = self._post_splash_mode"
      - "Assignment occurs after clearing _in_setup_mode and _setup_manager"
      - "No other behaviour in exit_setup_mode changes"
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Preserve existing logging"
        - "No interface/signature change"
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Design

```yaml
design:
  architecture: "Single-statement fix in existing method; no new components"

  components:
    - name: "DisplayManager.exit_setup_mode"
      type: "function"
      purpose: "Clear setup state and restore the normal display mode"
      logic:
        - "Set self._in_setup_mode = False (existing)"
        - "Set self._setup_manager = None (existing)"
        - "Set self.config.mode = self._post_splash_mode (new)"
        - "Log 'Exited setup mode' (existing)"

  dependencies:
    internal:
      - "manager.py: DisplayManager._post_splash_mode (already maintained)"
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Error Handling

```yaml
error_handling:
  strategy: "No new error paths; assignment is unconditional and safe."
  logging:
    level: "INFO"
    format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Testing

```yaml
testing:
  unit_tests:
    - scenario: "Call exit_setup_mode with _post_splash_mode == RADIAL"
      expected: "config.mode == DisplayMode.RADIAL after the call"
  edge_cases:
    - "exit_setup_mode called when config.mode already RADIAL — no change observed"
  validation:
    - "On-device: connected screen renders after clear-settings re-pair without long-press"
    - "gtach-debug.log shows 'Radial mode'/'band colour' markers immediately after 'Exited setup mode'"
```

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Deliverable

```yaml
deliverable:
  format_requirements:
    - "Modify file in place; preserve all behaviour not in scope"
  files:
    - path: "src/gtach/display/manager.py"
      content: "Add config.mode reset to _post_splash_mode in exit_setup_mode"

success_criteria:
  - "exit_setup_mode sets config.mode to _post_splash_mode"
  - "Connected screen renders after re-pairing via clear-settings"
  - "No changes outside exit_setup_mode"
```

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Tactical Brief

```yaml
tactical_brief: |
  Modify one function in src/gtach/display/manager.py. Read the function before
  editing. Exclude any *_backup.py files.

  Target: DisplayManager.exit_setup_mode(self).

  Current body:
    self._in_setup_mode = False
    self._setup_manager = None
    self.logger.info("Exited setup mode")

  Change: add one line before the log call so the body becomes:
    self._in_setup_mode = False
    self._setup_manager = None
    self.config.mode = self._post_splash_mode
    self.logger.info("Exited setup mode")

  Rationale: 'Clear settings' is pressed from the OPTIONS screen, so config.mode is
  OPTIONS when setup re-enters in-process. exit_setup_mode previously left config.mode
  unchanged, so the normal-mode dispatcher rendered OPTIONS after re-pairing. Resetting
  to _post_splash_mode restores the connected RADIAL/DIGITAL screen.

  Hard constraints:
  - Only this function changes. Do not touch app.py, splash logic, or _render_normal_modes.
  - No signature change. Preserve the existing log line.

  Deliverable: modified manager.py saved in place.
  Verify: exit_setup_mode assigns self.config.mode = self._post_splash_mode.
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.0 | 2026-05-29 | Initial prompt. |

---

Copyright (c) 2026 William Watson. MIT License.
