Created: 2026 June 11

```yaml
change_info:
  id: "change-1f4754d3"
  title: "Add systemd auto-start unit with boot-time install and Tier 2 rollback"
  date: "2026-06-11"
  author: "William Watson"
  status: "approved"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-1f4754d3"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-1f4754d3"
  description: >
    Deliver auto-start on boot and a supervised, recoverable on-device update
    path, executed before the application launches.

scope:
  summary: >
    Add a tracked systemd unit (gtach.service) and a boot-time preflight script
    (gtach-preflight.sh) that performs probation-based rollback then installs any
    pending wheel via a dedicated non-interactive pip path. Extend install.sh to
    register the unit and preflight, create the updates directory, and seed the
    known-good wheel. Add one guarded application hook that clears the probation
    marker on healthy startup.
  affected_components:
    - name: "gtach.service"
      file_path: "gtach.service"
      change_type: "add"
    - name: "gtach-preflight.sh"
      file_path: "gtach-preflight.sh"
      change_type: "add"
    - name: "install.sh"
      file_path: "install.sh"
      change_type: "modify"
    - name: "GTachApplication"
      file_path: "src/gtach/app.py"
      change_type: "modify"
  affected_designs:
    - design_ref: "design-gtach-master"
      sections:
        - "Deployment"
  out_of_scope:
    - "OPTIONS in-app update check/install UI and marker writing (separate triple)."
    - "Logging re-architecture, splash version display, debug toggle."
    - "GitHub update source."
    - "Dependency changes: a wheel adding new dependencies requires manual install (offline device)."
    - "systemd sd_notify watchdog integration."

rational:
  problem_statement: >
    No auto-start exists and no supervised install/rollback path exists. The
    running process cannot safely reinstall itself, so install must occur at boot.
  proposed_solution: >
    A systemd unit launches gtach on boot. Its ExecStartPre runs a preflight
    script that always exits 0: it first checks an update-probation marker and
    rolls back to the previous wheel if a newly installed wheel has failed to
    reach healthy startup; then, if a wheel is staged and marked, validates and
    installs it before launch. The application removes the probation marker once
    it reaches successful startup, signalling the update is healthy.
  alternatives_considered:
    - option: "Install from within the running application."
      reason_rejected: "A process cannot reliably reinstall its own venv; unsafe."
    - option: "Tier 1 (install-time safety only), no runtime health check."
      reason_rejected: "Does not catch a wheel that installs cleanly but crashes at startup — a known failure mode."
  benefits:
    - "Unattended start on boot suitable for in-vehicle use."
    - "Single install path reused by the later in-app update feature."
    - "Automatic recovery from a bad update without intervention."
  risks:
    - risk: "Preflight failure blocks boot."
      mitigation: "Preflight always exits 0; ExecStartPre uses the '-' prefix so a crash is ignored."
    - risk: "Probation threshold interacts badly with StartLimitBurst."
      mitigation: "Threshold 2 with burst 3; rollback fires before the burst limit, then the good wheel launches."
    - risk: "Rollback target absent on first update."
      mitigation: "install.sh seeds installed.whl; preflight copies installed.whl to previous.whl before each install."

technical_details:
  current_behavior: >
    gtach is launched manually. install.sh installs a wheel into /opt/gtach/venv
    and prints manual systemctl hints, but no unit file is tracked or installed.
  proposed_behavior: >
    gtach.service auto-starts gtach. ExecStartPre=/opt/gtach/gtach-preflight.sh
    performs rollback and pending install before ExecStart launches the venv
    entry point. The application clears /opt/gtach/.update-probation on healthy
    startup.
  implementation_approach: >
    Two new deploy files in the repo root, a focused install.sh extension on the
    Linux branch, and one guarded method in GTachApplication called at the end of
    a successful start().
  code_changes:
    - component: "gtach.service"
      file: "gtach.service"
      change_summary: >
        New systemd unit. [Unit] After=multi-user.target bluetooth.service,
        StartLimitIntervalSec=60, StartLimitBurst=3. [Service] Type=simple,
        User=root, WorkingDirectory=/opt/gtach,
        ExecStartPre=-/opt/gtach/gtach-preflight.sh,
        ExecStart=/opt/gtach/venv/bin/gtach, Restart=on-failure, RestartSec=5.
        [Install] WantedBy=multi-user.target.
      functions_affected: []
      classes_affected: []
    - component: "gtach-preflight.sh"
      file: "gtach-preflight.sh"
      change_summary: >
        New boot hook. Always exits 0. Step 1 (rollback): if probation marker
        present, read count; if >= 2 reinstall previous.whl, set installed.whl,
        delete marker; else increment and continue. Step 2 (install): if pending
        marker present, resolve wheel in updates/, validate zip via venv python,
        copy installed.whl to previous.whl, install via dedicated path, on success
        set installed.whl and reset probation to 0, on failure restore previous;
        always clear pending marker and staged wheel.
      functions_affected: []
      classes_affected: []
    - component: "install.sh"
      file: "install.sh"
      change_summary: >
        Linux branch only: after package install, copy gtach.service (from script
        dir) to /etc/systemd/system/, copy gtach-preflight.sh to /opt/gtach/
        (chmod +x), create /opt/gtach/updates/, copy the installed wheel to
        /opt/gtach/installed.whl, run systemctl daemon-reload and enable gtach.
      functions_affected: []
      classes_affected: []
    - component: "GTachApplication"
      file: "src/gtach/app.py"
      change_summary: >
        Add _clear_update_probation(): on Linux, remove /opt/gtach/.update-probation
        if present, tolerant of all errors. Call it as the final statement of the
        start() try block, after mode dispatch.
      functions_affected:
        - "start"
        - "_clear_update_probation"
      classes_affected:
        - "GTachApplication"
  data_changes:
    - entity: "/opt/gtach/.update-probation"
      change_type: "schema"
      details: "Plain-text integer marker; attempt counter for the current update under probation."
    - entity: "/opt/gtach/installed.whl, /opt/gtach/previous.whl"
      change_type: "schema"
      details: "Retained wheel copies: current known-good and rollback target."
    - entity: "/opt/gtach/updates/.install-pending"
      change_type: "schema"
      details: "Plain-text wheel filename staged for install (written by the later OPTIONS unit; consumed here)."
  interface_changes:
    - interface: "Supervisor contract (preflight <-> in-app update unit)"
      change_type: "contract"
      details: >
        Drop dir /opt/gtach/updates/; pending marker .install-pending containing a
        wheel filename; probation marker /opt/gtach/.update-probation. Defined here,
        consumed by the OPTIONS unit.
      backward_compatible: "n/a"

dependencies:
  internal:
    - component: "install.sh"
      impact: "Extended to register the unit; pre-existing manual run remains valid."
  external:
    - library: "systemd"
      version_change: "none"
      impact: "Unit installed and enabled."
  required_changes: []

testing_requirements:
  test_approach: "Manual verification on the Pi."
  test_cases:
    - scenario: "Reboot with no pending update."
      expected_result: "gtach starts automatically; preflight is a no-op; no probation marker."
    - scenario: "Stage a valid newer wheel and write .install-pending, then reboot."
      expected_result: "Preflight installs the wheel; gtach launches the new version; probation cleared on healthy startup."
    - scenario: "Stage a wheel that crashes at startup, then reboot."
      expected_result: "After threshold failed starts, preflight reverts to previous.whl; gtach launches the previous version."
    - scenario: "Stage a corrupt (truncated) wheel, then reboot."
      expected_result: "Preflight rejects it on zip validation; existing install launches unchanged."
  regression_scope:
    - "Manual install.sh on a fresh venv."
    - "Manual gtach launch from the venv."
  validation_criteria:
    - "gtach.service enabled and starts on boot."
    - "Preflight never blocks launch (always exits 0; '-' prefix)."
    - "Healthy update clears the probation marker on first good startup."
    - "Crash-looping update is reverted to previous.whl."
    - "Corrupt wheel is rejected without affecting the running install."

implementation:
  implementation_steps:
    - step: "Create gtach.service in repo root."
      owner: "Claude Code"
    - step: "Create gtach-preflight.sh in repo root."
      owner: "Claude Code"
    - step: "Extend install.sh Linux branch to register unit/preflight, seed wheel, create updates dir, enable service."
      owner: "Claude Code"
    - step: "Add _clear_update_probation() to GTachApplication and call it at end of start()."
      owner: "Claude Code"
  rollback_procedure: "Revert the four files via git; disable the unit with systemctl disable gtach on the Pi."
  deployment_notes: >
    scp install.sh, gtach.service and gtach-preflight.sh to /opt/gtach/ alongside
    the wheel; run install.sh. README §3 will be updated separately to document
    the new deploy files (documentation task, not part of this code change).

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
    - issue_ref: "issue-1f4754d3"
      relationship: "resolves"

notes: >
  Assumed location for the two new deploy files is the repo root, co-located with
  install.sh and build.sh. Adjust if a deploy/ subdirectory is preferred.

version_history:
  - version: "1.0"
    date: "2026-06-11"
    author: "William Watson"
    changes:
      - "Initial change document."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t02_change"
```
