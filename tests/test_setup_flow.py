#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Setup flow: one operation rule and presented outcomes (issue-34781bfe).

A completion or task callback acts only while its operation is the
registered one; cancelling removes the registration. Empty, failed and
fallback scans reach DEVICE_LIST. A scan is started once per entry to
DISCOVERY, by the touch action, never by the setup loop.

Uses a stub async manager that never runs anything on its own, a stub
pairing back end and a real SetupStateCoordinator.
"""

import logging
import socket
import threading
import time
import types
from datetime import datetime
from typing import Any, Callable, List, Optional, Tuple

import pygame
import pytest

import gtach.comm.device_store as device_store_module
import gtach.comm.rfcomm as rfcomm_module
import gtach.display.setup as setup_display
from gtach.display.async_operations import (
    AsyncOperationManager,
    OperationStatus,
    OperationType,
)
from gtach.display.setup import SetupDisplayManager
from gtach.display.setup_components.bluetooth import interface as interface_module
from gtach.display.setup_components.bluetooth.interface import (
    DEVICE_DISCOVERY,
    DEVICE_NOT_SAVED_TEXT,
    FALLBACK_LIST_TEXT,
    SCAN_FAILED_TEXT,
    BluetoothSetupInterface,
)
from gtach.display.setup_components.state.coordinator import SetupStateCoordinator
from gtach.display.setup_models import (
    BluetoothDevice,
    DeviceType,
    PairingStatus,
    SetupAction,
    SetupScreen,
)

WAIT_TIMEOUT = 5.0


@pytest.fixture(autouse=True, scope="module")
def _pygame_ready():
    """Off-screen surfaces and fonts; see tests/test_device_list_focus.py."""
    pygame.init()


def _device(
    n: int, classification: DeviceType = DeviceType.HIGHLY_LIKELY_ELM327
) -> BluetoothDevice:
    return BluetoothDevice(
        name=f"OBDII-{n}",
        mac_address=f"00:11:22:33:44:{n:02d}",
        signal_strength=-50,
        device_type="ELM327",
        last_seen=datetime(2026, 1, 1),
        device_classification=classification,
    )


class _StubAsync:
    """Records submissions and cancels; runs nothing on its own."""

    def __init__(self) -> None:
        self.submitted: List[Tuple[OperationType, Callable[..., Any], Any, str]] = []
        self.cancelled: List[str] = []

    def submit_operation(
        self, operation_type, task_func, *args, progress_callback=None, **kwargs
    ) -> str:
        async_id = f"op-{len(self.submitted)}"
        self.submitted.append((operation_type, task_func, progress_callback, async_id))
        return async_id

    def cancel_operation(self, operation_id: str) -> bool:
        self.cancelled.append(operation_id)
        return False

    def get_operation_status(self, operation_id: str) -> None:
        return None

    def of_type(self, operation_type: OperationType) -> List[Tuple[Any, ...]]:
        return [s for s in self.submitted if s[0] == operation_type]

    def last(self, operation_type: OperationType) -> Tuple[Any, ...]:
        return self.of_type(operation_type)[-1]


class _SyncAsync(_StubAsync):
    """Runs the task inside submit_operation: the completion arrives
    before submit_operation has returned its id."""

    def submit_operation(
        self, operation_type, task_func, *args, progress_callback=None, **kwargs
    ) -> str:
        async_id = super().submit_operation(
            operation_type, task_func, progress_callback=progress_callback
        )
        if operation_type is OperationType.BLUETOOTH_INIT:
            return async_id
        try:
            op = _op(OperationStatus.COMPLETED, result=task_func())
        except Exception as e:
            op = _op(OperationStatus.FAILED, error=e)
        if progress_callback:
            progress_callback(op)
        return async_id


class _StubPairing:
    """Back end: counts cancels; discovery and pairing are scripted."""

    def __init__(self) -> None:
        self.cancel_discovery_calls = 0
        self.cancel_pairing_calls = 0
        self.discover_hook: Optional[Callable[..., List[BluetoothDevice]]] = None

    def cancel_discovery(self) -> None:
        self.cancel_discovery_calls += 1

    def cancel_pairing(self) -> None:
        self.cancel_pairing_calls += 1

    def discover_elm327_devices(self, **kwargs: Any) -> List[BluetoothDevice]:
        if self.discover_hook is None:
            return []
        return self.discover_hook(**kwargs)

    def pair_device(self, device, status_callback=None) -> bool:
        return True

    def shutdown(self) -> None:
        pass


class _StubStore:
    def __init__(self, primary: Optional[BluetoothDevice] = None) -> None:
        self.primary = primary
        self.saved: List[Any] = []
        self.save_result = True

    def get_primary_device(self) -> Optional[BluetoothDevice]:
        return self.primary

    def save_device(self, device, is_primary: bool = True) -> bool:
        self.saved.append(device)
        return self.save_result

    def remove_device(self, mac_address: str) -> bool:
        self.primary = None
        return True


def _op(status, result=None, error=None):
    return types.SimpleNamespace(status=status, result=result, error=error)


class _Env:
    """A real SetupDisplayManager on stubs."""

    def __init__(
        self,
        monkeypatch,
        async_manager: Optional[_StubAsync] = None,
        primary: Optional[BluetoothDevice] = None,
        simulation: bool = True,
        surface: Optional[pygame.Surface] = None,
    ) -> None:
        self.async_manager = async_manager or _StubAsync()
        self.store = _StubStore(primary)
        self.pairing = _StubPairing()
        monkeypatch.setattr(
            interface_module, "get_async_manager", lambda: self.async_manager
        )
        monkeypatch.setattr(interface_module, "get_device_store", lambda: self.store)
        monkeypatch.setattr(device_store_module, "get_device_store", lambda: self.store)
        monkeypatch.setattr(BluetoothSetupInterface, "_DISCOVERY_SETTLE_S", 0.0)
        thread_manager = types.SimpleNamespace(
            register_thread=lambda *a, **k: None,
            update_heartbeat=lambda *a, **k: None,
        )
        self.manager = SetupDisplayManager(
            surface,
            thread_manager,  # type: ignore[arg-type]
            None,
            pairing_factory=(lambda: self.pairing) if simulation else None,
        )
        self.iface = self.manager.bluetooth_interface
        self.iface.pairing = self.pairing  # type: ignore[assignment]
        self.iface._pairing_ready.set()
        self.coordinator = self.manager.state_coordinator

    @property
    def state(self):
        return self.coordinator.get_state()

    def tap(self, action: str, *extra: Any):
        return self.manager._handle_touch_action(action, (action, None, *extra))

    def scans(self) -> List[Tuple[Any, ...]]:
        return self.async_manager.of_type(OperationType.DEVICE_DISCOVERY)

    def complete(self, operation_type: OperationType, op, index: int = -1) -> None:
        _, _, callback, _ = self.async_manager.of_type(operation_type)[index]
        callback(op)

    def regions(self) -> List[str]:
        return [r[0] for r in self.manager.touch_regions]

    def render(self) -> pygame.Surface:
        surface = pygame.Surface((480, 480))
        self.manager.render(surface)
        return surface


@pytest.fixture
def env(monkeypatch) -> _Env:
    return _Env(monkeypatch)


class _SpyFont:
    """Delegates to a real font and records the rendered texts."""

    def __init__(self, font, texts: List[str]) -> None:
        self._font = font
        self._texts = texts

    def render(self, text, *args, **kwargs):
        self._texts.append(text)
        return self._font.render(text, *args, **kwargs)

    def size(self, text):
        return self._font.size(text)


@pytest.fixture
def drawn_texts(monkeypatch) -> List[str]:
    texts: List[str] = []
    for name in ("get_body_font", "get_label_small_font"):
        real = getattr(setup_display, name)
        monkeypatch.setattr(
            setup_display, name, lambda real=real: _SpyFont(real(), texts)
        )
    return texts


# ---------------------------------------------------------------------------
# Scan outcomes (EDIT B)
# ---------------------------------------------------------------------------


class TestScanOutcomes:

    def test_two_elm327_devices(self, env):
        env.tap("start")
        env.complete(
            OperationType.DEVICE_DISCOVERY,
            _op(OperationStatus.COMPLETED, result=[_device(1), _device(2)]),
        )

        state = env.state
        assert state.current_screen == SetupScreen.DEVICE_LIST
        assert len(state.discovered_devices) == 2
        assert state.error_message is None
        assert state.pairing_status == PairingStatus.IDLE
        assert not env.iface.has_active_operation(DEVICE_DISCOVERY)

    def test_no_device_reaches_device_list_and_is_not_rescanned(self, env, drawn_texts):
        env.manager.start_setup()
        try:
            env.tap("start")
            env.complete(
                OperationType.DEVICE_DISCOVERY,
                _op(OperationStatus.COMPLETED, result=[]),
            )
            time.sleep(2.0)
        finally:
            env.manager.stop_setup()

        state = env.state
        assert state.current_screen == SetupScreen.DEVICE_LIST
        assert state.discovered_devices == []
        assert state.error_message is None
        env.render()
        assert "No devices found" in drawn_texts
        assert set(env.regions()) == {"back", "retry"}
        assert len(env.scans()) == 1

    def test_failed_scan(self, env, drawn_texts):
        env.manager.start_setup()
        try:
            env.tap("start")
            env.complete(
                OperationType.DEVICE_DISCOVERY,
                _op(OperationStatus.FAILED, error=RuntimeError("no adapter")),
            )
            time.sleep(0.3)
        finally:
            env.manager.stop_setup()

        state = env.state
        assert state.current_screen == SetupScreen.DEVICE_LIST
        assert state.discovered_devices == []
        assert state.error_message == SCAN_FAILED_TEXT
        env.render()
        assert SCAN_FAILED_TEXT in drawn_texts
        assert set(env.regions()) == {"back", "retry"}
        assert len(env.scans()) == 1

    def test_fallback_devices_are_listed_with_notice(self, env):
        devices = [_device(1, DeviceType.UNKNOWN), _device(2, DeviceType.UNKNOWN)]
        env.tap("start")
        env.complete(
            OperationType.DEVICE_DISCOVERY,
            _op(OperationStatus.COMPLETED, result=devices),
        )

        state = env.state
        assert state.current_screen == SetupScreen.DEVICE_LIST
        assert state.discovered_devices == devices
        assert state.error_message == FALLBACK_LIST_TEXT

    def test_mixed_classification_has_no_notice(self, env):
        env.tap("start")
        env.complete(
            OperationType.DEVICE_DISCOVERY,
            _op(
                OperationStatus.COMPLETED,
                result=[_device(1), _device(2, DeviceType.UNKNOWN)],
            ),
        )

        assert env.state.error_message is None


class TestOneScanPerEntry:

    def test_start_setup_submits_one_scan(self, env):
        env.tap("start")

        assert env.state.current_screen == SetupScreen.DISCOVERY
        assert len(env.scans()) == 1

    def test_retry_from_device_list_submits_one_scan(self, env):
        env.tap("start")
        env.complete(
            OperationType.DEVICE_DISCOVERY, _op(OperationStatus.COMPLETED, result=[])
        )
        # A selected device from an earlier pairing must not start pairing.
        env.coordinator.select_device(_device(9))

        env.tap("retry")

        assert env.state.current_screen == SetupScreen.DISCOVERY
        assert len(env.scans()) == 2
        assert env.async_manager.of_type(OperationType.DEVICE_PAIRING) == []

    def test_setup_loop_starts_no_scan(self, env):
        env.coordinator.transition_to_screen(SetupScreen.DISCOVERY)
        env.manager.start_setup()
        env.coordinator.transition_to_screen(SetupScreen.DISCOVERY)
        try:
            time.sleep(0.5)
        finally:
            env.manager.stop_setup()

        assert env.scans() == []
        assert env.state.current_screen == SetupScreen.DISCOVERY


# ---------------------------------------------------------------------------
# Cancellation and the operation rule (EDIT A)
# ---------------------------------------------------------------------------


class TestCancelDiscovery:

    @pytest.mark.parametrize(
        "late",
        [
            _op(OperationStatus.COMPLETED, result=[_device(1)]),
            _op(OperationStatus.FAILED, error=RuntimeError("late")),
        ],
        ids=["devices", "error"],
    )
    def test_abandoned_scan_changes_nothing(self, env, late):
        env.tap("start")
        async_id = env.scans()[0][3]

        env.tap("cancel")
        env.complete(OperationType.DEVICE_DISCOVERY, late)

        state = env.state
        assert env.pairing.cancel_discovery_calls == 1
        assert async_id in env.async_manager.cancelled
        assert state.current_screen == SetupScreen.WELCOME
        assert state.discovered_devices == []
        assert state.error_message is None

    def test_cancel_tapped_twice(self, env):
        env.tap("start")

        env.tap("cancel")
        env.tap("cancel")

        assert env.pairing.cancel_discovery_calls == 1
        assert env.state.current_screen == SetupScreen.WELCOME

    def test_device_found_from_cancelled_scan_is_not_added(self, env):
        def discover(device_found_callback=None, **kwargs):
            device_found_callback(_device(1))
            env.tap("cancel")
            device_found_callback(_device(2))
            return [_device(1), _device(2)]

        env.pairing.discover_hook = discover
        env.tap("start")
        _, task, _, _ = env.scans()[0]

        task()

        assert [d.mac_address for d in env.state.discovered_devices] == []
        assert env.state.current_screen == SetupScreen.WELCOME

    def test_device_found_from_current_scan_is_added(self, env):
        def discover(device_found_callback=None, **kwargs):
            device_found_callback(_device(1))
            return [_device(1)]

        env.pairing.discover_hook = discover
        env.tap("start")
        _, task, _, _ = env.scans()[0]

        task()

        assert env.state.discovered_devices == [_device(1)]

    def test_retry_while_previous_scan_still_runs(self, env):
        env.tap("start")  # scan 0, abandoned below
        env.tap("cancel")
        env.tap("start")  # scan 1
        env.complete(
            OperationType.DEVICE_DISCOVERY,
            _op(OperationStatus.COMPLETED, result=[]),
            index=1,
        )
        env.tap("retry")  # scan 2

        env.complete(
            OperationType.DEVICE_DISCOVERY,
            _op(OperationStatus.COMPLETED, result=[_device(1)]),
            index=0,
        )
        assert env.state.current_screen == SetupScreen.DISCOVERY
        assert env.state.discovered_devices == []

        env.complete(
            OperationType.DEVICE_DISCOVERY,
            _op(OperationStatus.COMPLETED, result=[_device(2), _device(3)]),
            index=2,
        )
        state = env.state
        assert state.current_screen == SetupScreen.DEVICE_LIST
        assert [d.mac_address for d in state.discovered_devices] == [
            _device(2).mac_address,
            _device(3).mac_address,
        ]

    def test_stop_setup_during_scan(self, env):
        env.tap("start")
        _, task, callback, _ = env.scans()[0]
        before = env.state

        env.manager.stop_setup()
        env.pairing.discover_hook = lambda device_found_callback=None, **k: (
            device_found_callback(_device(1)) or [_device(1)]
        )
        callback(_op(OperationStatus.COMPLETED, result=task()))

        after = env.state
        assert after.current_screen == before.current_screen == SetupScreen.DISCOVERY
        assert after.discovered_devices == []
        assert after.error_message is None
        assert after.pairing_status == before.pairing_status

    def test_completion_before_registration_is_stored(self, monkeypatch):
        env = _Env(monkeypatch, async_manager=_SyncAsync())
        env.pairing.discover_hook = lambda **k: [_device(1)]

        env.tap("start")

        state = env.state
        assert state.current_screen == SetupScreen.DEVICE_LIST
        assert state.discovered_devices == [_device(1)]
        assert not env.iface.has_active_operation(DEVICE_DISCOVERY)
        assert DEVICE_DISCOVERY not in env.iface._submitted_ids


class _FailingAsync(_StubAsync):
    def submit_operation(self, operation_type, *args, **kwargs) -> str:
        if operation_type is OperationType.BLUETOOTH_INIT:
            return super().submit_operation(operation_type, *args, **kwargs)
        raise RuntimeError("queue closed")


class TestSubmitFailure:

    def test_scan_not_submitted_shows_scan_failed(self, monkeypatch):
        env = _Env(monkeypatch, async_manager=_FailingAsync())

        env.tap("start")

        state = env.state
        assert state.current_screen == SetupScreen.DEVICE_LIST
        assert state.error_message == SCAN_FAILED_TEXT
        assert not env.iface.has_active_operation(DEVICE_DISCOVERY)

    def test_pairing_not_submitted_shows_failed(self, monkeypatch):
        env = _Env(monkeypatch, async_manager=_FailingAsync())

        env.tap("device", _device(1))

        assert env.state.current_screen == SetupScreen.PAIRING
        assert env.state.pairing_status == PairingStatus.FAILED
        assert "retry" in (env.render() and env.regions())


class TestCancelPairing:

    def _on_pairing(self, env) -> None:
        env.tap("start")
        env.complete(
            OperationType.DEVICE_DISCOVERY,
            _op(OperationStatus.COMPLETED, result=[_device(1)]),
        )
        env.tap("device", _device(1))
        assert env.state.current_screen == SetupScreen.PAIRING

    def test_back_then_successful_completion(self, env):
        self._on_pairing(env)

        env.tap("back")
        env.complete(
            OperationType.DEVICE_PAIRING, _op(OperationStatus.COMPLETED, result=True)
        )

        assert env.pairing.cancel_pairing_calls == 1
        assert env.store.saved == []
        assert env.state.current_screen == SetupScreen.DEVICE_LIST
        assert env.state.setup_complete is False

    def test_status_callback_after_back_writes_nothing(self, env):
        self._on_pairing(env)
        _, task, _, _ = env.async_manager.last(OperationType.DEVICE_PAIRING)

        def pair_device(device, status_callback=None):
            env.tap("back")
            status_callback(PairingStatus.FAILED, "late")
            return False

        env.pairing.pair_device = pair_device  # type: ignore[method-assign]
        task()

        assert env.state.error_message is None
        assert env.state.pairing_status == PairingStatus.IDLE

    def test_save_failure(self, env, monkeypatch):
        verified = []
        monkeypatch.setattr(
            env.iface, "verify_obd_connection", lambda s: verified.append(1) or True
        )
        env.store.save_result = False
        self._on_pairing(env)

        env.complete(
            OperationType.DEVICE_PAIRING, _op(OperationStatus.COMPLETED, result=True)
        )

        state = env.state
        assert state.pairing_status == PairingStatus.FAILED
        assert state.error_message == DEVICE_NOT_SAVED_TEXT
        assert verified == []
        assert state.current_screen == SetupScreen.PAIRING

    def test_successful_pairing_completes(self, env):
        self._on_pairing(env)

        env.complete(
            OperationType.DEVICE_PAIRING, _op(OperationStatus.COMPLETED, result=True)
        )

        assert len(env.store.saved) == 1
        assert env.state.current_screen == SetupScreen.COMPLETE


# ---------------------------------------------------------------------------
# Stored-device probe (EDIT C)
# ---------------------------------------------------------------------------


class TestProbeGuard:

    @pytest.fixture
    def stored(self, monkeypatch) -> _Env:
        env = _Env(monkeypatch, primary=_device(7))
        env.manager.start_setup()
        env.manager.stop_setup()
        assert env.state.current_screen == SetupScreen.CURRENT_DEVICE
        return env

    def test_new_setup_absent_while_probe_runs(self, stored):
        stored.render()
        assert "new_setup" in stored.regions()

        stored.tap("current_continue")
        stored.render()

        assert stored.regions() == ["current_continue"]

    def test_probe_after_new_setup_changes_nothing(self, stored):
        stored.tap("current_continue")
        stored.tap("new_setup")
        assert stored.state.current_screen == SetupScreen.WELCOME
        assert stored.store.primary is None

        stored.complete(
            OperationType.OBD_CONNECTION_TEST,
            _op(OperationStatus.COMPLETED, result=True),
        )

        state = stored.state
        assert state.current_screen == SetupScreen.WELCOME
        assert state.setup_complete is False
        assert state.error_message is None
        assert stored.manager._probe_in_flight is False

    def test_probe_success_completes(self, stored):
        stored.tap("current_continue")
        stored.complete(
            OperationType.OBD_CONNECTION_TEST,
            _op(OperationStatus.COMPLETED, result=True),
        )

        assert stored.state.current_screen == SetupScreen.COMPLETE


# ---------------------------------------------------------------------------
# Screens (EDIT D, EDIT G)
# ---------------------------------------------------------------------------


class TestScreens:

    def test_pairing_success_has_no_continue(self, env):
        env.coordinator.select_device(_device(1))
        env.coordinator.transition_to_screen(SetupScreen.PAIRING)
        env.coordinator.update_state(pairing_status=PairingStatus.SUCCESS)

        env.render()

        assert "continue" not in env.regions()
        assert env.regions() == []

    def test_spinner_fades_without_alpha(self, env, monkeypatch):
        real_circle = pygame.draw.circle
        calls: List[Tuple[Any, Tuple[int, int]]] = []

        def spy(surface, colour, center, *args, **kwargs):
            calls.append((colour, center))
            return real_circle(surface, colour, center, *args, **kwargs)

        monkeypatch.setattr(pygame.draw, "circle", spy)
        surface = pygame.Surface((480, 480))
        assert not surface.get_flags() & pygame.SRCALPHA

        for phase in range(8):
            calls.clear()
            env.coordinator.animation_time = phase * 0.25
            surface.fill(env.manager.colors["background"])
            env.manager._draw_spinner(surface, (240, 220))

            assert len(calls) == 8
            assert all(len(colour) == 3 for colour, _ in calls)
            drawn = {tuple(surface.get_at(center))[:3] for _, center in calls}
            assert len(drawn) >= 3

    def test_render_without_surface(self, monkeypatch):
        env = _Env(monkeypatch, surface=None)

        env.manager.render()

        target = env.render()
        assert target.get_at((240, 20))[:3] == env.manager.colors["background"]

    def test_uncached_screen_draws_on_target(self, env):
        class _NoCopy(pygame.Surface):
            def copy(self):
                raise AssertionError("copied")

        env.coordinator.transition_to_screen(SetupScreen.DISCOVERY)
        target = _NoCopy((480, 480))

        env.manager.render(target)

        assert target.get_at((240, 20))[:3] == env.manager.colors["background"]
        assert "cancel" in env.regions()


# ---------------------------------------------------------------------------
# Coordinator (EDIT A(5))
# ---------------------------------------------------------------------------


class TestDeviceListResetBeforeTransition:

    @pytest.mark.parametrize(
        "start, action",
        [
            (SetupScreen.WELCOME, SetupAction.START_DISCOVERY),
            (SetupScreen.DISCOVERY, SetupAction.CANCEL),
        ],
    )
    def test_list_empty_when_screen_announced(self, start, action):
        coordinator = SetupStateCoordinator()
        coordinator.transition_to_screen(start)
        coordinator.add_discovered_device(_device(1))
        seen: List[int] = []
        coordinator.register_screen_transition_callback(
            lambda old, new: seen.append(
                len(coordinator.get_state().discovered_devices)
            )
        )

        coordinator.handle_setup_action(action)

        assert seen == [0]


# ---------------------------------------------------------------------------
# AsyncOperationManager (EDIT E)
# ---------------------------------------------------------------------------


@pytest.fixture
def manager():
    m = AsyncOperationManager(max_workers=2)
    m.start()
    yield m
    m.stop()


def _wait_until(predicate: Callable[[], bool]) -> bool:
    deadline = time.monotonic() + WAIT_TIMEOUT
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return predicate()


class TestAsyncOperationManager:

    def test_declared_progress_callback_receives_progress(self, manager):
        seen: List[Tuple[OperationStatus, float, Optional[str]]] = []
        done = threading.Event()

        def task(progress_callback=None):
            progress_callback(0.5, "half way")
            return "ok"

        def on_update(op):
            seen.append((op.status, op.progress, op.metadata.get("progress_message")))
            if op.status is OperationStatus.COMPLETED:
                done.set()

        manager.submit_operation(
            OperationType.GENERAL_TASK, task, progress_callback=on_update
        )

        assert done.wait(WAIT_TIMEOUT)
        assert (OperationStatus.RUNNING, 0.5, "half way") in seen

    def test_task_without_parameter_is_called_without_it(self, manager):
        results: List[Any] = []
        done = threading.Event()

        def task():
            progress_callback = None  # a local of that name is not a parameter
            return progress_callback

        def on_update(op):
            results.append((op.status, op.result))
            done.set()

        manager.submit_operation(
            OperationType.GENERAL_TASK, task, progress_callback=on_update
        )

        assert done.wait(WAIT_TIMEOUT)
        assert results == [(OperationStatus.COMPLETED, None)]

    def test_finished_operations_are_not_retained(self, manager):
        finished = []
        lock = threading.Lock()

        def on_update(op):
            if op.status in (OperationStatus.COMPLETED, OperationStatus.FAILED):
                with lock:
                    finished.append(op.id)

        for i in range(10):
            task = (lambda: 1) if i % 2 else (lambda: 1 / 0)
            manager.submit_operation(
                OperationType.GENERAL_TASK, task, progress_callback=on_update
            )

        assert _wait_until(lambda: len(finished) == 10)
        assert _wait_until(
            lambda: not manager.operations and not manager.progress_callbacks
        )

    def test_cancelled_pending_operation_is_dropped(self):
        m = AsyncOperationManager(max_workers=1)
        op_id = m.submit_operation(OperationType.GENERAL_TASK, lambda: 1)
        assert m.cancel_operation(op_id) is True
        m.start()
        try:
            assert _wait_until(lambda: not m.operations)
        finally:
            m.stop()


# ---------------------------------------------------------------------------
# adapter_reset_in_session (EDIT F)
# ---------------------------------------------------------------------------


class _AnsweringTransport:
    """RFCOMM stand-in that connects and answers ATZ."""

    commands: List[str] = []

    def __init__(self, mac_address: str, channel: int = 1) -> None:
        self.last_failure_cause = None

    def connect(self) -> bool:
        return True

    def send_command(self, command: str, timeout: float = 5.0) -> str:
        _AnsweringTransport.commands.append(command)
        return "ELM327 v1.5"

    def disconnect(self) -> None:
        pass


class TestAdapterResetInSession:

    @pytest.fixture
    def real_bt(self, monkeypatch):
        monkeypatch.setattr(socket, "AF_BLUETOOTH", 31, raising=False)
        monkeypatch.setattr(rfcomm_module, "RFCOMMTransport", _AnsweringTransport)
        _AnsweringTransport.commands = []

    def test_false_at_construction(self, env):
        assert env.manager.adapter_reset_in_session is False

    def test_true_after_real_verification(self, monkeypatch, real_bt):
        env = _Env(monkeypatch, primary=_device(1), simulation=False)

        assert env.iface.verify_obd_connection(env.state) is True

        assert _AnsweringTransport.commands == ["ATZ"]
        assert env.manager.adapter_reset_in_session is True

    def test_false_after_simulation_pass_through(self, env):
        assert env.iface.verify_obd_connection(env.state) is True

        assert env.manager.adapter_reset_in_session is False

    def test_false_after_stored_device_probe(self, monkeypatch, real_bt):
        env = _Env(monkeypatch, primary=_device(1), simulation=False)
        results: List[bool] = []
        env.iface.start_device_probe(results.append)
        _, task, callback, _ = env.async_manager.last(OperationType.OBD_CONNECTION_TEST)

        callback(_op(OperationStatus.COMPLETED, result=task()))

        assert results == [True]
        assert _AnsweringTransport.commands == []
        assert env.manager.adapter_reset_in_session is False


def test_logger_is_quiet_for_ignored_completion(env, caplog):
    """An ignored completion is logged at DEBUG only."""
    env.tap("start")
    env.tap("cancel")

    with caplog.at_level(logging.DEBUG):
        env.complete(
            OperationType.DEVICE_DISCOVERY,
            _op(OperationStatus.COMPLETED, result=[_device(1)]),
        )

    ignored = [r for r in caplog.records if "Ignoring" in r.getMessage()]
    assert ignored and all(r.levelno == logging.DEBUG for r in ignored)
    assert not [r for r in caplog.records if r.levelno >= logging.WARNING]
