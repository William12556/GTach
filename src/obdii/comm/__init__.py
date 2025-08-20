# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Communication components for OBDII display application."""

from .bluetooth import BluetoothManager, BluetoothState
from .obd import OBDProtocol, OBDResponse
from .models import BluetoothDevice  # Add this line

__all__ = [
    'BluetoothManager',
    'BluetoothState',
    'OBDProtocol',
    'OBDResponse',
    'BluetoothDevice'  # Add this line
]