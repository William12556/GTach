# Prompt: Comm Transport Abstraction — Entry Point and Cleanup (Revised)

Created: 2026 March 24

---

## Table of Contents

- [1.0 Prompt Information](<#1.0 prompt information>)
- [2.0 Context](<#2.0 context>)
- [3.0 Specification](<#3.0 specification>)
- [4.0 Design](<#4.0 design>)
- [5.0 Deliverables](<#5.0 deliverables>)
- [6.0 Success Criteria](<#6.0 success criteria>)
- [7.0 Element Registry](<#7.0 element registry>)
- [8.0 Tactical Brief](<#8.0 tactical brief>)
- [Version History](<#version history>)

---

## 1.0 Prompt Information

```yaml
prompt_info:
  id: "prompt-e1f2a3b4"
  task_type: "code_generation"
  source_ref: "change-e1f2a3b4-comm-transport-abstraction.md"
  date: "2026-03-24"
  priority: "high"
  iteration: 2
  sequence: "3 of 3"
  coupled_docs:
    change_ref: "change-e1f2a3b4"
    change_iteration: 1

  prerequisite: >
    prompt-e1f2a3b4-1 and prompt-e1f2a3b4-2 must be complete.
    transport.py, rfcomm.py, tcp_transport.py, serial_transport.py must exist.
    obd.py, models.py, device_store.py, __init__.py must be updated.

tactical_execution:
  mode: "ralph_loop"
  worker_model: "Devstral-Small-2-24B-Instruct-2512"
  reviewer_model: "Devstral-Small-2-24B-Instruct-2512"
  max_iterations: 20
  boundary_conditions:
    token_budget: 50000
    time_limit_minutes: 30

notes: >
  Context window: 393,216 tokens (Devstral-Small-2-24B-Instruct-2512).
  max_iterations: 5 — outer Ralph Loop cycles (worker+reviewer pairs).
  phase_max_iterations: 50 (config.yaml) — inner tool-call iterations per phase.
  Iteration 2: app.py partially complete from prior run. See §2.0 for current state.
```

---

## 2.0 Context

```yaml
context:
  purpose: >
    Complete the transport abstraction change. app.py is partially updated
    from a prior run — two defects remain. Remaining files not yet touched:
    main.py, pyproject.toml, watchdog.py, bluetooth.py.

  app_py_current_state: >
    DONE: imports updated, __init__ args parameter, _start_normal_mode transport wiring,
    get_primary_device() setup detection.
    DEFECT 1 (shutdown): hasattr(self,'_bluetooth') block still present — replace with
      hasattr(self,'_transport') calling self._transport.disconnect().
    DEFECT 2 (_start_normal_mode): reconnect thread target is self._obd.reconnect_indefinitely
      — must be self._transport.reconnect_indefinitely.

  project_root: "/Users/williamwatson/Documents/GitHub/GTach"
  entry_point: "gtach.main:main (pyproject.toml [project.scripts])"
```

---

## 3.0 Specification

```yaml
specification:
  description: >
    Fix 2 defects in app.py, rewrite main.py, patch pyproject.toml,
    patch watchdog.py (one line), delete bluetooth.py.

  requirements:
    functional:

      - id: "app.py — defect fixes only"
        changes:
          - "DEFECT 1 shutdown(): replace the '_bluetooth' hasattr block:"
          - "  FROM: if hasattr(self, '_bluetooth'): self._bluetooth.stop()"
          - "  TO:   if hasattr(self, '_transport'): self._transport.disconnect()"
          - "DEFECT 2 _start_normal_mode(): fix reconnect thread target:"
          - "  FROM: target=self._obd.reconnect_indefinitely"
          - "  TO:   target=self._transport.reconnect_indefinitely"
          - "No other changes to app.py"

      - id: "main.py — full rewrite"
        changes:
          - "REWRITE to ~80-100 lines total"
          - "Keep: --config, --debug, --version='0.2.0', --validate-config, --validate-dependencies"
          - "ADD: --macos (store_true), --transport (choices=['tcp','serial','rfcomm']), --obd-host (default='localhost'), --obd-port (int, default=35000), --serial-port (default=None)"
          - "REMOVE: --service, --test-hardware, --validate-logging, --logging-health-check and all their handler functions"
          - "setup_logging(debug): if debug: basicConfig(DEBUG, StreamHandler); else: addHandler(NullHandler()) — nothing else"
          - "main(): GTachApplication(config_file, args.debug, args)"

      - id: "pyproject.toml"
        changes:
          - "version: '0.1.1' -> '0.2.0'"
          - "dependencies: add 'pyserial>=3.5'; remove 'bleak' if present"
          - "No other changes"

      - id: "watchdog.py — one line only"
        changes:
          - "self.critical_threads = {'display', 'transport', 'main'}"
          - "No other changes"

      - id: "bluetooth.py"
        changes:
          - "Overwrite with single line: # Removed — replaced by transport abstraction"
```

---

## 4.0 Design

### 4.1 app.py — two surgical edits

```python
# DEFECT 1: In shutdown(), replace:
#   if hasattr(self, '_bluetooth'):
#       self._bluetooth.stop()
# WITH:
#   if hasattr(self, '_transport'):
#       self._transport.disconnect()

# DEFECT 2: In _start_normal_mode(), replace:
#   transport_thread = threading.Thread(target=self._obd.reconnect_indefinitely, ...)
# WITH:
#   transport_thread = threading.Thread(target=self._transport.reconnect_indefinitely, ...)
```

### 4.2 main.py — complete replacement

```python
#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""GTach application entry point."""

import sys
import logging
import argparse
from pathlib import Path
from typing import Optional


def setup_logging(debug: bool = False) -> None:
    if debug:
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s %(name)s %(levelname)s %(message)s'
        )
    else:
        logging.getLogger().addHandler(logging.NullHandler())


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='GTach — real-time engine tachometer')
    parser.add_argument('--config', type=Path)
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--version', action='version', version='GTach 0.2.0')
    parser.add_argument('--validate-config', action='store_true')
    parser.add_argument('--validate-dependencies', action='store_true')
    parser.add_argument('--macos', action='store_true')
    parser.add_argument('--transport', choices=['tcp', 'serial', 'rfcomm'], default=None)
    parser.add_argument('--obd-host', default='localhost')
    parser.add_argument('--obd-port', type=int, default=35000)
    parser.add_argument('--serial-port', default=None)
    return parser.parse_args()


def find_configuration_file() -> Optional[Path]:
    import os
    env = os.getenv('GTACH_CONFIG')
    if env and Path(env).exists():
        return Path(env)
    user = Path.home() / '.config' / 'gtach' / 'config.yaml'
    if user.exists():
        return user
    system = Path('/etc/gtach/config.yaml')
    if system.exists():
        return system
    return None


def main() -> int:
    args = parse_arguments()
    config_file = args.config or find_configuration_file()
    setup_logging(args.debug)

    if args.validate_dependencies:
        from .utils import validate_dependencies
        v = validate_dependencies(debug=args.debug)
        v.print_report(show_successful=args.debug)
        return 0 if v.can_start_application() else 1

    if args.validate_config:
        try:
            from .utils.config import ConfigManager
            ConfigManager(config_file).load_config()
            return 0
        except Exception as e:
            print(f'Config invalid: {e}')
            return 1

    from .app import GTachApplication
    app = GTachApplication(config_file, args.debug, args)
    app.run()
    return 0


if __name__ == '__main__':
    sys.exit(main())
```

---

## 5.0 Deliverables

```yaml
deliverable:
  format_requirements:
    - "app.py: two surgical edits using edit tool"
    - "main.py: full file replacement using write tool"
    - "pyproject.toml: two targeted edits using edit tool"
    - "watchdog.py: one targeted edit using edit tool"
    - "bluetooth.py: overwrite with stub using write tool"

  files:
    - path: "src/gtach/app.py"
      action: "edit (2 lines)"
    - path: "src/gtach/main.py"
      action: "write (full replacement)"
    - path: "pyproject.toml"
      action: "edit (2 changes)"
    - path: "src/gtach/core/watchdog.py"
      action: "edit (1 line)"
    - path: "src/gtach/comm/bluetooth.py"
      action: "write (stub)"
```

---

## 6.0 Success Criteria

```yaml
success_criteria:
  - "app.py: shutdown() contains hasattr(self,'_transport') calling self._transport.disconnect(); no _bluetooth reference"
  - "app.py: _start_normal_mode() reconnect thread target is self._transport.reconnect_indefinitely"
  - "main.py: total line count 80-100; --macos, --transport, --obd-host, --obd-port, --serial-port present"
  - "main.py: --service, --test-hardware, --validate-logging, --logging-health-check absent"
  - "main.py: setup_logging contains only basicConfig or NullHandler"
  - "main.py: version string '0.2.0'"
  - "pyproject.toml: version '0.2.0'; pyserial>=3.5 in dependencies"
  - "watchdog.py: self.critical_threads = {'display', 'transport', 'main'}"
  - "bluetooth.py: contains only stub comment"
  - "python -c 'from gtach.main import main' imports without error"
```

---

## 7.0 Element Registry

```yaml
element_registry:
  modules:
    - name: "gtach.app"
      path: "src/gtach/app.py"
    - name: "gtach.main"
      path: "src/gtach/main.py"

  classes:
    - name: "GTachApplication"
      module: "gtach.app"
      base_classes: []

  functions:
    - name: "main"
      module: "gtach.main"
      signature: "main() -> int"
    - name: "parse_arguments"
      module: "gtach.main"
      signature: "parse_arguments() -> argparse.Namespace"
    - name: "setup_logging"
      module: "gtach.main"
      signature: "setup_logging(debug: bool = False) -> None"
    - name: "_start_normal_mode"
      module: "gtach.app"
      signature: "_start_normal_mode(self) -> None"
```

---

## 8.0 Tactical Brief

```yaml
tactical_brief: |
  TASK: Fix 2 defects in app.py, rewrite main.py, patch 2 files, stub bluetooth.py.
  Prerequisites: prompts 1 and 2 complete. app.py imports and _start_normal_mode are done.

  FILE 1: src/gtach/app.py — TWO EDITS ONLY
  Read the file first. Make both edits in a single edit call with two entries.
  EDIT A — shutdown(): replace
    if hasattr(self, '_bluetooth'):
        self._bluetooth.stop()
  WITH
    if hasattr(self, '_transport'):
        self._transport.disconnect()
  EDIT B — _start_normal_mode(): replace
    target=self._obd.reconnect_indefinitely
  WITH
    target=self._transport.reconnect_indefinitely

  FILE 2: src/gtach/main.py — FULL REPLACEMENT via write tool
  Do NOT edit. Write the entire file at once:
  - Header: MIT license block + module docstring
  - setup_logging(debug): if debug: basicConfig(DEBUG); else: NullHandler()
  - parse_arguments(): --config, --debug, --version='0.2.0', --validate-config,
    --validate-dependencies, --macos, --transport (choices tcp/serial/rfcomm),
    --obd-host (default localhost), --obd-port (int default 35000), --serial-port
  - find_configuration_file(): check GTACH_CONFIG env, ~/.config/gtach/config.yaml, /etc/gtach/config.yaml
  - main(): setup_logging; validate_dependencies if flag; validate_config if flag;
    GTachApplication(config_file, args.debug, args).run()
  - if __name__=='__main__': sys.exit(main())
  Target: 80-100 lines total.

  FILE 3: pyproject.toml — ONE edit call, two entries
  ENTRY A: version = "0.1.1"  ->  version = "0.2.0"
  ENTRY B: dependencies block — add 'pyserial>=3.5' (remove 'bleak' if present)

  FILE 4: src/gtach/core/watchdog.py — ONE edit
  Replace: self.critical_threads = {'display', 'bluetooth', 'main'}
  With:    self.critical_threads = {'display', 'transport', 'main'}

  FILE 5: src/gtach/comm/bluetooth.py — write tool
  Overwrite entire file with single line:
  # Removed — replaced by transport abstraction

  SUCCESS:
  - app.py: _bluetooth absent from shutdown(); _transport.reconnect_indefinitely in thread target
  - main.py: 80-100 lines; version 0.2.0; transport flags present; no --service or --test-hardware
  - pyproject.toml: version 0.2.0; pyserial present
  - watchdog.py: critical_threads has 'transport' not 'bluetooth'
  - bluetooth.py: stub only
```

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-03-24 | William Watson | Initial prompt |
| 2.0 | 2026-03-27 | William Watson | Narrowed to remaining work after partial prior run; fixed defect descriptions; explicit write vs edit guidance in brief |

---

Copyright (c) 2025 William Watson. This work is licensed under the MIT License.
