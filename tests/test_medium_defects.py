#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Bounded pairing, coordinated setup state, complete shutdown.

Covers change-d140121d (audit-36b6ea95 A07, A08, A17, C14, D04, D05,
X02). A Bluetooth socket timeout now bounds connect; pairing shutdown
does not wait on running scans; setup state is owned by the coordinator
and readers get copies; _active_operations is locked; shutdown arms the
exit backstop on every path and stops the async workers and the touch
interface.
"""

import datetime
import logging
import socket
import threading
import types

import pytest

import gtach.app as app_module
import gtach.display.async_operations as async_module
from gtach.app import GTachApplication
from gtach.comm.pairing import BluetoothPairing
from gtach.comm.system_bluetooth import BluetoothSocket
from gtach.display.async_operations import OperationStatus, OperationType
from gtach.display.manager import DisplayManager
from gtach.display.setup_components.bluetooth.interface import BluetoothSetupInterface
from gtach.display.setup_components.state.coordinator import SetupStateCoordinator
from gtach.display.setup_models import (
    BluetoothDevice,
    PairingStatus,
    SetupScreen,
    SetupState,
)

JOIN_TIMEOUT = 10.0


def _device(index):
    return BluetoothDevice(
        name=f"dev{index}",
        mac_address=f"00:11:22:33:44:{index:02X}",
        signal_strength=-60,
        device_type="ELM327",
        last_seen=datetime.datetime(2026, 10, 7),
    )


def _state():
    return SetupState(
        current_screen=SetupScreen.DISCOVERY,
        discovered_devices=[],
        selected_device=None,
        pairing_status=PairingStatus.IDLE,
        setup_complete=False,
    )


class TestBluetoothSocketTimeout:

    def test_timeout_applied_before_connect(self, monkeypatch):
        calls = []

        class _Sock:
            def settimeout(self, value):
                calls.append(("settimeout", value))

            def connect(self, address):
                calls.append(("connect", address))

        for name, value in (("AF_BLUETOOTH", 31), ("BTPROTO_RFCOMM", 3)):
            monkeypatch.setattr(socket, name, value, raising=False)
        monkeypatch.setattr(socket, "socket", lambda *a: _Sock())

        sock = BluetoothSocket()
        sock.settimeout(3)
        sock.connect(("00:11:22:33:44:55", 1))

        assert calls == [("settimeout", 3), ("connect", ("00:11:22:33:44:55", 1))]


class TestPairingShutdown:

    def test_does_not_wait(self):
        pairing = object.__new__(BluetoothPairing)
        pairing.logger = logging.getLogger("test.medium")
        pairing._cancel_discovery = threading.Event()
        pairing._cancel_pairing = threading.Event()
        recorded = []
        pairing._executor = types.SimpleNamespace(
            shutdown=lambda **kw: recorded.append(kw)
        )

        pairing.shutdown()

        assert recorded == [{"wait": False, "cancel_futures": True}]
        assert pairing._cancel_discovery.is_set()
        assert pairing._cancel_pairing.is_set()


class TestCoordinatorOwnsState:

    def test_get_state_returns_copies(self):
        coordinator = SetupStateCoordinator()
        first = coordinator.get_state()
        second = coordinator.get_state()

        first.discovered_devices.append(_device(1))
        first.error_message = "x"

        assert coordinator.get_state().discovered_devices == []
        assert coordinator.get_state().error_message is None
        assert first.discovered_devices is not second.discovered_devices

    def test_add_discovered_device_by_mac(self):
        coordinator = SetupStateCoordinator()
        notified = []
        coordinator.register_state_change_callback(notified.append)

        assert coordinator.add_discovered_device(_device(1)) is True
        assert coordinator.add_discovered_device(_device(1)) is False

        assert len(coordinator.get_state().discovered_devices) == 1
        assert notified == [["discovered_devices"]]


class _CapturingAsyncManager:

    def __init__(self):
        self.submitted = {}

    def submit_operation(
        self, operation_type, task_func, *args, progress_callback=None, **kw
    ):
        self.submitted[operation_type] = (task_func, progress_callback)
        return f"op-{operation_type.name}"

    def cancel_operation(self, operation_id):
        return True


def _interface(coordinator=None):
    iface = object.__new__(BluetoothSetupInterface)
    iface.logger = logging.getLogger("test.medium")
    iface.device_store = types.SimpleNamespace(save_device=lambda *a, **k: True)
    iface.async_manager = _CapturingAsyncManager()
    iface._pairing_factory = object
    iface._state_coordinator = coordinator
    iface.pairing = None
    iface._active_operations = {}
    iface._ops_lock = threading.Lock()
    iface._pairing_ready = threading.Event()
    return iface


def _op(status, result=None, error=None):
    return types.SimpleNamespace(status=status, result=result, error=error)


class TestInterfaceWrites:

    def test_handlers_write_through_coordinator(self):
        coordinator = SetupStateCoordinator()
        iface = _interface(coordinator)
        passed = coordinator.get_state()

        iface.start_discovery(passed)
        _, on_discovery = iface.async_manager.submitted[OperationType.DEVICE_DISCOVERY]
        on_discovery(_op(OperationStatus.COMPLETED, result=[_device(1)]))

        assert [d.mac_address for d in coordinator.get_state().discovered_devices] == [
            "00:11:22:33:44:01"
        ]

        iface.start_pairing(_device(1), passed)
        _, on_pairing = iface.async_manager.submitted[OperationType.DEVICE_PAIRING]
        on_pairing(_op(OperationStatus.FAILED, error=RuntimeError("refused")))

        state = coordinator.get_state()
        assert state.pairing_status == PairingStatus.FAILED
        assert state.error_message == "refused"
        # The copy handed to the interface is not where writes land.
        assert passed.discovered_devices == []
        assert passed.error_message is None

    def test_fallback_without_coordinator(self):
        iface = _interface()
        passed = _state()

        iface.start_discovery(passed)
        _, on_discovery = iface.async_manager.submitted[OperationType.DEVICE_DISCOVERY]
        on_discovery(_op(OperationStatus.COMPLETED, result=[]))

        assert passed.pairing_status == PairingStatus.IDLE
        assert passed.error_message.startswith("No devices found.")
        assert iface._add_device(passed, _device(2)) is True
        assert iface._add_device(passed, _device(2)) is False


class TestActiveOperationsLocked:

    def test_concurrent_readers_and_writer(self):
        iface = _interface()
        errors = []
        stop = threading.Event()

        def writer():
            try:
                for i in range(1000):
                    with iface._ops_lock:
                        iface._active_operations[f"op{i % 7}"] = str(i)
                    with iface._ops_lock:
                        iface._active_operations.pop(f"op{(i + 3) % 7}", None)
                    if i % 250 == 0:
                        iface.cancel_operations()
            except Exception as e:  # pragma: no cover - failure path
                errors.append(e)
            finally:
                stop.set()

        def reader():
            try:
                while not stop.is_set():
                    iface.has_active_operation("op1")
                    iface.get_active_operation_progress()
            except Exception as e:  # pragma: no cover - failure path
                errors.append(e)

        iface.async_manager.get_operation_status = lambda op_id: None
        threads = [
            threading.Thread(target=f, daemon=True) for f in (writer, reader, reader)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(JOIN_TIMEOUT)

        assert all(not t.is_alive() for t in threads)
        assert errors == []


class TestShutdown:

    def _app(self, calls, monkeypatch):
        app = object.__new__(GTachApplication)
        app.logger = logging.getLogger("test.medium")
        rec = lambda name: (lambda *a, **k: calls.append(name))
        app._arm_exit_backstop = rec("backstop")
        app._watchdog = types.SimpleNamespace(stop=rec("watchdog"))
        app._setup_manager = types.SimpleNamespace(stop_setup=rec("setup"))
        app._display = types.SimpleNamespace(stop=rec("display"))
        app._transport = types.SimpleNamespace(disconnect=rec("transport"))
        app._obd = types.SimpleNamespace(stop=rec("obd"))
        app._thread_manager = types.SimpleNamespace(shutdown=rec("thread_manager"))
        monkeypatch.setattr(async_module, "shutdown_async_manager", rec("async"))
        return app

    def test_order(self, monkeypatch):
        calls = []
        app = self._app(calls, monkeypatch)

        app.shutdown()

        assert calls == [
            "backstop",
            "watchdog",
            "setup",
            "async",
            "display",
            "transport",
            "obd",
            "thread_manager",
        ]

    def test_backstop_armed_once(self, monkeypatch):
        timers = []

        class _Timer:
            def __init__(self, interval, function):
                timers.append(interval)
                self.daemon = False

            def start(self):
                pass

        monkeypatch.setattr(app_module.threading, "Timer", _Timer)
        app = object.__new__(GTachApplication)
        app.logger = logging.getLogger("test.medium")
        app._stop_event = threading.Event()
        app._backstop_armed = False

        app._watchdog_shutdown()
        app.shutdown()
        app.shutdown()

        assert timers == [GTachApplication._EXIT_BACKSTOP_SEC]


class TestDisplayManagerStop:

    def test_stops_touch_handler(self):
        stops = []
        done = threading.Thread(target=lambda: None)
        done.start()
        done.join()
        host = types.SimpleNamespace(
            _shutdown_event=threading.Event(),
            display_thread=done,
            logger=logging.getLogger("test.medium"),
            performance_monitor=types.SimpleNamespace(stop_monitoring=lambda: None),
            rendering_engine=types.SimpleNamespace(cleanup=lambda: None),
            touch_handler=types.SimpleNamespace(stop=lambda: stops.append(1)),
        )

        DisplayManager.stop(host)

        assert stops == [1]
