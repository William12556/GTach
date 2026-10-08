Created: 2026 October 07

# Change: Always-On Error Log and Tracebacks on Broad Handlers

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-269871a0"
  title: "Add an always-on, size-rotated WARNING-level error.log; add exc_info=True to every ERROR/CRITICAL log call in a broad exception handler, enforced by a policy test"
  date: "2026-10-07"
  author: "William Watson"
  status: "closed"
  priority: "high"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-269871a0"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-269871a0"
  description: >
    Resolves issue-269871a0 (audit-36b6ea95 B04 and A11). After startup
    no handler accepts any record with debug off, and broad handlers log
    without tracebacks.

scope:
  summary: >
    EDIT A adds a third root handler in setup_logging that writes WARNING
    and above to /opt/gtach/error.log for the life of the process. EDIT B
    adds exc_info=True to every logger.error/critical call inside a broad
    exception handler across src/gtach. EDIT C adds a policy test and
    redirects the new log path in the existing logging test fixture.
    EDIT D updates CLAUDE.md §3.
  affected_components:
    - name: "setup_logging and module constants"
      file_path: "src/gtach/main.py"
      change_type: "modify"
    - name: "Broad exception handlers (206 sites, 25 modules)"
      file_path: "src/gtach/"
      change_type: "modify"
    - name: "TestSetupLoggingGate.isolated_logging fixture"
      file_path: "tests/test_stack_dump_toggle.py"
      change_type: "modify"
    - name: "Logging policy test"
      file_path: "tests/test_logging_policy.py"
      change_type: "add"
    - name: "Technology stack table, Logging row"
      file_path: "CLAUDE.md"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "start.log and debug.log behaviour, including debug.log rotate-at-start and the debug toggle. Both remain byte-identical in behaviour."
    - "GTachApplication._finish_startup_logging and toggle_debug_logging. Neither touches the new handler, so neither changes."
    - "Rate limiting of repeated errors in per-frame paths. The size cap bounds disk use; rate limiting is a separate decision."
    - "Changing log levels of existing calls, or adding exc_info to WARNING/INFO/DEBUG calls."
    - "src/gtach/display/manager_backup.py and setup_original_backup.py (excluded by CLAUDE.md)."
    - "The rest of finding E03 (os.system('stty sane')), handled separately."

rational:
  problem_statement: >
    setup_logging installs start.log (raised to CRITICAL + 1 when startup
    completes, app.py:209) and debug.log (CRITICAL + 1 unless debug,
    main.py:104). After startup, with debug off, every record is
    discarded. Confirmed on device 2026-10-07: an unexplained clean exit
    and restart left no record. Separately, 206 ERROR/CRITICAL calls in
    broad handlers omit exc_info, contrary to CLAUDE.md §4 rule 6.
  proposed_solution: >
    EDIT A — error.log. Add module constants _ERROR_LOG =
    '/opt/gtach/error.log', _ERROR_MAX_BYTES = 1 * 1024 * 1024 and
    _ERROR_BACKUPS = 5, and a module global _error_handler. In
    setup_logging, after the debug.log block, create a
    RotatingFileHandler(_ERROR_LOG, maxBytes=_ERROR_MAX_BYTES,
    backupCount=_ERROR_BACKUPS, encoding='utf-8') at logging.WARNING with
    the shared formatter and add it to the root logger. Do not call
    doRollover at start. Wrap creation in the same OSError guard and
    stderr warning used for the other two handlers.

    EDIT B — tracebacks. In every except handler in src/gtach (backups
    excluded) whose type is bare, Exception, BaseException, or a tuple
    containing Exception or BaseException, add exc_info=True to each
    logger .error(...) and .critical(...) call in the handler body that
    does not already pass exc_info. Messages and levels are unchanged.

    EDIT C — tests. Add tests/test_logging_policy.py that parses every
    module under src/gtach (backups excluded) with ast and fails, listing
    file:line, for any call matching EDIT B's rule without exc_info. Add
    tests for EDIT A. In tests/test_stack_dump_toggle.py, extend the
    isolated_logging fixture to monkeypatch _ERROR_LOG to tmp_path.

    EDIT D — CLAUDE.md §3 Logging row: add "error.log (WARNING and above,
    always on, 1 MB × 5, size rotation only)".
  alternatives_considered:
    - option: "Lower debug.log's default level from CRITICAL + 1 to WARNING."
      reason_rejected: >
        debug.log rotates at every start when it has content
        (issue-6a3b7c52). Every run that logged a warning would consume a
        generation and push deliberate debug captures off the ten-file
        chain within ten boots.
    - option: "Add a StreamHandler to stderr so records reach the systemd journal."
      reason_rejected: >
        Splits evidence between the journal and app-owned files, which
        change-bd8f95b7 deliberately consolidated under /opt/gtach, and
        bin/pull_logs.sh does not collect the journal.
    - option: "Rotate error.log at start like debug.log."
      reason_rejected: >
        A fault that causes a restart would rotate its own evidence away
        from the live file. Size rotation alone bounds disk use.
  benefits:
    - "WARNING and above are persisted in normal operation, across restarts."
    - "Every unexpected exception logged at ERROR/CRITICAL carries its traceback."
    - "The policy test prevents regression."
    - "bin/pull_logs.sh collects error.log without change (it pulls *.log and *.log.*)."
  risks:
    - risk: "A per-frame error with traceback rotates error.log quickly, discarding the first occurrence."
      mitigation: >
        Six files of 1 MB bound disk use at 6 MB. Repeated per-frame
        errors are a separate defect to be fixed where they occur; the
        first traceback of a run also reaches debug.log when debug is on.
    - risk: "The large mechanical diff (EDIT B) hides an accidental behaviour change."
      mitigation: >
        EDIT B adds a keyword argument only. The prompt forbids any other
        edit in those modules, and the policy test plus the full suite
        must pass.
    - risk: "Tests write to /opt/gtach on the development host."
      mitigation: "EDIT C redirects _ERROR_LOG in the existing fixture; new tests use tmp_path."

technical_details:
  current_behavior: >
    Two handlers; both suppressed after startup unless debug is on.
    Broad handlers log str(e) only.
  proposed_behavior: >
    Three handlers; error.log accepts WARNING and above for the life of
    the process regardless of the debug toggle and is never rotated at
    start. Broad handlers log with tracebacks.
  implementation_approach: >
    One functional edit in main.py; one mechanical keyword addition
    across 25 modules; two test files; one documentation line.
  code_changes:
    - component: "gtach.main"
      file: "src/gtach/main.py"
      change_summary: "Constants _ERROR_LOG, _ERROR_MAX_BYTES, _ERROR_BACKUPS; global _error_handler; error.log handler in setup_logging."
      functions_affected:
        - "setup_logging"
      classes_affected: []
    - component: "src/gtach (25 modules)"
      file: "src/gtach/"
      change_summary: "exc_info=True added to ERROR/CRITICAL calls in broad handlers."
      functions_affected: []
      classes_affected: []
  data_changes: []
  interface_changes:
    - interface: "gtach.main._error_handler"
      change_type: "contract"
      details: "New module-level handler reference, None until setup_logging runs or if the file cannot be opened."
      backward_compatible: "yes"

dependencies:
  internal:
    - component: "GTachApplication._finish_startup_logging / toggle_debug_logging"
      impact: "None. They reference _start_handler and _debug_handler only."
    - component: "bin/pull_logs.sh"
      impact: "None. error.log and error.log.N match its existing globs."
  external: []
  required_changes: []

testing_requirements:
  test_approach: "Unit tests with tmp_path log paths; AST policy test; full suite."
  test_cases:
    - scenario: "setup_logging(debug=False), then a WARNING and an ERROR are logged."
      expected_result: "Both appear in the redirected error.log; an INFO record does not."
    - scenario: "setup_logging(debug=False), start handler raised to CRITICAL + 1 as _finish_startup_logging does, then an ERROR is logged."
      expected_result: "The ERROR appears in error.log."
    - scenario: "setup_logging run twice against an error.log that already has content."
      expected_result: "No rollover at start: the earlier content is still in the live file."
    - scenario: "_ERROR_LOG points into a directory that does not exist."
      expected_result: "No exception; a warning is printed to stderr; _error_handler is None; other handlers are installed."
    - scenario: "Policy test over src/gtach."
      expected_result: "Passes with zero violations after EDIT B."
    - scenario: "Policy test over a synthetic module containing `except Exception as e: logger.error(f'x {e}')`."
      expected_result: "Reports one violation, proving the check detects the pattern."
  regression_scope:
    - "tests/test_stack_dump_toggle.py and tests/test_stacks_log_rotation.py."
    - "Full tests/ suite."
  validation_criteria:
    - "The debug.log rotate-at-start block and its CRITICAL + 1 default are unchanged."
    - "app.py _finish_startup_logging and toggle_debug_logging are unchanged."
    - "In the 25 modules, the diff consists only of added exc_info=True arguments."
    - "pytest tests/ passes."

implementation:
  effort_estimate: ""
  implementation_steps:
    - step: "EDIT A in main.py."
      owner: "tactical"
    - step: "EDIT C policy test written first; run it to list violations."
      owner: "tactical"
    - step: "EDIT B until the policy test passes."
      owner: "tactical"
    - step: "EDIT C remaining tests and fixture; EDIT D."
      owner: "tactical"
    - step: "Deploy; with debug off, cause an error; confirm error.log content and traceback."
      owner: "human"
  rollback_procedure: "Revert the commit."
  deployment_notes: "No service or packaging change. error.log is created on first start."

verification:
  implemented_date: "2026-10-07"
  implemented_by: "Claude Code"
  verification_date: "2026-10-08"
  verified_by: "William Watson"
  test_results: "Session D (2026-10-07): with debug off, link loss and connect refusals recorded in error.log; earlier records survived restart; broad-handler tracebacks recorded with debug off. Narrow OSError handlers log message-only, outside the exc_info policy."
  issues_found: []

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-bd8f95b7"
      relationship: "related. Established the two-file logging extended here."
    - change_ref: "change-6a3b7c52"
      relationship: "related. Established debug.log rotate-at-start, preserved here."
  related_issues:
    - issue_ref: "issue-269871a0"
      relationship: "resolves"
    - issue_ref: "issue-b9ee7428"
      relationship: "related"

notes: >
  The no-rotate-at-start property of error.log is the point of the
  change: a restart caused by a fault must not move that fault's record
  out of the live file.

version_history:
  - version: "1.0"
    date: "2026-10-07"
    author: "William Watson"
    changes:
      - "Initial change document resolving issue-269871a0 iteration 1."
  - version: "1.1"
    date: "2026-10-07"
    author: "William Watson"
    changes:
      - "Approved for implementation by William Watson before implementation; entry recorded retrospectively."
  - version: "1.2"
    date: "2026-10-07"
    author: "Claude Code"
    changes:
      - "Implemented in 5f3c50be158bf2bea57f47edf7383062032c3213."
  - version: "1.3"
    date: "2026-10-08"
    author: "William Watson"
    changes:
      - "Verified on device; closed at audit-36b6ea95 close-out."

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
| 1.0 | 2026-10-07 | Initial change document. Always-on error.log; exc_info on broad handlers; policy test. |
| 1.1 | 2026-10-07 | Approved for implementation (recorded retrospectively). |
| 1.2 | 2026-10-07 | Implemented in 5f3c50be158bf2bea57f47edf7383062032c3213. |
| 1.3 | 2026-10-08 | Verified on device; closed at audit-36b6ea95 close-out. |

---

Copyright (c) 2026 William Watson. MIT License.
