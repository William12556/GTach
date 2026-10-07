Created: 2026 October 07

# Change: Packaging, Service Hardening and Script Corrections

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-52653cd6"
  title: "Declare and install the touch stack; ERROR on mock fallback on a Pi; harden and bound the service unit; refresh package metadata; single version source; correct deployment scripts; update the audit check script"
  date: "2026-10-07"
  author: "William Watson"
  status: "implemented"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-52653cd6"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-52653cd6"
  description: "Resolves issue-52653cd6 (audit-36b6ea95 G01, G02, G03, G04, G06, G08, E05)."

scope:
  summary: "Edits to pyproject.toml, three source modules and nine bin/ files."
  affected_components:
    - name: "pyproject.toml"
      file_path: "pyproject.toml"
      change_type: "modify"
    - name: "__init__"
      file_path: "src/gtach/__init__.py"
      change_type: "modify"
    - name: "touch_interface"
      file_path: "src/gtach/display/touch_interface.py"
      change_type: "modify"
    - name: "dependencies"
      file_path: "src/gtach/utils/dependencies.py"
      change_type: "modify"
    - name: "bin scripts and unit"
      file_path: "bin/"
      change_type: "modify"
    - name: "CLAUDE.md §3"
      file_path: "CLAUDE.md"
      change_type: "modify"
    - name: "Tests"
      file_path: "tests/test_packaging_and_scripts.py"
      change_type: "add"
  affected_designs: []
  out_of_scope:
    - "Running as a non-root user (G02 full remedy), deferred by decision of 2026-10-07."
    - "Wheel signing or checksums (E06, G09): recorded as trust assumptions in the audit."
    - "bin/vendor/ and bin/pi-install.sh (already installs with [pi])."
    - "Deleting the backup modules (change-cd5ec050)."

rational:
  problem_statement: "See issue-52653cd6."
  proposed_solution: >
    EDIT A — pyproject.toml: pi extra = ["RPi.GPIO>=0.7.1",
    "hyperpixel2r>=0.0.1"] (gpiozero removed); remove click from
    dependencies; description "Retro-styled OBD-II tachometer for the
    Raspberry Pi with an ELM327 adapter"; keywords ["obd2", "elm327",
    "tachometer", "raspberry-pi"]; URLs
    https://github.com/William12556/GTach (Homepage, Repository,
    Documentation …/blob/main/README.md, Bug Tracker …/issues);
    classifiers add Python 3.12 and 3.13; mypy override modules
    ["RPi.*", "hyperpixel2r.*", "bluetooth.*"].

    EDIT B — __init__.py: __version__ from
    importlib.metadata.version('gtach'), falling back to '0+unknown' on
    PackageNotFoundError. Exports unchanged. build.sh no longer rewrites
    __init__.py (the pyproject.toml update stays).

    EDIT C — touch_interface.py: where the mock fallback is selected
    (the 'Falling back to mock implementation' and 'Using mock HyperPixel
    implementation' messages), log at ERROR when
    utils.platform.is_raspberry_pi() is True, otherwise INFO as now.

    EDIT D — dependencies.py (E05): drop the pybluez and requests
    checks; add psutil (required) and hyperpixel2r (optional, Pi only);
    remove the `pip show` subprocess fallback (use importlib.metadata
    only).

    EDIT E — gtach.service: [Unit] StartLimitIntervalSec=120,
    StartLimitBurst=5, add Wants=bluetooth.service; [Service]
    TimeoutStopSec=30, NoNewPrivileges=yes, PrivateTmp=yes,
    ProtectHome=yes, ProtectSystem=full. Comment each directive.

    EDIT F — install.sh: install "${WHEEL_PATH}[pi]" with
    --extra-index-url https://www.piwheels.org/simple/ (as pi-install.sh
    does).

    EDIT G — deploy.sh: copy all files first; then stop the service,
    run install.sh, and reboot; remove the `systemctl start` that
    immediately precedes the reboot.

    EDIT H — pull_logs.sh: copy into a temporary directory with a single
    remote glob '*.log*'; only on success replace the contents of logs/.

    EDIT I — gen_splash.py: font path from --font or the GTACH_SPLASH_FONT
    environment variable, defaulting to the current path; a clear error
    if the file does not exist.

    EDIT J — release.sh: refuse to release unless HEAD is contained in
    origin's default branch (git branch -r --contains HEAD); pass
    --target "$(git rev-parse HEAD)" to gh release create.

    EDIT K — gtach-preflight.sh: after each install_wheel of a new
    wheel, run "$VENV/bin/pip" check; on failure log the output, restore
    the previous wheel as the existing error path does, and remove the
    probation marker.

    EDIT L — gtach-audit-checks.sh: E01 section describes ConfigStore at
    $GTACH_HOME/config.yaml (default /opt/gtach) and DeviceStore at
    /opt/gtach/config/devices.yaml; candidate list reduced to those two
    plus /root/.local/share/obdii (reported as 'legacy, unused').

    EDIT M — CLAUDE.md §3 Hardware row: RPi.GPIO and hyperpixel2r
    (.[pi] extra); Version History row.
  alternatives_considered:
    - option: "Run as a dedicated user."
      reason_rejected: "Deferred; framebuffer, Bluetooth and reboot access need careful design."
  benefits:
    - "Touch works on a fresh install and a missing library is visible."
    - "Bounded stop; rollback no longer exhausts the start limit."
    - "Smaller attack surface for the root service."
    - "One version source; safer deploy, log pull and release."
  risks:
    - risk: "A hardening directive blocks a needed path on the Pi."
      mitigation: "Only /usr, /boot, /efi, /etc and home directories become read-only or hidden; GTach writes only under /opt/gtach. Verify on device; each directive is a single line to remove."
    - risk: "__version__ is '0+unknown' when running from a source tree without installation."
      mitigation: "Development uses pip install -e, which provides metadata."

technical_details:
  current_behavior: "See issue."
  proposed_behavior: "See proposed_solution."
  implementation_approach: "Configuration and script edits; three small source edits."
  code_changes:
    - component: "gtach package"
      file: "src/gtach/__init__.py, src/gtach/display/touch_interface.py, src/gtach/utils/dependencies.py"
      change_summary: "EDITS B, C, D"
      functions_affected: []
      classes_affected: []
  data_changes: []
  interface_changes: []

dependencies:
  internal: []
  external:
    - component: "hyperpixel2r (PyPI)"
      impact: "Now declared in the pi extra; already 0.0.1 on the device."
  required_changes: []

testing_requirements:
  test_approach: "Static tests over the files plus unit tests for EDITS B to D."
  test_cases:
    - scenario: "Parse pyproject.toml (tomllib/tomli or a regex fallback)."
      expected_result: "pi extra contains hyperpixel2r and not gpiozero; dependencies do not contain click."
    - scenario: "gtach.__version__ with importlib.metadata.version patched to raise PackageNotFoundError (reload the module)."
      expected_result: "'0+unknown'."
    - scenario: "Mock fallback with is_raspberry_pi patched True, then False."
      expected_result: "ERROR, then INFO."
    - scenario: "Read bin/gtach.service."
      expected_result: "Contains TimeoutStopSec=30, NoNewPrivileges=yes, PrivateTmp=yes, ProtectHome=yes, ProtectSystem=full, StartLimitBurst=5, Wants=bluetooth.service."
    - scenario: "bash -n on every edited .sh file; python -m py_compile bin/gen_splash.py."
      expected_result: "No errors."
    - scenario: "Read bin/build.sh."
      expected_result: "No write to src/gtach/__init__.py."
  regression_scope:
    - "Full tests/ suite."
  validation_criteria:
    - "pytest tests/ passes."

implementation:
  effort_estimate: ""
  implementation_steps:
    - step: "EDITS A to M and tests."
      owner: "tactical"
    - step: "Deploy; verify touch, security directives, stop time and rollback."
      owner: "human"
  rollback_procedure: "Revert the commit; on the Pi, reinstall the previous unit file."
  deployment_notes: "The unit file is copied by deploy.sh/install.sh; run `systemctl daemon-reload` (install.sh already does this) and verify."

verification:
  implemented_date: "2026-10-07"
  implemented_by: "Claude Code"
  verification_date: ""
  verified_by: ""
  test_results: ""
  issues_found: []

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-cd5ec050"
      relationship: "related"
  related_issues:
    - issue_ref: "issue-52653cd6"
      relationship: "resolves"

notes: ""

version_history:
  - version: "1.0"
    date: "2026-10-07"
    author: "William Watson"
    changes:
      - "Initial change document resolving issue-52653cd6 iteration 1."

  - version: "1.1"
    date: "2026-10-07"
    author: "William Watson"
    changes:
      - "Approved for implementation by William Watson."

  - version: "1.2"
    date: "2026-10-07"
    author: "Claude Code"
    changes:
      - "Implemented in f9273e05eca60a5def61c5ecae60c4b46ba1c035."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t02_change"
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-07 | Initial change document. Packaging, service and scripts. |
| 1.1 | 2026-10-07 | Approved for implementation. |
| 1.2 | 2026-10-07 | Implemented in f9273e05eca60a5def61c5ecae60c4b46ba1c035. |

---

Copyright (c) 2026 William Watson. MIT License.
