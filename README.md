# GTach - Retro styled OBD-II/ELM327 based Tachometer

**Created**: 2025 08 08

## Overview

GTach is an experimental embedded application under development for Raspberry Pi deployment with a Pimoroni HyperPixel Round 480×480 circular touchscreen display. The project implements real-time tachometer functionality via an ELM327 OBD-II adapter.

**Notice**: This software is experimental and in early development. Fitness for purpose is not guaranteed.

---

## Table of Contents

- [Requirements](<#requirements>)
- [Development Setup](<#development setup>)
- [Build and Deploy](<#build and deploy>)
- [Running GTach](<#running gtach>)
- [Project Structure](<#project structure>)
- [Version History](<#version history>)

---

## 1. Requirements

### 1.1 Deployment

- Raspberry Pi Zero 2W
- Pimoroni HyperPixel Round display (480×480)
- ELM327 OBD-II adapter (Bluetooth SPP)

---

## 2. Development Setup

```bash
git clone https://github.com/William12556/GTach GTach
```

---

## 3. Build and Deploy

### 3.1 Transfer install script to Pi

```bash
scp bin/install.sh root@gtach.local:/opt/gtach/
```

### 3.2 Build wheel and transfer to Pi

```bash
./bin/build.sh && scp dist/gtach-0.2.22-py3-none-any.whl root@gtach.local:/tmp/
```

### 3.3 Install on Pi

```bash
/opt/gtach/install.sh /tmp/gtach-0.2.22-py3-none-any.whl
```

### 3.4 Retrieve log from Pi

```bash
scp root@gtach.local:/opt/gtach/gtach-debug_PI.log ~/Documents/GitHub/GTach/
```

[Return to Table of Contents](<#table of contents>)

---

## 4. Running GTach

### 4.1 Basic usage

```bash
gtach [OPTIONS]
```

### 4.2 Options

| Option | Description | Default |
|---|---|---|
| `--config PATH` | Path to configuration file | Auto-detected |
| `--debug` | Enable debug logging | false |
| `--version` | Print version and exit | — |
| `--validate-config` | Validate configuration and exit | false |
| `--validate-dependencies` | Check runtime dependencies and exit | false |
| `--transport MODE` | Transport: `tcp`, `serial`, `rfcomm`, `simtcp`, `simbt` | None |
| `--obd-host HOST` | OBD TCP host | `localhost` |
| `--obd-port PORT` | OBD TCP port | `35000` |
| `--serial-port PORT` | Serial device path | None |

### 4.3 Examples

```bash
# Run with debug logging (Pi)
gtach --debug 2>&1 | tee /opt/gtach/gtach-debug_PI.log

# Simulated Bluetooth transport
gtach --transport simbt --debug

# TCP transport to emulator
gtach --transport tcp --obd-host ELM327-Emulator.local --obd-port 35000

# Validate dependencies
gtach --validate-dependencies
```

[Return to Table of Contents](<#table of contents>)

---

## 5. Project Structure

```
ai/           Governance framework
src/          Source code
tests/        Test suite
docs/         Technical documentation
workspace/    Development artefacts (issues, changes, design, requirements)
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date       | Notes                                    |
|---------|------------|------------------------------------------|
| 1.4     | 2026-06-17 | Updated script paths for bin/ relocation |
| 1.3     | 2026-05-20 | Updated CLI options in §4               |
| 1.2     | 2026-05-07 | Removed macOS runtime support            |
| 1.1     | 2026-05-06 | Updated build/deploy workflow            |
| 1.0     | 2025-08-08 | Initial README                           |

---

Copyright (c) 2026 William Watson. MIT License.
