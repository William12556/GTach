#!/bin/bash
# quiet-boot.sh — Suppress Linux boot output on the GTach display.
#
# Usage (run ON the Pi, as root):
#   sudo bash quiet-boot.sh            # apply
#   sudo bash quiet-boot.sh --dry-run  # show what would change, touch nothing
#   sudo bash quiet-boot.sh --revert   # restore from the newest backup
#
# docs/pi-setup.md §3.1 and §3.2 already specify disable_splash=1 and
# 'quiet loglevel=0 logo.nologo vt.global_cursor_default=0'. Those silence
# the firmware splash, the kernel ring buffer, the Tux logo and the cursor.
# They do not silence:
#
#   - the getty login prompt, which systemd puts on tty1 — the framebuffer
#     console — once boot completes, and which then sits on the panel until
#     GTach draws over it;
#   - systemd's own '[ OK ] Started ...' lines, which do not come from the
#     kernel and are unaffected by 'quiet'.
#
# This script masks getty@tty1 (no more login prompt on the panel) and adds
# systemd.show_status=0 (no more '[ OK ]' lines). console= is left at tty1;
# an earlier version of this script redirected console output to tty3 on
# the theory that tty3 is never displayed. It is not: console= also selects
# the active/foreground VT at boot, so redirecting there made tty3 — not
# tty1 — the VT sharing fbcon's framebuffer with GTach's direct /dev/fb0
# writes. Any later console write (an unmasked autovt getty, cron, wall,
# journald-to-console forwarding) then overwrote GTach's display. Leaving
# console=tty1 and masking only getty@tty1 avoids this.
#
# This script is idempotent: running it twice changes nothing the second
# time.
#
# WHAT YOU LOSE: masking getty@tty1 removes the local console login. SSH is
# unaffected. Recover with --revert, or from another machine.
#
# Copyright (c) 2026 William Watson. MIT License.

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Parameters added to cmdline.txt. console= is intentionally left untouched
# — see header comment for why redirecting it to another VT is unsafe.
CMDLINE_PARAMS=(
    "quiet"
    "loglevel=0"
    "logo.nologo"
    "vt.global_cursor_default=0"
    "systemd.show_status=0"
)

CONFIG_PARAMS=( "disable_splash=1" )

STAMP="$(date +%Y%m%d-%H%M%S)"
DRY_RUN=0
REVERT=0

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=1 ;;
        --revert)  REVERT=1 ;;
        -h|--help) sed -n '2,25p' "$0"; exit 0 ;;
        *) echo "Unknown argument: $arg" >&2; exit 2 ;;
    esac
done

say()  { echo "==> $*"; }
warn() { echo "WARNING: $*" >&2; }
die()  { echo "ERROR: $*" >&2; exit 1; }

# ---------------------------------------------------------------------------
# Preconditions
# ---------------------------------------------------------------------------
[ "$(id -u)" -eq 0 ] || die "must be run as root (use sudo)"

# Boot partition moved in Raspberry Pi OS Bookworm. Detect rather than assume.
if   [ -f /boot/firmware/cmdline.txt ]; then BOOT_DIR="/boot/firmware"
elif [ -f /boot/cmdline.txt ];          then BOOT_DIR="/boot"
else die "cannot find cmdline.txt in /boot/firmware or /boot"
fi

CMDLINE="$BOOT_DIR/cmdline.txt"
CONFIG="$BOOT_DIR/config.txt"
[ -f "$CONFIG" ] || die "cannot find $CONFIG"

say "Boot partition: $BOOT_DIR"

# ---------------------------------------------------------------------------
# Revert
# ---------------------------------------------------------------------------
if [ "$REVERT" -eq 1 ]; then
    newest_backup() { ls -1t "$1".bak-* 2>/dev/null | head -1; }

    CB="$(newest_backup "$CMDLINE")" || true
    GB="$(newest_backup "$CONFIG")"  || true

    [ -n "${CB:-}" ] || die "no backup found for $CMDLINE"

    say "Restoring $CMDLINE from $(basename "$CB")"
    cp "$CB" "$CMDLINE"

    if [ -n "${GB:-}" ]; then
        say "Restoring $CONFIG from $(basename "$GB")"
        cp "$GB" "$CONFIG"
    fi

    if systemctl is-enabled getty@tty1 2>/dev/null | grep -q masked; then
        say "Unmasking getty@tty1"
        systemctl unmask getty@tty1
    fi

    say "Reverted. Reboot to apply."
    exit 0
fi

# ---------------------------------------------------------------------------
# cmdline.txt
#
# This file MUST remain a single line. A stray newline makes the Pi
# unbootable, and recovery means pulling the card. Everything below builds
# the new content in a variable and writes it in one go.
# ---------------------------------------------------------------------------
say "Reading $CMDLINE"

# tr -d strips any newline the file already carries; the kernel reads only
# the first line, so a multi-line file is already a latent fault.
ORIGINAL="$(tr -d '\n' < "$CMDLINE")"
NEW="$ORIGINAL"

# Parameters, added only if absent. console= is not touched (see header).
for p in "${CMDLINE_PARAMS[@]}"; do
    key="${p%%=*}"
    if grep -qE "(^| )${key}(=| |$)" <<<"$NEW"; then
        say "  $key already present — left as is"
    else
        NEW="$NEW $p"
        say "  + $p"
    fi
done

# Collapse any double spaces the substitution may have produced.
NEW="$(tr -s ' ' <<<"$NEW")"
NEW="${NEW#"${NEW%%[![:space:]]*}"}"   # trim leading
NEW="${NEW%"${NEW##*[![:space:]]}"}"   # trim trailing

# ---------------------------------------------------------------------------
# config.txt
# ---------------------------------------------------------------------------
CONFIG_ADDITIONS=()
for p in "${CONFIG_PARAMS[@]}"; do
    key="${p%%=*}"
    if grep -qE "^[[:space:]]*${key}=" "$CONFIG"; then
        say "  $key already present in config.txt — left as is"
    else
        CONFIG_ADDITIONS+=("$p")
        say "  + $p (config.txt)"
    fi
done

# ---------------------------------------------------------------------------
# getty
# ---------------------------------------------------------------------------
GETTY_STATE="$(systemctl is-enabled getty@tty1 2>/dev/null || true)"
MASK_GETTY=0
if [ "$GETTY_STATE" = "masked" ]; then
    say "  getty@tty1 already masked"
else
    MASK_GETTY=1
    say "  getty@tty1 will be masked (state: ${GETTY_STATE:-unknown})"
fi

# ---------------------------------------------------------------------------
# Report and apply
# ---------------------------------------------------------------------------
echo
say "cmdline.txt would become:"
echo "    $NEW"
echo

if [ "$DRY_RUN" -eq 1 ]; then
    say "Dry run — nothing written."
    exit 0
fi

if [ "$NEW" = "$ORIGINAL" ] && [ ${#CONFIG_ADDITIONS[@]} -eq 0 ] && [ "$MASK_GETTY" -eq 0 ]; then
    say "Already configured. Nothing to do."
    exit 0
fi

# Back up before touching anything.
if [ "$NEW" != "$ORIGINAL" ]; then
    cp "$CMDLINE" "$CMDLINE.bak-$STAMP"
    say "Backed up to $CMDLINE.bak-$STAMP"
    printf '%s\n' "$NEW" > "$CMDLINE"

    # Verify: exactly one line, and it still names a root device. A
    # cmdline.txt without root= will not boot, and this is the last chance
    # to notice before a reboot makes it expensive.
    LINES="$(wc -l < "$CMDLINE")"
    [ "$LINES" -eq 1 ] || { cp "$CMDLINE.bak-$STAMP" "$CMDLINE"; die "wrote $LINES lines, expected 1 — restored backup"; }
    grep -q 'root=' "$CMDLINE" || { cp "$CMDLINE.bak-$STAMP" "$CMDLINE"; die "result has no root= — restored backup"; }
    say "Wrote $CMDLINE (1 line, root= present)"
fi

if [ ${#CONFIG_ADDITIONS[@]} -gt 0 ]; then
    cp "$CONFIG" "$CONFIG.bak-$STAMP"
    say "Backed up to $CONFIG.bak-$STAMP"
    {
        echo ""
        echo "# Added by quiet-boot.sh on $STAMP"
        printf '%s\n' "${CONFIG_ADDITIONS[@]}"
    } >> "$CONFIG"
    say "Appended to $CONFIG"
fi

if [ "$MASK_GETTY" -eq 1 ]; then
    systemctl mask getty@tty1
    say "Masked getty@tty1 — local console login is now disabled (SSH unaffected)"
fi

echo
say "Done. Reboot to apply:  sudo reboot"
say "To undo:                sudo bash quiet-boot.sh --revert"
