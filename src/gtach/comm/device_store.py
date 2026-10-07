#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Persistent device storage for OBDII display application.
Manages paired device configuration and setup state.
"""

import logging
import os
import threading
from datetime import datetime
from typing import List, Optional

# Conditional import of yaml with fallback
try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    yaml = None
    YAML_AVAILABLE = False

from ..utils.home import gtach_home
from .models import BluetoothDevice


class DeviceStore:
    """Manages persistent storage of paired Bluetooth devices.

    Thread-safe: every public method holds self._lock for its read or
    read-modify-save. The private helpers named *_locked assume the
    caller holds it; public methods never call each other while holding
    it, because threading.Lock is not reentrant (issue-453f0a80). Use
    get_device_store() for the shared instance.
    """

    def __init__(self, config_path: Optional[str] = None):
        """Create a store.

        Args:
            config_path: The devices file. Defaults to
                gtach_home()/config/devices.yaml.
        """
        self.logger = logging.getLogger("DeviceStore")
        if config_path is None:
            config_path = str(gtach_home() / "config" / "devices.yaml")
        self.config_path = config_path
        self._lock = threading.Lock()

        # Check yaml availability and warn if not available
        if not YAML_AVAILABLE:
            self.logger.warning(
                "YAML library not available - device storage will use in-memory "
                "fallback"
            )
            self.config = {"paired_devices": {}}
        else:
            self._ensure_config_dir()
            self._load_config()

    def _ensure_config_dir(self) -> None:
        """Ensure config directory exists"""
        config_dir = os.path.dirname(self.config_path)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)

    def _load_config(self) -> None:
        """Load device configuration from file"""
        if not YAML_AVAILABLE:
            self.logger.debug("YAML not available - using default config")
            self.config = {"paired_devices": {}}
            return

        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as f:
                    self.config = yaml.safe_load(f) or {}
            else:
                self.config = {"paired_devices": {}}
                self._save_config()
        except Exception as e:
            self.logger.error(f"Failed to load device config: {e}", exc_info=True)
            self.config = {"paired_devices": {}}

        # Runs on every exit path, including the error path above.
        self._normalise_config()

    def _normalise_config(self) -> None:
        """Enforce the structure the writers assume.

        yaml.safe_load returns whatever the file contains. An
        empty file, a partially written file or a hand edit can
        produce a mapping with no 'paired_devices' key, a null
        value under that key, or a top level that is not a
        mapping at all. save_device previously indexed into
        self.config['paired_devices'] directly and raised
        KeyError, which its own handler swallowed — so pairing
        reported success and persisted nothing (core review
        §3.4, recommendation #4).

        The contract is enforced once here rather than at each
        assignment site.
        """
        if not isinstance(self.config, dict):
            self.logger.warning(
                f"devices.yaml top level is {type(self.config).__name__}, "
                f"expected mapping — using an empty store"
            )
            self.config = {}

        paired = self.config.get("paired_devices")
        if not isinstance(paired, dict):
            if paired is not None:
                self.logger.warning(
                    f"paired_devices is {type(paired).__name__}, "
                    f"expected mapping — replacing"
                )
            self.config["paired_devices"] = {}

        secondary = self.config["paired_devices"].get("secondary")
        if secondary is not None and not isinstance(secondary, dict):
            self.logger.warning(
                f"paired_devices.secondary is {type(secondary).__name__}, "
                f"expected mapping — replacing"
            )
            self.config["paired_devices"]["secondary"] = {}

    def _save_config(self) -> bool:
        """Save device configuration to file.

        Returns:
            True when the store was written to disk, False otherwise —
            including when YAML is unavailable, since nothing is
            persisted in that state.
        """
        if not YAML_AVAILABLE:
            self.logger.debug("YAML not available - config will not be persisted")
            return False

        try:
            tmp_path = self.config_path + ".tmp"
            with open(tmp_path, "w") as f:
                yaml.dump(self.config, f, default_flow_style=False)
                # Durable before the rename (issue-453f0a80).
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, self.config_path)
            return True
        except Exception as e:
            self.logger.error(f"Failed to save device config: {e}", exc_info=True)
            return False

    def save_device(self, device: BluetoothDevice, is_primary: bool = True) -> bool:
        """Save a paired device to storage.

        Args:
            device: The device to persist.
            is_primary: Store as the primary device rather than under
                the secondary mapping.

        Returns:
            True when the device reached disk, False otherwise.
        """
        with self._lock:
            return self._save_device_locked(device, is_primary)

    def get_primary_device(self) -> Optional[BluetoothDevice]:
        """Get the primary paired device, or None."""
        with self._lock:
            return self._get_primary_device_locked()

    def get_all_devices(self) -> List[BluetoothDevice]:
        """Get all paired devices, primary first."""
        with self._lock:
            return self._get_all_devices_locked()

    def remove_device(self, mac_address: str) -> bool:
        """Remove a device from storage; True if one was removed."""
        with self._lock:
            return self._remove_device_locked(mac_address)

    def get_device_by_mac(self, mac_address: str) -> Optional[BluetoothDevice]:
        """Get a specific device by MAC address, or None."""
        with self._lock:
            return self._get_device_by_mac_locked(mac_address)

    def _save_device_locked(
        self, device: BluetoothDevice, is_primary: bool = True
    ) -> bool:
        """Save a paired device to storage. Caller holds self._lock.

        Args:
            device: The device to persist.
            is_primary: Store as the primary device rather than under
                the secondary mapping.

        Returns:
            True when the device reached disk, False when it did not —
            because the write failed, or because YAML is unavailable and
            the store is in-memory only. Callers that report pairing
            success to the operator should consult it.
        """
        try:
            device_data = {
                "name": device.name,
                "mac_address": device.mac_address,
                "device_type": device.device_type,
            }

            # Include last_connected if it exists
            if device.last_connected:
                device_data["last_connected"] = device.last_connected.isoformat()

            # setdefault rather than direct indexing: a devices.yaml
            # that exists but carries no paired_devices key raised
            # KeyError here, on BOTH branches, and the except below
            # swallowed it (core review §3.4, recommendation #4).
            paired = self.config.setdefault("paired_devices", {})

            if is_primary:
                paired["primary"] = device_data
            else:
                paired.setdefault("secondary", {})[device.mac_address] = device_data

            saved = self._save_config()
            if saved:
                self.logger.info(
                    f"Saved {'primary' if is_primary else 'secondary'} device: "
                    f"{device.name}"
                )
            else:
                self.logger.error(f"Device {device.name} was not persisted")
            return saved

        except Exception as e:
            self.logger.error(
                f"Failed to save device {device.name}: {e}", exc_info=True
            )
            return False

    def _get_primary_device_locked(self) -> Optional[BluetoothDevice]:
        """Get the primary paired device. Caller holds self._lock."""
        try:
            primary_data = self.config.get("paired_devices", {}).get("primary")
            if primary_data:
                last_connected = None
                if primary_data.get("last_connected"):
                    last_connected = datetime.fromisoformat(
                        primary_data["last_connected"]
                    )

                return BluetoothDevice(
                    name=primary_data["name"],
                    mac_address=primary_data["mac_address"],
                    device_type=primary_data.get("device_type", "UNKNOWN"),
                    last_connected=last_connected,
                )
            return None
        except Exception as e:
            self.logger.error(f"Failed to get primary device: {e}", exc_info=True)
            return None

    def _get_all_devices_locked(self) -> List[BluetoothDevice]:
        """Get all paired devices. Caller holds self._lock."""
        devices = []

        # Add primary device
        primary = self._get_primary_device_locked()
        if primary:
            devices.append(primary)

        # Add secondary devices
        try:
            secondary_devices = self.config.get("paired_devices", {}).get(
                "secondary", {}
            )
            for mac_address, device_data in secondary_devices.items():
                last_connected = None
                if device_data.get("last_connected"):
                    last_connected = datetime.fromisoformat(
                        device_data["last_connected"]
                    )
                device = BluetoothDevice(
                    name=device_data["name"],
                    mac_address=device_data["mac_address"],
                    device_type=device_data.get("device_type", "UNKNOWN"),
                    last_connected=last_connected,
                )
                devices.append(device)
        except Exception as e:
            self.logger.error(f"Failed to get secondary devices: {e}", exc_info=True)

        return devices

    def _remove_device_locked(self, mac_address: str) -> bool:
        """Remove a device from storage. Caller holds self._lock."""
        try:
            # Check if it's the primary device
            primary = self.config.get("paired_devices", {}).get("primary")
            if primary and primary.get("mac_address") == mac_address:
                del self.config["paired_devices"]["primary"]
                self._save_config()
                self.logger.info(f"Removed primary device: {mac_address}")
                return True

            # Check secondary devices
            secondary_devices = self.config.get("paired_devices", {}).get(
                "secondary", {}
            )
            if mac_address in secondary_devices:
                del secondary_devices[mac_address]
                self._save_config()
                self.logger.info(f"Removed secondary device: {mac_address}")
                return True

            return False
        except Exception as e:
            self.logger.error(
                f"Failed to remove device {mac_address}: {e}", exc_info=True
            )
            return False

    def _get_device_by_mac_locked(self, mac_address: str) -> Optional[BluetoothDevice]:
        """Get a specific device by MAC address. Caller holds self._lock."""
        for device in self._get_all_devices_locked():
            if device.mac_address == mac_address:
                return device
        return None


# The shared instance (issue-453f0a80). Independent instances each held
# their own copy of the file, so one could overwrite another's changes.
_shared: Optional[DeviceStore] = None
_shared_lock = threading.Lock()


def get_device_store() -> DeviceStore:
    """Return the process-wide DeviceStore, creating it on first use.

    Constructs through the module-level name DeviceStore, so a test that
    patches the class gets its replacement.

    Returns:
        The shared store.
    """
    global _shared
    with _shared_lock:
        if _shared is None:
            _shared = DeviceStore()
        return _shared


def reset_device_store() -> None:
    """Discard the shared instance; the next get_device_store() makes a new one.

    For tests.
    """
    global _shared
    with _shared_lock:
        _shared = None
