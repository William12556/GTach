Created: 2026 October 07

# Issue: A Failed Page-Flip Pan Freezes the Panel

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-70789d75"
  title: "After a pan failure with scan-out on the second buffer half, page flipping is disabled but every later frame is written to the first half, which is not displayed"
  date: "2026-10-07"
  reporter: "William Watson"
  status: "open"
  severity: "high"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-70789d75"
    change_iteration: 1

source:
  origin: "code_review"
  test_ref: ""
  description: "Raised from audit-36b6ea95 finding D02 (high, suspected)."

affected_scope:
  components:
    - name: "DisplayRenderingEngine frame write (page-flip and single-buffer branches)"
      file_path: "src/gtach/display/rendering/engine.py"
    - name: "DisplayRenderingEngine._pan_display"
      file_path: "src/gtach/display/rendering/engine.py"
  designs: []
  version: "0.4.3"

reproduction:
  prerequisites: "Page flipping active on the Pi (mmap path, second half established)."
  steps:
    - "Run until at least one successful flip (buffer_index 1)."
    - "Cause FBIOPAN_DISPLAY to fail once (in test: patch _pan_display to return False)."
  frequency: "rare (depends on a driver pan error)"
  reproducibility_conditions: "Deterministic in a unit test; on hardware only on a pan error."
  test_data: >
    engine.py:798-818. Page-flip branch: target = buffer_index ^ 1;
    write payload at target * fb_size; if _pan_display(target) is True,
    buffer_index = target, else page_flip = False (buffer_index and the
    hardware y-offset stay on the previously displayed half). The
    single-buffer branch then writes at offset 0 on every frame.
    _pan_display logs the failure once at INFO (engine.py:502-505).
  error_output: "One INFO line: 'Page flip failed, reverting to direct write'."

behavior:
  expected: "After a pan failure, frames continue to reach the displayed half."
  actual: >
    CONFIRMED IN SOURCE. If the displayed half is 1 when the pan fails,
    all later frames are written to half 0, which is not scanned out. The
    panel shows the last good frame indefinitely while the display
    thread, its heartbeat and the watchdog report healthy. Whether the
    driver ever returns a pan error on this target is not established.
  impact: "A frozen RPM indication with no visible fault."
  workaround: "Restart the service."

environment:
  python_version: "3.9"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies: []
  domain: "domain_1"

analysis:
  root_cause: "The single-buffer branch assumes the displayed half is always half 0."
  technical_notes: >
    Writing to the displayed half (buffer_index * fb_size) in the
    single-buffer branch fixes the defect without a second ioctl. It is
    correct in every case: buffer_index is 0 whenever page flipping was
    never established, and after a failed pan it still names the half
    that is displayed.
  related_issues:
    - issue_ref: "issue-e7a92c4f"
      relationship: "related. Established FB_ACTIVATE_NOW panning."

resolution:
  assigned_to: ""
  target_date: ""
  approach: >
    Single-buffer branch writes at buffer_index * fb_size. On pan
    failure, also write the current frame to the displayed half so it is
    not lost. Log the pan failure at WARNING so it reaches error.log.
  change_ref: "change-70789d75"
  resolved_date: ""
  resolved_by: ""
  fix_description: "After a failed pan the current and all later frames are written to the displayed framebuffer half (buffer_index * fb_size), and the one-time pan failure is logged at WARNING (commit b814ed9ce2786808fc708578ab45e158ef53adc1)."

verification:
  verified_date: ""
  verified_by: ""
  test_results: ""
  closure_notes: ""

prevention:
  preventive_measures: "Unit test of the pan-failure path."
  process_improvements: "None."

verification_enhanced:
  verification_steps:
    - "Confirm from source. [DONE.]"
    - "After the fix: unit tests per change-70789d75."
  verification_results: "First step complete."

traceability:
  design_refs: []
  change_refs:
    - "change-70789d75"
  test_refs: []

notes: "Audit reference: audit-36b6ea95 D02."

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-10-07"
    author: "William Watson"
    changes:
      - "Initial issue document from audit-36b6ea95 D02."

  - version: "1.1"
    date: "2026-10-07"
    author: "Claude Code"
    changes:
      - "Fix implemented in b814ed9ce2786808fc708578ab45e158ef53adc1; awaiting on-device verification."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t03_issue"
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-07 | Initial issue document. Frames written to the undisplayed half after a pan failure. |
| 1.1 | 2026-10-07 | Fix implemented in b814ed9ce2786808fc708578ab45e158ef53adc1; awaiting on-device verification. |

---

Copyright (c) 2026 William Watson. MIT License.
