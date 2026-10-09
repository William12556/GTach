Created: 2026 October 09

# Prompt: ConfigStore Reads Unknown Keys at Save Time

---

## Table of Contents

- [1. Prompt](<#1. prompt>)
- [2. Version History](<#2. version history>)

---

## 1. Prompt

```yaml
prompt_info:
  id: "prompt-ae65fa10"
  task_type: "debug"
  source_ref: "change-ae65fa10"
  target_profile: "claude_code"
  date: "2026-10-09"
  iteration: 1
  coupled_docs:
    change_ref: "change-ae65fa10"
    change_iteration: 1

context:
  purpose: "Stop ConfigStore.save from dropping unknown config.yaml keys when the store has not loaded."
  integration: "src/gtach/utils/config.py; tests/test_config_store.py."
  knowledge_references:
    - "ai/workspace/issues/issue-ae65fa10-config-store-save-drops-unknown-keys.md"
    - "ai/workspace/change/change-ae65fa10-config-store-save-drops-unknown-keys.md"
  constraints:
    - "File I/O and logging happen outside self._lock (CLAUDE.md §4 rule 8)."
    - "Do not change load() validation, CONFIG_KEYS or the atomic write sequence."
    - "Python 3.9+; PEP 8."

specification:
  description: "save() reads the current file's unknown keys before merging; shared helper for load() and save()."
  requirements:
    functional:
      - "save() on a fresh store preserves unknown keys already in the file."
      - "Keys added to the file after load() are preserved by save()."
      - "Missing file: unknown keys come from the retained set (empty if never loaded)."
      - "Unreadable file or invalid YAML: WARNING logged; retained set used; save proceeds."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Thread-safe: self._unknown read and written under self._lock"
        - "Professional docstrings"
  performance: []

design:
  architecture: "Read before lock; snapshot under lock; write after."
  components:
    - name: "_unknown_keys"
      type: "function"
      purpose: "Module-level: return {k: v for k, v in data.items() if k not in CONFIG_KEYS}."
      interface:
        inputs:
          - name: "data"
            type: "Dict[str, Any]"
            description: "Parsed config mapping."
        outputs:
          type: "Dict[str, Any]"
          description: "Keys not in CONFIG_KEYS."
        raises: []
    - name: "ConfigStore.load"
      type: "function"
      purpose: "Use _unknown_keys; behaviour unchanged."
    - name: "ConfigStore.save"
      type: "function"
      purpose: "Read current unknown keys first."
      logic:
        - "file_unknown = None"
        - "if self.path.exists(): try data = self._read(); if isinstance(data, dict): file_unknown = _unknown_keys(data); except (OSError, yaml.YAMLError) as e: self.logger.warning(f'Cannot read {self.path} before save: {e}; keeping retained unknown keys')"
        - "with self._lock: if file_unknown is not None: self._unknown = file_unknown; data = dict(self._unknown)"
        - "data.update(asdict(config)); write atomically as now"
        - "Update class and save() docstrings: unknown keys are read from the file at save time."

data_schema:
  entities: []

error_handling:
  strategy: "Read failure before save is logged at WARNING and does not abort the save."
  exceptions:
    - exception: "OSError, yaml.YAMLError"
      condition: "Reading the existing file in save()"
      handling: "WARNING; use retained keys"
  logging:
    level: "WARNING"
    format: "Existing logger"

testing:
  unit_tests:
    - scenario: "File with 'foo: 1' plus known keys; new ConfigStore(path); save(AppConfig()) without load()."
      expected: "Reloaded YAML contains foo: 1."
    - scenario: "load(); append 'bar: 2' to the file; save(AppConfig())."
      expected: "bar: 2 preserved."
    - scenario: "No file; save(AppConfig())."
      expected: "File keys equal set(CONFIG_KEYS)."
    - scenario: "File with invalid YAML; save(AppConfig())."
      expected: "Returns True; file has the known keys; a WARNING was logged (caplog)."
  edge_cases:
    - "File is a YAML list: no unknown keys taken from it; save proceeds."
  validation:
    - "pytest tests/ passes."

deliverable:
  format_requirements:
    - "Save code directly to the listed paths."
    - "Run pytest tests/ on completion; report pass/fail counts."
  files:
    - path: "src/gtach/utils/config.py"
      content: "_unknown_keys; load and save edits"
    - path: "tests/test_config_store.py"
      content: "Four regression tests"

success_criteria:
  - "The four regression tests pass."
  - "pytest tests/ passes."

element_registry:
  source: ""
  entries:
    modules:
      - name: "config"
        path: "src/gtach/utils/config.py"
    classes:
      - name: "ConfigStore"
        module: "gtach.utils.config"
    functions:
      - name: "_unknown_keys"
        module: "gtach.utils.config"
        signature: "_unknown_keys(data: Dict[str, Any]) -> Dict[str, Any]"
      - name: "save"
        module: "gtach.utils.config.ConfigStore"
        signature: "save(self, config: AppConfig) -> bool"
    constants: []

notes: "Human verification: none on device."
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-09 | Initial prompt implementing change-ae65fa10 iteration 1. Target profile claude_code. |

---

Copyright (c) 2026 William Watson. MIT License.
