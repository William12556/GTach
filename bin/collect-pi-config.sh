#!/bin/bash
# collect-pi-config.sh — Read-only diagnostic snapshot of the GTach appliance.
#
# Usage (run on Mac):
#   ./collect-pi-config.sh
#
# Connects to root@gtach.local over SSH and prints current boot
# configuration, USB OTG state, I2C/framebuffer state, GTach install state,
# and systemd unit status. Makes no changes on the Pi. Used to confirm
# on-device state before extending bin/pi-install.sh to write boot
# configuration automatically.
#
# Edit PI= below if the address changes.

set -e

PI="root@gtach.local"

echo "==> Connecting to $PI ..."
echo

ssh "$PI" bash -s <<'REMOTE'
section() { printf '\n--- %s ---\n' "$1"; }

section "Host"
hostname
grep -E '^(PRETTY_NAME|VERSION_CODENAME)=' /etc/os-release
uname -m

section "Boot partition"
if [ -f /boot/firmware/cmdline.txt ]; then
    echo "/boot/firmware (Bookworm-style)"
    BOOT_DIR=/boot/firmware
elif [ -f /boot/cmdline.txt ]; then
    echo "/boot (Bullseye-style)"
    BOOT_DIR=/boot
else
    echo "NOT FOUND"
    BOOT_DIR=""
fi

if [ -n "$BOOT_DIR" ]; then
    section "config.txt"
    cat "$BOOT_DIR/config.txt"

    section "cmdline.txt"
    cat "$BOOT_DIR/cmdline.txt"

    section "Existing boot-file backups (e.g. from quiet-boot.sh)"
    ls -1 "$BOOT_DIR"/config.txt.bak-* "$BOOT_DIR"/cmdline.txt.bak-* 2>/dev/null || echo "none"
fi

section "/etc/modules"
cat /etc/modules

section "getty@tty1 state"
systemctl is-enabled getty@tty1 2>&1 || true

section "USB OTG / dwc2 state"
lsmod | grep -E '^(dwc2|g_ether)' || echo "dwc2/g_ether not loaded"
ip addr show usb0 2>&1 || echo "usb0 not present"

section "I2C"
ls /dev/i2c* 2>&1 || echo "no i2c device nodes"

section "Framebuffer"
fbset -fb /dev/fb0 2>&1 || echo "fbset unavailable"

section "GTach install"
ls -la /opt/gtach 2>&1 || echo "/opt/gtach not present"
/opt/gtach/venv/bin/python -c "import importlib.metadata; print('gtach version:', importlib.metadata.version('gtach'))" 2>&1 || echo "gtach package not importable"

section "systemd units"
systemctl is-enabled gtach gtach-boot-splash hyperpixel2r-init bluetooth 2>&1 || true
systemctl is-active  gtach gtach-boot-splash hyperpixel2r-init bluetooth 2>&1 || true
REMOTE

echo
echo "==> Done."
