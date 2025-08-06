#!/usr/bin/env python3
"""
Bluetooth interface for setup mode operations.
Handles device discovery coordination and setup mode Bluetooth operations.
"""

import logging
import threading
from typing import Optional, Dict, Any, Callable
from ...setup_models import PairingStatus, BluetoothDevice
from ....comm.pairing import BluetoothPairing
from ....comm.device_store import DeviceStore
from ...async_operations import get_async_manager, OperationType, OperationStatus


class BluetoothSetupInterface:
    """Manages Bluetooth operations for setup mode with thread-safe async coordination"""
    
    def __init__(self):
        self.logger = logging.getLogger('BluetoothSetupInterface')
        self.device_store = DeviceStore()
        self.async_manager = get_async_manager()
        
        # Bluetooth pairing state
        self.pairing = None
        self._active_operations: Dict[str, str] = {}
        self._pairing_ready = threading.Event()
        
        # Initialize Bluetooth pairing asynchronously
        self._init_bluetooth_pairing_async()
    
    def _init_bluetooth_pairing_async(self) -> None:
        """Initialize Bluetooth pairing asynchronously to prevent UI blocking"""
        def init_bluetooth_pairing(progress_callback=None):
            """Initialize BluetoothPairing in worker thread"""
            try:
                if progress_callback:
                    progress_callback(0.2, "Creating BluetoothPairing instance...")
                
                pairing = BluetoothPairing()
                
                if progress_callback:
                    progress_callback(0.8, "Testing Bluetooth adapter...")
                
                try:
                    adapter_available = hasattr(pairing, 'adapter') and pairing.adapter is not None
                    if progress_callback:
                        progress_callback(1.0, "Bluetooth initialization complete")
                except Exception as e:
                    self.logger.warning(f"Bluetooth adapter check failed: {e}")
                    if progress_callback:
                        progress_callback(1.0, "Bluetooth initialization complete (limited)")
                
                return pairing
                
            except Exception as e:
                self.logger.error(f"Bluetooth pairing initialization failed: {e}")
                if progress_callback:
                    progress_callback(1.0, f"Bluetooth initialization failed: {str(e)}")
                raise
        
        def on_bluetooth_init_complete(operation):
            """Callback when Bluetooth initialization completes"""
            try:
                if operation.status == OperationStatus.COMPLETED:
                    self.pairing = operation.result
                    self._pairing_ready.set()
                    self.logger.info("Bluetooth pairing initialized successfully in background")
                elif operation.status == OperationStatus.FAILED:
                    self.logger.error(f"Bluetooth pairing initialization failed: {operation.error}")
                    self.pairing = None
                    self._pairing_ready.set()
                else:
                    self.logger.warning(f"Bluetooth pairing initialization ended with status: {operation.status}")
                    self.pairing = None
                    self._pairing_ready.set()
                
                if 'bluetooth_init' in self._active_operations:
                    del self._active_operations['bluetooth_init']
                    
            except Exception as e:
                self.logger.error(f"Error in bluetooth init callback: {e}")
                self.pairing = None
                self._pairing_ready.set()
        
        try:
            operation_id = self.async_manager.submit_operation(
                OperationType.BLUETOOTH_INIT,
                init_bluetooth_pairing,
                progress_callback=on_bluetooth_init_complete
            )
            
            self._active_operations['bluetooth_init'] = operation_id
            self.logger.info(f"Bluetooth pairing initialization started (operation: {operation_id})")
            
        except Exception as e:
            self.logger.error(f"Failed to submit bluetooth initialization operation: {e}")
            try:
                self.pairing = BluetoothPairing()
                self._pairing_ready.set()
                self.logger.warning("Fallback to synchronous Bluetooth initialization")
            except Exception as fallback_error:
                self.logger.error(f"Synchronous Bluetooth initialization also failed: {fallback_error}")
                self.pairing = None
                self._pairing_ready.set()
    
    def ensure_pairing_initialized(self) -> bool:
        """Ensure Bluetooth pairing is initialized, waiting if necessary"""
        try:
            if not self._pairing_ready.wait(timeout=10.0):
                self.logger.error("Timeout waiting for Bluetooth pairing initialization")
                return False
            
            if self.pairing is None:
                self.logger.error("Bluetooth pairing initialization failed")
                return False
            
            self.logger.debug("Bluetooth pairing ready for use")
            return True
            
        except Exception as e:
            self.logger.error(f"Error ensuring pairing initialization: {e}")
            return False
    
    def start_discovery(self, state, progress_callback=None, device_found_callback=None, 
                       show_all_devices=False) -> None:
        """Start device discovery using async operation framework"""
        def discovery_task(progress_callback_inner=None):
            """Discover devices in worker thread"""
            try:
                if not self.ensure_pairing_initialized():
                    self.logger.error("Cannot start discovery - Bluetooth pairing not available")
                    state.pairing_status = PairingStatus.FAILED
                    raise RuntimeError("Bluetooth pairing not available")
                
                if progress_callback_inner:
                    progress_callback_inner(0.1, "Starting device discovery...")
                
                state.pairing_status = PairingStatus.DISCOVERING
                state.discovery_progress = 0.0
                state.discovered_devices = []
                
                def internal_progress_callback(progress):
                    """Internal progress callback to update state and external callback"""
                    state.discovery_progress = progress
                    if progress_callback:
                        progress_callback(progress)
                    if progress_callback_inner:
                        progress_callback_inner(progress, f"Discovering devices... {int(progress * 100)}%")
                
                def internal_device_found_callback(device):
                    """Internal device found callback"""
                    if device and device not in state.discovered_devices:
                        state.discovered_devices.append(device)
                        if device_found_callback:
                            device_found_callback(device)
                
                devices = self.pairing.discover_elm327_devices(
                    timeout=state.discovery_timeout,
                    progress_callback=internal_progress_callback,
                    device_found_callback=internal_device_found_callback,
                    show_all_devices=show_all_devices
                )
                
                return devices
                
            except Exception as e:
                self.logger.error(f"Device discovery failed: {e}", exc_info=True)
                state.pairing_status = PairingStatus.FAILED
                raise
        
        def on_discovery_complete(operation):
            """Callback when discovery operation completes"""
            try:
                if operation.status == OperationStatus.COMPLETED:
                    devices = operation.result
                    state.discovered_devices = devices
                    state.pairing_status = PairingStatus.IDLE
                    self.logger.info(f"Discovery completed with {len(devices)} devices")
                elif operation.status == OperationStatus.FAILED:
                    self.logger.error(f"Discovery failed: {operation.error}")
                    state.pairing_status = PairingStatus.FAILED
                else:
                    self.logger.warning(f"Discovery ended with status: {operation.status}")
                    state.pairing_status = PairingStatus.IDLE
                
                if 'device_discovery' in self._active_operations:
                    del self._active_operations['device_discovery']
                    
            except Exception as e:
                self.logger.error(f"Error in discovery callback: {e}")
                state.pairing_status = PairingStatus.FAILED
        
        try:
            if 'device_discovery' in self._active_operations:
                existing_op_id = self._active_operations['device_discovery']
                self.async_manager.cancel_operation(existing_op_id)
                del self._active_operations['device_discovery']
            
            operation_id = self.async_manager.submit_operation(
                OperationType.DEVICE_DISCOVERY,
                discovery_task,
                progress_callback=on_discovery_complete
            )
            
            self._active_operations['device_discovery'] = operation_id
            self.logger.info(f"Device discovery started (operation: {operation_id})")
            
        except Exception as e:
            self.logger.error(f"Failed to submit discovery operation: {e}")
            state.pairing_status = PairingStatus.FAILED
    
    def start_pairing(self, device: BluetoothDevice, state, progress_callback=None) -> None:
        """Start pairing with selected device using async operation framework"""
        def pairing_task(progress_callback_inner=None):
            """Pair with device in worker thread"""
            try:
                if not self.ensure_pairing_initialized():
                    self.logger.error("Cannot start pairing - Bluetooth pairing not available")
                    state.pairing_status = PairingStatus.FAILED
                    raise RuntimeError("Bluetooth pairing not available")
                
                if progress_callback_inner:
                    progress_callback_inner(0.1, f"Starting pairing with {device.name}...")
                
                def status_callback(status, message):
                    """Internal status callback to update state"""
                    state.pairing_status = status
                    if status == PairingStatus.FAILED:
                        state.error_message = message
                    
                    if status == PairingStatus.PAIRING:
                        if progress_callback:
                            progress_callback(0.5, f"Pairing with {device.name}...")
                        if progress_callback_inner:
                            progress_callback_inner(0.5, f"Pairing with {device.name}...")
                    elif status == PairingStatus.SUCCESS:
                        if progress_callback:
                            progress_callback(1.0, f"Successfully paired with {device.name}")
                        if progress_callback_inner:
                            progress_callback_inner(1.0, f"Successfully paired with {device.name}")
                    elif status == PairingStatus.FAILED:
                        if progress_callback:
                            progress_callback(1.0, f"Failed to pair with {device.name}: {message}")
                        if progress_callback_inner:
                            progress_callback_inner(1.0, f"Failed to pair with {device.name}: {message}")
                
                success = self.pairing.pair_device(device, status_callback)
                return success
                
            except Exception as e:
                self.logger.error(f"Device pairing failed: {e}", exc_info=True)
                state.pairing_status = PairingStatus.FAILED
                state.error_message = str(e)
                raise
        
        def on_pairing_complete(operation):
            """Callback when pairing operation completes"""
            try:
                if operation.status == OperationStatus.COMPLETED:
                    success = operation.result
                    if success:
                        state.pairing_status = PairingStatus.SUCCESS
                        self.logger.info(f"Successfully paired with device: {device.name}")
                    else:
                        state.pairing_status = PairingStatus.FAILED
                        self.logger.error(f"Failed to pair with device: {device.name}")
                elif operation.status == OperationStatus.FAILED:
                    state.pairing_status = PairingStatus.FAILED
                    state.error_message = str(operation.error) if operation.error else "Unknown pairing error"
                    self.logger.error(f"Pairing operation failed: {operation.error}")
                else:
                    self.logger.warning(f"Pairing ended with status: {operation.status}")
                    state.pairing_status = PairingStatus.FAILED
                
                if 'device_pairing' in self._active_operations:
                    del self._active_operations['device_pairing']
                    
            except Exception as e:
                self.logger.error(f"Error in pairing callback: {e}")
                state.pairing_status = PairingStatus.FAILED
        
        try:
            if 'device_pairing' in self._active_operations:
                existing_op_id = self._active_operations['device_pairing']
                self.async_manager.cancel_operation(existing_op_id)
                del self._active_operations['device_pairing']
            
            operation_id = self.async_manager.submit_operation(
                OperationType.DEVICE_PAIRING,
                pairing_task,
                progress_callback=on_pairing_complete
            )
            
            self._active_operations['device_pairing'] = operation_id
            self.logger.info(f"Device pairing started (operation: {operation_id})")
            
        except Exception as e:
            self.logger.error(f"Failed to submit pairing operation: {e}")
            state.pairing_status = PairingStatus.FAILED
    
    def cancel_operations(self) -> None:
        """Cancel all active Bluetooth operations"""
        try:
            for operation_id in list(self._active_operations.values()):
                self.async_manager.cancel_operation(operation_id)
            self._active_operations.clear()
        except Exception as e:
            self.logger.error(f"Error cancelling async operations: {e}")
        
        if self.pairing is not None:
            try:
                self.pairing.cancel_discovery()
                self.pairing.cancel_pairing()
            except Exception as e:
                self.logger.warning(f"Error cancelling pairing operations: {e}")
    
    def get_active_operation_progress(self) -> dict:
        """Get progress information for active async operations"""
        progress_info = {
            'has_active_operations': False,
            'progress': 0.0,
            'message': '',
            'operation_type': None
        }
        
        try:
            if not self._active_operations:
                return progress_info
            
            for operation_type, operation_id in self._active_operations.items():
                operation = self.async_manager.get_operation_status(operation_id)
                if operation:
                    progress_info['has_active_operations'] = True
                    progress_info['progress'] = operation.progress
                    progress_info['operation_type'] = operation_type
                    
                    if 'progress_message' in operation.metadata:
                        progress_info['message'] = operation.metadata['progress_message']
                    else:
                        if operation.status.name == 'PENDING':
                            progress_info['message'] = f"Starting {operation_type.replace('_', ' ').lower()}..."
                        elif operation.status.name == 'RUNNING':
                            progress_info['message'] = f"Running {operation_type.replace('_', ' ').lower()}..."
                        elif operation.status.name == 'COMPLETED':
                            progress_info['message'] = f"Completed {operation_type.replace('_', ' ').lower()}"
                        elif operation.status.name == 'FAILED':
                            progress_info['message'] = f"Failed {operation_type.replace('_', ' ').lower()}"
                        else:
                            progress_info['message'] = f"Processing {operation_type.replace('_', ' ').lower()}..."
                    
                    break
            
        except Exception as e:
            self.logger.debug(f"Error getting operation progress: {e}")
        
        return progress_info