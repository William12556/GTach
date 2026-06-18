# GTach - Retro Styled OBD-II/ELM327 Tachometer

Created: 2025 08 08

## Overview

GTach is an experimental embedded application for Raspberry Pi with a Pimoroni HyperPixel Round 480×480 display. It implements real-time tachometer functionality via an ELM327 OBD-II Bluetooth adapter.

**Notice**: This software is experimental. Fitness for purpose is not guaranteed.

---

## Table of Contents

[1.0 Requirements](<#1.0 requirements>)
[2.0 Installation](<#2.0 installation>)
[3.0 Build and Deploy](<#3.0 build and deploy>)
[4.0 Service Management](<#4.0 service management>)
[5.0 CLI Reference](<#5.0 cli reference>)
[6.0 Project Structure](<#6.0 project structure>)
[Version History](<#version history>)

---

## 1.0 Requirements

### 1.1 Hardware

- Raspberry Pi Zero 2W
- Pimoroni HyperPixel Round display (480×480)
- ELM327 OBD-II adapter (Bluetooth SPP)

### 1.2 Software

- Python 3.9+
- git

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Installation

### 2.1 Standard Install

For reinstalls and updates on a Pi where the systemd service is already configured.

```bash
/opt/gtach/venv/bin/pip install \
  --extra-index-url https://www.piwheels.org/simple/ \
  "git+https://github.com/William12556/GTach.git[pi]"
```

Restart the service after install:

```bash
systemctl restart gtach
```

### 2.2 Developer Install

For first-time Pi setup and active development, use the full developer workflow in §3.0.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Build and Deploy

Developer workflow. Requires the repository cloned on Mac and SSH access to the Pi at `root@gtach.local`.

### 3.1 Clone Repository (Mac)

```bash
git clone https://github.com/William12556/GTach GTach
cd GTach
python3 -m venv venv
source venv/bin/activate
pip install -e .[dev]
```

### 3.2 Deploy to Pi

Full deploy — build, transfer, install, restart service:

```bash
./bin/deploy.sh
```

Stage update only — transfers wheel to Pi drop directory; install via GTach update menu:

```bash
./bin/deploy.sh --stage
```

### 3.3 Manual Deploy

If deploying without `deploy.sh`:

```bash
# Build
./bin/build.sh

# Transfer files — substitute actual wheel filename from dist/
scp bin/install.sh root@gtach.local:/opt/gtach/
scp dist/gtach-<version>-py3-none-any.whl root@gtach.local:/tmp/

# Install on Pi
ssh root@gtach.local "/opt/gtach/install.sh /tmp/gtach-<version>-py3-none-any.whl"
```

### 3.4 Retrieve Logs

```bash
scp root@gtach.local:/opt/gtach/debug.log ~/Documents/GitHub/GTach/
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Service Management

GTach runs as a systemd service and starts automatically at boot.

### 4.1 Service Control

```bash
systemctl start gtach
systemctl stop gtach
systemctl restart gtach
systemctl status gtach
```

### 4.2 Logs

```bash
# Live service output
journalctl -u gtach -f

# Startup log — truncated at each boot
tail -f /opt/gtach/start.log

# Debug log — written when GTach is started with --debug
tail -f /opt/gtach/debug.log
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 CLI Reference

Manual invocation is for development and debug use. Normal operation uses the systemd service (§4.0).

### 5.1 Options

| Option | Description | Default |
|---|---|---|
| `--config PATH` | Path to configuration file | Auto-detected |
| `--debug` | Enable debug logging to `/opt/gtach/debug.log` | false |
| `--version` | Print version and exit | — |
| `--validate-config` | Validate configuration and exit | false |
| `--validate-dependencies` | Check runtime dependencies and exit | false |
| `--transport MODE` | Transport: `tcp`, `serial`, `rfcomm`, `simtcp`, `simbt` | None |
| `--obd-host HOST` | OBD TCP host | `localhost` |
| `--obd-port PORT` | OBD TCP port | `35000` |
| `--serial-port PORT` | Serial device path | None |

### 5.2 Examples

```bash
# Run with debug logging
gtach --debug

# Simulated Bluetooth transport
gtach --transport simbt --debug

# TCP transport to emulator
gtach --transport tcp --obd-host ELM327-Emulator.local --obd-port 35000

# Validate dependencies
gtach --validate-dependencies
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Project Structure

```
ai/      Governance framework and workspace
bin/     Build, deploy, install, and release scripts
src/     Source code
tests/   Test suite
docs/    Technical documentation
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Notes |
|---|---|---|
| 2.0 | 2026-06-18 | Reorganised: added Installation and Service Management sections; corrected log paths; renamed CLI Reference; fixed Project Structure; corrected ToC anchors |
| 1.5 | 2026-06-17 | Fixed stale version in §3.2/§3.3 |
| 1.4 | 2026-06-17 | Updated script paths for bin/ relocation |
| 1.3 | 2026-05-20 | Updated CLI options |
| 1.2 | 2026-05-07 | Removed macOS runtime support |
| 1.1 | 2026-05-06 | Updated build/deploy workflow |
| 1.0 | 2025-08-08 | Initial README |

---

Copyright (c) 2026 William Watson. MIT License.
