Created: 2026 June 11

```yaml
issue_info:
  id: "issue-1f4754d3"
  title: "GTach does not start on boot and has no controlled on-device update path"
  date: "2026-06-11"
  reporter: "William Watson"
  status: "open"
  severity: "medium"
  type: "enhancement"
  iteration: 1
  coupled_docs:
    change_ref: "change-1f4754d3"
    change_iteration: 1

source:
  origin: "requirement_change"
  test_ref: ""
  description: >
    GTach is launched manually on the Pi (gtach --debug | tee ...). It does not
    start automatically on boot, and there is no supervised mechanism to install
    a newer wheel and recover if that wheel fails. A running process cannot
    safely reinstall itself, so installation must occur before launch, performed
    by a boot-time supervisor.

affected_scope:
  components:
    - name: "gtach.service"
      file_path: "gtach.service"
    - name: "gtach-preflight.sh"
      file_path: "gtach-preflight.sh"
    - name: "install.sh"
      file_path: "install.sh"
    - name: "GTachApplication"
      file_path: "src/gtach/app.py"
  designs:
    - design_ref: "design-gtach-master"
  version: "0.2.61"

reproduction:
  prerequisites: "Pi Zero 2W with gtach installed at /opt/gtach."
  steps:
    - "Reboot the Pi."
    - "Observe GTach does not launch; manual shell invocation is required."
    - "Stage a newer wheel — no on-device path applies it before launch."
  frequency: "always"
  reproducibility_conditions: "Any boot of the deployed device."
  preconditions: ""
  test_data: ""
  error_output: ""

behavior:
  expected: >
    GTach starts automatically on boot. A wheel staged in /opt/gtach/updates/
    and marked for install is installed by a boot-time supervisor before launch.
    A wheel that fails to start is rolled back to the previous known-good wheel.
  actual: >
    No auto-start. No supervised install. No rollback. Updates are applied
    manually via install.sh and the process is launched by hand.
  impact: >
    Device is unusable as an unattended in-vehicle appliance and an in-app
    update feature cannot function without the boot-time install path.
  workaround: "Manual SSH launch and manual install.sh invocation."

environment:
  python_version: "3.11"
  os: "Debian Linux (Raspberry Pi Zero 2W)"
  dependencies: []
  domain: "domain_1"

analysis:
  root_cause: >
    No systemd unit exists for gtach (install.sh references enabling one, but the
    unit file is not tracked or installed). No supervisor performs install-at-boot
    or rollback. Self-reinstallation by the running process is unsafe, so the
    install step must be owned by a pre-start hook.
  technical_notes: >
    Resolution introduces a systemd unit, a boot-time preflight script (rollback
    plus pending-install), an install.sh extension to register them, and a single
    application hook that clears a probation marker on healthy startup so the
    supervisor can detect a crash-looping update and revert it.
  related_issues: []

resolution:
  assigned_to: "Claude Code"
  target_date: "2026-06-11"
  approach: "See change-1f4754d3"
  change_ref: "change-1f4754d3"
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
    Keep the install/launch supervisor separate from the application; never
    perform self-reinstallation from the running process.
  process_improvements: ""

traceability:
  design_refs:
    - "design-gtach-master"
  change_refs:
    - "change-1f4754d3"
  test_refs: []

notes: >
  First of a sequence. The OPTIONS in-app "Check for updates / Install" unit
  depends on the boot-time install path delivered here and will follow as a
  separate triple.

version_history:
  - version: "1.0"
    date: "2026-06-11"
    author: "William Watson"
    changes:
      - "Initial issue document."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t03_issue"
```
