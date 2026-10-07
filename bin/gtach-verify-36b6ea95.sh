#!/usr/bin/env bash
# gtach-verify-36b6ea95.sh — automated on-device checks for the
# audit-36b6ea95 remediation (ai/task.md, "On-Device Verification
# Outstanding"). Read-only by default: no installs, no edits to
# /opt/gtach, no service restarts. Writes only to /tmp (the report and
# one temporary config copy for the invalid-config test).
#
# Usage (on the Pi, as root):
#   bash /tmp/gtach-verify-36b6ea95.sh                 # log window = this boot
#   bash /tmp/gtach-verify-36b6ea95.sh --since all     # whole log files
#   bash /tmp/gtach-verify-36b6ea95.sh --since "2026-10-07 18:00:00"
#   bash /tmp/gtach-verify-36b6ea95.sh --stop-test     # also times a
#        service stop and starts it again (interrupts the display ~30 s)
#
# Transfer, run and copy back (from the repository root on the Mac):
#   scp bin/gtach-verify-36b6ea95.sh root@gtach.local:/tmp/
#   ssh root@gtach.local 'bash /tmp/gtach-verify-36b6ea95.sh'
#   scp 'root@gtach.local:/tmp/gtach-verify-*.txt' ai/workspace/test/
#
# Each check prints PASS, FAIL, INFO, SKIP or MANUAL. PASS/FAIL refer
# only to what can be observed from files and systemd; steps that need
# a person are covered by ai/workspace/test/
# test-36b6ea95-on-device-verification.md.
#
# Copyright (c) 2026 William Watson. MIT License.

set -u

APP=/opt/gtach
VENV="$APP/venv"
GTACH="$VENV/bin/gtach"
PIP="$VENV/bin/pip"
PY="$VENV/bin/python"
TS="$(date +%Y%m%d-%H%M%S)"
REPORT="/tmp/gtach-verify-$TS.txt"
SINCE="boot"
STOP_TEST=0

while [ $# -gt 0 ]; do
    case "$1" in
        --since) SINCE="${2:-boot}"; shift 2 ;;
        --stop-test) STOP_TEST=1; shift ;;
        -h|--help) sed -n 2,24p "$0"; exit 0 ;;
        *) echo "Unknown option: $1" >&2; exit 2 ;;
    esac
done

if [ "$(id -u)" -ne 0 ]; then
    echo "Run as root." >&2
    exit 1
fi

[ "$SINCE" = "boot" ] && SINCE="$(uptime -s)"
[ "$SINCE" = "all" ] && SINCE="0000-00-00 00:00:00"

exec > >(tee "$REPORT") 2>&1

RESULTS=()
hdr() { printf '\n==== %s ====\n' "$1"; }
sub() { printf '\n-- %s\n' "$1"; }
result() {
    # result <check-id> <issue> <STATUS> <text>
    printf '>> %-4s %-8s %-6s %s\n' "$1" "$2" "$3" "$4"
    RESULTS+=("$(printf '%-4s %-8s %-6s %s' "$1" "$2" "$3" "$4")")
}

# Rotated log set in chronological order: name.5 .. name.1, name.
logset() {
    local base="$1" f
    for f in $(ls -1 "$base".[0-9]* 2>/dev/null | sort -t. -k3 -rn); do
        echo "$f"
    done
    [ -f "$base" ] && echo "$base"
}

# Lines of the given files whose record timestamp is >= SINCE.
# Continuation lines (tracebacks) follow their record.
window() {
    [ $# -eq 0 ] && return 0
    awk -v s="$SINCE" '
        /^20[0-9][0-9]-[0-9][0-9]-[0-9][0-9] / { k = (($1 " " substr($2, 1, 8)) >= s) }
        k' "$@"
}

ERR_FILES=$(logset "$APP/error.log")
DBG_FILES=$(logset "$APP/debug.log")
# shellcheck disable=SC2086
ERR_WIN="$(window $ERR_FILES)"
# shellcheck disable=SC2086
DBG_WIN="$(window $DBG_FILES)"
ALL_WIN="$(printf '%s\n%s\n' "$ERR_WIN" "$DBG_WIN")"

count() { printf '%s\n' "$ALL_WIN" | grep -cE "$1"; }
show()  { printf '%s\n' "$ALL_WIN" | grep -E "$1" | sort -u | tail -n "${2:-5}" | sed 's/^/      /'; }

# ------------------------------------------------------------ Context
hdr "Context"
echo "Host:          $(hostname)"
echo "Date:          $(date -Is)"
echo "Booted:        $(uptime -s)  (up $(uptime -p))"
echo "Log window:    records at or after '$SINCE'"
echo "Kernel:        $(uname -r)"
echo "Python:        $("$PY" --version 2>&1)"
echo "GTach:         $("$PIP" show gtach 2>/dev/null | awk '/^Version:/{print $2}')"
echo "Service:       $(systemctl is-active gtach)  since $(systemctl show -p ActiveEnterTimestamp --value gtach)"
echo "NRestarts:     $(systemctl show -p NRestarts --value gtach)"
echo "error.log set: $(echo $ERR_FILES)"
echo "debug.log set: $(echo $DBG_FILES)"
command -v vcgencmd >/dev/null && echo "Throttled:     $(vcgencmd get_throttled)  Temp: $(vcgencmd measure_temp)"

if [ "$(systemctl is-active gtach)" = "active" ]; then
    result C0 general PASS "gtach.service active"
else
    result C0 general FAIL "gtach.service not active"
fi

# ------------------------------------------------- C1 b9ee7428 (B13)
hdr "C1 b9ee7428 — no watchdog restart after boot clock step"
sub "Clock synchronisation this boot (monotonic seconds since boot)"
journalctl -b -o short-monotonic --no-pager 2>/dev/null \
    | grep -E "systemd-timesyncd|Time has been changed|Synchroni[sz]ed|Clock change" | head -5
sub "gtach.service journal this boot (state changes)"
J=$(journalctl -u gtach -b --no-pager 2>/dev/null)
printf '%s\n' "$J" | grep -E "Started|Stopped|Succeeded|Scheduled restart|Main process exited|Failed with result|Deactivated" | tail -10
BAD=$(printf '%s\n' "$J" | grep -cE "Succeeded|Scheduled restart|Main process exited|Failed with result|Deactivated successfully")
NR=$(systemctl show -p NRestarts --value gtach)
if [ "$BAD" -eq 0 ] && [ "${NR:-0}" -eq 0 ]; then
    result C1 b9ee7428 PASS "no exit or restart of gtach this boot (NRestarts=0)"
else
    result C1 b9ee7428 FAIL "$BAD exit/restart lines this boot; NRestarts=$NR"
fi
echo "   Note: meaningful only after a cold boot (power off > 1 min) with Wi-Fi; see guide session C (4.3)."

# ------------------------------------------------- C2 269871a0 (B04)
hdr "C2 269871a0 — error.log always on and preserved"
if [ -n "$ERR_FILES" ]; then
    for f in $ERR_FILES; do
        printf '   %-28s %8s bytes  first %s  last %s\n' "$f" "$(stat -c %s "$f")" \
            "$(grep -m1 -oE '^20[0-9-]+ [0-9:]+' "$f")" \
            "$(grep -oE '^20[0-9-]+ [0-9:]+' "$f" | tail -1)"
    done
    TB=$(printf '%s\n' "$ERR_WIN" | grep -c "^Traceback")
    echo "   Records in window: $(printf '%s\n' "$ERR_WIN" | grep -cE '^20[0-9][0-9]-') ; tracebacks: $TB"
    printf '%s\n' "$ERR_WIN" | grep -E " (WARNING|ERROR|CRITICAL) " | tail -8 | sed 's/^/      /'
    OLDEST=$(grep -m1 -hoE '^20[0-9-]+ [0-9:]+' $(echo "$ERR_FILES" | head -1))
    if [ -n "$OLDEST" ] && [[ "$OLDEST" < "$(uptime -s)" ]]; then
        result C2 269871a0 PASS "error.log present; records older than this boot survive ($OLDEST)"
    else
        result C2 269871a0 INFO "error.log present; no records older than this boot yet"
    fi
else
    result C2 269871a0 FAIL "no $APP/error.log"
fi
result C2b 269871a0 MANUAL "adapter-off event with traceback: guide session D (4.4), then rerun"

# ---------------------------------------- C3 watchdog (Phase 1 issues)
hdr "C3 e9216e17 / fbe7e98a / 860fd5f7 — watchdog and shutdown events"
W_TOTAL=0
for p in "appears unresponsive" "no in-process restart" "exited unexpectedly" \
         "Initiating graceful shutdown" "forcing process termination"; do
    n=$(count "$p"); W_TOTAL=$((W_TOTAL + n))
    printf '   %-32s %s\n' "$p" "$n"
done
show "appears unresponsive|no in-process restart|exited unexpectedly|Initiating graceful shutdown|forcing process termination" 10
OBD_STALL=$(count "Thread obd_protocol.*unresponsive")
if [ "$OBD_STALL" -eq 0 ]; then
    result C3a 860fd5f7 PASS "no obd_protocol unresponsive record in window"
else
    result C3a 860fd5f7 FAIL "$OBD_STALL obd_protocol unresponsive records in window"
fi
if [ "$W_TOTAL" -eq 0 ]; then
    result C3b phase-1 PASS "no watchdog stall, thread exit or shutdown records in window"
else
    result C3b phase-1 FAIL "$W_TOTAL watchdog/shutdown records in window (inspect above; a SIGTERM stop also logs shutdown)"
fi

# ------------------------------------------------- C4 907de6de (Phase 2)
hdr "C4 907de6de — OBD initialisation and link events"
for p in "Initialization failed" "No valid 0100" "adapter closed the connection" \
         "consecutive timeouts" "dropped - will attempt to reconnect" "Connected to "; do
    printf '   %-40s %s\n' "$p" "$(count "$p")"
done
show "Initialization failed|No valid 0100|adapter closed the connection|consecutive timeouts|dropped - will|Connected to " 10
if [ -z "$DBG_FILES" ]; then
    echo "   debug.log absent: INFO-level link records are only in debug.log; enable Debug for guide session F (4.6)."
fi
result C4 907de6de MANUAL "evidence above; pass judged against guide session F (4.6)"

# ------------------------------------------------- C5 5fbff586 (Phase 3)
hdr "C5 5fbff586 — configuration"
CFG="$APP/config.yaml"
if [ -f "$CFG" ]; then
    echo "   $CFG  $(stat -c '%s bytes  mtime %y' "$CFG" | cut -d. -f1)"
    sed 's/^/      /' "$CFG" | grep -vE '^\s*#|^\s*$' | head -20
else
    echo "   $CFG absent (defaults apply)"
fi
sub "gtach --validate-config"
OUT=$(timeout 60 "$GTACH" --validate-config 2>&1); RC=$?
echo "$OUT" | tail -5 | sed 's/^/      /'
if [ $RC -eq 0 ] && echo "$OUT" | grep -q "Config valid"; then
    result C5a 5fbff586 PASS "--validate-config: valid (exit 0)"
else
    result C5a 5fbff586 FAIL "--validate-config exit $RC"
fi
sub "gtach --validate-config on a temporary copy with fps_limit: 0"
TMPCFG="/tmp/gtach-verify-config-$TS.yaml"
if [ -f "$CFG" ]; then grep -v '^\s*fps_limit\s*:' "$CFG" > "$TMPCFG"; else : > "$TMPCFG"; fi
echo "fps_limit: 0" >> "$TMPCFG"
OUT=$(timeout 60 "$GTACH" --validate-config --config "$TMPCFG" 2>&1); RC=$?
echo "$OUT" | tail -5 | sed 's/^/      /'
rm -f "$TMPCFG"
if [ $RC -eq 1 ] && echo "$OUT" | grep -q "Config invalid"; then
    result C5b 5fbff586 PASS "invalid fps_limit rejected (exit 1); real config untouched"
else
    result C5b 5fbff586 FAIL "invalid fps_limit not rejected (exit $RC)"
fi
INV=$(count "Invalid value for")
[ "$INV" -gt 0 ] && show "Invalid value for" 5
if [ "$INV" -eq 0 ]; then
    result C5c 5fbff586 PASS "no 'Invalid value for' records at load"
else
    result C5c 5fbff586 FAIL "$INV 'Invalid value for' records at load"
fi

sub "Acknowledgement state"
ACK="$APP/config/ack_state.yaml"
LEGACY=/root/.local/share/obdii
if [ -f "$ACK" ]; then
    echo "   $ACK  $(stat -c 'mtime %y' "$ACK" | cut -d. -f1)"
    result C5d 5fbff586 PASS "ack_state.yaml at new location"
else
    result C5d 5fbff586 INFO "no $ACK yet (expected until the screen is acknowledged once)"
fi
[ -e "$LEGACY" ] && echo "   Legacy $LEGACY still present (no longer read; may be removed later)."

# ------------------------------------------------- C6 453f0a80 (Phase 3)
hdr "C6 453f0a80 — paired device store"
DEV="$APP/config/devices.yaml"
if [ -f "$DEV" ]; then
    echo "   $DEV  $(stat -c '%s bytes  mtime %y' "$DEV" | cut -d. -f1)"
    grep -nE '^\s*-?\s*(mac_address|name|is_primary|primary|device_type)\s*:' "$DEV" | head -12 | sed 's/^/      /'
    if grep -qE '([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}' "$DEV"; then
        result C6 453f0a80 PASS "devices.yaml present with at least one MAC address"
    else
        result C6 453f0a80 FAIL "devices.yaml present but holds no MAC address"
    fi
else
    result C6 453f0a80 FAIL "no $DEV"
fi
result C6b 453f0a80 MANUAL "adapter used without re-pairing: guide session A (4.1)"

# ------------------------------------------------- C7 52653cd6 (Phase 5)
hdr "C7 52653cd6 — packaging"
PK_OK=1
for pkg in hyperpixel2r RPi.GPIO; do
    v=$("$PIP" show "$pkg" 2>/dev/null | awk '/^Version:/{print $2}')
    if [ -n "$v" ]; then echo "   $pkg $v"; else echo "   $pkg NOT INSTALLED"; PK_OK=0; fi
done
if [ $PK_OK -eq 1 ]; then
    result C7a 52653cd6 PASS "[pi] extra installed (hyperpixel2r, RPi.GPIO)"
else
    result C7a 52653cd6 FAIL "[pi] extra incomplete"
fi
OUT=$("$PIP" check 2>&1); RC=$?
echo "$OUT" | head -5 | sed 's/^/      /'
if [ $RC -eq 0 ]; then
    result C7b 52653cd6 PASS "pip check clean"
else
    result C7b 52653cd6 FAIL "pip check reports broken requirements"
fi

sub "Mock fallback (start.log is this start only)"
MOCK_RE="Failed to start real HyperPixel|Falling back to mock|Using mock HyperPixel"
MS=$(grep -cE "$MOCK_RE" "$APP/start.log" 2>/dev/null)
ME=$(count "$MOCK_RE")
grep -E "$MOCK_RE" "$APP/start.log" 2>/dev/null | tail -3 | sed 's/^/      /'
if [ "${MS:-0}" -eq 0 ] && [ "$ME" -eq 0 ]; then
    result C7c 52653cd6 PASS "no HyperPixel mock fallback"
else
    result C7c 52653cd6 FAIL "mock fallback recorded (start.log $MS, window $ME)"
fi

hdr "C8 52653cd6 — service unit hardening"
declare -A EXP=(
    [TimeoutStopUSec]="30s" [NoNewPrivileges]="yes" [PrivateTmp]="yes"
    [ProtectHome]="yes" [ProtectSystem]="full" [StartLimitIntervalUSec]="2min"
    [StartLimitBurst]="5" [Restart]="always"
)
U_OK=1
for k in TimeoutStopUSec NoNewPrivileges PrivateTmp ProtectHome ProtectSystem \
         StartLimitIntervalUSec StartLimitBurst Restart; do
    v=$(systemctl show -p "$k" --value gtach)
    m="ok"; [ "$v" = "${EXP[$k]}" ] || { m="EXPECTED ${EXP[$k]}"; U_OK=0; }
    printf '   %-24s %-8s %s\n' "$k" "$v" "$m"
done
W=$(systemctl show -p Wants --value gtach)
echo "   Wants                    $W"
echo "$W" | grep -q bluetooth.service || U_OK=0
if [ $U_OK -eq 1 ]; then
    result C8a 52653cd6 PASS "unit directives as expected"
else
    result C8a 52653cd6 FAIL "unit directives differ (unit not reinstalled or daemon-reload missing?)"
fi
sub "systemd-analyze security gtach (summary)"
systemd-analyze security gtach --no-pager 2>/dev/null | grep -E "NoNewPrivileges|PrivateTmp|ProtectHome|ProtectSystem|Overall exposure" | sed 's/^/   /'
result C8b 52653cd6 INFO "exposure level recorded above"

# ------------------------------------------------- C9 674bec49 (Phase 2)
hdr "C9 674bec49 — SetupManager threads in stacks.log"
STK_FILES=$(ls -1 "$APP"/stacks.log* 2>/dev/null)
if [ -n "$STK_FILES" ]; then
    # shellcheck disable=SC2086
    "$PY" - $STK_FILES <<'PYEOF'
import re, sys
# A faulthandler dump is a run of "Thread 0x..." blocks. A new dump
# starts at a run header or when a thread id repeats. Count, per dump,
# the threads whose stack contains SetupManager._setup_loop.
worst = dumps = 0
for path in sys.argv[1:]:
    seen, setup, cur = set(), set(), None
    def close():
        global worst, dumps
        if seen:
            dumps += 1
            worst = max(worst, len(setup))
    for line in open(path, errors="replace"):
        m = re.match(r"(?:Current thread|Thread) (0x[0-9a-f]+)", line)
        if line.startswith("=== gtach") or (m and m.group(1) in seen):
            close()
            seen, setup, cur = set(), set(), None
        if m:
            cur = m.group(1)
            seen.add(cur)
        elif cur and "_setup_loop" in line:
            setup.add(cur)
    close()
print(f"   dumps parsed: {dumps}; max SetupManager threads in one dump: {worst}")
sys.exit(0 if worst <= 1 else 3)
PYEOF
    RC=$?
    if [ $RC -eq 0 ]; then
        result C9 674bec49 PASS "at most one SetupManager thread per stack dump"
    else
        result C9 674bec49 FAIL "more than one SetupManager thread in a stack dump"
    fi
    echo "   Run headers:"; grep -h "^=== gtach" $STK_FILES | tail -5 | sed 's/^/      /'
else
    result C9 674bec49 SKIP "no stacks.log (Debug not enabled); see guide session E (4.5)"
fi

# ------------------------------------- C10 stop timing (opt-in, intrusive)
hdr "C10 52653cd6 / d140121d — service stop time"
if [ $STOP_TEST -eq 1 ]; then
    T0=$(date +%s.%N)
    systemctl stop gtach
    T1=$(date +%s.%N)
    DT=$(awk -v a="$T0" -v b="$T1" 'BEGIN{printf "%.1f", b-a}')
    echo "   systemctl stop gtach took ${DT} s"
    journalctl -u gtach --since "@${T0%.*}" --no-pager | tail -5 | sed 's/^/      /'
    if awk -v d="$DT" 'BEGIN{exit !(d < 25)}'; then
        result C10 52653cd6 PASS "stop in ${DT} s (< 25 s, under TimeoutStopSec=30)"
    else
        result C10 52653cd6 FAIL "stop took ${DT} s"
    fi
    systemctl start gtach
    sleep 20
    if [ "$(systemctl is-active gtach)" = "active" ]; then
        result C10b general PASS "service active 20 s after restart"
    else
        result C10b general FAIL "service not active after restart"
    fi
else
    result C10 52653cd6 SKIP "rerun with --stop-test (interrupts the display)"
fi

# ------------------------------------------------------------ Summary
hdr "Summary"
printf '%s\n' "${RESULTS[@]}"
P=$(printf '%s\n' "${RESULTS[@]}" | grep -c " PASS ")
F=$(printf '%s\n' "${RESULTS[@]}" | grep -c " FAIL ")
echo
echo "PASS $P  FAIL $F  (report: $REPORT)"
