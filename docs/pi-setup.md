Created: 2026 June 19

# GTach — Raspberry Pi Zero 2W Hardware Setup

---

## Table of Contents

[1.0 Hardware](<#1.0 hardware>)
[2.0 Operating System](<#2.0 operating system>)
[3.0 Boot Configuration](<#3.0 boot configuration>)
[3.1 config.txt](<#3.1 config.txt>)
[3.2 cmdline.txt](<#3.2 cmdline.txt>)
[4.0 GTach Installation](<#4.0 gtach installation>)
[5.0 Development Access](<#5.0 development access>)
[5.1 Hardware](<#5.1 hardware>)
[5.2 Pi Configuration](<#5.2 pi configuration>)
[5.3 Laptop Connection](<#5.3 laptop connection>)
[5.4 Verification](<#5.4 verification>)
[Version History](<#version history>)

---

## 1.0 Hardware

| Component | Specification |
|---|---|
| SBC | Raspberry Pi Zero 2W |
| Display | Pimoroni HyperPixel 2.1" Round (480×480, IPS, DPI interface) |
| OBD-II Adapter | ELM327 Bluetooth SPP |

**Assembly note:** The HyperPixel 2.1 Round connects directly to the Pi Zero 2W 40-pin GPIO header without a booster header. When mounting, place the display face-down on a soft surface and gently seat the Pi onto the header. Do not press on the display glass. Short standoffs may be used to secure the assembly.

**GPIO constraint:** The HyperPixel DPI interface occupies all GPIO pins. No additional HATs or GPIO-connected devices are supported.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Operating System

**Debian GNU/Linux 11 (Bullseye), 64-bit.** Newer releases have known compatibility issues with this hardware configuration and are not supported.

Use Raspberry Pi Imager to write the image to a microSD card. Select: *Raspberry Pi OS (other)* → *Raspberry Pi OS Lite (64-bit)* — then verify the image reports Bullseye before writing.

**Imager settings to configure before writing:**

- Hostname: `gtach`
- Enable SSH: yes
- Username: `root` (or a user with sudo; configure for root access as required by GTach)
- Wi-Fi credentials: as required

GTach runs as root under systemd. Ensure root SSH login is enabled:

```bash
# /etc/ssh/sshd_config
PermitRootLogin yes
```

Restart SSH after editing:

```bash
systemctl restart ssh
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Boot Configuration

### 3.1 config.txt

`/boot/config.txt` — required settings for the HyperPixel 2.1 Round DPI display.

```ini
arm_64bit=1

boot_delay=0
initial_turbo=30
arm_boost=1
avoid_warnings=1
disable_splash=1

gpu_mem=128

hdmi_force_hotplug=1
hdmi_mode=1
hdmi_group=1

dtoverlay=hyperpixel2r:disable-touch
enable_dpi_lcd=1
dpi_group=2
dpi_mode=87
dpi_output_format=0x7f216
dpi_timings=480 0 10 16 55 480 0 15 60 15 0 0 0 60 0 19200000 6

dtparam=i2c_arm=on
```

**Notes:**

- `disable_splash=1` suppresses the Pi firmware rainbow splash. Required — Plymouth is not supported with the DPI interface.
- `dtoverlay=hyperpixel2r:disable-touch` loads the HyperPixel kernel driver. Touch is disabled; GTach does not use touch input.
- `dtparam=i2c_arm=on` enables I2C. Required by the HyperPixel driver.
- Do not add `dtoverlay=vc4-kms-dpi-hyperpixel2r`. The settings above use the legacy DPI configuration, which is required for this hardware combination.

[Return to Table of Contents](<#table of contents>)

---

### 3.2 cmdline.txt

`/boot/cmdline.txt` — suppress boot text for end-user deployment.

Append the following parameters to the existing single-line content. Do not add newlines.

```
quiet loglevel=0 logo.nologo vt.global_cursor_default=0
```

| Parameter | Effect |
|---|---|
| `quiet` | Suppresses most kernel boot messages |
| `loglevel=0` | Suppresses all but emergency kernel messages |
| `logo.nologo` | Removes the Tux penguin logo |
| `vt.global_cursor_default=0` | Hides the terminal cursor |

**Note:** Plymouth animated boot splash is not compatible with the HyperPixel DPI interface and must not be installed. The display will show a blank screen from power-on until GTach initialises.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 GTach Installation

With the Pi booted and accessible at `gtach.local`, install GTach:

```bash
curl -fsSL https://raw.githubusercontent.com/William12556/GTach/main/bin/pi-install.sh | sudo bash
```

See the project `README.md` for full installation and deployment documentation.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Development Access

**For development use only.** Not required for normal GTach operation.

The Pi Zero 2W USB OTG port provides a virtual Ethernet connection to a development laptop. This is the recommended method for SSH access when testing in the car, where no network infrastructure is available.

[Return to Table of Contents](<#table of contents>)

---

### 5.1 Hardware

| Connection | Port |
|---|---|
| Car power supply | `PWR IN` (left micro-USB) |
| Laptop | `USB` (right micro-USB, OTG) |

Both ports may be used simultaneously. The `PWR IN` port is power only. The `USB` port carries data and may also supply power from the laptop.

[Return to Table of Contents](<#table of contents>)

---

### 5.2 Pi Configuration

One-time setup. Requires SSH access to the Pi before in-car testing.

**1. Enable DWC2 overlay**

Append to `/boot/config.txt`:

```ini
# USB OTG — development access
dtoverlay=dwc2
```

**2. Load USB gadget modules**

Append to `/etc/modules`:

```
dwc2
g_ether
```

**3. Reboot**

```bash
reboot
```

[Return to Table of Contents](<#table of contents>)

---

### 5.3 Laptop Connection

Connect a micro-USB cable to the Pi `USB` (OTG) port. macOS detects the Pi as a USB Ethernet device automatically — no driver installation required. A new network interface (e.g., `en7`) appears in System Settings → Network.

SSH to the Pi:

```bash
ssh root@gtach.local
```

`avahi-daemon` runs by default on Raspberry Pi OS and advertises `gtach.local` over all active interfaces including `usb0`. The hostname resolves correctly over USB with no additional configuration.

**Internet access:** The laptop's WiFi connection is unaffected. macOS routes internet traffic over WiFi and Pi traffic over the USB interface independently.

[Return to Table of Contents](<#table of contents>)

---

### 5.4 Verification

```bash
# On Pi — confirm usb0 is up
ip addr show usb0

# On Mac — confirm reachability
ssh root@gtach.local
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-06-19 | Initial draft — hardware, OS, boot configuration, GTach installation |
| 0.2 | 2026-06-19 | §2.0: pinned OS to Debian 11 Bullseye; newer releases not supported |
| 0.3 | 2026-06-19 | §3.1, §3.2: corrected boot file paths to /boot/ for Debian 11 |
| 0.4 | 2026-06-19 | Added §5.0 Development Access — USB OTG configuration for in-car SSH |
| 0.5 | 2026-06-19 | §5.2: removed dhcpcd.conf static IP step — unnecessary; §5.3, §5.4: gtach.local is the SSH target |

---

Copyright (c) 2026 William Watson. MIT License.
