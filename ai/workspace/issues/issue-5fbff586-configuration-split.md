Created: 2026 October 07

# Issue: Configuration Split Across Unrelated Files

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-5fbff586"
  title: "Configuration is split across three files with three owners; the main ConfigManager file is loaded and discarded; --validate-config cannot fail; utils/config.py and utils/home.py carry obsolete code and write into the repository in development"
  date: "2026-10-07"
  reporter: "William Watson"
  status: "open"
  severity: "medium"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-5fbff586"
    change_iteration: 1

source:
  origin: "code_review"
  test_ref: ""
  description: >
    Raised from audit-36b6ea95 findings E01, E02, E04, E08, G07 and X04,
    confirmed on gtach.local on 2026-10-07 (audit Section 6). Design
    decisions by William Watson on 2026-10-07: keep the flat file
    /opt/gtach/config.yaml as the single configuration; resolve
    locations from GTACH_HOME (default /opt/gtach); remove the obsolete
    code in this phase.

affected_scope:
  components:
    - name: "ConfigManager and associated classes"
      file_path: "src/gtach/utils/config.py"
    - name: "OBDIIHome"
      file_path: "src/gtach/utils/home.py"
    - name: "DisplayManager._load_config / _save_config"
      file_path: "src/gtach/display/manager.py"
    - name: "GTachApplication"
      file_path: "src/gtach/app.py"
    - name: "main (--config, --validate-config)"
      file_path: "src/gtach/main.py"
    - name: "BluetoothPairing.__init__"
      file_path: "src/gtach/comm/pairing.py"
    - name: "AcknowledgementStateManager"
      file_path: "src/gtach/utils/ack_state.py"
  designs:
    - "ai/workspace/design/design-b4c5d6e7-component_utils_config_manager.md"
    - "ai/workspace/design/design-f8a9b0c1-component_utils_home.md"
  version: "0.4.3"

reproduction:
  prerequisites: "GTach installed on the Pi."
  steps:
    - "Inspect /root/.local/share/obdii/config/config.yaml, /opt/gtach/config.yaml and /opt/gtach/config/devices.yaml (bin/gtach-audit-checks.sh)."
    - "Run `gtach --validate-config` against an invalid file."
  frequency: "always"
  reproducibility_conditions: "Deterministic."
  test_data: >
    On device 2026-10-07: DisplayManager reads /opt/gtach/config.yaml
    (fps_limit 30, mode RADIAL); ConfigManager's
    /root/.local/share/obdii/config/config.yaml (mode DIGITAL,
    fps_limit 60) is loaded at app.py:134 and discarded; DeviceStore
    uses the CWD-relative config/devices.yaml.

    pairing.py re-parses ConfigManager's file for bluetooth.pairing.*,
    which is defined nowhere, so its defaults always apply.

    main.py --validate-config calls ConfigManager.load_config, which
    logs validation errors and returns defaults on any exception, so the
    command exits 0 for any file (E02).

    utils/config.py holds Bleak-era BluetoothConfig fields, OBDConfig,
    ConfigValidator, SessionManager, ConfigTransaction, legacy INI
    migration and RWLock, used only by ConfigManager (E04). home.py
    treats any path containing 'src/gtach' as development and then
    resolves home to the repository root, so tests and development runs
    write config/, data/, logs/ and cache/ there; its capability probe
    creates directories as a side effect (E08). The tracked
    config/config.yaml and config/devices.yaml are rewritten at runtime
    in development (G07).

    ack_state.py stores acknowledgement state under OBDII_HOME/config.
  error_output: "None."

behavior:
  expected: "One configuration file, one owner, one location rule; a validation command that fails on invalid input."
  actual: "As in test_data. Confirmed in source and on device."
  impact: >
    Edits to config/config.yaml have no effect; maintainers cannot tell
    which file governs behaviour; development runs modify tracked files.
  workaround: "Edit /opt/gtach/config.yaml directly."

environment:
  python_version: "3.9"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies: []
  domain: "domain_1"

analysis:
  root_cause: >
    Configuration grew three owners. ConfigManager's schema predates the
    RFCOMM transport and no longer matches any consumer; DisplayManager
    acquired its own file; DeviceStore uses a working-directory path.
  technical_notes: >
    The flat /opt/gtach/config.yaml is what the device uses, so keeping
    it avoids any migration of display settings.

    Moving acknowledgement state from OBDII_HOME/config to
    GTACH_HOME/config means the acknowledgement screen is shown once
    more after the upgrade on an installed device.

    tests/utils/test_rwlock.py tests RWLock, which has no consumer once
    ConfigManager is removed.
  related_issues:
    - issue_ref: "issue-453f0a80"
      relationship: "related. Shared DeviceStore located under GTACH_HOME."

resolution:
  assigned_to: ""
  target_date: ""
  approach: "See change-5fbff586."
  change_ref: "change-5fbff586"
  resolved_date: ""
  resolved_by: ""
  fix_description: ""

verification:
  verified_date: ""
  verified_by: ""
  test_results: ""
  closure_notes: ""

prevention:
  preventive_measures: "A single configuration module with a validation command that is tested."
  process_improvements: "None."

verification_enhanced:
  verification_steps:
    - "Confirm on device. [DONE: audit Section 6.]"
    - "After the fix: unit tests per change-5fbff586."
    - "After the fix: on the Pi, settings in /opt/gtach/config.yaml (fps_limit, palette, engine_profile) still apply; `gtach --validate-config` exits 0; an invalid value makes it exit 1."
  verification_results: "First step complete."

traceability:
  design_refs:
    - "design-b4c5d6e7-component_utils_config_manager"
    - "design-f8a9b0c1-component_utils_home"
  change_refs:
    - "change-5fbff586"
  test_refs: []

notes: "Audit reference: audit-36b6ea95 E01, E02, E04, E08, G07, X04."

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
      - "Initial issue document from audit-36b6ea95 E01 cluster with design decisions of 2026-10-07."

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
| 1.0 | 2026-10-07 | Initial issue document. Configuration split, unvalidatable, obsolete code. |

---

Copyright (c) 2026 William Watson. MIT License.
