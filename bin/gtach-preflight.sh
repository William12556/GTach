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

check_env() {
    # Verify the environment's dependencies are consistent
    # (issue-52653cd6). On a pip check failure its output is logged.
    local out
    if ! out="$("$VENV/bin/pip" check 2>&1)"; then
        log "ERROR: pip check failed after installing $(basename "$1"):"
        log "$out"
        return 1
    fi
}

install_and_check() {
    install_wheel "$1" || return 1
    check_env "$1"
}

restore_previous() {
    # Reinstall the previous wheel. installed.whl follows what pip
    # installed, whatever pip check then reports, so a later update
    # cannot save a rejected wheel as previous.whl (audit-71ab3751 G02).
    [ -f "$PREVIOUS" ] || return 1
    install_wheel "$PREVIOUS" || return 1
    cp -f "$PREVIOUS" "$INSTALLED"
    check_env "$PREVIOUS" || log "WARNING: environment inconsistent after restoring previous wheel"
    return 0
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
        if restore_previous; then
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
            if install_and_check "$wheel_path"; then
                cp -f "$wheel_path" "$INSTALLED"
                echo 0 > "$PROBATION"
                log "installed $wheel_name; probation started"
            else
                log "ERROR: install failed — restoring previous"
                if ! restore_previous; then
                    # Nothing to restore: the rejected wheel may still be
                    # installed, and no rollback is possible (audit-71ab3751 G02).
                    log "ERROR: no previous wheel restored — $wheel_name may remain installed without rollback protection"
                fi
                rm -f "$PROBATION"
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
