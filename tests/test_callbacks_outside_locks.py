#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Callbacks run outside locks; the Continue probe is asynchronous.

Covers change-fbe7e98a (audit-36b6ea95 D03, D06, C04, C02, D12). Async
operation callbacks, touch-coordinator button callbacks and touch-interface
callbacks were invoked with the owner's lock held, and the 'current_continue'
action ran a blocking RFCOMM connect on the touch thread. Every callback now
runs after the lock is released, completion handlers ignore progress
updates, and the reachability probe runs on an async worker.
"""

import logging
import socket
import threading
import types

import pygame
import pytest

import gtach.comm.rfcomm as rfcomm_module
from gtach.display.async_operations import (
    AsyncOperationManager,
    OperationStatus,
    OperationType,
)
from gtach.display.input.touch_coordinator import TouchEventCoordinator
from gtach.display.setup import SetupDisplayManager
from gtach.display.setup_components.bluetooth.interface import BluetoothSetupInterface
from gtach.display.setup_models import PairingStatus
from gtach.display.touch_interface import MockTouchInterface, TouchEvent, TouchEventType
from gtach.display.input.interfaces import TouchAction

WAIT_TIMEOUT = 5.0


def _free(lock) -> bool:
    """True if lock is currently free; releases it again if acquired."""
    acquired = lock.acquire(blocking=False)
    if acquired:
        lock.release()
    return acquired


class _CapturingAsyncManager:
    """Records submissions; never runs anything."""

    def __init__(self):
        self.submitted = []

    def submit_operation(self, operation_type, task_func, *args,
                         progress_callback=None, **kwargs):
        self.submitted.append((operation_type, task_func, progress_callback))
        return f'op-{len(self.submitted)}'


class _SyncAsyncManager:
    """Runs the task at once and reports a terminal status."""

    def submit_operation(self, operation_type, task_func, *args,
                         progress_callback=None, **kwargs):
        try:
            op = types.SimpleNamespace(status=OperationStatus.COMPLETED,
                                       result=task_func(*args, **kwargs))
        except Exception as e:
            op = types.SimpleNamespace(status=OperationStatus.FAILED,
                                       result=None, error=e)
        if progress_callback:
            progress_callback(op)
        return 'op-sync'


def _interface(async_manager, pairing_factory=None, device_store=None):
    """A BluetoothSetupInterface without real workers or a device store."""
    iface = object.__new__(BluetoothSetupInterface)
    iface.logger = logging.getLogger('test.callbacks_outside_locks')
    iface.device_store = device_store
    iface.async_manager = async_manager
    iface._pairing_factory = pairing_factory
    iface._state_coordinator = None
    iface.pairing = None
    iface._active_operations = {}
    iface._pairing_ready = threading.Event()
    return iface


class TestAsyncManagerCallbacks:

    @pytest.fixture
    def manager(self):
        mgr = AsyncOperationManager(max_workers=1)
        mgr.start()
        yield mgr
        mgr.stop()

    def test_progress_and_completion_run_unlocked(self, manager):
        calls = []
        finished = threading.Event()

        def task(progress_callback=None):
            progress_callback(0.5)
            return 'ok'

        def callback(operation):
            calls.append(_free(manager._operations_lock))
            if operation.status == OperationStatus.COMPLETED:
                finished.set()

        manager.submit_operation(OperationType.GENERAL_TASK, task,
                                 progress_callback=callback)

        assert finished.wait(WAIT_TIMEOUT)
        assert len(calls) >= 2
        assert all(calls)

    def test_callback_may_query_the_manager(self, manager):
        seen = []
        finished = threading.Event()

        def callback(operation):
            seen.append(manager.get_operation_status(operation.id))
            if operation.status == OperationStatus.COMPLETED:
                finished.set()

        manager.submit_operation(OperationType.GENERAL_TASK, lambda: 'ok',
                                 progress_callback=callback)

        assert finished.wait(WAIT_TIMEOUT)
        assert seen and all(op is not None for op in seen)


class TestCompletionHandlersIgnoreProgress:
    """D12: a RUNNING update is not a terminal outcome."""

    def _running(self):
        return types.SimpleNamespace(status=OperationStatus.RUNNING,
                                     result=object(), error=None)

    def _snapshot(self, iface, state):
        return (state.pairing_status, iface.pairing,
                iface._pairing_ready.is_set(), dict(iface._active_operations))

    def _handlers(self):
        stub = _CapturingAsyncManager()
        iface = _interface(stub)
        state = types.SimpleNamespace(pairing_status=PairingStatus.IDLE,
                                      discovered_devices=[],
                                      discovery_progress=0.0)
        iface._init_bluetooth_pairing_async()
        iface.start_discovery(state)
        device = types.SimpleNamespace(name='dev', mac_address='00:11:22:33:44:55')
        iface.start_pairing(device, state)
        handlers = {op_type: cb for op_type, _, cb in stub.submitted}
        return iface, state, handlers

    @pytest.mark.parametrize('op_type', [
        OperationType.BLUETOOTH_INIT,
        OperationType.DEVICE_DISCOVERY,
        OperationType.DEVICE_PAIRING,
    ])
    def test_running_update_changes_nothing(self, op_type):
        iface, state, handlers = self._handlers()
        before = self._snapshot(iface, state)

        handlers[op_type](self._running())

        assert self._snapshot(iface, state) == before


class TestTouchCoordinatorButtonCallback:

    @pytest.fixture(autouse=True)
    def _pygame(self):
        pygame.init()

    def test_callback_runs_with_coordinator_lock_free(self):
        coordinator = TouchEventCoordinator()
        recorded = []

        def callback(pos):
            def probe():
                acquired = coordinator._lock.acquire(timeout=1)
                if acquired:
                    coordinator._lock.release()
                recorded.append(acquired)
            helper = threading.Thread(target=probe, daemon=True)
            helper.start()
            helper.join(WAIT_TIMEOUT)

        coordinator.register_button_region(
            'b', pygame.Rect(0, 0, 100, 100), TouchAction.BUTTON_PRESS, callback)

        result = coordinator.handle_touch_down((50, 50))

        assert recorded == [True]
        assert result == TouchAction.BUTTON_PRESS

    def test_callback_may_register_regions(self):
        """Edge case: DisplayManager re-registers regions from a callback."""
        coordinator = TouchEventCoordinator()

        def callback(pos):
            coordinator.register_button_region('c', pygame.Rect(200, 200, 10, 10))

        coordinator.register_button_region(
            'b', pygame.Rect(0, 0, 100, 100), TouchAction.BUTTON_PRESS, callback)

        worker = threading.Thread(target=coordinator.handle_touch_down,
                                  args=((50, 50),), daemon=True)
        worker.start()
        worker.join(WAIT_TIMEOUT)

        assert not worker.is_alive()


class TestTouchInterfaceEmit:

    def test_callback_runs_with_interface_lock_free(self):
        iface = MockTouchInterface()
        recorded = []
        iface.register_callback(lambda event: recorded.append(_free(iface._lock)))

        iface._emit_touch_event(TouchEvent(TouchEventType.TOUCH_DOWN, 0.5, 0.5))

        assert recorded == [True]


class TestStartDeviceProbe:

    @pytest.fixture
    def no_transport(self, monkeypatch):
        def _forbidden(*args, **kwargs):
            raise AssertionError('RFCOMMTransport constructed')
        monkeypatch.setattr(rfcomm_module, 'RFCOMMTransport', _forbidden)

    def test_simulation_passes_without_rfcomm(self, no_transport):
        iface = _interface(_SyncAsyncManager(), pairing_factory=object)
        results = []

        iface.start_device_probe(results.append)

        assert results == [True]

    def test_unreachable_device_reports_false(self, monkeypatch):
        if not hasattr(socket, 'AF_BLUETOOTH'):
            monkeypatch.setattr(socket, 'AF_BLUETOOTH', 31, raising=False)
        device = types.SimpleNamespace(mac_address='00:11:22:33:44:55')
        store = types.SimpleNamespace(get_primary_device=lambda: device)
        monkeypatch.setattr(rfcomm_module.RFCOMMTransport, 'connect',
                            lambda self: False)
        iface = _interface(_SyncAsyncManager(), device_store=store)
        results = []

        iface.start_device_probe(results.append)

        assert results == [False]

    def test_progress_update_is_not_reported(self):
        stub = _CapturingAsyncManager()
        iface = _interface(stub, pairing_factory=object)
        results = []

        iface.start_device_probe(results.append)
        _, _, handler = stub.submitted[0]
        handler(types.SimpleNamespace(status=OperationStatus.RUNNING, result=None))

        assert results == []


class TestCurrentContinue:

    def test_one_probe_and_no_action(self):
        manager = object.__new__(SetupDisplayManager)
        manager.logger = logging.getLogger('test.callbacks_outside_locks')
        manager._probe_in_flight = False
        probes = []
        manager.bluetooth_interface = types.SimpleNamespace(
            start_device_probe=lambda on_result: probes.append(on_result))

        first = manager._handle_touch_action('current_continue', ('current_continue',))
        second = manager._handle_touch_action('current_continue', ('current_continue',))

        assert len(probes) == 1
        assert first is None and second is None
