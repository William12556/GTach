# Change: Application Lifecycle, Logging and Utility Corrections

Created: 2026 November 11

## Table of Contents

- [1.0 Change Information](#10-change-information)
- [Version History](#version-history)

---

## 1.0 Change Information

```yaml
change_info:
  id: "change-042dd7ff"
  title: "Keep the pairing factory on setup re-entry; skip ATZ only after a reset in this session; truthful exit status; step-wise shutdown; root log level follows the debug switch; side-effect-free validation commands; log paths under GTACH_HOME; utility corrections"
  date: "2026-11-11"
  author: "William Watson"
  status: "implemented"
  priority: "low"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-042dd7ff"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-042dd7ff"
  description: "Resolves issue-042dd7ff. Run 3 of proposal-71ab3751."

scope:
  summary: "Four edit groups: app.py, main.py, core/watchdog.py and utils/; one pyproject.toml line; tests."
  affected_components:
    - name: "GTachApplication"
      file_path: "src/gtach/app.py"
      change_type: "modify"
    - name: "main, setup_logging"
      file_path: "src/gtach/main.py"
      change_type: "modify"
    - name: "WatchdogMonitor"
      file_path: "src/gtach/core/watchdog.py"
      change_type: "modify"
    - name: "ConfigStore, load_engine_profile"
      file_path: "src/gtach/utils/config.py"
      change_type: "modify"
    - name: "Dependency validator, TerminalRestorer, pi_reset, ack_state"
      file_path: "src/gtach/utils/dependencies.py, terminal.py, pi_reset.py, ack_state.py"
      change_type: "modify"
    - name: "[tool.mypy]"
      file_path: "pyproject.toml"
      change_type: "modify"
    - name: "Tests"
      file_path: "tests/test_lifecycle_logging_utils.py (new), tests/test_lifecycle_sim.py"
      change_type: "add"
  affected_designs:
    - "design-b4c5d6e7-component_utils_config_manager"
  out_of_scope:
    - "src/gtach/comm and src/gtach/display."
    - "ThreadManager internals (core/thread.py): no change needed after change-b4f9607a."
    - "Shutdown join budgets (B04 part 3): the exit backstop bounds them; no change."
    - "[tool.mypy] python_version: see notes."
    - "The version number in pyproject.toml (one increment after run 5)."

rational:
  problem_statement: "See issue-042dd7ff."
  proposed_solution: >
    EDIT A — app.py lifecycle.
    (1) B01: remember the pairing_factory given to the first
    _start_setup_mode call on the instance; _re_enter_setup passes it.
    (2) A10 application part: before the first get_device_store()
    call, when the transport argument is 'simbt', call
    gtach.comm.device_store.set_device_store_path with
    gtach_home()/config/devices-sim.yaml.
    (3) B02: _start_obd passes adapter_pre_initialised from
    bool(getattr(self._setup_manager, 'adapter_reset_in_session',
    False)) when a setup manager exists, else False. The attribute is
    provided by change-34781bfe (run 4); until then ATZ is always sent.
    (4) B03: _on_setup_complete clears _obd_started under _obd_lock if
    _start_obd raises, logs the error with exc_info and leaves the
    display on the DISCONNECTED path it already has.
    (5) B04, decision D7: the application records an exit status.
    0: stop by SIGINT or SIGTERM and the update restart
    (_request_restart). 1: startup failure, runtime error in run(), and
    a watchdog-requested exit. run() returns it and main() returns it.
    (6) B04: each step of shutdown() runs in its own try/except that
    logs with exc_info and continues; order unchanged.
    (7) B06: the comment in _re_enter_setup states what holds after
    change-b4f9607a: each stop_thread call is bounded by its timeout.

    EDIT B — main.py logging.
    (1) O1: add set_runtime_log_level(debug: bool), which sets the
    root logger to DEBUG when debug is on and to WARNING otherwise.
    setup_logging keeps DEBUG for startup.
    GTachApplication._finish_startup_logging calls it with the current
    debug state after closing start.log; toggle_debug_logging calls it
    with the new state before logging its own INFO record. Handler
    levels are unchanged.
    (2) --validate-config and --validate-dependencies are handled
    before setup_logging and before stack_dump.install. They log to
    stderr only (WARNING and above, DEBUG with --debug) and open no log
    file. This removes the cause of G01.
    (3) The four log paths are derived from gtach_home() when logging
    is set up, replacing the fixed /opt/gtach constants. With the
    default home the paths are unchanged.

    EDIT C — core/watchdog.py (B07). For a thread that is not critical,
    _handle_critical_timeout logs one WARNING when the stall is first
    seen at this level, stating that no action is taken, and repeats it
    at most once per 60 s (monotonic) while the stall lasts. The text
    'initiating emergency procedures' is used only for critical
    threads. Behaviour for critical threads is unchanged.

    EDIT D — utils.
    (1) E06: ConfigStore.load accepts a value only if it passes the
    same type rule validate() applies (no bool for a number, no
    non-integral float for an int, no None); otherwise it warns and
    uses the default. One shared helper serves both methods.
    (2) E05: ConfigStore.save serialises the whole save with a
    dedicated lock (a file-serialising lock may span that file's I/O,
    CLAUDE.md section 4 rule 8).
    (3) load_engine_profile: determine why the importlib.resources
    path fails on a normal start, correct it so the packaged file is
    found by the first method, and remove the pkg_resources branch for
    Python below 3.9. A normal start logs no failure record.
    (4) E03: the debug-mode find_spec call is guarded against
    ImportError and ValueError.
    (5) E04: TerminalRestorer tolerates a missing or closed stdin
    (None, ValueError, OSError from fileno()): no backup is taken and
    construction succeeds.
    (6) Reset outcome: reboot_device logs the return code and the
    first line of stderr at WARNING when the code is not 0. A negative
    code (the command was ended by a signal) returns the 'reboot
    initiated' outcome, because the host is then already stopping the
    process. A positive code still returns 'reboot command failed'.
    (7) E02: the pi_reset module docstring states the actual boundary:
    pi_reset is the only module that acts on the host; subprocess is
    also used read-only for discovery (comm/system_bluetooth.py) and
    platform detection (utils/platform.py).
    (8) get_state_info returns the loaded value only if it is a dict,
    else None; the type: ignore and TODO markers at that site are
    removed.

    EDIT E — pyproject.toml: add platform = "linux" under [tool.mypy].

    EDIT F — tests/test_lifecycle_sim.py (F01): the SIGTERM test
    asserts exit status 0.

    COMMENT RULE — In every file edited, comments that narrate history
    are reduced to the current behaviour plus at most one issue
    reference (CLAUDE.md section 4).
  alternatives_considered:
    - option: "B02: always send ATZ and remove adapter_pre_initialised."
      reason_rejected: "Adds a second adapter reset after every pairing; the pre-initialised path exists to avoid it. Kept as the interim behaviour until run 4."
    - option: "O1: guard each debug call site."
      reason_rejected: "The root level removes the cost at every site at once."
    - option: "Exit status 1 for SIGTERM."
      reason_rejected: "A requested stop is not a failure."
  benefits:
    - "Simulated sessions leave the real device store untouched (with change-b4f9607a)."
    - "systemd records failures as failures."
    - "No record construction for debug calls when debug is off."
    - "Validation commands can be run beside the service."
  risks:
    - risk: "O1: a record expected in start.log after startup is lost."
      mitigation: "start.log is closed at the same point today; the level change follows that close."
    - risk: "B02 interim: ATZ directly after pairing verification is slow or fails on the emulator."
      mitigation: "Checked in device session A; resolved by run 4."
    - risk: "Reset outcome: a negative return code is not a reboot in progress."
      mitigation: "The code is logged at WARNING either way."
    - risk: "D7: a script depends on exit status 0."
      mitigation: "gtach.service uses Restart=always; the bin/ scripts test only the --validate-config status, whose meaning is unchanged."

technical_details:
  current_behavior: "See issue."
  proposed_behavior: "See proposed_solution."
  implementation_approach: "Local edits."
  code_changes:
    - component: "app"
      file: "src/gtach/app.py"
      change_summary: "EDIT A, EDIT B(1) call sites"
      functions_affected:
        - "GTachApplication.__init__"
        - "GTachApplication._start_setup_mode"
        - "GTachApplication._re_enter_setup"
        - "GTachApplication._start_obd"
        - "GTachApplication._on_setup_complete"
        - "GTachApplication.run"
        - "GTachApplication.shutdown"
        - "GTachApplication._watchdog_shutdown"
        - "GTachApplication._finish_startup_logging"
        - "GTachApplication.toggle_debug_logging"
      classes_affected: []
    - component: "main"
      file: "src/gtach/main.py"
      change_summary: "EDIT B"
      functions_affected:
        - "main"
        - "setup_logging"
        - "set_runtime_log_level (new)"
      classes_affected: []
    - component: "core"
      file: "src/gtach/core/watchdog.py"
      change_summary: "EDIT C"
      functions_affected:
        - "WatchdogMonitor._handle_critical_timeout"
      classes_affected: []
    - component: "utils"
      file: "config.py, dependencies.py, terminal.py, pi_reset.py, ack_state.py"
      change_summary: "EDIT D"
      functions_affected:
        - "ConfigStore.load"
        - "ConfigStore.save"
        - "load_engine_profile"
        - "TerminalRestorer.__init__"
        - "reboot_device"
        - "get_state_info"
      classes_affected: []
  data_changes: []
  interface_changes:
    - interface: "GTachApplication.run"
      change_type: "signature"
      details: "Returns the exit status (int)."
      backward_compatible: "yes"
    - interface: "Process exit status"
      change_type: "contract"
      details: "1 after startup failure, runtime error or watchdog exit; 0 otherwise."
      backward_compatible: "no"

dependencies:
  internal: []
  external: []
  required_changes:
    - change_ref: "change-b4f9607a"
      relationship: "precedes; provides set_device_store_path and the non-joining OBD stop function"

testing_requirements:
  test_approach: "Unit tests with stubs (object.__new__ for GTachApplication where construction is heavy); subprocess for main()."
  test_cases:
    - scenario: "B01: start setup with a factory, call _re_enter_setup with stubs."
      expected_result: "The second _start_setup_mode receives the same factory."
    - scenario: "A10: construct the application with transport 'simbt' and a temporary GTACH_HOME."
      expected_result: "get_device_store().config_path ends with config/devices-sim.yaml; with another transport it ends with devices.yaml."
    - scenario: "B02: _start_obd with no setup manager, with a manager lacking the attribute, and with adapter_reset_in_session True."
      expected_result: "adapter_pre_initialised False, False, True."
    - scenario: "B03: _on_setup_complete with _start_obd raising TransportError, then a second call."
      expected_result: "_obd_started False after the first; the second call runs _start_obd again."
    - scenario: "B04: run() with start raising; with _stop_event set by the signal handler; after _watchdog_shutdown; after _request_restart."
      expected_result: "1, 0, 1, 0."
    - scenario: "B04: shutdown with stop_setup raising."
      expected_result: "display.stop, transport.disconnect, obd.stop and thread_manager.shutdown are still called, in order."
    - scenario: "O1: set_runtime_log_level(False) then (True)."
      expected_result: "Root level WARNING then DEBUG; logger.isEnabledFor(DEBUG) False then True."
    - scenario: "main(['--validate-config']) with GTACH_HOME at a temporary directory holding a start.log with known content."
      expected_result: "start.log unchanged; no debug.log created; exit status reflects validity."
    - scenario: "Log paths with GTACH_HOME set."
      expected_result: "The handlers' files are under that directory."
    - scenario: "B07: a non-critical thread stalled across six watchdog checks (time patched)."
      expected_result: "One WARNING; no ERROR containing 'emergency'."
    - scenario: "E06: load() of a file with palette null, touch_long_press true, fps_limit 30.9."
      expected_result: "Three warnings; defaults used; validate() reports the same three keys."
    - scenario: "E05: two threads call save() 200 times each."
      expected_result: "All return True; the file parses after each."
    - scenario: "load_engine_profile on an installed package layout with DEBUG capture."
      expected_result: "No 'failed' record; the default profile loads."
    - scenario: "E03: validator in debug mode with import name 'RPi.GPIO' absent."
      expected_result: "No exception."
    - scenario: "E04: TerminalRestorer with sys.stdin None and with a closed stdin."
      expected_result: "Constructs; original_termios None."
    - scenario: "Reset: subprocess.run stub returning 0, 1 and -15."
      expected_result: "'reboot initiated', 'reboot command failed', 'reboot initiated'; a WARNING naming the code for 1 and -15."
    - scenario: "get_state_info with a state file holding a YAML list."
      expected_result: "None."
    - scenario: "F01: SIGTERM lifecycle test."
      expected_result: "Exit status 0."
  regression_scope:
    - "tests/test_lifecycle_sim.py, tests/test_watchdog_process_termination.py, tests/test_medium_defects.py and the config, logging and updater tests."
    - "Full tests/ suite."
  validation_criteria:
    - "pytest tests/ passes; mypy src/ reports no issues."

implementation:
  effort_estimate: ""
  implementation_steps:
    - step: "EDITS A to F and tests."
      owner: "tactical"
    - step: "Device session A: logging checks, Reset return code, forced startup failure, simbt re-entry."
      owner: "human"
  rollback_procedure: "Revert the commit."
  deployment_notes: "bin/gtach-verify-36b6ea95.sh reads /opt/gtach/start.log; unaffected with the default home."

verification:
  implemented_date: "2026-11-11"
  implemented_by: "Claude Code"
  verification_date: ""
  verified_by: ""
  test_results: "Commit 2cffdaeaef6b774b3b2ba21fbe4741d647ad0b11: pytest 654 passed (35 new in tests/test_lifecycle_logging_utils.py); mypy src/ no issues (worker's results, report-042dd7ff section 5)."
  issues_found:
    - "load_engine_profile cause: gtach.assets has no __init__.py; on Python 3.9 importlib.resources.files() raises TypeError for such a namespace package. Fixed by resolving from files('gtach'). Not reproduced on 3.9 by the worker; confirm in device session A."
    - "E06: an integral float (fps_limit: 30.0) is now accepted by both load() and validate(); validate() previously rejected it."
    - "B03: if _start_obd fails after the transport thread has started, that thread keeps running until setup is re-entered. Accepted."
    - "toggle_debug_logging(False): 'Debug logging disabled' is not written anywhere, as before the change."

traceability:
  design_updates:
    - "design-b4c5d6e7 (config): load() type rule. Planner, in the design refresh after run 5."
  related_changes:
    - change_ref: "change-b4f9607a"
      relationship: "depends on"
    - change_ref: "change-34781bfe"
      relationship: "follows; provides SetupDisplayManager.adapter_reset_in_session"
  related_issues:
    - issue_ref: "issue-042dd7ff"
      relationship: "resolves"

notes: >
  Open point, not changed here: [tool.mypy] python_version = "3.9" is
  not selectable in the installed mypy release. The device runs Python
  3.9, so raising the value would stop mypy checking 3.9 compatibility;
  pinning an older mypy is the alternative. Owner decision.

version_history:
  - version: "1.0"
    date: "2026-11-11"
    author: "William Watson"
    changes:
      - "Initial change document resolving issue-042dd7ff iteration 1."

  - version: "1.1"
    date: "2026-11-11"
    author: "William Watson"
    changes:
      - "Approved for implementation by William Watson."

  - version: "1.2"
    date: "2026-11-11"
    author: "William Watson"
    changes:
      - "Implemented in 2cffdaeaef6b774b3b2ba21fbe4741d647ad0b11; awaiting device session A."

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
| 1.0 | 2026-11-11 | Initial change document. EDITS A to F. |
| 1.1 | 2026-11-11 | Approved for implementation. |
| 1.2 | 2026-11-11 | Implemented in 2cffdae; awaiting device session A. |

---

Copyright (c) 2026 William Watson. MIT License.
