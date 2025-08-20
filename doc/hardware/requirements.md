# Hardware Requirements

**Created**: 2025 08 20

## Development Environment

### Minimum Requirements
- Modern development machine (Mac, Linux, or Windows)
- Python 3.9+
- 4GB RAM minimum
- Git version control
- USB connectivity for Pi deployment

### Recommended Development Setup
- Multi-core processor for compilation and testing
- 8GB+ RAM for development tools
- SSD storage for improved I/O performance
- Network connectivity for package management

## Deployment Environment (Raspberry Pi)

### Required Hardware
- **Raspberry Pi**: Any model with 40-pin GPIO header
- **Display**: Pimoroni Hyperpixel 2.1" Round (480x480 pixels)
- **Storage**: MicroSD card (minimum 8GB, Class 10 recommended)
- **Power**: Official Raspberry Pi power supply (model-appropriate)

### Optional Hardware
- **Case**: Compatible with Hyperpixel display mounting
- **Cooling**: Heat sinks or fan for sustained operation
- **Connectivity**: Wi-Fi or Ethernet for deployment and updates

## Software Requirements

### Development Environment
- Python 3.9 or newer
- Git version control system
- Text editor or IDE with Python support
- Terminal/command line access

### Raspberry Pi (Deployment)
- Raspberry Pi OS (Debian-based)
- Python 3.9+
- Hyperpixel display drivers (kernel built-in)
- Hyperpixel touch driver library

## Network Requirements

### Development Workflow
- Internet connectivity for package installation
- SSH access to Raspberry Pi for deployment
- Local network connectivity between development machine and Pi

### Deployment Environment
- Network connectivity for initial setup
- SSH server enabled on Raspberry Pi
- Optional: Internet access for package updates

## Storage Requirements

### Development Environment
- **Project Files**: ~50MB for source code and documentation
- **Dependencies**: ~200MB for Python packages and development tools
- **Build Artifacts**: ~100MB for testing and packaging

### Raspberry Pi Deployment
- **System**: Minimum 4GB for Raspberry Pi OS
- **Application**: ~100MB for GTach application and dependencies
- **Logs**: ~50MB for operational logging
- **Free Space**: 2GB minimum recommended for updates

## Performance Considerations

### Development Environment
- Build and test operations benefit from SSD storage
- Multi-core processors improve compilation times
- Adequate RAM prevents swap usage during development

### Raspberry Pi Deployment
- **Display Performance**: 60 FPS target requires sufficient GPU memory allocation
- **Touch Responsiveness**: Real-time touch processing requirements
- **Thermal Management**: Sustained operation may require cooling

## Compatibility Matrix

| Component | Development | Raspberry Pi |
|-----------|-------------|--------------|
| **OS** | macOS/Linux/Windows | Raspberry Pi OS |
| **Python** | 3.9+ | 3.9+ |
| **Display** | Simulated | Hyperpixel 2.1" Round |
| **Touch** | Simulated | Capacitive multi-touch |
| **GPIO** | Mocked | Hardware GPIO |

## Verification Commands

### Development Environment
```bash
python3 --version          # Confirm Python 3.9+
git --version              # Confirm Git installation
pip3 list                  # Verify package manager
```

### Raspberry Pi Environment
```bash
cat /proc/device-tree/model # Confirm Pi model
python3 --version          # Confirm Python 3.9+
ls /dev/fb*                # Confirm display device
dmesg | grep -i hyperpixel # Confirm display driver
```

For detailed hardware setup procedures, see:
- [Hyperpixel Display Setup](hyperpixel_setup.md)
- [Raspberry Pi Configuration](../setup/raspberry_pi_deployment.md)

---

**Copyright**: Copyright (c) 2025 William Watson. This work is licensed under the MIT License.
