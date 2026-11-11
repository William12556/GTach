#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Communication layer corrections (change-b4f9607a).

One test class per edit group: a connect that completes after
disconnect (A01), refused connects and send-time causes (A03, A04),
OSError on serial (A02), quieter OBD start-up and a non-joining stop
function (A05, B06), discovery wait sizing and hcitool diagnostics
(A06, A07), the discovery fallback, pairing cancellation (X01),
truthful device-store results (A09), the store path (A10), SimTransport
shutdown (A11) and last_connected parsing.
"""

import concurrent.futures
import errno
import logging
import subprocess
import threading
import time
import types
from datetime import datetime
from typing import Any, List, Optional

import pytest

import gtach.comm.obd as obd_module
import gtach.comm.pairing as pairing_module
import gtach.comm.system_bluetooth as system_bluetooth
import gtach.comm.transport as transport_module
from gtach.comm.device_store import (
    DeviceStore,
    get_device_store,
    set_device_store_path,
)
from gtach.comm.models import BluetoothDevice as StoredDevice
from gtach.comm.obd import OBDProtocol
from gtach.comm.pairing import BluetoothPairing
from gtach.comm.serial_transport import SerialTransport
from gtach.comm.sim_transport import SimTransport
from gtach.comm.transport import (
    _CONNECT_FAULT_CAUSES,
    _WEDGED_LINK_CAUSE,
    OBDTransport,
    TransportState,
)
from gtach.core.thread import ThreadManager
from gtach.display.setup_models import BluetoothDevice, DeviceType

JOIN_TIMEOUT = 5.0


# --------------------------------------------------------------------------
# Transport stubs
# --------------------------------------------------------------------------


class _Handle:
    """A handle that records close and can fail its write."""

    def __init__(self, write_error: Optional[BaseException] = None) -> None:
        self.closed = False
        self.write_error = write_error

    def settimeout(self, timeout: float) -> None:
        pass


class _StubTransport(OBDTransport):
    """An OBDTransport whose _open is scripted."""

    _ADAPTER_CHECKS = True

    def __init__(self) -> None:
        super().__init__()
        self.open_results: List[Any] = []
        self.open_entered = threading.Event()
        self.open_release: Optional[threading.Event] = None

    def _open(self) -> Any:
        self.open_entered.set()
        if self.open_release is not None:
            assert self.open_release.wait(JOIN_TIMEOUT)
        result = self.open_results.pop(0)
        if isinstance(result, BaseException):
            raise result
        return result

    def _close(self, handle: _Handle) -> None:
        handle.closed = True

    def _write(self, handle: _Handle, data: bytes) -> None:
        if handle.write_error is not None:
            raise handle.write_error

    def _read(self, handle: _Handle, n: int) -> bytes:
        return b"OK>"

    def _discard_input(self, handle: Any) -> int:
        return 0


class TestConnectAfterDisconnect:
    """A01: a handle that arrives after disconnect() is closed, not kept."""

    def test_disconnect_during_blocking_open(self):
        transport = _StubTransport()
        handle = _Handle()
        transport.open_results = [handle]
        transport.open_release = threading.Event()
        result: List[bool] = []

        worker = threading.Thread(target=lambda: result.append(transport.connect()))
        worker.start()
        assert transport.open_entered.wait(JOIN_TIMEOUT)
        transport.disconnect()
        transport.open_release.set()
        worker.join(JOIN_TIMEOUT)

        assert result == [False]
        assert handle.closed
        assert transport.state == TransportState.DISCONNECTED
        assert not transport.is_connected()
        assert transport._handle is None

    def test_disconnect_before_connect(self):
        transport = _StubTransport()
        handle = _Handle()
        transport.open_results = [handle]
        transport.disconnect()

        assert transport.connect() is False
        assert handle.closed
        assert transport._handle is None

    def test_connect_without_disconnect_keeps_handle(self):
        transport = _StubTransport()
        handle = _Handle()
        transport.open_results = [handle]

        assert transport.connect() is True
        assert not handle.closed
        assert transport.is_connected()


class TestFailureCauses:
    """A03, A04: refused connects and send-time failures."""

    @pytest.fixture(autouse=True)
    def _adapter_present(self, monkeypatch):
        monkeypatch.setattr(
            transport_module, "_bluetooth_adapter_present", lambda: True
        )

    def test_refused_connects_do_not_count_towards_wedge(self):
        transport = _StubTransport()
        refusals = [OSError(errno.ECONNREFUSED, "refused") for _ in range(6)]
        transport.open_results = refusals + [OSError(errno.ETIMEDOUT, "timed out")]

        for _ in range(7):
            assert transport.connect() is False

        cause = transport.last_failure_cause
        assert cause != _WEDGED_LINK_CAUSE
        assert cause == _CONNECT_FAULT_CAUSES[errno.ETIMEDOUT]

    def test_sustained_timeouts_still_report_wedge(self):
        transport = _StubTransport()
        transport.open_results = [
            OSError(errno.ETIMEDOUT, "timed out") for _ in range(6)
        ]

        for _ in range(6):
            transport.connect()

        assert transport.last_failure_cause == _WEDGED_LINK_CAUSE

    def test_send_io_error_records_cause(self):
        transport = _StubTransport()
        transport.open_results = [
            _Handle(write_error=ConnectionResetError(errno.ECONNRESET, "reset"))
        ]
        assert transport.connect() is True

        assert transport.send_command("010C", timeout=0.1) is None
        assert transport.state == TransportState.DISCONNECTED
        assert transport.last_failure_cause


class _FailingPort:
    """A serial port whose in_waiting raises EIO, as on unplug."""

    is_open = True
    timeout = 1.0

    @property
    def in_waiting(self) -> int:
        raise OSError(errno.EIO, "Input/output error")

    def close(self) -> None:
        self.is_open = False


class TestSerialOSError:
    """A02: OSError on a serial port drops the link."""

    def test_oserror_in_io_errors(self):
        assert OSError in SerialTransport._IO_ERRORS

    def test_in_waiting_oserror_drops_link(self, caplog):
        transport = SerialTransport(port="/dev/null-test")
        port = _FailingPort()
        with transport._lock:
            transport._handle = port
            transport._state = TransportState.CONNECTED

        with caplog.at_level(logging.DEBUG):
            assert transport.send_command("010C", timeout=0.1) is None

        assert not transport.is_connected()
        assert transport._handle is None
        assert not port.is_open
        assert not any("Unexpected error" in r.getMessage() for r in caplog.records)


# --------------------------------------------------------------------------
# OBD protocol
# --------------------------------------------------------------------------


class _ScriptedTransport:
    """A connected transport answering 0100 from a script."""

    def __init__(self, replies_0100: List[str]) -> None:
        self.replies_0100 = replies_0100

    def is_connected(self) -> bool:
        return True

    def send_command(self, command: str, timeout: float = 2.0) -> Optional[str]:
        if command == "0100":
            return self.replies_0100.pop(0)
        return "OK"


def _thread_manager_stub() -> Any:
    return types.SimpleNamespace(
        register_thread=lambda *a, **k: None,
        update_heartbeat=lambda name: None,
    )


class TestNoVehicleLogging:
    """A05: a missing 4100 reply is a rate-limited WARNING."""

    def _protocol(self, replies: List[str]) -> OBDProtocol:
        return OBDProtocol(_ScriptedTransport(replies), _thread_manager_stub())

    def test_warning_once_then_info_on_recovery(self, caplog):
        protocol = self._protocol(
            ["NO DATA", "NO DATA", "NO DATA", "41 00 BE 3E B8 11"]
        )
        with caplog.at_level(logging.DEBUG, logger="OBDProtocol"):
            results = [protocol._initialize_protocol() for _ in range(4)]

        assert results == [False, False, False, True]
        records = [r for r in caplog.records if r.name == "OBDProtocol"]
        warnings = [r for r in records if r.levelno == logging.WARNING]
        assert len(warnings) == 1
        assert warnings[0].exc_info is None
        assert not [r for r in records if r.levelno >= logging.ERROR]
        recovered = [r for r in records if "Vehicle answered" in r.getMessage()]
        assert len(recovered) == 1
        assert recovered[0].levelno == logging.INFO

    def test_warning_repeats_after_interval(self, caplog, monkeypatch):
        clock = [1000.0]
        monkeypatch.setattr(
            obd_module,
            "time",
            types.SimpleNamespace(monotonic=lambda: clock[0], sleep=time.sleep),
        )
        protocol = self._protocol(["NO DATA", "NO DATA", "NO DATA"])
        with caplog.at_level(logging.WARNING, logger="OBDProtocol"):
            protocol._initialize_protocol()
            clock[0] += 59.0
            protocol._initialize_protocol()
            clock[0] += 2.0
            protocol._initialize_protocol()

        warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert len(warnings) == 2


class TestNonJoiningStop:
    """B06: stop_thread's timeout bounds the OBD stop."""

    @pytest.fixture
    def manager(self):
        tm = ThreadManager()
        yield tm
        tm.shutdown(timeout=3.0)

    @staticmethod
    def _stubborn_protocol(
        monkeypatch, manager: ThreadManager, seconds: float
    ) -> OBDProtocol:
        def _loop(self: OBDProtocol) -> None:
            time.sleep(seconds)  # ignores shutdown_event

        monkeypatch.setattr(OBDProtocol, "_protocol_loop", _loop)
        return OBDProtocol(_ScriptedTransport([]), manager)

    def test_stop_thread_bounded_by_its_timeout(self, monkeypatch, manager):
        protocol = self._stubborn_protocol(monkeypatch, manager, 2.0)
        protocol.start()

        started = time.monotonic()
        manager.stop_thread("obd_protocol", timeout=0.5)
        elapsed = time.monotonic() - started

        assert protocol.shutdown_event.is_set()
        assert elapsed < 1.5
        protocol.obd_thread.join(JOIN_TIMEOUT)

    def test_direct_stop_still_joins(self, monkeypatch, manager):
        protocol = self._stubborn_protocol(monkeypatch, manager, 0.5)
        protocol.start()

        protocol.stop(timeout=5.0)

        assert not protocol.obd_thread.is_alive()

    def test_stop_zero_signals_only(self, monkeypatch, manager):
        protocol = self._stubborn_protocol(monkeypatch, manager, 0.5)
        protocol.start()

        protocol.stop(timeout=0)

        assert protocol.shutdown_event.is_set()
        assert protocol.obd_thread.is_alive()
        protocol.obd_thread.join(JOIN_TIMEOUT)


# --------------------------------------------------------------------------
# Discovery and pairing
# --------------------------------------------------------------------------


class _BluetoothError(Exception):
    pass


class _Future:
    """A future whose scan 'takes' scan_seconds; the wait is checked, not slept."""

    def __init__(self, result: Any, scan_seconds: float, on_result: Any) -> None:
        self._result = result
        self._scan_seconds = scan_seconds
        self._on_result = on_result

    def result(self, timeout: Optional[float] = None) -> Any:
        if timeout is not None and timeout < self._scan_seconds:
            raise concurrent.futures.TimeoutError()
        if self._on_result is not None:
            self._on_result()
        return self._result


class _Executor:
    """Records each scan submitted and answers from a script."""

    def __init__(self, scans: List[List[tuple]], scan_seconds: float = 0.0) -> None:
        self.scans = scans
        self.scan_seconds = scan_seconds
        self.submitted: List[dict] = []
        self.on_result: Any = None

    def submit(self, fn: Any, **kwargs: Any) -> _Future:
        self.submitted.append(kwargs)
        return _Future(self.scans.pop(0), self.scan_seconds, self.on_result)

    def shutdown(self, wait: bool = True, cancel_futures: bool = False) -> None:
        pass


@pytest.fixture
def pairing(monkeypatch):
    monkeypatch.setattr(
        pairing_module,
        "bluetooth",
        types.SimpleNamespace(
            discover_devices=lambda **k: [],
            BluetoothError=_BluetoothError,
            BluetoothSocket=None,
            RFCOMM="RFCOMM",
        ),
    )
    instance = BluetoothPairing()
    yield instance
    instance.shutdown()


def _install(pairing: BluetoothPairing, executor: _Executor) -> None:
    pairing._executor.shutdown(wait=False)
    pairing._executor = executor


class TestChunkWait:
    """A06: a chunk's wait covers the back end's own limit."""

    def test_slow_scan_results_are_used(self, pairing):
        duration = pairing.DISCOVERY_CHUNK_S
        executor = _Executor(
            [[("00:11:22:33:44:55", "OBDII")]], scan_seconds=duration + 6
        )
        _install(pairing, executor)

        devices = pairing.discover_elm327_devices(timeout=duration)

        assert [d.name for d in devices] == ["OBDII"]
        assert len(executor.submitted) == 1


class TestHcitoolDiagnostics:
    """A07: a failing hcitool is logged; the module reuses one manager."""

    def test_return_code_logged_and_manager_reused(self, monkeypatch, caplog):
        version_calls: List[list] = []

        def _run(args, **kwargs):
            if args[0] == "bluetoothctl":
                version_calls.append(args)
                return subprocess.CompletedProcess(args, 0, "5.66", "")
            return subprocess.CompletedProcess(
                args, 1, "", "Device is not available.\nsecond line\n"
            )

        monkeypatch.setattr(system_bluetooth.subprocess, "run", _run)
        monkeypatch.setattr(system_bluetooth, "_manager", None)

        with caplog.at_level(logging.WARNING, logger="SystemBluetoothManager"):
            first = system_bluetooth.discover_devices(duration=1)
            second = system_bluetooth.discover_devices(duration=1)

        assert first == [] and second == []
        warnings = [r.getMessage() for r in caplog.records]
        assert len(warnings) == 2
        assert "returned 1" in warnings[0]
        assert "Device is not available." in warnings[0]
        assert "second line" not in warnings[0]
        assert len(version_calls) == 1


class TestDiscoveryFallback:
    """EDIT F: named UNKNOWN devices when no ELM327-like device is found."""

    def _discover(self, pairing, scan, executor=None):
        executor = executor or _Executor([scan])
        _install(pairing, executor)
        found: List[BluetoothDevice] = []
        progress: List[float] = []
        devices = pairing.discover_elm327_devices(
            timeout=pairing.DISCOVERY_CHUNK_S,
            progress_callback=progress.append,
            device_found_callback=found.append,
        )
        return devices, found, progress

    def test_fallback_returns_named_unknown_devices(self, pairing, caplog):
        scan = [
            ("AA:00:00:00:00:01", "Phone"),
            ("AA:00:00:00:00:02", "Speaker"),
            ("AA:00:00:00:00:02", "Speaker"),
            ("AA:00:00:00:00:03", ""),
        ]
        with caplog.at_level(logging.INFO, logger="BluetoothPairing"):
            devices, found, progress = self._discover(pairing, scan)

        assert [d.name for d in devices] == ["Phone", "Speaker"]
        assert all(d.device_classification == DeviceType.UNKNOWN for d in devices)
        assert found == devices
        assert progress[-1] == 1.0
        offers = [r for r in caplog.records if "No ELM327-like" in r.getMessage()]
        assert len(offers) == 1

    def test_fallback_not_used_when_elm327_found(self, pairing):
        scan = [("AA:00:00:00:00:01", "OBDII"), ("AA:00:00:00:00:02", "Phone")]
        devices, found, _ = self._discover(pairing, scan)

        assert [d.name for d in devices] == ["OBDII"]
        assert [d.name for d in found] == ["OBDII"]

    def test_empty_scan_returns_empty(self, pairing):
        devices, found, _ = self._discover(pairing, [])

        assert devices == [] and found == []

    def test_no_fallback_after_cancel(self, pairing):
        executor = _Executor([[("AA:00:00:00:00:01", "Phone")]])
        executor.on_result = pairing.cancel_discovery
        devices, found, progress = self._discover(pairing, None, executor)

        assert devices == []
        assert found == []
        assert progress == [0.0]


class _Socket:
    """A Bluetooth socket double recording connect and close."""

    instances: List["_Socket"] = []
    on_connect: Any = None

    def __init__(self, socket_type: str) -> None:
        self.connected = False
        self.closed = False
        _Socket.instances.append(self)

    def settimeout(self, timeout: float) -> None:
        pass

    def connect(self, address_port: tuple) -> None:
        self.connected = True
        if _Socket.on_connect is not None:
            _Socket.on_connect()

    def close(self) -> None:
        self.closed = True


class TestPairingCancellation:
    """X01: pair_device honours cancel_pairing()."""

    @pytest.fixture(autouse=True)
    def _socket(self, pairing):
        _Socket.instances = []
        _Socket.on_connect = None
        pairing_module.bluetooth.BluetoothSocket = _Socket
        yield

    @staticmethod
    def _device() -> BluetoothDevice:
        return BluetoothDevice(
            name="OBDII",
            mac_address="00:11:22:33:44:55",
            signal_strength=-50,
            device_type="ELM327",
            last_seen=datetime.now(),
        )

    def test_cancel_before_connect(self, pairing):
        statuses: List[tuple] = []

        def _status(status, message):
            statuses.append((status, message))
            pairing.cancel_pairing()

        assert pairing.pair_device(self._device(), status_callback=_status) is False
        sock = _Socket.instances[0]
        assert not sock.connected
        assert sock.closed
        assert len(statuses) == 1  # the initial CONNECTING only

    def test_cancel_during_connect(self, pairing, monkeypatch):
        statuses: List[tuple] = []
        _Socket.on_connect = pairing.cancel_pairing
        monkeypatch.setattr(
            pairing,
            "_test_basic_communication",
            lambda sock: pytest.fail("communication test after cancel"),
        )

        result = pairing.pair_device(
            self._device(), status_callback=lambda s, m: statuses.append((s, m))
        )

        assert result is False
        assert _Socket.instances[0].closed
        assert len(statuses) == 1


# --------------------------------------------------------------------------
# Device store
# --------------------------------------------------------------------------


def _stored(prefix: str) -> StoredDevice:
    return StoredDevice(
        name=f"{prefix}-OBD",
        mac_address=f"{prefix}:00:00:00:00:01",
        device_type="ELM327",
    )


class TestStoreResults:
    """A09: a failed save leaves memory unchanged and returns False."""

    @pytest.fixture
    def store(self, tmp_path):
        store = DeviceStore(str(tmp_path / "devices.yaml"))
        assert store.save_device(_stored("AA"))
        assert store.save_device(_stored("BB"), is_primary=False)
        return store

    def test_failed_save_device(self, store, monkeypatch):
        monkeypatch.setattr(store, "_save_config", lambda: False)

        assert store.save_device(_stored("CC")) is False
        assert store.save_device(_stored("DD"), is_primary=False) is False
        assert store.get_primary_device().mac_address == "AA:00:00:00:00:01"
        assert [d.mac_address for d in store.get_all_devices()] == [
            "AA:00:00:00:00:01",
            "BB:00:00:00:00:01",
        ]

    def test_failed_remove_device(self, store, monkeypatch):
        monkeypatch.setattr(store, "_save_config", lambda: False)

        assert store.remove_device("AA:00:00:00:00:01") is False
        assert store.remove_device("BB:00:00:00:00:01") is False
        assert store.get_primary_device().mac_address == "AA:00:00:00:00:01"
        assert store.get_device_by_mac("BB:00:00:00:00:01") is not None

    def test_remove_absent_device(self, store):
        assert store.remove_device("EE:00:00:00:00:01") is False

    def test_successful_remove(self, store):
        assert store.remove_device("AA:00:00:00:00:01") is True
        assert store.get_primary_device() is None


class TestStorePath:
    """A10: set_device_store_path selects the shared store's file."""

    @pytest.fixture(autouse=True)
    def _restore_path(self):
        yield
        set_device_store_path(None)

    def test_path_used_and_default_restored(self, tmp_path, monkeypatch):
        home = tmp_path / "home"
        monkeypatch.setenv("GTACH_HOME", str(home))
        default = home / "config" / "devices.yaml"
        sim_path = tmp_path / "devices-sim.yaml"

        first = get_device_store()
        default_before = default.read_text()
        set_device_store_path(str(sim_path))
        store = get_device_store()

        assert store is not first
        assert store.config_path == str(sim_path)
        assert store.save_device(_stored("AA"))
        assert "AA:00:00:00:00:01" in sim_path.read_text()
        assert default.read_text() == default_before

        set_device_store_path(None)
        assert get_device_store().config_path == str(default)


# --------------------------------------------------------------------------
# Simulation and models
# --------------------------------------------------------------------------


class TestSimTransportShutdown:
    """A11: connect() does not clear the shutdown flag."""

    def test_shutdown_survives_reconnect(self):
        transport = SimTransport()
        transport.disconnect()
        transport.connect()

        assert transport._shutdown.is_set()


class TestLastConnected:
    """last_connected is parsed in from_dict only."""

    def _from(self, value: Any) -> Optional[datetime]:
        data = {"name": "OBDII", "mac_address": "aa:bb:cc:dd:ee:ff"}
        if value is not None:
            data["last_connected"] = value
        return StoredDevice.from_dict(data).last_connected

    def test_iso_string(self):
        assert self._from("2026-11-11T10:30:00") == datetime(2026, 11, 11, 10, 30)

    def test_absent(self):
        assert self._from(None) is None

    def test_invalid_string(self):
        assert self._from("not a date") is None
