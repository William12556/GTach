Created: 2026 October 07

# Prompt: Single Configuration Store Under GTACH_HOME

---

## Table of Contents

- [1. Prompt](<#1. prompt>)
- [2. Version History](<#2. version history>)

---

## 1. Prompt

```yaml
prompt_info:
  id: "prompt-5fbff586"
  task_type: "refactor"
  source_ref: "change-5fbff586"
  target_profile: "claude_code"
  date: "2026-10-07"
  iteration: 1
  coupled_docs:
    change_ref: "change-5fbff586"
    change_iteration: 1

context:
  purpose: >
    Make GTACH_HOME/config.yaml (flat schema, default /opt/gtach) the
    only configuration file, owned by a new ConfigStore, and remove the
    obsolete ConfigManager stack and OBDII_HOME resolver.
  integration: >
    utils/home.py, utils/config.py, utils/__init__.py, utils/ack_state.py,
    display/manager.py, display/setup.py, app.py, main.py,
    comm/pairing.py, config/, tests/, CLAUDE.md.
  knowledge_references:
    - "ai/workspace/issues/issue-5fbff586-configuration-split.md"
    - "ai/workspace/change/change-5fbff586-configuration-split.md"
    - "CLAUDE.md §4"
  constraints:
    - "CRITICAL: on the Pi the file /opt/gtach/config.yaml, with its current flat keys, must keep producing identical display behaviour (mode, palette, engine_profile, fps_limit, touch_long_press). No migration step."
    - "CRITICAL: nothing in src/ or tests/ may write into the repository working tree; tests use GTACH_HOME pointing at a temporary directory."
    - "Keep load_engine_profile and SplashConfig unchanged in utils/config.py."
    - "Do not change DeviceStore (change-453f0a80)."
    - "Do not change transport selection or its CLI flags."
    - "ConfigStore uses threading.Lock; save is atomic (temporary file in the same directory, flush, os.fsync, os.replace) and never calls out under the lock (CLAUDE.md rule 8)."
    - "Every logger .error/.critical in a broad handler passes exc_info=True."
    - "Do not modify src/gtach/display/manager_backup.py or setup_original_backup.py."
    - "Python 3.9+ compatible. PEP 8. Type hints on public interfaces. Google-style docstrings."

specification:
  description: "Apply EDITS A to L of change-5fbff586."
  requirements:
    functional:
      - "gtach_home() returns $GTACH_HOME if set and non-empty, else /opt/gtach."
      - "ConfigStore.load/save/validate behave as specified in EDIT B, including retention of unknown keys and DIGITAL→RADIAL."
      - "DisplayManager performs no direct configuration file I/O."
      - "--validate-config exits 1 on any validation error and 0 otherwise."
      - "BluetoothPairing uses constant timeouts equal to today's defaults."
      - "Acknowledgement state lives at gtach_home()/config/ack_state.yaml."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Thread-safe if concurrent access"
        - "Comprehensive error handling"
        - "Professional docstrings"
  performance: []

design:
  architecture: "gtach_home() → ConfigStore(path) → AppConfig, injected into DisplayManager by GTachApplication."
  components:
    - name: "EDIT A — utils/home.py"
      type: "module"
      purpose: "Single location rule."
      logic:
        - "Replace the module body with GTACH_HOME_ENV, DEFAULT_GTACH_HOME and gtach_home() as specified; module docstring explains the rule and cites issue-5fbff586."
    - name: "EDIT B — utils/config.py"
      type: "module"
      purpose: "AppConfig and ConfigStore; remove obsolete classes."
      logic:
        - "Delete ConfigManager, ConfigValidator, ConfigTransaction, RWLock, BluetoothConfig, DisplayConfig, SessionConfig, SessionManager, OBDConfig, legacy INI handling and their imports."
        - "Add AppConfig (dataclass, fields and defaults per change) and ConfigStore per EDIT B. Known keys and accepted values are module-level constants. Type coercion: int(), float(), str() with fallback to the default and logger.warning naming the key."
        - "validate() checks engine_profile against the profiles in assets/engine_profiles.yaml (read with the same loader load_engine_profile uses)."
    - name: "EDIT C — utils/__init__.py"
      type: "module"
      purpose: "Exports."
      logic:
        - "Export ConfigStore, AppConfig, gtach_home; remove ConfigManager and OBDConfig."
    - name: "EDIT D — DisplayManager"
      type: "class"
      purpose: "Use the injected store."
      logic:
        - "__init__(self, thread_manager, terminal_restorer=None, config_store: Optional[ConfigStore] = None); `self._config_store = config_store or ConfigStore()`; remove self.config_path."
        - "_load_config: `app = self._config_store.load()`; apply the existing rules for DIGITAL, transient modes, palette name and engine profile to build DisplayConfig(mode=SPLASH, rpm_warning, rpm_danger, fps_limit, touch_long_press, engine_profile, rpm_bands) and _post_splash_mode. Keep the existing error fallback. Remove the first-run save."
        - "_save_config: keep the transient-mode rule; build AppConfig(mode=..., palette=self._palette.name, engine_profile=..., fps_limit=..., touch_long_press=..., rpm_warning=..., rpm_danger=...) and call self._config_store.save()."
        - "Remove YAML imports from manager.py if no longer used."
    - name: "EDIT E — app.py"
      type: "class"
      purpose: "Single store, injected."
      logic:
        - "Replace ConfigManager import and construction with `self._config_store = ConfigStore(Path(config_path) if config_path else None)`."
        - "Pass config_store=self._config_store at both DisplayManager constructions."
        - "Delete `config = self._config_manager.load_config()` in start()."
    - name: "EDIT F — main.py"
      type: "function"
      purpose: "Strict validation; one location rule."
      logic:
        - "Delete find_configuration_file; `config_file = args.config`."
        - "--validate-config per change EDIT F."
    - name: "EDIT G — pairing.py"
      type: "class"
      purpose: "No configuration dependency."
      logic:
        - "Per change EDIT G; keep the 'Pairing timeouts: ...' info log."
    - name: "EDIT H — setup.py"
      type: "module"
      purpose: "Remove unused import."
      logic:
        - "Delete `from ..utils import ConfigManager`."
    - name: "EDIT I — ack_state.py"
      type: "class"
      purpose: "Location under GTACH_HOME."
      logic:
        - "Default path gtach_home() / 'config' / 'ack_state.yaml'; create the parent directory in the save path (not in __init__); update the docstring."
    - name: "EDIT J — repository config"
      type: "module"
      purpose: "No runtime-written tracked files."
      logic:
        - "`git rm config/config.yaml`; add config/config.example.yaml with the seven flat keys at AppConfig defaults and a header comment: copy to $GTACH_HOME/config.yaml (default /opt/gtach/config.yaml); `gtach --validate-config` checks it; Copyright line."
    - name: "EDIT K — tests"
      type: "module"
      purpose: "Isolation and coverage."
      logic:
        - "tests/conftest.py: set os.environ['GTACH_HOME'] (replacing OBDII_HOME) to the session temporary directory; remove the ConfigManager reset fixture."
        - "`git rm tests/utils/test_rwlock.py`."
        - "Add tests/test_config_store.py per change testing_requirements."
    - name: "EDIT L — CLAUDE.md"
      type: "module"
      purpose: "Keep context accurate."
      logic:
        - "§3 Configuration row and §9 utils line per change; Version History row (next minor version, today, 'Configuration: single ConfigStore under GTACH_HOME (change-5fbff586)')."

data_schema:
  entities:
    - name: "config.yaml"
      purpose: "Persisted display settings"
      fields:
        - name: "mode"
          type: "str"
          constraints: "RADIAL (DIGITAL accepted on read, mapped to RADIAL)"
        - name: "palette"
          type: "str"
          constraints: "day | night"
        - name: "engine_profile"
          type: "str"
          constraints: "key of profiles in assets/engine_profiles.yaml"
        - name: "fps_limit"
          type: "int"
          constraints: "1..60, default 30"
        - name: "touch_long_press"
          type: "float"
          constraints: "0.1..5.0, default 1.0"
        - name: "rpm_warning"
          type: "int"
          constraints: "default 6500"
        - name: "rpm_danger"
          type: "int"
          constraints: "default 7000"

error_handling:
  strategy: "Configuration problems never prevent startup; defaults apply and the problem is logged."
  exceptions:
    - exception: "OSError, yaml.YAMLError"
      condition: "File unreadable, invalid YAML, or save failure"
      handling: "logger.error(..., exc_info=True); defaults on load; False on save"
  logging:
    level: "WARNING for invalid values, ERROR for I/O failures"
    format: "Unchanged"

testing:
  unit_tests:
    - scenario: "As listed in change-5fbff586 testing_requirements.test_cases."
      expected: "As listed there."
  edge_cases:
    - "config.yaml that is a YAML list, not a mapping: load returns defaults; validate reports one error."
    - "save when the existing file holds only unknown keys: they are preserved."
  validation:
    - "python -c 'import gtach.app, gtach.main'"
    - "pytest tests/ passes."

deliverable:
  format_requirements:
    - "Edit in place; use git rm for removed files."
  files:
    - path: "src/gtach/utils/home.py"
      content: "EDIT A"
    - path: "src/gtach/utils/config.py"
      content: "EDIT B"
    - path: "src/gtach/utils/__init__.py"
      content: "EDIT C"
    - path: "src/gtach/display/manager.py"
      content: "EDIT D"
    - path: "src/gtach/app.py"
      content: "EDIT E"
    - path: "src/gtach/main.py"
      content: "EDIT F"
    - path: "src/gtach/comm/pairing.py"
      content: "EDIT G"
    - path: "src/gtach/display/setup.py"
      content: "EDIT H"
    - path: "src/gtach/utils/ack_state.py"
      content: "EDIT I"
    - path: "config/config.example.yaml"
      content: "EDIT J"
    - path: "tests/conftest.py"
      content: "EDIT K"
    - path: "tests/test_config_store.py"
      content: "EDIT K"
    - path: "CLAUDE.md"
      content: "EDIT L"

success_criteria:
  - "grep -rn 'ConfigManager\\|OBDConfig\\|OBDII_HOME\\|OBDIIHome\\|RWLock\\|ConfigValidator\\|SessionManager\\|find_configuration_file' src tests (excluding manager_backup.py and setup_original_backup.py) returns nothing."
  - "DisplayManager contains no open(), yaml.dump or yaml.safe_load for configuration."
  - "config/config.yaml is removed; config/config.example.yaml exists."
  - "tests/utils/test_rwlock.py is removed."
  - "After a full pytest run, `git status --porcelain` shows no new or modified files outside the commit."
  - "python -c 'import gtach.app, gtach.main' succeeds."
  - "pytest tests/ passes."

element_registry:
  source: ""
  entries:
    modules:
      - name: "home"
        path: "src/gtach/utils/home.py"
      - name: "config"
        path: "src/gtach/utils/config.py"
    classes:
      - name: "AppConfig"
        module: "gtach.utils.config"
      - name: "ConfigStore"
        module: "gtach.utils.config"
    functions:
      - name: "gtach_home"
        module: "gtach.utils.home"
        signature: "() -> Path"
      - name: "ConfigStore.load"
        module: "gtach.utils.config"
        signature: "(self) -> AppConfig"
      - name: "ConfigStore.save"
        module: "gtach.utils.config"
        signature: "(self, config: AppConfig) -> bool"
      - name: "ConfigStore.validate"
        module: "gtach.utils.config"
        signature: "(self) -> List[str]"
    constants:
      - name: "DEFAULT_GTACH_HOME"
        module: "gtach.utils.home"
        type: "Path"

notes: >
  Human verification on the Pi after deployment: display settings from
  /opt/gtach/config.yaml still apply; `/opt/gtach/venv/bin/gtach
  --validate-config` prints 'Config valid'; editing fps_limit to 0 makes
  it exit 1 (restore afterwards); the acknowledgement screen appears
  once after the upgrade and is then remembered.
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-07 | Initial prompt implementing change-5fbff586 iteration 1. Target profile claude_code. |
| 1.1 | 2026-10-07 | Implemented; closed |

---

Copyright (c) 2026 William Watson. MIT License.
