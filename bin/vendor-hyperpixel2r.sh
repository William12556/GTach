#!/bin/bash
# vendor-hyperpixel2r.sh — One-time extraction of the Pimoroni HyperPixel 2r
# driver artifacts from a working installation on root@gtach.local into this
# repository, so pi-install.sh can install them directly without a live
# dependency on the pimoroni/hyperpixel2r repository at setup time.
#
# Usage (run on Mac, from repo root):
#   ./bin/vendor-hyperpixel2r.sh
#
# See bin/vendor/hyperpixel2r/NOTICE.md for provenance and license.
#
# Edit PI= below if the address changes.

set -e

PI="root@gtach.local"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENDOR_DIR="$SCRIPT_DIR/vendor/hyperpixel2r"

mkdir -p "$VENDOR_DIR"

echo "==> Pulling HyperPixel 2r driver artifacts from $PI ..."
scp "$PI:/boot/overlays/hyperpixel2r.dtbo"               "$VENDOR_DIR/"
scp "$PI:/usr/bin/hyperpixel2r-init"                     "$VENDOR_DIR/"
scp "$PI:/usr/bin/hyperpixel2r-rotate"                   "$VENDOR_DIR/"
scp "$PI:/etc/systemd/system/hyperpixel2r-init.service"  "$VENDOR_DIR/"

chmod 0644 "$VENDOR_DIR/hyperpixel2r.dtbo" "$VENDOR_DIR/hyperpixel2r-init.service"
chmod 0755 "$VENDOR_DIR/hyperpixel2r-init" "$VENDOR_DIR/hyperpixel2r-rotate"

echo "==> Done. Files in $VENDOR_DIR:"
ls -la "$VENDOR_DIR"
