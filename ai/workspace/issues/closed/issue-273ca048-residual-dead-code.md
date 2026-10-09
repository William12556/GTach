Created: 2026 October 07

# Issue: Residual Dead Code

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: issue-273ca048
  title: Unreferenced helpers retained by change-cd5ec050 because they were not
    in its removal list
  date: '2026-10-07'
  reporter: Claude Code
  status: closed
  severity: low
  type: defect
  iteration: 1
  coupled_docs:
    change_ref: change-273ca048
    change_iteration: 1
source:
  origin: code_review
  test_ref: ''
  description: Recorded in report-cd5ec050 (kept items) and report-4005360c (unreachable
    trim branch). Findings B and C of report-b64d2b77 (vestigial SetupScreen members)
    folded in on 2026-10-09.
affected_scope:
  components:
  - name: TouchHandler.get_touch_interface_info
    file_path: src/gtach/display/touch.py
  - name: CircularPositioningEngine.get_circular_safe_area, clear_layout_cache
    file_path: src/gtach/display/setup_components/layout/circular_positioning.py
  - name: normalize_coordinates, denormalize_coordinates, HyperPixelTouchInterface.simulate_touch_event,
      MockHyperPixelTouch.simulate_touch
    file_path: src/gtach/display/touch_interface.py
  - name: ButtonSize, ButtonState
    file_path: src/gtach/display/typography.py
  - name: initialize_performance_manager, cleanup_performance_manager
    file_path: src/gtach/display/performance/__init__.py
  - name: SplashScreen.get_performance_report
    file_path: src/gtach/display/splash.py
  - name: ACQUIRE_TIMEOUT
    file_path: tests/conftest.py
  - name: SetupScreen.DEVICE_MANAGEMENT, SetupScreen.CONFIRMATION
    file_path: src/gtach/display/setup_models.py
  - name: SetupScreen.CONFIRMATION entry in the render-cache screen list
    file_path: src/gtach/display/setup.py
  designs:
  - design_ref: ''
  version: 34c1ffd
reproduction:
  prerequisites: ''
  steps:
  - grep each name over src, tests and bin.
  frequency: always
  reproducibility_conditions: ''
  preconditions: ''
  test_data: ''
  error_output: ''
behavior:
  expected: No unreachable code in src/ or unused constants in tests/.
  actual: touch.py:345; circular_positioning.py:63,384; touch_interface.py:219,448,741,759;
    typography.py:49,59; performance/__init__.py:22,30 (exported only); splash.py:724
    (its trim branch at :772 is unreachable since change-4005360c bounded the deque);
    conftest.py:53; setup_models.py:29,30 (SetupScreen members with no render
    branch or transition); setup.py:324 (CONFIRMATION in the should_cache list).
  impact: Maintenance cost only.
  workaround: ''
environment:
  python_version: 3.9+ (observed on 3.13)
  os: Linux
  dependencies:
  - library: ''
    version: ''
  domain: ''
analysis:
  root_cause: change-cd5ec050 removed only listed items (its constraint); these
    became or stayed unreferenced.
  technical_notes: Re-check each name with grep before removal.
  related_issues:
  - issue_ref: issue-cd5ec050
    relationship: related
resolution:
  assigned_to: ''
  target_date: ''
  approach: Remove after a fresh reference check.
  change_ref: change-273ca048
  resolved_date: '2026-10-09'
  resolved_by: Claude Code (change-273ca048, commit bf03008)
  fix_description: ''
verification:
  verified_date: '2026-10-09'
  verified_by: William Watson
  test_results: test-273ca048 passed (5/5); no source reference to removed names; SetupScreen values unchanged; normal use on gtach.local.
  closure_notes: Closed. Further dead code left in place by constraint is listed in report-273ca048 section 6.
prevention:
  preventive_measures: ''
  process_improvements: ''
verification_enhanced:
  verification_steps:
  - grep finds no reference other than the definitions before removal; pytest passes
    after.
  verification_results: ''
traceability:
  design_refs:
  - ''
  change_refs:
  - change-273ca048
  test_refs:
  - ''
notes: Follow-up to change-cd5ec050. Also covers report-b64d2b77 findings B and C; the owner confirmed on 2026-10-09 that neither screen is reserved for planned use.
loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ''
  last_review_feedback: ''
version_history:
- version: '1.0'
  date: '2026-10-07'
  author: Claude Code
  changes:
  - Initial issue document, raised at the close of audit-36b6ea95 remediation.
- version: '1.1'
  date: '2026-10-09'
  author: William Watson
  changes:
  - Folded in report-b64d2b77 findings B and C (SetupScreen.DEVICE_MANAGEMENT, SetupScreen.CONFIRMATION and the setup.py:324 cache-list entry).
- version: '1.2'
  date: '2026-10-09'
  author: William Watson
  changes:
  - Coupled to change-273ca048 (P03.7).
- version: '1.3'
  date: '2026-10-09'
  author: William Watson
  changes:
  - Resolved by change-273ca048; verified by test-273ca048; closed.
metadata:
  copyright: Copyright (c) 2026 William Watson. MIT License.
  template_version: '1.0'
  schema_type: t03_issue
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-07 | Initial issue document. Raised at the close of audit-36b6ea95 remediation. |
| 1.1 | 2026-10-09 | Folded in report-b64d2b77 findings B and C. |
| 1.2 | 2026-10-09 | Coupled to change-273ca048. |
| 1.3 | 2026-10-09 | Resolved by change-273ca048; verified by test-273ca048; closed. |

---

Copyright (c) 2026 William Watson. MIT License.
