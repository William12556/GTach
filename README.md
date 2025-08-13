# GTach - Hyperpixel Round Display Application

**Created**: 2025 08 08

## Overview

GTach is an embedded application designed for Raspberry Pi deployment with Pimoroni Hyperpixel 2.1" Round touchscreen display. The project provides real-time tachometer functionality through a circular interface optimized for the 480x480 pixel round display while supporting cross-platform development workflows.

This project represents a first attempt at AI-supported software development using Claude Desktop and Claude Code tools. The implementation is experimental in nature, serving as a learning exercise in AI-assisted development workflows, protocol-driven project management, and cross-platform embedded systems development.

## Hardware Platform

The project is designed for **Raspberry Pi** (any compatible model) with **Pimoroni Hyperpixel 2.1" Round** display:

- **Display**: 2.1" IPS round touchscreen (480x480 pixels, ~229 PPI)
- **Interface**: High-speed DPI interface (60 FPS frame rate)
- **Touch**: Capacitive multi-touch support with Python library
- **Platform**: Raspberry Pi (any model) optimized form factor
- **Colors**: 18-bit color depth (262,144 colors)

## Project Structure

The project follows Protocol 1 standards with a hierarchical organization supporting embedded systems complexity while maintaining development efficiency and cross-platform compatibility.

### Key Features

- **Hyperpixel Integration**: Native support for Pimoroni Hyperpixel 2.1" Round display
- **Cross-Platform Development**: Multi-platform development with Raspberry Pi deployment
- **Touch Interface**: Capacitive touchscreen support with gesture recognition
- **Circular UI Design**: Interface optimized for 480x480 round display geometry
- **Documentation**: Protocol-driven documentation with visual diagram support
- **AI-Assisted Development**: Claude Desktop and Claude Code integration per Protocol 4
- **Iterative Development**: Iteration-based workflow per Protocol 2

## Development Environment Setup

### Development Environment

1. **Prerequisites**: Python 3.9+, Git, development dependencies
2. **Installation**: Clone repository and install development dependencies
3. **Configuration**: Platform detection automatically configures development environment with Hyperpixel mocking
4. **Testing**: Multi-layer testing architecture supports development validation including display simulation

### Raspberry Pi Deployment Environment (Linux)

1. **Platform**: Raspberry Pi (any model) with Hyperpixel 2.1" Round display
2. **Display Drivers**: Built-in kernel drivers with `dtoverlay=vc4-kms-dpi-hyperpixel2r`
3. **Touch Support**: Python touch driver for capacitive touchscreen functionality
4. **Installation**: Deployment package transfer and setup.py execution
5. **Configuration**: Production environment configuration with Hyperpixel hardware integration

## Hyperpixel Display Configuration

### Display Driver Setup (Linux/Raspberry Pi)
```bash
# Add to /boot/firmware/config.txt
dtoverlay=vc4-kms-dpi-hyperpixel2r

# Disable I2C for display compatibility
sudo raspi-config nonint do_i2c 1
```

### Touch Driver Installation (Linux/Raspberry Pi)
```bash
# Install Python touch library
pip3 install hyperpixel2r

# For development setup
git clone https://github.com/pimoroni/hyperpixel2r-python
cd hyperpixel2r-python
sudo ./install.sh
```

## Step-by-Step Guide: Packaging, Distributing, and Installing GTach Application

### Prerequisites

Before you begin, ensure you have:
- Development machine (Mac, Linux, or Windows) with project files
- Raspberry Pi with network access
- SSH access to the Raspberry Pi
- Python 3.9+ installed on both systems
- All 143 project tests passing

---

### Part 1: Package Creation (on Development Machine)

#### Step 1: Open Terminal and Navigate to Project
```bash
cd /path/to/your/GTach
```

#### Step 2: Verify Project Status
```bash
# Run the test suite to ensure everything works
python -m pytest src/tests/ -v

# You should see: 143 tests passed
```

#### Step 3: Create the Deployment Package
```bash
# Navigate to the provisioning directory
cd src/provisioning

# Run the package creation script
python example_usage.py
```

**What happens:** The system will:
- Collect all source files from `src/obdii`
- Process configuration templates for Raspberry Pi
- Generate installation scripts
- Create a compressed package file
- Save it to the `packages/` directory

#### Step 4: Verify Package Creation
```bash
# Check the packages directory
ls -la ../../packages/

# You should see a file like:
# gtach-pi-deployment-1.0.0-20250810_143022.tar.gz
```

---

### Part 2: Package Distribution

#### Step 5: Transfer Package to Raspberry Pi
```bash
# Copy the package to your Pi (replace with your Pi's IP address)
scp ../../packages/gtach-pi-deployment-*.tar.gz pi@192.168.1.100:/home/pi/
```

**Alternative method using USB drive:**
1. Copy the package file to a USB drive
2. Insert USB drive into Raspberry Pi
3. Copy file from USB to Pi's home directory

---

### Part 3: Installation (on Raspberry Pi)

#### Step 6: Connect to Raspberry Pi
```bash
# SSH into your Raspberry Pi
ssh pi@192.168.1.100
```

#### Step 7: Prepare Installation Directory
```bash
# Create application directory
sudo mkdir -p /opt/gtach

# Set ownership to pi user
sudo chown pi:pi /opt/gtach
```

#### Step 8: Extract and Install the Package
```bash
# Navigate to home directory where package was copied
cd /home/pi

# Extract the package
tar -xzf gtach-pi-deployment-*.tar.gz

# Navigate into extracted directory
cd gtach-pi-deployment-*

# Run the installation script
sudo chmod +x install.sh
sudo ./install.sh
```

**What the installer does:**
- Copies application files to `/opt/gtach/`
- Installs Python dependencies
- Sets up proper file permissions
- Creates systemd service (if configured)

#### Step 9: Verify Installation
```bash
# Check if files were installed
ls -la /opt/gtach/

# Try running the application
cd /opt/gtach
python3 main.py --help
```

---

### Part 4: Configuration and Service Setup

#### Step 10: Configure for Your Hardware
```bash
# Edit configuration for your specific setup
nano /opt/gtach/config/platform_config.json

# Make sure GPIO and display settings match your hardware
```

#### Step 11: Start the Application Service
```bash
# If systemd service was created during installation
sudo systemctl enable gtach
sudo systemctl start gtach

# Check service status
sudo systemctl status gtach
```

#### Step 12: Test Basic Functionality
```bash
# Check application logs
sudo journalctl -u gtach -f

# Or check log files directly
tail -f /opt/gtach/logs/session_*.log
```

---

### Part 5: Verification and Troubleshooting

#### Step 13: Verify Hardware Interfaces
```bash
# Test GPIO functionality (if your hardware supports it)
cd /opt/gtach
python3 -c "from src.obdii.utils.platform import get_platform_info; print(get_platform_info())"

# Should show Pi-specific capabilities
```

#### Step 14: Run Application Tests
```bash
# Run the test suite on the Pi to verify everything works
cd /opt/gtach
python3 -m pytest src/tests/ -v

# All tests should pass on the Pi as well
```

---

### Part 6: Updates (Future Deployments)

#### For Future Updates:

##### Step 15: Create New Package (on Mac)
```bash
# Update version number in your code first
# Then create new package
cd /path/to/your/GTach/src/provisioning
python example_usage.py
```

##### Step 16: Deploy Update (on Pi)
```bash
# The system automatically creates backups before updates
# Copy new package to Pi and extract
tar -xzf gtach-pi-deployment-NEW_VERSION.tar.gz
cd gtach-pi-deployment-NEW_VERSION

# Run update installation
sudo ./install.sh
```

---

### Quick Command Summary

**On Development Machine (Packaging):**
```bash
cd /path/to/your/GTach
python -m pytest src/tests/ -v                    # Verify tests pass
cd src/provisioning && python example_usage.py    # Create package
scp ../../packages/gtach-*.tar.gz pi@PI_IP:/home/pi/  # Transfer to Pi
```

**On Pi (Installation):**
```bash
tar -xzf gtach-*.tar.gz                          # Extract package
cd gtach-* && sudo ./install.sh                  # Install
sudo systemctl start gtach                       # Start service
sudo systemctl status gtach                      # Check status
```

---

### Common Issues and Solutions

**Problem:** Permission denied during installation  
**Solution:** Make sure you're using `sudo` for installation commands

**Problem:** Package not found error  
**Solution:** Verify the package was transferred correctly and filename matches

**Problem:** GPIO not working  
**Solution:** Check that SPI/I2C interfaces are enabled in `raspi-config`

**Problem:** Service won't start  
**Solution:** Check logs with `sudo journalctl -u gtach -f` for error messages

**Problem:** Tests fail on Pi  
**Solution:** Ensure all Python dependencies installed correctly with `pip3 list`

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

### Production Environment (Linux/Raspberry Pi)
```bash
# Deploy package (from development environment)
scp deployment_package.tar.gz pi@raspberry-pi:/tmp/
ssh pi@raspberry-pi "cd /tmp && tar -xzf deployment_package.tar.gz && python setup.py install"

# Run on Raspberry Pi with Hyperpixel display
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

- **Layer 1**: Unit Tests (macOS Compatible) - Individual function validation with display mocking
- **Layer 2**: Business Logic Tests (macOS Compatible) - Component integration testing with UI simulation
- **Layer 3**: Platform Interface Tests (Mock Development/Real Linux) - Display and touch interface validation
- **Layer 4**: Hardware Integration Tests (Linux Only) - Hyperpixel display and touch validation

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

- **Development**: Any modern development machine (Mac, Linux, Windows) with display mocking and testing capabilities
- **Deployment**: Raspberry Pi with Hyperpixel 2.1" Round display integration
- **Configuration**: JSON-based platform detection and display configuration management
- **Testing**: Validation across both environments including display simulation

## License

[License information - see LICENSE file]

## Technical Requirements

### Development Environment
- Modern development machine (Mac, Linux, or Windows)
- Python 3.9+
- Development dependencies per requirements.txt
- Display simulation capabilities for development testing

### Deployment Environment (Linux)
- Raspberry Pi (any model compatible with Hyperpixel display)
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
- **Pi Integration**: Optimized form factor for Raspberry Pi mounting

---

**Project Status**: Active Development  
**Protocol Compliance**: All protocols implemented and maintained  
**Hardware Platform**: Raspberry Pi with Hyperpixel 2.1" Round Display  
**Cross-Platform Status**: Multi-platform development and Linux deployment validated  
**Documentation Status**: Documentation with visual diagram support
