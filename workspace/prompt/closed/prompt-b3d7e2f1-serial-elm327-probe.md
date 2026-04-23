# Prompt: SerialTransport ELM327 ATZ Probe Validation

Created: 2026 April 17

---

## Table of Contents

- [1.0 Prompt Information](<#1.0 prompt information>)
- [2.0 Context](<#2.0 context>)
- [3.0 Specification](<#3.0 specification>)
- [4.0 Design](<#4.0 design>)
- [5.0 Current Source](<#5.0 current source>)
- [6.0 Error Handling](<#6.0 error handling>)
- [7.0 Testing](<#7.0 testing>)
- [8.0 Deliverable](<#8.0 deliverable>)
- [9.0 Success Criteria](<#9.0 success criteria>)
- [10.0 Element Registry](<#10.0 element registry>)
- [Version History](<#version history>)

---

## 1.0 Prompt Information

```yaml
prompt_info:
  id: "prompt-b3d7e2f1"
  task_type: "code_generation"
  source_ref: "change-b3d7e2f1"
  date: "2026-04-17"
  iteration: 1
  coupled_docs:
    change_ref: "change-b3d7e2f1"
    change_iteration: 1
```

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Context

```yaml
context:
  purpose: >
    Add ELM327 ATZ probe validation to SerialTransport._discover_port().
    A new private method _probe_port(device) sends ATZ\r to each name-matched
    candidate serial port and accepts it only if the response contains "ELM327".
    This prevents GTach from connecting to phantom macOS Bluetooth SPP virtual
    ports that match the OBD name pattern but yield no ELM327 responses.
  integration: >
    Single file change: src/gtach/comm/serial_transport.py.
    _discover_port() calls _probe_port() after the existing name-pattern match.
    connect() and all other methods are unchanged.
  knowledge_references: []
  constraints:
    - "Only serial_transport.py is modified. No other files."
    - "connect(), disconnect(), send_command(), is_connected() are not modified."
    - "OBDTransport ABC and transport.py are not modified."
    - "Probe uses a dedicated serial.Serial instance, closed before returning."
    - "Probe timeout is 2 seconds. Must not stall discovery unreasonably."
    - "ATZ reset of the adapter during probe is acceptable and harmless."
    - "Python 3.9+. pyserial >= 3.5 already a project dependency."
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Specification

```yaml
specification:
  description: >
    Modify SerialTransport._discover_port() to validate each name-matched
    candidate port via an ATZ probe before returning it. Add private method
    _probe_port(device: str) -> bool implementing the probe.
  requirements:
    functional:
      - "_probe_port(device) opens the port, sends ATZ\\r, reads until b'>', returns True if 'ELM327' in response."
      - "_probe_port returns False on SerialException, timeout, or missing 'ELM327'."
      - "_probe_port always closes the port before returning, regardless of outcome."
      - "_discover_port() calls _probe_port() after each name-pattern match."
      - "_discover_port() logs a DEBUG message when a port is probed."
      - "_discover_port() logs an INFO message when a port passes the probe."
      - "_discover_port() logs a WARNING message when a port fails the probe and is skipped."
      - "_discover_port() returns None if no candidate passes the probe (existing behaviour)."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "PEP 8 style"
        - "Google-style docstring on _probe_port"
        - "Thread-safe: _probe_port uses only local variables, no shared state"
        - "No new imports required beyond those already present"
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Design

```yaml
design:
  architecture: >
    Single new private method _probe_port inserted in SerialTransport.
    _discover_port() modified to call _probe_port after pattern match.
    All other methods unchanged.

  components:
    - name: "_probe_port"
      type: "method"
      purpose: >
        Open a candidate serial port, send ATZ\r, read response, verify
        it contains "ELM327". Close port unconditionally before returning.
      interface:
        inputs:
          - name: "device"
            type: "str"
            description: "Device path e.g. /dev/cu.ELM327-xxx"
        outputs:
          type: "bool"
          description: "True if ELM327 response received, False otherwise"
        raises: []
      logic:
        - "Open serial.Serial(device, self._baudrate, timeout=2)"
        - "Write b'ATZ\\r' to port"
        - "Read until b'>' with 2s timeout"
        - "Decode response as ASCII ignoring errors"
        - "Return True if 'ELM327' in response.upper()"
        - "Catch serial.SerialException and any Exception; return False"
        - "Always close port in finally block"

    - name: "_discover_port (modified)"
      type: "method"
      purpose: >
        Existing method — add _probe_port call after each name-pattern match.
        Return device only if probe passes. Continue loop if probe fails.
      logic:
        - "Existing tty.* skip on Darwin — unchanged"
        - "Existing pattern match on device_name_lower and description_lower — unchanged"
        - "After a pattern match: call _probe_port(device_name)"
        - "If _probe_port True: log INFO 'ELM327 probe passed on <port>', return device_name"
        - "If _probe_port False: log WARNING 'Port <port> matched pattern but failed ELM327 probe — skipping', continue"
        - "End of loop: log INFO 'No OBD device found' (existing), return None"

  dependencies:
    internal:
      - "serial (pyserial) — already imported"
      - "logging — already imported"
    external: []
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Current Source

The complete current content of `src/gtach/comm/serial_transport.py` is provided
below for reference. Modify only `_discover_port` and add `_probe_port`.

```python
#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Serial Transport Implementation

This module provides an implementation of the OBDTransport interface using
serial communication for direct connection to an ELM327 OBD-II adapter.
"""

import logging
import platform
import threading
from typing import Optional

import serial
from serial.tools import list_ports

from .transport import OBDTransport, TransportState, TransportError


class SerialTransport(OBDTransport):
    """Serial transport implementation for direct UART communication."""
    
    def __init__(self, port: Optional[str] = None, baudrate: int = 38400, retry_delay: float = 5.0):
        super().__init__()
        self._port = port
        self._baudrate = baudrate
        self._retry_delay = retry_delay
        self._serial = None
        self._state = TransportState.DISCONNECTED
    
    def connect(self) -> bool:
        """Establish a serial connection to the OBD device."""
        logger = logging.getLogger('SerialTransport')
        with self._lock:
            self._state = TransportState.CONNECTING
        
        resolved_port = self._port
        if resolved_port is None:
            resolved_port = self._discover_port()
        
        if resolved_port is None:
            logger.warning("No serial port found")
            with self._lock:
                self._state = TransportState.DISCONNECTED
            return False
        
        try:
            self._serial = serial.Serial(
                port=resolved_port,
                baudrate=self._baudrate,
                timeout=2
            )
            with self._lock:
                self._state = TransportState.CONNECTED
            logger.info("Connected to serial device %s at %d baud", resolved_port, self._baudrate)
            return True
        except serial.SerialException as e:
            logger.error("Failed to connect to serial device %s: %s", resolved_port, e)
            self._close_serial()
            with self._lock:
                self._state = TransportState.DISCONNECTED
            return False
        except Exception as e:
            logger.error("Unexpected error during serial connection: %s", e)
            self._close_serial()
            with self._lock:
                self._state = TransportState.ERROR
            return False
    
    def disconnect(self) -> None:
        """Close the serial connection."""
        logger = logging.getLogger('SerialTransport')
        self._shutdown.set()
        with self._lock:
            self._close_serial()
            self._state = TransportState.DISCONNECTED
        logger.info("Disconnected from serial device")
    
    def send_command(self, command: str, timeout: float = 2.0) -> Optional[str]:
        """Send a command to the OBD device and receive the response."""
        logger = logging.getLogger('SerialTransport')
        if not self.is_connected():
            logger.warning("Cannot send command: transport is not connected")
            return None
        try:
            encoded_cmd = (command.strip() + '\r').encode('ascii')
            self._serial.write(encoded_cmd)
            self._serial.timeout = timeout
            response = self._serial.read_until(b'>')
            decoded_response = response.decode('ascii', errors='ignore').strip()
            decoded_response = decoded_response.rstrip('>').strip()
            return decoded_response
        except serial.SerialException as e:
            logger.error("Error communicating with device: %s", e)
            with self._lock:
                self._state = TransportState.DISCONNECTED
            self._close_serial()
            return None
        except Exception as e:
            logger.error("Unexpected error during command send: %s", e)
            return None
    
    def is_connected(self) -> bool:
        """Check if the transport is currently connected."""
        with self._lock:
            return self._state == TransportState.CONNECTED
    
    @property
    def state(self) -> TransportState:
        """Get the current state of the transport."""
        with self._lock:
            return self._state
    
    def _discover_port(self) -> Optional[str]:
        """Discover available serial ports matching known OBD adapter patterns."""
        logger = logging.getLogger('SerialTransport')
        patterns = ['ELM', 'OBD', 'OBDII']
        
        for port in list_ports.comports():
            if platform.system() == 'Darwin' and '/dev/tty.' in port.device:
                continue
            device_name = port.device
            description = getattr(port, 'description', '')
            device_name_lower = device_name.lower()
            description_lower = description.lower()
            if any(pattern.lower() in device_name_lower for pattern in patterns):
                logger.info("Found OBD device on port %s", device_name)
                return device_name
            if any(pattern.lower() in description_lower for pattern in patterns):
                logger.info("Found OBD device (description: %s) on port %s", description, device_name)
                return device_name
        
        logger.info("No OBD device found in available serial ports")
        return None
    
    def _close_serial(self) -> None:
        """Close the serial connection if it is open."""
        if self._serial:
            try:
                if self._serial.is_open:
                    self._serial.close()
            except serial.SerialException:
                pass
            finally:
                self._serial = None
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Error Handling

```yaml
error_handling:
  strategy: >
    _probe_port catches all exceptions and returns False. Probe failures are
    non-fatal; discovery continues to the next candidate. No exception
    propagates out of _probe_port.
  exceptions:
    - exception: "serial.SerialException"
      condition: "Port cannot be opened or read fails"
      handling: "Log DEBUG, return False"
    - exception: "Exception"
      condition: "Any other unexpected error during probe"
      handling: "Log DEBUG with message, return False"
  logging:
    level: "DEBUG for probe open/fail; INFO for probe pass; WARNING for pattern match + probe fail"
    format: "logging.getLogger('SerialTransport')"
```

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Testing

```yaml
testing:
  unit_tests:
    - scenario: "Port responds with ELM327 version string"
      expected: "_probe_port returns True"
    - scenario: "Port responds with unrecognised string (no ELM327)"
      expected: "_probe_port returns False"
    - scenario: "Port raises SerialException on open"
      expected: "_probe_port returns False, no exception raised"
    - scenario: "Port times out (read_until returns empty)"
      expected: "_probe_port returns False"
    - scenario: "_discover_port — one candidate, probe passes"
      expected: "device path returned"
    - scenario: "_discover_port — one candidate, probe fails"
      expected: "None returned"
    - scenario: "_discover_port — two candidates, first fails probe, second passes"
      expected: "second device path returned"
  edge_cases:
    - "Response contains ELM327 in mixed case (e.g. 'elm327')"
    - "Port opens but immediately closes (OSError on write)"
    - "Empty response from read_until (timeout with no data)"
  validation:
    - "Port is always closed after probe regardless of outcome"
    - "No shared state modified by _probe_port"
```

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Deliverable

```yaml
deliverable:
  format_requirements:
    - "Save generated code directly to the specified path."
    - "Preserve all existing methods and docstrings exactly."
    - "Only _discover_port and the new _probe_port are modified/added."
  files:
    - path: "src/gtach/comm/serial_transport.py"
      content: "Full file with _probe_port added and _discover_port modified."
```

[Return to Table of Contents](<#table of contents>)

---

## 9.0 Success Criteria

```yaml
success_criteria:
  - "_probe_port(device) method added to SerialTransport."
  - "_probe_port sends ATZ\\r, reads until '>', returns True iff 'ELM327' in response."
  - "_probe_port closes port in finally block unconditionally."
  - "_probe_port catches all exceptions and returns False without propagating."
  - "_discover_port calls _probe_port after each name-pattern match."
  - "_discover_port skips and logs WARNING for ports that fail probe."
  - "_discover_port returns None if no candidate passes (existing behaviour preserved)."
  - "connect(), disconnect(), send_command(), is_connected() are byte-for-byte unchanged."
  - "No new imports added."
  - "File saved to src/gtach/comm/serial_transport.py."
```

[Return to Table of Contents](<#table of contents>)

---

## 10.0 Element Registry

```yaml
element_registry:
  source: "workspace/design/design-gtach-master.md"
  entries:
    modules:
      - name: "serial_transport"
        path: "src/gtach/comm/serial_transport.py"
    classes:
      - name: "SerialTransport"
        module: "serial_transport"
    functions:
      - name: "_discover_port"
        module: "serial_transport"
        signature: "_discover_port(self) -> Optional[str]"
      - name: "_probe_port"
        module: "serial_transport"
        signature: "_probe_port(self, device: str) -> bool"
      - name: "_close_serial"
        module: "serial_transport"
        signature: "_close_serial(self) -> None"
```

[Return to Table of Contents](<#table of contents>)

---

## tactical_brief

```yaml
tactical_brief: >
  File to modify: src/gtach/comm/serial_transport.py

  Task: Add ELM327 ATZ probe validation to SerialTransport port discovery.

  Changes required (two only):

  1. Add new private method _probe_port(self, device: str) -> bool
     - Open serial.Serial(device, self._baudrate, timeout=2)
     - Write b"ATZ\r"
     - Read until b">" with 2s timeout
     - Return True if "ELM327" in decoded response (case-insensitive)
     - Return False on SerialException, any Exception, or missing "ELM327"
     - Always close port in finally block
     - Use logging.getLogger('SerialTransport') for debug messages
     - Google-style docstring

  2. Modify _discover_port(self) — after each name-pattern match block
     that would have returned device_name, instead:
     - Call self._probe_port(device_name)
     - If True: log INFO "ELM327 probe passed on <device>", return device_name
     - If False: log WARNING "Port <device> matched pattern but failed ELM327 probe — skipping", continue loop
     - Apply to BOTH pattern-match branches (device_name and description)

  Hard constraints:
  - connect(), disconnect(), send_command(), is_connected(), _close_serial() unchanged
  - No new imports
  - Port must be closed in finally block in _probe_port

  Success: File saved. _probe_port present. _discover_port calls probe after match.
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date       | Author         | Changes                 |
| ------- | ---------- | -------------- | ----------------------- |
| 1.0     | 2026-04-17 | William Watson | Initial prompt creation |
| 1.1     | 2026-04-22 | William Watson | Code generated and verified — closing |

---

Copyright (c) 2026 William Watson. MIT License.
