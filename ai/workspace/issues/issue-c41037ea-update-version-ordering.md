# Issue: Update Check Cannot Order Pre-Release Versions

Created: 2026 November 13

## Table of Contents

- [1.0 Issue Information](#10-issue-information)
- [Version History](#version-history)

---

## 1.0 Issue Information

```yaml
issue_info:
  id: "issue-c41037ea"
  title: "The update check parses only purely numeric versions; with a release candidate installed or staged, 'Check for updates' finds nothing"
  date: "2026-11-13"
  reporter: "Claude Code session (proposal-f8d0064b), for William Watson"
  status: "open"
  severity: "high"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-c41037ea"
    change_iteration: 1

source:
  origin: "code_review"
  test_ref: ""
  description: "Finding H01 of audit-bce0d69a (release-readiness audit, proposal-f8d0064b WP7)."

affected_scope:
  components:
    - name: "_parse_version_str; get_installed_version; parse_wheel_version; find_available_update"
      file_path: "src/gtach/utils/updater.py"
  designs:
    - "design-9a1f3c7e-domain_utils"
  version: "0.5.0"

reproduction:
  prerequisites: "Any Python environment with the project installed."
  steps:
    - "python -c \"from gtach.utils import updater; print(updater._parse_version_str('1.0.0rc1'))\""
    - "Or on the device: install gtach 1.0.0rc1, stage gtach-1.0.0-py3-none-any.whl with deploy.sh --stage, open OPTIONS, Check for updates."
  frequency: "always"
  reproducibility_conditions: "Any version string with a pre-release segment."
  test_data: >
    _parse_version_str('1.0.0rc1') returns None (reproduced 2026-11-13,
    Python 3.13.18). parse_wheel_version('gtach-1.0.0rc1-py3-none-any.whl')
    returns None. '0.5.0' gives (0, 5, 0); '1.0' gives (1, 0), which
    compares below (1, 0, 0).
  error_output: "None. The update view shows 'No update found'; nothing is logged."

behavior:
  expected: "A release candidate is ordered below its final release and above every earlier release; an installed release candidate can be updated from a staged wheel."
  actual: "Installed 1.0.0rc1: get_installed_version() is None, so find_available_update() returns None for every staged wheel. Staged 1.0.0rc1 on 0.5.0: the wheel is skipped."
  impact: "Decision D1 of proposal-f8d0064b sets the version to 1.0.0rc1. The on-device update path (deploy.sh --stage, OPTIONS, Check for updates) is inert for the release candidate in both directions, without any message."
  workaround: "Full deploy with ./bin/deploy.sh."

environment:
  python_version: "3.9"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies: []
  domain: "domain_1"

analysis:
  root_cause: "_parse_version_str applies int() to each dot-separated part; '0rc1' is not an integer, and the ValueError is mapped to None."
  technical_notes: >
    importlib.metadata reports the normalised PEP 440 form ('1.0.0rc1'),
    and setuptools writes the same form into the wheel file name, so only
    that form needs to be read. The 'packaging' library is not a declared
    dependency and is not importable in the Pi venv, so the ordering is
    implemented locally. bin/gtach-preflight.sh handles the wheel by file
    name and is not affected.
  related_issues: []

resolution:
  assigned_to: "Claude Code"
  target_date: "2026-11-13"
  approach: "See change-c41037ea."
  change_ref: "change-c41037ea"
  resolved_date: ""
  resolved_by: ""
  fix_description: ""

verification:
  verified_date: ""
  verified_by: ""
  test_results: ""
  closure_notes: ""

prevention:
  preventive_measures: "Unit tests over the version ordering, including the D1 version."
  process_improvements: "None."

verification_enhanced:
  verification_steps:
    - "Reproduce from source. [DONE, 2026-11-13.]"
    - "After the fix: unit tests per change-c41037ea."
    - "Device (owner, after the run): with 1.0.0rc1 installed, stage a higher version, Check for updates, Install."
  verification_results: ""

traceability:
  design_refs:
    - "design-9a1f3c7e-domain_utils"
  change_refs:
    - "change-c41037ea"
  test_refs: []

notes: >
  Raised under delegated approval (proposal-f8d0064b section 3.0).

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-11-13"
    author: "Claude Code session (proposal-f8d0064b)"
    changes:
      - "Initial issue document."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t03_issue"
```

[Return to Table of Contents](#table-of-contents)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-13 | Initial issue document. Finding H01 of audit-bce0d69a. |

---

Copyright (c) 2026 William Watson. MIT License.
