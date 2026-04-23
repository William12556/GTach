#!/bin/bash

# =============================================================================
# Usage
# =============================================================================
#
# Starts GTach on macOS in development/testing mode using TCP transport.
# Connects to the ELM327 emulator running on the Raspberry Pi.
#
# Prerequisites:
#   - ELM327 emulator must be running on the Pi before starting GTach.
#     On the Pi: sudo bash /opt/elm327/start-elm327-emulator-tcp.sh
#   - macOS development environment must be configured.
#   - Python virtual environment must be activated if applicable.
#
# Pi hostname is hardcoded below as ELM327-Emulator.local.
# Change ELM_HOST if the Pi hostname or IP address differs.
#
# Usage:
#   bash start-gtach-macos-tcp.sh
#
# =============================================================================

ELM_HOST="ELM327-Emulator.local"
ELM_PORT=35000
CONFIG="workspace/config/config-macos-dev.yaml"

echo "Starting GTach (macOS, TCP transport) -> ${ELM_HOST}:${ELM_PORT}"

python -m gtach \
    --macos \
    --transport tcp \
    --obd-host "${ELM_HOST}" \
    --config "${CONFIG}" \
    --debug \
    2>&1 | tee gtach.log
