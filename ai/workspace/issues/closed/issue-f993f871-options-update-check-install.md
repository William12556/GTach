Created: 2026 June 12

```yaml
issue_info:
  id: "issue-f993f871"
  title: "No in-app path to discover and install a staged wheel update"
  date: "2026-06-12"
  reporter: "William Watson"
  status: "open"
  severity: "medium"
  type: "enhancement"
  iteration: 1
  coupled_docs:
    change_ref: "change-f993f871"
    change_iteration: 1

source:
  origin: "requirement_change"
  test_ref: ""
  description: >
    The boot-time supervisor (gtach-preflight.sh, 1f4754d3) installs a wheel that
    has been staged in /opt/gtach/updates/ and marked via .install-pending, with
    Tier 2 rollback. No in-app affordance exists to check for a staged wheel,
    confirm it, write the marker, and trigger the restart that performs the
    install. This is the operator-facing half of the update feature.

affected_scope:
  components:
    - name: "updater"
      file_path: "src/gtach/utils/updater.py"
    - name: "DisplayManager"
      file_path: "src/gtach/display/manager.py"
    - name: "GTachApplication"
      file_path: "src/gtach/app.py"
    - name: "gtach.service"
      file_path: "gtach.service"
  designs:
    - design_ref: "design-gtach-master"
  version: "0.2.61"

reproduction:
  prerequisites: "Wheel newer than installed staged in /opt/gtach/updates/."
  steps:
    - "Long-press to enter OPTIONS."
    - "Observe: no way to detect or install the staged wheel."
    - "The wheel is only installed if .install-pending is written manually and the device restarted."
  frequency: "always"
  reproducibility_conditions: "Any deployment."
  preconditions: ""
  test_data: ""
  error_output: ""

behavior:
  expected: >
    OPTIONS offers 'Check for updates'. The app scans /opt/gtach/updates/ for a
    valid wheel strictly newer than the installed version (tuple comparison),
    validates its zip integrity, and presents 'Install v X.Y.Z'. Confirming writes
    .install-pending and restarts; the supervisor installs on relaunch.
  actual: >
    No in-app update affordance. The supervisor contract exists but is unreachable
    from the UI.
  impact: >
    Updating requires manual marker creation and restart over SSH, defeating the
    unattended-appliance goal.
  workaround: "Manual: echo <wheel> > /opt/gtach/updates/.install-pending; reboot."

environment:
  python_version: "3.11"
  os: "Debian Linux (Raspberry Pi Zero 2W)"
  dependencies: []
  domain: "domain_1"

analysis:
  root_cause: >
    The in-app half of the update feature was deferred until the supervisor
    (1f4754d3) existed. The supervisor and its contract (drop dir, .install-pending
    marker) are now in place, so the UI can be built on top.
  technical_notes: >
    A pure helper module (utils/updater.py) provides scan, parse, validate,
    find-available (newer-only tuple comparison vs importlib.metadata installed
    version), and stage-pending. The OPTIONS screen gains a sub-state machine
    (_options_view: menu | update). The check runs on thread_manager.worker_pool
    to avoid stalling the 60 Hz display loop. Confirming install writes the marker
    and triggers a clean restart. Because gtach.service used Restart=on-failure, a
    clean exit would not relaunch; the unit is changed to Restart=always so a clean
    exit relaunches and the supervisor performs the install.
  related_issues:
    - issue_ref: "issue-1f4754d3"
      relationship: "depends_on"

resolution:
  assigned_to: "Claude Code"
  target_date: "2026-06-12"
  approach: "See change-f993f871"
  change_ref: "change-f993f871"
  resolved_date: ""
  resolved_by: ""
  fix_description: ""

verification:
  verified_date: ""
  verified_by: ""
  test_results: ""
  closure_notes: ""

prevention:
  preventive_measures: ""
  process_improvements: ""

traceability:
  design_refs:
    - "design-gtach-master"
  change_refs:
    - "change-f993f871"
  test_refs: []

notes: >
  Final item of the update/logging series. Consumes the supervisor contract from
  1f4754d3 and the installed-version accessor from 55c879fd.

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
