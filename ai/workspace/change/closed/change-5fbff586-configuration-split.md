Created: 2026 October 07

# Change: Single Configuration Store Under GTACH_HOME

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-5fbff586"
  title: "Replace ConfigManager and OBDIIHome with gtach_home() and a ConfigStore over the flat config.yaml; inject it into DisplayManager; strict --validate-config; constant pairing timeouts; acknowledgement state under GTACH_HOME; remove obsolete configuration code"
  date: "2026-10-07"
  author: "William Watson"
  status: "closed"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-5fbff586"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-5fbff586"
  description: "Resolves issue-5fbff586 (audit-36b6ea95 E01, E02, E04, E08, G07; X04 in part)."

scope:
  summary: >
    One configuration file (GTACH_HOME/config.yaml, flat schema, the file
    the Pi already uses), one owner (ConfigStore), one location rule
    (gtach_home()). Everything ConfigManager-related is removed.
  affected_components:
    - name: "gtach_home (replaces OBDIIHome)"
      file_path: "src/gtach/utils/home.py"
      change_type: "refactor"
    - name: "AppConfig, ConfigStore (replace ConfigManager and friends)"
      file_path: "src/gtach/utils/config.py"
      change_type: "refactor"
    - name: "utils package exports"
      file_path: "src/gtach/utils/__init__.py"
      change_type: "modify"
    - name: "DisplayManager config load/save"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "SetupDisplayManager import"
      file_path: "src/gtach/display/setup.py"
      change_type: "modify"
    - name: "GTachApplication"
      file_path: "src/gtach/app.py"
      change_type: "modify"
    - name: "main --validate-config"
      file_path: "src/gtach/main.py"
      change_type: "modify"
    - name: "BluetoothPairing timeouts"
      file_path: "src/gtach/comm/pairing.py"
      change_type: "modify"
    - name: "AcknowledgementStateManager default path"
      file_path: "src/gtach/utils/ack_state.py"
      change_type: "modify"
    - name: "Repository configuration files"
      file_path: "config/"
      change_type: "modify"
    - name: "Tests"
      file_path: "tests/"
      change_type: "modify"
    - name: "CLAUDE.md §3, §9"
      file_path: "CLAUDE.md"
      change_type: "modify"
  affected_designs:
    - design_ref: "design-b4c5d6e7-component_utils_config_manager"
      update_required: "Rewrite after implementation (P04.3)."
    - design_ref: "design-f8a9b0c1-component_utils_home"
      update_required: "Rewrite after implementation (P04.3)."
  out_of_scope:
    - "DeviceStore location and sharing (change-453f0a80)."
    - "Transport selection flags (--transport, --obd-host, --obd-port, --serial-port) stay CLI-only."
    - "engine_profiles.yaml default_profile key (unchanged; the code default remains abarth_595_turismo)."
    - "SplashConfig and load_engine_profile behaviour (kept as they are)."
    - "Installer changes; the service already runs with WorkingDirectory=/opt/gtach and needs no environment variable."

rational:
  problem_statement: "See issue-5fbff586."
  proposed_solution: >
    EDIT A — home.py. Replace the module with:
    `GTACH_HOME_ENV = 'GTACH_HOME'`, `DEFAULT_GTACH_HOME = Path('/opt/gtach')`,
    and `def gtach_home() -> Path` returning Path(os.environ['GTACH_HOME'])
    if set and non-empty, else DEFAULT_GTACH_HOME. No directory is
    created here.

    EDIT B — config.py. Keep load_engine_profile and SplashConfig
    unchanged. Remove ConfigManager, ConfigValidator, ConfigTransaction,
    RWLock, BluetoothConfig, DisplayConfig, SessionConfig,
    SessionManager, OBDConfig and the legacy INI path. Add:
    - `@dataclass AppConfig` with fields mode: str = 'RADIAL',
      palette: str = 'day', engine_profile: str = 'abarth_595_turismo',
      fps_limit: int = 30, touch_long_press: float = 1.0,
      rpm_warning: int = 6500, rpm_danger: int = 7000.
    - `class ConfigStore` with `__init__(self, path: Optional[Path] = None)`
      (default gtach_home() / 'config.yaml'), a threading.Lock, and:
      `load() -> AppConfig` (missing file → defaults, nothing written;
      unreadable or invalid YAML → defaults and logger.error with
      exc_info; known keys read with type coercion, invalid values
      replaced by defaults with a warning; unknown keys retained in an
      internal dict);
      `save(config: AppConfig) -> bool` (merge known fields over the
      retained unknown keys; write to a temporary file in the same
      directory, flush, os.fsync, os.replace; create the directory if
      missing; return False and log on failure);
      `validate() -> List[str]` (error strings for: file unreadable or
      not a mapping; unknown key; wrong type; mode not in {'RADIAL'};
      palette not in {'day', 'night'}; engine_profile not defined in
      engine_profiles.yaml; fps_limit not in 1..60; touch_long_press
      not in 0.1..5.0; an empty list means valid; a missing file is
      valid).
    'DIGITAL' in mode is accepted by load() and mapped to 'RADIAL' as
    DisplayManager does today; validate() reports it as a warning-free
    accepted legacy value (not an error).

    EDIT C — utils/__init__.py exports ConfigStore, AppConfig and
    gtach_home instead of ConfigManager and OBDConfig.

    EDIT D — DisplayManager. Constructor parameter `config_path: str`
    is replaced by `config_store: Optional[ConfigStore] = None`
    (default ConfigStore()). _load_config builds its DisplayConfig from
    config_store.load() with the existing DIGITAL→RADIAL, transient-mode
    and palette rules and engine profile loading. _save_config builds
    an AppConfig from current state and calls config_store.save(). No
    direct file I/O remains in DisplayManager. The first-run "save
    defaults" behaviour is removed: defaults are not written until a
    setting changes.

    EDIT E — app.py. Remove ConfigManager. `__init__` creates
    `self._config_store = ConfigStore(Path(config_path) if config_path else None)`.
    Both DisplayManager constructions pass config_store=self._config_store.
    Remove the discarded load_config() call in start().

    EDIT F — main.py. Delete find_configuration_file (a fourth location
    rule: GTACH_CONFIG, ~/.config/gtach, /etc/gtach); config_file is
    args.config only, None meaning the ConfigStore default.
    --validate-config: errors = ConfigStore(config_file).validate();
    print each error; return 1 if any, else print 'Config valid: <path>'
    and return 0.

    EDIT G — pairing.py. Remove the ConfigManager import, the
    config_manager parameter and the YAML read. Timeouts become class
    constants with the current defaults: DISCOVERY_TIMEOUT_S = 30,
    CONNECTION_TIMEOUT_S = 10, LOOKUP_TIMEOUT_S = 5,
    INITIALIZATION_TIMEOUT_S = 15, OPERATION_TIMEOUT_S = 30, assigned
    to the existing instance attributes in __init__.

    EDIT H — setup.py: remove the unused `from ..utils import ConfigManager`.

    EDIT I — ack_state.py default path: gtach_home() / 'config' /
    'ack_state.yaml'; the directory is created on save, not in __init__.

    EDIT J — repository. Replace config/config.yaml with
    config/config.example.yaml containing the flat schema and default
    values with a header comment (copy to $GTACH_HOME/config.yaml to
    use). config/devices.yaml is handled by change-453f0a80.

    EDIT K — tests. conftest sets GTACH_HOME (not OBDII_HOME) to the
    session temporary directory and drops the ConfigManager reset
    fixture. Delete tests/utils/test_rwlock.py. Add
    tests/test_config_store.py.

    EDIT L — CLAUDE.md: §3 Configuration row 'PyYAML — single flat
    config.yaml under GTACH_HOME (default /opt/gtach)'; §9 utils line
    'ConfigStore, gtach_home, PlatformDetector'. Version History row.
  alternatives_considered:
    - option: "Nested schema with migration."
      reason_rejected: "Decided against on 2026-10-07."
    - option: "~/.config/gtach off the Pi."
      reason_rejected: "Decided against on 2026-10-07; GTACH_HOME is simpler and explicit."
    - option: "Defer dead-code removal to Phase 5."
      reason_rejected: "Decided against on 2026-10-07."
  benefits:
    - "One file decides behaviour; the device needs no migration."
    - "--validate-config can fail."
    - "Development and tests never write into the repository."
    - "About 1,000 lines of unused code removed."
  risks:
    - risk: "The acknowledgement screen is shown once more on the installed Pi."
      mitigation: "Accepted; it is a one-time effect of the path change."
    - risk: "A test or module still imports a removed name."
      mitigation: "pytest and `python -c 'import gtach.app'` must pass; grep for removed names is a success criterion."
    - risk: "Unknown keys in an existing config.yaml are lost on save."
      mitigation: "ConfigStore retains unknown keys and writes them back."

technical_details:
  current_behavior: "Three files, three owners; ConfigManager result discarded."
  proposed_behavior: "GTACH_HOME/config.yaml read and written only by ConfigStore."
  implementation_approach: "Refactor two utility modules; rewire four consumers; update tests."
  code_changes:
    - component: "utils"
      file: "src/gtach/utils/home.py, src/gtach/utils/config.py, src/gtach/utils/__init__.py, src/gtach/utils/ack_state.py"
      change_summary: "EDITS A, B, C, I"
      functions_affected:
        - "gtach_home"
        - "ConfigStore.load"
        - "ConfigStore.save"
        - "ConfigStore.validate"
      classes_affected:
        - "AppConfig"
        - "ConfigStore"
    - component: "consumers"
      file: "src/gtach/display/manager.py, src/gtach/app.py, src/gtach/main.py, src/gtach/comm/pairing.py, src/gtach/display/setup.py"
      change_summary: "EDITS D to H"
      functions_affected:
        - "DisplayManager.__init__"
        - "DisplayManager._load_config"
        - "DisplayManager._save_config"
        - "GTachApplication.__init__"
        - "GTachApplication.start"
        - "main"
        - "find_configuration_file (deleted)"
        - "BluetoothPairing.__init__"
      classes_affected: []
  data_changes:
    - entity: "config.yaml"
      change_type: "schema"
      details: "Flat keys mode, palette, engine_profile, fps_limit, touch_long_press, rpm_warning, rpm_danger; unknown keys preserved. Location GTACH_HOME/config.yaml (unchanged on the Pi)."
  interface_changes:
    - interface: "DisplayManager.__init__"
      change_type: "signature"
      details: "config_path: str replaced by config_store: Optional[ConfigStore]."
      backward_compatible: "no"
    - interface: "BluetoothPairing.__init__"
      change_type: "signature"
      details: "config_manager parameter removed."
      backward_compatible: "no"
    - interface: "gtach.utils exports"
      change_type: "contract"
      details: "ConfigManager and OBDConfig removed; ConfigStore, AppConfig, gtach_home added."
      backward_compatible: "no"

dependencies:
  internal:
    - component: "DeviceStore"
      impact: "Unchanged here; moves under gtach_home() in change-453f0a80."
  external: []
  required_changes: []

testing_requirements:
  test_approach: "Unit tests in tests/test_config_store.py using tmp_path; full suite."
  test_cases:
    - scenario: "gtach_home with GTACH_HOME unset, empty, and set."
      expected_result: "/opt/gtach, /opt/gtach, the set path."
    - scenario: "ConfigStore.load with no file."
      expected_result: "AppConfig defaults; no file created."
    - scenario: "load of the device's file (engine_profile abarth_595_turismo, fps_limit 30, mode RADIAL)."
      expected_result: "Those values."
    - scenario: "load with mode DIGITAL."
      expected_result: "mode 'RADIAL'."
    - scenario: "load with fps_limit 'abc'."
      expected_result: "fps_limit 30; warning logged."
    - scenario: "save then load; file with an unknown key 'foo: 1'."
      expected_result: "Round trip equal; 'foo: 1' still present after save."
    - scenario: "save into a directory that does not exist."
      expected_result: "Directory created; True returned."
    - scenario: "validate on a valid file, a missing file, and files with each invalid case."
      expected_result: "[] for the first two; one error naming the key for each invalid case."
    - scenario: "main() with sys.argv patched to ['gtach', '--validate-config', '--config', <invalid file>]."
      expected_result: "Exit code 1; error printed."
    - scenario: "DisplayManager._load_config/_save_config with a ConfigStore on tmp_path (DisplayManager constructed as existing display tests do, or methods called on a host object)."
      expected_result: "Palette and mode round-trip through the store; no file written by DisplayManager itself."
  regression_scope:
    - "All display and app tests; tests/test_stack_dump_toggle.py; tests/test_pi_reset.py."
    - "Full tests/ suite."
  validation_criteria:
    - "grep -rn 'ConfigManager\\|OBDConfig\\|OBDII_HOME\\|OBDIIHome\\|RWLock\\|ConfigValidator\\|SessionManager' src tests returns nothing (backup modules excluded)."
    - "python -c 'import gtach.app, gtach.main' succeeds."
    - "pytest tests/ passes."

implementation:
  effort_estimate: ""
  implementation_steps:
    - step: "EDITS A to L."
      owner: "tactical"
    - step: "On the Pi: settings still apply; --validate-config behaves; acknowledgement shown once."
      owner: "human"
    - step: "Rewrite design-b4c5d6e7 and design-f8a9b0c1 to match (P04.3)."
      owner: "strategic"
  rollback_procedure: "Revert the commit."
  deployment_notes: >
    No action needed on the Pi: /opt/gtach/config.yaml remains the file
    in use. /root/.local/share/obdii/ is no longer read and may be
    removed by the owner.

verification:
  implemented_date: "2026-10-07"
  implemented_by: "Claude Code"
  verification_date: "2026-10-08"
  verified_by: "William Watson"
  test_results: "Session A (2026-10-07): existing config applied; --validate-config valid, fps_limit 0 rejected (exit 1); acknowledgement shown once after upgrade, then remembered."
  issues_found: []

traceability:
  design_updates:
    - design_ref: "design-b4c5d6e7-component_utils_config_manager"
      sections_updated: ["all (rewritten as version 2.0, ConfigStore)"]
      update_date: "2026-10-07"
    - design_ref: "design-f8a9b0c1-component_utils_home"
      sections_updated: ["all (rewritten as version 2.0, gtach_home)"]
      update_date: "2026-10-07"
  related_changes:
    - change_ref: "change-453f0a80"
      relationship: "related. Implemented after this change."
  related_issues:
    - issue_ref: "issue-5fbff586"
      relationship: "resolves"

notes: "Design decisions recorded in issue-5fbff586 source.description."

version_history:
  - version: "1.0"
    date: "2026-10-07"
    author: "William Watson"
    changes:
      - "Initial change document resolving issue-5fbff586 iteration 1."

  - version: "1.1"
    date: "2026-10-07"
    author: "William Watson"
    changes:
      - "Approved for implementation by William Watson."

  - version: "1.2"
    date: "2026-10-07"
    author: "Claude Code"
    changes:
      - "Implemented in f5ab73a994fe898d521f26fdd41225a53c69f90c."
  - version: "1.3"
    date: "2026-10-08"
    author: "William Watson"
    changes:
      - "Verified on device; closed at audit-36b6ea95 close-out."

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
| 1.0 | 2026-10-07 | Initial change document. Single ConfigStore under GTACH_HOME; obsolete code removed. |
| 1.1 | 2026-10-07 | Approved for implementation. |
| 1.2 | 2026-10-07 | Implemented in f5ab73a994fe898d521f26fdd41225a53c69f90c. |
| 1.3 | 2026-10-08 | Verified on device; closed at audit-36b6ea95 close-out. |

---

Copyright (c) 2026 William Watson. MIT License.
