#!/bin/bash
# gtach-preflight.sh — systemd ExecStartPre hook (runs as root). Always exits 0.
# Tier 2 rollback then pending-wheel install, before the application launches.

INSTALL_DIR="/opt/gtach"
UPDATES_DIR="$INSTALL_DIR/updates"
VENV="$INSTALL_DIR/venv"
PENDING="$UPDATES_DIR/.install-pending"
PROBATION="$INSTALL_DIR/.update-probation"
INSTALLED="$INSTALL_DIR/installed.whl"
PREVIOUS="$INSTALL_DIR/previous.whl"
THRESHOLD=2

log() { echo "[gtach-preflight] $*"; }

install_wheel() {
    # Dedicated non-interactive path: no sudo, no prompts, no network.
    "$VENV/bin/pip" install --force-reinstall --no-deps "$1" >/dev/null 2>&1
}

valid_wheel() {
    "$VENV/bin/python" - "$1" <<'PY' 2>/dev/null
import sys, zipfile
p = sys.argv[1]
sys.exit(0 if zipfile.is_zipfile(p) and zipfile.ZipFile(p).testzip() is None else 1)
PY
}

# Step 1 — rollback check
if [ -f "$PROBATION" ]; then
    count="$(cat "$PROBATION" 2>/dev/null)"
    case "$count" in (''|*[!0-9]*) count=0;; esac
    if [ "$count" -ge "$THRESHOLD" ]; then
        log "probation exceeded ($count) — rolling back"
        if [ -f "$PREVIOUS" ] && install_wheel "$PREVIOUS"; then
            cp -f "$PREVIOUS" "$INSTALLED"
            log "rolled back to previous wheel"
        else
            log "ERROR: rollback unavailable or failed"
        fi
        rm -f "$PROBATION"
        exit 0
    fi
    echo "$((count + 1))" > "$PROBATION"
    log "probation attempt $((count + 1))"
fi

# Step 2 — pending install
if [ -f "$PENDING" ]; then
    wheel_name="$(cat "$PENDING" 2>/dev/null)"
    wheel_path="$UPDATES_DIR/$wheel_name"
    if [ -n "$wheel_name" ] && [ -f "$wheel_path" ]; then
        if valid_wheel "$wheel_path"; then
            [ -f "$INSTALLED" ] && cp -f "$INSTALLED" "$PREVIOUS"
            if install_wheel "$wheel_path"; then
                cp -f "$wheel_path" "$INSTALLED"
                echo 0 > "$PROBATION"
                log "installed $wheel_name; probation started"
            else
                log "ERROR: install failed — restoring previous"
                [ -f "$PREVIOUS" ] && install_wheel "$PREVIOUS" && cp -f "$PREVIOUS" "$INSTALLED"
            fi
        else
            log "ERROR: $wheel_name failed zip validation — skipping"
        fi
        rm -f "$wheel_path"
    else
        log "pending marker present but wheel missing"
    fi
    rm -f "$PENDING"
fi

exit 0
