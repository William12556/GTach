Created: 2026 October 09

# Change: Remove Eager Package Re-exports

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-2b3a1547"
  title: "Drop the GTachApplication and main re-exports from src/gtach/__init__.py"
  date: "2026-10-09"
  author: "William Watson"
  status: "proposed"
  priority: "low"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-2b3a1547"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-2b3a1547"
  description: "Resolves issue-2b3a1547. Approach chosen 2026-10-09: drop the re-exports rather than make them lazy."

scope:
  summary: "Importing gtach or any submodule no longer imports gtach.app, pygame or the transport stack."
  affected_components:
    - name: "gtach package"
      file_path: "src/gtach/__init__.py"
      change_type: "modify"
    - name: "Stale comments describing the re-export"
      file_path: "tests/test_stack_dump_toggle.py, tests/test_stacks_log_rotation.py"
      change_type: "modify"
    - name: "Import-cost test"
      file_path: "tests/test_package_import.py"
      change_type: "add"
  affected_designs: []
  out_of_scope:
    - "Eager imports in subpackage __init__ files (gtach.utils, gtach.comm, gtach.display)."
    - "The sys.modules['gtach.main'] lookups in tests and app.py (still valid; not simplified)."
    - "main.py's deferred imports."

rational:
  problem_statement: >
    See issue-2b3a1547. src/gtach/__init__.py lines 14-15 import .app and
    .main, so any gtach import loads app.py, pygame and the transport
    stack, and the function main shadows the submodule gtach.main.
  proposed_solution: >
    Delete 'from .app import GTachApplication' and 'from .main import
    main'; set __all__ = ['__version__']. Keep __version__ and
    __author__. The console script (gtach.main:main) and
    src/gtach/__main__.py already import from gtach.main. Update the two
    test comments that explain the shadowing (test_stack_dump_toggle.py
    ~line 33, test_stacks_log_rotation.py ~line 24) to state that
    gtach.main is the submodule; do not change test code.
  alternatives_considered:
    - option: "Lazy re-exports via module __getattr__."
      reason_rejected: "Decided against on 2026-10-09; keeps gtach.main ambiguous (function or module by import order)."
  benefits:
    - "--validate-config and --validate-dependencies start without pygame."
    - "gtach.main always names the submodule."
  risks:
    - risk: "External code using gtach.GTachApplication or 'from gtach import main' breaks."
      mitigation: "No in-repo caller (grep at ba661d4); GTach has no library consumers; the console script is unaffected."

technical_details:
  current_behavior: "import gtach.<anything> imports app.py and pygame."
  proposed_behavior: "import gtach.main imports only main.py's top-level dependencies."
  implementation_approach: "Delete two imports; adjust __all__ and two comments; add a subprocess test."
  code_changes:
    - component: "gtach"
      file: "src/gtach/__init__.py"
      change_summary: "Remove re-exports."
      functions_affected: []
      classes_affected: []
  data_changes: []
  interface_changes:
    - interface: "gtach package namespace"
      change_type: "contract"
      details: "gtach.GTachApplication removed; gtach.main is the submodule, not the function."
      backward_compatible: "no"

dependencies:
  internal: []
  external: []
  required_changes:
    - change_ref: "change-52653cd6"
      relationship: "related. Removed the hard-coded __version__."

testing_requirements:
  test_approach: "Subprocess test so sys.modules starts clean."
  test_cases:
    - scenario: "subprocess: python -c \"import sys, gtach.main; assert 'pygame' not in sys.modules and 'gtach.app' not in sys.modules\"."
      expected_result: "Exit status 0."
    - scenario: "subprocess: python -c \"import gtach; print(gtach.__version__)\"."
      expected_result: "Exit status 0; prints a version."
    - scenario: "python -m gtach --version."
      expected_result: "Prints the version and exits 0."
  regression_scope:
    - "Full tests/ suite."
  validation_criteria:
    - "pytest tests/ passes."

implementation:
  effort_estimate: "0.5 hour"
  implementation_steps:
    - step: "Edit __init__.py and the two comments; add tests/test_package_import.py."
      owner: "worker (Claude Code)"
  rollback_procedure: "Revert the commit."
  deployment_notes: "Human verification: the systemd service starts normally on the Pi."

verification:
  implemented_date: ""
  implemented_by: ""
  verification_date: ""
  verified_by: ""
  test_results: ""
  issues_found: []

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-52653cd6"
      relationship: "related"
    - change_ref: "change-c1d4b8e6"
      relationship: "related. Introduced the sys.modules workaround in tests."
  related_issues:
    - issue_ref: "issue-2b3a1547"
      relationship: "resolves"

notes: ""

version_history:
  - version: "1.0"
    date: "2026-10-09"
    author: "William Watson"
    changes:
      - "Initial change document resolving issue-2b3a1547 iteration 1."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t02_change"
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-09 | Initial change document resolving issue-2b3a1547 iteration 1. |

---

Copyright (c) 2026 William Watson. MIT License.
