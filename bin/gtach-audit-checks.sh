#!/usr/bin/env bash
# gtach-audit-checks.sh — read-only on-device checks for audit-36b6ea95
# findings G01 (touch stack), E01 (effective configuration) and B04
# (runtime logging). Changes nothing: no installs, no restarts, no
# writes outside the report file in /tmp.
#
# Usage (on the Pi, as root):  bash /tmp/gtach-audit-checks.sh
#
# Copyright (c) 2026 William Watson. MIT License.

set -u

APP=/opt/gtach
VENV_PY="$APP/venv/bin/python"
VENV_PIP="$APP/venv/bin/pip"
REPORT="/tmp/gtach-audit-checks-$(date +%Y%m%d-%H%M%S).txt"

if [ "$(id -u)" -ne 0 ]; then
    echo "Run as root (the service runs as root and reads /root paths)." >&2
    exit 1
fi

exec > >(tee "$REPORT") 2>&1

hdr()  { printf '\n==== %s ====\n' "$1"; }
sub()  { printf '\n-- %s\n' "$1"; }

file_info() {
    # Path, existence, size, mtime and selected keys of a config file.
    local f="$1"
    if [ -f "$f" ]; then
        printf '%-50s EXISTS  %6s bytes  mtime %s\n' "$f" \
            "$(stat -c %s "$f")" "$(stat -c %y "$f" | cut -d. -f1)"
        grep -nE '^\s*(fps_limit|engine_profile|mode|display|bluetooth|obd|devices|primary)\b' "$f" \
            | sed 's/^/      /' | head -20
    else
        printf '%-50s absent\n' "$f"
    fi
}

hdr "Context"
echo "Host:        $(hostname)"
echo "Date:        $(date -Is)"
echo "Kernel:      $(uname -r)"
echo "Python:      $("$VENV_PY" --version 2>&1)"
echo "GTach:       $("$VENV_PIP" show gtach 2>/dev/null | awk '/^Version:/{print $2}')"
PID="$(systemctl show -p MainPID --value gtach 2>/dev/null)"
echo "Service:     $(systemctl is-active gtach 2>/dev/null)  MainPID=${PID:-0}"
echo "Started:     $(systemctl show -p ActiveEnterTimestamp --value gtach 2>/dev/null)"
echo "Environment: $(systemctl show -p Environment --value gtach 2>/dev/null)"
[ -n "${PID:-}" ] && [ "$PID" != "0" ] && echo "Process cwd: $(readlink /proc/$PID/cwd)"

# ---------------------------------------------------------------- G01
hdr "G01 — touch stack (hyperpixel2r, RPi.GPIO)"

sub "pip show (venv)"
for pkg in hyperpixel2r RPi.GPIO gpiozero; do
    if "$VENV_PIP" show "$pkg" >/dev/null 2>&1; then
        echo "$pkg: INSTALLED $("$VENV_PIP" show "$pkg" | awk '/^Version:/{print $2}')"
    else
        echo "$pkg: NOT INSTALLED"
    fi
done

sub "Module resolution in the venv (find_spec; nothing is imported)"
"$VENV_PY" - <<'EOF'
import importlib.util as u
for m in ("hyperpixel2r", "RPi.GPIO", "gpiozero"):
    try:
        s = u.find_spec(m)
        print(f"{m}: {'found at ' + str(s.origin) if s else 'NOT FOUND'}")
    except Exception as e:
        print(f"{m}: NOT FOUND ({type(e).__name__}: {e})")
EOF

sub "Touch implementation selected at last start (start.log)"
if [ -f "$APP/start.log" ]; then
    grep -nE 'mock HyperPixel|Mock HyperPixel|Falling back to mock|HyperPixel2R (library imported|import failed)' \
        "$APP/start.log" || echo "No touch-selection lines found in start.log."
else
    echo "$APP/start.log absent."
fi

# ---------------------------------------------------------------- E01
hdr "E01 — effective configuration files"
echo "ConfigManager resolves OBDII_HOME, else ~/.local/share/obdii (root: /root/...)."
echo "DisplayManager reads ./config.yaml relative to the working directory ($APP)."
echo "DeviceStore reads ./config/devices.yaml relative to the working directory."

sub "Candidate files"
for f in \
    /root/.local/share/obdii/config/config.yaml \
    /opt/obdii/config/config.yaml \
    /usr/local/share/obdii/config/config.yaml \
    "$APP/config.yaml" \
    "$APP/config/config.yaml" \
    "$APP/config/devices.yaml" \
    /root/.local/share/obdii/config/devices.yaml; do
    file_info "$f"
done

sub "Other config.yaml / devices.yaml files on the system (excluding the venv)"
find / -xdev \( -path /proc -o -path "$APP/venv" \) -prune -o \
    \( -name config.yaml -o -name devices.yaml \) -type f -print 2>/dev/null \
    | grep -vE '/(site-packages|dist-packages)/' | sort

sub "fps_limit in the file DisplayManager reads"
if [ -f "$APP/config.yaml" ]; then
    grep -nE '^\s*fps_limit' "$APP/config.yaml" || echo "fps_limit not set — DisplayManager default (60) applies."
else
    echo "$APP/config.yaml absent — DisplayManager defaults apply (fps_limit 60)."
fi

# ---------------------------------------------------------------- B04
hdr "B04 — runtime logging"

sub "Log files"
for f in "$APP/start.log" "$APP/debug.log" "$APP/stacks.log"; do
    if [ -f "$f" ]; then
        printf '%-28s %8s bytes  mtime %s\n' "$f" "$(stat -c %s "$f")" \
            "$(stat -c %y "$f" | cut -d. -f1)"
    else
        printf '%-28s absent\n' "$f"
    fi
done
ls -l "$APP"/debug.log.* 2>/dev/null | sed 's/^/  /'

sub "Last 5 lines of start.log (expect the startup-complete line last)"
tail -n 5 "$APP/start.log" 2>/dev/null

sub "Handler suppression in the installed package (static)"
PKG_DIR="$("$VENV_PY" -c 'import importlib.util as u; print(u.find_spec("gtach").submodule_search_locations[0])' 2>/dev/null)"
echo "Package: ${PKG_DIR:-not found}"
if [ -n "${PKG_DIR:-}" ]; then
    grep -nE 'CRITICAL \+ 1' "$PKG_DIR/main.py" "$PKG_DIR/app.py" 2>/dev/null
    grep -nE 'StreamHandler|SysLogHandler|JournalHandler' "$PKG_DIR/main.py" \
        || echo "No stream/syslog/journal handler in main.py."
fi

sub "Journal output from gtach since boot (process stderr)"
journalctl -u gtach -b --no-pager -o cat 2>/dev/null | grep -vE '^(Started|Stopped|Starting|Stopping) ' \
    | tail -n 15
echo "(lines above, if any, are process output; systemd start/stop lines filtered)"

hdr "Manual step for B04 (not performed by this script)"
cat <<'EOF'
With debug OFF and the service running:
  1. Note:  stat -c '%s %y' /opt/gtach/start.log /opt/gtach/debug.log
  2. Cause a runtime error, e.g. power off the ELM327 adapter (or stop the
     emulator) for about 30 s, then restore it.
  3. Repeat step 1 and run:  journalctl -u gtach --since "-5 min" --no-pager
  B04 is confirmed if neither file grew and the journal shows nothing.
EOF

hdr "Done"
echo "Report saved to $REPORT"
