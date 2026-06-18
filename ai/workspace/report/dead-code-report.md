Created: 2026 June 18

# Dead Code Report — GTach `src/gtach`

---

## Table of Contents

[1.0 Purpose](<#1.0 purpose>)
[2.0 Methodology](<#2.0 methodology>)
[3.0 Dead Files](<#3.0 dead files>)
[4.0 Dead Code Within Active Files](<#4.0 dead code within active files>)
[5.0 Dead Assets](<#5.0 dead assets>)
[6.0 Summary](<#6.0 summary>)
[Version History](<#version history>)

---

## 1.0 Purpose

This document catalogues dead code identified in `src/gtach` — code that is defined but unreachable at runtime. It is a reference for cleanup decisions; no source changes are made here.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Methodology

Each file in `src/gtach` was inspected for:

- Imports not originating from any active module.
- Classes and functions defined but never called.
- Files shadowed by Python package resolution rules.

Backup files (`manager_backup.py`, `setup_original_backup.py`) were excluded from analysis per standing convention.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Dead Files

Files with no reachable import path from any active module.

### 3.1 `core/watchdog_enhanced.py`

Defines `EnhancedWatchdogMonitor(WatchdogMonitor)`. Not exported from `core/__init__.py`. No import reference anywhere in the codebase.

Estimated size: ~400 lines.

### 3.2 `display/hardware_interface.py`

Provides a touch hardware abstraction. No import reference anywhere in the codebase.

Estimated size: ~250 lines.

### 3.3 `display/ui_testing_framework.py`

A UI test harness. Not imported by any active module.

Estimated size: ~200 lines.

### 3.4 `display/enhanced_touch_factory.py`

Only referenced by `ui_testing_framework.py` (dead, §3.3) and `setup_original_backup.py` (excluded backup). Not reachable from any active module.

Estimated size: ~700 lines.

### 3.5 `display/performance.py` (flat file)

Python packages take precedence over modules of the same name in the same directory. The `display/performance/` package shadows this file completely — `from .performance import ...` resolves to the package. This file cannot be imported.

Estimated size: ~800 lines.

### 3.6 `display/components/` (package)

Contains `coordinator.py` (`DisplayComponentCoordinator`) and `factory.py` (`DisplayComponentFactory`). Neither is imported by any module outside the package. The package `__init__.py` exports them but nothing imports from the package.

Estimated size: ~600 lines combined.

### 3.7 `utils/services/` (package)

Contains `registry.py`, `configuration.py`, `platform.py`, `dependency.py`. Not imported anywhere from `utils/__init__.py` or any other active module. The package is entirely unreachable.

Estimated size: ~2000 lines combined.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Dead Code Within Active Files

### 4.1 `core/thread.py` — `AsyncSyncBridge` class

`AsyncSyncBridge` is instantiated in `ThreadManager.__init__` and its `shutdown()` is called in `ThreadManager.shutdown()`, but none of its functional methods are ever called: `set_event_loop`, `submit_async_task`, `send_message`. The class exists to support async/sync coordination that was never wired up.

Lines: ~60 lines for the class itself; instantiation and shutdown hooks are small but also effectively dead in terms of utility.

### 4.2 `core/thread.py` — Unused `ThreadManager` public API

The following methods are defined and exported but never called by any external code:

| Method | Note |
|---|---|
| `get_statistics()` | Returns thread counts, restarts, operation count |
| `list_threads()` | Returns snapshot of all thread info |
| `get_thread_info(name)` | Only called by `list_threads()` above |
| `is_healthy()` | Health check by heartbeat timeout |

These expose diagnostic data that nothing reads.

### 4.3 `core/thread.py` — `_sync_timing()` and `_operation_count`

`_sync_timing()` is a context manager used internally to time lock acquisitions and accumulate `_operation_count`. The counters are only surfaced via `get_statistics()` (dead, §4.2). The timing overhead runs on every lock acquisition for no operational benefit.

### 4.4 `utils/config.py` — `ConfigManager.setup_logging()` and helpers

`ConfigManager.setup_logging()` and its internal helpers `_setup_production_logging()`, `_setup_debug_logging()`, and `_log_pi_hardware_status()` are dead. Logging is fully managed in `main.py`'s standalone `setup_logging()`. These methods are never called.

This is a known open item from prior analysis.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Dead Assets

### 5.1 `assets/fonts/BebasNeue-Regular.ttf`

No reference to `BebasNeue` found anywhere in the Python source tree. Only `Michroma-Regular.ttf` is referenced. This font file is unused.

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Summary

| Category | Item | Approx. Lines |
|---|---|---|
| Dead file | `core/watchdog_enhanced.py` | ~400 |
| Dead file | `display/hardware_interface.py` | ~250 |
| Dead file | `display/ui_testing_framework.py` | ~200 |
| Dead file | `display/enhanced_touch_factory.py` | ~700 |
| Dead file | `display/performance.py` (shadowed) | ~800 |
| Dead package | `display/components/` | ~600 |
| Dead package | `utils/services/` | ~2000 |
| Dead class | `core/thread.py` — `AsyncSyncBridge` | ~60 |
| Dead methods | `core/thread.py` — `ThreadManager` public API | ~80 |
| Dead instrumentation | `core/thread.py` — `_sync_timing` / `_operation_count` | ~20 |
| Dead methods | `utils/config.py` — `setup_logging` group | ~200 |
| Dead asset | `assets/fonts/BebasNeue-Regular.ttf` | — |

Total dead Python: approximately 5300 lines across `src/gtach`.

No changes to source files are made by this report.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-06-18 | Initial report |

---

Copyright (c) 2026 William Watson. MIT License.
