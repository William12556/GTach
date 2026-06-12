Created: 2026 June 12

```yaml
change_info:
  id: "change-bd8f95b7"
  title: "Replace tee-based logging with app-owned two-file model"
  date: "2026-06-12"
  author: "William Watson"
  status: "approved"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-bd8f95b7"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-bd8f95b7"
  description: >
    Replace the tee-pipe logging pattern with application-owned file handlers
    that survive systemd launch and support the future in-app debug toggle.

scope:
  summary: >
    Replace main.py:setup_logging() with a two-handler root logger. Add
    _finish_startup_logging() and toggle_debug_logging() to GTachApplication.
    On Linux: start.log captures startup; debug.log captures post-startup
    detail when toggled on. On non-Linux: existing stderr/NullHandler behaviour
    is preserved unchanged.
  affected_components:
    - name: "setup_logging"
      file_path: "src/gtach/main.py"
      change_type: "modify"
    - name: "GTachApplication"
      file_path: "src/gtach/app.py"
      change_type: "modify"
  affected_designs:
    - design_ref: "design-gtach-master"
      sections:
        - "Deployment"
        - "Logging"
  out_of_scope:
    - "Wiring toggle_debug_logging() to the OPTIONS UI (Item 3)."
    - "ConfigManager.setup_logging() — unused, not removed, not called."
    - "faulthandler redirection — stderr captured by journald under systemd."
    - "Log file location configuration via config.yaml."
    - "macOS logging behaviour — unchanged."

rational:
  problem_statement: >
    The tee-pipe pattern is incompatible with systemd. No persistent log is
    produced on boot, blocking diagnosis and making the debug toggle impossible.
  proposed_solution: >
    The root logger acquires two FileHandlers at startup (Linux only). The
    startup handler is detached when the application reaches normal running
    state. The debug handler is suppressed by default and activated via a
    method that the OPTIONS toggle will call in Item 3.
  alternatives_considered:
    - option: "Use ConfigManager.setup_logging()."
      reason_rejected: >
        Session-ID filename scheme produces unbounded file accumulation unsuitable
        for an embedded device; requires the ConfigManager path to be stable before
        logging is initialised.
    - option: "Write to journald via systemd-cat or sd-journal."
      reason_rejected: >
        Breaks the existing scp-log-to-Mac workflow; adds a systemd dependency
        to the Python package.
  benefits:
    - "Persistent startup record on every boot."
    - "Debug log bounded to 100 MB; no accumulation across boots."
    - "Provides the toggle mechanism required by Item 3."
    - "Non-Linux behaviour unchanged — no regression on dev machine."
  risks:
    - risk: "/opt/gtach not writable on first boot before install.sh has run."
      mitigation: >
        FileHandler open is guarded; on any OSError the handler is skipped and
        the root logger falls back to stderr. A failed open is printed to stderr
        (journald) and does not abort startup.
    - risk: "RotatingFileHandler truncation at boot discards the previous session's debug.log."
      mitigation: "Confirmed requirement: debug.log is truncated at every boot."

technical_details:
  current_behavior: >
    main.py:setup_logging(debug): debug=True -> basicConfig to stderr at DEBUG;
    debug=False -> NullHandler. No files produced. Under systemd all output
    goes to journald.
  proposed_behavior: >
    main.py:setup_logging(debug) on Linux:
      Root logger set to DEBUG.
      start_handler: FileHandler('/opt/gtach/start.log', mode='w'), level=DEBUG.
        Formatter: '%(asctime)s,%(msecs)03d %(name)s %(levelname)s %(message)s'.
      debug_handler: RotatingFileHandler('/opt/gtach/debug.log', mode='w',
        maxBytes=100*1024*1024, backupCount=0), level=CRITICAL+1 (suppressed).
        Same formatter.
      Both handlers stored as module-level references for later manipulation.
      If --debug flag: debug_handler raised to DEBUG immediately.
      On non-Linux: existing behaviour preserved (basicConfig stderr or NullHandler).
    GTachApplication.start() calls self._finish_startup_logging() at the same
      site as _clear_update_probation() — end of the startup try block.
    _finish_startup_logging(): raises start_handler level to CRITICAL+1
      (effectively silent), logging "Startup complete — start.log closed".
    toggle_debug_logging(enable: bool): sets debug_handler level to DEBUG or
      CRITICAL+1, logs the state change. No-op on non-Linux. Tolerant of all
      errors.
  implementation_approach: >
    Module-level handler references in main.py (_start_handler, _debug_handler).
    GTachApplication imports the toggle function from main. Three small, isolated
    additions; no structural change.
  code_changes:
    - component: "setup_logging"
      file: "src/gtach/main.py"
      change_summary: >
        Replace the two-branch setup_logging() with the two-handler Linux
        implementation. Expose _start_handler and _debug_handler as module-level
        references. Preserve non-Linux behaviour in the else branch.
      functions_affected:
        - "setup_logging"
      classes_affected: []
    - component: "GTachApplication"
      file: "src/gtach/app.py"
      change_summary: >
        Add _finish_startup_logging() and toggle_debug_logging(enable). Call
        _finish_startup_logging() at the end of start() try block alongside
        _clear_update_probation(). No other changes.
      functions_affected:
        - "start"
        - "_finish_startup_logging"
        - "toggle_debug_logging"
      classes_affected:
        - "GTachApplication"
  data_changes:
    - entity: "/opt/gtach/start.log"
      change_type: "schema"
      details: "New file. Truncated at boot. Receives startup records only."
    - entity: "/opt/gtach/debug.log"
      change_type: "schema"
      details: >
        New file. Truncated at boot. Receives post-startup DEBUG records when
        toggle is active. Rotates at 100 MB, no backups retained.
  interface_changes:
    - interface: "toggle_debug_logging"
      change_type: "contract"
      details: >
        GTachApplication.toggle_debug_logging(enable: bool) -> None.
        Called by the OPTIONS toggle in Item 3.
      backward_compatible: "n/a"

dependencies:
  internal:
    - component: "GTachApplication.start"
      impact: "One additional call at end of try block."
  external: []
  required_changes: []

testing_requirements:
  test_approach: "Manual verification on Pi after wheel deployment."
  test_cases:
    - scenario: "Boot without --debug."
      expected_result: >
        /opt/gtach/start.log exists and contains startup records.
        /opt/gtach/debug.log exists but contains no post-startup records.
    - scenario: "Boot with --debug."
      expected_result: >
        /opt/gtach/start.log contains startup records.
        /opt/gtach/debug.log contains post-startup DEBUG records.
    - scenario: "Second boot (no --debug)."
      expected_result: >
        Both files are truncated; previous session content is gone.
    - scenario: "toggle_debug_logging(True) called at runtime."
      expected_result: "debug.log begins receiving records immediately."
    - scenario: "toggle_debug_logging(False) called at runtime."
      expected_result: "debug.log receives no further records."
  regression_scope:
    - "macOS dev launch — no log files created; stderr logging unchanged."
    - "validate-config and validate-dependencies modes — unaffected."
  validation_criteria:
    - "start.log present and non-empty after boot."
    - "debug.log present on Pi (may be empty in normal mode)."
    - "No startup crash attributable to logging setup."
    - "toggle_debug_logging callable without error."

implementation:
  implementation_steps:
    - step: "Rewrite setup_logging() in main.py."
      owner: "Claude Code"
    - step: "Add _finish_startup_logging() and toggle_debug_logging() to app.py."
      owner: "Claude Code"
    - step: "Call _finish_startup_logging() at end of start() try block."
      owner: "Claude Code"
  rollback_procedure: "Revert main.py and app.py via git."
  deployment_notes: >
    Build wheel and deploy to Pi per standard workflow. No config.yaml changes
    required. /opt/gtach/ is writable by root (confirmed by systemd unit).

verification:
  implemented_date: ""
  implemented_by: ""
  verification_date: ""
  verified_by: ""
  test_results: ""
  issues_found: []

traceability:
  related_changes: []
  related_issues:
    - issue_ref: "issue-bd8f95b7"
      relationship: "resolves"

notes: ""

version_history:
  - version: "1.0"
    date: "2026-06-12"
    author: "William Watson"
    changes:
      - "Initial change document."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t02_change"
```
