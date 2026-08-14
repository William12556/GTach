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

import os
import signal
import logging
import atexit
import threading
from typing import NoReturn
import argparse
from .core import ThreadManager, WatchdogMonitor
from .comm import OBDProtocol, select_transport
from .comm.transport import TRANSPORT_NAMES, TRANSPORT_FORCED, TRANSPORT_FAST
from .comm.device_store import DeviceStore
from .display import DisplayManager
from .display.setup import SetupDisplayManager
from .utils import ConfigManager, TerminalRestorer, get_platform_type

class GTachApplication:
    """Main application controller"""

    # Upper bound on the orderly-exit path once the watchdog has asked
    # for termination. If run()'s finally block has not finished
    # tearing components down within this window, the process exits
    # anyway so systemd (Restart=always) can relaunch it.
    _EXIT_BACKSTOP_SEC: float = 20.0

    def __init__(self, config_path: str = None, debug: bool = False, args=None):
        """Initialize application components"""
        self._config_manager = ConfigManager(config_path)
        self.logger = logging.getLogger(__name__)
        self._args = args or argparse.Namespace()
        self._debug = debug

        # Initialize terminal restorer as early as possible
        self._terminal_restorer = TerminalRestorer()

        # Created before the watchdog: _watchdog_shutdown is bound as
        # the watchdog's shutdown callback and sets this event, so the
        # attribute must already exist at construction time.
        self._stop_event = threading.Event()

        self._thread_manager = ThreadManager()
        self._watchdog = WatchdogMonitor(
            self._thread_manager,
            check_interval=5.0,
            warning_timeout=15.0,
            recovery_timeout=30.0,
            critical_timeout=45.0,
            shutdown_callback=self._watchdog_shutdown
        )

        # Initialize device store for setup detection
        self._device_store = DeviceStore()
        self._setup_mode = False

        # Debounce for the DISCONNECTED screen's Reset button. A press
        # while a reset is in flight is ignored, not queued
        # (issue-4ab5ff88).
        self._reset_in_flight = threading.Event()

        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Ensure cleanup on exit
        atexit.register(self.shutdown)

    def _watchdog_shutdown(self) -> None:
        """Terminate the process in response to a critical-thread timeout.

        Signals the main loop to exit and arms a daemon backstop timer;
        it does not tear anything down itself.

        Teardown is deliberately left to :meth:`run`'s finally block,
        which is idempotent via ``_shutdown_called``. Two consequences
        follow, and both are the point of this split:

        * :meth:`shutdown` is never invoked from the watchdog thread,
          so component stop calls run on the main thread as they do on
          every other exit path.
        * The recovery path does not depend on
          :meth:`WatchdogMonitor.stop`'s self-join guard. Previously the
          callback was ``shutdown`` itself, so the watchdog thread
          called ``WatchdogMonitor.stop()`` on itself; the guard made
          that survivable but left the process alive with its
          components torn down and its screen dead.

        The backstop timer is a daemon thread, so a normal exit that
        beats it is not delayed by its remaining lifetime.
        """
        self.logger.critical(
            "Watchdog requested process termination — signalling main loop "
            f"(force exit in {self._EXIT_BACKSTOP_SEC:.1f}s if not complete)"
        )
        self._stop_event.set()

        timer = threading.Timer(self._EXIT_BACKSTOP_SEC, self._force_exit)
        timer.daemon = True
        timer.start()

    def _force_exit(self) -> None:
        """Force process termination when orderly exit has overrun.

        Called only from the backstop timer armed by
        :meth:`_watchdog_shutdown`. Flushes logging on a best-effort
        basis, then leaves via ``os._exit`` so that no atexit handler,
        finaliser or non-daemon thread can hold the process open.
        """
        self.logger.critical(
            f"Orderly exit did not complete within {self._EXIT_BACKSTOP_SEC:.1f}s "
            "— forcing process termination"
        )
        try:
            logging.shutdown()
        except Exception:
            pass
        os._exit(1)

    def start(self) -> None:
        """Start application components"""
        try:
            from . import __version__
            self.logger.info(f"Starting GTach application v{__version__}")
            config = self._config_manager.load_config()
            
            # Check if setup is needed
            # If --transport is explicitly specified, bypass device store check
            transport_arg = getattr(self._args, 'transport', None)
            transport_forced = transport_arg in TRANSPORT_FORCED
            if transport_forced:
                self.logger.info("Transport explicitly specified - skipping setup mode")
                self._start_normal_mode()
            # The complement of the forced set, computed rather than
            # restated so the two cannot drift (core review §5.8).
            elif (transport_arg in TRANSPORT_NAMES
                  and transport_arg not in TRANSPORT_FORCED):
                # Bluetooth transport — always enter setup mode for device pairing
                from .comm.sim_bluetooth import SimBluetoothPairing
                pairing_factory = (lambda: SimBluetoothPairing()) if transport_arg == 'simbt' else None
                self.logger.info(f"{transport_arg} transport - entering setup mode")
                self._setup_mode = True
                self._start_setup_mode(pairing_factory=pairing_factory)
            elif self._device_store.get_primary_device() is None:
                self.logger.info("Setup required - entering setup mode")
                self._setup_mode = True
                self._start_setup_mode()
            else:
                self.logger.info("Setup complete - starting normal mode")
                self._start_normal_mode()

            self._clear_update_probation()
            self._finish_startup_logging()

        except Exception as e:
            self.logger.error(f"Startup failed: {e}", exc_info=True)
            self.shutdown()
            raise

    def _clear_update_probation(self) -> None:
        """Remove the update-probation marker on healthy startup.

        Signals the boot-time supervisor that the current install reached
        successful startup, so a newly applied wheel is not rolled back.
        Linux deployment only; tolerant of all errors.
        """
        try:
            import os
            import sys
            if sys.platform.startswith('linux'):
                marker = "/opt/gtach/.update-probation"
                if os.path.exists(marker):
                    os.remove(marker)
                    self.logger.info("Cleared update probation marker — startup healthy")
        except Exception as e:
            self.logger.debug(f"Could not clear probation marker: {e}")

    def _finish_startup_logging(self) -> None:
        """Detach start.log after startup is complete.

        Raises the start handler threshold to suppress further writes.
        Startup records are retained in the file.
        """
        try:
            import logging
            import sys
            if sys.platform.startswith('linux'):
                # gtach/__init__.py re-exports the main FUNCTION under
                # the name 'main', so the package attribute shadows the
                # module and 'from . import main' retrieves the
                # function — whose namespace has no _debug_handler or
                # _start_handler. The module object is retrievable from
                # sys.modules, which the import system keys by the full
                # dotted name (issue-c1d4b8e6).
                _main = sys.modules.get('gtach.main')
                if _main is None:
                    return
                if _main._start_handler is not None:
                    self.logger.info("Startup complete — start.log closed")
                    _main._start_handler.setLevel(logging.CRITICAL + 1)
        except Exception as e:
            self.logger.debug(f"Could not finish startup logging: {e}")

    def toggle_debug_logging(self, enable: bool) -> None:
        """Activate or suppress runtime diagnostics.

        Toggles debug.log's handler level and, on the same signal, arms
        or disarms the periodic all-thread stack dumps written to
        stacks.log. This is the signal that turns debug on in the field
        — bin/gtach.service passes no --debug, so the startup flag
        never fires in production (issue-2ac1c602 iteration 3).

        The two diagnostics degrade independently: a failure in the
        stack-dump path cannot prevent the debug log handler from being
        toggled, which is the operator's primary diagnostic control.

        Args:
            enable: True to start writing to debug.log and dumping
                stacks; False to suppress both.
        """
        try:
            import logging
            import sys
            if not sys.platform.startswith('linux'):
                return
            # gtach/__init__.py re-exports the main FUNCTION under the
            # name 'main', so the package attribute shadows the module
            # and 'from . import main' retrieves the function — whose
            # namespace has no _debug_handler or _start_handler. The
            # module object is retrievable from sys.modules, which the
            # import system keys by the full dotted name
            # (issue-c1d4b8e6).
            _main = sys.modules.get('gtach.main')
            if _main is None:
                return
            if _main._debug_handler is None:
                return
            if enable:
                _main._debug_handler.setLevel(logging.DEBUG)
                self.logger.info("Debug logging enabled")
                # Own guard, and getattr rather than attribute access:
                # a partially loaded or older gtach.main must not raise
                # out of the debug-handler toggle.
                try:
                    _arm = getattr(_main, 'enable_stack_dumps', None)
                    if _arm is not None:
                        _arm()
                except Exception as e:
                    self.logger.debug(
                        f"Could not arm stack dumps: {e}", exc_info=True
                    )
            else:
                _main._debug_handler.setLevel(logging.CRITICAL + 1)
                self.logger.info("Debug logging disabled")
                try:
                    _disarm = getattr(_main, 'disable_stack_dumps', None)
                    if _disarm is not None:
                        _disarm()
                except Exception as e:
                    self.logger.debug(
                        f"Could not disarm stack dumps: {e}", exc_info=True
                    )
        except Exception as e:
            self.logger.debug(f"Could not toggle debug logging: {e}")

    def _disconnected_cause(self):
        """Resolve the string the DISCONNECTED screen's cause line shows.

        Called on the display thread on every frame the DISCONNECTED
        screen is drawn.

        Returns:
            The cause string, or None when there is nothing to show.
        """
        transport = getattr(self, '_transport', None)

        return getattr(transport, 'last_failure_cause', None)

    def _on_reset_pi(self) -> None:
        """Dispatch an operator-requested reboot of the host.

        Returns immediately, performing no blocking call itself. The
        reboot runs on a daemon worker because 'display' is a watchdog
        critical thread at a 45 s timeout, and since change-2ac1c602 a
        critical timeout terminates the process — so a synchronous
        subprocess in this touch callback would race the reboot against
        the watchdog (issue-4ab5ff88).

        A press while a reset is in flight is ignored rather than
        queued: repeated reboots are not useful and a queue would let
        an impatient operator stack them.

        No outcome is written to the cause line. A successful reboot
        ends the process before any such status could be read, so the
        debounce alone is what a second press meets.

        The worker is deliberately NOT registered with ThreadManager.
        It is short-lived, and registering it would put it under
        WatchdogMonitor for the seconds it exists.
        """
        if self._reset_in_flight.is_set():
            self.logger.info("Reset already in flight - press ignored")
            return
        self._reset_in_flight.set()

        self.logger.info("Operator requested device reset")

        def _worker() -> None:
            try:
                from .utils import pi_reset
                outcome = pi_reset.reboot_device()
                self.logger.info(f"Reset outcome: {outcome}")
            except Exception as e:
                self.logger.error(f"Reset worker failed: {e}", exc_info=True)
            finally:
                # In a finally so a raising worker cannot wedge the
                # button for the life of the process.
                self._reset_in_flight.clear()

        threading.Thread(target=_worker, name='pi_reset', daemon=True).start()

    def _request_restart(self) -> None:
        """Request a clean restart; systemd (Restart=always) relaunches,
        and gtach-preflight.sh installs any staged wheel."""
        self.logger.info("Restart requested — stopping for relaunch")
        self._stop_event.set()

    def _start_setup_mode(self, pairing_factory=None) -> None:
        """Start application in setup mode with splash screen"""
        # Guard: watchdog may already be running on re-entry
        if not self._watchdog._thread.is_alive():
            self._watchdog.start()

        # Reuse existing DisplayManager on re-entry; only create on first call
        if not hasattr(self, '_display') or self._display is None:
            self._display = DisplayManager(self._thread_manager, self._terminal_restorer)
            self._display._setup_entry_callback = self._re_enter_setup
            self._display._restart_callback = self._request_restart
            self._display._debug_toggle_callback = self.toggle_debug_logging
            self._display._debug_logging_on = self._debug
            # The display asks the transport whether the link is up.
            # Guarded: during setup, and before select_transport has
            # run, there is no transport — and 'no transport' is
            # correctly 'not connected' (issue-4d9e2f18).
            self._display._link_connected_callback = (
                lambda: bool(
                    getattr(self, '_transport', None)
                    and self._transport.is_connected()
                )
            )
            # Same guard, same reason: before select_transport has run
            # there is no transport, and 'no transport' has no failure
            # cause to report (issue-5e7a03c4).
            self._display._link_cause_callback = self._disconnected_cause
            # Wired here as well as in _start_normal_mode: _start_obd
            # runs against THIS display instance after setup completes
            # (app.py:485), so the DISCONNECTED screen reached by that
            # route is drawn by it. Wiring only normal mode would leave
            # the button absent for every operator who passed through
            # setup.
            self._display._reset_callback = self._on_reset_pi
            # Period for the DISCONNECTED screen's retry arc, guarded
            # the same way and for the same reason. Yields None today —
            # reconnect_indefinitely is started without a retry_delay,
            # so its 5.0 s default applies and the arc's own fallback
            # is that same 5.0. Reading the attribute rather than
            # hard-coding it means the arc follows any future
            # configured value without further wiring (issue-4f1e82b7).
            self._display._retry_interval_callback = (
                lambda: getattr(
                    getattr(self, '_transport', None), 'retry_delay', None
                )
            )
            self._display.start()
            self.logger.info("Splash screen activated for setup mode")
        else:
            self.logger.info("Reusing existing DisplayManager for setup re-entry")

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
        if getattr(self, '_obd_started', False):
            self.logger.warning("_on_setup_complete called more than once — ignoring")
            return
        self._obd_started = True
        self.logger.info("Setup complete — transitioning to normal mode")
        self._display.exit_setup_mode()
        self._start_obd()

    def _re_enter_setup(self) -> None:
        """Re-enter setup mode from DISCONNECTED screen"""
        try:
            self.logger.info("Re-entering setup from DISCONNECTED screen")

            # Same sequence as shutdown() (app.py:295-310), and for
            # the same reason. ThreadManager.stop_thread sets no
            # event and does not call the registered stop_func, so
            # it can only join. OBDProtocol's inner loop is bounded
            # by transport.is_connected() (obd.py:79) and its outer
            # loop by shutdown_event (obd.py:68), and when the
            # transport is down the outer loop sleeps and continues
            # rather than returning (obd.py:72-74). Disconnecting
            # alone does not end the thread and stopping alone does
            # not either — both are required, in this order.
            # Previously the join came first, could never succeed,
            # and ran to its 5s default on a UI callback while
            # holding the thread-state lock (core review §5.9).

            # 1. Transport — closes the socket, releasing the OBD
            #    thread from any blocking read.
            if hasattr(self, '_transport'):
                try:
                    self._transport.disconnect()
                except Exception as e:
                    self.logger.warning(f"Transport disconnect on re-entry: {e}")

            # 2. OBD — sets shutdown_event, which is the only thing
            #    that ends _protocol_loop.
            if hasattr(self, '_obd'):
                try:
                    self._obd.stop()
                except Exception as e:
                    self.logger.warning(f"OBD stop on re-entry: {e}")

            # 3. Thread manager — bookkeeping. The thread is already
            #    dead by now, so this records STOPPED rather than
            #    FAILED. 2.0s rather than the 5.0s default because
            #    this runs on a UI-driven callback and a join that
            #    needs longer than that indicates a fault worth
            #    seeing in the log.
            if hasattr(self, '_thread_manager'):
                self._thread_manager.stop_thread('obd_protocol', timeout=2.0)

            self._obd_started = False
            # Re-enter setup
            self._start_setup_mode()
        except Exception as e:
            self.logger.error(f"Re-enter setup error: {e}", exc_info=True)

    def _start_obd(self) -> None:
        """Start transport and OBD protocol against the existing display"""
        platform_type = get_platform_type()
        self._transport = select_transport(platform_type, self._args)
        transport_arg = getattr(self._args, 'transport', None)
        _poll_interval = 0.02 if transport_arg in TRANSPORT_FAST else 0.05
        self._obd = OBDProtocol(self._transport, self._thread_manager, poll_interval_s=_poll_interval, adapter_pre_initialised=True)
        # Registration is what makes the thread visible to
        # WatchdogMonitor, which iterates thread_manager.threads only:
        # a bare Thread(name='transport') is not monitored however it
        # is named (issue-2ac1c602).
        transport_thread = threading.Thread(
            target=self._transport.reconnect_indefinitely,
            kwargs={'heartbeat': lambda: self._thread_manager.update_heartbeat('transport')},
            name='transport', daemon=True
        )
        self._thread_manager.register_thread('transport', transport_thread)
        transport_thread.start()
        self._obd.start()
        self.logger.info("OBD protocol started after setup")

    def _start_normal_mode(self) -> None:
        """Start application in normal mode with splash screen"""
        # Initialize display manager first with splash screen
        self._display = DisplayManager(self._thread_manager, self._terminal_restorer)
        self._display._setup_entry_callback = self._re_enter_setup
        self._display._restart_callback = self._request_restart
        self._display._debug_toggle_callback = self.toggle_debug_logging
        self._display._debug_logging_on = self._debug
        # The display asks the transport whether the link is up.
        # Guarded: before select_transport has run there is no
        # transport — and 'no transport' is correctly 'not connected'
        # (issue-4d9e2f18).
        self._display._link_connected_callback = (
            lambda: bool(
                getattr(self, '_transport', None)
                and self._transport.is_connected()
            )
        )
        # Same guard, same reason: before select_transport has run
        # there is no transport, and 'no transport' has no failure
        # cause to report (issue-5e7a03c4).
        self._display._link_cause_callback = self._disconnected_cause
        self._display._reset_callback = self._on_reset_pi
        # Period for the DISCONNECTED screen's retry arc, guarded the
        # same way and for the same reason. Yields None today —
        # reconnect_indefinitely is started without a retry_delay, so
        # its 5.0 s default applies and the arc's own fallback is that
        # same 5.0. Reading the attribute rather than hard-coding it
        # means the arc follows any future configured value without
        # further wiring (issue-4f1e82b7).
        self._display._retry_interval_callback = (
            lambda: getattr(
                getattr(self, '_transport', None), 'retry_delay', None
            )
        )
        self._display.start()  # This automatically starts the splash screen
        self.logger.info("Splash screen activated for normal mode")
        
        # Initialize transport and OBD protocol
        platform_type = get_platform_type()
        self._transport = select_transport(platform_type, self._args)
        self._obd = OBDProtocol(self._transport, self._thread_manager)
        
        # Start background components during splash screen
        self._watchdog.start()
        
        # Start reconnect_indefinitely in a daemon thread.
        # Registration is what makes the thread visible to
        # WatchdogMonitor, which iterates thread_manager.threads only:
        # a bare Thread(name='transport') is not monitored however it
        # is named (issue-2ac1c602).
        transport_thread = threading.Thread(
            target=self._transport.reconnect_indefinitely,
            kwargs={'heartbeat': lambda: self._thread_manager.update_heartbeat('transport')},
            name='transport', daemon=True
        )
        self._thread_manager.register_thread('transport', transport_thread)
        transport_thread.start()
        
        self._obd.start()
        
        self.logger.info("Background components initialized while splash screen displays")

    def run(self) -> NoReturn:
        """Run application main loop"""
        try:
            self.start()
            while not self._stop_event.is_set():
                self._stop_event.wait(timeout=0.5)
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