#!/bin/bash
# pull_logs.sh — Pull GTach logs from the Pi via scp.
#
# Usage:
#   ./pull_logs.sh
#
# Pulls /opt/gtach/start.log and /opt/gtach/debug.log from root@gtach.local
# and saves them to logs/ in the local repository. Edit PI= below if the
# address changes.

set -e

PI="root@gtach.local"
REMOTE_DIR="/opt/gtach"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"

mkdir -p "$LOG_DIR"

echo "==> Pulling logs from $PI:$REMOTE_DIR ..."
scp "$PI:$REMOTE_DIR/start.log" "$LOG_DIR/start.log"
scp "$PI:$REMOTE_DIR/debug.log" "$LOG_DIR/debug.log"

echo "==> Logs saved to $LOG_DIR"
