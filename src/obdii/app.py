#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Main application class for OBDII display application.
Manages component lifecycle and initialization.
"""

import signal
import logging
import atexit
from typing import NoReturn
from .core import ThreadManager, WatchdogMonitor
from .comm import BluetoothManager, OBDProtocol
from .comm.device_store import DeviceStore
from .display import DisplayManager
from .display.setup import SetupDisplayManager
from .utils import ConfigManager, TerminalRestorer

class OBDIIApplication:
    """Main application controller"""
    
    def __init__(self, config_path: str = None, debug: bool = False):
        """Initialize application components"""
        self._config_manager = ConfigManager(config_path)
        self.logger = logging.getLogger(__name__)
        
        # Initialize terminal restorer as early as possible
        self._terminal_restorer = TerminalRestorer()
        
        self._thread_manager = ThreadManager()
        self._watchdog = WatchdogMonitor(
            self._thread_manager, 
            check_interval=5.0,
            warning_timeout=15.0,
            recovery_timeout=30.0,
            critical_timeout=45.0,
            shutdown_callback=self.shutdown
        )
        
        # Initialize device store for setup detection
        self._device_store = DeviceStore()
        self._setup_mode = False
        
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Ensure cleanup on exit
        atexit.register(self.shutdown)

    def start(self) -> None:
        """Start application components"""
        try:
            self.logger.info("Starting OBDII application")
            config = self._config_manager.load_config()
            
            # Check if setup is needed
            if not self._device_store.is_setup_complete():
                self.logger.info("Setup required - entering setup mode")
                self._setup_mode = True
                self._start_setup_mode()
            else:
                self.logger.info("Setup complete - starting normal mode")
                self._start_normal_mode()
            
        except Exception as e:
            self.logger.error(f"Startup failed: {e}", exc_info=True)
            self.shutdown()
            raise
    
    def _start_setup_mode(self) -> None:
        """Start application in setup mode with splash screen"""
        self._watchdog.start()
        
        # Initialize display manager with splash screen
        self._display = DisplayManager(self._thread_manager, self._terminal_restorer)
        self._display.start()  # This automatically starts the splash screen
        self.logger.info("Splash screen activated for setup mode")
        
        # Initialize setup manager while splash is showing
        self._setup_manager = SetupDisplayManager(
            self._display.main_surface,
            self._thread_manager,
            self._display.touch_handler
        )
        self._setup_manager.start_setup()
        
        # Set display to setup mode (will transition after splash completes)
        self._display.set_setup_mode(self._setup_manager)
    
    def _start_normal_mode(self) -> None:
        """Start application in normal mode with splash screen"""
        # Initialize display manager first with splash screen
        self._display = DisplayManager(self._thread_manager, self._terminal_restorer)
        self._display.start()  # This automatically starts the splash screen
        self.logger.info("Splash screen activated for normal mode")
        
        # Initialize other components while splash is showing
        self._bluetooth = BluetoothManager(self._thread_manager, self._device_store)
        self._obd = OBDProtocol(self._bluetooth, self._thread_manager)
        
        # Start background components during splash screen
        self._watchdog.start()
        self._bluetooth.start()
        self._obd.start()
        
        self.logger.info("Background components initialized while splash screen displays")

    def run(self) -> NoReturn:
        """Run application main loop"""
        try:
            self.start()
            signal.pause()
        except KeyboardInterrupt:
            self.logger.info("Shutting down...")
        except Exception as e:
            self.logger.error(f"Runtime error: {e}", exc_info=True)
        finally:
            self.shutdown()

    def shutdown(self) -> None:
        """Shutdown application components"""
        self.logger.info("Shutting down application")
        
        try:
            if hasattr(self, '_setup_manager'):
                self._setup_manager.stop_setup()
            if hasattr(self, '_display'):
                self._display.stop()
            if hasattr(self, '_obd'):
                self._obd.stop()
            if hasattr(self, '_bluetooth'):
                self._bluetooth.stop()
            if hasattr(self, '_watchdog'):
                self._watchdog.stop()
            if hasattr(self, '_thread_manager'):
                self._thread_manager.shutdown()
                
            # Terminal restoration will happen via atexit
        except Exception as e:
            self.logger.error(f"Shutdown error: {e}", exc_info=True)

    def _signal_handler(self, signum: int, frame) -> None:
        """Handle system signals"""
        self.logger.info(f"Received signal {signum}")
        self.shutdown()