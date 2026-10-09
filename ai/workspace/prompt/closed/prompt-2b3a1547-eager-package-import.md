Created: 2026 October 09

# Prompt: Remove Eager Package Re-exports

---

## Table of Contents

- [1. Prompt](<#1. prompt>)
- [2. Version History](<#2. version history>)

---

## 1. Prompt

```yaml
prompt_info:
  id: "prompt-2b3a1547"
  task_type: "refactor"
  source_ref: "change-2b3a1547"
  target_profile: "claude_code"
  date: "2026-10-09"
  iteration: 1
  coupled_docs:
    change_ref: "change-2b3a1547"
    change_iteration: 1

context:
  purpose: "Importing gtach or a submodule must not import gtach.app or pygame."
  integration: "src/gtach/__init__.py; two test comments; tests/test_package_import.py."
  knowledge_references:
    - "ai/workspace/issues/issue-2b3a1547-eager-package-import.md"
    - "ai/workspace/change/change-2b3a1547-eager-package-import.md"
  constraints:
    - "Drop the re-exports; do not add a module __getattr__."
    - "Keep __version__ (importlib.metadata) and __author__."
    - "Do not change test code other than the two comments; keep the sys.modules['gtach.main'] lookups."
    - "Do not change subpackage __init__ files or main.py."

specification:
  description: "Delete 'from .app import GTachApplication' and 'from .main import main'; __all__ = ['__version__']."
  requirements:
    functional:
      - "python -c \"import sys, gtach.main; assert 'pygame' not in sys.modules and 'gtach.app' not in sys.modules\" exits 0."
      - "The gtach console script and python -m gtach work unchanged."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Professional docstrings"
  performance: []

design:
  architecture: "Package namespace reduced to metadata."
  components:
    - name: "src/gtach/__init__.py"
      type: "module"
      purpose: "Remove the two imports; __all__ = ['__version__']; add a one-line comment citing issue-2b3a1547."
    - name: "Test comments"
      type: "module"
      purpose: "tests/test_stack_dump_toggle.py (~line 33) and tests/test_stacks_log_rotation.py (~line 24): reword the comments that say the package re-exports main so that 'from gtach import main' yields the function; state that gtach.main is the submodule."
    - name: "tests/test_package_import.py"
      type: "module"
      purpose: "Subprocess tests (sys.executable) for import cost and __version__."

data_schema:
  entities: []

error_handling:
  strategy: "Not applicable."
  exceptions: []
  logging:
    level: "Unchanged"
    format: "Unchanged"

testing:
  unit_tests:
    - scenario: "subprocess: import sys, gtach.main; assert 'pygame' not in sys.modules and 'gtach.app' not in sys.modules."
      expected: "Return code 0."
    - scenario: "subprocess: import gtach; print(gtach.__version__)."
      expected: "Return code 0; non-empty output."
    - scenario: "subprocess: python -m gtach --version."
      expected: "Return code 0."
  edge_cases: []
  validation:
    - "grep -rn 'gtach.GTachApplication\\|from gtach import main' src tests bin returns only comments, if anything."
    - "pytest tests/ passes."

deliverable:
  format_requirements:
    - "Save code directly to the listed paths."
    - "Run pytest tests/ on completion; report pass/fail counts."
  files:
    - path: "src/gtach/__init__.py"
      content: "Re-exports removed"
    - path: "tests/test_stack_dump_toggle.py"
      content: "Comment only"
    - path: "tests/test_stacks_log_rotation.py"
      content: "Comment only"
    - path: "tests/test_package_import.py"
      content: "Subprocess tests"

success_criteria:
  - "src/gtach/__init__.py contains no 'from .app' or 'from .main'."
  - "The three subprocess tests pass."
  - "pytest tests/ passes."

element_registry:
  source: ""
  entries:
    modules:
      - name: "gtach"
        path: "src/gtach/__init__.py"
    classes: []
    functions: []
    constants:
      - name: "__all__"
        module: "gtach"
        type: "List[str]"

notes: "Human verification on the Pi: the gtach service starts and gtach --validate-config runs."
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-09 | Initial prompt implementing change-2b3a1547 iteration 1. Target profile claude_code. |
| 1.1 | 2026-10-09 | Implemented; closed |

---

Copyright (c) 2026 William Watson. MIT License.
