Created: 2026 October 07

# Prompt: Always-On Error Log and Tracebacks on Broad Handlers

---

## Table of Contents

- [1. Prompt](<#1. prompt>)
- [2. Version History](<#2. version history>)

---

## 1. Prompt

```yaml
prompt_info:
  id: "prompt-269871a0"
  task_type: "debug"
  source_ref: "change-269871a0"
  target_profile: "claude_code"
  date: "2026-10-07"
  iteration: 1
  coupled_docs:
    change_ref: "change-269871a0"
    change_iteration: 1

context:
  purpose: >
    Persist WARNING and above for the life of the process regardless of
    the debug toggle, and make every ERROR/CRITICAL log call in a broad
    exception handler carry its traceback. At present nothing is logged
    after startup with debug off.
  integration: >
    Functional edit in src/gtach/main.py only. Mechanical keyword
    additions across src/gtach. Two test files. One line in CLAUDE.md.
  knowledge_references:
    - "ai/workspace/issues/issue-269871a0-runtime-errors-not-logged.md"
    - "ai/workspace/change/change-269871a0-always-on-error-log.md"
    - "ai/workspace/audit/audit-36b6ea95-full-codebase.md (B04, A11, Section 6)"
  constraints:
    - "CRITICAL: error.log must NOT rotate at start. Do not call doRollover on it. A restart caused by a fault must leave that fault's record in the live file."
    - "Do not change the start.log or debug.log handlers, the debug.log rotate-at-start block, or the CRITICAL + 1 default of debug.log."
    - "Do not modify GTachApplication._finish_startup_logging or toggle_debug_logging in src/gtach/app.py, other than EDIT B keyword additions if the policy test reports sites there."
    - "EDIT B adds `exc_info=True` only. Do not change messages, levels, control flow, imports or formatting in any module touched by EDIT B."
    - "Do not modify src/gtach/display/manager_backup.py or src/gtach/display/setup_original_backup.py."
    - "Tests must never write to /opt/gtach. Redirect _ERROR_LOG to tmp_path wherever setup_logging runs in tests."
    - "Python 3.9+ compatible. PEP 8. Type hints on public interfaces. Google-style docstrings."

specification:
  description: "Apply EDITS A to D, then run the full test suite."
  requirements:
    functional:
      - "With debug off, WARNING, ERROR and CRITICAL records emitted after startup are written to /opt/gtach/error.log."
      - "error.log is size-rotated at 1 MiB with 5 backups and never rotated at start."
      - "Every logger .error/.critical call inside a broad exception handler in src/gtach passes exc_info=True."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Thread-safe if concurrent access"
        - "Comprehensive error handling"
        - "Professional docstrings"
  performance: []

design:
  architecture: >
    A third root handler, independent of the startup and debug handlers,
    gives warnings and errors a persistent sink. The existing two-file
    design is preserved unchanged.
  components:
    - name: "EDIT A — error.log handler in setup_logging"
      type: "function"
      purpose: "Persist WARNING and above for the process lifetime."
      logic:
        - "Below the existing _DEBUG_BACKUPS constant add: _ERROR_LOG = '/opt/gtach/error.log', _ERROR_MAX_BYTES = 1 * 1024 * 1024, _ERROR_BACKUPS = 5, with a comment: always on, WARNING and above, size rotation only, never rotated at start (issue-269871a0)."
        - "Beside _start_handler and _debug_handler add the module global `_error_handler: Optional[logging.Handler] = None`."
        - "Add _error_handler to the `global` statement in setup_logging."
        - "After the debug.log block and before the `if debug` lines, create RotatingFileHandler(_ERROR_LOG, maxBytes=_ERROR_MAX_BYTES, backupCount=_ERROR_BACKUPS, encoding='utf-8'), setLevel(logging.WARNING), setFormatter(formatter), root.addHandler(...)."
        - "Wrap creation in `try/except OSError as e` printing `[gtach] WARNING: could not open {_ERROR_LOG}: {e}` to stderr, matching the existing pattern. On failure _error_handler stays None."
        - "Update the setup_logging docstring (or add one) to describe all three handlers."
    - name: "EDIT B — exc_info on broad handlers"
      type: "module"
      purpose: "Comply with CLAUDE.md §4 rule 6."
      logic:
        - "Rule: an except handler is broad if its type is absent (bare), Exception, BaseException, or a tuple containing Exception or BaseException."
        - "For each broad handler in src/gtach (backups excluded), every call node in its body of the form <expr>.error(...) or <expr>.critical(...) that has no exc_info keyword gets `exc_info=True` appended as the last argument."
        - "Write the EDIT C policy test first and use its output as the work list. The audit scan found 206 sites in 25 modules; the policy test is authoritative."
        - "If a reported call is not a logger (for example argparse's parser.error), add it to an explicit, commented allow-list in the policy test instead of editing it, and record it in the report."
    - name: "EDIT C — tests"
      type: "module"
      purpose: "Enforce EDIT B and verify EDIT A."
      logic:
        - "Create tests/test_logging_policy.py. Walk src/gtach/**/*.py excluding the two backup modules; parse with ast; apply EDIT B's rule; collect file:line for violations; assert the list is empty, printing it on failure."
        - "In the same file, add a test that runs the checker function over a synthetic source string containing one violation and asserts it is detected."
        - "Add EDIT A tests (location of your choice under tests/), each redirecting _START_LOG, _DEBUG_LOG and _ERROR_LOG to tmp_path and restoring root handlers afterwards, per testing.unit_tests."
        - "In tests/test_stack_dump_toggle.py, extend TestSetupLoggingGate.isolated_logging to monkeypatch gtach_main._ERROR_LOG to str(tmp_path / 'error.log'). Change nothing else in that file."
    - name: "EDIT D — CLAUDE.md"
      type: "module"
      purpose: "Keep the context file accurate."
      logic:
        - "In CLAUDE.md §3 Technology Stack, Logging row, append: `+ error.log (WARNING and above, always on, 1 MB × 5, size rotation only)`."
        - "Add a Version History row: next minor version, today's date, 'Logging row: error.log (change-269871a0)'."

data_schema:
  entities: []

error_handling:
  strategy: "Logging setup must never prevent startup."
  exceptions:
    - exception: "OSError"
      condition: "error.log cannot be opened."
      handling: "Print a warning to stderr; continue with the other handlers."
  logging:
    level: "WARNING for error.log"
    format: "Existing _LOG_FORMAT and _LOG_DATE_FMT."

testing:
  unit_tests:
    - scenario: "setup_logging(debug=False); log INFO, WARNING and ERROR."
      expected: "error.log contains the WARNING and ERROR lines and not the INFO line."
    - scenario: "setup_logging(debug=False); set the start handler to CRITICAL + 1; log ERROR."
      expected: "error.log contains the ERROR line."
    - scenario: "error.log pre-populated; setup_logging(debug=False)."
      expected: "Pre-existing content remains in the live error.log; no error.log.1 is created."
    - scenario: "_ERROR_LOG set to a path in a nonexistent directory."
      expected: "No exception; _error_handler is None; stderr contains the warning."
    - scenario: "Policy test over src/gtach."
      expected: "Zero violations."
    - scenario: "Policy checker over a synthetic violating source."
      expected: "Exactly one violation reported."
  edge_cases:
    - "A broad handler nested inside another handler: both are checked."
    - "A call already passing exc_info=False: not a violation (explicit choice); do not change it."
  validation:
    - "pytest tests/ passes."
    - "python -c \"import ast; ast.parse(open('src/gtach/main.py').read())\""

deliverable:
  format_requirements:
    - "Edit existing files in place."
  files:
    - path: "src/gtach/main.py"
      content: "EDIT A"
    - path: "src/gtach/ (modules listed by the policy test)"
      content: "EDIT B"
    - path: "tests/test_logging_policy.py"
      content: "EDIT C policy test and checker test"
    - path: "tests/test_stack_dump_toggle.py"
      content: "EDIT C fixture redirect"
    - path: "CLAUDE.md"
      content: "EDIT D"

success_criteria:
  - "main.py defines _ERROR_LOG, _ERROR_MAX_BYTES == 1048576, _ERROR_BACKUPS == 5 and _error_handler."
  - "setup_logging adds a RotatingFileHandler at WARNING for _ERROR_LOG and never calls doRollover on it."
  - "The debug.log block, including its rotate-at-start and CRITICAL + 1 default, is unchanged."
  - "src/gtach/app.py functions _finish_startup_logging and toggle_debug_logging are unchanged apart from exc_info additions reported by the policy test."
  - "tests/test_logging_policy.py passes with zero violations."
  - "git diff of every EDIT B module shows only added exc_info=True arguments."
  - "No test writes under /opt/gtach."
  - "pytest tests/ passes."

element_registry:
  source: ""
  entries:
    modules:
      - name: "main"
        path: "src/gtach/main.py"
    classes: []
    functions:
      - name: "setup_logging"
        module: "gtach.main"
        signature: "(debug: bool = False) -> None"
    constants:
      - name: "_ERROR_LOG"
        module: "gtach.main"
        type: "str"
      - name: "_ERROR_MAX_BYTES"
        module: "gtach.main"
        type: "int"
      - name: "_ERROR_BACKUPS"
        module: "gtach.main"
        type: "int"

notes: >
  On-target verification is a human step: with debug off, power off the
  adapter for 30 s and confirm error.log records the event with a
  traceback; restart the service and confirm the earlier records remain.
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-07 | Initial prompt implementing change-269871a0 iteration 1. Target profile claude_code. |
| 1.1 | 2026-10-07 | Implemented; closed |

---

Copyright (c) 2026 William Watson. MIT License.
