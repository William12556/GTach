Created: 2026 October 07

# Issue: Runtime Errors Are Not Logged in Production

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-269871a0"
  title: "After startup every log record is discarded unless debug is enabled, and most broad exception handlers log without a traceback, so field faults leave no diagnosable record"
  date: "2026-10-07"
  reporter: "William Watson"
  status: "open"
  severity: "high"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-269871a0"
    change_iteration: 1

source:
  origin: "code_review"
  test_ref: ""
  description: >
    Raised from audit-36b6ea95 findings B04 (high, raised from medium in
    audit version 1.1) and A11 (medium). B04 was confirmed on gtach.local
    on 2026-10-07 by bin/gtach-audit-checks.sh: start.log closed at
    "Startup complete", debug.log 0 bytes, and the installed package sets
    both handlers to CRITICAL + 1 with no other handler present. On the
    same boot the service exited cleanly and was restarted by systemd
    with no record of the cause (audit finding B13).

affected_scope:
  components:
    - name: "setup_logging"
      file_path: "src/gtach/main.py"
    - name: "GTachApplication._finish_startup_logging"
      file_path: "src/gtach/app.py"
    - name: "GTachApplication.toggle_debug_logging"
      file_path: "src/gtach/app.py"
    - name: "Broad exception handlers logging at ERROR or CRITICAL without exc_info (206 sites in 25 modules)"
      file_path: "src/gtach/"
  designs: []
  version: "0.4.3"

reproduction:
  prerequisites: >
    GTach 0.4.3 running under systemd on gtach.local with debug logging
    off (the default; bin/gtach.service passes no --debug).
  steps:
    - "Note the sizes of /opt/gtach/start.log and /opt/gtach/debug.log."
    - "Cause a runtime error after startup, e.g. power off the ELM327 adapter for 30 s."
    - "Compare the file sizes and run journalctl -u gtach --since '-5 min'."
  frequency: "always"
  reproducibility_conditions: >
    Deterministic. Follows from the handler levels set in main.py:104 and
    app.py:209 and from the absence of any other handler.
  test_data: >
    bin/gtach-audit-checks.sh output, 2026-10-07 07:25:35
    (ai/workspace/audit/gtach-audit-checks-20261007-072535.txt):

      start.log   5932 bytes, last line "Startup complete — start.log closed"
      debug.log      0 bytes, mtime 2026-10-02 10:14:35
      main.py:104  _debug_handler.setLevel(logging.CRITICAL + 1)  # suppressed
      app.py:209   _main._start_handler.setLevel(logging.CRITICAL + 1)
      app.py:262   _main._debug_handler.setLevel(logging.CRITICAL + 1)
      "No stream/syslog/journal handler in main.py."

    journalctl -u gtach -b, same boot:

      07:18:29.831 gtach.service: Succeeded.
      07:18:35.012 Scheduled restart job, restart counter is at 1.

    No log file records why the process exited.
  error_output: "None. That is the defect."

behavior:
  expected: >
    WARNING, ERROR and CRITICAL records emitted at any point in the
    process lifetime are persisted, independent of the debug toggle, and
    every unexpected exception logged at ERROR or CRITICAL carries its
    traceback (CLAUDE.md §4 rule 6).
  actual: >
    CONFIRMED. setup_logging installs two handlers on the root logger:
    start.log (FileHandler, DEBUG) and debug.log (RotatingFileHandler,
    suppressed at CRITICAL + 1 unless debug). _finish_startup_logging
    raises start.log to CRITICAL + 1 once startup completes. From that
    point no handler accepts any record unless the operator has enabled
    debug in OPTIONS. Watchdog escalation, link loss, render faults and
    shutdown causes are all discarded.

    CONFIRMED. A static scan of src/gtach (excluding the two backup
    modules) finds 206 logger.error/critical calls inside handlers that
    catch Exception, BaseException or everything, without exc_info. Even
    with debug enabled, these record only str(e), so the failing line is
    unknown.
  impact: >
    Field faults cannot be diagnosed after the fact. The restart observed
    on 2026-10-07 is the concrete case: the watchdog's shutdown message
    was emitted and discarded. Every other finding in audit-36b6ea95 that
    manifests in the field (D01, B01, D02, D03, A06) would likewise leave
    no trace.
  workaround: >
    Enable debug in OPTIONS before reproducing a fault. This does not
    help with faults that are not anticipated, and debug.log at DEBUG
    level grows at roughly 10 MB per ninety minutes.

environment:
  python_version: "3.9"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies: []
  domain: "domain_1"

analysis:
  root_cause: >
    The two-file logging design (change-bd8f95b7) separates startup
    records from opt-in debug records but provides no persistent sink for
    warnings and errors during normal operation. The design treats
    "not debugging" as "nothing to record".
  technical_notes: >
    Making debug.log carry WARNING by default is the smallest edit but
    interferes with its rotate-at-start chain: every run that logged a
    warning would consume one of the ten generations, pushing deliberate
    debug captures off the end within ten boots (one restart per boot is
    already occurring, B13). A separate, small, always-on file keeps both
    purposes intact.

    The new handler must not rotate at start. A restart caused by a fault
    must leave the previous run's records in place; size-based rotation
    alone bounds disk use.

    Adding exc_info=True to handlers inside per-frame loops (for example
    DisplayManager render paths) can produce a traceback per frame. The
    size cap of the new file bounds the disk impact. Rate-limiting is out
    of scope.

    tests/test_stack_dump_toggle.py::TestSetupLoggingGate redirects
    _START_LOG and _DEBUG_LOG to tmp_path. Any new log path constant must
    be redirected there too, or the test will attempt to write
    /opt/gtach on the development host.
  related_issues:
    - issue_ref: "issue-b9ee7428"
      relationship: "related. The restart that this defect left unexplained."
    - issue_ref: "issue-6a3b7c52"
      relationship: "related. Established debug.log rotate-at-start; must remain unchanged."
    - issue_ref: "issue-bd8f95b7"
      relationship: "related. Established the app-owned two-file logging this issue extends."

resolution:
  assigned_to: ""
  target_date: ""
  approach: >
    1. Add a third, always-on handler: /opt/gtach/error.log, a
    RotatingFileHandler at WARNING, size-rotated only, untouched by the
    startup-completion and debug-toggle paths.

    2. Add exc_info=True to every logger.error and logger.critical call
    inside a broad exception handler, and add a test that enforces the
    rule so that it holds for future code.
  change_ref: "change-269871a0"
  resolved_date: ""
  resolved_by: ""
  fix_description: "setup_logging now adds an always-on WARNING-level error.log (1 MiB x 5, never rotated at start), and all 204 ERROR/CRITICAL calls in broad exception handlers pass exc_info=True, enforced by tests/test_logging_policy.py (commit 5f3c50be158bf2bea57f47edf7383062032c3213)."

verification:
  verified_date: ""
  verified_by: ""
  test_results: ""
  closure_notes: ""

prevention:
  preventive_measures: >
    A policy test enforces exc_info on broad handlers. Any future change
    to logging must state where WARNING and above go when debug is off.
  process_improvements: >
    On-device verification of a fault should begin by confirming the
    fault would be recorded with debug off.

verification_enhanced:
  verification_steps:
    - "Confirm from source that no handler accepts records after startup with debug off. [DONE: audit-36b6ea95 B04 and on-device check.]"
    - "After the fix: with debug off, cause a runtime error and confirm it appears in /opt/gtach/error.log with a traceback."
    - "After the fix: restart the service and confirm error.log retains the previous run's records."
    - "After the fix: toggle debug on and off and confirm error.log continues to receive WARNING and above throughout."
  verification_results: "First step complete. Remaining steps require the fix."

traceability:
  design_refs: []
  change_refs:
    - "change-269871a0"
  test_refs: []

notes: >
  Audit reference: audit-36b6ea95 B04 and A11, Section 6 on-device
  verification.

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
      - "Initial issue document from audit-36b6ea95 B04 and A11, confirmed on device."
  - version: "1.1"
    date: "2026-10-07"
    author: "Claude Code"
    changes:
      - "Fix implemented in 5f3c50be158bf2bea57f47edf7383062032c3213; awaiting on-device verification."

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
| 1.0 | 2026-10-07 | Initial issue document. No log sink after startup with debug off (B04); broad handlers log without tracebacks (A11). |
| 1.1 | 2026-10-07 | Fix implemented in 5f3c50be158bf2bea57f47edf7383062032c3213; awaiting on-device verification. |

---

Copyright (c) 2026 William Watson. MIT License.
