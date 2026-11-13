# Prompt: Order Pre-Release Versions in the Update Check

Created: 2026 November 13

## Table of Contents

- [1.0 Prompt](#10-prompt)
- [Version History](#version-history)

---

## 1.0 Prompt

```yaml
prompt_info:
  id: "prompt-c41037ea"
  task_type: "debug"
  source_ref: "change-c41037ea"
  target_profile: "claude_code"
  date: "2026-11-13"
  iteration: 1
  coupled_docs:
    change_ref: "change-c41037ea"
    change_iteration: 1

context:
  purpose: "Apply EDITS A and B of change-c41037ea: the update check reads PEP 440 pre-release versions."
  integration: "src/gtach/utils/updater.py; tests/test_update_version_ordering.py."
  knowledge_references:
    - "ai/workspace/issues/issue-c41037ea-update-version-ordering.md"
    - "ai/workspace/change/change-c41037ea-update-version-ordering.md"
    - "CLAUDE.md section 4"
  constraints:
    - "CRITICAL: no new dependency; standard library only."
    - "CRITICAL: signatures and return types of _parse_version_str, get_installed_version, parse_wheel_version and find_available_update are unchanged."
    - "CRITICAL: only src/gtach/utils/updater.py changes under src/."
    - "Python 3.9 compatible. PEP 8, line length 88. Type hints. Google-style docstrings. Comments state current behaviour and cite issue-c41037ea at most once each."

specification:
  description: "Apply EDITS A and B; add tests."
  requirements:
    functional:
      - "As in change-c41037ea rational.proposed_solution."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Professional docstrings"

design:
  architecture: "Unchanged."
  components:
    - name: "EDIT A"
      type: "function"
      purpose: "Order key for PEP 440 release and pre-release versions."
      logic:
        - "Module constants: _VERSION_RE = re.compile(r'^(\\d+(?:\\.\\d+)*)(?:(a|b|rc)(\\d+))?$'); _PRE_RELEASE_RANK = {'a': -3, 'b': -2, 'rc': -1}; _MIN_RELEASE_PARTS = 3."
        - "_parse_version_str(s): return None unless s is a str matching _VERSION_RE after strip()."
        - "release = the integers of group 1, padded with zeros to _MIN_RELEASE_PARTS."
        - "Return release + (rank, number): (0, 0) for a final release; (_PRE_RELEASE_RANK[phase], int(number)) otherwise."
    - name: "EDIT B"
      type: "function"
      purpose: "Leave a record when the check cannot work."
      logic:
        - "find_available_update: when get_installed_version() is None, logger.warning('Installed version not recognised; update check skipped') before returning None."
        - "For a .whl whose parse_wheel_version is None: logger.debug(f'Skipping wheel with unrecognised version: {name}') and continue. A wheel that is recognised and not newer is skipped without a record, as before."

error_handling:
  strategy: "Unchanged: every function returns None or False on failure and never raises."
  exceptions: []
  logging:
    level: "WARNING for an unrecognised installed version; DEBUG for an unrecognised wheel version"
    format: "Unchanged"

testing:
  unit_tests:
    - scenario: "As listed in change-c41037ea testing_requirements.test_cases."
      expected: "As listed there."
  edge_cases:
    - "Whitespace around the version string."
    - "Release with one, two and four components."
    - "A staged file that is not a valid zip is still skipped with the existing WARNING."
  validation:
    - "pytest tests/ passes."
    - "python -m mypy src/ reports no issues."

deliverable:
  format_requirements:
    - "Edit in place. Tests in the new tests/test_update_version_ordering.py; the module docstring cites issue-c41037ea and change-c41037ea. Tests use tmp_path and monkeypatch for UPDATES_DIR and get_installed_version; real zip files as wheels."
    - "Execute the pytest suite on completion; report the pass/fail summary."
    - "Report ai/workspace/report/report-c41037ea-update-version-ordering.md."
  files:
    - path: "src/gtach/utils/updater.py"
      content: "EDIT A, EDIT B"
    - path: "tests/test_update_version_ordering.py"
      content: "Tests"

success_criteria:
  - "_parse_version_str('1.0.0rc1') < _parse_version_str('1.0.0')."
  - "find_available_update offers 1.0.0 to an installed 1.0.0rc1 and 1.0.0rc1 to an installed 0.5.0."
  - "git diff touches only src/gtach/utils/updater.py, the new test module and documents."
  - "pytest tests/ passes; python -m mypy src/ reports no issues."

element_registry:
  source: ""
  entries:
    modules: []
    classes: []
    functions:
      - name: "_parse_version_str"
        module: "gtach.utils.updater"
        signature: "_parse_version_str(s: str) -> Optional[Tuple[int, ...]]"
    constants:
      - name: "_VERSION_RE"
        module: "gtach.utils.updater"
        type: "Pattern[str]"
      - name: "_PRE_RELEASE_RANK"
        module: "gtach.utils.updater"
        type: "Dict[str, int]"
      - name: "_MIN_RELEASE_PARTS"
        module: "gtach.utils.updater"
        value: "3"

notes: "Execution profile P13.3 Option C, run by the session of proposal-f8d0064b. Device verification by the owner after the run: staged update from the release candidate."
```

[Return to Table of Contents](#table-of-contents)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-13 | Initial prompt implementing change-c41037ea iteration 1. Target profile claude_code. |

---

Copyright (c) 2026 William Watson. MIT License.
