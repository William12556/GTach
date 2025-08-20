# Cross-Platform Development Guide

**Created**: 2025 08 20

## Development Strategy

### Dual-Environment Approach
- **Development**: Mac/Linux/Windows with mocks
- **Deployment**: Raspberry Pi with hardware
- **Testing**: Multi-layer validation across platforms

## Platform Detection

### Automatic Configuration
```python
from src.gtach.utils.platform import get_platform_info

platform_info = get_platform_info()
if platform_info['is_raspberry_pi']:
    # Use hardware GPIO
    import RPi.GPIO as GPIO
else:
    # Use mock GPIO
    import mock_gpio as GPIO
```

### Configuration Management
```json
{
  "common": {
    "app_name": "GTach",
    "logging_level": "INFO"
  },
  "mac": {
    "gpio_mock": true,
    "display_simulation": true
  },
  "pi": {
    "gpio_hardware": true,
    "hyperpixel_display": true
  }
}
```

## Implementation Patterns

### Conditional Imports
```python
try:
    import RPi.GPIO as GPIO
    HARDWARE_AVAILABLE = True
except ImportError:
    import mock_gpio as GPIO
    HARDWARE_AVAILABLE = False
```

### Factory Pattern
```python
def create_display_controller():
    if platform.is_raspberry_pi():
        return HyperpixelController()
    else:
        return MockDisplayController()
```

### Dependency Injection
```python
class Application:
    def __init__(self, gpio_controller, display_controller):
        self.gpio = gpio_controller
        self.display = display_controller
```

## Testing Strategy

### Layer 1-2: Cross-Platform (Mac/Pi)
- Unit tests with mocks
- Business logic validation
- Configuration management

### Layer 3: Platform-Specific
- Mock interfaces on development machine
- Real hardware on Raspberry Pi
- API compatibility validation

### Layer 4: Hardware Integration (Pi Only)
- GPIO interface testing
- Display driver validation
- Touch interface verification

## Development Workflow

### 1. Development Phase (Mac)
```bash
# Mock-based development
python3 -m gtach.main --debug --simulate-display
python3 -m pytest src/tests/unit/ -v
```

### 2. Cross-Platform Validation
```bash
# Test platform detection
python3 -c "from src.gtach.utils.platform import detect_platform; print(detect_platform())"

# Test configuration loading
python3 -c "from src.gtach.config import load_config; print(load_config())"
```

### 3. Pi Integration Testing
```bash
# Deploy and test on Pi
scp package.tar.gz pi@PI_IP:/home/pi/
ssh pi@PI_IP "cd /opt/gtach && python3 -m pytest src/tests/ -v"
```

## Common Patterns

### Error Handling
```python
try:
    result = hardware_operation()
except HardwareNotAvailable:
    result = mock_operation()
    logger.warning("Using mock implementation")
```

### Resource Management
```python
class GPIOManager:
    def __enter__(self):
        if HARDWARE_AVAILABLE:
            GPIO.setmode(GPIO.BCM)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if HARDWARE_AVAILABLE:
            GPIO.cleanup()
```

## Deployment Considerations

### Package Creation
- Development machine creates deployment package
- Platform-specific dependencies included
- Configuration templates processed

### Installation
- Automatic platform detection during setup
- Hardware-specific driver installation
- Service configuration for Pi deployment

## Troubleshooting

| Issue | Development | Raspberry Pi |
|-------|------------|--------------|
| Import errors | Check mock dependencies | Verify hardware libraries |
| GPIO failures | Mock validation | Check hardware connections |
| Display issues | Simulation problems | Driver configuration |
| Performance | Mock timing | Hardware optimization |

For implementation details, see [Development Environment Setup](../setup/development_environment.md).

---

**Copyright**: Copyright (c) 2025 William Watson. This work is licensed under the MIT License.
