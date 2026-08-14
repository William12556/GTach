Created: 2026 August 14

# Issue: Acknowledgement Screen Unreachable — No Entry Trigger

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [Version History](<#version history>)

---

## 1.0 Document Information

```yaml
issue_info:
  id: "issue-e22142da"
  title: "DisplayMode.ACKNOWLEDGEMENT is fully built but no code path ever enters it"
  date: "2026-08-14"
  reporter: "William Watson"
  status: "open"
  severity: "high"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-e22142da"
    change_iteration: 1

source:
  origin: "code_review"
  description: >
    Navigation-reachability audit (report-b64d2b77-unreachable-navigation-screens.md,
    §4.0 Finding A) found that DisplayMode.ACKNOWLEDGEMENT is rendered,
    hit-tested, and dismissed correctly once active, but no code path
    in src/gtach/ ever assigns DisplayMode.ACKNOWLEDGEMENT to
    self.config.mode. AcknowledgementStateManager.is_acknowledged() is
    never called anywhere.

affected_scope:
  components:
    - name: "DisplayManager.start_splash"
      file_path: "src/gtach/display/manager.py"
    - name: "DisplayManager._draw_splash_mode"
      file_path: "src/gtach/display/manager.py"
    - name: "DisplayManager.exit_setup_mode"
      file_path: "src/gtach/display/manager.py"
    - name: "AcknowledgementStateManager"
      file_path: "src/gtach/utils/ack_state.py"
  version: "0.4.1"

reproduction:
  prerequisites: >
    None — the condition is unconditional. No ack_state.yaml is
    required to observe it; the screen never appears regardless of
    acknowledgement state, because nothing ever checks that state.
  steps:
    - "Delete or do not create ~/.config/gtach/ack_state.yaml (or leave it absent, the default on a fresh install)."
    - "Start GTach (systemd or manual invocation)."
    - "Observe the display through splash completion."
  frequency: "always"
  reproducibility_conditions: "Every startup and every completion of first-time Bluetooth setup."
  error_output: "None — no exception is raised; the omission is silent."

behavior:
  expected: >
    When the current RPM bands and engine profile have not been
    acknowledged (AcknowledgementStateManager.is_acknowledged() returns
    False), the display shows DisplayMode.ACKNOWLEDGEMENT — title,
    "OBD tachometer — experimental software", and a tap-to-dismiss
    instruction — before the operator reaches RADIAL, OPTIONS, or the
    DISCONNECTED screen.
  actual: >
    The display transitions directly from SPLASH (or from setup
    completion) to self._post_splash_mode. DisplayMode.ACKNOWLEDGEMENT
    is never assigned to self.config.mode by any code path.
  impact: >
    Safety-relevant: the acknowledgement notice cannot appear during
    normal operation under any configuration. The full render/dismiss/
    persistence mechanism built for it (_draw_acknowledgement_mode(),
    _register_acknowledgement_regions(), _on_acknowledgement_dismissed(),
    AcknowledgementStateManager) is complete but permanently idle.
  workaround: "None."

environment:
  python_version: "3.11"
  os: "Debian GNU/Linux 11 (Bullseye) 64-bit"
  domain: "domain_1"

analysis:
  root_cause: >
    change-f3a7c2e1 (issue-f3a7c2e1, closed 2026-05-26) implemented the
    exit half of the acknowledgement screen — the render branch in
    _render_normal_modes(), _draw_acknowledgement_mode(), the dismiss
    region, and _on_acknowledgement_dismissed() — in response to a
    report that the screen "does not block until explicitly dismissed."
    That fix addressed blocking correctly, but no change ever added the
    entry half: nothing calls AcknowledgementStateManager.is_acknowledged()
    or conditionally assigns DisplayMode.ACKNOWLEDGEMENT. A search of
    src/gtach/ for both symbols confirms every occurrence is either the
    definition, a downstream consumer of an already-set mode, or a
    transient-mode exclusion list (_load_config(), _save_config()). No
    trace of an entry trigger exists even in
    src/gtach/display/manager_backup.py, an earlier retained copy of
    this module.
  technical_notes: >
    Six sites in DisplayManager unconditionally assign
    self.config.mode = self._post_splash_mode, and are the only places
    that transition out of a transient state (SPLASH or SETUP) into
    normal operation: start_splash() (no-splash-screen branch and its
    exception handler), _draw_splash_mode() (no-splash-screen branch,
    splash-complete branch, and its exception handler), and
    exit_setup_mode(). Any one of these gates first-run acknowledgement;
    all six must, since each represents a distinct route by which the
    operator can reach normal operation without having seen the notice.
    A seventh and eighth occurrence of the same assignment, inside
    _on_acknowledgement_dismissed(), are the exit path and must not be
    touched.
  related_issues:
    - issue_ref: "issue-f3a7c2e1"
      relationship: "related"

resolution:
  assigned_to: "Claude Code"
  approach: "Per change-e22142da."

verification:
  test_results: ""
  closure_notes: ""

traceability:
  related_issues:
    - issue_ref: "issue-f3a7c2e1"

version_history:
  - version: "1.0"
    date: "2026-08-14"
    author: "William Watson"
    changes:
      - "Initial issue creation."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.3"
  schema_type: "t03_issue"
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date       | Changes           |
|---------|------------|--------------------|
| 1.0     | 2026-08-14 | Initial creation   |

---

Copyright (c) 2026 William Watson. MIT License.
