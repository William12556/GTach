#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Operator-initiated reboot of the host.

Covers change-4ab5ff88. The DISCONNECTED screen's Bluetooth Reset
button invoked ``hciconfig hci0 reset``, which frequently left the
adapter down on target; only a reboot recovered the link. The button
and its whole callback chain are replaced by a Reset button that
reboots the Pi.

Two properties here are load-bearing rather than incidental, and are
asserted structurally as well as behaviourally:

* The reboot must never run on the display thread. 'display' is a
  watchdog critical thread at a 45 s timeout, and since change-2ac1c602
  a critical timeout terminates the process — so a synchronous
  subprocess in the touch callback would race the reboot against the
  watchdog. TestDispatchIsOffThread covers this.
* There must be no automatic invocation of reboot_device on any
  trigger. The button callback is the only call site, and that boundary
  is the entire basis on which host action is permitted at all.
  TestPrivilegedSurfaceIsContained covers this.
"""

import logging
import subprocess
import threading
import time
import types

import pytest

from gtach.utils import pi_reset
from gtach.utils.pi_reset import reboot_device

# Bound on every blocking assertion. A dispatch regression shows up as
# a worker that never finishes, so an unbounded wait would turn a
# failure into a hung run with no diagnostic.
JOIN_TIMEOUT = 5.0


def _code_only(path):
    """Return the file's source with comments and strings blanked.

    The scans below describe CODE. pi_reset.py's own docstring names
    subprocess, shell=True, systemctl and shutdown precisely in order
    to state the rules it follows, and must stay free to. Blanking
    preserves line numbers so an offender is reported at its real
    location, and loses nothing: every construct hunted for is a call
    or an import, whose name is a NAME token.
    """
    import io
    import tokenize

    text = path.read_text(encoding='utf-8')
    rows = [list(line) for line in text.splitlines(keepends=True)]

    for token in tokenize.generate_tokens(io.StringIO(text).readline):
        if token.type not in (tokenize.COMMENT, tokenize.STRING):
            continue
        (start_row, start_col), (end_row, end_col) = token.start, token.end
        for row in range(start_row, end_row + 1):
            line = rows[row - 1]
            begin = start_col if row == start_row else 0
            finish = end_col if row == end_row else len(line)
            for index in range(begin, min(finish, len(line))):
                if line[index] != '\n':
                    line[index] = ' '

    return ''.join(''.join(row) for row in rows)


class _Completed:
    """Stands in for subprocess.CompletedProcess."""

    def __init__(self, returncode=0):
        self.stdout = b''
        self.stderr = b''
        self.returncode = returncode


@pytest.fixture
def reboot_present(monkeypatch):
    """Report /sbin/reboot as present and record every invocation."""
    monkeypatch.setattr(pi_reset.os.path, 'exists', lambda path: True)
    return types.SimpleNamespace(calls=[])


def _script(recorder, monkeypatch, outcome):
    """Install a subprocess.run double returning (or raising) `outcome`."""
    def _run(args, **kwargs):
        recorder.calls.append((list(args), kwargs))
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome

    monkeypatch.setattr(pi_reset.subprocess, 'run', _run)


class TestRebootDevice:
    """Every path returns a short string; none raises."""

    def test_success(self, reboot_present, monkeypatch):
        _script(reboot_present, monkeypatch, _Completed(0))

        assert reboot_device() == 'reboot initiated'
        assert len(reboot_present.calls) == 1
        args, kwargs = reboot_present.calls[0]
        assert args == ['/sbin/reboot']
        assert 'shell' not in kwargs

    def test_non_zero_return_code(self, reboot_present, monkeypatch):
        """Not silently a success: the reboot did not take."""
        _script(reboot_present, monkeypatch, _Completed(1))

        assert reboot_device() == 'reboot command failed'

    def test_reboot_path_absent(self, monkeypatch):
        monkeypatch.setattr(pi_reset.os.path, 'exists', lambda path: False)
        attempted = []
        monkeypatch.setattr(
            pi_reset.subprocess, 'run', lambda *a, **k: attempted.append(a)
        )

        assert reboot_device() == 'reboot command not found'
        assert attempted == []

    def test_timeout(self, reboot_present, monkeypatch):
        _script(reboot_present, monkeypatch,
                subprocess.TimeoutExpired(cmd='/sbin/reboot', timeout=10.0))

        assert reboot_device() == 'reboot timed out'

    def test_permission_error(self, reboot_present, monkeypatch):
        _script(reboot_present, monkeypatch, PermissionError('not root'))

        assert reboot_device() == 'reboot not permitted'

    def test_file_not_found(self, reboot_present, monkeypatch):
        """Vanished between the existence check and the invocation."""
        _script(reboot_present, monkeypatch, FileNotFoundError('vanished'))

        assert reboot_device() == 'reboot command not found'

    def test_arbitrary_exception(self, reboot_present, monkeypatch):
        _script(reboot_present, monkeypatch, RuntimeError('something odd'))

        assert reboot_device() == 'reboot failed'

    def test_timeout_is_passed_through(self, reboot_present, monkeypatch):
        _script(reboot_present, monkeypatch, _Completed(0))

        reboot_device(timeout=3.5)

        _args, kwargs = reboot_present.calls[0]
        assert kwargs.get('timeout') == 3.5

    def test_every_outcome_fits_the_cause_line(self):
        outcomes = [
            pi_reset._OK,
            pi_reset._TIMED_OUT,
            pi_reset._NOT_PERMITTED,
            pi_reset._NOT_FOUND,
            pi_reset._FAILED,
            pi_reset._COMMAND_FAILED,
        ]
        for text in outcomes:
            assert text
            assert len(text) <= 40, (text, len(text))

    def test_reboot_path_is_fixed(self):
        """William's explicit choice: the literal path, not a lookup."""
        assert pi_reset._REBOOT_PATH == '/sbin/reboot'


class TestPrivilegedSurfaceIsContained:
    """The boundary that permits host action at all."""

    def _src_files(self):
        import pathlib

        root = pathlib.Path(__file__).resolve().parents[1] / 'src'
        return sorted(root.rglob('*.py'))

    def test_subprocess_only_in_the_reset_module(self):
        offenders = []
        for path in self._src_files():
            if path.name == 'pi_reset.py':
                continue
            for number, line in enumerate(_code_only(path).splitlines(), 1):
                if 'subprocess' in line:
                    offenders.append(f'{path.name}:{number}: {line.strip()}')

        # Pre-existing users outside this change's remit; none is a
        # link recovery action. Recorded explicitly so a NEW importer
        # anywhere else fails this test.
        #
        # system_bluetooth  — bluetoothctl/hcitool for setup-mode
        #                     device DISCOVERY, not recovery.
        # platform          — capability detection.
        # dependencies      — dependency validation.
        # manager_backup    — dead file. Unreferenced, 0% covered, and
        #                     superseded by manager.py; it is in src/
        #                     only because it was never deleted.
        allowed_files = {
            'system_bluetooth.py', 'platform.py', 'dependencies.py',
            'manager_backup.py',
        }
        unexpected = [o for o in offenders
                      if o.split(':')[0] not in allowed_files]
        assert unexpected == [], unexpected

    def test_no_subprocess_under_comm(self):
        """change-5e7a03c4 forbids it there, and system_bluetooth is
        the setup-mode pairing subsystem, not a reset path."""
        import pathlib

        root = pathlib.Path(__file__).resolve().parents[1] / 'src'
        transport = _code_only(root / 'gtach' / 'comm' / 'transport.py')

        assert 'subprocess' not in transport

    def test_no_shell_true_anywhere(self):
        for path in self._src_files():
            assert 'shell=True' not in _code_only(path), path

    def test_exactly_one_call_site(self):
        """Definition plus one caller; nothing automatic."""
        sites = []
        for path in self._src_files():
            for number, line in enumerate(_code_only(path).splitlines(), 1):
                if 'reboot_device' in line:
                    sites.append((path.name, number, line.strip()))

        definitions = [s for s in sites if s[2].startswith('def reboot_device')]
        calls = [s for s in sites if 'reboot_device(' in s[2]
                 and not s[2].startswith('def ')]

        assert len(definitions) == 1, definitions
        assert len(calls) == 1, calls
        assert calls[0][0] == 'app.py', calls

    def test_no_alternative_reboot_invocations(self):
        """systemctl reboot and shutdown -r were explicitly rejected."""
        import re

        forbidden = re.compile(
            r'systemctl|shutdown -r|shutil\.which|hciuart|rfkill|modprobe'
            r'|insmod|rmmod', re.IGNORECASE
        )
        for path in self._src_files():
            # Pre-existing: capability detection and setup-mode pairing.
            if path.name in ('platform.py', 'system_bluetooth.py'):
                continue
            for number, line in enumerate(_code_only(path).splitlines(), 1):
                assert not forbidden.search(line), f'{path.name}:{number}'

    def test_no_bluetooth_reset_remnants(self):
        """The retired path is deleted, not left unwired."""
        import pathlib

        root = pathlib.Path(__file__).resolve().parents[1]
        assert not (root / 'src' / 'gtach' / 'utils' / 'bluetooth_reset.py').exists()
        assert not (root / 'tests' / 'test_bluetooth_reset.py').exists()

        retired = (
            '_bluetooth_reset_callback', '_disconnected_btn_bt_reset',
            'disconnected_bt_reset', '_bt_reset_in_flight',
            '_bt_reset_status', '_on_bluetooth_reset', 'reset_adapter',
        )
        for path in self._src_files():
            code = _code_only(path)
            for name in retired:
                assert name not in code, f'{path.name}: {name}'

    def test_module_imports_are_minimal(self):
        import ast

        source = open(pi_reset.__file__, encoding='utf-8').read()
        imported = set()
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Import):
                imported.update(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.add(node.module)

        assert imported == {'logging', 'os', 'subprocess'}


def _app_host():
    """The minimal self _on_reset_pi actually uses."""
    host = types.SimpleNamespace()
    host.logger = logging.getLogger('test.pireset')
    host._reset_in_flight = threading.Event()
    return host


def _press(host):
    from gtach.app import GTachApplication

    GTachApplication._on_reset_pi(host)


class TestDispatchIsOffThread:
    """The button must never block the display thread."""

    def _threads_named(self, name):
        return [t for t in threading.enumerate() if t.name == name]

    def test_single_press_returns_promptly(self, monkeypatch):
        release = threading.Event()
        monkeypatch.setattr(
            pi_reset, 'reboot_device',
            lambda *a, **k: (release.wait(JOIN_TIMEOUT), 'reboot initiated')[1]
        )

        host = _app_host()
        started = time.time()
        _press(host)
        elapsed = time.time() - started

        # The worker is still blocked; the caller returned anyway.
        assert elapsed < 0.5, elapsed
        assert host._reset_in_flight.is_set() is True
        assert self._threads_named('pi_reset')

        release.set()
        deadline = time.time() + JOIN_TIMEOUT
        while host._reset_in_flight.is_set() and time.time() < deadline:
            time.sleep(0.01)

    def test_worker_is_a_daemon(self, monkeypatch):
        """Shutdown mid-reset must not delay interpreter exit."""
        release = threading.Event()
        monkeypatch.setattr(
            pi_reset, 'reboot_device',
            lambda *a, **k: (release.wait(JOIN_TIMEOUT), 'ok')[1]
        )

        host = _app_host()
        _press(host)

        workers = self._threads_named('pi_reset')
        assert workers
        assert all(t.daemon for t in workers)

        release.set()

    def test_worker_is_not_registered_with_thread_manager(self):
        """It is short-lived and must not be watchdog-monitored."""
        import inspect

        from gtach.app import GTachApplication

        source = inspect.getsource(GTachApplication._on_reset_pi)
        assert 'register_thread' not in source

    def test_second_press_while_in_flight_is_ignored(self, monkeypatch):
        release = threading.Event()
        calls = []
        monkeypatch.setattr(
            pi_reset, 'reboot_device',
            lambda *a, **k: (calls.append(1), release.wait(JOIN_TIMEOUT), 'ok')[2]
        )

        host = _app_host()
        _press(host)
        _press(host)

        assert len(self._threads_named('pi_reset')) == 1

        release.set()
        deadline = time.time() + JOIN_TIMEOUT
        while host._reset_in_flight.is_set() and time.time() < deadline:
            time.sleep(0.01)
        assert len(calls) == 1

    def test_press_after_completion_starts_a_new_worker(self, monkeypatch):
        calls = []
        monkeypatch.setattr(
            pi_reset, 'reboot_device',
            lambda *a, **k: (calls.append(1), 'reboot initiated')[1]
        )

        host = _app_host()
        for _ in range(2):
            _press(host)
            deadline = time.time() + JOIN_TIMEOUT
            while host._reset_in_flight.is_set() and time.time() < deadline:
                time.sleep(0.01)
            assert host._reset_in_flight.is_set() is False

        assert len(calls) == 2

    def test_raising_worker_clears_the_event(self, monkeypatch):
        """A raising worker must not wedge the button permanently."""
        def _boom(*a, **k):
            raise RuntimeError('reboot exploded')

        monkeypatch.setattr(pi_reset, 'reboot_device', _boom)

        host = _app_host()
        _press(host)

        deadline = time.time() + JOIN_TIMEOUT
        while host._reset_in_flight.is_set() and time.time() < deadline:
            time.sleep(0.01)

        assert host._reset_in_flight.is_set() is False

    def test_callback_performs_no_blocking_call(self):
        import inspect

        from gtach.app import GTachApplication

        source = inspect.getsource(GTachApplication._on_reset_pi)
        # The only reboot_device reference is inside the nested worker.
        outer = source.split('def _worker')[0]
        assert 'reboot_device' not in outer
        assert 'join(' not in source
        assert 'time.sleep' not in source
