# Hyperpixel 2.1" Round Display Specifications

**Created**: 2025 08 20

## Hardware Platform

The project targets **Raspberry Pi** (any compatible model) with **Pimoroni Hyperpixel 2.1" Round** display:

### Display Specifications
- **Resolution**: 480x480 pixels (~229 PPI)
- **Size**: 2.1" diagonal, perfectly circular
- **Technology**: IPS display with 175° viewing angle
- **Color Depth**: 18-bit (262,144 colors)
- **Frame Rate**: 60 FPS via high-speed DPI interface
- **Dimensions**: 71.80 x 71.80 x 10.8mm

### Touch Interface
- **Type**: Capacitive multi-touch support
- **Library**: Python touch driver
- **Integration**: Hardware interrupt-based touch detection

### Platform Integration
- **Interface**: High-speed DPI interface
- **Platform**: Raspberry Pi (any model) optimized form factor
- **Mounting**: Optimized form factor for Raspberry Pi mounting
- **Power**: Powered through Pi GPIO header

## Technical Requirements

### Raspberry Pi Compatibility
- Any Raspberry Pi model with 40-pin GPIO header
- Minimum 512MB RAM recommended
- MicroSD card (minimum 8GB)
- Network connectivity for deployment

### System Requirements
- Raspberry Pi OS (Debian-based)
- Python 3.9+
- Kernel drivers (built-in support)
- Touch driver library

## Display Driver Configuration

Complete kernel configuration required in `/boot/firmware/config.txt`:

```bash
# System Architecture
arm_64bit=1
boot_delay=0              
initial_turbo=30 
arm_boost=1    
avoid_warnings=1
disable_splash=1
gpu_mem=128

# Display Configuration
hdmi_force_hotplug=1
hdmi_mode=1
hdmi_group=1

# Hyperpixel 2.1" Round DPI Configuration
dtoverlay=hyperpixel2r:disable-touch
enable_dpi_lcd=1
dpi_group=2
dpi_mode=87
dpi_output_format=0x7f216
dpi_timings=480 0 10 16 55 480 0 15 60 15 0 0 0 60 0 19200000 6
dtparam=i2c_arm=on
```

## Touch Driver Setup

### Python Library Installation
```bash
# Install Python touch library
pip3 install hyperpixel2r

# Alternative: Manual installation
git clone https://github.com/pimoroni/hyperpixel2r-python
cd hyperpixel2r-python
sudo ./install.sh
```

### Integration Notes
- Touch events handled through Python callbacks
- Multi-touch gesture support available
- Hardware interrupt-based for responsive interaction

## Circular UI Design Considerations

The 480x480 round display requires specific design considerations:

### Layout Principles
- **Circular Layout**: UI elements arranged for round display utilization
- **Touch Zones**: Touch areas optimized for finger interaction
- **Visual Hierarchy**: Information presentation adapted to circular geometry
- **Edge Utilization**: Minimize information loss at display edges

### Performance Optimization
- **Frame Rate**: Target 60 FPS for smooth tachometer animations
- **Resource Management**: Efficient rendering for Pi hardware constraints
- **Touch Responsiveness**: Minimize latency between touch and response

## References

Pimoroni Ltd. (2024) *Hyperpixel 2.1" Round*. [Online]. Available at: https://shop.pimoroni.com/products/hyperpixel-2-1-round [Accessed 20 August 2025].

Pimoroni Ltd. (2024) *Hyperpixel2r Python Library*. [Online]. Available at: https://github.com/pimoroni/hyperpixel2r-python [Accessed 20 August 2025].

---

**Copyright**: Copyright (c) 2025 William Watson. This work is licensed under the MIT License.
