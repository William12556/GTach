#!/bin/bash
# GTach Pi Install Script
# Installs the latest GTach release directly from GitHub.
# Does not require cloning the repository.
# Supports: Linux (Debian/Raspberry Pi OS)
#
# Usage: sudo bash pi-install.sh

set -e

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
INSTALL_DIR="/opt/gtach"
VENV_DIR="$INSTALL_DIR/venv"

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

# ---------------------------------------------------------------------------
# systemd registration
# ---------------------------------------------------------------------------
echo "==> Registering systemd service..."
systemctl daemon-reload
systemctl enable gtach
echo "    Service 'gtach' enabled. Start now with: systemctl start gtach"
