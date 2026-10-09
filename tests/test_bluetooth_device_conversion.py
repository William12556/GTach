# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""BluetoothDevice.from_discovered: setup → comm conversion (issue-c9de5fb0)."""

import types
from datetime import datetime

from gtach.comm.models import BluetoothDevice
from gtach.display.setup_models import BluetoothDevice as SetupBluetoothDevice


def test_from_setup_device():
    setup_device = SetupBluetoothDevice(
        name="ELM327 X",
        mac_address="aa:bb:cc:dd:ee:ff",
        signal_strength=-60,
        device_type="ELM327",
        last_seen=datetime.now(),
    )

    device = BluetoothDevice.from_discovered(setup_device)

    assert device.name == "ELM327 X"
    assert device.mac_address == "AA:BB:CC:DD:EE:FF"
    assert device.device_type == "ELM327"
    assert device.last_connected is None


def test_from_any_object_with_the_three_attributes():
    discovered = types.SimpleNamespace(
        name="Adapter", mac_address="11:22:33:44:55:66", device_type="ELM327"
    )

    device = BluetoothDevice.from_discovered(discovered)

    assert device.mac_address == "11:22:33:44:55:66"
    assert device.device_type == "ELM327"


def test_unknown_type_is_classified_from_name():
    discovered = types.SimpleNamespace(
        name="Vgate OBD", mac_address="11:22:33:44:55:66", device_type="UNKNOWN"
    )

    assert BluetoothDevice.from_discovered(discovered).device_type == "OBD"
