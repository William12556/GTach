#!/bin/bash
# GTach Pi Install Script
# Installs the latest GTach release directly from GitHub, configures boot
# settings for the HyperPixel 2.1 Round display and USB OTG, and installs
# the vendored HyperPixel driver (see bin/vendor/hyperpixel2r/NOTICE.md).
# Does not require cloning the repository.
# Supports: Linux (Debian/Raspberry Pi OS)
#
# Usage: sudo bash pi-install.sh
#
# Idempotent: safe to re-run. Boot files are backed up before any write, as
# $FILE.bak-<timestamp>, and only touched when a change is actually needed.

set -e

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
INSTALL_DIR="/opt/gtach"
VENV_DIR="$INSTALL_DIR/venv"
STAMP="$(date +%Y%m%d-%H%M%S)"

# ---------------------------------------------------------------------------
# OS check
# ---------------------------------------------------------------------------
OS="$(uname -s)"
if [[ "$OS" != Linux* ]]; then
    echo "ERROR: Unsupported operating system: $OS (Linux only)"
    exit 1
fi

# ---------------------------------------------------------------------------
# Dependency checks
# ---------------------------------------------------------------------------
for cmd in python3 git curl; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "ERROR: $cmd not found in PATH"
        echo "Install with: sudo apt-get install $cmd"
        exit 1
    fi
done

# ---------------------------------------------------------------------------
# Resolve latest release tag
# ---------------------------------------------------------------------------
echo "==> Resolving latest release..."
LATEST=$(curl -fsSL https://api.github.com/repos/William12556/GTach/releases/latest \
    | grep '"tag_name"' | cut -d'"' -f4)

if [ -z "$LATEST" ]; then
    echo "ERROR: Could not resolve latest release tag"
    exit 1
fi

GITHUB_RAW="https://raw.githubusercontent.com/William12556/GTach/${LATEST}/bin"

echo "==> Installing GTach ${LATEST}"
echo "==> Install directory: $INSTALL_DIR"

# ---------------------------------------------------------------------------
# Boot configuration — HyperPixel display + USB OTG
#
# /boot/config.txt, /boot/cmdline.txt and /etc/modules are edited
# append-only, and only when a directive is actually missing, so this
# section is safe to re-run and never disturbs device-specific content
# already present (e.g. a Wi-Fi regulatory domain token added by Raspberry
# Pi Imager). Each file is backed up as $FILE.bak-$STAMP immediately before
# its first write.
# ---------------------------------------------------------------------------
echo "==> Checking boot configuration..."

if [ -f /boot/firmware/cmdline.txt ]; then
    BOOT_DIR="/boot/firmware"
elif [ -f /boot/cmdline.txt ]; then
    BOOT_DIR="/boot"
else
    echo "ERROR: cannot find cmdline.txt in /boot/firmware or /boot"
    exit 1
fi

CONFIG="$BOOT_DIR/config.txt"
CMDLINE="$BOOT_DIR/cmdline.txt"
MODULES="/etc/modules"

# --- config.txt: HyperPixel DPI block + USB OTG overlay ---
CONFIG_LINES=(
    "arm_64bit=1"
    "boot_delay=0"
    "initial_turbo=30"
    "arm_boost=1"
    "avoid_warnings=1"
    "disable_splash=1"
    "gpu_mem=128"
    "hdmi_force_hotplug=1"
    "hdmi_mode=1"
    "hdmi_group=1"
    "dtoverlay=hyperpixel2r:disable-touch"
    "enable_dpi_lcd=1"
    "dpi_group=2"
    "dpi_mode=87"
    "dpi_output_format=0x7f216"
    "dpi_timings=480 0 10 16 55 480 0 15 60 15 0 0 0 60 0 19200000 6"
    "dtparam=i2c_arm=on"
    "dtoverlay=dwc2"
)

CONFIG_ADDITIONS=()
for line in "${CONFIG_LINES[@]}"; do
    if grep -qxF "$line" "$CONFIG" 2>/dev/null; then
        :
    else
        CONFIG_ADDITIONS+=("$line")
    fi
done

if [ ${#CONFIG_ADDITIONS[@]} -gt 0 ]; then
    cp "$CONFIG" "$CONFIG.bak-$STAMP"
    echo "    Backed up to $CONFIG.bak-$STAMP"
    {
        echo ""
        echo "# Added by pi-install.sh on $STAMP"
        printf '%s\n' "${CONFIG_ADDITIONS[@]}"
    } >> "$CONFIG"
    echo "    Added ${#CONFIG_ADDITIONS[@]} line(s) to $CONFIG"
else
    echo "    $CONFIG already configured"
fi

# --- cmdline.txt: quiet boot parameters (must remain a single line) ---
CMDLINE_PARAMS=(
    "quiet"
    "loglevel=0"
    "logo.nologo"
    "vt.global_cursor_default=0"
    "systemd.show_status=0"
)

ORIGINAL="$(tr -d '\n' < "$CMDLINE")"
NEW="$ORIGINAL"
for p in "${CMDLINE_PARAMS[@]}"; do
    key="${p%%=*}"
    if grep -qE "(^| )${key}(=| |$)" <<<"$NEW"; then
        :
    else
        NEW="$NEW $p"
    fi
done
NEW="$(tr -s ' ' <<<"$NEW")"
NEW="${NEW#"${NEW%%[![:space:]]*}"}"
NEW="${NEW%"${NEW##*[![:space:]]}"}"

if [ "$NEW" != "$ORIGINAL" ]; then
    cp "$CMDLINE" "$CMDLINE.bak-$STAMP"
    echo "    Backed up to $CMDLINE.bak-$STAMP"
    printf '%s\n' "$NEW" > "$CMDLINE"

    # Verify before trusting the write: exactly one line, root= present.
    LINES="$(wc -l < "$CMDLINE")"
    [ "$LINES" -eq 1 ] || { cp "$CMDLINE.bak-$STAMP" "$CMDLINE"; echo "ERROR: wrote $LINES lines, expected 1 — restored backup"; exit 1; }
    grep -q 'root=' "$CMDLINE" || { cp "$CMDLINE.bak-$STAMP" "$CMDLINE"; echo "ERROR: result has no root= — restored backup"; exit 1; }
    echo "    Updated $CMDLINE"
else
    echo "    $CMDLINE already configured"
fi

# --- getty@tty1: masked so the login prompt never appears on the panel ---
if systemctl is-enabled getty@tty1 2>/dev/null | grep -q masked; then
    echo "    getty@tty1 already masked"
else
    systemctl mask getty@tty1
    echo "    Masked getty@tty1"
fi

# --- /etc/modules: I2C + USB OTG gadget modules ---
MODULE_LINES=("i2c-dev" "dwc2" "g_ether")
MODULES_ADDITIONS=()
for m in "${MODULE_LINES[@]}"; do
    if grep -qxF "$m" "$MODULES" 2>/dev/null; then
        :
    else
        MODULES_ADDITIONS+=("$m")
    fi
done

if [ ${#MODULES_ADDITIONS[@]} -gt 0 ]; then
    cp "$MODULES" "$MODULES.bak-$STAMP"
    echo "    Backed up to $MODULES.bak-$STAMP"
    printf '%s\n' "${MODULES_ADDITIONS[@]}" >> "$MODULES"
    echo "    Added ${#MODULES_ADDITIONS[@]} line(s) to $MODULES"
else
    echo "    $MODULES already configured"
fi

# ---------------------------------------------------------------------------
# HyperPixel driver — vendored artifacts
# Source, license basis, and provenance: bin/vendor/hyperpixel2r/NOTICE.md
# ---------------------------------------------------------------------------
echo "==> Installing HyperPixel 2r driver..."
VENDOR_RAW="https://raw.githubusercontent.com/William12556/GTach/${LATEST}/bin/vendor/hyperpixel2r"

curl -fsSL "${VENDOR_RAW}/hyperpixel2r.dtbo"          -o /boot/overlays/hyperpixel2r.dtbo
curl -fsSL "${VENDOR_RAW}/hyperpixel2r-init"          -o /usr/bin/hyperpixel2r-init
curl -fsSL "${VENDOR_RAW}/hyperpixel2r-rotate"        -o /usr/bin/hyperpixel2r-rotate
curl -fsSL "${VENDOR_RAW}/hyperpixel2r-init.service"  -o /etc/systemd/system/hyperpixel2r-init.service

chmod 0644 /boot/overlays/hyperpixel2r.dtbo /etc/systemd/system/hyperpixel2r-init.service
chmod 0755 /usr/bin/hyperpixel2r-init /usr/bin/hyperpixel2r-rotate

systemctl daemon-reload
systemctl enable hyperpixel2r-init.service
echo "    hyperpixel2r-init.service enabled"

# ---------------------------------------------------------------------------
# Directory structure and clean state
# ---------------------------------------------------------------------------
echo "==> Ensuring directory structure..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR/updates"

echo "==> Cleaning stale state..."
[ -f "$INSTALL_DIR/installed.whl" ] && cp -f "$INSTALL_DIR/installed.whl" "$INSTALL_DIR/previous.whl" || true
rm -f "$INSTALL_DIR/.update-probation" || true
rm -f "$INSTALL_DIR/updates/.install-pending" || true
rm -f "$INSTALL_DIR/gtach-debug.log" "$INSTALL_DIR/gtach-debug_PI.log" || true

# ---------------------------------------------------------------------------
# Virtual environment
# ---------------------------------------------------------------------------
if [ ! -d "$VENV_DIR" ]; then
    echo "==> Creating virtual environment at $VENV_DIR"
    python3 -m venv "$VENV_DIR"
fi

# ---------------------------------------------------------------------------
# Install package from GitHub
# ---------------------------------------------------------------------------
echo "==> Cleaning existing installation..."
"$VENV_DIR/bin/pip" uninstall -y gtach 2>/dev/null || true

echo "==> Installing from GitHub (${LATEST})..."
"$VENV_DIR/bin/pip" install \
    --extra-index-url https://www.piwheels.org/simple/ \
    "git+https://github.com/William12556/GTach.git@${LATEST}[pi]"

# ---------------------------------------------------------------------------
# Version verification
# ---------------------------------------------------------------------------
echo "==> Verifying installation..."
INSTALLED=$("$VENV_DIR/bin/python" -c \
    "import importlib.metadata; print(importlib.metadata.version('gtach'))")

echo ""
echo "✓ Installation successful: version $INSTALLED"
echo ""

# ---------------------------------------------------------------------------
# Service files
# ---------------------------------------------------------------------------
echo "==> Fetching service files..."
curl -fsSL "${GITHUB_RAW}/gtach.service"       -o /etc/systemd/system/gtach.service
curl -fsSL "${GITHUB_RAW}/gtach-preflight.sh"  -o "${INSTALL_DIR}/gtach-preflight.sh"
chmod 0755 "${INSTALL_DIR}/gtach-preflight.sh"

echo "==> Fetching boot splash..."
curl -fsSL "${GITHUB_RAW}/gtach-boot-splash.service" -o /etc/systemd/system/gtach-boot-splash.service
curl -fsSL "${GITHUB_RAW}/boot-splash.raw"            -o "${INSTALL_DIR}/boot-splash.raw"

# ---------------------------------------------------------------------------
# systemd registration
# ---------------------------------------------------------------------------
echo "==> Registering systemd service..."
systemctl daemon-reload
systemctl enable gtach
systemctl enable gtach-boot-splash
echo "    Service 'gtach' enabled — will start automatically after reboot."

# ---------------------------------------------------------------------------
# Reboot — required for boot configuration and driver changes to take effect
# ---------------------------------------------------------------------------
echo ""
echo "A reboot is required for the boot configuration and HyperPixel driver"
echo "changes to take effect. 'gtach' will not display correctly until then."

if [ -r /dev/tty ]; then
    read -r -p "Reboot now? [y/N] " REPLY < /dev/tty
else
    REPLY="n"
fi

case "$REPLY" in
    [yY]*)
        echo "==> Rebooting..."
        reboot
        ;;
    *)
        echo "Not rebooting. Run 'sudo reboot' when ready."
        ;;
esac
