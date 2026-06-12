Created: 2026 June 12

```yaml
issue_info:
  id: "issue-bd8f95b7"
  title: "Logging is unowned, ephemeral, and not suitable for an unattended boot device"
  date: "2026-06-12"
  reporter: "William Watson"
  status: "open"
  severity: "medium"
  type: "enhancement"
  iteration: 1
  coupled_docs:
    change_ref: "change-bd8f95b7"
    change_iteration: 1

source:
  origin: "requirement_change"
  test_ref: ""
  description: >
    GTach's log output is owned by the launch shell via a tee pipe. Under
    systemd auto-start there is no shell, no tee, and no persistent log.
    The debug toggle (Item 3) and the OPTIONS update UI both require the
    application to own its log files. A two-file model is required:
    start.log captures startup unconditionally; debug.log captures post-startup
    detail only when debug is active.

affected_scope:
  components:
    - name: "setup_logging"
      file_path: "src/gtach/main.py"
    - name: "GTachApplication"
      file_path: "src/gtach/app.py"
  designs:
    - design_ref: "design-gtach-master"
  version: "0.2.61"

reproduction:
  prerequisites: "Deploy via systemd unit (1f4754d3)."
  steps:
    - "Reboot Pi. GTach starts via systemd."
    - "Look for a log file. None exists — stdout/stderr go to journald only."
    - "Transfer log from Pi — there is no log file to transfer."
  frequency: "always"
  reproducibility_conditions: "Any boot under systemd without the tee wrapper."
  preconditions: ""
  test_data: ""
  error_output: ""

behavior:
  expected: >
    On every boot: /opt/gtach/start.log is truncated and startup records are
    written. After startup, file logging is suppressed unless debug is active.
    /opt/gtach/debug.log receives post-startup records when debug is toggled on
    (via --debug flag or OPTIONS toggle); it is truncated at boot and rotates at
    100 MB with no backup copies retained.
  actual: >
    No log files are produced. All output goes to stderr, captured only by the
    interactive tee wrapper. Under systemd, output goes to journald only.
  impact: >
    Post-mortem diagnosis impossible without journald access. The in-app debug
    toggle (Item 3) has nothing to act on. The scp-log-to-Mac workflow is broken.
  workaround: "Launch manually with the tee wrapper (not viable under systemd)."

environment:
  python_version: "3.11"
  os: "Debian Linux (Raspberry Pi Zero 2W)"
  dependencies: []
  domain: "domain_1"

analysis:
  root_cause: >
    main.py:setup_logging() configures the root logger to stderr (debug) or
    NullHandler (normal). File ownership was historically provided by the tee
    shell wrapper. ConfigManager.setup_logging() implements file logging but is
    never called from the launch path.
  technical_notes: >
    Resolution replaces main.py:setup_logging() with a two-handler root logger:
    a startup FileHandler (/opt/gtach/start.log, truncated at boot, detached after
    startup) and a RotatingFileHandler (/opt/gtach/debug.log, truncated at boot,
    suppressed by default, activated by toggle). Both handlers are Linux-only;
    non-Linux falls back to the existing stderr/NullHandler behaviour. The faulthandler
    diagnostic already writes to stderr; under systemd stderr is captured by journald,
    so no redirection is required. ConfigManager.setup_logging() is not removed
    but is explicitly not called from the new path (it is unused infrastructure).
  related_issues: []

resolution:
  assigned_to: "Claude Code"
  target_date: "2026-06-12"
  approach: "See change-bd8f95b7"
  change_ref: "change-bd8f95b7"
  resolved_date: ""
  resolved_by: ""
  fix_description: ""

verification:
  verified_date: ""
  verified_by: ""
  test_results: ""
  closure_notes: ""

prevention:
  preventive_measures: >
    Application-owned file logging should be established from the first deployment
    to any unattended device.
  process_improvements: ""

traceability:
  design_refs:
    - "design-gtach-master"
  change_refs:
    - "change-bd8f95b7"
  test_refs: []

notes: >
  Prerequisite for Item 3 (debug toggle in OPTIONS). The toggle method
  toggle_debug_logging() is delivered in this item but wired to OPTIONS in Item 3.

version_history:
  - version: "1.0"
    date: "2026-06-12"
    author: "William Watson"
    changes:
      - "Initial issue document."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t03_issue"
```
