# Change: Order Pre-Release Versions in the Update Check

Created: 2026 November 13

## Table of Contents

- [1.0 Change Information](#10-change-information)
- [Version History](#version-history)

---

## 1.0 Change Information

```yaml
change_info:
  id: "change-c41037ea"
  title: "Read PEP 440 pre-release versions in the update check and order them below their final release"
  date: "2026-11-13"
  author: "Claude Code session (proposal-f8d0064b), for William Watson"
  status: "approved"
  priority: "high"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-c41037ea"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-c41037ea"
  description: "Finding H01 of audit-bce0d69a."

scope:
  summary: "One function body and one log record in src/gtach/utils/updater.py; one new test module."
  affected_components:
    - name: "_parse_version_str; find_available_update"
      file_path: "src/gtach/utils/updater.py"
      change_type: "modify"
  affected_designs:
    - design_ref: "design-9a1f3c7e-domain_utils"
      sections:
        - "4.3 Updater"
  out_of_scope:
    - "Development, post-release, local and epoch versions (still not recognised)."
    - "bin/gtach-preflight.sh, bin/deploy.sh, bin/build.sh."
    - "The update view texts and layout."
    - "The fixed /opt/gtach/updates location (audit-bce0d69a L07)."

rational:
  problem_statement: "See issue-c41037ea."
  proposed_solution: >
    EDIT A: _parse_version_str recognises the normalised PEP 440 form
    N(.N)*[{a|b|rc}N] with a module-level regular expression. It returns
    an order key: the release numbers padded with zeros to at least three
    components, followed by a phase rank (a = -3, b = -2, rc = -1,
    final = 0) and the pre-release number (0 for a final release). Tuple
    comparison then orders 1.0.0a1 < 1.0.0b1 < 1.0.0rc1 < 1.0.0rc2 <
    1.0.0 < 1.0.1, and 1.0 equals 1.0.0. Any other string returns None,
    as before. The return type stays Optional[Tuple[int, ...]].
    EDIT B: find_available_update logs one WARNING when the installed
    version is not recognised, and one DEBUG record for a wheel whose
    version is not recognised, so that an inert check leaves a record.
  alternatives_considered:
    - option: "Use packaging.version.Version."
      reason_rejected: "packaging is not a declared dependency; adding one for a single comparison enlarges the install on the Pi."
    - option: "Release 1.0.0 directly (D1 alternative), avoiding pre-release versions."
      reason_rejected: "D1 was accepted by the owner; the defect would remain for any later release candidate."
    - option: "Strip the pre-release segment and compare release numbers only."
      reason_rejected: "1.0.0rc1 would equal 1.0.0, so the final release would not be offered to a release-candidate installation."
  benefits:
    - "The staged-update path works for release candidates in both directions."
  risks:
    - risk: "The order key is two elements longer than before; a caller that reads the tuple as (major, minor, patch) would break."
      mitigation: "The only callers are inside updater.py and compare whole tuples (verified by search); the displayed version is the raw string from the file name."
    - risk: "A wheel with an unsupported version form is still skipped."
      mitigation: "It is now logged at DEBUG."

technical_details:
  current_behavior: "tuple(int(p) for p in s.strip().split('.')); None on ValueError."
  proposed_behavior: "See rational.proposed_solution."
  implementation_approach: "Edit in place; one new test module; one commit."
  code_changes:
    - component: "updater.py"
      file: "src/gtach/utils/updater.py"
      change_summary: "EDIT A, EDIT B"
      functions_affected:
        - "_parse_version_str"
        - "find_available_update"
      classes_affected: []
  data_changes: []
  interface_changes:
    - interface: "_parse_version_str, get_installed_version, parse_wheel_version"
      change_type: "contract"
      details: "The returned tuple is an order key (release padded to three or more components, phase rank, pre-release number) instead of the bare release numbers. Signatures unchanged."
      backward_compatible: "yes, for comparison; no caller indexes the tuple"

dependencies:
  internal:
    - component: "DisplayManager._run_update_check"
      impact: "None; it uses the (filename, version string) result of find_available_update."
  external: []
  required_changes: []

testing_requirements:
  test_approach: "Unit tests in tests/test_update_version_ordering.py; then the full suite."
  test_cases:
    - scenario: "Ordering: 0.5.0 < 1.0.0a1 < 1.0.0b2 < 1.0.0rc1 < 1.0.0rc2 < 1.0.0 < 1.0.1 < 1.1.0."
      expected_result: "Keys compare in that order."
    - scenario: "'1.0' and '1.0.0'."
      expected_result: "Equal keys."
    - scenario: "Unsupported: '', 'abc', '1.0.0.dev1', '1.0.0+local', '1.0.0-rc.1', '1..0', None."
      expected_result: "None; no exception."
    - scenario: "parse_wheel_version('gtach-1.0.0rc1-py3-none-any.whl')."
      expected_result: "The key of 1.0.0rc1."
    - scenario: "find_available_update with installed 1.0.0rc1 and a valid staged 1.0.0 wheel."
      expected_result: "('gtach-1.0.0-py3-none-any.whl', '1.0.0')."
    - scenario: "find_available_update with installed 0.5.0 and a valid staged 1.0.0rc1 wheel."
      expected_result: "The rc wheel is returned."
    - scenario: "find_available_update with installed 1.0.0 and staged 1.0.0rc1 and 0.5.0 wheels."
      expected_result: "None."
    - scenario: "find_available_update with installed 1.0.0rc1 and staged 1.0.0rc2 and 1.0.0 wheels."
      expected_result: "The 1.0.0 wheel."
    - scenario: "Installed version not recognised."
      expected_result: "None and one WARNING record."
  regression_scope:
    - "tests/test_lifecycle_logging_utils.py"
    - "tests/test_gauge_display_touch.py"
  validation_criteria:
    - "pytest tests/ passes; python -m mypy src/ reports no issues; flake8 and black --check clean on the changed files."

implementation:
  effort_estimate: "30 minutes"
  implementation_steps:
    - step: "EDITS A and B per prompt-c41037ea."
      owner: "Claude Code"
    - step: "Device check of the staged-update path with the release candidate."
      owner: "William Watson (after the run)"
  rollback_procedure: "git revert of the implementation commit."
  deployment_notes: "None."

verification:
  implemented_date: ""
  implemented_by: ""
  verification_date: ""
  verified_by: ""
  test_results: ""
  issues_found: []

traceability:
  design_updates: []
  related_changes: []
  related_issues: []

notes: >
  Maintenance classification (P04.7): corrective.
  Impact analysis (P04.5, P04.9): confined to utils/updater.py. Callers:
  DisplayManager._run_update_check (uses find_available_update only);
  no other module imports the parsing functions (search of src/, bin/
  and tests/, 2026-11-13). No effect on performance (the check runs on a
  worker thread on operator request), on security (no new input source;
  the regular expression is anchored and linear) or on stored data.
  Approved under delegated approval (proposal-f8d0064b section 3.0).

version_history:
  - version: "1.0"
    date: "2026-11-13"
    author: "Claude Code session (proposal-f8d0064b)"
    changes:
      - "Initial change document."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t02_change"
```

[Return to Table of Contents](#table-of-contents)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-13 | Initial change document. EDITS A and B. |

---

Copyright (c) 2026 William Watson. MIT License.
