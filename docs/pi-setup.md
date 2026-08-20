Created: 2026 June 19

# GTach — Raspberry Pi Zero 2W Hardware Setup

---

## Table of Contents

[1.0 Hardware](<#1.0 hardware>)
[2.0 Operating System](<#2.0 operating system>)
[3.0 Boot Configuration](<#3.0 boot configuration>)
[3.1 config.txt](<#3.1 config.txt>)
[3.2 cmdline.txt](<#3.2 cmdline.txt>)
[3.3 HyperPixel Driver](<#3.3 hyperpixel driver>)
[3.4 USB OTG](<#3.4 usb otg>)
[4.0 GTach Installation](<#4.0 gtach installation>)
[5.0 Development Access](<#5.0 development access>)
[5.1 Hardware](<#5.1 hardware>)
[5.2 Laptop Connection](<#5.2 laptop connection>)
[5.3 Verification](<#5.3 verification>)
[6.0 References](<#6.0 references>)
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

**Backlight note:** The display backlight does not turn off automatically when the Pi shuts down. For longevity, cut power at the source (e.g. ignition-switched supply) rather than relying on a software shutdown to blank the panel (Pimoroni Ltd., 2026).

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

OS provisioning is the only manual step. Everything in §3.0 below is applied automatically by the installer described in §4.0 — the reference material is retained here for troubleshooting, not as instructions to follow by hand.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Boot Configuration

Applied automatically by `bin/pi-install.sh` and `bin/install.sh`. Both scripts check each setting before writing it — an already-configured device is left untouched — and back up any file they modify as `<file>.bak-<timestamp>` before the first change.

### 3.1 config.txt

`/boot/config.txt` — HyperPixel 2.1 Round DPI settings plus the USB OTG overlay (§3.4).

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

dtoverlay=dwc2
```

**Notes:**

- `disable_splash=1` suppresses the Pi firmware rainbow splash. Required — Plymouth is not supported with the DPI interface.
- `hdmi_force_hotplug=1` / `hdmi_mode=1` / `hdmi_group=1` work around a Pygame limitation, not a GTach requirement: the Pygame version shipped with Raspberry Pi OS rejects non-standard resolutions such as 480×480 unless a standard HDMI mode is first forced (Pimoroni, 2026b).
- `dtoverlay=hyperpixel2r:disable-touch` loads the HyperPixel kernel driver (§3.3). Touch is disabled; GTach does not use touch input.
- `dtparam=i2c_arm=on` enables I2C. Required by the HyperPixel driver.
- `dtoverlay=dwc2` enables USB OTG (§3.4).
- Do not add `dtoverlay=vc4-kms-dpi-hyperpixel2r`. This is Pimoroni's current recommended overlay for Bullseye and later (Pimoroni Ltd., 2026), built into the OS kernel rather than requiring the driver in §3.3. GTach deliberately uses the legacy overlay above instead, since that is the configuration verified working on GTach hardware. Do not mix settings from the two approaches.

[Return to Table of Contents](<#table of contents>)

---

### 3.2 cmdline.txt

`/boot/cmdline.txt` — suppress boot text and the local console login for end-user deployment. Appended to the existing single-line content; never replaces it.

```
quiet loglevel=0 logo.nologo vt.global_cursor_default=0 systemd.show_status=0
```

| Parameter | Effect |
|---|---|
| `quiet` | Suppresses most kernel boot messages |
| `loglevel=0` | Suppresses all but emergency kernel messages |
| `logo.nologo` | Removes the Tux penguin logo |
| `vt.global_cursor_default=0` | Hides the terminal cursor |
| `systemd.show_status=0` | Suppresses systemd's own `[ OK ]` boot lines |

In addition, `getty@tty1` is masked, removing the local console login prompt that would otherwise appear on the panel once boot completes. SSH access is unaffected.

**Note:** Plymouth animated boot splash is not compatible with the HyperPixel DPI interface and must not be installed. The display shows a blank screen from power-on until GTach initialises.

[Return to Table of Contents](<#table of contents>)

---

### 3.3 HyperPixel Driver

The HyperPixel 2.1 Round requires Pimoroni's `hyperpixel2r` kernel driver — the compiled device-tree overlay, an initialisation binary, and a systemd unit that `gtach.service` depends on. GTach vendors these as pre-built artifacts in `bin/vendor/hyperpixel2r/`, rather than cloning and building Pimoroni's repository at setup time. Source, license basis, and provenance are documented in `bin/vendor/hyperpixel2r/NOTICE.md`.

| Installed file | Target |
|---|---|
| `hyperpixel2r.dtbo` | `/boot/overlays/hyperpixel2r.dtbo` |
| `hyperpixel2r-init` | `/usr/bin/hyperpixel2r-init` |
| `hyperpixel2r-rotate` | `/usr/bin/hyperpixel2r-rotate` (unused by GTach; installed for completeness) |
| `hyperpixel2r-init.service` | `/etc/systemd/system/hyperpixel2r-init.service`, enabled |

**Known fragility:** Pimoroni's own issue tracker documents unreliable HyperPixel 2r behaviour specifically on Raspberry Pi Zero 2 with Bullseye — the display can flash the boot logo and then go blank (Pimoroni, 2021). GTach's configuration is verified working, but this combination is not guaranteed reliable by the upstream driver. Confirm the display is producing output after the first reboot following installation.

[Return to Table of Contents](<#table of contents>)

---

### 3.4 USB OTG

The Pi Zero 2W's USB OTG port is configured for use as a development-access network interface (§5.0) as part of standard setup, not as an optional step.

`/etc/modules` — kernel modules loaded at boot:

```
i2c-dev
dwc2
g_ether
```

`i2c-dev` and `dwc2` are also declared in `config.txt` (§3.1); the `/etc/modules` entries ensure they load at boot without depending on overlay auto-loading behaviour.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 GTach Installation

Two entry points, both idempotent — safe to re-run, and safe to run on a device that already has some or all settings applied.

**Standard install** — on a Pi already booted and reachable at `gtach.local`:

```bash
curl -fsSL https://raw.githubusercontent.com/William12556/GTach/main/bin/pi-install.sh | sudo bash
```

Applies §3.0 boot configuration, installs the HyperPixel driver, installs the GTach package from the latest GitHub release, and registers the systemd services. Prompts for confirmation before rebooting — a reboot is required for the boot configuration and driver changes to take effect.

**Developer install** — from a cloned repository on Mac, via `./bin/deploy.sh` (see project `README.md` §4.0). `deploy.sh` transfers the wheel, service files, and vendored driver files to the Pi and runs `bin/install.sh`, which applies the same boot configuration and driver installation as `pi-install.sh`. `deploy.sh` reboots the Pi automatically after installation.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Development Access

**For development use only.** Not required for normal GTach operation. USB OTG itself is configured automatically (§3.4); this section covers the physical connection and its use for SSH access.

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

### 5.2 Laptop Connection

Connect a micro-USB cable to the Pi `USB` (OTG) port. macOS detects the Pi as a USB Ethernet device automatically — no driver installation required. A new network interface appears in System Settings → Network.

SSH to the Pi:

```bash
ssh root@gtach.local
```

`avahi-daemon` runs by default on Raspberry Pi OS and advertises `gtach.local` over all active interfaces including `usb0`. The hostname resolves correctly over USB with no additional configuration.

**Internet access:** The laptop's WiFi connection is unaffected. macOS routes internet traffic over WiFi and Pi traffic over the USB interface independently.

[Return to Table of Contents](<#table of contents>)

---

### 5.3 Verification

```bash
# On Pi — confirm usb0 is up
ip addr show usb0

# On Mac — confirm reachability
ssh root@gtach.local
```

[Return to Table of Contents](<#table of contents>)

---

## 6.0 References

Pimoroni Ltd. (2026) *HyperPixel 2.1 Round – Hi-Res Display for Raspberry Pi*. Available at: https://shop.pimoroni.com/products/hyperpixel-round (Accessed: 20 August 2026).

Pimoroni (2026a) *hyperpixel2r* [GitHub repository]. Available at: https://github.com/pimoroni/hyperpixel2r (Accessed: 20 August 2026).

Pimoroni (2026b) *hyperpixel2r-python* [GitHub repository]. Available at: https://github.com/pimoroni/hyperpixel2r-python (Accessed: 20 August 2026).

Pimoroni (2021) *Compatibility with Raspberry Pi Zero 2*, Issue #1, pimoroni/hyperpixel2r [GitHub]. Available at: https://github.com/pimoroni/hyperpixel2r/issues/1 (Accessed: 20 August 2026).

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
| 0.6 | 2026-08-20 | Reframed §3.0 as automated (applied by pi-install.sh/install.sh) rather than manual instructions; added §3.3 HyperPixel Driver (vendored, previously undocumented) and §3.4 USB OTG (moved from §5.0, now default rather than dev-only); §1.0 added backlight longevity note; §4.0 rewritten for both install entry points and idempotency; §5.0 narrowed to physical connection/use, removed now-redundant manual OTG configuration steps; added §6.0 References; removed a stray unresolved merge-conflict marker from the former §5.3 |

---

Copyright (c) 2026 William Watson. MIT License.
