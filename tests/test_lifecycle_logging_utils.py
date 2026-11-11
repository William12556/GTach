#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Application lifecycle, logging and utility corrections (change-042dd7ff)."""

import importlib
import importlib.resources
import io
import logging
import os
import subprocess
import sys
import threading
import types
from pathlib import Path

import pytest
import yaml

import gtach.app as app_module
from gtach.app import EXIT_FAILURE, EXIT_OK, GTachApplication
from gtach.comm import device_store
from gtach.comm.transport import TransportError
from gtach.core import watchdog as watchdog_module
from gtach.core.thread import ThreadManager
from gtach.core.watchdog import WatchdogMonitor
from gtach.utils import config as config_module
from gtach.utils import pi_reset
from gtach.utils import terminal as terminal_module
from gtach.utils.ack_state import AcknowledgementStateManager
from gtach.utils.config import AppConfig, ConfigStore, load_engine_profile
from gtach.utils.dependencies import DependencyValidator
from gtach.utils.terminal import TerminalRestorer

# The module object, not a re-exported function (issue-c1d4b8e6).
gtach_main = importlib.import_module("gtach.main")

REPO_SRC = Path(__file__).resolve().parent.parent / "src"


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def _bare_app():
    """A GTachApplication with no constructor side effects."""
    app = object.__new__(GTachApplication)
    app.logger = logging.getLogger("test.app")
    app._stop_event = threading.Event()
    app._obd_lock = threading.Lock()
    app._exit_status = EXIT_OK
    # A backstop timer must never reach os._exit inside the test process.
    app._backstop_armed = True
    return app


class _FakeSetupManager:
    instances = []

    def __init__(self, *args, pairing_factory=None, on_complete=None):
        self.pairing_factory = pairing_factory
        _FakeSetupManager.instances.append(self)

    def start_setup(self):
        pass

    def stop_setup(self):
        pass


@pytest.fixture
def restore_root_logger():
    root = logging.getLogger()
    before = list(root.handlers)
    level = root.level
    yield root
    for handler in list(root.handlers):
        if handler not in before:
            root.removeHandler(handler)
            try:
                handler.close()
            except Exception:
                pass
    root.setLevel(level)


# --------------------------------------------------------------------------
# EDIT A — app.py lifecycle
# --------------------------------------------------------------------------


class TestReEnterSetupKeepsFactory:

    def test_second_start_receives_same_factory(self, monkeypatch):
        _FakeSetupManager.instances = []
        monkeypatch.setattr(app_module, "SetupDisplayManager", _FakeSetupManager)
        app = _bare_app()
        app._watchdog = types.SimpleNamespace(
            _thread=types.SimpleNamespace(is_alive=lambda: True)
        )
        app._display = types.SimpleNamespace(
            rendering_engine=types.SimpleNamespace(main_surface=object()),
            touch_handler=object(),
            set_setup_mode=lambda manager: None,
        )
        app._thread_manager = types.SimpleNamespace(
            stop_thread=lambda name, timeout: True
        )

        def factory():
            return object()

        app._start_setup_mode(pairing_factory=factory)
        app._re_enter_setup()

        assert len(_FakeSetupManager.instances) == 2
        assert _FakeSetupManager.instances[1].pairing_factory is factory


class TestSimulatedDeviceStore:

    @pytest.fixture
    def construct(self, tmp_path, monkeypatch):
        monkeypatch.setenv("GTACH_HOME", str(tmp_path))
        monkeypatch.setattr("gtach.app.atexit.register", lambda *a, **k: None)
        monkeypatch.setattr("gtach.app.signal.signal", lambda *a, **k: None)
        monkeypatch.setattr("gtach.app.TerminalRestorer", lambda *a, **k: object())
        device_store.set_device_store_path(None)
        yield lambda transport: GTachApplication(
            debug=False, args=types.SimpleNamespace(transport=transport)
        )
        device_store.set_device_store_path(None)

    def test_simbt_uses_sim_file(self, construct):
        construct("simbt")
        path = device_store.get_device_store().config_path
        assert path.endswith(os.path.join("config", "devices-sim.yaml"))

    def test_other_transport_uses_default_file(self, construct):
        construct("tcp")
        path = device_store.get_device_store().config_path
        assert path.endswith(os.path.join("config", "devices.yaml"))


class TestAdapterPreInitialised:

    @pytest.fixture
    def captured(self, monkeypatch):
        kwargs = {}

        class _FakeOBD:
            def __init__(self, *args, **kw):
                kwargs.update(kw)

            def start(self):
                pass

        transport = types.SimpleNamespace(
            reconnect_indefinitely=lambda **kw: None,
            retry_delay=1.0,
            disconnect=lambda: None,
        )
        monkeypatch.setattr(app_module, "get_platform_type", lambda: None)
        monkeypatch.setattr(app_module, "select_transport", lambda *a: transport)
        monkeypatch.setattr(app_module, "OBDProtocol", _FakeOBD)
        return kwargs

    def _start(self, manager):
        app = _bare_app()
        app._args = types.SimpleNamespace(transport="tcp")
        app._thread_manager = types.SimpleNamespace(
            register_thread=lambda *a, **k: None, update_heartbeat=lambda n: None
        )
        if manager is not None:
            app._setup_manager = manager
        app._start_obd()

    def test_no_setup_manager(self, captured):
        self._start(None)
        assert captured["adapter_pre_initialised"] is False

    def test_manager_without_attribute(self, captured):
        self._start(types.SimpleNamespace())
        assert captured["adapter_pre_initialised"] is False

    def test_manager_reset_in_session(self, captured):
        self._start(types.SimpleNamespace(adapter_reset_in_session=True))
        assert captured["adapter_pre_initialised"] is True


class TestSetupCompleteStartFailure:

    def test_flag_cleared_and_retry_runs(self):
        app = _bare_app()
        app._display = types.SimpleNamespace(exit_setup_mode=lambda: None)
        calls = []

        def failing_start():
            calls.append(1)
            raise TransportError("no link")

        app._start_obd = failing_start

        app._on_setup_complete()
        assert app._obd_started is False

        app._on_setup_complete()
        assert len(calls) == 2


class TestExitStatus:

    def _run(self, monkeypatch, start):
        app = _bare_app()
        monkeypatch.setattr(app, "start", lambda: start(app))
        monkeypatch.setattr(app, "shutdown", lambda: None)
        return app.run()

    def test_startup_failure(self, monkeypatch):
        def start(app):
            raise RuntimeError("startup failed")

        assert self._run(monkeypatch, start) == EXIT_FAILURE

    def test_signal(self, monkeypatch):
        def start(app):
            app._signal_handler(15, None)

        assert self._run(monkeypatch, start) == EXIT_OK

    def test_watchdog_exit(self, monkeypatch):
        def start(app):
            app._watchdog_shutdown()

        assert self._run(monkeypatch, start) == EXIT_FAILURE

    def test_requested_restart(self, monkeypatch):
        def start(app):
            app._request_restart()

        assert self._run(monkeypatch, start) == EXIT_OK

    def test_main_returns_run_status(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["gtach"])
        monkeypatch.setattr(gtach_main, "setup_logging", lambda debug: None)
        monkeypatch.setattr("gtach.utils.stack_dump.install", lambda getter: True)

        class _FakeApp:
            def __init__(self, *args):
                pass

            def run(self):
                return EXIT_FAILURE

        monkeypatch.setattr(app_module, "GTachApplication", _FakeApp)
        assert gtach_main.main() == EXIT_FAILURE


class TestShutdownSteps:

    def test_steps_isolated_and_ordered(self, monkeypatch):
        monkeypatch.setattr(
            "gtach.display.async_operations.shutdown_async_manager", lambda: None
        )
        order = []

        def stub(name, method, fail=False):
            def call():
                order.append(name)
                if fail:
                    raise RuntimeError(name)

            return types.SimpleNamespace(**{method: call})

        app = _bare_app()
        app._watchdog = stub("watchdog", "stop")
        app._setup_manager = stub("setup", "stop_setup", fail=True)
        app._display = stub("display", "stop")
        app._transport = stub("transport", "disconnect")
        app._obd = stub("obd", "stop")
        app._thread_manager = stub("thread_manager", "shutdown")

        app.shutdown()
        app.shutdown()

        assert order == [
            "watchdog",
            "setup",
            "display",
            "transport",
            "obd",
            "thread_manager",
        ]


# --------------------------------------------------------------------------
# EDIT B — main.py logging
# --------------------------------------------------------------------------


class TestRuntimeLogLevel:

    def test_follows_debug_switch(self, restore_root_logger):
        probe = logging.getLogger("test.probe")

        gtach_main.set_runtime_log_level(False)
        assert restore_root_logger.level == logging.WARNING
        assert probe.isEnabledFor(logging.DEBUG) is False

        gtach_main.set_runtime_log_level(True)
        assert restore_root_logger.level == logging.DEBUG
        assert probe.isEnabledFor(logging.DEBUG) is True

    def test_toggle_sets_root_level(self, restore_root_logger, monkeypatch):
        monkeypatch.setattr(sys, "platform", "linux")
        handler = logging.NullHandler()
        monkeypatch.setattr(gtach_main, "_debug_handler", handler)
        monkeypatch.setattr(gtach_main, "enable_stack_dumps", lambda: True)
        monkeypatch.setattr(gtach_main, "disable_stack_dumps", lambda: None)
        app = _bare_app()

        app.toggle_debug_logging(True)
        assert restore_root_logger.level == logging.DEBUG

        app.toggle_debug_logging(False)
        assert restore_root_logger.level == logging.WARNING

    def test_finish_startup_lowers_root(self, restore_root_logger, monkeypatch):
        monkeypatch.setattr(sys, "platform", "linux")
        handler = logging.NullHandler()
        handler.setLevel(logging.CRITICAL + 1)
        monkeypatch.setattr(gtach_main, "_debug_handler", handler)
        monkeypatch.setattr(gtach_main, "_start_handler", logging.NullHandler())
        restore_root_logger.setLevel(logging.DEBUG)

        _bare_app()._finish_startup_logging()

        assert restore_root_logger.level == logging.WARNING


class TestValidateConfigOpensNoLog:

    def _run(self, home, *args):
        env = dict(os.environ, GTACH_HOME=str(home))
        env["PYTHONPATH"] = os.pathsep.join([str(REPO_SRC), env.get("PYTHONPATH", "")])
        return subprocess.run(
            [sys.executable, "-m", "gtach", *args],
            env=env,
            cwd=home,
            capture_output=True,
            timeout=60,
        )

    def test_valid_config(self, tmp_path):
        start_log = tmp_path / "start.log"
        start_log.write_text("known content\n", encoding="utf-8")

        result = self._run(tmp_path, "--validate-config")

        assert result.returncode == 0, result.stderr
        assert start_log.read_text(encoding="utf-8") == "known content\n"
        assert not (tmp_path / "debug.log").exists()
        assert not (tmp_path / "error.log").exists()

    def test_invalid_config(self, tmp_path):
        (tmp_path / "config.yaml").write_text("fps_limit: 0\n", encoding="utf-8")
        start_log = tmp_path / "start.log"
        start_log.write_text("known content\n", encoding="utf-8")

        result = self._run(tmp_path, "--validate-config")

        assert result.returncode == 1
        assert start_log.read_text(encoding="utf-8") == "known content\n"
        assert not (tmp_path / "debug.log").exists()


class TestLogPathsUnderHome:

    def test_handlers_under_home(self, tmp_path, monkeypatch, restore_root_logger):
        monkeypatch.setenv("GTACH_HOME", str(tmp_path))
        for name in (
            "_START_LOG",
            "_DEBUG_LOG",
            "_ERROR_LOG",
            "_STACKS_LOG",
            "_start_handler",
            "_debug_handler",
            "_error_handler",
        ):
            monkeypatch.setattr(gtach_main, name, getattr(gtach_main, name))

        gtach_main.setup_logging(debug=False)

        for handler in (
            gtach_main._start_handler,
            gtach_main._debug_handler,
            gtach_main._error_handler,
        ):
            assert handler is not None
            assert Path(handler.baseFilename).parent == tmp_path
        assert Path(gtach_main._STACKS_LOG).parent == tmp_path

    def test_default_home_paths(self):
        assert gtach_main._START_LOG == "/opt/gtach/start.log"
        assert gtach_main._DEBUG_LOG == "/opt/gtach/debug.log"
        assert gtach_main._ERROR_LOG == "/opt/gtach/error.log"


# --------------------------------------------------------------------------
# EDIT C — watchdog
# --------------------------------------------------------------------------


class TestNonCriticalStall:

    def test_one_warning_no_emergency(self, monkeypatch, caplog):
        clock = [1000.0]
        monkeypatch.setattr(
            watchdog_module,
            "time",
            types.SimpleNamespace(monotonic=lambda: clock[0], sleep=lambda s: None),
        )
        manager = ThreadManager()
        monitor = WatchdogMonitor(manager, shutdown_callback=lambda: None)
        manager.register_thread("worker", threading.Thread(target=lambda: None))
        manager.threads["worker"].last_heartbeat = clock[0] - (
            monitor.critical_timeout + 5
        )

        with caplog.at_level(logging.WARNING, logger="WatchdogMonitor"):
            for _ in range(6):
                monitor._check_thread_health()
                clock[0] += 5.0

        warnings = [
            r
            for r in caplog.records
            if r.levelno == logging.WARNING and "worker" in r.getMessage()
        ]
        assert len(warnings) == 1
        assert not any(
            r.levelno >= logging.ERROR and "emergency" in r.getMessage()
            for r in caplog.records
        )

    def test_repeats_after_interval(self, monkeypatch, caplog):
        clock = [1000.0]
        monkeypatch.setattr(
            watchdog_module,
            "time",
            types.SimpleNamespace(monotonic=lambda: clock[0], sleep=lambda s: None),
        )
        monitor = WatchdogMonitor(ThreadManager(), shutdown_callback=lambda: None)
        health = watchdog_module.ThreadHealth(name="worker")

        with caplog.at_level(logging.WARNING, logger="WatchdogMonitor"):
            monitor._handle_critical_timeout("worker", health, 50.0)
            clock[0] += watchdog_module.NON_CRITICAL_WARNING_INTERVAL_S
            monitor._handle_critical_timeout("worker", health, 110.0)

        assert len(caplog.records) == 2


# --------------------------------------------------------------------------
# EDIT D — utils
# --------------------------------------------------------------------------


class TestConfigTypeRule:

    def test_load_and_validate_agree(self, tmp_path, caplog):
        path = tmp_path / "config.yaml"
        path.write_text(
            yaml.safe_dump(
                {"palette": None, "touch_long_press": True, "fps_limit": 30.9}
            ),
            encoding="utf-8",
        )
        store = ConfigStore(path)

        with caplog.at_level(logging.WARNING):
            config = store.load()

        warned = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert len(warned) == 3
        assert config == AppConfig()
        errors = store.validate()
        assert len(errors) == 3
        for key in ("palette", "touch_long_press", "fps_limit"):
            assert any(e.startswith(key) for e in errors)

    def test_integral_float_accepted_for_int(self, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text("fps_limit: 30.0\n", encoding="utf-8")
        store = ConfigStore(path)
        assert store.load().fps_limit == 30
        assert store.validate() == []


class TestConfigSaveSerialised:

    def test_concurrent_saves(self, tmp_path):
        store = ConfigStore(tmp_path / "config.yaml")
        results = []
        parse_errors = []

        def worker(fps):
            for _ in range(200):
                results.append(store.save(AppConfig(fps_limit=fps)))
                try:
                    data = yaml.safe_load(store.path.read_text(encoding="utf-8"))
                    assert isinstance(data, dict)
                except Exception as e:  # pragma: no cover - failure path
                    parse_errors.append(e)

        threads = [threading.Thread(target=worker, args=(f,)) for f in (20, 40)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(60)

        assert len(results) == 400
        assert all(results)
        assert parse_errors == []


class TestEngineProfile:

    def test_no_failure_record(self, caplog):
        with caplog.at_level(logging.DEBUG):
            bands = load_engine_profile()

        assert not any(
            "failed" in r.getMessage()
            for r in caplog.records
            if r.name.startswith("gtach.utils.config")
        )
        assert bands.redline_rpm == 6500

    def test_assets_namespace_not_used(self, monkeypatch, caplog):
        """files('gtach.assets') raises on Python 3.9; it must not be needed."""
        real_files = importlib.resources.files

        def files(package):
            if package == "gtach.assets":
                raise TypeError("namespace package")
            return real_files(package)

        monkeypatch.setattr(config_module.importlib.resources, "files", files)
        with caplog.at_level(logging.DEBUG):
            bands = load_engine_profile()

        assert not any(
            "failed" in r.getMessage()
            for r in caplog.records
            if r.name.startswith("gtach.utils.config")
        )
        assert bands.redline_rpm == 6500


class TestDependencyFindSpec:

    def test_absent_dotted_module_does_not_raise(self, monkeypatch):
        monkeypatch.setitem(sys.modules, "RPi", None)
        validator = DependencyValidator(debug=True)

        available, version, error = validator._check_import("RPi.GPIO")

        assert available is False


class TestTerminalRestorer:

    @pytest.fixture(autouse=True)
    def _no_atexit(self, monkeypatch):
        monkeypatch.setattr(terminal_module.atexit, "register", lambda f: None)

    def test_stdin_none(self, monkeypatch):
        monkeypatch.setattr(sys, "stdin", None)
        assert TerminalRestorer().original_termios is None

    def test_stdin_closed(self, monkeypatch):
        closed = io.StringIO()
        closed.close()
        monkeypatch.setattr(sys, "stdin", closed)
        assert TerminalRestorer().original_termios is None


class TestResetOutcome:

    @pytest.mark.parametrize(
        "code, outcome",
        [
            (0, "reboot initiated"),
            (1, "reboot command failed"),
            (-15, "reboot initiated"),
        ],
    )
    def test_return_codes(self, code, outcome, monkeypatch, caplog):
        monkeypatch.setattr(pi_reset.os.path, "exists", lambda p: True)
        monkeypatch.setattr(
            pi_reset.subprocess,
            "run",
            lambda *a, **k: subprocess.CompletedProcess(
                a[0], code, stdout=b"", stderr=b"first line\nsecond\n"
            ),
        )

        with caplog.at_level(logging.WARNING, logger=pi_reset.__name__):
            assert pi_reset.reboot_device() == outcome

        warnings = [r.getMessage() for r in caplog.records]
        if code == 0:
            assert warnings == []
        else:
            assert len(warnings) == 1
            assert str(code) in warnings[0]
            assert "first line" in warnings[0]


class TestStateInfo:

    def test_list_gives_none(self, tmp_path):
        path = tmp_path / "ack_state.yaml"
        path.write_text("- a\n- b\n", encoding="utf-8")
        assert AcknowledgementStateManager(path).get_state_info() is None

    def test_mapping_returned(self, tmp_path):
        path = tmp_path / "ack_state.yaml"
        path.write_text("key: value\n", encoding="utf-8")
        assert AcknowledgementStateManager(path).get_state_info() == {"key": "value"}
