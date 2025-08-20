# Raspberry Pi Deployment Guide

**Created**: 2025 08 20

## Prerequisites

- Development machine with GTach project
- Raspberry Pi with Hyperpixel 2.1" Round display
- Network connectivity between machines
- SSH access to Raspberry Pi

**Warning**: This software is experimental and unproven. Use at your own risk.

## Part 1: Package Creation (Development Machine)

### Step 1: Prepare Environment
```bash
cd /path/to/GTach
python3 -m pytest src/tests/ -v  # Verify tests pass
```

### Step 2: Create Deployment Package
```bash
cd src/provisioning
python3 create_package.py
ls -la ../../packages/  # Verify package creation
```

## Part 2: Package Transfer

### Step 3: Transfer to Raspberry Pi
```bash
# Replace with your Pi's IP address
scp ../../packages/gtach-pi-deployment-*.tar.gz pi@192.168.1.100:/home/pi/
```

## Part 3: Installation (Raspberry Pi)

### Step 4: Connect and Prepare
```bash
ssh pi@192.168.1.100
sudo mkdir -p /opt/gtach
sudo chown pi:pi /opt/gtach
```

### Step 5: Install Package
```bash
cd /home/pi
tar -xzf gtach-pi-deployment-*.tar.gz
cd gtach-pi-deployment-*
sudo chmod +x install.sh
sudo ./install.sh
```

### Step 6: Verify Installation
```bash
ls -la /opt/gtach/
cd /opt/gtach
python3 main.py --help
```

## Part 4: Configuration

### Step 7: Configure Hardware
```bash
nano /opt/gtach/config/platform_config.json
# Verify GPIO and display settings
```

### Step 8: Start Service
```bash
sudo systemctl enable gtach
sudo systemctl start gtach
sudo systemctl status gtach
```

## Part 5: Verification

### Step 9: Test Functionality
```bash
# Check logs
sudo journalctl -u gtach -f
tail -f /opt/gtach/logs/session_*.log

# Run tests
cd /opt/gtach
python3 -m pytest src/tests/ -v
```

## Quick Reference Commands

### Package and Deploy
```bash
# Development machine
cd GTach && python3 -m pytest src/tests/ -v
cd src/provisioning && python3 create_package.py
scp ../../packages/gtach-*.tar.gz pi@PI_IP:/home/pi/

# Raspberry Pi
tar -xzf gtach-*.tar.gz && cd gtach-*
sudo ./install.sh && sudo systemctl start gtach
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Permission denied | Use `sudo` for installation |
| Package not found | Verify transfer and filename |
| GPIO not working | Enable SPI/I2C in `raspi-config` |
| Service won't start | Check `sudo journalctl -u gtach -f` |
| Tests fail | Verify dependencies with `pip3 list` |

## Updates

For future deployments:
1. Create new package on development machine
2. Transfer to Pi and extract
3. Run `sudo ./install.sh` (automatic backup created)
4. Restart service

For detailed hardware setup, see [Hyperpixel Setup Guide](../hardware/hyperpixel_setup.md).

---

**Copyright**: Copyright (c) 2025 William Watson. This work is licensed under the MIT License.
