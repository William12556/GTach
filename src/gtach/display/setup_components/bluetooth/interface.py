#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Bluetooth interface for setup mode operations.
Handles device discovery coordination and setup mode Bluetooth operations.
"""

import logging
import threading
import time
import uuid
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, cast

from ....comm.device_store import get_device_store
from ....comm.models import BluetoothDevice as CommBluetoothDevice
from ....comm.pairing import BluetoothPairing
from ....comm.transport import LINK_BUSY_CAUSE
from ....utils.waits import wait_for_event
from ...async_operations import (
    AsyncOperation,
    OperationStatus,
    OperationType,
    get_async_manager,
)
from ...setup_models import (
    BluetoothDevice,
    DeviceType,
    PairingStatus,
    SetupScreen,
    SetupState,
)

if TYPE_CHECKING:
    from ..state.coordinator import SetupStateCoordinator

# Operation names under which running operations are registered.
BLUETOOTH_INIT = "bluetooth_init"
DEVICE_DISCOVERY = "device_discovery"
DEVICE_PAIRING = "device_pairing"
DEVICE_PROBE = "device_probe"

# DEVICE_LIST error-line texts (design-a3b4c5d6 section 4.0).
SCAN_FAILED_TEXT = "Scan failed"
FALLBACK_LIST_TEXT = "No ELM327 found - showing all devices"
DEVICE_NOT_SAVED_TEXT = "Device not saved"
OBD_CHECK_FAILED_TEXT = "OBD check failed"


class BluetoothSetupInterface:
    """Manages Bluetooth operations for setup mode.

    Each operation is registered under its name with an id the interface
    issues before submitting it. Its completion and the callbacks its task
    makes act only while that id is still the registered one; cancelling
    removes the registration (design-a3b4c5d6 section 6.0).
    """

    # The RFCOMM connect issued milliseconds after pairing can fail with
    # EBUSY while the link is still held. Retry that cause only, up to
    # this many attempts in total, this far apart (issue-d26ca557).
    _VERIFY_BUSY_ATTEMPTS: int = 3
    _VERIFY_BUSY_RETRY_DELAY_S: float = 1.0

    # Lets the RFCOMM stack release the adapter after a previous pairing
    # attempt before the scan starts.
    _DISCOVERY_SETTLE_S: float = 2.0

    def __init__(
        self,
        pairing_factory: Optional[Callable[[], Any]] = None,
        state_coordinator: Optional["SetupStateCoordinator"] = None,
    ) -> None:
        self.logger = logging.getLogger("BluetoothSetupInterface")
        self.device_store = get_device_store()
        self.async_manager = get_async_manager()
        self._pairing_factory = pairing_factory
        self._state_coordinator = state_coordinator

        # Bluetooth pairing state: a BluetoothPairing, or the duck-typed
        # stand-in pairing_factory builds (SimBluetoothPairing).
        self.pairing: Optional[BluetoothPairing] = None
        # Guarded by _ops_lock: name -> registration id, name -> async id,
        # and whether verify_obd_connection reset the adapter.
        self._active_operations: Dict[str, str] = {}
        self._submitted_ids: Dict[str, str] = {}
        self._adapter_reset = False
        self._ops_lock = threading.Lock()
        self._pairing_ready = threading.Event()

        # Initialize Bluetooth pairing asynchronously
        self._init_bluetooth_pairing_async()

    def _init_bluetooth_pairing_async(self) -> None:
        """Initialize Bluetooth pairing asynchronously to prevent UI blocking"""

        def init_bluetooth_pairing(
            progress_callback: Optional[Callable[[float, str], None]] = None,
        ) -> Any:
            """Initialize BluetoothPairing in worker thread"""
            try:
                if progress_callback:
                    progress_callback(0.2, "Creating BluetoothPairing instance...")

                pairing = (
                    self._pairing_factory if self._pairing_factory else BluetoothPairing
                )()

                if progress_callback:
                    progress_callback(0.8, "Testing Bluetooth adapter...")

                try:
                    if progress_callback:
                        progress_callback(1.0, "Bluetooth initialization complete")
                except Exception as e:
                    self.logger.warning(f"Bluetooth adapter check failed: {e}")
                    if progress_callback:
                        progress_callback(
                            1.0, "Bluetooth initialization complete (limited)"
                        )

                return pairing

            except Exception as e:
                self.logger.error(
                    f"Bluetooth pairing initialization failed: {e}", exc_info=True
                )
                if progress_callback:
                    progress_callback(1.0, f"Bluetooth initialization failed: {str(e)}")
                raise

        def on_bluetooth_init_complete(operation: AsyncOperation) -> None:
            """Callback when Bluetooth initialization completes"""
            try:
                # Progress updates arrive here too; act only on a
                # terminal status.
                if operation.status in (
                    OperationStatus.PENDING,
                    OperationStatus.RUNNING,
                ):
                    return
                if operation.status == OperationStatus.COMPLETED:
                    self.pairing = operation.result
                    self._pairing_ready.set()
                    self.logger.info(
                        "Bluetooth pairing initialized successfully in background"
                    )
                elif operation.status == OperationStatus.FAILED:
                    self.logger.error(
                        f"Bluetooth pairing initialization failed: {operation.error}"
                    )
                    self.pairing = None
                    self._pairing_ready.set()
                else:
                    self.logger.warning(
                        "Bluetooth pairing initialization ended with status: "
                        f"{operation.status}"
                    )
                    self.pairing = None
                    self._pairing_ready.set()

                self._release(BLUETOOTH_INIT, token)

            except Exception as e:
                self.logger.error(
                    f"Error in bluetooth init callback: {e}", exc_info=True
                )
                self.pairing = None
                self._pairing_ready.set()

        token = self._register(BLUETOOTH_INIT)
        if not self._submit(
            BLUETOOTH_INIT,
            token,
            OperationType.BLUETOOTH_INIT,
            init_bluetooth_pairing,
            on_bluetooth_init_complete,
        ):
            try:
                self.pairing = (
                    self._pairing_factory if self._pairing_factory else BluetoothPairing
                )()
                self._pairing_ready.set()
                self.logger.warning("Fallback to synchronous Bluetooth initialization")
            except Exception as fallback_error:
                self.logger.error(
                    "Synchronous Bluetooth initialization also failed: "
                    f"{fallback_error}",
                    exc_info=True,
                )
                self.pairing = None
                self._pairing_ready.set()

    def ensure_pairing_initialized(self) -> bool:
        """Ensure Bluetooth pairing is initialized, waiting if necessary"""
        try:
            if not wait_for_event(self._pairing_ready, 10.0):
                self.logger.error(
                    "Timeout waiting for Bluetooth pairing initialization"
                )
                return False

            if self.pairing is None:
                self.logger.error("Bluetooth pairing initialization failed")
                return False

            self.logger.debug("Bluetooth pairing ready for use")
            return True

        except Exception as e:
            self.logger.error(
                f"Error ensuring pairing initialization: {e}", exc_info=True
            )
            return False

    @property
    def adapter_reset(self) -> bool:
        """Whether verify_obd_connection sent ATZ and received a reply."""
        with self._ops_lock:
            return self._adapter_reset

    def verify_obd_connection(self, state: SetupState) -> bool:
        """Verify OBD connection using ATZ probe over RFCOMM

        A reply to ATZ sets adapter_reset. The simulation pass-through
        sends nothing and leaves it unchanged.

        Args:
            state: SetupState instance

        Returns:
            bool: True if OBD verification succeeds, False otherwise
        """
        import socket as _socket

        from ....comm.rfcomm import RFCOMMTransport

        # Skip RFCOMM probe in simulation mode (pairing_factory injected)
        # or when AF_BLUETOOTH is unavailable
        if self._pairing_factory is not None or not hasattr(_socket, "AF_BLUETOOTH"):
            self.logger.info(
                "OBD verify: simulation mode or no AF_BLUETOOTH — pass-through"
            )
            return True
        try:
            device = self.device_store.get_primary_device()
            if device is None:
                self.logger.error("OBD verify: no primary device in store")
                return False

            transport = RFCOMMTransport(device.mac_address, channel=1)
            for attempt in range(1, self._VERIFY_BUSY_ATTEMPTS + 1):
                if transport.connect():
                    break
                if (
                    transport.last_failure_cause != LINK_BUSY_CAUSE
                    or attempt == self._VERIFY_BUSY_ATTEMPTS
                ):
                    self.logger.warning("OBD verify: RFCOMM connect failed")
                    return False
                self.logger.info(
                    "OBD verify: link busy, retrying "
                    f"(attempt {attempt + 1}/{self._VERIFY_BUSY_ATTEMPTS})"
                )
                time.sleep(self._VERIFY_BUSY_RETRY_DELAY_S)

            try:
                response = transport.send_command("ATZ", timeout=5.0)
                ok = response is not None and len(response.strip()) > 0
                self.logger.info(
                    f"OBD verify: {'pass' if ok else 'fail'} response={response!r}"
                )
                if ok:
                    with self._ops_lock:
                        self._adapter_reset = True
                return ok
            finally:
                transport.disconnect()
        except Exception as e:
            self.logger.error(f"OBD verify exception: {e}", exc_info=True)
            return False

    def start_discovery(
        self,
        state: SetupState,
        device_found_callback: Optional[Callable[[BluetoothDevice], None]] = None,
        show_all_devices: bool = False,
    ) -> None:
        """Start one scan; its completion moves setup to DEVICE_LIST.

        A scan registered earlier is cancelled first.

        Args:
            state: Setup state; writes go through the coordinator.
            device_found_callback: Called with each newly found device.
            show_all_devices: Passed to the back end's discovery.
        """
        token = self._register(DEVICE_DISCOVERY)

        def current() -> bool:
            return self._is_current(DEVICE_DISCOVERY, token)

        def discovery_task(
            progress_callback: Optional[Callable[[float, str], None]] = None,
        ) -> List[BluetoothDevice]:
            """Discover devices in worker thread"""
            try:
                if not self.ensure_pairing_initialized():
                    raise RuntimeError("Bluetooth pairing not available")

                if progress_callback:
                    progress_callback(0.1, "Starting device discovery...")

                time.sleep(self._DISCOVERY_SETTLE_S)
                if not current():
                    return []

                self._set_state(
                    state,
                    pairing_status=PairingStatus.DISCOVERING,
                    discovery_progress=0.0,
                    discovered_devices=[],
                )

                def on_progress(progress: float) -> None:
                    if not current():
                        return
                    self._set_state(state, discovery_progress=progress)
                    if progress_callback:
                        progress_callback(
                            progress, f"Discovering devices... {int(progress * 100)}%"
                        )

                def on_device_found(device: BluetoothDevice) -> None:
                    if not device or not current():
                        return
                    if self._add_device(state, device) and device_found_callback:
                        device_found_callback(device)

                # ensure_pairing_initialized() above checked for None.
                return cast(BluetoothPairing, self.pairing).discover_elm327_devices(
                    timeout=state.discovery_timeout,
                    progress_callback=on_progress,
                    device_found_callback=on_device_found,
                    show_all_devices=show_all_devices,
                )

            except Exception as e:
                self.logger.error(f"Device discovery failed: {e}", exc_info=True)
                raise

        def on_discovery_complete(operation: AsyncOperation) -> None:
            """Present the scan outcome on DEVICE_LIST."""
            # Progress updates arrive here too; act only on a terminal status.
            if operation.status in (OperationStatus.PENDING, OperationStatus.RUNNING):
                return
            if not current():
                self.logger.debug(f"Ignoring completion of discovery {token}")
                return
            try:
                self._present_scan_result(state, operation)
            except Exception as e:
                self.logger.error(f"Error in discovery callback: {e}", exc_info=True)
            finally:
                self._release(DEVICE_DISCOVERY, token)

        if not self._submit(
            DEVICE_DISCOVERY,
            token,
            OperationType.DEVICE_DISCOVERY,
            discovery_task,
            on_discovery_complete,
        ):
            self._present_scan_result(
                state,
                AsyncOperation(
                    id=token,
                    operation_type=OperationType.DEVICE_DISCOVERY,
                    status=OperationStatus.FAILED,
                ),
            )

    def _present_scan_result(
        self, state: SetupState, operation: AsyncOperation
    ) -> None:
        """Write a finished scan's devices and error line; show DEVICE_LIST.

        Args:
            state: Setup state; writes go through the coordinator.
            operation: The finished discovery operation.
        """
        devices: List[BluetoothDevice] = []
        error: Optional[str] = None
        if operation.status == OperationStatus.COMPLETED:
            devices = list(operation.result or [])
            # The back end's fallback list holds only UNKNOWN devices.
            if devices and all(
                d.device_classification is DeviceType.UNKNOWN for d in devices
            ):
                error = FALLBACK_LIST_TEXT
            self.logger.info(f"Discovery completed with {len(devices)} devices")
        else:
            self.logger.error(f"Discovery failed: {operation.error}")
            error = SCAN_FAILED_TEXT

        self._set_state(
            state,
            discovered_devices=devices,
            error_message=error,
            pairing_status=PairingStatus.IDLE,
        )
        if self._state_coordinator is not None:
            self._state_coordinator.transition_to_screen(SetupScreen.DEVICE_LIST)

    def start_pairing(self, device: BluetoothDevice, state: SetupState) -> None:
        """Pair with the selected device, then save and verify it.

        A pairing registered earlier is cancelled first.

        Args:
            device: The device to pair with.
            state: Setup state; writes go through the coordinator.
        """
        token = self._register(DEVICE_PAIRING)

        def current() -> bool:
            return self._is_current(DEVICE_PAIRING, token)

        def pairing_task(
            progress_callback: Optional[Callable[[float, str], None]] = None,
        ) -> bool:
            """Pair with device in worker thread"""
            try:
                if not self.ensure_pairing_initialized():
                    raise RuntimeError("Bluetooth pairing not available")

                if progress_callback:
                    progress_callback(0.1, f"Starting pairing with {device.name}...")

                def status_callback(status: PairingStatus, message: str) -> None:
                    """Write pairing status updates and report progress."""
                    if not current():
                        return
                    self._set_state(state, pairing_status=status)
                    if status == PairingStatus.FAILED:
                        self._set_state(state, error_message=message)

                    if progress_callback is None:
                        return
                    if status == PairingStatus.CONNECTING:
                        progress_callback(0.5, f"Pairing with {device.name}...")
                    elif status == PairingStatus.SUCCESS:
                        progress_callback(
                            1.0, f"Successfully paired with {device.name}"
                        )
                    elif status == PairingStatus.FAILED:
                        progress_callback(
                            1.0, f"Failed to pair with {device.name}: {message}"
                        )

                # ensure_pairing_initialized() above checked for None.
                return cast(BluetoothPairing, self.pairing).pair_device(
                    device, status_callback
                )

            except Exception as e:
                self.logger.error(f"Device pairing failed: {e}", exc_info=True)
                raise

        def on_pairing_complete(operation: AsyncOperation) -> None:
            """Save and verify a paired device, or show the failure."""
            # Progress updates arrive here too; act only on a terminal status.
            if operation.status in (OperationStatus.PENDING, OperationStatus.RUNNING):
                return
            if not current():
                self.logger.debug(f"Ignoring completion of pairing {token}")
                return
            try:
                if operation.status == OperationStatus.COMPLETED and operation.result:
                    self._finish_pairing(device, state, current)
                elif operation.status == OperationStatus.COMPLETED:
                    self._set_state(state, pairing_status=PairingStatus.FAILED)
                    self.logger.error(f"Failed to pair with device: {device.name}")
                else:
                    self._set_state(
                        state,
                        pairing_status=PairingStatus.FAILED,
                        error_message=(
                            str(operation.error)
                            if operation.error
                            else "Unknown pairing error"
                        ),
                    )
                    self.logger.error(f"Pairing operation failed: {operation.error}")
            except Exception as e:
                self.logger.error(f"Error in pairing callback: {e}", exc_info=True)
                if current():
                    self._set_state(state, pairing_status=PairingStatus.FAILED)
            finally:
                self._release(DEVICE_PAIRING, token)

        if not self._submit(
            DEVICE_PAIRING,
            token,
            OperationType.DEVICE_PAIRING,
            pairing_task,
            on_pairing_complete,
        ):
            self._set_state(
                state,
                pairing_status=PairingStatus.FAILED,
                error_message="Unknown pairing error",
            )

    def _finish_pairing(
        self,
        device: BluetoothDevice,
        state: SetupState,
        current: Callable[[], bool],
    ) -> None:
        """Save the paired device, verify it and complete setup.

        Args:
            device: The paired device.
            state: Setup state; writes go through the coordinator.
            current: Whether the pairing operation is still registered;
                checked again after the blocking save and verification.
        """
        self._set_state(state, pairing_status=PairingStatus.SUCCESS)
        self.logger.info(f"Successfully paired with device: {device.name}")

        # DeviceStore takes the comm model, which has last_connected.
        saved = self.device_store.save_device(
            CommBluetoothDevice.from_discovered(device), is_primary=True
        )
        if not current():
            return
        if not saved:
            self.logger.error(f"Paired device not saved: {device.name}")
            self._set_state(
                state,
                pairing_status=PairingStatus.FAILED,
                error_message=DEVICE_NOT_SAVED_TEXT,
            )
            return

        verified = self.verify_obd_connection(state)
        if not current():
            return
        if self._state_coordinator is None:
            self.logger.warning("OBD verify finished but state_coordinator is None")
            return
        if verified:
            self._state_coordinator.complete_setup()
            return
        self._set_state(state, error_message=OBD_CHECK_FAILED_TEXT)
        self._state_coordinator.transition_to_screen(SetupScreen.DEVICE_LIST)

    def start_device_probe(self, on_result: Callable[[bool], None]) -> None:
        """Check asynchronously that the stored device is reachable.

        Runs the RFCOMM connect on an async worker so the caller (the
        touch thread) never blocks on it (issue-fbe7e98a). In simulation
        mode, or where AF_BLUETOOTH is unavailable, the probe passes.

        Args:
            on_result: Called once, on a worker thread, with True if the
                device answered and False otherwise; not called if the
                probe is cancelled first.
        """
        token = self._register(DEVICE_PROBE)

        def probe_task() -> bool:
            """Connect to the primary device and disconnect again."""
            import socket as _socket

            from ....comm.rfcomm import RFCOMMTransport

            if self._pairing_factory is not None or not hasattr(
                _socket, "AF_BLUETOOTH"
            ):
                return True
            device = self.device_store.get_primary_device()
            if device is None:
                return False
            transport = RFCOMMTransport(device.mac_address, channel=1)
            ok = transport.connect()
            if ok:
                transport.disconnect()
            return ok

        def deliver(ok: bool) -> None:
            try:
                on_result(ok)
            except Exception as e:
                self.logger.error(
                    f"Device probe result handler failed: {e}", exc_info=True
                )

        def on_probe_complete(operation: AsyncOperation) -> None:
            """Report the probe outcome on a terminal status only."""
            if operation.status in (OperationStatus.PENDING, OperationStatus.RUNNING):
                return
            if not self._is_current(DEVICE_PROBE, token):
                self.logger.debug(f"Ignoring completion of probe {token}")
                return
            try:
                deliver(
                    operation.status == OperationStatus.COMPLETED
                    and bool(operation.result)
                )
            finally:
                self._release(DEVICE_PROBE, token)

        if not self._submit(
            DEVICE_PROBE,
            token,
            OperationType.OBD_CONNECTION_TEST,
            probe_task,
            on_probe_complete,
        ):
            deliver(False)

    def _register(self, name: str) -> str:
        """Cancel any operation registered under name and register a new id.

        The id is registered before the operation is submitted, so a
        completion that arrives before submit_operation returns is current.

        Args:
            name: Operation name, e.g. DEVICE_DISCOVERY.

        Returns:
            The new registration id.
        """
        self.cancel_operation(name)
        operation_id = f"{name}-{uuid.uuid4().hex[:8]}"
        with self._ops_lock:
            self._active_operations[name] = operation_id
        return operation_id

    def _submit(
        self,
        name: str,
        operation_id: str,
        operation_type: OperationType,
        task: Callable[..., Any],
        on_complete: Callable[[AsyncOperation], None],
    ) -> bool:
        """Submit a registered operation and record its async id.

        Args:
            name: Operation name.
            operation_id: The registration id from _register.
            operation_type: Async operation type.
            task: The task to run on a worker.
            on_complete: Called with progress updates and the outcome.

        Returns:
            True if submitted; False, with the registration removed, if not.
        """
        try:
            async_id = self.async_manager.submit_operation(
                operation_type, task, progress_callback=on_complete
            )
        except Exception as e:
            self.logger.error(f"Failed to submit {name}: {e}", exc_info=True)
            self._release(name, operation_id)
            return False

        with self._ops_lock:
            if self._active_operations.get(name) == operation_id:
                self._submitted_ids[name] = async_id
        self.logger.info(f"{name} started (operation: {async_id})")
        return True

    def _is_current(self, name: str, operation_id: str) -> bool:
        """Whether operation_id is the registered operation for name.

        Args:
            name: Operation name.
            operation_id: Registration id held by the caller.

        Returns:
            True if the operation is still wanted.
        """
        with self._ops_lock:
            return self._active_operations.get(name) == operation_id

    def _release(self, name: str, operation_id: str) -> bool:
        """Remove the registration for name if operation_id holds it.

        Args:
            name: Operation name.
            operation_id: Registration id held by the caller.

        Returns:
            True if the registration was removed.
        """
        with self._ops_lock:
            if self._active_operations.get(name) != operation_id:
                return False
            del self._active_operations[name]
            self._submitted_ids.pop(name, None)
            return True

    def _set_state(self, state: SetupState, **fields: Any) -> None:
        """Write setup state fields through the coordinator.

        The handlers receive a copy from get_state(), so writes must go
        to the coordinator (issue-d140121d). Without one, the fields are
        set on the passed object.
        """
        if self._state_coordinator is not None:
            self._state_coordinator.update_state(**fields)
            return
        for key, value in fields.items():
            setattr(state, key, value)

    def _add_device(self, state: SetupState, device: BluetoothDevice) -> bool:
        """Record a discovered device; True if it was new."""
        if self._state_coordinator is not None:
            return self._state_coordinator.add_discovered_device(device)
        if device in state.discovered_devices:
            return False
        state.discovered_devices.append(device)
        return True

    def has_active_operation(self, name: str) -> bool:
        """Whether an operation of the given name is in progress.

        Args:
            name: Operation name, e.g. 'device_discovery'.

        Returns:
            True if it is registered as active.
        """
        with self._ops_lock:
            return name in self._active_operations

    def shutdown(self) -> None:
        """Cancel operations and shut the pairing executor down."""
        self.cancel_operations()
        pairing = self.pairing
        if pairing is not None and hasattr(pairing, "shutdown"):
            try:
                pairing.shutdown()
            except Exception as e:
                self.logger.error(f"Pairing shutdown failed: {e}", exc_info=True)

    def cancel_operation(self, name: str) -> None:
        """Cancel the operation registered under name.

        The registration is removed first, so the operation's completion
        and its task's callbacks change nothing; then the async manager and
        the back end are asked to stop it. Does nothing if no operation is
        registered under name.

        Args:
            name: Operation name, e.g. DEVICE_DISCOVERY.
        """
        with self._ops_lock:
            registered = self._active_operations.pop(name, None)
            async_id = self._submitted_ids.pop(name, None)
        if registered is None:
            return
        self.logger.info(f"Cancelling {name}")

        try:
            if async_id is not None:
                self.async_manager.cancel_operation(async_id)
        except Exception as e:
            self.logger.error(f"Error cancelling {name}: {e}", exc_info=True)

        pairing = self.pairing
        if pairing is None:
            return
        try:
            if name == DEVICE_DISCOVERY:
                pairing.cancel_discovery()
            elif name == DEVICE_PAIRING:
                pairing.cancel_pairing()
        except Exception as e:
            self.logger.warning(f"Error cancelling {name} in the back end: {e}")

    def cancel_operations(self) -> None:
        """Cancel every registered operation through cancel_operation."""
        with self._ops_lock:
            names = list(self._active_operations)
        for name in names:
            self.cancel_operation(name)

    def get_active_operation_progress(self) -> dict:
        """Get progress information for active async operations"""
        progress_info = {
            "has_active_operations": False,
            "progress": 0.0,
            "message": "",
            "operation_type": None,
        }

        try:
            # Copy under the lock; query async_manager after release.
            with self._ops_lock:
                active = dict(self._submitted_ids)
            if not active:
                return progress_info

            for operation_type, operation_id in active.items():
                operation = self.async_manager.get_operation_status(operation_id)
                if operation:
                    progress_info["has_active_operations"] = True
                    progress_info["progress"] = operation.progress
                    progress_info["operation_type"] = operation_type

                    if "progress_message" in operation.metadata:
                        progress_info["message"] = operation.metadata[
                            "progress_message"
                        ]
                    else:
                        if operation.status.name == "PENDING":
                            progress_info["message"] = (
                                "Starting "
                                f"{operation_type.replace('_', ' ').lower()}..."
                            )
                        elif operation.status.name == "RUNNING":
                            progress_info["message"] = (
                                f"Running {operation_type.replace('_', ' ').lower()}..."
                            )
                        elif operation.status.name == "COMPLETED":
                            progress_info["message"] = (
                                f"Completed {operation_type.replace('_', ' ').lower()}"
                            )
                        elif operation.status.name == "FAILED":
                            progress_info["message"] = (
                                f"Failed {operation_type.replace('_', ' ').lower()}"
                            )
                        else:
                            progress_info["message"] = (
                                "Processing "
                                f"{operation_type.replace('_', ' ').lower()}..."
                            )

                    break

        except Exception as e:
            self.logger.debug(f"Error getting operation progress: {e}")

        return progress_info
