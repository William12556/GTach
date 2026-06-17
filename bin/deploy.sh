#!/bin/bash
# deploy.sh — Mac-side build and deploy to the Pi.
#
# Usage:
#   ./deploy.sh           Full deploy: build, transfer all files, install, restart service.
#   ./deploy.sh --stage   Stage update: build, transfer wheel to Pi drop directory only.
#                         Use 'Check for updates' in GTach OPTIONS to install.
#
# The Pi is addressed as root@gtach.local. Edit PI= below if the address changes.

set -e

PI="root@gtach.local"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
INSTALL_DIR="/opt/gtach"

# ---------------------------------------------------------------------------
# Mode
# ---------------------------------------------------------------------------
MODE="full"
if [ "$1" = "--stage" ] || [ "$1" = "--stage-update" ]; then
    MODE="stage"
fi

# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
echo "==> Building GTach..."
cd "$PROJECT_ROOT"
"$SCRIPT_DIR/build.sh"

# Find the wheel produced by build.sh
WHEEL=$(ls dist/gtach-*.whl 2>/dev/null | sort -V | tail -1)
if [ -z "$WHEEL" ]; then
    echo "ERROR: No wheel found in dist/"
    exit 1
fi
WHEEL_NAME=$(basename "$WHEEL")
VERSION=$(echo "$WHEEL_NAME" | cut -d'-' -f2)
echo "==> Wheel: $WHEEL_NAME (v$VERSION)"

# ---------------------------------------------------------------------------
# Stage mode — transfer wheel to drop directory only
# ---------------------------------------------------------------------------
if [ "$MODE" = "stage" ]; then
    echo "==> Staging $WHEEL_NAME on Pi at $INSTALL_DIR/updates/..."
    ssh "$PI" "mkdir -p $INSTALL_DIR/updates"
    scp "$WHEEL" "${PI}:${INSTALL_DIR}/updates/"
    echo ""
    echo "✓ Staged v$VERSION. Use 'Check for updates' in GTach OPTIONS to install."
    exit 0
fi

# ---------------------------------------------------------------------------
# Full deploy — stop service, transfer all files, install, start service
# ---------------------------------------------------------------------------
echo "==> Stopping GTach service on Pi..."
ssh "$PI" "systemctl stop gtach || true"

echo "==> Ensuring $INSTALL_DIR exists on Pi..."
ssh "$PI" "mkdir -p $INSTALL_DIR"

echo "==> Transferring wheel..."
scp "$WHEEL" "${PI}:/tmp/"

echo "==> Transferring deploy files..."
scp "$SCRIPT_DIR/install.sh" "${PI}:${INSTALL_DIR}/"
scp "$SCRIPT_DIR/gtach.service" "${PI}:${INSTALL_DIR}/"
scp "$SCRIPT_DIR/gtach-preflight.sh" "${PI}:${INSTALL_DIR}/"

echo "==> Running install on Pi..."
ssh "$PI" "$INSTALL_DIR/install.sh /tmp/$WHEEL_NAME"

echo "==> Starting GTach service..."
ssh "$PI" "systemctl start gtach"

echo ""
echo "✓ Deployed v$VERSION to Pi."
