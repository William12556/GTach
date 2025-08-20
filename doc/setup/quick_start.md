# Quick Start Guide

**Created**: 2025 08 20

## 5-Minute Setup

### Development Environment
```bash
# Clone and setup
git clone [repository-url] GTach
cd GTach
pip3 install -r requirements.txt

# Run tests
python3 -m pytest src/tests/ -v

# Start with debug
python3 -m gtach.main --debug --simulate-display
```

### Raspberry Pi Setup
```bash
# Create package
cd src/provisioning && python3 create_package.py

# Deploy to Pi
scp ../../packages/gtach-*.tar.gz pi@PI_IP:/home/pi/
ssh pi@PI_IP
tar -xzf gtach-*.tar.gz && cd gtach-*
sudo ./install.sh
```

## Hardware Requirements
- **Development**: Python 3.9+, modern machine
- **Deployment**: Raspberry Pi + Hyperpixel 2.1" Round display

## Next Steps
- [Development Setup](development_environment.md) - Full development environment
- [Pi Deployment](raspberry_pi_deployment.md) - Complete Pi setup
- [Hardware Setup](../hardware/hyperpixel_setup.md) - Display configuration

## Need Help?
- [Hardware Requirements](../hardware/requirements.md)
- [Troubleshooting](../hardware/troubleshooting.md)
- [Testing Guide](../testing/testing_overview.md)

---

**Copyright**: Copyright (c) 2025 William Watson. This work is licensed under the MIT License.
