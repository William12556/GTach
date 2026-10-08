Created: 2026 October 07

# Issue: Packaging, Service Unit and Deployment Script Defects

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-52653cd6"
  title: "Touch library not declared or installed by deploy.sh; mock fallback silent on a Pi; service unit unhardened, without stop timeout, with a tight start limit; stale package metadata and duplicated version; deployment script defects; audit check script outdated"
  date: "2026-10-07"
  reporter: "William Watson"
  status: "closed"
  severity: "medium"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-52653cd6"
    change_iteration: 1

source:
  origin: "code_review"
  test_ref: ""
  description: >
    Raised from audit-36b6ea95 findings G01 (medium), G02 (medium,
    hardening directives only, as planned), G03, G04, G06 (version
    duplication; backup-module packaging is resolved by their deletion in
    change-cd5ec050), G08, E05 (low), and the outdated
    bin/gtach-audit-checks.sh reported in report-5fbff586.

affected_scope:
  components:
    - name: "Package metadata and extras"
      file_path: "pyproject.toml"
    - name: "Package version"
      file_path: "src/gtach/__init__.py"
    - name: "Touch mock fallback logging"
      file_path: "src/gtach/display/touch_interface.py"
    - name: "Dependency validator"
      file_path: "src/gtach/utils/dependencies.py"
    - name: "Service unit and scripts"
      file_path: "bin/gtach.service, bin/install.sh, bin/build.sh, bin/deploy.sh, bin/pull_logs.sh, bin/release.sh, bin/gen_splash.py, bin/gtach-preflight.sh, bin/gtach-audit-checks.sh"
  designs: []
  version: "0.4.3"

reproduction:
  prerequisites: "Repository and a Pi."
  steps:
    - "Inspect the listed files; see test_data."
  frequency: "always"
  reproducibility_conditions: "Deterministic from source."
  test_data: >
    pyproject: pi extra lacks hyperpixel2r and declares unused gpiozero;
    click is declared and never imported; description, keywords and URLs
    are stale; mypy overrides name unused gpiozero/obd modules.
    install.sh installs the wheel without [pi]. touch_interface.py logs
    the mock fallback at INFO even on a Pi. dependencies.py checks
    pybluez and requests (undeclared) and not psutil or hyperpixel2r,
    and shells out to `pip show`.
    gtach.service: no NoNewPrivileges/PrivateTmp/ProtectHome/
    ProtectSystem; no TimeoutStopSec (90 s default); StartLimitBurst=3
    in 60 s while update rollback uses three starts; After= without
    Wants=bluetooth.service.
    __init__.py hard-codes __version__; build.sh rewrites __init__.py
    wholesale to keep it in step with pyproject.
    deploy.sh stops the service before copying files under set -e, then
    starts it immediately before rebooting. pull_logs.sh deletes local
    logs before an scp whose '*.log.*' glob fails when no rotated log
    exists. gen_splash.py hard-codes a macOS FreeCAD font path.
    release.sh lets gh create the tag on the remote default branch.
    gtach-preflight.sh installs with --no-deps, so an update needing a
    new dependency installs and then fails at import.
    gtach-audit-checks.sh still describes ConfigManager and OBDII_HOME
    locations.
  error_output: "None."

behavior:
  expected: "Correct dependencies, a hardened and bounded service, one version source, safe scripts."
  actual: "As in test_data."
  impact: "Silent loss of touch on a fresh install; long stops; unit failure after a rollback; a stopped service after a failed deploy; lost logs; mis-tagged releases."
  workaround: "Manual care during deployment."

environment:
  python_version: "3.9"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies: []
  domain: "domain_1"

analysis:
  root_cause: "Packaging and scripts were not updated as the application changed."
  technical_notes: >
    The service runs as root and needs /dev/fb0, Bluetooth sockets,
    /opt/gtach writes (configuration, logs, updates, the venv) and
    /sbin/reboot. NoNewPrivileges, PrivateTmp, ProtectHome and
    ProtectSystem=full are compatible with all of these; on-device
    verification is still required.
  related_issues:
    - issue_ref: "issue-cd5ec050"
      relationship: "related. Deletes the backup modules (G06 packaging part)."

resolution:
  assigned_to: ""
  target_date: ""
  approach: "See change-52653cd6."
  change_ref: "change-52653cd6"
  resolved_date: "2026-10-08"
  resolved_by: "change-52653cd6"
  fix_description: "The pi extra now installs RPi.GPIO and hyperpixel2r (click and gpiozero removed) and install.sh uses it, the mock touch fallback logs ERROR on a Pi, gtach.service gains TimeoutStopSec, wider start limits, Wants=bluetooth.service and four hardening directives, pyproject.toml is the single version source, metadata and dependency checks are current, and deploy, pull_logs, gen_splash, release, preflight and the audit check script are corrected (commit f9273e05eca60a5def61c5ecae60c4b46ba1c035)."

verification:
  verified_date: "2026-10-08"
  verified_by: "William Watson"
  test_results: "Session A/B (2026-10-07): deploy, service start and touch; unit directives as expected (C8a); stop 0.4-3.0 s; no mock fallback (C7c); [pi] extra installed; pip check clean."
  closure_notes: "Closed at audit-36b6ea95 close-out after on-device verification."

prevention:
  preventive_measures: "None beyond the change."
  process_improvements: "Review bin/ and pyproject.toml with every dependency or path change."

verification_enhanced:
  verification_steps:
    - "Confirm from source. [DONE.]"
    - "After the fix: deploy with bin/deploy.sh; service starts; touch works; `systemd-analyze security gtach` shows the four directives; `systemctl stop gtach` completes within 30 s."
  verification_results: "All verification steps complete; see verification.test_results."

traceability:
  design_refs: []
  change_refs:
    - "change-52653cd6"
  test_refs: []

notes: "Audit reference: audit-36b6ea95 G01, G02, G03, G04, G06, G08, E05."

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
      - "Initial issue document for Phase 5 packaging and service."

  - version: "1.1"
    date: "2026-10-07"
    author: "Claude Code"
    changes:
      - "Fix implemented in f9273e05eca60a5def61c5ecae60c4b46ba1c035; awaiting on-device verification."
  - version: "1.2"
    date: "2026-10-08"
    author: "William Watson"
    changes:
      - "On-device verification complete; closed at audit-36b6ea95 close-out."

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
| 1.0 | 2026-10-07 | Initial issue document. Packaging, service and script defects. |
| 1.1 | 2026-10-07 | Fix implemented in f9273e05eca60a5def61c5ecae60c4b46ba1c035; awaiting on-device verification. |
| 1.2 | 2026-10-08 | On-device verification complete; closed at audit-36b6ea95 close-out. |

---

Copyright (c) 2026 William Watson. MIT License.
