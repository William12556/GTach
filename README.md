# GTach - Retro styled ODBII/ELM327 based Tachometer

**Created**: 2025 08 08

## Overview

GTach is an experimental embedded application under development for Raspberry Pi deployment with Pimoroni Hyperpixel 2.1" Round touchscreen display. The project implements real-time tachometer functionality through a circular interface for the 480x480 pixel round display.

**Important Notice**: This software is currently very unproven and in early development stages. The implementation is experimental in nature, serving as a learning exercise in AI-assisted development workflows, protocol-driven project management, and cross-platform embedded systems development. Actual fitness for purpose is not guaranteed.

This project represents a first attempt at AI-supported software development using Claude Desktop, Claude Code and Codestral 22b AI tools. The objective is to establish a sort of AI orchestration framework to guide software development. A kind of AI wrangler if you will.

What you see from this point on is completely AI generated.

## Quick Start

### Development Environment
```bash
git clone [repository-url] GTach
cd GTach
python3 -m venv venv
source venv/bin/activate
pip install -e .[dev]
python3 -m pytest tests/ -v
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

## Documentation

### Project Structure
- `ai/` - Governance framework and templates
- `workspace/design/` - Architecture and component design documents
- `workspace/` - Development artifacts (issues, changes, tests, audits)
- `src/` - Source code
- `tests/` - Test suite
- `docs/` - Technical documentation

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
