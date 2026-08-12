#!/bin/bash
# pull_logs.sh — Pull GTach logs from the Pi via scp.
#
# Usage:
#   ./pull_logs.sh
#
# Deletes all existing files in logs/, then pulls every *.log and rotated
# log (*.log.N) from /opt/gtach on root@gtach.local and saves them to logs/
# in the local repository. Edit PI= below if the address changes.

set -e

PI="root@gtach.local"
REMOTE_DIR="/opt/gtach"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"

mkdir -p "$LOG_DIR"

echo "==> Removing old logs from $LOG_DIR ..."
rm -f "$LOG_DIR"/*

echo "==> Pulling logs from $PI:$REMOTE_DIR ..."
scp "$PI:$REMOTE_DIR/*.log" "$PI:$REMOTE_DIR/*.log.*" "$LOG_DIR/"

echo "==> Logs saved to $LOG_DIR"
