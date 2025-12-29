# Component Design: ConfigManager

Created: 2025-12-29

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [2.0 Component Overview](<#2.0 component overview>)
- [3.0 Class Design](<#3.0 class design>)
- [4.0 Method Specifications](<#4.0 method specifications>)
- [5.0 Configuration Hierarchy](<#5.0 configuration hierarchy>)
- [6.0 Thread Safety](<#6.0 thread safety>)
- [7.0 Error Handling](<#7.0 error handling>)
- [8.0 Visual Documentation](<#8.0 visual documentation>)
- [Version History](<#version history>)

---

## 1.0 Document Information

```yaml
document_info:
  document_id: "design-b4c5d6e7-component_utils_config_manager"
  tier: 3
  domain: "Utilities"
  component: "ConfigManager"
  parent: "design-9a1f3c7e-domain_utils.md"
  source_file: "src/gtach/utils/config.py"
  version: "1.0"
  date: "2025-12-29"
  author: "William Watson"
```

### 1.1 Parent Reference

- **Domain Design**: [design-9a1f3c7e-domain_utils.md](<design-9a1f3c7e-domain_utils.md>)
- **Master Design**: [design-0000-master_gtach.md](<design-0000-master_gtach.md>)

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Component Overview

### 2.1 Purpose

ConfigManager provides a thread-safe singleton for application configuration management with YAML persistence, validation, and session-based debug logging.

### 2.2 Responsibilities

1. Load configuration from YAML file hierarchy
2. Provide thread-safe read/write access via RWLock
3. Validate configuration against constraints
4. Support atomic transactions with rollback
5. Enable session-based debug logging
6. Persist changes to YAML file

### 2.3 Singleton Pattern

ConfigManager uses double-checked locking to ensure exactly one instance exists application-wide, providing a single source of truth for configuration.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Class Design

### 3.1 ConfigManager Class

```python
class ConfigManager:
    """Thread-safe singleton configuration manager.
    
    Provides concurrent read access with exclusive write access
    via RWLock synchronization.
    """
    
    _instance: Optional['ConfigManager'] = None
    _instance_lock: threading.Lock = threading.Lock()
```

### 3.2 get_instance (Singleton Access)

```python
@classmethod
def get_instance(cls) -> 'ConfigManager':
    """Get singleton instance with double-checked locking.
    
    Returns:
        ConfigManager singleton instance
    
    Thread Safety:
        Uses double-checked locking pattern
    """
    if cls._instance is None:
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = cls()
    return cls._instance
```

### 3.3 Constructor (Private)

```python
def __init__(self) -> None:
    """Initialize config manager (use get_instance()).
    
    Raises:
        RuntimeError: If called directly after instance exists
    """
```

### 3.4 Attributes

| Attribute | Type | Purpose |
|-----------|------|---------|
| `_config` | `OBDConfig` | Current configuration |
| `_rw_lock` | `RWLock` | Read-write lock |
| `_config_path` | `Path` | Active config file path |
| `_session_id` | `Optional[str]` | Debug session identifier |
| `_log_file` | `Optional[Path]` | Session log file path |
| `_validators` | `List[ConfigValidator]` | Validation rules |
| `_callbacks` | `List[Callable]` | Change observers |

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Method Specifications

### 4.1 get_config

```python
def get_config(self) -> OBDConfig:
    """Get configuration copy (thread-safe read).
    
    Returns:
        Deep copy of current OBDConfig
    
    Thread Safety:
        Acquires read lock
    """
```

### 4.2 get_bluetooth_config / get_display_config

```python
def get_bluetooth_config(self) -> BluetoothConfig:
    """Get Bluetooth configuration section."""

def get_display_config(self) -> DisplayConfig:
    """Get display configuration section."""
```

### 4.3 update_config

```python
def update_config(self, updates: Dict[str, Any]) -> bool:
    """Update configuration (thread-safe write).
    
    Args:
        updates: Dictionary of updates (nested keys supported)
    
    Returns:
        True if update successful
    
    Thread Safety:
        Acquires write lock
    
    Algorithm:
        1. Acquire write lock
        2. Create backup of current config
        3. Apply updates
        4. Validate new configuration
        5. If valid: save to file, notify callbacks
        6. If invalid: restore backup, return False
        7. Release lock
    """
```

### 4.4 begin_transaction

```python
def begin_transaction(self) -> ConfigTransaction:
    """Begin atomic configuration transaction.
    
    Returns:
        ConfigTransaction context manager
    
    Usage:
        with config_manager.begin_transaction() as txn:
            txn.set('bluetooth.timeout', 15.0)
            txn.set('display.fps_limit', 30)
            # Automatically commits on exit, rollback on exception
    """
```

### 4.5 validate

```python
def validate(self) -> Dict[str, Any]:
    """Validate current configuration.
    
    Returns:
        Dict with 'valid' bool and 'errors' list
    """
```

### 4.6 Session Logging

```python
def enable_debug_logging(self, session_id: str = None) -> str:
    """Enable session-based debug logging.
    
    Args:
        session_id: Optional custom session ID (generates UUID if None)
    
    Returns:
        Session ID
    
    Creates:
        Log file at ~/.config/gtach/logs/session_<id>.log
    """

def get_log_file_path(self) -> Optional[Path]:
    """Get current session log file path."""
```

### 4.7 reload

```python
def reload(self) -> bool:
    """Reload configuration from file.
    
    Returns:
        True if reload successful
    
    Thread Safety:
        Acquires write lock during reload
    """
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Configuration Hierarchy

### 5.1 Resolution Order

```
1. $GTACH_CONFIG environment variable (if set)
2. ~/.config/gtach/config.yaml (user config)
3. /etc/gtach/config.yaml (system config)
4. Built-in defaults
```

### 5.2 OBDConfig Structure

```python
@dataclass
class OBDConfig:
    """Root configuration container."""
    bluetooth: BluetoothConfig
    display: DisplayConfig
    session: SessionConfig

@dataclass
class BluetoothConfig:
    scan_duration: float = 10.0
    connection_timeout: float = 10.0
    command_timeout: float = 2.0
    retry_limit: int = 3
    retry_delay: float = 3.0

@dataclass
class DisplayConfig:
    mode: str = "DIGITAL"
    rpm_warning: int = 6500
    rpm_danger: int = 7000
    fps_limit: int = 60

@dataclass
class SessionConfig:
    debug_mode: bool = False
    log_level: str = "INFO"
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Thread Safety

### 6.1 RWLock Implementation

```python
class RWLock:
    """Reader-writer lock allowing multiple readers or single writer."""
    
    def __init__(self):
        self._read_ready = threading.Condition(threading.Lock())
        self._readers = 0
    
    def acquire_read(self) -> None:
        """Acquire read lock (blocks if writer active)."""
    
    def release_read(self) -> None:
        """Release read lock."""
    
    def acquire_write(self) -> None:
        """Acquire write lock (blocks until no readers/writers)."""
    
    def release_write(self) -> None:
        """Release write lock."""
```

### 6.2 Context Managers

```python
@contextmanager
def read_lock(self):
    """Context manager for read access."""
    self._rw_lock.acquire_read()
    try:
        yield
    finally:
        self._rw_lock.release_read()

@contextmanager
def write_lock(self):
    """Context manager for write access."""
    self._rw_lock.acquire_write()
    try:
        yield
    finally:
        self._rw_lock.release_write()
```

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Error Handling

### 7.1 Exception Strategy

| Scenario | Handling |
|----------|----------|
| YAML not available | Use defaults, log warning |
| File not found | Use defaults, create on save |
| Parse error | Use defaults, log error |
| Validation failure | Reject update, return errors |
| Save failure | Log error, data in memory |

### 7.2 ConfigTransaction Rollback

```python
class ConfigTransaction:
    """Atomic configuration transaction with rollback."""
    
    def __enter__(self):
        self._snapshot = copy.deepcopy(self._config)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # Rollback on exception
            self._config = self._snapshot
            return False
        # Commit changes
        self._manager._save()
        return True
```

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Visual Documentation

### 8.1 Class Diagram

```mermaid
classDiagram
    class ConfigManager {
        -OBDConfig _config
        -RWLock _rw_lock
        -Path _config_path
        -str _session_id
        +get_instance() ConfigManager
        +get_config() OBDConfig
        +update_config(updates) bool
        +begin_transaction() ConfigTransaction
        +validate() Dict
        +enable_debug_logging(id) str
        +reload() bool
    }
    
    class RWLock {
        -Condition _read_ready
        -int _readers
        +acquire_read()
        +release_read()
        +acquire_write()
        +release_write()
    }
    
    class ConfigTransaction {
        -ConfigManager _manager
        -OBDConfig _snapshot
        +set(key, value)
        +get(key) Any
        +commit()
        +rollback()
    }
    
    class OBDConfig {
        +BluetoothConfig bluetooth
        +DisplayConfig display
        +SessionConfig session
    }
    
    ConfigManager *-- RWLock
    ConfigManager *-- OBDConfig
    ConfigManager --> ConfigTransaction
```

### 8.2 Read-Write Lock Sequence

```mermaid
sequenceDiagram
    participant R1 as Reader 1
    participant R2 as Reader 2
    participant W as Writer
    participant RWL as RWLock
    
    R1->>RWL: acquire_read()
    RWL-->>R1: granted
    R2->>RWL: acquire_read()
    Note over RWL: Multiple readers OK
    RWL-->>R2: granted
    
    W->>RWL: acquire_write()
    Note over RWL: Writer waits
    
    R1->>RWL: release_read()
    R2->>RWL: release_read()
    
    RWL-->>W: granted (exclusive)
    W->>W: modify config
    W->>RWL: release_write()
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-29 | William Watson | Initial component design document |

---

Copyright (c) 2025 William Watson. This work is licensed under the MIT License.
