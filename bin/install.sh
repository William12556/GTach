#!/bin/bash
# GTach Install Script
# Supports: Linux (Debian/Raspberry Pi)
# Usage: ./install.sh <wheel-filename>
#
# Linux: installs to /opt/gtach/, configures boot settings for the
# HyperPixel 2.1 Round display and USB OTG, installs the vendored
# HyperPixel driver (see bin/vendor/hyperpixel2r/NOTICE.md), and registers
# the systemd service.
#
# Idempotent: safe to re-run. Boot files are backed up before any write, as
# $FILE.bak-<timestamp>, and only touched when a change is actually needed.

set -e  # Exit on error

# ---------------------------------------------------------------------------
# OS detection
# ---------------------------------------------------------------------------
OS="$(uname -s)"
case "$OS" in
    Linux*)
        INSTALL_DIR="/opt/gtach"
        ;;
    *)
        echo "ERROR: Unsupported operating system: $OS (Linux only)"
        exit 1
        ;;
esac

VENV_DIR="$INSTALL_DIR/venv"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d-%H%M%S)"

# ---------------------------------------------------------------------------
# Argument validation
# ---------------------------------------------------------------------------
if [ -z "$1" ]; then
    echo "ERROR: Wheel filename required"
    echo "Usage: ./install.sh gtach-X.Y.Z-py3-none-any.whl"
    exit 1
fi

WHEEL="$1"
VERSION=$(echo "$WHEEL" | cut -d'-' -f2)

echo "==> Installing gtach version $VERSION"
echo "==> Platform: $OS"
echo "==> Install directory: $INSTALL_DIR"

# ---------------------------------------------------------------------------
# python3 availability check
# ---------------------------------------------------------------------------
if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found in PATH"
    echo "Install Python 3:  sudo apt-get install python3 python3-venv"
    exit 1
fi

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
        echo "# Added by install.sh on $STAMP"
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
# HyperPixel driver — vendored artifacts, transferred locally by deploy.sh
# Source, license basis, and provenance: bin/vendor/hyperpixel2r/NOTICE.md
# ---------------------------------------------------------------------------
echo "==> Installing HyperPixel 2r driver..."

install -m 0644 "$SCRIPT_DIR/hyperpixel2r.dtbo"         /boot/overlays/hyperpixel2r.dtbo
install -m 0755 "$SCRIPT_DIR/hyperpixel2r-init"         /usr/bin/hyperpixel2r-init
install -m 0755 "$SCRIPT_DIR/hyperpixel2r-rotate"       /usr/bin/hyperpixel2r-rotate
install -m 0644 "$SCRIPT_DIR/hyperpixel2r-init.service" /etc/systemd/system/hyperpixel2r-init.service

systemctl daemon-reload
systemctl enable hyperpixel2r-init.service
echo "    hyperpixel2r-init.service enabled"

# ---------------------------------------------------------------------------
# Directory structure and clean state (Linux only)
# ---------------------------------------------------------------------------
if [ "$OS" = "Linux" ]; then
    echo "==> Ensuring directory structure..."
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$INSTALL_DIR/updates"

    echo "==> Cleaning stale state..."
    # Promote current known-good wheel to previous before overwriting
    [ -f "$INSTALL_DIR/installed.whl" ] && cp -f "$INSTALL_DIR/installed.whl" "$INSTALL_DIR/previous.whl" || true
    # Clear state markers — full manual install is a clean slate
    rm -f "$INSTALL_DIR/.update-probation" || true
    rm -f "$INSTALL_DIR/updates/.install-pending" || true
    # Remove old tee-based log files (superseded by app-owned logging)
    rm -f "$INSTALL_DIR/gtach-debug.log" "$INSTALL_DIR/gtach-debug_PI.log" || true
fi

# ---------------------------------------------------------------------------
# Virtual environment setup
# ---------------------------------------------------------------------------
if [ ! -d "$VENV_DIR" ]; then
    echo "==> Creating virtual environment at $VENV_DIR"
    python3 -m venv "$VENV_DIR"
fi

# ---------------------------------------------------------------------------
# Install package
# ---------------------------------------------------------------------------
echo "==> Cleaning existing installation..."
"$VENV_DIR/bin/pip" uninstall -y gtach 2>/dev/null || true

# Handle both relative and absolute wheel paths
if [[ "$WHEEL" = /* ]]; then
    WHEEL_PATH="$WHEEL"
else
    WHEEL_PATH="/tmp/$WHEEL"
fi

echo "==> Installing from $WHEEL_PATH"
"$VENV_DIR/bin/pip" install "$WHEEL_PATH"

# ---------------------------------------------------------------------------
# Version verification
# ---------------------------------------------------------------------------
echo "==> Verifying installation..."
INSTALLED=$("$VENV_DIR/bin/python" -c "import os; os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'; import gtach; print(gtach.__version__)")

if [ "$INSTALLED" != "$VERSION" ]; then
    echo "ERROR: Version mismatch - expected $VERSION, got $INSTALLED"
    exit 1
fi

echo ""
echo "✓ Installation successful: version $INSTALLED"
echo ""

# ---------------------------------------------------------------------------
# Post-install: platform-specific instructions
# ---------------------------------------------------------------------------
# ---- systemd service + boot-time update supervisor ----
echo "==> Registering systemd service and update supervisor"
install -m 0644 "$SCRIPT_DIR/gtach.service" /etc/systemd/system/gtach.service
if [ "$SCRIPT_DIR/gtach-preflight.sh" != "$INSTALL_DIR/gtach-preflight.sh" ]; then
    install -m 0755 "$SCRIPT_DIR/gtach-preflight.sh" "$INSTALL_DIR/gtach-preflight.sh"
else
    chmod 0755 "$INSTALL_DIR/gtach-preflight.sh"
fi
cp -f "$WHEEL_PATH" "$INSTALL_DIR/installed.whl"

echo "==> Registering boot splash"
install -m 0644 "$SCRIPT_DIR/gtach-boot-splash.service" /etc/systemd/system/gtach-boot-splash.service
if [ "$SCRIPT_DIR/boot-splash.raw" != "$INSTALL_DIR/boot-splash.raw" ]; then
    install -m 0644 "$SCRIPT_DIR/boot-splash.raw" "$INSTALL_DIR/boot-splash.raw"
else
    chmod 0644 "$INSTALL_DIR/boot-splash.raw"
fi

systemctl daemon-reload
systemctl enable gtach
systemctl enable gtach-boot-splash
echo "    Service 'gtach' enabled. Start now with: systemctl start gtach"

echo "Run gtach with:"
echo "  $VENV_DIR/bin/gtach"
