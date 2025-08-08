# GTach - GPIO-based Tachometer Application

**Created**: 2025 08 08

## Overview

GTach is a sophisticated embedded application designed for Raspberry Pi deployment that provides real-time tachometer functionality through GPIO interfaces while supporting comprehensive cross-platform development workflows on Mac development environments.

## Project Structure

The project follows Protocol 1 standards with a hierarchical organization supporting embedded systems complexity while maintaining development efficiency and cross-platform compatibility.

### Key Features

- **Cross-Platform Development**: Mac Mini M4 development with Raspberry Pi deployment
- **GPIO Hardware Integration**: Complete hardware interface support per Protocol 10
- **Comprehensive Documentation**: Protocol-driven documentation with visual diagram support
- **AI-Assisted Development**: Claude Desktop and Claude Code integration per Protocol 4
- **Iterative Development**: Systematic iteration-based workflow per Protocol 2

## Development Environment Setup

### Mac Development Environment

1. **Prerequisites**: Python 3.9+, Git, development dependencies
2. **Installation**: Clone repository and install development dependencies
3. **Configuration**: Platform detection automatically configures Mac development mocking
4. **Testing**: Multi-layer testing architecture supports complete development validation

### Raspberry Pi Deployment Environment

1. **Platform**: Raspberry Pi with GPIO hardware interface capabilities
2. **Installation**: Secure deployment package transfer and setup.py execution
3. **Configuration**: Production environment configuration with hardware integration
4. **Validation**: Hardware integration testing with real GPIO interfaces

## Usage Examples

### Development Environment
```bash
# Install development environment
python setup.py develop

# Run with debug logging
python -m obdii.main --debug

# Execute test suite
python -m pytest src/tests/
```

### Production Environment
```bash
# Deploy package (from development environment)
scp deployment_package.tar.gz pi@raspberry-pi:/tmp/
ssh pi@raspberry-pi "cd /tmp && tar -xzf deployment_package.tar.gz && python setup.py install"

# Run on Raspberry Pi
gtach --debug
```

## Documentation

Comprehensive documentation follows Protocol 3 standards with Obsidian integration and visual documentation per Protocol 12:

- **Protocols**: `doc/protocol/` - Development workflow and standards
- **Design**: `doc/design/` - Architecture decisions and visual documentation
- **Hardware**: `doc/hardware/` - GPIO interfaces and hardware integration
- **Templates**: `doc/templates/` - Standardized document formats

## Testing Architecture

Multi-layer testing architecture per Protocol 6:

- **Layer 1**: Unit Tests (Mac Compatible) - Individual function validation with mocking
- **Layer 2**: Business Logic Tests (Mac Compatible) - Component integration testing
- **Layer 3**: Platform Interface Tests (Mock Mac/Real Pi) - Platform-specific API validation
- **Layer 4**: Hardware Integration Tests (Pi Only) - Complete hardware interface validation

## Contributing

Development follows systematic protocols with AI coordination support:

1. **Iteration Planning**: Protocol 2 iteration-based development workflow
2. **Implementation**: Claude Code prompts per Protocol 4 integration standards
3. **Documentation**: Protocol 3 documentation standards with Protocol 12 visual documentation
4. **Quality Assurance**: Protocol 8 logging standards and comprehensive testing
5. **Version Control**: Protocol 5 GitHub Desktop workflow integration

## Cross-Platform Compatibility

The application supports seamless operation across development and deployment environments:

- **Development**: Mac Mini M4 with complete mocking and testing capabilities
- **Deployment**: Raspberry Pi with hardware GPIO interface integration
- **Configuration**: JSON-based platform detection and configuration management
- **Testing**: Comprehensive validation across both environments

## License

[License information - see LICENSE file]

## Technical Requirements

### Development Environment
- Mac Mini M4 (macOS)
- Python 3.9+
- Development dependencies per requirements.txt
- GPIO mocking capabilities for development testing

### Deployment Environment
- Raspberry Pi (Linux)
- GPIO hardware interface capabilities
- Python 3.9+
- Production dependencies per requirements.txt

## Contact and Support

[Contact information and support procedures]

---

**Project Status**: Active Development  
**Protocol Compliance**: All protocols implemented and maintained  
**Cross-Platform Status**: Mac development and Pi deployment validated  
**Documentation Status**: Comprehensive documentation with visual diagram support
