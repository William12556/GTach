# Prompt: Remove Unused Code and Configuration Keys

Created: 2026 November 11

## Table of Contents

- [1.0 Prompt](#10-prompt)
- [Version History](#version-history)

---

## 1.0 Prompt

```yaml
prompt_info:
  id: "prompt-cfa4e617"
  task_type: "refactor"
  source_ref: "change-cfa4e617"
  target_profile: "claude_code"
  date: "2026-11-11"
  iteration: 1
  coupled_docs:
    change_ref: "change-cfa4e617"
    change_iteration: 1

context:
  purpose: "Run 1 of proposal-71ab3751: delete unused code so that runs 2 to 5 read less. No behaviour change."
  integration: "Deletions across src/gtach/display, src/gtach/utils, two comm files, tests/ and one rule in CLAUDE.md."
  knowledge_references:
    - "ai/workspace/issues/issue-cfa4e617-dead-code-removal.md"
    - "ai/workspace/change/change-cfa4e617-dead-code-removal.md"
    - "ai/workspace/proposal/proposal-71ab3751-audit-remediation-and-simplification.md sections 4.2 and 6.0"
    - "CLAUDE.md section 4"
  constraints:
    - "CRITICAL: subtractive only. Do not fix defects, rename, reformat or restructure. If a deletion would need a behaviour change to keep the code working, leave the candidate in place and report it."
    - "CRITICAL: apply the RULE of change-cfa4e617 to every candidate. The candidate lists in the issue and the change come from a textual search and are not proof."
    - "Verify each candidate independently and adversarially before deleting it: search src/ and tests/ for the name, for string forms of the name, for getattr and hasattr uses, and for subclasses or interfaces that reach it."
    - "Keep BluetoothSetupInterface.start_discovery(show_all_devices=...) and BluetoothPairing.discover_elm327_devices(show_all_devices=...)."
    - "Keep TouchEventCoordinator.swipe_threshold: display/touch.py reads it through getattr."
    - "Keep detection in utils/platform.py; keep every PerformanceMonitor member that DisplayManager uses."
    - "Do not touch optional-dependency import guards (hyperpixel2r, RPi.GPIO, PyBluez, pyserial)."
    - "Do not add type: ignore, and do not remove a TODO: issue-ac11505d marker except where EDIT F or a deletion removes its line."
    - "Python 3.9+ compatible. Line length 88."

specification:
  description: "Apply EDITS A to H of change-cfa4e617."
  requirements:
    functional:
      - "As in change-cfa4e617 proposed_solution."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "No behaviour change"
        - "No orphaned imports, attributes or exports after a deletion"

design:
  architecture: "Unchanged."
  components:
    - name: "EDITS A to H"
      type: "module"
      purpose: "As in change-cfa4e617."
      logic:
        - "Work group by group (A to G). After each group run pytest tests/ and mypy src/ before starting the next, so that a failure identifies its group."
        - "After a deletion, remove imports, attributes, __all__ entries and docstring references that it leaves unused."
        - "EDIT C: after removing the coordinator attribute, the start_discovery call in SetupDisplayManager._setup_loop passes no show_all_devices argument."
        - "EDIT F: confirm in pyproject.toml that the package is a required dependency before removing its fallback."
        - "EDIT H: CLAUDE.md rule text exactly as given in the change; add a version-history row."

data_schema:
  entities: []

error_handling:
  strategy: "Unchanged."
  exceptions: []
  logging:
    level: "Unchanged"
    format: "Unchanged"

testing:
  unit_tests:
    - scenario: "As listed in change-cfa4e617 testing_requirements.test_cases."
      expected: "As listed there."
  edge_cases:
    - "A test imports a removed symbol only to assert that it exists: delete the test."
    - "A candidate turns out to be referenced: keep it and report the reference."
  validation:
    - "pytest tests/ passes."
    - "mypy src/ reports no issues."

deliverable:
  format_requirements:
    - "Edit in place. One commit."
    - "Report: every removed symbol with its file; every candidate kept with the reference that kept it; every deleted or reduced test; total lines of src/gtach before and after (wc -l)."
  files:
    - path: "src/gtach/display/**, src/gtach/utils/**, src/gtach/comm/pairing.py, src/gtach/comm/device_store.py"
      content: "EDITS A to G"
    - path: "CLAUDE.md"
      content: "EDIT H"
    - path: "tests/"
      content: "Deletions and reductions; one new ConfigStore unknown-key test"

success_criteria:
  - "No name listed for deletion in change-cfa4e617 remains in src/, except candidates reported as kept."
  - "utils/default-config.txt is absent and nothing references it."
  - "No dead import fallback with a TODO: issue-ac11505d marker remains for pygame, yaml, SplashConfig or TouchHandler."
  - "git diff shows deletions, the plain imports of EDIT F, the comment of EDIT G, the CLAUDE.md rule and test changes; nothing else."
  - "pytest tests/ passes; mypy src/ reports no issues."

element_registry:
  source: ""
  entries:
    modules: []
    classes: []
    functions: []
    constants: []

notes: >
  Operator invocation. Type the instruction; do not paste it from a
  file, because the keyword below takes effect only in a typed prompt:
  'ultracode. Implement ai/workspace/prompt/prompt-cfa4e617-dead-code-removal.md
  and close the prompt T-Doc when finished. Verify each deletion
  candidate independently and adversarially before deleting it. Leave
  the issue and change T-Docs active pending test results. Then, once
  finished, write a report in
  ai/workspace/report/report-cfa4e617-dead-code-removal.md.'
  Model: Claude Opus 5.5, effort medium. The keyword is used for this
  run only.
```

[Return to Table of Contents](#table-of-contents)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-11 | Initial prompt implementing change-cfa4e617 iteration 1. Target profile claude_code. |
| 1.1 | 2026-11-11 | Executed by Claude Code. EDITS A to H applied; candidates kept with their references are listed in report-cfa4e617. pytest and mypy pass. Closed and moved to ai/workspace/prompt/closed/. |

---

Copyright (c) 2026 William Watson. MIT License.
