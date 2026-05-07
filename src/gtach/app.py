#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Main application class for GTach display application.
Manages component lifecycle and initialization.
"""

import signal
import logging
import atexit
import threading
from typing import NoReturn
import argparse
from .core import ThreadManager, WatchdogMonitor
from .comm import OBDProtocol, select_transport
from .comm.device_store import DeviceStore
from .display import DisplayManager
from .display.setup import SetupDisplayManager
from .utils import ConfigManager, TerminalRestorer, get_platform_type

class GTachApplication:
    """Main application controller"""
    
    def __init__(self, config_path: str = None, debug: bool = False, args=None):
        """Initialize application components"""
        self._config_manager = ConfigManager(config_path)
        self.logger = logging.getLogger(__name__)
        self._args = args or argparse.Namespace()
        
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
        self._stop_event = threading.Event()
        
        # Ensure cleanup on exit
        atexit.register(self.shutdown)

    def start(self) -> None:
        """Start application components"""
        try:
            self.logger.info("Starting GTach application")
            config = self._config_manager.load_config()
            
            # Check if setup is needed
            # If --transport is explicitly specified, bypass device store check
            transport_arg = getattr(self._args, 'transport', None)
            transport_forced = transport_arg in ('tcp', 'serial', 'simtcp')
            if transport_forced:
                self.logger.info("Transport explicitly specified - skipping setup mode")
                self._start_normal_mode()
            elif transport_arg == 'simbt':
                # Simulation mode with Bluetooth setup
                from .comm.sim_bluetooth import SimBluetoothPairing
                self.logger.info("Simulation Bluetooth transport - entering setup mode")
                self._setup_mode = True
                self._start_setup_mode(pairing_factory=lambda: SimBluetoothPairing())
            elif self._device_store.get_primary_device() is None:
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
    
    def _start_setup_mode(self, pairing_factory=None) -> None:
        """Start application in setup mode with splash screen"""
        self._watchdog.start()

        # Initialize display manager with splash screen
        self._display = DisplayManager(self._thread_manager, self._terminal_restorer)
        self._display.start()  # This automatically starts the splash screen
        self.logger.info("Splash screen activated for setup mode")

        # Initialize setup manager while splash is showing
        self._setup_manager = SetupDisplayManager(
            self._display.rendering_engine.main_surface,
            self._thread_manager,
            self._display.touch_handler,
            pairing_factory=pairing_factory,
            on_complete=self._on_setup_complete
        )
        self._setup_manager.start_setup()
        
        # Set display to setup mode (will transition after splash completes)
        self._display.set_setup_mode(self._setup_manager)
    
    def _on_setup_complete(self) -> None:
        """Called by SetupDisplayManager when setup finishes"""
        self.logger.info("Setup complete — transitioning to normal mode")
        self._display.exit_setup_mode()
        self._start_obd()

    def _start_obd(self) -> None:
        """Start transport and OBD protocol against the existing display"""
        platform_type = get_platform_type()
        self._transport = select_transport(platform_type, self._args)
        self._obd = OBDProtocol(self._transport, self._thread_manager)
        transport_thread = threading.Thread(
            target=self._transport.reconnect_indefinitely, name='transport', daemon=True
        )
        transport_thread.start()
        self._obd.start()
        self.logger.info("OBD protocol started after setup")

    def _start_normal_mode(self) -> None:
        """Start application in normal mode with splash screen"""
        # Initialize display manager first with splash screen
        self._display = DisplayManager(self._thread_manager, self._terminal_restorer)
        self._display.start()  # This automatically starts the splash screen
        self.logger.info("Splash screen activated for normal mode")
        
        # Initialize transport and OBD protocol
        platform_type = get_platform_type()
        self._transport = select_transport(platform_type, self._args)
        self._obd = OBDProtocol(self._transport, self._thread_manager)
        
        # Start background components during splash screen
        self._watchdog.start()
        
        # Start reconnect_indefinitely in a daemon thread
        transport_thread = threading.Thread(target=self._transport.reconnect_indefinitely, name='transport', daemon=True)
        transport_thread.start()
        
        self._obd.start()
        
        self.logger.info("Background components initialized while splash screen displays")

    def run(self) -> NoReturn:
        """Run application main loop"""
        try:
            self.start()
            self._stop_event.wait()
        except (KeyboardInterrupt, SystemExit):
            self.logger.info("Shutting down...")
        except Exception as e:
            self.logger.error(f"Runtime error: {e}", exc_info=True)
        finally:
            self.shutdown()

    def shutdown(self) -> None:
        """Shutdown application components"""
        if getattr(self, '_shutdown_called', False):
            return
        self._shutdown_called = True

        self.logger.info("Shutting down application")

        try:
            # Shutdown order is important:
            # 1. Watchdog first — prevents recovery attempts on dying threads
            # 2. Display — closes pygame window
            # 3. Transport — closes socket, unblocks any OBD thread blocked on recv
            # 4. OBD — safe to join now that socket is closed
            # 5. Thread manager — final cleanup
            if hasattr(self, '_watchdog'):
                self._watchdog.stop()
            if hasattr(self, '_setup_manager'):
                self._setup_manager.stop_setup()
            if hasattr(self, '_display'):
                self._display.stop()
            if hasattr(self, '_transport'):
                self._transport.disconnect()
            if hasattr(self, '_obd'):
                self._obd.stop()
            if hasattr(self, '_thread_manager'):
                self._thread_manager.shutdown()

            # Terminal restoration will happen via atexit
        except Exception as e:
            self.logger.error(f"Shutdown error: {e}", exc_info=True)

    def _signal_handler(self, signum: int, frame) -> None:
        """Handle system signals"""
        self.logger.info(f"Received signal {signum}")
        self._stop_event.set()
        raise SystemExit(0)