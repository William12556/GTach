# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Communication components for OBDII display application."""

from .transport import OBDTransport, TransportState, TransportError, select_transport
from .rfcomm import RFCOMMTransport
from .tcp_transport import TCPTransport
from .serial_transport import SerialTransport
from .obd import OBDProtocol, OBDResponse
from .models import BluetoothDevice

__all__ = [
    'OBDTransport',
    'TransportState',
    'TransportError',
    'select_transport',
    'RFCOMMTransport',
    'TCPTransport',
    'SerialTransport',
    'OBDProtocol',
    'OBDResponse',
    'BluetoothDevice'
]
