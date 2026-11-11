# Issue: Application Lifecycle, Logging and Utility Defects

Created: 2026 November 11

## Table of Contents

- [1.0 Issue Information](#10-issue-information)
- [Version History](#version-history)

---

## 1.0 Issue Information

```yaml
issue_info:
  id: "issue-042dd7ff"
  title: "Setup re-entry, OBD start and exit-status defects in app.py; logging cost and side effects in main.py; watchdog log repetition; configuration, dependency, terminal and reset-outcome defects in utils/"
  date: "2026-11-11"
  reporter: "William Watson"
  status: "resolved"
  severity: "low"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-042dd7ff"
    change_iteration: 1

source:
  origin: "code_review"
  test_ref: ""
  description: "Raised from audit-71ab3751 findings B01, B02, B03, B04, B06 (app part), B07, E02, E03, E04, E05, E06, F01, observation O1, the cause of G01, the application part of A10, and the ai/task.md rows: [tool.mypy] platform, --validate-config logging, Reset outcome log, log paths and GTACH_HOME, load_engine_profile DEBUG record, unchecked get_state_info."

affected_scope:
  components:
    - name: "GTachApplication: _re_enter_setup, _start_obd, _on_setup_complete, run, shutdown, logging switches"
      file_path: "src/gtach/app.py"
    - name: "main, setup_logging, log path constants"
      file_path: "src/gtach/main.py"
    - name: "WatchdogMonitor._handle_critical_timeout"
      file_path: "src/gtach/core/watchdog.py"
    - name: "ConfigStore.load, ConfigStore.save, load_engine_profile"
      file_path: "src/gtach/utils/config.py"
    - name: "Dependency validator debug path"
      file_path: "src/gtach/utils/dependencies.py"
    - name: "TerminalRestorer.__init__"
      file_path: "src/gtach/utils/terminal.py"
    - name: "reboot_device; module docstring"
      file_path: "src/gtach/utils/pi_reset.py"
    - name: "get_state_info"
      file_path: "src/gtach/utils/ack_state.py"
    - name: "[tool.mypy]"
      file_path: "pyproject.toml"
    - name: "SIGTERM test"
      file_path: "tests/test_lifecycle_sim.py"
  designs: []
  version: "0.4.13"

reproduction:
  prerequisites: "From source; Pi for the logging and reset rows."
  steps:
    - "B01: 'gtach --transport simbt', complete setup, tap Setup on the DISCONNECTED screen, pair again."
    - "B04: start with a failing startup; read the unit's result in 'systemctl status gtach'."
    - "G01 cause: run 'gtach --validate-config' while the service runs; read /opt/gtach/start.log."
    - "Log paths: run on the Mac with GTACH_HOME set; no log file appears under it."
  frequency: "always"
  reproducibility_conditions: "From source."
  test_data: >
    B01: _re_enter_setup calls _start_setup_mode() without
    pairing_factory, so a simbt session re-enters setup with the real
    BluetoothPairing.
    B02: _start_obd always passes adapter_pre_initialised=True; the
    stored-device probe and the Cancel path send no ATZ.
    B03: _on_setup_complete sets _obd_started before _start_obd; a
    raising _start_obd leaves the flag set.
    B04: main() returns 0 after a startup failure, a watchdog exit or a
    runtime error; shutdown() runs all steps in one try block.
    B06: the comment in _re_enter_setup states a 2.0 s bound that does
    not hold before change-b4f9607a.
    B07: _handle_critical_timeout logs 'initiating emergency
    procedures' at ERROR on every 5 s check for a stalled non-critical
    thread and takes no action for it.
    O1: setup_logging fixes the root logger at DEBUG; with debug off,
    every logger.debug call still builds a record, per frame and per
    OBD command.
    --validate-config and --validate-dependencies run after
    setup_logging, which truncates start.log and can rotate debug.log.
    Log paths are fixed at /opt/gtach/ regardless of GTACH_HOME.
    Reset: 'Reset outcome: reboot command failed' was logged on
    2026-10-09 10:14:04 although the Pi rebooted; reboot_device maps
    every non-zero return code to that text and does not log the code
    above DEBUG.
    load_engine_profile logs 'importlib.resources failed' at DEBUG on
    every start and then falls back.
    get_state_info returns yaml.safe_load's result unchecked under a
    type: ignore.
    E02: pi_reset's docstring states subprocess is imported nowhere
    else; comm/system_bluetooth.py and utils/platform.py import it.
    E03: in debug mode the ImportError handler calls
    importlib.util.find_spec('RPi.GPIO'), which raises
    ModuleNotFoundError when the parent package is absent.
    E04: TerminalRestorer calls sys.stdin.fileno() unguarded.
    E05: concurrent ConfigStore.save calls share one temp path.
    E06: load() coerces with kind(value) and accepts values validate()
    rejects.
    F01: 'assert proc.wait(timeout=10.0) is not None' passes for any
    exit status.
    mypy: a plain 'mypy src/' on macOS reports 4 platform-only errors.
  error_output: "None common."

behavior:
  expected: "A simulated session stays simulated; ATZ is skipped only when this session reset the adapter; a failed start is visible in the exit status; diagnostics commands have no side effects on the service's logs; debug-off logging costs no record construction."
  actual: "As in test_data."
  impact: "Low individually. B02 can leave an adapter unreset; B04 hides failures from systemd; O1 is avoidable work on the display and OBD threads."
  workaround: "None needed."

environment:
  python_version: "3.9"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies: []
  domain: "domain_1"

analysis:
  root_cause: "Individual omissions; no common cause."
  technical_notes: >
    The cause of the 'reboot command failed' record is not established.
    Inference: /sbin/reboot is terminated, or returns non-zero, while
    systemd is already stopping the unit. The change logs the return
    code so the next occurrence decides it.
    The cause of the importlib.resources DEBUG record is not
    established either; the change requires it to be determined before
    it is fixed.
    gtach.service has Restart=always, so a non-zero exit status changes
    what systemd records, not whether it restarts.
  related_issues:
    - issue_ref: "issue-b4f9607a"
      relationship: "related. Provides set_device_store_path and the non-joining OBD stop function."

resolution:
  assigned_to: ""
  target_date: ""
  approach: "See change-042dd7ff."
  change_ref: "change-042dd7ff"
  resolved_date: "2026-11-11"
  resolved_by: "change-042dd7ff"
  fix_description: "Setup re-entry keeps the pairing factory; simbt uses config/devices-sim.yaml; ATZ is skipped only after an adapter reset in this setup session (attribute supplied by run 4); _obd_started cleared when _start_obd raises; exit status 1 after startup failure, runtime error or watchdog exit; shutdown steps isolated; root log level WARNING after startup unless debug; validation commands log to stderr only; log paths from gtach_home(); one rate-limited WARNING for a stalled non-critical thread; one type rule for ConfigStore load and validate; serialised save; engine profile resolved through files('gtach') (Python 3.9 namespace-package TypeError); find_spec guard; TerminalRestorer tolerates a missing stdin; reboot return code logged, a negative code treated as a reboot in progress; pi_reset docstring corrected; get_state_info checks its type; [tool.mypy] platform = linux; SIGTERM test asserts status 0 (commit 2cffdaeaef6b774b3b2ba21fbe4741d647ad0b11; report-042dd7ff)."

verification:
  verified_date: ""
  verified_by: ""
  test_results: ""
  closure_notes: ""

prevention:
  preventive_measures: "Diagnostic entry points do not share the service's logging setup."
  process_improvements: "None."

verification_enhanced:
  verification_steps:
    - "Confirm from source. [DONE, audit-71ab3751.]"
    - "After the fix: unit tests per change-042dd7ff."
    - "After the fix: device session A — start.log unchanged after 'gtach --validate-config'; debug toggle writes debug.log; Reset logs its return code; 'systemctl status' after a forced startup failure."
  verification_results: "pytest 654 passed and mypy clean (worker's results). Device session A outstanding."

traceability:
  design_refs: []
  change_refs:
    - "change-042dd7ff"
  test_refs: []

notes: "Audit reference: audit-71ab3751 B01-B04, B06, B07, E02-E06, F01, O1, G01 (cause), A10 (application part). Run 3 of proposal-71ab3751."

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-11-11"
    author: "William Watson"
    changes:
      - "Initial issue document."

  - version: "1.1"
    date: "2026-11-11"
    author: "William Watson"
    changes:
      - "Resolved by change-042dd7ff (2cffdaeaef6b774b3b2ba21fbe4741d647ad0b11); awaiting device session A."

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
| 1.0 | 2026-11-11 | Initial issue document. B01-B04, B06, B07, E02-E06, F01, O1 and six task rows. |
| 1.1 | 2026-11-11 | Resolved by change-042dd7ff (2cffdae); awaiting device session A. |

---

Copyright (c) 2026 William Watson. MIT License.
