Created: 2026 June 12

```yaml
change_info:
  id: "change-f993f871"
  title: "Add OPTIONS update check/install with restart-to-apply"
  date: "2026-06-12"
  author: "William Watson"
  status: "approved"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-f993f871"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-f993f871"
  description: >
    Build the operator-facing update flow on top of the boot-time supervisor:
    check, confirm, stage marker, restart.

scope:
  summary: >
    Add utils/updater.py (pure scan/validate/compare/stage helpers). Add an
    OPTIONS sub-state machine (_options_view: menu | update) with a fourth menu
    button 'Check for updates' and an update sub-view (checking / available /
    none / error / pending). The check runs on the worker pool. Confirming staging
    writes .install-pending and triggers a clean restart via a new app callback.
    Change gtach.service Restart=on-failure to Restart=always so a clean exit
    relaunches.
  affected_components:
    - name: "updater"
      file_path: "src/gtach/utils/updater.py"
      change_type: "add"
    - name: "DisplayManager"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "GTachApplication"
      file_path: "src/gtach/app.py"
      change_type: "modify"
    - name: "gtach.service"
      file_path: "gtach.service"
      change_type: "modify"
  affected_designs:
    - design_ref: "design-gtach-master"
      sections:
        - "Options screen"
        - "Update"
        - "Deployment"
  out_of_scope:
    - "Install execution and rollback (owned by gtach-preflight.sh, 1f4754d3)."
    - "GitHub as an update source."
    - "Dependency changes in a wheel (offline device; manual install required)."
    - "Persisting any update state across reboots."
    - "Changes to the three existing OPTIONS buttons' behaviour."

rational:
  problem_statement: >
    The supervisor can install a staged, marked wheel at boot, but nothing in the
    UI can stage or mark one.
  proposed_solution: >
    A pure helper module performs scan, newer-only tuple comparison against the
    installed version, zip validation, and marker staging. The OPTIONS screen adds
    a fourth button that enters an update sub-view; the check runs asynchronously;
    confirming writes the marker and requests a clean restart, which the supervisor
    converts into an install.
  alternatives_considered:
    - option: "New DisplayMode.UPDATE."
      reason_rejected: "Adds enum and dispatch surface; an OPTIONS sub-state is more contained."
    - option: "Run the check synchronously on the display thread."
      reason_rejected: "Zip validation of a multi-MB wheel would stall the 60 Hz loop."
  benefits:
    - "Operator-driven update without SSH."
    - "Reuses the existing supervisor install/rollback path."
    - "Newer-only comparison prevents accidental downgrade."
  risks:
    - risk: "Restart=always relaunches on any clean exit."
      mitigation: "Desired for a kiosk device; systemctl stop is still honoured; StartLimitBurst bounds loops."
    - risk: "Four buttons crowd the circular display."
      mitigation: "Geometry tuned to four 55px buttons at y=92/157/222/287 within the safe radius."
    - risk: "Worker writes update-state fields read by the display thread."
      mitigation: "Simple attribute assignments (status string, filename, version); atomic under CPython."

technical_details:
  current_behavior: >
    OPTIONS draws three buttons. gtach.service uses Restart=on-failure. No update
    discovery exists in the app.
  proposed_behavior: >
    utils/updater.py: UPDATES_DIR=/opt/gtach/updates, PENDING_MARKER=.install-pending;
    get_installed_version() via importlib.metadata; parse_wheel_version();
    validate_wheel() (zipfile integrity); find_available_update() returns
    (filename, version_str) for the newest valid wheel strictly newer than
    installed, else None; stage_pending(filename) writes the marker.
    DisplayManager: __init__ adds _restart_callback=None, _options_view='menu',
    _update_status='idle', _update_wheel=None, _update_version=None.
    _draw_options_mode dispatches to _draw_options_menu (four buttons) or
    _draw_update_view (state machine). New handlers _on_check_updates (submit
    worker), _run_update_check (worker), _on_confirm_install (stage + restart),
    _on_cancel_update (back to menu). _handle_long_press resets _options_view to
    'menu' on entering OPTIONS.
    app.py: _request_restart() sets self._stop_event; wired as
    self._display._restart_callback at both DisplayManager sites.
    gtach.service: Restart=always.
  implementation_approach: >
    One new module; one OPTIONS refactor into menu/update sub-views; one app
    callback; one unit-file line.
  code_changes:
    - component: "updater"
      file: "src/gtach/utils/updater.py"
      change_summary: "New module with scan/parse/validate/find/stage helpers."
      functions_affected:
        - "get_installed_version"
        - "parse_wheel_version"
        - "validate_wheel"
        - "find_available_update"
        - "stage_pending"
      classes_affected: []
    - component: "DisplayManager"
      file: "src/gtach/display/manager.py"
      change_summary: >
        __init__ adds restart callback and update-state fields. _handle_long_press
        resets _options_view on OPTIONS entry. _draw_options_mode dispatches to
        _draw_options_menu / _draw_update_view. Adds the four handlers.
      functions_affected:
        - "__init__"
        - "_handle_long_press"
        - "_draw_options_mode"
        - "_draw_options_menu"
        - "_draw_update_view"
        - "_on_check_updates"
        - "_run_update_check"
        - "_on_confirm_install"
        - "_on_cancel_update"
      classes_affected:
        - "DisplayManager"
    - component: "GTachApplication"
      file: "src/gtach/app.py"
      change_summary: >
        Add _request_restart(); wire self._display._restart_callback =
        self._request_restart at both DisplayManager creation sites.
      functions_affected:
        - "_request_restart"
        - "_start_setup_mode"
        - "_start_normal_mode"
      classes_affected:
        - "GTachApplication"
    - component: "gtach.service"
      file: "gtach.service"
      change_summary: "Restart=on-failure -> Restart=always."
      functions_affected: []
      classes_affected: []
  data_changes:
    - entity: "/opt/gtach/updates/.install-pending"
      change_type: "data"
      details: "Written by stage_pending(); consumed by gtach-preflight.sh."
  interface_changes:
    - interface: "DisplayManager._restart_callback"
      change_type: "contract"
      details: "Callable[[], None] set by app.py; requests a clean restart."
      backward_compatible: "yes"

dependencies:
  internal:
    - component: "gtach-preflight.sh"
      impact: "Consumes the .install-pending marker written here."
    - component: "importlib.metadata version accessor"
      impact: "Installed-version source (55c879fd established the pattern)."
  external: []
  required_changes:
    - change_ref: "change-1f4754d3"
      relationship: "depends_on"

testing_requirements:
  test_approach: "On-Pi verification with a staged newer wheel."
  test_cases:
    - scenario: "No wheel staged; tap Check for updates."
      expected_result: "Update view shows 'No update found'; Back returns to menu."
    - scenario: "Valid newer wheel staged; tap Check for updates."
      expected_result: "Shows 'Available: v X.Y.Z' with Install/Cancel."
    - scenario: "Tap Install."
      expected_result: ".install-pending written with the wheel filename; device restarts; supervisor installs; new version runs."
    - scenario: "Older or equal wheel staged."
      expected_result: "'No update found' (newer-only)."
    - scenario: "Corrupt wheel staged."
      expected_result: "Rejected by validate_wheel; 'No update found'."
    - scenario: "Cancel from available."
      expected_result: "Returns to options menu; no marker written."
  regression_scope:
    - "Existing three OPTIONS buttons."
    - "OPTIONS long-press return."
    - "systemctl stop gtach still stops the service (Restart=always)."
  validation_criteria:
    - "Four menu buttons render within the circular viewport."
    - "Check runs without stalling the display."
    - "Newer-only comparison correct."
    - "Install writes the marker and restarts; supervisor applies it."
    - "Corrupt/old wheels are not offered."

implementation:
  implementation_steps:
    - step: "Create src/gtach/utils/updater.py."
      owner: "Claude Code"
    - step: "Refactor OPTIONS into menu/update sub-views; add handlers and state."
      owner: "Claude Code"
    - step: "Add _request_restart() and wire _restart_callback in app.py."
      owner: "Claude Code"
    - step: "Change gtach.service Restart to always."
      owner: "Claude Code"
  rollback_procedure: "Revert the four files via git; redeploy."
  deployment_notes: >
    Deploy the new wheel plus the updated gtach.service (scp alongside install.sh)
    and run install.sh, which copies the unit and runs daemon-reload. The new
    Restart= value takes effect on the next unit start.

verification:
  implemented_date: ""
  implemented_by: ""
  verification_date: ""
  verified_by: ""
  test_results: ""
  issues_found: []

traceability:
  related_changes:
    - change_ref: "change-1f4754d3"
      relationship: "depends_on"
  related_issues:
    - issue_ref: "issue-f993f871"
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
