#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Arming and disarming all-thread stack dumps.

Covers change-2ac1c602 iteration 2: /opt/gtach/stacks.log must be armed
from the runtime OPTIONS debug toggle, not only from the --debug startup
flag that bin/gtach.service never passes. The arming helpers must be
idempotent in both directions, and a failure in the stack-dump path must
never prevent the debug log handler from being toggled.

The faulthandler module is replaced throughout by a recording double.
Arming the real one would start a 15 s repeating timer writing into the
test process for the remainder of the run, and the teardown ORDER that
disable_stack_dumps must observe is only assertable against a recorder.
"""

import logging
import sys
import types

import pytest

import gtach.main  # noqa: F401  — ensures the module is in sys.modules
from gtach.app import GTachApplication

# gtach/__init__.py re-exports the main FUNCTION under the name 'main',
# so `from gtach import main` retrieves the function and not the module
# — whose namespace has no _stacks_file or _STACKS_LOG. The module is
# retrievable from sys.modules, keyed by the full dotted name. This is
# the same trap issue-c1d4b8e6 documents in
# GTachApplication.toggle_debug_logging, and the reason that method
# reaches for sys.modules rather than importing.
gtach_main = sys.modules['gtach.main']


class _FakeFaulthandler:
    """Records calls in order; performs no real arming."""

    def __init__(self):
        self.calls = []
        self.enabled_files = []
        self.dump_args = []

    def enable(self, file=None):
        self.calls.append('enable')
        self.enabled_files.append(file)

    def disable(self):
        self.calls.append('disable')

    def dump_traceback_later(self, timeout, repeat=False, file=None):
        self.calls.append('dump_traceback_later')
        self.dump_args.append((timeout, repeat, file))

    def cancel_dump_traceback_later(self):
        self.calls.append('cancel_dump_traceback_later')


@pytest.fixture
def fh(monkeypatch):
    """Install the recording double and guarantee a disarmed module.

    _stacks_file is module-level state, so it is reset on the way out
    whatever the test did with it; otherwise one test's armed handle
    leaks into the next.
    """
    fake = _FakeFaulthandler()
    monkeypatch.setattr(gtach_main, 'faulthandler', fake)
    monkeypatch.setattr(gtach_main, '_stacks_file', None)
    yield fake
    stacks = gtach_main._stacks_file
    if stacks is not None:
        try:
            stacks.close()
        except Exception:
            pass
    gtach_main._stacks_file = None


@pytest.fixture
def stacks_path(tmp_path, monkeypatch):
    """Point _STACKS_LOG at a writable temporary file."""
    path = tmp_path / 'stacks.log'
    monkeypatch.setattr(gtach_main, '_STACKS_LOG', str(path))
    return path


class TestEnableStackDumps:
    """enable_stack_dumps — idempotent arming."""

    def test_arms_once(self, fh, stacks_path):
        assert gtach_main.enable_stack_dumps() is True
        assert stacks_path.exists()
        assert gtach_main._stacks_file is not None
        assert fh.calls == ['enable', 'dump_traceback_later']

    def test_dump_interval_is_fifteen_seconds_repeating(self, fh, stacks_path):
        gtach_main.enable_stack_dumps()
        timeout, repeat, target = fh.dump_args[0]
        assert timeout == 15
        assert repeat is True
        assert target is gtach_main._stacks_file

    def test_second_call_opens_no_second_handle(self, fh, stacks_path):
        assert gtach_main.enable_stack_dumps() is True
        first = gtach_main._stacks_file

        assert gtach_main.enable_stack_dumps() is True

        assert gtach_main._stacks_file is first
        # No second arming of either faulthandler entry point.
        assert fh.calls == ['enable', 'dump_traceback_later']

    def test_unwritable_path_returns_false(self, fh, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr(
            gtach_main, '_STACKS_LOG', str(tmp_path / 'no' / 'such' / 'dir' / 's.log')
        )

        assert gtach_main.enable_stack_dumps() is False
        assert gtach_main._stacks_file is None
        assert fh.calls == []
        assert 'WARNING' in capsys.readouterr().err


class TestDisableStackDumps:
    """disable_stack_dumps — order-sensitive teardown, no-op when idle."""

    def test_closes_file_and_clears_state(self, fh, stacks_path):
        gtach_main.enable_stack_dumps()
        handle = gtach_main._stacks_file

        gtach_main.disable_stack_dumps()

        assert gtach_main._stacks_file is None
        assert handle.closed is True

    def test_cancels_before_closing(self, fh, stacks_path):
        """A dump firing against a closed descriptor would fault."""
        gtach_main.enable_stack_dumps()
        handle = gtach_main._stacks_file

        closed_at = []
        original_close = handle.close

        def _tracking_close():
            closed_at.append(len(fh.calls))
            original_close()

        handle.close = _tracking_close
        gtach_main.disable_stack_dumps()

        cancel_index = fh.calls.index('cancel_dump_traceback_later')
        disable_index = fh.calls.index('disable')
        assert cancel_index < disable_index
        assert closed_at[0] > disable_index

    def test_no_op_when_not_armed(self, fh):
        gtach_main.disable_stack_dumps()

        assert gtach_main._stacks_file is None
        assert fh.calls == []

    def test_close_failure_still_clears_state(self, fh, stacks_path, capsys):
        """Otherwise a failed close would permanently block re-arming."""
        gtach_main.enable_stack_dumps()

        def _boom():
            raise OSError('close exploded')

        gtach_main._stacks_file.close = _boom
        gtach_main.disable_stack_dumps()

        assert gtach_main._stacks_file is None
        assert 'WARNING' in capsys.readouterr().err


class TestArmingCycle:
    """Each transition must leave a consistent _stacks_file state."""

    def test_enable_disable_enable_rearms(self, fh, stacks_path):
        assert gtach_main.enable_stack_dumps() is True
        first = gtach_main._stacks_file

        gtach_main.disable_stack_dumps()
        assert gtach_main._stacks_file is None

        assert gtach_main.enable_stack_dumps() is True
        assert gtach_main._stacks_file is not None
        assert gtach_main._stacks_file is not first
        assert fh.calls.count('dump_traceback_later') == 2

    def test_off_on_off(self, fh, stacks_path):
        gtach_main.disable_stack_dumps()
        gtach_main.enable_stack_dumps()
        assert gtach_main._stacks_file is not None
        gtach_main.disable_stack_dumps()
        assert gtach_main._stacks_file is None


class TestSetupLoggingGate:
    """setup_logging arms when and only when its debug argument is truthy."""

    @pytest.fixture
    def isolated_logging(self, tmp_path, monkeypatch):
        """Redirect the log paths and restore the root handler set."""
        monkeypatch.setattr(gtach_main, '_START_LOG', str(tmp_path / 'start.log'))
        monkeypatch.setattr(gtach_main, '_DEBUG_LOG', str(tmp_path / 'debug.log'))
        root = logging.getLogger()
        before = list(root.handlers)
        level = root.level
        yield
        for handler in list(root.handlers):
            if handler not in before:
                root.removeHandler(handler)
                try:
                    handler.close()
                except Exception:
                    pass
        root.setLevel(level)

    def test_debug_false_does_not_arm(self, isolated_logging, monkeypatch):
        calls = []
        monkeypatch.setattr(gtach_main, 'enable_stack_dumps', lambda: calls.append(1))

        gtach_main.setup_logging(debug=False)

        assert calls == []
        assert gtach_main._stacks_file is None

    def test_debug_true_arms_exactly_once(self, isolated_logging, monkeypatch):
        calls = []
        monkeypatch.setattr(gtach_main, 'enable_stack_dumps', lambda: calls.append(1))

        gtach_main.setup_logging(debug=True)

        assert len(calls) == 1

    def test_no_direct_faulthandler_call_in_setup_logging(self):
        """dump_traceback_later belongs to enable_stack_dumps alone."""
        import inspect

        source = inspect.getsource(gtach_main.setup_logging)
        assert 'dump_traceback_later' not in source
        assert 'faulthandler' not in source


def _toggle_host():
    """The minimal self toggle_debug_logging actually uses."""
    host = types.SimpleNamespace()
    host.logger = logging.getLogger('test.toggle')
    return host


def _stub_main(**attrs):
    """A stand-in gtach.main exposing a recording debug handler."""
    stub = types.SimpleNamespace()
    stub._debug_handler = types.SimpleNamespace(levels=[])
    stub._debug_handler.setLevel = stub._debug_handler.levels.append
    for name, value in attrs.items():
        setattr(stub, name, value)
    return stub


@pytest.fixture
def linux(monkeypatch):
    """toggle_debug_logging early-returns off linux; tests run on macOS."""
    monkeypatch.setattr(sys, 'platform', 'linux')


class TestToggleDebugLogging:
    """The runtime OPTIONS toggle drives both diagnostics."""

    def test_enable_sets_level_and_arms(self, linux, monkeypatch):
        armed = []
        stub = _stub_main(enable_stack_dumps=lambda: armed.append(1))
        monkeypatch.setitem(sys.modules, 'gtach.main', stub)

        GTachApplication.toggle_debug_logging(_toggle_host(), True)

        assert stub._debug_handler.levels == [logging.DEBUG]
        assert armed == [1]

    def test_disable_raises_level_and_disarms(self, linux, monkeypatch):
        disarmed = []
        stub = _stub_main(disable_stack_dumps=lambda: disarmed.append(1))
        monkeypatch.setitem(sys.modules, 'gtach.main', stub)

        GTachApplication.toggle_debug_logging(_toggle_host(), False)

        assert stub._debug_handler.levels == [logging.CRITICAL + 1]
        assert disarmed == [1]

    def test_arming_failure_does_not_block_the_handler(self, linux, monkeypatch):
        """The debug handler is the operator's primary control."""
        def _boom():
            raise RuntimeError('arming exploded')

        stub = _stub_main(enable_stack_dumps=_boom)
        monkeypatch.setitem(sys.modules, 'gtach.main', stub)

        GTachApplication.toggle_debug_logging(_toggle_host(), True)

        assert stub._debug_handler.levels == [logging.DEBUG]

    def test_disarming_failure_does_not_block_the_handler(self, linux, monkeypatch):
        def _boom():
            raise RuntimeError('disarming exploded')

        stub = _stub_main(disable_stack_dumps=_boom)
        monkeypatch.setitem(sys.modules, 'gtach.main', stub)

        GTachApplication.toggle_debug_logging(_toggle_host(), False)

        assert stub._debug_handler.levels == [logging.CRITICAL + 1]

    def test_missing_helper_is_not_an_attribute_error(self, linux, monkeypatch):
        """An older or partially loaded gtach.main must not raise."""
        stub = _stub_main()
        monkeypatch.setitem(sys.modules, 'gtach.main', stub)

        GTachApplication.toggle_debug_logging(_toggle_host(), True)
        GTachApplication.toggle_debug_logging(_toggle_host(), False)

        assert stub._debug_handler.levels == [logging.DEBUG, logging.CRITICAL + 1]

    def test_non_linux_returns_before_any_stack_dump_call(self, monkeypatch):
        armed = []
        stub = _stub_main(enable_stack_dumps=lambda: armed.append(1))
        monkeypatch.setitem(sys.modules, 'gtach.main', stub)
        monkeypatch.setattr(sys, 'platform', 'darwin')

        GTachApplication.toggle_debug_logging(_toggle_host(), True)

        assert armed == []
        assert stub._debug_handler.levels == []


class TestStartupThenToggle:
    """--debug at startup followed by an OPTIONS enable must not double-arm."""

    def test_second_arming_is_a_no_op(self, fh, stacks_path, linux, monkeypatch):
        gtach_main.enable_stack_dumps()
        first = gtach_main._stacks_file

        stub = _stub_main(enable_stack_dumps=gtach_main.enable_stack_dumps)
        monkeypatch.setitem(sys.modules, 'gtach.main', stub)

        GTachApplication.toggle_debug_logging(_toggle_host(), True)

        assert gtach_main._stacks_file is first
        assert fh.calls.count('dump_traceback_later') == 1


class TestIterationOneUntouched:
    """Constraints: iteration 1's termination path must be unchanged."""

    def test_stacks_log_path(self):
        assert gtach_main._STACKS_LOG == '/opt/gtach/stacks.log'

    def test_exit_backstop_unchanged(self):
        assert GTachApplication._EXIT_BACKSTOP_SEC == 20.0
        assert callable(GTachApplication._watchdog_shutdown)
        assert callable(GTachApplication._force_exit)
