# GTach - Retro styled ODBII/ELM327 based Tachometer

**Created**: 2025 08 08

## Overview

GTach is an experimental embedded application under development for Raspberry Pi deployment with Pimoroni Hyperpixel 2.1" Round touchscreen display. The project implements real-time tachometer functionality through a circular interface for the 480x480 pixel round display.

**Important Notice**: This software is currently very unproven and in early development stages. The implementation is experimental in nature, serving as a learning exercise in AI-assisted development workflows, protocol-driven project management, and cross-platform embedded systems development. Actual fitness for purpose is not guaranteed.

This project represents a first attempt at AI-supported software development using Claude Desktop and Claude Code tools.

## Quick Start

### Development Environment
```bash
git clone [repository-url] GTach
cd GTach
pip3 install -r requirements.txt
python3 -m pytest src/tests/ -v
python3 -m gtach.main --debug --simulate-display
```

### Raspberry Pi Deployment
```bash
# Create deployment package
cd src/provisioning && python3 create_package.py

# Deploy to Pi
scp ../../packages/gtach-*.tar.gz pi@PI_IP:/home/pi/
ssh pi@PI_IP "tar -xzf gtach-*.tar.gz && cd gtach-* && sudo ./install.sh"
```

## Requirements

### Development
- Python 3.9+
- Modern development machine
- Git version control

### Deployment  
- Raspberry Pi (any model)
- Pimoroni Hyperpixel 2.1" Round display (480x480 pixels)
- MicroSD card (8GB minimum)

## Documentation Guide

### Essential Reading
- [Quick Start Guide](doc/setup/quick_start.md) - Get running in 5 minutes
- [Hardware Requirements](doc/hardware/requirements.md) - What you need
- [Hyperpixel Specifications](doc/hardware/hyperpixel_specifications.md) - Display details

### Setup and Installation
- [Development Setup](doc/setup/development_environment.md) - Development machine setup
- [Raspberry Pi Deployment](doc/setup/raspberry_pi_deployment.md) - Target hardware setup

### Development
- [Development Protocols](doc/protocol/README.md) - Development workflow overview
- [Testing Guide](doc/testing/testing_overview.md) - Running and writing tests
- [Cross-Platform Development](doc/development/cross_platform_guide.md) - Mac/Pi compatibility

### Hardware Integration
- [GPIO Interfaces](doc/hardware/gpio_interfaces.md) - Hardware connections
- [Troubleshooting](doc/hardware/troubleshooting.md) - Common hardware issues

## Project Status

**Development Stage**: Early experimental development  
**Hardware Platform**: Raspberry Pi with Hyperpixel 2.1" Round Display  
**Cross-Platform**: Framework designed, validation in progress  
**Testing**: Multi-layer testing architecture implemented  
**AI Integration**: Claude Desktop and Claude Code workflow active

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Warning**: This is experimental software. Actual fitness for purpose is not guaranteed.
