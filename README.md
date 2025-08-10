# GTach - Hyperpixel Round Display Application

**Created**: 2025 08 08

## Overview

GTach is an embedded application designed for Raspberry Pi Zero deployment with Pimoroni Hyperpixel 2.1" Round touchscreen display. The project provides real-time tachometer functionality through a circular interface optimized for the 480x480 pixel round display while supporting cross-platform development workflows on Mac development environments.

This project represents a first attempt at AI-supported software development using Claude Desktop and Claude Code tools. The implementation is experimental in nature, serving as a learning exercise in AI-assisted development workflows, protocol-driven project management, and cross-platform embedded systems development.

## Hardware Platform

The project is designed for the **Raspberry Pi Zero** with **Pimoroni Hyperpixel 2.1" Round** display:

- **Display**: 2.1" IPS round touchscreen (480x480 pixels, ~229 PPI)
- **Interface**: High-speed DPI interface (60 FPS frame rate)
- **Touch**: Capacitive multi-touch support with Python library
- **Platform**: Raspberry Pi Zero/Zero W optimized form factor
- **Colors**: 18-bit color depth (262,144 colors)

## Project Structure

The project follows Protocol 1 standards with a hierarchical organization supporting embedded systems complexity while maintaining development efficiency and cross-platform compatibility.

### Key Features

- **Hyperpixel Integration**: Native support for Pimoroni Hyperpixel 2.1" Round display
- **Cross-Platform Development**: Mac Mini M4 development with Raspberry Pi Zero deployment
- **Touch Interface**: Capacitive touchscreen support with gesture recognition
- **Circular UI Design**: Interface optimized for 480x480 round display geometry
- **Documentation**: Protocol-driven documentation with visual diagram support
- **AI-Assisted Development**: Claude Desktop and Claude Code integration per Protocol 4
- **Iterative Development**: Iteration-based workflow per Protocol 2

## Development Environment Setup

### Mac Development Environment

1. **Prerequisites**: Python 3.9+, Git, development dependencies
2. **Installation**: Clone repository and install development dependencies
3. **Configuration**: Platform detection automatically configures Mac development with Hyperpixel mocking
4. **Testing**: Multi-layer testing architecture supports development validation including display simulation

### Raspberry Pi Zero Deployment Environment

1. **Platform**: Raspberry Pi Zero/Zero W with Hyperpixel 2.1" Round display
2. **Display Drivers**: Built-in kernel drivers with `dtoverlay=vc4-kms-dpi-hyperpixel2r`
3. **Touch Support**: Python touch driver for capacitive touchscreen functionality
4. **Installation**: Deployment package transfer and setup.py execution
5. **Configuration**: Production environment configuration with Hyperpixel hardware integration

## Hyperpixel Display Configuration

### Display Driver Setup
```bash
# Add to /boot/firmware/config.txt
dtoverlay=vc4-kms-dpi-hyperpixel2r

# Disable I2C for display compatibility
sudo raspi-config nonint do_i2c 1
```

### Touch Driver Installation
```bash
# Install Python touch library
pip3 install hyperpixel2r

# For development setup
git clone https://github.com/pimoroni/hyperpixel2r-python
cd hyperpixel2r-python
sudo ./install.sh
```

## Usage Examples

### Development Environment
```bash
# Install development environment
python setup.py develop

# Run with debug logging and display simulation
python -m gtach.main --debug --simulate-display

# Execute test suite including display tests
python -m pytest src/tests/
```

### Production Environment (Raspberry Pi Zero)
```bash
# Deploy package (from development environment)
scp deployment_package.tar.gz pi@pi-zero:/tmp/
ssh pi@pi-zero "cd /tmp && tar -xzf deployment_package.tar.gz && python setup.py install"

# Run on Raspberry Pi Zero with Hyperpixel display
gtach --debug
```

## Documentation

Documentation follows Protocol 3 standards with Obsidian integration and visual documentation per Protocol 12:

- **Protocols**: `doc/protocol/` - Development workflow and standards
- **Design**: `doc/design/` - Architecture decisions and visual documentation
- **Hardware**: `doc/hardware/` - Hyperpixel display interfaces and hardware integration
- **Templates**: `doc/templates/` - Document formats

## Testing Architecture

Multi-layer testing architecture per Protocol 6 with Hyperpixel-specific considerations:

- **Layer 1**: Unit Tests (Mac Compatible) - Individual function validation with display mocking
- **Layer 2**: Business Logic Tests (Mac Compatible) - Component integration testing with UI simulation
- **Layer 3**: Platform Interface Tests (Mock Mac/Real Pi) - Display and touch interface validation
- **Layer 4**: Hardware Integration Tests (Pi Only) - Hyperpixel display and touch validation

## Circular UI Design Considerations

The application interface is designed for the round 480x480 pixel display:

- **Circular Layout**: UI elements arranged for round display utilization
- **Touch Zones**: Touch areas optimized for finger interaction on round display
- **Visual Hierarchy**: Information presentation adapted to circular geometry
- **Performance Optimization**: 60 FPS rendering for tachometer animations
- **Multi-touch Support**: Gesture recognition for user interaction

## Contributing

Development follows protocols with AI coordination support:

1. **Iteration Planning**: Protocol 2 iteration-based development workflow
2. **Implementation**: Claude Code prompts per Protocol 4 integration standards
3. **Documentation**: Protocol 3 documentation standards with Protocol 12 visual documentation
4. **Quality Assurance**: Protocol 8 logging standards and testing
5. **Version Control**: Protocol 5 GitHub Desktop workflow integration

## Cross-Platform Compatibility

The application supports operation across development and deployment environments:

- **Development**: Mac Mini M4 with Hyperpixel mocking and testing capabilities
- **Deployment**: Raspberry Pi Zero with Hyperpixel 2.1" Round display integration
- **Configuration**: JSON-based platform detection and display configuration management
- **Testing**: Validation across both environments including display simulation

## License

[License information - see LICENSE file]

## Technical Requirements

### Development Environment
- Mac Mini M4 (macOS)
- Python 3.9+
- Development dependencies per requirements.txt
- Hyperpixel display simulation capabilities for development testing

### Deployment Environment
- Raspberry Pi Zero/Zero W (Linux)
- Pimoroni Hyperpixel 2.1" Round display (480x480 pixels)
- Hyperpixel display drivers (built-in kernel support)
- Hyperpixel touch drivers (Python library)
- Python 3.9+
- Production dependencies per requirements.txt

## Hardware Specifications

### Hyperpixel 2.1" Round Display
- **Resolution**: 480x480 pixels (~229 PPI)
- **Size**: 2.1" diagonal, perfectly circular
- **Technology**: IPS display with 175° viewing angle
- **Color Depth**: 18-bit (262,144 colors)
- **Frame Rate**: 60 FPS via high-speed DPI interface
- **Touch**: Capacitive multi-touch with Python library support
- **Dimensions**: 71.80 x 71.80 x 10.8mm
- **Pi Zero Integration**: Optimized form factor for Pi Zero mounting

---

**Project Status**: Active Development  
**Protocol Compliance**: All protocols implemented and maintained  
**Hardware Platform**: Raspberry Pi Zero with Hyperpixel 2.1" Round Display  
**Cross-Platform Status**: Mac development and Pi Zero deployment validated  
**Documentation Status**: Documentation with visual diagram support
