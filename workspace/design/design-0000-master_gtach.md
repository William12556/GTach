# GTach Master Design Document

Created: 2025-12-29

---

## Table of Contents

- [1.0 Project Information](<#1.0 project information>)
- [2.0 Scope](<#2.0 scope>)
- [3.0 System Overview](<#3.0 system overview>)
- [4.0 Design Constraints](<#4.0 design constraints>)
- [5.0 Development Environment](<#5.0 development environment>)
- [6.0 Target Platform](<#6.0 target platform>)
- [7.0 Architecture](<#7.0 architecture>)
- [8.0 Domain Structure](<#8.0 domain structure>)
- [9.0 Data Design](<#9.0 data design>)
- [10.0 Interfaces](<#10.0 interfaces>)
- [11.0 Error Handling](<#11.0 error handling>)
- [12.0 Non-Functional Requirements](<#12.0 non-functional requirements>)
- [13.0 Visual Documentation](<#13.0 visual documentation>)
- [14.0 Tier 2 Domain Documents](<#14.0 tier 2 domain documents>)
- [Version History](<#version history>)

---

## 1.0 Project Information

```yaml
project_info:
  name: "GTach"
  version: "0.1.0-alpha.1"
  date: "2025-12-29"
  author: "William Watson"
  description: "Real-time automotive tachometer display for embedded circular touch screens"
  license: "MIT"
```

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Scope

### 2.1 Purpose

GTach provides real-time engine RPM monitoring via OBD-II Bluetooth interface with visualization on embedded circular touch displays. The application connects to ELM327-compatible Bluetooth OBD-II adapters, retrieves engine telemetry data, and renders tachometer displays optimized for automotive dash mounting.

### 2.2 In Scope

- ELM327 OBD-II protocol communication via Bluetooth
- Real-time RPM data acquisition and display
- Digital and analog gauge display modes
- Touch-based user interface with gesture navigation
- Setup wizard for initial Bluetooth device pairing
- Cross-platform development (macOS) to deployment (Raspberry Pi) pipeline
- Thread-safe concurrent operation with watchdog monitoring
- Session-based configuration and logging management
- Graceful degradation with hardware mock fallbacks

### 2.3 Out of Scope

- WiFi OBD-II adapters
- CAN bus direct connection
- Data logging and analytics
- Cloud connectivity
- Multi-vehicle profiles
- Advanced diagnostics beyond RPM display
- Audio/haptic feedback systems

### 2.4 Terminology

| Term | Definition |
|------|------------|
| ELM327 | Microcontroller chip implementing OBD-II to RS-232 protocol translation |
| OBD-II | On-Board Diagnostics version 2 - standardized vehicle diagnostic interface |
| PID | Parameter ID - OBD-II data request identifier (e.g., 0x0C for RPM) |
| BLE | Bluetooth Low Energy - wireless communication protocol |
| Framebuffer | Direct video memory access for display rendering |
| HyperPixel | Pimoroni circular touch display for Raspberry Pi |

[Return to Table of Contents](<#table of contents>)

---

## 3.0 System Overview

### 3.1 Description

GTach is a Python-based embedded application implementing a real-time automotive tachometer. The system architecture follows a domain-driven design with five functional domains: Core (threading/watchdog), Communication (Bluetooth/OBD), Display (rendering/touch), Utilities (configuration/platform), and Provisioning (deployment/versioning).

### 3.2 Context Flow

```
Vehicle ECU → ELM327 Adapter → Bluetooth → BluetoothManager → OBDProtocol → DisplayManager → Framebuffer → User
                                                    ↓
                                              ThreadManager ← WatchdogMonitor
                                                    ↓
                                              ConfigManager
```

### 3.3 Primary Functions

1. **Bluetooth Device Management**: Scan, discover, connect to ELM327 OBD-II adapters
2. **OBD Protocol Handling**: Initialize ELM327, request RPM data (PID 0x0C), parse responses
3. **Display Rendering**: Double-buffered 60 FPS rendering to framebuffer with mode switching
4. **Touch Input Processing**: Gesture recognition (swipe, long-press) for mode navigation
5. **Thread Lifecycle Management**: Atomic state transitions with automatic restart on failure
6. **Watchdog Monitoring**: Health checks with escalating recovery procedures
7. **Platform Abstraction**: Cross-platform operation with conditional hardware access

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Design Constraints

### 4.1 Technical Constraints

- Raspberry Pi Zero 2W resource limitations (512MB RAM, quad-core ARM)
- Circular display resolution (480x480 HyperPixel)
- Bluetooth Classic for ELM327 compatibility (most adapters do not support BLE)
- Real-time rendering requirements (30-60 FPS minimum)
- Automotive environment considerations (vibration, temperature variation)

### 4.2 Implementation Constraints

```yaml
implementation:
  language: "Python 3.9+"
  framework: "None (pure Python with minimal dependencies)"
  libraries:
    - "bleak: Cross-platform Bluetooth (async)"
    - "pygame: Display rendering and event handling"
    - "PyYAML: Configuration file parsing (optional)"
  standards:
    - "PEP 8: Python style guide"
    - "PEP 484: Type hints"
    - "SAE J1979: OBD-II PID definitions"
```

### 4.3 Performance Targets

| Metric | Target Value |
|--------|--------------|
| Display Frame Rate | 60 FPS (development), 30 FPS (deployment) |
| OBD Response Latency | < 100ms |
| Bluetooth Reconnection | < 5 seconds |
| Memory Usage | < 256MB resident |
| Startup Time | < 10 seconds to operational |
| Thread Recovery | < 30 seconds automatic restart |

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Development Environment

```yaml
development_environment:
  platform: "macOS 14+ (Sonoma)"
  python_version: "3.9+"
  toolchain:
    - "pytest: Unit and integration testing"
    - "pytest-asyncio: Async test support"
    - "pytest-cov: Coverage analysis"
    - "mypy: Static type checking (recommended)"
  ide: "Any Python-capable editor"
  version_control: "Git with GitHub"
```

### 5.1 Development Dependencies

- Python virtual environment (venv)
- Mock implementations for Raspberry Pi hardware (GPIO, framebuffer)
- Bluetooth adapter for ELM327 testing
- Pygame for display simulation

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Target Platform

```yaml
target_platform:
  type: "embedded"
  hardware: "Raspberry Pi Zero 2W"
  os: "Raspberry Pi OS (Debian-based Linux)"
  architecture: "ARM64 (aarch64)"
  display: "Pimoroni HyperPixel 2.1 Round (480x480)"
  constraints:
    - "512MB RAM"
    - "Quad-core ARM Cortex-A53 @ 1GHz"
    - "microSD storage"
    - "Single USB port (Bluetooth dongle or built-in)"
    - "GPIO pins occupied by display"
```

### 6.1 Deployment Requirements

- Raspberry Pi OS Lite (headless) or Desktop
- Python 3.9+ with virtual environment
- Framebuffer access permissions
- Bluetooth service enabled and accessible
- Auto-start via systemd service unit

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Architecture

### 7.1 Architectural Pattern

**Layered Domain Architecture** with asynchronous coordination

The system employs a domain-driven design where each functional area (Core, Communication, Display, Utilities, Provisioning) operates as an independent domain with well-defined interfaces. Cross-domain communication occurs through the ThreadManager and event queues.

### 7.2 Component Relationships

```
GTachApplication (Coordinator)
    ├── ConfigManager (Singleton)
    ├── ThreadManager (Singleton-like)
    │   └── AsyncSyncBridge
    ├── WatchdogMonitor
    │   └── ThreadManager (reference)
    ├── BluetoothManager
    │   ├── ThreadManager (reference)
    │   └── DeviceStore
    ├── OBDProtocol
    │   ├── BluetoothManager (reference)
    │   └── ThreadManager (reference)
    └── DisplayManager
        ├── ThreadManager (reference)
        ├── DisplayRenderingEngine
        ├── TouchEventCoordinator
        ├── PerformanceMonitor
        └── SetupDisplayManager (conditional)
```

### 7.3 Technology Stack

```yaml
technology_stack:
  language: "Python 3.9+"
  runtime: "CPython interpreter"
  async_framework: "asyncio (standard library)"
  bluetooth: "Bleak (cross-platform BLE/Classic)"
  display: "Pygame (SDL2 wrapper)"
  configuration: "PyYAML (optional, graceful fallback)"
  data_store: "YAML files (device persistence)"
  testing: "pytest ecosystem"
```

### 7.4 Directory Structure

```
GTach/
├── ai/
│   ├── governance.md
│   └── templates/
├── src/
│   ├── gtach/
│   │   ├── __init__.py          # Package exports, version
│   │   ├── main.py              # Entry point, CLI
│   │   ├── app.py               # Application controller
│   │   ├── core/                # Threading, watchdog
│   │   ├── comm/                # Bluetooth, OBD protocol
│   │   ├── display/             # Rendering, touch, UI
│   │   └── utils/               # Config, platform detection
│   ├── provisioning/            # Deployment tooling
│   ├── scripts/                 # Release utilities
│   ├── config/                  # Runtime configuration
│   └── tests/                   # Unit tests
├── tests/                       # Integration tests
├── workspace/
│   ├── design/
│   ├── change/
│   ├── issues/
│   ├── prompt/
│   ├── test/
│   ├── trace/
│   ├── audit/
│   └── knowledge/
├── docs/
└── pyproject.toml
```

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Domain Structure

### 8.1 Core Domain

**Location**: `src/gtach/core/`

**Purpose**: Thread lifecycle management and system health monitoring

**Components**:
- `ThreadManager`: Thread-safe lifecycle management with atomic state transitions
- `WatchdogMonitor`: Health monitoring with escalating recovery procedures
- `AsyncSyncBridge`: Coordination between async and sync execution contexts

**Key Patterns**:
- State Machine: ThreadStatus (STARTING → RUNNING → STOPPING → STOPPED)
- Observer: Thread heartbeat monitoring
- Strategy: Platform-optimized worker pool sizing

### 8.2 Communication Domain

**Location**: `src/gtach/comm/`

**Purpose**: Bluetooth connectivity and OBD-II protocol handling

**Components**:
- `BluetoothManager`: Bleak-based cross-platform Bluetooth with state management
- `OBDProtocol`: ELM327 initialization and RPM data acquisition
- `DeviceStore`: YAML-based persistent device storage
- `BluetoothDevice`: Device model with connection metadata

**Key Patterns**:
- State Machine: BluetoothState (DISCONNECTED → SCANNING → CONNECTING → CONNECTED)
- Repository: DeviceStore for device persistence
- Adapter: OBDProtocol adapting ELM327 to application interface

### 8.3 Display Domain

**Location**: `src/gtach/display/`

**Purpose**: Visual rendering, touch input, and user interface

**Components**:
- `DisplayManager`: Component orchestration and lifecycle
- `DisplayRenderingEngine`: Double-buffered framebuffer rendering
- `TouchEventCoordinator`: Gesture recognition and event routing
- `PerformanceMonitor`: FPS and frame time tracking
- `SetupDisplayManager`: Initial device pairing wizard
- `SplashScreen`: Automotive-themed startup display

**Key Patterns**:
- State Machine: DisplayMode (SPLASH → DIGITAL/GAUGE → SETTINGS)
- Factory: Component creation via factory classes
- Observer: Touch gesture callbacks
- Double Buffer: Front/back buffer swapping for tear-free rendering

### 8.4 Utilities Domain

**Location**: `src/gtach/utils/`

**Purpose**: Cross-cutting concerns and platform abstraction

**Components**:
- `ConfigManager`: Thread-safe singleton configuration with session management
- `PlatformDetector`: Multi-method Raspberry Pi detection
- `TerminalRestorer`: Console state management for framebuffer applications
- `DependencyValidator`: Runtime dependency checking
- `OBDII_HOME`: Standardized path management

**Key Patterns**:
- Singleton: ConfigManager with double-checked locking
- Strategy: Platform-specific detection methods
- Template Method: Configuration hierarchy (env → user → system → default)

### 8.5 Provisioning Domain

**Location**: `src/provisioning/`

**Purpose**: Deployment package creation and version management

**Components**:
- `PackageCreator`: Deployment archive generation
- `ConfigProcessor`: Platform-specific configuration templating
- `ArchiveManager`: Compression with metadata
- `VersionStateManager`: Semantic versioning with development stages

**Key Patterns**:
- Builder: Package assembly with validation
- Strategy: Compression format selection

[Return to Table of Contents](<#table of contents>)

---

## 9.0 Data Design

### 9.1 Entities

#### 9.1.1 BluetoothDevice

```yaml
entity:
  name: "BluetoothDevice"
  purpose: "Represents a discovered or paired Bluetooth OBD-II adapter"
  attributes:
    - name: "name"
      type: "str"
      constraints: "Required, max 64 characters"
    - name: "address"
      type: "str"
      constraints: "Required, MAC address format (XX:XX:XX:XX:XX:XX)"
    - name: "device_type"
      type: "str"
      constraints: "Optional, e.g., 'ELM327', 'OBDLink'"
    - name: "signal_strength"
      type: "int"
      constraints: "Optional, RSSI in dBm"
    - name: "connection_verified"
      type: "bool"
      constraints: "Default False"
    - name: "last_seen"
      type: "datetime"
      constraints: "Auto-updated on detection"
```

#### 9.1.2 OBDResponse

```yaml
entity:
  name: "OBDResponse"
  purpose: "Parsed OBD-II response data"
  attributes:
    - name: "pid"
      type: "int"
      constraints: "0x00-0xFF"
    - name: "data"
      type: "bytes"
      constraints: "Raw response bytes"
    - name: "value"
      type: "float"
      constraints: "Calculated value (e.g., RPM)"
    - name: "timestamp"
      type: "float"
      constraints: "Unix timestamp"
    - name: "valid"
      type: "bool"
      constraints: "Response validity flag"
```

#### 9.1.3 DisplayConfig

```yaml
entity:
  name: "DisplayConfig"
  purpose: "Display rendering and interaction settings"
  attributes:
    - name: "mode"
      type: "DisplayMode"
      constraints: "Enum: SPLASH, DIGITAL, GAUGE, SETTINGS"
    - name: "rpm_warning"
      type: "int"
      constraints: "Default 6500 (Fiat 500 Abarth)"
    - name: "rpm_danger"
      type: "int"
      constraints: "Default 7000"
    - name: "fps_limit"
      type: "int"
      constraints: "Default 60"
    - name: "gesture_swipe_threshold"
      type: "int"
      constraints: "Default 80 pixels"
```

### 9.2 Storage

#### 9.2.1 Device Store

```yaml
storage:
  name: "devices.yaml"
  location: "~/.config/gtach/devices.yaml"
  format: "YAML"
  fields:
    - name: "primary_device"
      type: "BluetoothDevice"
      constraints: "Single device, nullable"
    - name: "secondary_devices"
      type: "List[BluetoothDevice]"
      constraints: "Backup devices"
    - name: "setup_complete"
      type: "bool"
      constraints: "Setup wizard completion flag"
```

#### 9.2.2 Configuration

```yaml
storage:
  name: "config.yaml"
  location_hierarchy:
    - "$GTACH_CONFIG (environment)"
    - "~/.config/gtach/config.yaml (user)"
    - "/etc/gtach/config.yaml (system)"
    - "Built-in defaults"
  format: "YAML"
  sections:
    - "obd: port, baudrate, timeout, reconnect_attempts"
    - "bluetooth: scan_timeout, connect_timeout, auto_reconnect"
    - "display: mode, fps_limit, rpm_warning, rpm_danger"
    - "session: debug, log_retention_days"
```

### 9.3 Validation Rules

- MAC addresses validated against standard format regex
- RPM values constrained to 0-15000 range
- Configuration values type-checked with fallback to defaults
- Device names sanitized for filesystem safety

[Return to Table of Contents](<#table of contents>)

---

## 10.0 Interfaces

### 10.1 Internal Interfaces

#### 10.1.1 ThreadManager Interface

```python
class ThreadManager:
    def register_thread(self, name: str, thread: threading.Thread) -> bool
    def start_thread(self, name: str) -> bool
    def stop_thread(self, name: str, timeout: float = 5.0) -> bool
    def get_thread_status(self, name: str) -> Optional[ThreadStatus]
    def update_heartbeat(self, name: str) -> None
    def submit_task(self, func: Callable, *args, **kwargs) -> Future
    def shutdown(self) -> None
```

#### 10.1.2 BluetoothManager Interface

```python
class BluetoothManager:
    async def scan_devices(self, timeout: float = 10.0) -> List[BluetoothDevice]
    async def connect(self, device: BluetoothDevice) -> bool
    async def disconnect(self) -> None
    async def send_command(self, command: str) -> str
    def get_state(self) -> BluetoothState
    def start(self) -> None
    def stop(self) -> None
```

#### 10.1.3 DisplayManager Interface

```python
class DisplayManager:
    def start(self) -> None
    def stop(self) -> None
    def set_mode(self, mode: DisplayMode) -> None
    def update_rpm(self, rpm: int) -> None
    def set_setup_mode(self, setup_manager: SetupDisplayManager) -> None
    def register_touch_callback(self, callback: Callable) -> None
```

### 10.2 External Interfaces

#### 10.2.1 ELM327 OBD-II Protocol

```yaml
interface:
  name: "ELM327 AT Commands"
  protocol: "Serial over Bluetooth RFCOMM"
  data_format: "ASCII text with CR termination"
  commands:
    - "ATZ: Reset adapter"
    - "ATE0: Echo off"
    - "ATSP0: Auto protocol detection"
    - "ATSP8: ISO 15765-4 CAN (29-bit, 500 kbaud)"
    - "010C: Request engine RPM"
  response_format: "Hex bytes followed by > prompt"
```

#### 10.2.2 Framebuffer Interface

```yaml
interface:
  name: "Linux Framebuffer"
  protocol: "Direct memory-mapped I/O"
  device: "/dev/fb0"
  data_format: "Raw pixel data (RGB565 or RGB888)"
  operations:
    - "Memory map framebuffer"
    - "Write pixel data"
    - "Page flip (double buffering)"
```

[Return to Table of Contents](<#table of contents>)

---

## 11.0 Error Handling

### 11.1 Exception Hierarchy

```
Exception
├── GTachError (base)
│   ├── ConfigurationError
│   │   ├── ConfigFileNotFoundError
│   │   └── ConfigValidationError
│   ├── BluetoothError
│   │   ├── BluetoothConnectionError
│   │   ├── BluetoothTimeoutError
│   │   └── DeviceNotFoundError
│   ├── OBDError
│   │   ├── OBDConnectionError
│   │   ├── OBDProtocolError
│   │   └── OBDResponseError
│   ├── DisplayError
│   │   ├── FramebufferError
│   │   └── RenderingError
│   └── PlatformError
│       └── HardwareNotAvailableError
```

### 11.2 Error Strategy

| Error Type | Handling Strategy |
|------------|-------------------|
| Validation Errors | Log warning, use default values, continue operation |
| Bluetooth Failures | Exponential backoff retry (3 attempts), enter scanning mode |
| OBD Timeouts | Retry with increased timeout, reconnect on 3 consecutive failures |
| Display Errors | Graceful degradation to console mode if framebuffer unavailable |
| Thread Failures | Automatic restart via WatchdogMonitor with backoff |
| Configuration Errors | Fall back to built-in defaults, log warning |

### 11.3 Logging Configuration

```yaml
logging:
  levels:
    - "DEBUG: Development diagnostics (conditional on debug flag)"
    - "INFO: Operational events (production default)"
    - "WARNING: Recoverable issues"
    - "ERROR: Failures requiring attention"
    - "CRITICAL: System-wide failures"
  required_info:
    - "Timestamp (ISO 8601)"
    - "Logger name (module path)"
    - "Log level"
    - "Message"
    - "Exception traceback (for errors)"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  session_based: "Debug logs written to session-specific files"
```

[Return to Table of Contents](<#table of contents>)

---

## 12.0 Non-Functional Requirements

### 12.1 Performance

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Display Refresh Rate | ≥30 FPS on Pi, ≥60 FPS development | PerformanceMonitor frame timing |
| RPM Update Latency | <100ms end-to-end | Timestamp correlation |
| Memory Usage | <256MB resident | /proc/meminfo monitoring |
| Startup Time | <10 seconds to display | Timed from process start |
| CPU Usage | <50% average on Pi Zero 2W | top/htop monitoring |

### 12.2 Reliability

```yaml
reliability:
  error_recovery: "Automatic thread restart with exponential backoff"
  fault_tolerance:
    - "Watchdog monitoring with escalating recovery"
    - "Graceful degradation to mock implementations"
    - "Connection retry with exponential backoff"
    - "Configuration fallback hierarchy"
  availability_target: "99% uptime during vehicle operation"
```

### 12.3 Security

```yaml
security:
  authentication: "N/A (local device only)"
  authorization: "Linux user permissions for hardware access"
  data_protection:
    - "No sensitive data stored"
    - "Configuration files readable only by owner"
    - "No network connectivity beyond Bluetooth"
```

### 12.4 Maintainability

```yaml
maintainability:
  code_organization:
    - "Domain-driven directory structure"
    - "Single responsibility per module"
    - "Interface-based component coupling"
  documentation:
    - "Comprehensive docstrings (Google style)"
    - "Type hints throughout"
    - "Design documents per governance.md"
  testing:
    coverage_target: "80% line coverage"
    approaches:
      - "Unit tests with mocked dependencies"
      - "Integration tests on target platform"
      - "Manual system tests for UI"
```

[Return to Table of Contents](<#table of contents>)

---

## 13.0 Visual Documentation

### 13.1 System Architecture Diagram

```mermaid
graph TB
    subgraph "GTach Application"
        APP[GTachApplication]
        
        subgraph "Core Domain"
            TM[ThreadManager]
            WD[WatchdogMonitor]
            ASB[AsyncSyncBridge]
        end
        
        subgraph "Communication Domain"
            BT[BluetoothManager]
            OBD[OBDProtocol]
            DS[DeviceStore]
        end
        
        subgraph "Display Domain"
            DM[DisplayManager]
            RE[RenderingEngine]
            TC[TouchCoordinator]
            PM[PerformanceMonitor]
        end
        
        subgraph "Utilities Domain"
            CM[ConfigManager]
            PD[PlatformDetector]
            TR[TerminalRestorer]
        end
    end
    
    subgraph "External Systems"
        ECU[Vehicle ECU]
        ELM[ELM327 Adapter]
        FB[Framebuffer /dev/fb0]
        TS[Touch Screen]
    end
    
    ECU -->|OBD-II| ELM
    ELM -->|Bluetooth| BT
    BT --> OBD
    OBD --> DM
    DM --> RE
    RE --> FB
    TS --> TC
    TC --> DM
    
    APP --> TM
    APP --> WD
    APP --> BT
    APP --> OBD
    APP --> DM
    APP --> CM
    
    TM --> ASB
    WD --> TM
    BT --> DS
    BT --> TM
    OBD --> TM
    DM --> TM
    DM --> TR
```

### 13.2 Thread State Machine

```mermaid
stateDiagram-v2
    [*] --> STARTING: register_thread()
    STARTING --> RUNNING: start successful
    STARTING --> FAILED: start error
    STARTING --> STOPPING: stop requested
    
    RUNNING --> STOPPING: stop requested
    RUNNING --> FAILED: runtime error
    RUNNING --> RESTARTING: watchdog recovery
    
    STOPPING --> STOPPED: cleanup complete
    STOPPING --> FAILED: cleanup error
    
    STOPPED --> STARTING: restart
    STOPPED --> [*]: unregister
    
    FAILED --> RESTARTING: watchdog recovery
    FAILED --> STOPPING: forced stop
    FAILED --> STOPPED: cleanup complete
    
    RESTARTING --> STARTING: restart initiated
    RESTARTING --> FAILED: restart error
    RESTARTING --> STOPPED: max restarts exceeded
```

### 13.3 Bluetooth State Machine

```mermaid
stateDiagram-v2
    [*] --> DISCONNECTED
    
    DISCONNECTED --> SCANNING: scan_devices()
    DISCONNECTED --> CONNECTING: connect() with known device
    
    SCANNING --> DISCONNECTED: scan complete/timeout
    SCANNING --> CONNECTING: device selected
    
    CONNECTING --> CONNECTED: connection success
    CONNECTING --> DISCONNECTED: connection failed
    CONNECTING --> ERROR: critical error
    
    CONNECTED --> DISCONNECTED: disconnect() or lost
    CONNECTED --> ERROR: protocol error
    
    ERROR --> DISCONNECTED: reset
    ERROR --> SCANNING: retry
```

### 13.4 Display Mode Flow

```mermaid
stateDiagram-v2
    [*] --> SPLASH: application start
    
    SPLASH --> DIGITAL: splash timeout (setup complete)
    SPLASH --> SETUP: splash timeout (setup needed)
    
    SETUP --> DIGITAL: setup complete
    
    DIGITAL --> GAUGE: swipe gesture
    DIGITAL --> SETTINGS: long press
    
    GAUGE --> DIGITAL: swipe gesture
    GAUGE --> SETTINGS: long press
    
    SETTINGS --> DIGITAL: back gesture
    SETTINGS --> GAUGE: mode select
```

### 13.5 Data Flow Diagram

```mermaid
flowchart LR
    subgraph "Vehicle"
        ECU[Engine ECU]
    end
    
    subgraph "OBD Adapter"
        ELM[ELM327]
    end
    
    subgraph "GTach Application"
        BT[BluetoothManager]
        OBD[OBDProtocol]
        Q[Data Queue]
        DM[DisplayManager]
        RE[RenderingEngine]
    end
    
    subgraph "Hardware"
        FB[Framebuffer]
        DISP[Display]
    end
    
    ECU -->|CAN Bus| ELM
    ELM -->|Bluetooth RFCOMM| BT
    BT -->|Raw Response| OBD
    OBD -->|Parsed RPM| Q
    Q -->|Read| DM
    DM -->|Render Commands| RE
    RE -->|Pixel Data| FB
    FB -->|Video Signal| DISP
```

[Return to Table of Contents](<#table of contents>)

---

## 14.0 Tier 2 Domain Documents

The following Tier 2 domain design documents decompose each domain:

| Document | Domain | Status |
|----------|--------|--------|
| [design-4f8a2b1c-domain_core.md](<design-4f8a2b1c-domain_core.md>) | Core (Threading/Watchdog) | Complete |
| [design-7d3e9f5a-domain_comm.md](<design-7d3e9f5a-domain_comm.md>) | Communication (Bluetooth/OBD) | Complete |
| [design-2c6b8e4d-domain_display.md](<design-2c6b8e4d-domain_display.md>) | Display (Rendering/Touch) | Complete |
| [design-9a1f3c7e-domain_utils.md](<design-9a1f3c7e-domain_utils.md>) | Utilities (Config/Platform) | Complete |
| [design-5b2d4e6f-domain_provisioning.md](<design-5b2d4e6f-domain_provisioning.md>) | Provisioning (Deployment) | Complete |

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-29 | William Watson | Initial master design document created via reverse engineering of existing source code |
| 1.1 | 2025-12-29 | William Watson | Added Tier 2 domain document cross-references (Core, Comm, Display, Utils, Provisioning) |

---

Copyright (c) 2025 William Watson. This work is licensed under the MIT License.
