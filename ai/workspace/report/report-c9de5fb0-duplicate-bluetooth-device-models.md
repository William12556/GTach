Created: 2026 October 09

# Report: Single Bluetooth Device Conversion

---

## Table of Contents

1. [Summary](<#1. summary>)
2. [Files Changed](<#2. files changed>)
3. [Tests and Result](<#3. tests and result>)
4. [Success Criteria](<#4. success criteria>)
5. [Deviations](<#5. deviations>)
6. [Items Kept](<#6. items kept>)
7. [On-Device Verification Outstanding](<#7. on-device verification outstanding>)
8. [Version History](<#version history>)

---

## 1. Summary

prompt-c9de5fb0 (change-c9de5fb0, issue-c9de5fb0) is implemented. `gtach.comm.models` gains a `DiscoveredDevice` `typing.Protocol` (name, mac_address, device_type) and `BluetoothDevice.from_discovered(device)`. Both hand-written setup → comm conversions now call it.

[Return to Table of Contents](<#table of contents>)

---

## 2. Files Changed

| File | Change |
|---|---|
| `src/gtach/comm/models.py` | New `DiscoveredDevice` Protocol; new classmethod `BluetoothDevice.from_discovered`. |
| `src/gtach/display/setup_components/bluetooth/interface.py` | Pairing-success path uses `CommBluetoothDevice.from_discovered(device)`. |
| `src/gtach/comm/sim_bluetooth.py` | `SimBluetoothPairing.pair_device` uses `CommBluetoothDevice.from_discovered(device)`. |
| `tests/test_bluetooth_device_conversion.py` | New: 3 tests. |

[Return to Table of Contents](<#table of contents>)

---

## 3. Tests and Result

New tests: setup model converts with upper-cased MAC and `last_connected` None; a `SimpleNamespace` with the three attributes converts; `device_type 'UNKNOWN'` with "OBD" in the name is classified `OBD` by `__post_init__`.

- Before: 553 passed.
- After: 556 passed.
- mypy error count unchanged (338).

[Return to Table of Contents](<#table of contents>)

---

## 4. Success Criteria

| Criterion | Result |
|---|---|
| No `CommBluetoothDevice(` in `src/gtach` | Met |
| No display import in `comm/models.py` | Met |
| `pytest tests/` passes | Met |

[Return to Table of Contents](<#table of contents>)

---

## 5. Deviations

None.

[Return to Table of Contents](<#table of contents>)

---

## 6. Items Kept

- Both dataclasses' fields are unchanged.
- Each call site keeps its `CommBluetoothDevice` import alias and its surrounding try/except; the comment above the interface.py call is kept.

[Return to Table of Contents](<#table of contents>)

---

## 7. On-Device Verification Outstanding

- On the Pi, pair a device in setup; confirm it is saved (`devices` file under GTACH_HOME) and reconnects after `systemctl restart gtach`.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-09 | Initial report for prompt-c9de5fb0. |

---

Copyright (c) 2026 William Watson. MIT License.
