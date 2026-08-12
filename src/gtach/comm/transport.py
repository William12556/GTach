"""
OBD Transport Abstraction Layer

This module defines the abstract base class for OBD transport implementations,
including state management, error handling, and a factory function for selecting
the appropriate transport based on platform and arguments.

Copyright (c) 2025 William Watson. This work is licensed under the MIT License.
"""

from abc import ABC, abstractmethod
from enum import Enum, auto
import argparse
import errno as _errno
import logging
import os
import threading
from typing import Callable, Optional

from ..utils.platform import PlatformType
from .device_store import DeviceStore


# The transport name set and its classifications, defined
# once. Previously maintained in four places — main.py's
# argparse choices, app.py's forced test, app.py's fast-poll
# test and select_transport below — with an omission in any
# one of them changing behaviour silently rather than
# raising (core review §5.8).
TRANSPORT_NAMES = ('tcp', 'serial', 'rfcomm', 'simtcp', 'simbt')

# Forced transports skip setup mode. simtcp is forced while
# simbt routes through setup: that asymmetry is deliberate
# and serves the pairing-simulation design. Do not
# 'correct' it.
TRANSPORT_FORCED = ('tcp', 'serial', 'simtcp')

# Fast transports poll at 0.02 s rather than 0.05 s.
TRANSPORT_FAST = ('simbt', 'simtcp', 'tcp')


# errno arrives at connect()'s first except handler and was discarded
# there, so an adapter fault and a missing OBD dongle produced
# identical logs and an identical DISCONNECTED screen. Establishing
# which it was took a full session of manual hcitool work to recover
# information errno already carried (issue-5e7a03c4).
#
# Every value is 40 characters or fewer so it renders on the 480x480
# display without truncation. A test asserts that bound over the whole
# mapping; keep any addition within it.
_CONNECT_FAULT_CAUSES = {
    _errno.EBUSY: 'bluetooth link busy - may need reset',
    _errno.ETIMEDOUT: 'connection timed out',
    _errno.EHOSTDOWN: 'adapter not reachable',
    _errno.EHOSTUNREACH: 'adapter not reachable',
    _errno.ENODEV: 'no bluetooth controller',
    _errno.ENETDOWN: 'bluetooth controller down',
    _errno.ECONNREFUSED: 'connection refused by adapter',
}

# Sysfs path listing Bluetooth controllers. PlatformDetector already
# probes this same path (platform.py:706), so reading it here is a
# precedented pattern rather than a new dependency.
_BLUETOOTH_SYSFS = '/sys/class/bluetooth'


def _bluetooth_adapter_present() -> bool:
    """Report whether a Bluetooth controller is present.

    Reads sysfs only. This change REPORTS and must never ACT on the
    host: no adapter reset, rfkill cycle, hciuart restart or module
    reload, and no shell invocation of any kind (issue-5e7a03c4).

    Returns:
        True if any controller is listed, False if the directory
        exists and is empty, and True if the check cannot be performed
        at all. The unknown case is deliberately optimistic: an
        unreadable sysfs must never be reported to the operator as a
        hardware fault.
    """
    try:
        if not os.path.isdir(_BLUETOOTH_SYSFS):
            return True
        return bool(os.listdir(_BLUETOOTH_SYSFS))
    except Exception:
        return True


class TransportState(Enum):
    """Enumeration of transport connection states."""
    
    DISCONNECTED = auto()
    """Transport is disconnected."""
    
    CONNECTING = auto()
    """Transport is in the process of connecting."""
    
    CONNECTED = auto()
    """Transport is connected and ready for communication."""
    
    ERROR = auto()
    """Transport encountered an error."""


class TransportError(Exception):
    """Base exception for transport-related errors."""
    pass


class ConnectionError(TransportError):
    """Exception raised for connection-related errors."""
    pass


class TimeoutError(TransportError):
    """Exception raised for timeout-related errors."""
    pass


class ProtocolError(TransportError):
    """Exception raised for protocol-related errors."""
    pass


class OBDTransport(ABC):
    """Abstract base class for OBD transport implementations.

    Holds the connection skeleton once. RFCOMM, TCP and serial had
    three near-identical copies of connect, disconnect, send_command,
    is_connected and state, differing only in how a handle is opened,
    closed, written to and read from (core review §5.8). Those four
    operations are the abstract surface; everything else is concrete
    here.

    The capture-then-use discipline in send_command is the point of
    change-6481f8ce: the handle is captured under the lock ONCE and
    every subsequent operation uses that reference, so a concurrent
    disconnect() produces the I/O error the handlers expect rather than
    an AttributeError on None (core review §5.3).
    """

    # Errors a subclass's I/O raises when the handle or the peer fails.
    # Caught by connect and send_command, which mark the transport
    # disconnected and discard the handle.
    _IO_ERRORS: tuple = (OSError,)

    # Errors meaning "no response within the timeout". Logged and
    # returning None WITHOUT marking the transport disconnected. Caught
    # before _IO_ERRORS because socket.timeout is an OSError subclass.
    _TIMEOUT_ERRORS: tuple = ()

    # Whether an empty read means the peer closed the connection.
    # True for stream sockets. False for pyserial, whose read_until
    # returns b'' on timeout with the port still open.
    _EMPTY_READ_IS_EOF: bool = True

    # Consecutive read timeouts that constitute a dead peer. A command
    # timeout is 1.0 s and the observed failure cycled at ~1.07 s, so
    # five trips the threshold at ~5.4 s: above any single slow adapter
    # response, and below WatchdogMonitor's 15 s warning threshold, so
    # the link is dropped and reconnection is under way before the
    # watchdog has anything to say about it (issue-9c2f41d8).
    _MAX_CONSECUTIVE_TIMEOUTS: int = 5

    def __init__(self):
        # OBDTransport is abstract. The four handle primitives below are
        # deliberately NOT @abstractmethod: SimTransport overrides the
        # whole skeleton and supplies none of them, and change-6481f8ce
        # may not modify it. Declaring them abstract would make
        # SimTransport uninstantiable and break simtcp and simbt. The
        # guard keeps direct instantiation an error regardless.
        if type(self) is OBDTransport:
            raise TypeError(
                "OBDTransport is abstract and cannot be instantiated"
            )
        self._shutdown = threading.Event()
        self._lock = threading.RLock()
        self._handle = None
        self._state = TransportState.DISCONNECTED
        self._consecutive_timeouts = 0
        self._last_failure_cause: Optional[str] = None

    def _open(self):
        """Open and return a connected handle.

        Returns:
            The handle, or None if no device could be resolved.
        """
        raise NotImplementedError(
            f"{type(self).__name__} must implement _open"
        )

    def _close(self, handle) -> None:
        """Close the given handle."""
        raise NotImplementedError(
            f"{type(self).__name__} must implement _close"
        )

    def _write(self, handle, data: bytes) -> None:
        """Write bytes to the given handle."""
        raise NotImplementedError(
            f"{type(self).__name__} must implement _write"
        )

    def _read(self, handle, n: int) -> bytes:
        """Read up to n bytes from the given handle."""
        raise NotImplementedError(
            f"{type(self).__name__} must implement _read"
        )

    def _set_timeout(self, handle, timeout: float) -> None:
        """Apply a read timeout to the handle. Override if it differs."""
        handle.settimeout(timeout)

    def _describe(self) -> str:
        """Describe the endpoint, for log messages."""
        return self.__class__.__name__

    def _acquire_handle(self):
        """Return the handle captured under the lock.

        is_connected() reads the state under the lock and releases it,
        so a caller acting on its result is acting on a stale answer.
        Capturing the reference means a closed handle fails the way the
        code already handles (core review §5.3).

        Returns:
            The handle, or None if not connected.
        """
        with self._lock:
            return self._handle

    def _discard_handle(self) -> None:
        """Close and clear the handle, acquiring the lock."""
        with self._lock:
            self._discard_handle_locked()

    def _discard_handle_locked(self) -> None:
        """Close and clear the handle. The caller holds the lock."""
        handle = self._handle
        self._handle = None
        if handle is not None:
            try:
                self._close(handle)
            except self._IO_ERRORS:
                pass

    @property
    def last_failure_cause(self) -> Optional[str]:
        """Why the most recent connect attempt failed.

        Read from the display thread while :meth:`connect` writes it
        from the transport thread, so both go through ``_lock``.

        Returns:
            A short cause string, or None when no connect has failed
            since the last success.
        """
        with self._lock:
            return self._last_failure_cause

    def _classify_connect_error(self, exc: OSError) -> str:
        """Resolve a connect failure to a named cause.

        A missing controller overrides whatever errno reported: it is
        the more specific and more actionable fact, and errno alone
        cannot discriminate a controller that is absent from a peer
        that is merely unreachable.

        Never raises, for any input including an exception carrying no
        errno at all — a diagnostic must not become a new failure
        source.

        Args:
            exc: The exception raised by the connect attempt.

        Returns:
            A short cause string, never empty.
        """
        try:
            if not _bluetooth_adapter_present():
                return 'no bluetooth controller'

            code = getattr(exc, 'errno', None)
            if code in _CONNECT_FAULT_CAUSES:
                return _CONNECT_FAULT_CAUSES[code]
            if code is not None:
                # Unmapped: the errno NAME is still far more use than
                # discarding it, which is what happened before.
                named = _errno.errorcode.get(code)
                if named:
                    return named
            return str(exc) or 'unknown connection failure'
        except Exception:
            return 'unknown connection failure'

    def connect(self) -> bool:
        """Establish a connection to the OBD device.

        Returns:
            bool: True if the connection was successful, False otherwise.
        """
        logger = logging.getLogger(self.__class__.__name__)
        with self._lock:
            self._state = TransportState.CONNECTING

        try:
            handle = self._open()
            if handle is None:
                with self._lock:
                    self._state = TransportState.DISCONNECTED
                return False

            with self._lock:
                self._handle = handle
                self._state = TransportState.CONNECTED
                self._last_failure_cause = None
            logger.info("Connected to %s", self._describe())
            return True
        except self._IO_ERRORS as e:
            cause = self._classify_connect_error(e)
            logger.error("Failed to connect to %s: %s (%s)",
                         self._describe(), e, cause)
            self._discard_handle()
            with self._lock:
                self._state = TransportState.DISCONNECTED
                self._last_failure_cause = cause
            return False
        except Exception as e:
            logger.error("Unexpected error during connection to %s: %s",
                         self._describe(), e)
            self._discard_handle()
            with self._lock:
                self._state = TransportState.ERROR
            return False

    def disconnect(self) -> None:
        """Close the connection to the OBD device."""
        logger = logging.getLogger(self.__class__.__name__)
        self._shutdown.set()
        with self._lock:
            self._discard_handle_locked()
            self._state = TransportState.DISCONNECTED
        logger.info("Disconnected from %s", self._describe())

    def drop_link(self) -> None:
        """Close the current link while leaving reconnection possible.

        The distinction from :meth:`disconnect` is the whole point of
        this method and must not be collapsed. ``disconnect()`` ends the
        transport's life: it sets ``_shutdown``, which is the event
        :meth:`reconnect_indefinitely` loops on and waits on, and which
        nothing ever clears. ``drop_link()`` closes only the CURRENT
        link, so the supervising loop observes ``is_connected()`` go
        False and re-establishes it.

        Tearing a dead link down via ``disconnect()`` would permanently
        disable reconnection for the life of the process, while still
        satisfying any check that merely asserts the transport went
        not-connected (issue-9c2f41d8).

        Safe to call when nothing is connected: ``_discard_handle_locked``
        tolerates a None handle.
        """
        logger = logging.getLogger(self.__class__.__name__)
        with self._lock:
            self._discard_handle_locked()
            self._state = TransportState.DISCONNECTED
        logger.info("Link to %s dropped - will attempt to reconnect",
                    self._describe())

    def send_command(self, command: str, timeout: float = 2.0) -> Optional[str]:
        """Send a command to the OBD device and receive the response.

        Args:
            command: The OBD command to send.
            timeout: Timeout in seconds for the response.

        Returns:
            Optional[str]: The response from the device, or None if the command failed.
        """
        logger = logging.getLogger(self.__class__.__name__)
        # Capture ONCE, before the receive loop. Re-capturing per
        # iteration would reintroduce the window this closes.
        handle = self._acquire_handle()
        if handle is None:
            logger.warning("Cannot send command: transport is not connected")
            return None

        try:
            # Prepare the command
            encoded_cmd = (command.strip() + '\r').encode('ascii')
            logger.debug("TX: %r", encoded_cmd)
            self._write(handle, encoded_cmd)

            # Set timeout for response
            self._set_timeout(handle, timeout)

            # Read response until '>' prompt is received
            buf = b''
            while True:
                data = self._read(handle, 1024)
                if not data:
                    if self._EMPTY_READ_IS_EOF:
                        # Connection closed by the other end
                        with self._lock:
                            self._state = TransportState.DISCONNECTED
                        logger.error("Connection closed by device")
                        return None
                    # A timed-out read on an open port: return what
                    # arrived, as the serial implementation always did.
                    break
                buf += data
                if b'>' in buf:
                    break

            # Decode and strip the response
            response = buf.decode('ascii', errors='ignore').strip()
            # Remove the trailing '>' prompt
            response = response.rstrip('>').strip()
            logger.debug("RX: %r", response)
            # Any answer at all means the peer is alive. The threshold
            # counts CONSECUTIVE silences, so an occasional slow
            # response never accumulates towards a drop.
            with self._lock:
                self._consecutive_timeouts = 0
            return response
        except self._TIMEOUT_ERRORS:
            logger.warning("Timeout waiting for response from device "
                           "(cmd=%r, timeout=%.1fs)", command, timeout)
            with self._lock:
                self._consecutive_timeouts += 1
                _dead = self._consecutive_timeouts >= self._MAX_CONSECUTIVE_TIMEOUTS
                if _dead:
                    # Reset here, under the same lock that observed the
                    # trip, so the next silence starts a fresh count and
                    # a sixth timeout cannot drop the link a second time.
                    _count = self._consecutive_timeouts
                    self._consecutive_timeouts = 0
            if _dead:
                logger.error(
                    "No response from %s after %d consecutive timeouts "
                    "- dropping link", self._describe(), _count
                )
                # OUTSIDE the lock: drop_link takes _lock itself. The
                # decision is captured above and acted on here.
                self.drop_link()
            return None
        except self._IO_ERRORS as e:
            logger.error("Error communicating with device: %s", e)
            with self._lock:
                self._state = TransportState.DISCONNECTED
            self._discard_handle()
            return None
        except Exception as e:
            logger.error("Unexpected error during command send: %s", e)
            return None

    def is_connected(self) -> bool:
        """Check if the transport is currently connected.

        Returns:
            bool: True if connected, False otherwise.
        """
        with self._lock:
            return self._state == TransportState.CONNECTED

    @property
    def state(self) -> TransportState:
        """Get the current state of the transport.

        Returns:
            TransportState: The current state.
        """
        with self._lock:
            return self._state

    def reconnect_indefinitely(self, retry_delay: float = 5.0,
                               heartbeat: Optional[Callable[[], None]] = None) -> None:
        """Supervise the link for the life of the process.

        Connects, then watches the established link and reconnects
        whenever it drops. This method does NOT return on a successful
        connect; its only exit is ``_shutdown`` being set. Both call
        sites run it on a daemon thread registered with ThreadManager
        as 'transport', so that thread simply never returns
        (change-2ac1c602).

        Previously it returned on first success, which left nothing to
        re-enter it: a mid-session link loss was unrecoverable for the
        life of the process (issue-9c2f41d8).

        Every wait is on ``_shutdown`` rather than ``time.sleep``, so a
        shutdown while connected or mid-retry is observed immediately
        rather than after the remaining delay.

        Args:
            retry_delay: Delay in seconds between retry attempts.
            heartbeat: Optional zero-argument callable invoked at each
                point in the loop where liveness can be asserted — on
                entry to every iteration, on either side of the
                connect() outcome, and on every supervising poll while
                connected. Supplied by the caller to report thread
                liveness to a monitor; failures are logged and
                swallowed so that reconnection is never stopped by a
                faulty observer.
        """
        logger = logging.getLogger(self.__class__.__name__)

        def _beat() -> None:
            if heartbeat is None:
                return
            try:
                heartbeat()
            except Exception as e:
                logger.debug("Heartbeat callback failed: %s", e, exc_info=True)

        while not self._shutdown.is_set():
            _beat()
            if self.connect():
                _beat()
                # Supervise the established link. The 1.0 s poll bounds
                # how long after a drop_link the loop notices, and it
                # keeps the 'transport' heartbeat flowing while
                # connected, which the ThreadManager registration
                # requires — without it the thread would look stalled
                # for as long as the link stayed healthy.
                while self.is_connected() and not self._shutdown.is_set():
                    _beat()
                    self._shutdown.wait(1.0)
                if self._shutdown.is_set():
                    return
                # The link dropped. Fall through to the next outer
                # iteration, which retries from connect() — but only
                # after retry_delay. A link that drops immediately on
                # every connect would otherwise spin this loop at full
                # speed; the wait is on _shutdown, so it costs nothing
                # at shutdown.
                logger.info("Link lost - resuming reconnection attempts "
                            "in %.1f seconds", retry_delay)
                self._shutdown.wait(retry_delay)
                continue
            _beat()
            logger.warning("Failed to connect, retrying in %.1f seconds...", retry_delay)
            self._shutdown.wait(retry_delay)


def select_transport(platform_type: PlatformType, args: argparse.Namespace) -> OBDTransport:
    """Factory function to select the appropriate transport based on platform and arguments.
    
    Args:
        platform_type: The platform type (e.g., RASPBERRY_PI).
        args: Command-line arguments namespace.
        
    Returns:
        OBDTransport: An instance of the appropriate transport class.
        
    Raises:
        TransportError: If the platform is unsupported or no paired device is found.
    """
    from .rfcomm import RFCOMMTransport
    from .serial_transport import SerialTransport
    from .tcp_transport import TCPTransport

    transport_arg = getattr(args, 'transport', None)

    # Simulation transports for hardware-free testing. SimTransport
    # serves both simtcp and simbt; they are classified differently for
    # forcing, which is the pairing-simulation design rather than an
    # inconsistency (core review §5.8).
    _simulated = tuple(n for n in TRANSPORT_NAMES if n.startswith('sim'))
    if transport_arg in _simulated:
        from .sim_transport import SimTransport
        return SimTransport()

    if transport_arg == 'tcp':
        host = getattr(args, 'obd_host', 'localhost')
        port = getattr(args, 'obd_port', 35000)
        return TCPTransport(host=host, port=port)
    
    elif transport_arg == 'serial':
        port = getattr(args, 'serial_port', None)
        return SerialTransport(port=port)
    
    elif transport_arg == 'rfcomm':
        return _get_rfcomm()
    
    # Auto-detect based on platform if no transport argument is provided
    if platform_type.name.startswith('RASPBERRY_PI'):
        return _get_rfcomm()
    else:
        raise TransportError('Unsupported platform')


def _get_rfcomm() -> OBDTransport:
    """Helper function to create an RFCOMM transport using the primary device.
    
    Returns:
        RFCOMMTransport: An instance of RFCOMMTransport.
        
    Raises:
        TransportError: If no paired device is found.
    """
    from .rfcomm import RFCOMMTransport
    
    ds = DeviceStore()
    dev = ds.get_primary_device()
    if not dev:
        raise TransportError('No paired device found')
    return RFCOMMTransport(mac_address=dev.mac_address)
