#!/usr/bin/env python3
"""
Bluetooth connection management for OBDII display application.
Uses Bleak library for cross-platform Bluetooth LE and classic Bluetooth support.
Handles device discovery and connection management with async/await patterns.
"""

import asyncio
import logging
import threading
import time
from enum import Enum, auto
from typing import Optional, Tuple, List, Dict, Any, Callable
import uuid
import concurrent.futures
from contextlib import contextmanager

# Import Bleak for cross-platform Bluetooth support
try:
    from bleak import BleakClient, BleakScanner
    from bleak.backends.device import BLEDevice
    from bleak.exc import BleakError
    BLUETOOTH_BACKEND = 'bleak'
    BLUETOOTH_AVAILABLE = True
except ImportError:
    BleakClient = None
    BleakScanner = None
    BLEDevice = None
    BleakError = Exception
    BLUETOOTH_BACKEND = 'none'
    BLUETOOTH_AVAILABLE = False

from ..core import ThreadManager
from .device_store import DeviceStore


class BluetoothState(Enum):
    """Bluetooth connection states"""
    DISCONNECTED = auto()
    SCANNING = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    ERROR = auto()


class BluetoothConnectionError(Exception):
    """Exception raised for Bluetooth connection issues"""
    pass


class BluetoothManager:
    """
    Manages Bluetooth device discovery and connection using Bleak library.
    
    This class provides cross-platform Bluetooth support with async/await patterns
    while maintaining thread safety and backward compatibility with the existing
    OBD2 interface.
    """
    
    def __init__(self, thread_manager: ThreadManager, device_store: DeviceStore = None):
        """
        Initialize Bluetooth manager with thread management and device storage.
        
        Args:
            thread_manager: ThreadManager instance for thread lifecycle management
            device_store: DeviceStore instance for device persistence (optional)
        """
        self.logger = logging.getLogger('BluetoothManager')
        self.thread_manager = thread_manager
        self.device_store = device_store or DeviceStore()
        
        # Thread-safe state management with proper synchronization
        self._state_lock = threading.RLock()  # Reentrant lock for nested operations
        self._state = BluetoothState.DISCONNECTED
        self._current_device: Optional[Tuple[str, str]] = None
        self._client: Optional[BleakClient] = None
        
        # Connection retry settings - thread-safe access
        self._retry_count = 0
        self._max_retries = 3
        self._retry_delay = 3
        
        # Threading synchronization with proper coordination
        self._connection_event = threading.Event()
        self._shutdown_event = threading.Event()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        
        # Thread-safe command queue for communication coordination
        self._command_queue = asyncio.Queue()
        self._response_cache: Dict[str, Any] = {}
        self._cache_lock = threading.Lock()
        
        # OBD2 communication settings - thread-safe access
        self._obd_service_uuid = "00001101-0000-1000-8000-00805f9b34fb"  # Serial Port Profile
        self._notification_characteristic: Optional[str] = None
        self._write_characteristic: Optional[str] = None
        
        # Check if Bleak is available
        if not BLUETOOTH_AVAILABLE:
            self.logger.error("Bleak library not available. Install with: pip install bleak")
            with self._state_lock:
                self._state = BluetoothState.ERROR
            return
        
        self.logger.info(f"Using Bluetooth backend: {BLUETOOTH_BACKEND}")
    
    @contextmanager
    def _state_access(self, write_mode: bool = False):
        """Context manager for thread-safe state access"""
        if write_mode:
            with self._state_lock:
                yield
        else:
            with self._state_lock:
                yield
    
    @property
    def state(self) -> BluetoothState:
        """Thread-safe state access"""
        with self._state_lock:
            return self._state
    
    @state.setter
    def state(self, value: BluetoothState) -> None:
        """Thread-safe state update"""
        with self._state_lock:
            self._state = value
    
    @property
    def current_device(self) -> Optional[Tuple[str, str]]:
        """Thread-safe current device access"""
        with self._state_lock:
            return self._current_device
    
    @current_device.setter
    def current_device(self, value: Optional[Tuple[str, str]]) -> None:
        """Thread-safe current device update"""
        with self._state_lock:
            self._current_device = value
    
    @property
    def client(self) -> Optional[BleakClient]:
        """Thread-safe client access"""
        with self._state_lock:
            return self._client
    
    @client.setter
    def client(self, value: Optional[BleakClient]) -> None:
        """Thread-safe client update"""
        with self._state_lock:
            self._client = value
    
    @property
    def retry_count(self) -> int:
        """Thread-safe retry count access"""
        with self._state_lock:
            return self._retry_count
    
    @retry_count.setter
    def retry_count(self, value: int) -> None:
        """Thread-safe retry count update"""
        with self._state_lock:
            self._retry_count = value
    
    @property
    def connection_event(self) -> threading.Event:
        """Thread-safe connection event access"""
        return self._connection_event
    
    @property
    def notification_characteristic(self) -> Optional[str]:
        """Thread-safe notification characteristic access"""
        with self._state_lock:
            return self._notification_characteristic
    
    @notification_characteristic.setter
    def notification_characteristic(self, value: Optional[str]) -> None:
        """Thread-safe notification characteristic update"""
        with self._state_lock:
            self._notification_characteristic = value
    
    @property
    def write_characteristic(self) -> Optional[str]:
        """Thread-safe write characteristic access"""
        with self._state_lock:
            return self._write_characteristic
    
    @write_characteristic.setter
    def write_characteristic(self, value: Optional[str]) -> None:
        """Thread-safe write characteristic update"""
        with self._state_lock:
            self._write_characteristic = value
    
    @property
    def max_retries(self) -> int:
        """Thread-safe max retries access"""
        with self._state_lock:
            return self._max_retries
    
    @property
    def retry_delay(self) -> float:
        """Thread-safe retry delay access"""
        with self._state_lock:
            return self._retry_delay
    
    @property
    def _last_response(self) -> Optional[str]:
        """Backward compatibility for _last_response access"""
        with self._cache_lock:
            return self._response_cache.get('last_response')
    
    @_last_response.setter
    def _last_response(self, value: Optional[str]) -> None:
        """Backward compatibility for _last_response setting"""
        with self._cache_lock:
            self._response_cache['last_response'] = value
            self._response_cache['timestamp'] = time.time()
        
        # Initialize async event loop in separate thread
        self._bt_thread = threading.Thread(
            target=self._bluetooth_loop,
            name='BluetoothManager'
        )
        self.thread_manager.register_thread('bluetooth', self._bt_thread)

    def start(self) -> None:
        """Start Bluetooth manager thread"""
        with self._state_lock:
            if self._state == BluetoothState.ERROR:
                self.logger.error("Cannot start Bluetooth manager - Bleak not available")
                return
        
        self._bt_thread.start()
        self.logger.info("Bluetooth manager started")

    def stop(self) -> None:
        """Stop Bluetooth manager and cleanup resources"""
        self._shutdown_event.set()
        
        # Cleanup async resources
        if self._loop and not self._loop.is_closed():
            try:
                future = asyncio.run_coroutine_threadsafe(
                    self._cleanup_async_resources(), self._loop
                )
                future.result(timeout=5)
            except Exception as e:
                self.logger.error(f"Error during async cleanup: {e}")
        
        # Wait for thread to finish
        if self._bt_thread.is_alive():
            self._bt_thread.join(timeout=5)
            if self._bt_thread.is_alive():
                self.logger.warning("Bluetooth thread did not terminate cleanly")
        
        # Cleanup executor
        self._executor.shutdown(wait=True)
        
        self.logger.info("Bluetooth manager stopped")

    def _bluetooth_loop(self) -> None:
        """Main Bluetooth management loop running in separate thread"""
        try:
            # Create new event loop for this thread
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            
            # Run the async main loop
            self._loop.run_until_complete(self._async_bluetooth_loop())
            
        except Exception as e:
            self.logger.error(f"Bluetooth loop error: {e}", exc_info=True)
            self.state = BluetoothState.ERROR
        finally:
            if self._loop and not self._loop.is_closed():
                self._loop.close()

    async def _async_bluetooth_loop(self) -> None:
        """Async Bluetooth management loop"""
        while not self._shutdown_event.is_set():
            try:
                self.thread_manager.update_heartbeat('bluetooth')
                
                # Thread-safe state access
                with self._state_lock:
                    current_state = self._state
                    
                if current_state == BluetoothState.DISCONNECTED:
                    await self._handle_disconnected()
                elif current_state == BluetoothState.SCANNING:
                    await self._handle_scanning()
                elif current_state == BluetoothState.CONNECTING:
                    await self._handle_connecting()
                elif current_state == BluetoothState.CONNECTED:
                    await self._handle_connected()
                elif current_state == BluetoothState.ERROR:
                    await self._handle_error()
                
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Bluetooth async error: {e}", exc_info=True)
                with self._state_lock:
                    self._state = BluetoothState.ERROR

    async def _handle_disconnected(self) -> None:
        """Handle disconnected state"""
        # Check for stored primary device first
        primary_device = self.device_store.get_primary_device()
        if primary_device:
            self.logger.info(f"Attempting to connect to stored device: {primary_device.name}")
            with self._state_lock:
                self._current_device = (primary_device.mac_address, primary_device.name)
                self._state = BluetoothState.CONNECTING
        else:
            self.logger.info("No stored device found, starting device scan")
            with self._state_lock:
                self._state = BluetoothState.SCANNING

    async def _handle_scanning(self) -> None:
        """Handle scanning state using Bleak device discovery"""
        try:
            self.logger.info("Starting Bluetooth device scan...")
            
            # Use Bleak scanner to discover devices
            devices = await BleakScanner.discover(timeout=8.0)
            
            # Filter for OBD2/ELM327 devices
            elm_devices = []
            for device in devices:
                device_name = device.name or "Unknown"
                if any(keyword in device_name.upper() for keyword in ['OBD', 'ELM', 'OBDII']):
                    elm_devices.append((device.address, device_name))
            
            if elm_devices:
                self.logger.info(f"Found {len(elm_devices)} potential OBD2 devices")
                
                # Prefer devices that are in our store
                preferred_device = None
                for addr, name in elm_devices:
                    stored_device = self.device_store.get_device_by_mac(addr)
                    if stored_device:
                        preferred_device = (addr, name)
                        break
                
                with self._state_lock:
                    self._current_device = preferred_device or elm_devices[0]
                    self._state = BluetoothState.CONNECTING
            else:
                self.logger.warning("No OBD2/ELM327 devices found")
                with self._state_lock:
                    self._state = BluetoothState.ERROR
                
        except Exception as e:
            self.logger.error(f"Scan error: {e}")
            with self._state_lock:
                self._state = BluetoothState.ERROR

    async def _handle_connecting(self) -> None:
        """Handle connecting state using BleakClient"""
        try:
            with self._state_lock:
                current_device = self._current_device
                
            if not current_device:
                with self._state_lock:
                    self._state = BluetoothState.ERROR
                return
                
            addr, name = current_device
            self.logger.info(f"Connecting to {name} ({addr})")
            
            # Create Bleak client
            client = BleakClient(addr)
            with self._state_lock:
                self._client = client
            
            # Connect to device
            await client.connect()
            
            if client.is_connected:
                self.logger.info("Connected successfully")
                
                # Discover services and characteristics for OBD2 communication
                await self._discover_obd_characteristics()
                
                with self._state_lock:
                    self._state = BluetoothState.CONNECTED
                    self._retry_count = 0
                self._connection_event.set()
                
                # Update device store if this is a new device
                stored_device = self.device_store.get_device_by_mac(addr)
                if not stored_device:
                    self.logger.info(f"Connected to new device {name}, but not saving as primary")
            else:
                raise BluetoothConnectionError("Failed to establish connection")
                
        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            await self._cleanup_connection()
            
            with self._state_lock:
                self._retry_count += 1
                retry_count = self._retry_count
                max_retries = self._max_retries
                retry_delay = self._retry_delay
                
            if retry_count >= max_retries:
                with self._state_lock:
                    self._state = BluetoothState.ERROR
            else:
                await asyncio.sleep(retry_delay)
                with self._state_lock:
                    self._state = BluetoothState.SCANNING

    async def _handle_connected(self) -> None:
        """Handle connected state - maintain connection and handle communication"""
        try:
            with self._state_lock:
                client = self._client
                
            if not client or not client.is_connected:
                raise BluetoothConnectionError("Connection lost")
            
            # Send keepalive or test command
            await self._send_keepalive()
            
        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            with self._state_lock:
                self._state = BluetoothState.DISCONNECTED
            self._connection_event.clear()
            await self._cleanup_connection()

    async def _handle_error(self) -> None:
        """Handle error state"""
        self.logger.info("Attempting recovery from error")
        with self._state_lock:
            retry_delay = self._retry_delay
            
        await asyncio.sleep(retry_delay)
        with self._state_lock:
            self._state = BluetoothState.DISCONNECTED
            self._retry_count = 0

    async def _discover_obd_characteristics(self) -> None:
        """Discover OBD2 communication characteristics"""
        try:
            with self._state_lock:
                client = self._client
                
            if not client or not client.is_connected:
                return
            
            # Get all services
            services = client.services
            
            # Look for Serial Port Profile or custom OBD2 service
            for service in services:
                self.logger.debug(f"Found service: {service.uuid}")
                
                for characteristic in service.characteristics:
                    self.logger.debug(f"Found characteristic: {characteristic.uuid}")
                    
                    # Look for write characteristic (typically for sending commands)
                    if "write" in characteristic.properties:
                        with self._state_lock:
                            self._write_characteristic = characteristic.uuid
                        self.logger.info(f"Found write characteristic: {characteristic.uuid}")
                    
                    # Look for notify characteristic (typically for receiving responses)
                    if "notify" in characteristic.properties:
                        with self._state_lock:
                            self._notification_characteristic = characteristic.uuid
                        self.logger.info(f"Found notify characteristic: {characteristic.uuid}")
                        
                        # Enable notifications
                        await client.start_notify(characteristic.uuid, self._notification_handler)
            
        except Exception as e:
            self.logger.error(f"Error discovering characteristics: {e}")

    def _notification_handler(self, sender: str, data: bytes) -> None:
        """Handle incoming notifications from OBD2 device"""
        try:
            # Decode and process incoming data
            message = data.decode('utf-8', errors='ignore').strip()
            self.logger.debug(f"Received notification: {message}")
            
            # Store received data for retrieval by OBD protocol handler (thread-safe)
            # Update both new cache and old attribute for backward compatibility
            with self._cache_lock:
                self._response_cache['last_response'] = message
                self._response_cache['timestamp'] = time.time()
                
        except Exception as e:
            self.logger.error(f"Error handling notification: {e}")

    async def _send_keepalive(self) -> None:
        """Send keepalive command to maintain connection"""
        try:
            with self._state_lock:
                client = self._client
                write_char = self._write_characteristic
                
            if write_char and client:
                # Send basic OBD2 keepalive command
                await client.write_gatt_char(write_char, b"\r\n")
            elif client:
                # If no write characteristic found, just check connection
                if not client.is_connected:
                    raise BluetoothConnectionError("Connection lost")
            else:
                raise BluetoothConnectionError("No client available")
                    
        except Exception as e:
            raise BluetoothConnectionError(f"Keepalive failed: {e}")

    async def _cleanup_connection(self) -> None:
        """Cleanup connection resources with proper synchronization"""
        try:
            with self._state_lock:
                client = self._client
                self._client = None
                
            if client:
                if client.is_connected:
                    await client.disconnect()
        except Exception as e:
            self.logger.error(f"Error during connection cleanup: {e}")

    async def _cleanup_async_resources(self) -> None:
        """Cleanup async resources"""
        await self._cleanup_connection()

    def connect_to_device(self, mac_address: str, device_name: str = None) -> None:
        """
        Force connection to a specific device.
        
        Args:
            mac_address: MAC address of the device to connect to
            device_name: Optional device name for logging
        """
        self.logger.info(f"Forcing connection to device: {mac_address}")
        with self._state_lock:
            self._current_device = (mac_address, device_name or f"Device ({mac_address})")
            self._state = BluetoothState.CONNECTING
            self._retry_count = 0

    def get_connection_status(self) -> Dict[str, Any]:
        """
        Get current connection status information (thread-safe).
        
        Returns:
            Dictionary containing connection status and device information
        """
        with self._state_lock:
            state = self._state
            current_device = self._current_device
            retry_count = self._retry_count
            client = self._client
            
        status = {
            'state': state.name,
            'connected': state == BluetoothState.CONNECTED,
            'current_device': None,
            'retry_count': retry_count,
            'bluetooth_backend': BLUETOOTH_BACKEND,
            'backend_available': BLUETOOTH_AVAILABLE,
            'client_connected': client.is_connected if client else False
        }
        
        if current_device:
            addr, name = current_device
            status['current_device'] = {
                'mac_address': addr,
                'name': name
            }
        
        return status

    def get_backend_info(self) -> Dict[str, Any]:
        """
        Get information about the Bluetooth backend being used.
        
        Returns:
            Dictionary containing backend information
        """
        return {
            'backend': BLUETOOTH_BACKEND,
            'available': BLUETOOTH_AVAILABLE,
            'bleak_available': BLUETOOTH_BACKEND == 'bleak',
            'version': self._get_bleak_version()
        }

    def _get_bleak_version(self) -> Optional[str]:
        """Get Bleak library version"""
        try:
            import bleak
            return bleak.__version__
        except (ImportError, AttributeError):
            return None

    # Synchronous interface methods for backward compatibility
    def send_command(self, command: str, timeout: float = 2.0) -> Optional[str]:
        """
        Send OBD2 command and return response (synchronous interface).
        
        Args:
            command: OBD2 command to send
            timeout: Response timeout in seconds
            
        Returns:
            Response string or None if failed
        """
        with self._state_lock:
            state = self._state
            
        if not self._loop or state != BluetoothState.CONNECTED:
            return None
        
        try:
            # Run async operation in the event loop
            future = asyncio.run_coroutine_threadsafe(
                self._async_send_command(command, timeout), self._loop
            )
            return future.result(timeout=timeout + 1)
        except Exception as e:
            self.logger.error(f"Error sending command: {e}")
            return None

    async def _async_send_command(self, command: str, timeout: float) -> Optional[str]:
        """
        Async implementation of send_command with thread-safe access.
        
        Args:
            command: OBD2 command to send
            timeout: Response timeout in seconds
            
        Returns:
            Response string or None if failed
        """
        try:
            with self._state_lock:
                client = self._client
                write_char = self._write_characteristic
                
            if not client or not client.is_connected:
                return None
            
            if not write_char:
                self.logger.error("No write characteristic available")
                return None
            
            # Send command
            command_bytes = f"{command}\r\n".encode('utf-8')
            await client.write_gatt_char(write_char, command_bytes)
            
            # Wait for response (simplified implementation)
            # In a real implementation, you'd want to use proper async event handling
            await asyncio.sleep(0.1)  # Give device time to respond
            
            # Return last received response (thread-safe)
            with self._cache_lock:
                return self._response_cache.get('last_response')
            
        except Exception as e:
            self.logger.error(f"Error in async send command: {e}")
            return None

    def is_connected(self) -> bool:
        """
        Check if device is currently connected (thread-safe).
        
        Returns:
            True if connected, False otherwise
        """
        with self._state_lock:
            state = self._state
            client = self._client
            
        return (state == BluetoothState.CONNECTED and 
                client is not None and 
                client.is_connected)

    def wait_for_connection(self, timeout: float = 30.0) -> bool:
        """
        Wait for device connection.
        
        Args:
            timeout: Maximum time to wait for connection
            
        Returns:
            True if connected within timeout, False otherwise
        """
        return self._connection_event.wait(timeout)