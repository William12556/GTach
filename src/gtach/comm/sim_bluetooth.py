#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Simulation Bluetooth Pairing for GTach

Provides scripted Bluetooth device discovery and pairing for hardware-free testing.
Duck-type compatible with BluetoothPairing from comm.pairing.
"""

import logging
import random
import threading
import time
from datetime import datetime
from typing import List, Optional, Callable

from ..display.setup_models import BluetoothDevice, PairingStatus, DeviceType


# Hardcoded fake devices for discovery
_FAKE_DEVICES = [
    BluetoothDevice(
        name='ELM327 OBD Adapter',
        mac_address='AA:BB:CC:DD:EE:01',
        signal_strength=-60,
        device_type='ELM327',
        last_seen=datetime.now()
    ),
    BluetoothDevice(
        name='OBDLink MX+',
        mac_address='AA:BB:CC:DD:EE:02',
        signal_strength=-55,
        device_type='ELM327',
        last_seen=datetime.now()
    ),
    BluetoothDevice(
        name='VEEPEAK OBD2',
        mac_address='AA:BB:CC:DD:EE:03',
        signal_strength=-70,
        device_type='ELM327',
        last_seen=datetime.now()
    ),
    BluetoothDevice(
        name='Generic BT Adapter',
        mac_address='AA:BB:CC:DD:EE:04',
        signal_strength=-65,
        device_type='Compatible',
        last_seen=datetime.now()
    )
]


class SimBluetoothPairing:
    """Simulation Bluetooth pairing for hardware-free testing.

    Duck-type compatible with BluetoothPairing. Returns scripted discovery
    results and simulates pairing with 80% success rate.
    """

    def __init__(self):
        """Initialize simulation Bluetooth pairing."""
        self.logger = logging.getLogger('SimBluetoothPairing')
        self._discovery_active = False
        self._pairing_active = False
        self._cancel_discovery = threading.Event()
        self._cancel_pairing = threading.Event()
        self.bluetooth_available = True

    def discover_elm327_devices(
        self,
        timeout: float = 10.0,
        progress_callback: Optional[Callable[[float], None]] = None,
        device_found_callback: Optional[Callable[[BluetoothDevice], None]] = None,
        show_all_devices: bool = False
    ) -> List[BluetoothDevice]:
        """Simulate Bluetooth device discovery.

        Fires progress_callback at 0%, 33%, 66%, 100% with ~0.75s between steps.
        Fires device_found_callback for each discovered device.

        Args:
            timeout: Unused (discovery is scripted).
            progress_callback: Optional callback(progress: float) for UI updates.
            device_found_callback: Optional callback(device: BluetoothDevice).
            show_all_devices: Unused (always returns all 4 fake devices).

        Returns:
            List[BluetoothDevice]: 4 fake devices.
        """
        try:
            self._discovery_active = True
            self.logger.info("SimBluetoothPairing: starting discovery")

            # Progress updates at 0%, 33%, 66%, 100%
            progress_steps = [0.0, 0.33, 0.66, 1.0]
            for progress in progress_steps:
                if self._cancel_discovery.is_set():
                    self.logger.info("SimBluetoothPairing: discovery cancelled")
                    break

                if progress_callback:
                    progress_callback(progress)

                time.sleep(0.75)

            # Fire device_found_callback for each device
            for device in _FAKE_DEVICES:
                if self._cancel_discovery.is_set():
                    break

                if device_found_callback:
                    device_found_callback(device)

            self._discovery_active = False
            self.logger.info(f"SimBluetoothPairing: discovery complete ({len(_FAKE_DEVICES)} devices)")
            return _FAKE_DEVICES.copy()

        except Exception as e:
            self.logger.error(f"SimBluetoothPairing discovery error: {e}", exc_info=True)
            self._discovery_active = False
            return []

    def discover_all_devices(
        self,
        timeout: float = 10.0,
        progress_callback: Optional[Callable[[float], None]] = None,
        device_found_callback: Optional[Callable[[BluetoothDevice], None]] = None
    ) -> List[BluetoothDevice]:
        """Simulate discovery of all Bluetooth devices.

        Delegates to discover_elm327_devices with show_all_devices=True.

        Args:
            timeout: Unused.
            progress_callback: Optional callback(progress: float).
            device_found_callback: Optional callback(device: BluetoothDevice).

        Returns:
            List[BluetoothDevice]: 4 fake devices.
        """
        return self.discover_elm327_devices(
            timeout=timeout,
            progress_callback=progress_callback,
            device_found_callback=device_found_callback,
            show_all_devices=True
        )

    def pair_device(
        self,
        device: BluetoothDevice,
        status_callback: Optional[Callable[[PairingStatus, str], None]] = None
    ) -> bool:
        """Simulate pairing with a Bluetooth device.

        Fires status_callback(CONNECTING), sleeps 1s, status_callback(TESTING),
        sleeps 1s, then succeeds with 80% probability.

        Args:
            device: Device to pair with (not used in simulation).
            status_callback: Optional callback(status: PairingStatus, message: str).

        Returns:
            bool: True if pairing succeeded (80% rate), False otherwise.
        """
        try:
            self._pairing_active = True
            self.logger.info(f"SimBluetoothPairing: starting pairing with {device.name}")

            # Step 1: Connecting
            if status_callback:
                status_callback(PairingStatus.CONNECTING, 'Connecting...')
            time.sleep(1.0)

            if self._cancel_pairing.is_set():
                self.logger.info("SimBluetoothPairing: pairing cancelled")
                self._pairing_active = False
                return False

            # Step 2: Testing
            if status_callback:
                status_callback(PairingStatus.TESTING, 'Testing...')
            time.sleep(1.0)

            if self._cancel_pairing.is_set():
                self.logger.info("SimBluetoothPairing: pairing cancelled")
                self._pairing_active = False
                return False

            # Succeed with 80% probability
            success = random.random() > 0.2

            if success:
                if status_callback:
                    status_callback(PairingStatus.SUCCESS, 'Connected')
                self.logger.info(f"SimBluetoothPairing: pairing succeeded with {device.name}")
            else:
                if status_callback:
                    status_callback(PairingStatus.FAILED, 'Simulated failure')
                self.logger.info(f"SimBluetoothPairing: pairing failed (simulated) with {device.name}")

            self._pairing_active = False
            return success

        except Exception as e:
            self.logger.error(f"SimBluetoothPairing pairing error: {e}", exc_info=True)
            self._pairing_active = False
            return False

    def cancel_discovery(self) -> None:
        """Cancel ongoing discovery operation."""
        self._cancel_discovery.set()
        self.logger.info("SimBluetoothPairing: discovery cancellation requested")

    def cancel_pairing(self) -> None:
        """Cancel ongoing pairing operation."""
        self._cancel_pairing.set()
        self.logger.info("SimBluetoothPairing: pairing cancellation requested")

    def shutdown(self) -> None:
        """Shutdown simulation Bluetooth pairing (no-op)."""
        self.logger.info("SimBluetoothPairing: shutdown")

    def is_discovery_active(self) -> bool:
        """Check if discovery is currently active.

        Returns:
            bool: True if discovery is in progress.
        """
        return self._discovery_active

    def is_pairing_active(self) -> bool:
        """Check if pairing is currently active.

        Returns:
            bool: True if pairing is in progress.
        """
        return self._pairing_active
