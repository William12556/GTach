# Prompt: Application Lifecycle, Logging and Utility Corrections

Created: 2026 November 11

## Table of Contents

- [1.0 Prompt](#10-prompt)
- [Version History](#version-history)

---

## 1.0 Prompt

```yaml
prompt_info:
  id: "prompt-042dd7ff"
  task_type: "debug"
  source_ref: "change-042dd7ff"
  target_profile: "claude_code"
  date: "2026-11-11"
  iteration: 1
  coupled_docs:
    change_ref: "change-042dd7ff"
    change_iteration: 1

context:
  purpose: "Run 3 of proposal-71ab3751: application lifecycle, logging and utils findings of audit-71ab3751 and six ai/task.md rows."
  integration: "src/gtach/app.py, main.py, core/watchdog.py, utils/*, pyproject.toml; tests."
  knowledge_references:
    - "ai/workspace/issues/issue-042dd7ff-lifecycle-logging-utils.md"
    - "ai/workspace/change/change-042dd7ff-lifecycle-logging-utils.md"
    - "ai/workspace/change/change-b4f9607a-comm-layer-defects.md (EDITS D and I: interfaces used here)"
    - "CLAUDE.md section 4 (rule 8) and the logging table"
  constraints:
    - "CRITICAL: edit no source file under src/gtach/comm or src/gtach/display."
    - "CRITICAL: the exit backstop is armed exactly once per process and shutdown() stays idempotent (issue-d140121d). Shutdown order is unchanged."
    - "CRITICAL: handler levels and files of start.log, debug.log and error.log are unchanged; only the root logger level and the path derivation change."
    - "set_device_store_path is called before the first get_device_store() of the process, and only for transport 'simbt'."
    - "gtach.main is reached from app.py through sys.modules['gtach.main'] (issue-c1d4b8e6); keep that access pattern for set_runtime_log_level."
    - "pi_reset keeps a fixed argument list, no shell, and never raises."
    - "Every logger .error or .critical in a broad handler passes exc_info=True."
    - "Monotonic clock for rate limiting."
    - "Python 3.9+ compatible. PEP 8, line length 88. Type hints on public interfaces. Google-style docstrings."

specification:
  description: "Apply EDITS A to F and the COMMENT RULE of change-042dd7ff; add tests/test_lifecycle_logging_utils.py."
  requirements:
    functional:
      - "As in change-042dd7ff proposed_solution."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Thread-safe if concurrent access"
        - "Professional docstrings"
  performance:
    - target: "No LogRecord is created for logger.debug calls while debug logging is off after startup"
      metric: "resources"

design:
  architecture: "Unchanged."
  components:
    - name: "EDITS A to F"
      type: "module"
      purpose: "As in change-042dd7ff."
      logic:
        - "EDIT A(5): keep one attribute for the exit status, default 0; _watchdog_shutdown and the two exception paths set 1; _request_restart and the signal handler leave 0. main() returns app.run()."
        - "EDIT A(5): a startup failure currently re-raises out of start() after shutdown(); run() catches it and the status is 1."
        - "EDIT B(2): parse arguments, then branch to the validation commands before any file handler exists; use logging.basicConfig(stream=sys.stderr) there."
        - "EDIT B(3): compute the paths inside setup_logging and keep module-level names that stack_dump.install and tests can read; the default home must give the present /opt/gtach paths."
        - "EDIT C: keep the rate-limit timestamp on ThreadHealth or beside it; reset it when the thread recovers."
        - "EDIT D(1): bool is a subclass of int; test for it explicitly."
        - "EDIT D(3): first reproduce the DEBUG record in a test or a one-off run and state the cause in the report."
        - "EDIT D(6): subprocess.CompletedProcess.returncode is negative when the child was ended by a signal."

data_schema:
  entities: []

error_handling:
  strategy: "Shutdown steps are isolated; validation commands never open the service's log files; nothing new raises out of shutdown or pi_reset."
  exceptions: []
  logging:
    level: "Root DEBUG during startup, then WARNING, or DEBUG while the debug switch is on"
    format: "Unchanged"

testing:
  unit_tests:
    - scenario: "As listed in change-042dd7ff testing_requirements.test_cases."
      expected: "As listed there."
  edge_cases:
    - "toggle_debug_logging(False) must log its own INFO record before lowering the root level, or accept that it is not written; state which in the docstring."
    - "shutdown() called twice: steps run once."
    - "GTACH_HOME not writable: logging setup warns on stderr and startup continues, as today."
  validation:
    - "pytest tests/ passes."
    - "mypy src/ reports no issues, on Linux and with platform = linux on macOS."

deliverable:
  format_requirements:
    - "Edit in place; one new test module; one commit."
    - "Report: per EDIT, what changed; the cause found for the importlib.resources record; any deviation from the change document; test results."
  files:
    - path: "src/gtach/app.py"
      content: "EDIT A; call sites of EDIT B(1)"
    - path: "src/gtach/main.py"
      content: "EDIT B"
    - path: "src/gtach/core/watchdog.py"
      content: "EDIT C"
    - path: "src/gtach/utils/config.py, dependencies.py, terminal.py, pi_reset.py, ack_state.py"
      content: "EDIT D"
    - path: "pyproject.toml"
      content: "EDIT E"
    - path: "tests/test_lifecycle_logging_utils.py, tests/test_lifecycle_sim.py"
      content: "Tests, EDIT F"

success_criteria:
  - "_re_enter_setup reuses the session's pairing factory."
  - "A 'simbt' session uses config/devices-sim.yaml."
  - "adapter_pre_initialised is True only when the setup manager reports adapter_reset_in_session."
  - "_obd_started is cleared when _start_obd raises."
  - "main() returns 1 after startup failure, runtime error or watchdog exit, and 0 otherwise."
  - "Each shutdown step is isolated."
  - "The root logger is at WARNING after startup with debug off and follows the debug switch."
  - "--validate-config and --validate-dependencies open no log file."
  - "Log paths derive from gtach_home()."
  - "No 'emergency procedures' record for a non-critical thread."
  - "ConfigStore.load and validate() apply the same type rule; save is serialised."
  - "No type: ignore remains at get_state_info."
  - "git diff touches only app.py, main.py, core/, utils/, pyproject.toml and tests/."
  - "pytest tests/ passes; mypy src/ reports no issues."

element_registry:
  source: ""
  entries:
    modules: []
    classes: []
    functions:
      - name: "set_runtime_log_level"
        module: "gtach.main"
        signature: "(debug: bool) -> None"
      - name: "run"
        module: "gtach.app"
        signature: "(self) -> int"
      - name: "set_device_store_path"
        module: "gtach.comm.device_store"
        signature: "(path: Optional[str]) -> None"
    constants: []

notes: "Model: Claude Opus 5.5, effort medium, no ultracode. Human verification: device session A follows this run."
```

[Return to Table of Contents](#table-of-contents)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-11 | Initial prompt implementing change-042dd7ff iteration 1. Target profile claude_code. |

---

Copyright (c) 2026 William Watson. MIT License.
