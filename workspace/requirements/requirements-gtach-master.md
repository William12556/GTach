# GTach Requirements

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [2.0 Naming Conventions](<#2.0 naming conventions>)
- [3.0 Functional Requirements](<#3.0 functional requirements>)
- [4.0 Non-Functional Requirements](<#4.0 non-functional requirements>)
- [5.0 Architectural Requirements](<#5.0 architectural requirements>)
- [6.0 Out of Scope — Flagged for Review](<#6.0 out of scope — flagged for review>)
- [7.0 Traceability](<#7.0 traceability>)
- [8.0 Validation](<#8.0 validation>)
- [Version History](<#version history>)

---

```yaml
project_info:
  name: "GTach"
  version: "0.1.0-dev"
  date: "2026-03-13"
  author: "William Watson"
  status: "active"
  description: >
    Real-time automotive tachometer application. Displays engine RPM on a
    circular touch display connected to a Raspberry Pi Zero. Obtains RPM
    data via Bluetooth ELM327 OBD-II adapter. Primary functionality is
    RPM display. Secondary functionality is one-time Bluetooth device
    setup via touch interface.
```

---

## 1.0 Document Information

Functional, non-functional, and architectural requirements for the GTach real-time RPM display application.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Naming Conventions

[Return to Table of Contents](<#table of contents>)

```yaml
naming_conventions:
  package_name: "gtach"
  module_style: "snake_case"
  class_style: "PascalCase"
  function_style: "snake_case"
  constant_style: "UPPER_SNAKE_CASE"
  notes: >
    Root package is 'gtach'. Domain subpackages: comm, core, display, utils.
```

---

## 3.0 Functional Requirements

[Return to Table of Contents](<#table of contents>)

```yaml
functional_requirements:

  - id: "a1b2c3d4"
    type: "functional"
    description: >
      The application shall display engine RPM in real time on a circular
      touch display. RPM data is obtained from an OBD-II adapter via Bluetooth.
    acceptance_criteria:
      - "Application polls OBD-II PID 0x0C at a configured minimum interval of 200 ms (5 Hz target)"
      - "Displayed RPM value reflects the most recently received OBD-II PID 0x0C response"
    source: "stakeholder"
    rationale: "Primary application purpose."
    dependencies: []

  - id: "b2c3d4e5"
    type: "functional"
    description: >
      The application shall support two RPM display modes: DIGITAL (numeric
      readout) and GAUGE (arc or needle representation). The user may switch
      between modes at runtime via a swipe gesture on the display.
    acceptance_criteria:
      - "DIGITAL mode renders a numerical RPM value centered on the display"
      - "GAUGE mode renders a circular arc or needle proportional to RPM"
      - "A swipe-left or swipe-right gesture on the display switches between modes"
      - "Mode switches without interrupting Bluetooth or OBD polling"
      - "The active mode persists to the configuration file after each switch"
      - "Initial mode on startup is read from the configuration file"
    source: "stakeholder"
    rationale: >
      Swipe gesture allows mode switching without navigating a settings screen.
      Persistence ensures the user preference survives power cycles.
    dependencies:
      - "a1b2c3d4"

  - id: "c3d4e5f6"
    type: "functional"
    description: >
      The application shall use the display background colour as the primary
      RPM visual indicator, divided into four fixed discrete bands. As RPM
      increases the background transitions through black, green, yellow, and
      red. Screen elements (RPM numeral or gauge arc) shall remain legible
      against each background colour.
    acceptance_criteria:
      - "Background is black for RPM 0–2999"
      - "Background is green for RPM 3000–3999"
      - "Background is yellow for RPM 4000–4999"
      - "Background is red for RPM 5000 and above"
      - "Background colour changes immediately when RPM crosses a band boundary"
      - "RPM numeral and gauge arc are rendered in a contrasting colour against each background band"
      - "Band boundaries are fixed and not user-configurable"
    source: "stakeholder"
    rationale: >
      A simple colour progression from green to red provides an immediate,
      intuitive visual cue without requiring the driver to read a scale.
      Fixed bands minimise configuration surface and implementation complexity.
    dependencies:
      - "a1b2c3d4"

  - id: "d4e5f6a7"
    type: "functional"
    description: >
      On first run (no paired device stored), the application shall enter a
      setup mode that guides the user through Bluetooth device discovery and
      pairing via the touch interface.
    acceptance_criteria:
      - "Application detects absence of stored device and enters setup mode automatically"
      - "Setup mode discovers and lists all nearby Bluetooth devices without name filtering"
      - "User can select a device from the list via touch"
      - "Selected device address is persisted to the device store"
      - "Application transitions to normal RPM display mode after successful pairing"
    source: "stakeholder"
    rationale: >
      One-time Bluetooth pairing is a prerequisite for operation. No name filter is
      applied — the user identifies and selects their adapter from all visible devices.
      Manual MAC address entry is not feasible on a small touch display.
    dependencies: []

  - id: "e5f6a7b8"
    type: "functional"
    description: >
      On subsequent runs, the application shall automatically connect to the
      stored paired device without user interaction. If the connection is lost
      during operation, the application shall display a static disconnected
      indicator and continue attempting to reconnect indefinitely in the
      background. There is no retry limit.
    acceptance_criteria:
      - "Application reads stored device address from device store on startup"
      - "Bluetooth connection attempt to stored device begins before entering normal mode"
      - "On connection loss, display transitions to a static disconnected state"
      - "Background reconnection attempts continue indefinitely with a configured delay between attempts"
      - "Normal RPM display resumes automatically when the connection is re-established"
      - "No retry limit is enforced; the application never autonomously enters setup mode from a disconnected state"
    source: "stakeholder"
    rationale: >
      Hands-free reconnection is required for automotive use. A retry limit that
      forces setup mode is inappropriate while the vehicle is moving. The driver
      must retain control of any mode transition.
    dependencies:
      - "d4e5f6a7"

  - id: "f3a4b5c6"
    type: "functional"
    description: >
      While in the disconnected state, a deliberate touch gesture on the display
      shall allow the user to manually enter setup mode to pair a different device.
    acceptance_criteria:
      - "A long-press (duration configurable, default 3 seconds) on the disconnected screen triggers entry to setup mode"
      - "A visible prompt on the disconnected screen indicates the gesture required"
      - "Entering setup mode via this gesture clears the stored device and starts device discovery"
    source: "stakeholder"
    rationale: >
      The driver must be able to re-pair when the vehicle is safely stopped.
      A long-press is deliberate and unlikely to be triggered accidentally.
    dependencies:
      - "e5f6a7b8"
      - "d4e5f6a7"

  - id: "f6a7b8c9"
    type: "functional"
    description: >
      The application shall poll OBD-II PID 0x0C (Engine RPM) at regular
      intervals over the Bluetooth connection using the ELM327 protocol.
    acceptance_criteria:
      - "ELM327 initialization sequence is sent after Bluetooth connection"
      - "PID 0x0C is requested at configured polling interval"
      - "RPM value is parsed from ELM327 response and passed to display"
      - "A timeout or parse error results in a defined error state, not a crash"
    source: "stakeholder"
    rationale: "OBD-II PID 0x0C is the sole data source for RPM."
    dependencies:
      - "e5f6a7b8"

  - id: "a7b8c9d0"
    type: "functional"
    description: >
      The application shall persist configuration to a YAML file. Configurable
      parameters are: display mode, FPS limit, and Bluetooth settings
      (stored device, scan duration, retry delay).
    acceptance_criteria:
      - "Configuration file is created with defaults on first run if absent"
      - "Configuration is loaded from file on startup"
      - "Configuration file path follows the hierarchy: env var > user (~/.config/gtach/) > system (/etc/gtach/)"
      - "Invalid configuration values produce a warning and fall back to defaults"
    source: "stakeholder"
    rationale: "Persistent configuration avoids re-entry on each startup."
    dependencies: []

  - id: "b8c9d0e1"
    type: "functional"
    description: >
      The application shall display a splash screen during startup before
      transitioning to either setup mode or normal RPM display mode.
    acceptance_criteria:
      - "Splash screen is displayed for a configurable duration (default 4 seconds)"
      - "Splash screen can be disabled via configuration"
      - "Splash screen transitions cleanly to setup or normal mode"
    source: "stakeholder"
    rationale: "Provides visual feedback during initialisation on slow hardware."
    dependencies: []

  - id: "c9d0e1f2"
    type: "functional"
    description: >
      The application shall handle graceful shutdown on SIGINT and SIGTERM,
      stopping all threads and releasing resources cleanly.
    acceptance_criteria:
      - "SIGINT and SIGTERM signals trigger shutdown sequence"
      - "All managed threads are stopped before process exit"
      - "No zombie threads or resource leaks on clean shutdown"
    source: "constraint"
    rationale: "Required for reliable operation as a system application."
    dependencies: []

  - id: "d1e2f3a4"
    type: "functional"
    description: >
      The application shall start automatically at system boot on the target
      platform. Autostart is implemented via a systemd unit file; the application
      itself does not implement daemon or service logic.
    acceptance_criteria:
      - "A systemd unit file is provided that starts gtach after the graphical target"
      - "Application starts without manual user intervention after Pi Zero boot"
      - "systemd restarts the application automatically on unexpected exit"
    source: "stakeholder"
    rationale: >
      GTach is a single-purpose device. Manual launch after each boot is not
      acceptable in automotive use. Systemd is the standard Linux mechanism for
      service management; daemon logic within the application is unnecessary.
    dependencies:
      - "c9d0e1f2"
```

---

## 4.0 Non-Functional Requirements

[Return to Table of Contents](<#table of contents>)

```yaml
non_functional_requirements:

  - id: "d0e1f2a3"
    type: "non_functional"
    category: "performance"
    description: >
      The application shall operate within the resource constraints of a
      Raspberry Pi Zero (ARMv6, 512 MB RAM, single core).
    acceptance_criteria:
      - "Display frame rate does not exceed 30 FPS on the target platform"
      - "Idle CPU usage does not exceed 50% on the Pi Zero during normal operation"
      - "Total memory footprint does not exceed 128 MB RSS"
    target_metric: "FPS ≤ 30; CPU ≤ 50%; RSS ≤ 128 MB"
    source: "constraint"
    rationale: "Pi Zero has limited CPU and memory resources."
    dependencies: []

  - id: "e1f2a3b4"
    type: "non_functional"
    category: "maintainability"
    description: >
      Logging shall be disabled by default. Debug logging shall be
      activated only when the --debug flag is passed at startup.
    acceptance_criteria:
      - "Application produces no log file output in default (production) mode"
      - "Debug mode enables console and file logging at DEBUG level"
      - "Debug log file is written to ~/.local/share/gtach/logs/ or /var/log/gtach/"
      - "Log format: timestamp level logger message (flat file)"
    target_metric: "Zero file I/O for logging in production mode"
    source: "stakeholder"
    rationale: >
      Log file I/O degrades performance and consumes SD card write cycles
      on Pi Zero. Logging overhead is unacceptable in production.
    dependencies: []

  - id: "f2a3b4c5"
    type: "non_functional"
    category: "reliability"
    description: >
      The application shall automatically attempt to reconnect to the paired
      Bluetooth device after a connection loss, indefinitely, until the
      connection is restored or the user manually enters setup mode.
    acceptance_criteria:
      - "Connection loss is detected within the configured keepalive interval"
      - "Reconnection attempts are made continuously with a configured delay between each attempt"
      - "No reconnection attempt limit is enforced"
      - "RPM display shows a static disconnected indicator during reconnection"
      - "Normal operation resumes automatically on successful reconnection"
    target_metric: "Reconnection attempt initiated within keepalive interval of connection loss"
    source: "stakeholder"
    rationale: >
      Automotive environment may cause intermittent Bluetooth dropouts.
      The application must recover without driver intervention. Imposing a
      retry limit that forces setup mode is unsafe while driving.
    dependencies:
      - "e5f6a7b8"

  - id: "a3b4c5d6"
    type: "non_functional"
    category: "usability"
    description: >
      The touch interface used during setup and on the disconnected screen shall
      be operable on the HyperPixel Round 480×480 circular display, with a
      minimum touch target size of 44×44 pixels.
    acceptance_criteria:
      - "All interactive touch targets are at minimum 44×44 pixels"
      - "Touch regions do not overlap"
      - "Interactive elements are positioned within the visible circular area of the display"
    target_metric: "Minimum touch target: 44×44 px; all elements within 480×480 circle"
    source: "constraint"
    rationale: "HyperPixel Round circular display requires adequate touch target sizing and circular-aware layout."
    dependencies:
      - "b0c1d2e3"
      - "d4e5f6a7"

  - id: "b4c5d6e7"
    type: "non_functional"
    category: "maintainability"
    description: >
      The codebase shall use conditional imports for platform-specific
      dependencies to permit development and testing on macOS.
    acceptance_criteria:
      - "Import of pygame, bleak, and hardware-specific modules is guarded by try/except"
      - "Application degrades gracefully on macOS when hardware interfaces are absent"
      - "Mock stubs are sufficient for unit testing without target hardware"
    target_metric: "All platform-specific imports are conditional"
    source: "constraint"
    rationale: "Development occurs on macOS; deployment target is Raspberry Pi."
    dependencies: []
```

---

## 5.0 Architectural Requirements

[Return to Table of Contents](<#table of contents>)

```yaml
architectural_requirements:

  - id: "b0c1d2e3"
    type: "architectural"
    description: >
      The target hardware platform is fixed and non-optional: Raspberry Pi Zero 2W
      with a Pimoroni HyperPixel Round display (480×480 px circular touch display).
      All display geometry, touch input, and resource constraints are derived from
      this hardware combination.
    acceptance_criteria:
      - "Application renders all display output to a 480×480 pixel surface"
      - "Rendering geometry accounts for the circular visible area; UI elements are not placed in the corners outside the inscribed circle"
      - "Touch events are received via the pygame event system without hardware-specific driver code in the application"
    constraints:
      - "Raspberry Pi Zero 2W — ARMv8 quad-core 1 GHz, 512 MB RAM"
      - "Pimoroni HyperPixel Round — 480×480 px, circular, capacitive touch, DSI interface"
      - "No other display or compute hardware is supported"
    source: "stakeholder"
    rationale: >
      GTach is a single-purpose embedded device. Hardware is fixed;
      portability to other display or compute hardware is not a requirement.
    dependencies: []

  - id: "c5d6e7f8"
    type: "architectural"
    description: >
      The application shall be structured as a Python package (gtach) with
      domain subpackages: comm (Bluetooth, OBD), core (threads, watchdog),
      display (rendering, setup, touch), utils (config, platform, home).
    acceptance_criteria:
      - "Package structure matches defined domain layout"
      - "No circular imports between subpackages"
      - "Each subpackage has a defined public interface via __init__.py"
    constraints:
      - "Python >= 3.9"
      - "Package installable via pyproject.toml"
    source: "architectural"
    rationale: "Domain separation supports maintainability and testability."
    dependencies: []

  - id: "d6e7f8a9"
    type: "architectural"
    description: >
      The application shall use pygame for display rendering and touch input
      handling on the target platform.
    acceptance_criteria:
      - "All display rendering uses pygame surfaces and draw primitives"
      - "Touch events are received and dispatched via pygame event loop"
      - "pygame import is conditional for cross-platform compatibility"
    constraints:
      - "pygame >= 2.0"
    source: "architectural"
    rationale: "pygame is a well-supported, lightweight rendering library for Pi."
    dependencies:
      - "c5d6e7f8"

  - id: "e7f8a9b0"
    type: "architectural"
    description: >
      The application shall use the Bleak library for Bluetooth communication
      with the ELM327 adapter.
    acceptance_criteria:
      - "Bluetooth operations use Bleak BleakScanner and BleakClient"
      - "Bleak operations execute in a dedicated event loop thread"
      - "Synchronous interface is provided for OBD protocol caller"
    constraints:
      - "bleak >= 0.20"
    source: "architectural"
    rationale: "Bleak provides cross-platform BLE support compatible with both macOS and Pi."
    dependencies:
      - "c5d6e7f8"

  - id: "f8a9b0c1"
    type: "architectural"
    description: >
      All inter-thread shared state shall be protected by appropriate
      synchronization primitives (threading.Lock, threading.Event).
    acceptance_criteria:
      - "No shared mutable state is accessed without a lock"
      - "Deadlock-prone patterns (nested locks, lock inversions) are absent"
      - "Thread lifecycle is managed by a central ThreadManager"
    constraints:
      - "Complexity of synchronization is minimised for Pi Zero single-core context"
    source: "architectural"
    rationale: "Thread safety is required; over-engineering adds CPU overhead on Pi Zero."
    dependencies:
      - "c5d6e7f8"

  - id: "a9b0c1d2"
    type: "architectural"
    description: >
      The application shall use a watchdog monitor to detect and respond to
      unresponsive threads during normal operation.
    acceptance_criteria:
      - "Watchdog checks thread heartbeats at a configured interval"
      - "Watchdog triggers shutdown callback when a thread exceeds critical timeout"
      - "Watchdog is itself a managed thread subject to shutdown"
    constraints: []
    source: "architectural"
    rationale: "Watchdog provides a last-resort recovery mechanism for hung threads."
    dependencies:
      - "f8a9b0c1"
```

---

## 6.0 Out of Scope — Flagged for Review

[Return to Table of Contents](<#table of contents>)

The following features were identified in the existing source code but are considered
outside the defined scope of a minimal RPM display application. Each is flagged for
explicit acceptance or rejection before design begins.

| ID | Feature | Source Location | Disposition |
|----|---------|-----------------|-------------|
| OOS-01 | Service / daemon mode (`--service` flag, `run_as_service()`) | `main.py` | **Out of scope** — autostart delegated to systemd unit file; application does not implement daemon behaviour. Systemd unit file is an in-scope deployment artefact. |
| OOS-02 | Logging validation CLI modes (`--validate-logging`, `--logging-health-check`) | `main.py` | **Out of scope** — remove |
| OOS-03 | Hardware test CLI mode (`--test-hardware`) | `main.py` | **Out of scope** — remove; field diagnostics not required |
| OOS-04 | Data logging (`data_log_enabled`, `data_log_path`) | `config.py OBDConfig` | **Out of scope** — remove |
| OOS-05 | Session log management and archival (`SessionManager`, `SessionConfig`) | `config.py` | **Out of scope** — remove |
| OOS-06 | Configuration transaction system (`ConfigTransaction`) | `config.py` | **Out of scope** — remove |
| OOS-07 | Reader-writer lock (`RWLock`) | `config.py` | **Out of scope** — simplify to `threading.Lock` |
| OOS-08 | Configuration performance monitoring (op counters, timing) | `config.py ConfigManager` | **Out of scope** — remove |
| OOS-09 | Config validator with Pi/Mac-specific checks (`ConfigValidator`) | `config.py` | **Out of scope** — simplify to basic range checks only |
| OOS-10 | Splash screen animation modes (automotive, minimal, text_only) | `config.py SplashConfig` | **Out of scope** — retain splash screen (REQ b8c9d0e1); single minimal rendering mode only |
| OOS-11 | Provisioning domain (`src/provisioning/`) | `src/` | **Out of scope** — remove; traditional deployment methods used |
| OOS-12 | `demonstrate_version_*.py` scripts in `src/` | `src/` | **Out of scope** — remove |
| OOS-13 | FPS limit default of 60 (excessive for Pi Zero) | `config.py DisplayConfig` | **Out of scope** — default changed to 30 FPS; configurable, target platform upper bound 30 FPS |
| OOS-14 | Manual device MAC entry in setup mode | `display/setup.py` | **Out of scope** — remove; MAC entry not feasible on touch display |
| OOS-15 | Legacy INI config migration path | `config.py ConfigManager` | **Out of scope** — remove; no prior installation to migrate from |

> **OOS-01 Deployment note:** Autostart at boot is an **in-scope deployment requirement**
> implemented as a systemd unit file (not application code). The unit file shall be created
> as a deployment artefact outside the Python package.

---

## 7.0 Traceability

[Return to Table of Contents](<#table of contents>)

```yaml
traceability:
  design_refs: []
  test_refs: []
  code_refs:
    - req_id: "a1b2c3d4"
      component: "OBDProtocol, DisplayManager"
      file_path: "src/gtach/comm/obd.py, src/gtach/display/manager.py"
    - req_id: "d4e5f6a7"
      component: "SetupDisplayManager, BluetoothManager"
      file_path: "src/gtach/display/setup.py, src/gtach/comm/bluetooth.py"
    - req_id: "e5f6a7b8"
      component: "BluetoothManager, DeviceStore"
      file_path: "src/gtach/comm/bluetooth.py, src/gtach/comm/device_store.py"
    - req_id: "f6a7b8c9"
      component: "OBDProtocol"
      file_path: "src/gtach/comm/obd.py"
    - req_id: "a7b8c9d0"
      component: "ConfigManager"
      file_path: "src/gtach/utils/config.py"
    - req_id: "f8a9b0c1"
      component: "ThreadManager"
      file_path: "src/gtach/core/thread.py"
    - req_id: "a9b0c1d2"
      component: "WatchdogMonitor"
      file_path: "src/gtach/core/watchdog.py"
```

---

## 8.0 Validation

[Return to Table of Contents](<#table of contents>)

```yaml
validation:
  completeness_check: "approved"
  clarity_check: "approved"
  testability_check: "approved"
  conflicts_identified:
    - req_id_1: "d0e1f2a3"
      req_id_2: "b2c3d4e5"
      conflict_description: >
        GAUGE mode arc rendering may consume more CPU than DIGITAL mode.
        30 FPS constraint must be validated for GAUGE mode on Pi Zero 2W.
      resolution: "pending — validate during performance testing"
```

---

## Version History

| Version | Date       | Author         | Changes |
|---------|------------|----------------|---------|
| 0.1     | 2026-03-13 | William Watson | Initial draft — reverse engineered from existing source code |
| 0.2     | 2026-03-13 | William Watson | OOS items reviewed: OOS-01,02,03,04,05,06,07,08,09,10,11,12,13,15 resolved; OOS-14 pending; added REQ d1e2f3a4 (autostart via systemd) |
| 0.3     | 2026-03-13 | William Watson | OOS-14 resolved out of scope; REQ d4e5f6a7 updated — scan filter removed, all Bluetooth devices listed unfiltered |
| 0.4     | 2026-03-13 | William Watson | Added ARCH b0c1d2e3 (fixed hardware: Pi Zero 2W + HyperPixel Round 480×480); reworked REQ e5f6a7b8 — indefinite background reconnect, no retry limit, static disconnected state; added REQ f3a4b5c6 — long-press gesture on disconnected screen to enter setup mode; updated NFR f2a3b4c5 and a3b4c5d6 accordingly |
| 0.5     | 2026-03-13 | William Watson | Removed hardware-uninfluenceable acceptance criteria: dropped "readable under ambient lighting" (REQ a1b2c3d4); rephrased 5 Hz criterion as configurable polling interval target; removed "deliberate enough to prevent accidental activation" (REQ f3a4b5c6); replaced hardware-fact criteria in ARCH b0c1d2e3 with software-testable equivalents |
| 0.6     | 2026-03-13 | William Watson | REQ b2c3d4e5 — added swipe left/right gesture for runtime mode switching; mode persists to config file. REQ c3d4e5f6 — rpm_warning, rpm_danger, rpm_max now explicitly configurable; added guard criterion for invalid threshold ordering |
| 0.8     | 2026-03-13 | William Watson | Section 1.0 populated with document purpose statement; validation status set to approved |

---

Copyright (c) 2025 William Watson. This work is licensed under the MIT License.
