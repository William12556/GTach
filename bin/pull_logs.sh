#!/bin/bash
# pull_logs.sh — Pull GTach logs from the Pi via scp.
#
# Usage:
#   ./pull_logs.sh
#
# Pulls every *.log and rotated log (*.log.N) from /opt/gtach on
# root@gtach.local into a temporary directory; only if that succeeds
# are the contents of logs/ in the local repository replaced. Edit PI=
# below if the address changes.

set -e

PI="root@gtach.local"
REMOTE_DIR="/opt/gtach"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"

mkdir -p "$LOG_DIR"

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

echo "==> Pulling logs from $PI:$REMOTE_DIR ..."
# One remote glob: matches live and rotated logs, and succeeds when
# there are no rotated logs (issue-52653cd6).
scp "$PI:$REMOTE_DIR/*.log*" "$tmp/"

echo "==> Replacing old logs in $LOG_DIR ..."
rm -f "$LOG_DIR"/*
mv "$tmp"/* "$LOG_DIR/"

echo "==> Logs saved to $LOG_DIR"
