# Prompt: Comm Transport Abstraction — Entry Point and Cleanup

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
  iteration: 1
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
  max_iterations: 20 — orchestrator uses this for both outer loop and inner phase.
```

---

## 2.0 Context

```yaml
context:
  purpose: >
    Update application entry point, configuration, and supporting files to
    complete the transport abstraction change. Wire select_transport() into
    GTachApplication. Strip OOS dead code from main.py. Update pyproject.toml
    dependencies. Fix watchdog critical thread name. Delete bluetooth.py.

  integration: >
    Prompts 1 and 2 created and updated comm domain files. This prompt
    completes the change by updating the application layer and removing
    the now-defunct bluetooth.py.

  project_root: "/Users/williamwatson/Documents/GitHub/GTach"
  entry_point: "gtach.main:main (pyproject.toml [project.scripts])"
```

---

## 3.0 Specification

```yaml
specification:
  description: >
    Modify four files and delete one:
      1. src/gtach/app.py          — wire select_transport(); fix setup detection; update shutdown
      2. src/gtach/main.py         — remove OOS dead code; add new CLI flags; simplify logging
      3. pyproject.toml            — swap bleak for pyserial; bump version to 0.2.0
      4. src/gtach/core/watchdog.py — 'bluetooth' -> 'transport' in critical_threads
      DELETE: src/gtach/comm/bluetooth.py

  requirements:
    functional:

      - id: "app.py"
        changes:
          - "Remove: from .comm import BluetoothManager"
          - "Add: from .comm import select_transport; from .utils.platform import get_platform_type"
          - "GTachApplication.__init__: add 'args' parameter (argparse.Namespace, default None)"
          - "Store self._args = args or argparse.Namespace()"
          - "Remove self._bluetooth = BluetoothManager(...) line"
          - "_start_normal_mode(): add transport instantiation before OBDProtocol:"
          - "  platform_type = get_platform_type()"
          - "  self._transport = select_transport(platform_type, self._args)"
          - "  self._obd = OBDProtocol(self._transport, self._thread_manager)"
          - "  self._transport.reconnect_indefinitely called via threading.Thread or directly in OBDProtocol loop — OBDProtocol already handles waiting; no explicit reconnect call needed in app"
          - "Setup mode detection: replace self._device_store.is_setup_complete() with self._device_store.get_primary_device() is None"
          - "shutdown(): replace self._bluetooth.stop() with self._transport.disconnect() wrapped in hasattr check"
          - "import argparse at top of file"

      - id: "main.py"
        changes:
          - "REWRITE parse_arguments(): keep --config, --debug, --version ('0.2.0'), --validate-config, --validate-dependencies"
          - "ADD to parse_arguments(): --macos (store_true), --transport (choices=['tcp','serial','rfcomm'], default=None), --obd-host (default='localhost'), --obd-port (type=int, default=35000), --serial-port (default=None)"
          - "REMOVE from parse_arguments(): --service, --test-hardware, --validate-logging, --logging-health-check"
          - "SIMPLIFY setup_logging(debug): replace entire session/validation machinery with basicConfig call — if debug: level=DEBUG, handlers=[StreamHandler]; else: level=WARNING, handlers=[NullHandler()]. That is all."
          - "REMOVE all functions: validate_logging_configuration, test_logging_functionality, perform_logging_health_check, test_logging_thread_safety, create_logging_fallback_handler, setup_logging_with_validation, print_logging_validation_report, test_hardware"
          - "main(): remove --service, --test-hardware, --validate-logging, --logging-health-check handling; pass args to GTachApplication: app = GTachApplication(config_file, args.debug, args)"
          - "GTachApplication import and instantiation: pass args as third positional argument"
          - "Result: ~80-100 lines total"

      - id: "pyproject.toml"
        changes:
          - "version: '0.1.1' -> '0.2.0'"
          - "dependencies: remove 'bleak' if present; add 'pyserial>=3.5'"
          - "No other changes"

      - id: "watchdog.py"
        changes:
          - "critical_threads: replace 'bluetooth' with 'transport' in the set literal"
          - "One line change only: self.critical_threads = {'display', 'transport', 'main'}"
          - "No other changes"

      - id: "bluetooth.py"
        changes:
          - "DELETE the file src/gtach/comm/bluetooth.py"
          - "Use MCP filesystem delete or write an empty file if delete unavailable"
```

---

## 4.0 Design

### 4.1 app.py — _start_normal_mode skeleton

```python
from .comm import select_transport
from .utils.platform import get_platform_type
import argparse

class GTachApplication:
    def __init__(self, config_path=None, debug=False, args=None):
        ...
        self._args = args or argparse.Namespace()
        ...

    def _start_normal_mode(self):
        self._display = DisplayManager(self._thread_manager, self._terminal_restorer)
        self._display.start()

        platform_type = get_platform_type()
        self._transport = select_transport(platform_type, self._args)
        self._obd = OBDProtocol(self._transport, self._thread_manager)

        self._watchdog.start()
        # Transport connects via OBDProtocol._protocol_loop (waits for is_connected)
        # Start reconnect loop in background thread:
        import threading
        self._reconnect_thread = threading.Thread(
            target=self._transport.reconnect_indefinitely,
            name='transport',
            daemon=True
        )
        self._reconnect_thread.start()
        self._obd.start()

    def _start_setup_mode(self):
        # Setup detection already handled upstream; no transport needed here
        ...

    def start(self):
        if self._device_store.get_primary_device() is None:   # was is_setup_complete()
            self._start_setup_mode()
        else:
            self._start_normal_mode()

    def shutdown(self):
        ...
        if hasattr(self, '_transport'):
            self._transport.disconnect()
        ...
```

### 4.2 main.py — skeleton

```python
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
    # Transport flags
    parser.add_argument('--macos', action='store_true',
                        help='Activate macOS development mode')
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
        # basic config load check
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
    - "Modify files in place using MCP filesystem tools"
    - "Delete bluetooth.py using MCP filesystem delete tool"
    - "If filesystem delete unavailable, overwrite bluetooth.py with a single comment: '# Removed — replaced by transport abstraction'"

  files:
    - path: "src/gtach/app.py"
      action: "modify"
    - path: "src/gtach/main.py"
      action: "rewrite"
    - path: "pyproject.toml"
      action: "modify"
    - path: "src/gtach/core/watchdog.py"
      action: "modify (one line)"
    - path: "src/gtach/comm/bluetooth.py"
      action: "delete"
```

---

## 6.0 Success Criteria

```yaml
success_criteria:
  - "app.py: no reference to BluetoothManager; select_transport() called in _start_normal_mode"
  - "app.py: setup detection uses get_primary_device() is None"
  - "app.py: transport thread registered under name 'transport'"
  - "app.py: shutdown calls self._transport.disconnect()"
  - "main.py: --macos, --transport, --obd-host, --obd-port, --serial-port args present"
  - "main.py: --service, --test-hardware, --validate-logging, --logging-health-check absent"
  - "main.py: setup_logging contains only basicConfig or NullHandler — no session machinery"
  - "main.py: version string '0.2.0'"
  - "pyproject.toml: version '0.2.0'; pyserial>=3.5 in dependencies; bleak absent"
  - "watchdog.py: critical_threads = {'display', 'transport', 'main'}"
  - "bluetooth.py: deleted or replaced with stub comment"
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

```
TASK: Modify 4 files, delete 1 file. Prerequisites: prompts 1 and 2 complete.

FILE 1: src/gtach/app.py
- Remove: from .comm import BluetoothManager
- Add: from .comm import select_transport; from .utils.platform import get_platform_type; import argparse
- GTachApplication.__init__(self, config_path=None, debug=False, args=None): store self._args = args or argparse.Namespace()
- _start_normal_mode(): after display.start() add:
    platform_type = get_platform_type()
    self._transport = select_transport(platform_type, self._args)
    self._obd = OBDProtocol(self._transport, self._thread_manager)
    start reconnect_indefinitely in threading.Thread(name='transport', daemon=True)
    self._obd.start()
- start(): replace is_setup_complete() with get_primary_device() is None
- shutdown(): replace self._bluetooth.stop() with self._transport.disconnect() (hasattr guard)

FILE 2: src/gtach/main.py  — REWRITE to ~80-100 lines
- Keep: --config, --debug, --version='0.2.0', --validate-config, --validate-dependencies
- ADD: --macos (store_true), --transport (choices tcp/serial/rfcomm), --obd-host (default localhost), --obd-port (int, default 35000), --serial-port (default None)
- REMOVE: --service, --test-hardware, --validate-logging, --logging-health-check and all associated functions
- setup_logging: if debug: basicConfig(DEBUG); else: addHandler(NullHandler()) — nothing else
- main(): GTachApplication(config_file, args.debug, args)

FILE 3: pyproject.toml
- version: '0.1.1' -> '0.2.0'
- dependencies: add 'pyserial>=3.5'; remove 'bleak' if present

FILE 4: src/gtach/core/watchdog.py
- ONE LINE: self.critical_threads = {'display', 'transport', 'main'}

DELETE: src/gtach/comm/bluetooth.py
- Delete file or overwrite with: # Removed — replaced by transport abstraction

SUCCESS: python -c 'from gtach.main import main' imports without error.
         pyproject.toml version == '0.2.0'. bluetooth.py absent or stub only.
```

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-03-24 | William Watson | Initial prompt |

---

Copyright (c) 2025 William Watson. This work is licensed under the MIT License.
