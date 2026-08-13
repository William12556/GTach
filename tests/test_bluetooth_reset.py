#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Operator-initiated Bluetooth reset.

Covers change-8a63d5f1. The DISCONNECTED screen reported "bluetooth
wedged - reset required" and offered no way to perform that reset.

Two properties here are load-bearing rather than incidental, and are
asserted structurally as well as behaviourally:

* The reset must never run on the display thread. 'display' is a
  watchdog critical thread at a 45 s timeout, and since change-2ac1c602
  a critical timeout terminates the process — so a synchronous
  subprocess in the touch callback would make the button restart the
  application. TestDispatchIsOffThread covers this.
* There must be no automatic invocation of reset_adapter on any
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

from gtach.utils import bluetooth_reset
from gtach.utils.bluetooth_reset import reset_adapter

# Bound on every blocking assertion. A dispatch regression shows up as
# a worker that never finishes, so an unbounded wait would turn a
# failure into a hung run with no diagnostic.
JOIN_TIMEOUT = 5.0

UP_OUTPUT = b'hci0:\tType: Primary  Bus: UART\n\tUP RUNNING\n'
DOWN_OUTPUT = b'hci0:\tType: Primary  Bus: UART\n\tDOWN\n'


def _code_only(path):
    """Return the file's source with comments and strings blanked.

    The scans below describe CODE. bluetooth_reset.py's own docstring
    names subprocess, shell=True, hciuart, rfkill and the down/up
    sequence precisely in order to state the rules it follows, and must
    stay free to. Blanking preserves line numbers so an offender is
    reported at its real location, and loses nothing: every construct
    hunted for is a call or an import, whose name is a NAME token.
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

    def __init__(self, stdout=b'', returncode=0):
        self.stdout = stdout
        self.stderr = b''
        self.returncode = returncode


@pytest.fixture
def hciconfig(monkeypatch):
    """Resolve hciconfig to a fixed path and record every invocation."""
    monkeypatch.setattr(
        bluetooth_reset, '_hciconfig_path', lambda: '/usr/bin/hciconfig'
    )
    return types.SimpleNamespace(calls=[])


def _script(hciconfig, monkeypatch, outcomes):
    """Install a subprocess.run double returning `outcomes` in order."""
    remaining = list(outcomes)

    def _run(args, **kwargs):
        hciconfig.calls.append(list(args))
        result = remaining.pop(0) if remaining else _Completed(DOWN_OUTPUT)
        if isinstance(result, BaseException):
            raise result
        return result

    monkeypatch.setattr(bluetooth_reset.subprocess, 'run', _run)


class TestResetAdapter:
    """Every path returns a short string; none raises."""

    def test_reset_then_up_running(self, hciconfig, monkeypatch):
        _script(hciconfig, monkeypatch, [
            _Completed(b'', 0),          # reset
            _Completed(UP_OUTPUT, 0),    # verify
        ])

        assert reset_adapter() == 'bluetooth adapter reset'
        assert len(hciconfig.calls) == 2
        assert hciconfig.calls[0] == ['/usr/bin/hciconfig', 'hci0', 'reset']
        assert hciconfig.calls[1] == ['/usr/bin/hciconfig', 'hci0']

    def test_up_attempt_recovers(self, hciconfig, monkeypatch):
        _script(hciconfig, monkeypatch, [
            _Completed(b'', 0),            # reset
            _Completed(DOWN_OUTPUT, 0),    # verify — still down
            _Completed(b'', 0),            # up
            _Completed(UP_OUTPUT, 0),      # verify — now up
        ])

        assert reset_adapter() == 'bluetooth adapter reset'
        assert ['/usr/bin/hciconfig', 'hci0', 'up'] in hciconfig.calls

    def test_adapter_stays_down(self, hciconfig, monkeypatch):
        _script(hciconfig, monkeypatch, [
            _Completed(b'', 0),
            _Completed(DOWN_OUTPUT, 0),
            _Completed(b'', 1),
            _Completed(DOWN_OUTPUT, 0),
        ])

        assert reset_adapter() == 'adapter down - reboot required'

    def test_timeout(self, hciconfig, monkeypatch):
        _script(hciconfig, monkeypatch, [
            subprocess.TimeoutExpired(cmd='hciconfig', timeout=10.0),
        ])

        assert reset_adapter() == 'bluetooth reset timed out'

    def test_path_unresolved(self, monkeypatch):
        monkeypatch.setattr(bluetooth_reset, '_hciconfig_path', lambda: None)
        attempted = []
        monkeypatch.setattr(
            bluetooth_reset.subprocess, 'run',
            lambda *a, **k: attempted.append(a)
        )

        assert reset_adapter() == 'hciconfig not found'
        assert attempted == []

    def test_permission_error(self, hciconfig, monkeypatch):
        _script(hciconfig, monkeypatch, [PermissionError('not root')])

        assert reset_adapter() == 'bluetooth reset not permitted'

    def test_file_not_found(self, hciconfig, monkeypatch):
        _script(hciconfig, monkeypatch, [FileNotFoundError('vanished')])

        assert reset_adapter() == 'hciconfig not found'

    def test_arbitrary_exception(self, hciconfig, monkeypatch):
        _script(hciconfig, monkeypatch, [RuntimeError('something odd')])

        assert reset_adapter() == 'bluetooth reset failed'

    def test_unexpected_stdout_is_treated_as_down(self, hciconfig, monkeypatch):
        """A parsing surprise costs one up attempt, not an exception."""
        _script(hciconfig, monkeypatch, [
            _Completed(b'', 0),
            _Completed(b'\x00\xff nonsense not utf-8', 0),
            _Completed(b'', 0),
            _Completed(UP_OUTPUT, 0),
        ])

        assert reset_adapter() == 'bluetooth adapter reset'

    def test_timeout_is_passed_through(self, hciconfig, monkeypatch):
        captured = []

        def _run(args, **kwargs):
            captured.append(kwargs.get('timeout'))
            return _Completed(UP_OUTPUT, 0)

        monkeypatch.setattr(bluetooth_reset.subprocess, 'run', _run)

        reset_adapter(timeout=3.5)

        assert captured and all(t == 3.5 for t in captured)

    def test_every_outcome_fits_the_cause_line(self):
        outcomes = [
            bluetooth_reset._OK,
            bluetooth_reset._DOWN,
            bluetooth_reset._TIMED_OUT,
            bluetooth_reset._NOT_PERMITTED,
            bluetooth_reset._NOT_FOUND,
            bluetooth_reset._FAILED,
        ]
        for text in outcomes:
            assert text
            assert len(text) <= 40, (text, len(text))

    def test_reboot_message_is_not_softened(self):
        """The manual attempt on target left the host in this state."""
        assert bluetooth_reset._DOWN == 'adapter down - reboot required'


class TestPrivilegedSurfaceIsContained:
    """The boundary that permits host action at all."""

    def _src_files(self):
        import pathlib

        root = pathlib.Path(__file__).resolve().parents[1] / 'src'
        return sorted(root.rglob('*.py'))

    def test_subprocess_only_in_the_reset_module(self):
        offenders = []
        for path in self._src_files():
            if path.name == 'bluetooth_reset.py':
                continue
            for number, line in enumerate(_code_only(path).splitlines(), 1):
                if 'subprocess' in line:
                    offenders.append(f'{path.name}:{number}: {line.strip()}')

        # Pre-existing users outside this change's remit; none is a
        # Bluetooth recovery action. Recorded explicitly so a NEW
        # importer anywhere else fails this test.
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
                if 'reset_adapter' in line:
                    sites.append((path.name, number, line.strip()))

        definitions = [s for s in sites if s[2].startswith('def reset_adapter')]
        calls = [s for s in sites if 'reset_adapter(' in s[2]
                 and not s[2].startswith('def ')]

        assert len(definitions) == 1, definitions
        assert len(calls) == 1, calls
        assert calls[0][0] == 'app.py', calls

    def test_no_down_then_up_sequence(self):
        """That sequence bricked the controller on target."""
        for path in self._src_files():
            text = path.read_text(encoding='utf-8')
            # Not blanked: the argument list IS string literals.
            assert "'hci0', 'down'" not in text, path
            assert '"hci0", "down"' not in text, path

    def test_no_systemctl_hciuart_rfkill_or_modules(self):
        import re

        forbidden = re.compile(
            r'systemctl|hciuart|rfkill|modprobe|insmod|rmmod', re.IGNORECASE
        )
        for path in self._src_files():
            # Pre-existing: capability detection and setup-mode pairing.
            if path.name in ('platform.py', 'system_bluetooth.py'):
                continue
            for number, line in enumerate(_code_only(path).splitlines(), 1):
                assert not forbidden.search(line), f'{path.name}:{number}'

    def test_module_imports_are_minimal(self):
        import ast

        source = open(bluetooth_reset.__file__, encoding='utf-8').read()
        imported = set()
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Import):
                imported.update(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.add(node.module)

        assert imported == {'logging', 'shutil', 'subprocess', 'typing'}


def _app_host():
    """The minimal self _on_bluetooth_reset actually uses."""
    host = types.SimpleNamespace()
    host.logger = logging.getLogger('test.btreset')
    host._bt_reset_in_flight = threading.Event()
    host._bt_reset_status = None
    host._bt_reset_lock = threading.Lock()

    from gtach.app import GTachApplication
    host._set_bt_reset_status = lambda status: \
        GTachApplication._set_bt_reset_status(host, status)
    return host


def _press(host):
    from gtach.app import GTachApplication

    GTachApplication._on_bluetooth_reset(host)


class TestDispatchIsOffThread:
    """The button must never block the display thread."""

    def _threads_named(self, name):
        return [t for t in threading.enumerate() if t.name == name]

    def test_single_press_returns_promptly(self, monkeypatch):
        release = threading.Event()
        monkeypatch.setattr(
            bluetooth_reset, 'reset_adapter',
            lambda *a, **k: (release.wait(JOIN_TIMEOUT), 'bluetooth adapter reset')[1]
        )

        host = _app_host()
        started = time.time()
        _press(host)
        elapsed = time.time() - started

        # The worker is still blocked; the caller returned anyway.
        assert elapsed < 0.5, elapsed
        assert host._bt_reset_in_flight.is_set() is True
        assert self._threads_named('bt_reset')

        release.set()
        deadline = time.time() + JOIN_TIMEOUT
        while host._bt_reset_in_flight.is_set() and time.time() < deadline:
            time.sleep(0.01)

    def test_worker_is_a_daemon(self, monkeypatch):
        """Shutdown mid-reset must not delay interpreter exit."""
        release = threading.Event()
        monkeypatch.setattr(
            bluetooth_reset, 'reset_adapter',
            lambda *a, **k: (release.wait(JOIN_TIMEOUT), 'ok')[1]
        )

        host = _app_host()
        _press(host)

        workers = self._threads_named('bt_reset')
        assert workers
        assert all(t.daemon for t in workers)

        release.set()

    def test_worker_is_not_registered_with_thread_manager(self):
        """It is short-lived and must not be watchdog-monitored."""
        import inspect

        from gtach.app import GTachApplication

        source = inspect.getsource(GTachApplication._on_bluetooth_reset)
        assert 'register_thread' not in source

    def test_second_press_while_in_flight_is_ignored(self, monkeypatch):
        release = threading.Event()
        calls = []
        monkeypatch.setattr(
            bluetooth_reset, 'reset_adapter',
            lambda *a, **k: (calls.append(1), release.wait(JOIN_TIMEOUT), 'ok')[2]
        )

        host = _app_host()
        _press(host)
        _press(host)

        assert len(self._threads_named('bt_reset')) == 1

        release.set()
        deadline = time.time() + JOIN_TIMEOUT
        while host._bt_reset_in_flight.is_set() and time.time() < deadline:
            time.sleep(0.01)
        assert len(calls) == 1

    def test_press_after_completion_starts_a_new_worker(self, monkeypatch):
        calls = []
        monkeypatch.setattr(
            bluetooth_reset, 'reset_adapter',
            lambda *a, **k: (calls.append(1), 'bluetooth adapter reset')[1]
        )

        host = _app_host()
        for _ in range(2):
            _press(host)
            deadline = time.time() + JOIN_TIMEOUT
            while host._bt_reset_in_flight.is_set() and time.time() < deadline:
                time.sleep(0.01)
            assert host._bt_reset_in_flight.is_set() is False

        assert len(calls) == 2

    def test_raising_worker_clears_the_event(self, monkeypatch):
        """A raising worker must not wedge the button permanently."""
        def _boom(*a, **k):
            raise RuntimeError('reset exploded')

        monkeypatch.setattr(bluetooth_reset, 'reset_adapter', _boom)

        host = _app_host()
        _press(host)

        deadline = time.time() + JOIN_TIMEOUT
        while host._bt_reset_in_flight.is_set() and time.time() < deadline:
            time.sleep(0.01)

        assert host._bt_reset_in_flight.is_set() is False
        assert host._bt_reset_status == 'bluetooth reset failed'

    def test_progress_then_outcome_written(self, monkeypatch):
        seen = []
        release = threading.Event()

        def _slow(*a, **k):
            seen.append(('during', None))
            release.wait(JOIN_TIMEOUT)
            return 'bluetooth adapter reset'

        monkeypatch.setattr(bluetooth_reset, 'reset_adapter', _slow)

        host = _app_host()
        _press(host)

        # Progress is visible before the worker finishes.
        assert host._bt_reset_status == 'resetting bluetooth...'

        release.set()
        deadline = time.time() + JOIN_TIMEOUT
        while host._bt_reset_in_flight.is_set() and time.time() < deadline:
            time.sleep(0.01)

        assert host._bt_reset_status == 'bluetooth adapter reset'

    def test_callback_performs_no_blocking_call(self):
        import inspect

        from gtach.app import GTachApplication

        source = inspect.getsource(GTachApplication._on_bluetooth_reset)
        # The only reset_adapter reference is inside the nested worker.
        outer = source.split('def _worker')[0]
        assert 'reset_adapter' not in outer
        assert 'join(' not in source
        assert 'time.sleep' not in source


class TestCauseLineMerge:
    """A reset outcome supersedes the transport cause, then clears."""

    def _host(self, transport=None):
        host = types.SimpleNamespace()
        host._bt_reset_status = None
        host._bt_reset_lock = threading.Lock()
        if transport is not None:
            host._transport = transport
        return host

    def _cause(self, host):
        from gtach.app import GTachApplication

        return GTachApplication._disconnected_cause(host)

    def test_no_transport_and_no_status(self):
        assert self._cause(self._host()) is None

    def test_transport_cause_when_no_reset_status(self):
        transport = types.SimpleNamespace(
            is_connected=lambda: False,
            last_failure_cause='adapter stopped responding',
        )

        assert self._cause(self._host(transport)) == 'adapter stopped responding'

    def test_reset_status_supersedes_transport_cause(self):
        transport = types.SimpleNamespace(
            is_connected=lambda: False,
            last_failure_cause='bluetooth wedged - reset required',
        )
        host = self._host(transport)
        host._bt_reset_status = 'resetting bluetooth...'

        assert self._cause(host) == 'resetting bluetooth...'

    def test_status_cleared_once_the_link_returns(self):
        """A stale outcome must not mask a later transport failure."""
        transport = types.SimpleNamespace(
            is_connected=lambda: True,
            last_failure_cause=None,
        )
        host = self._host(transport)
        host._bt_reset_status = 'adapter down - reboot required'

        assert self._cause(host) is None
        assert host._bt_reset_status is None

    def test_button_press_with_no_transport_is_guarded(self):
        """Edge case: pressed before select_transport has run."""
        host = self._host()
        host._bt_reset_status = 'resetting bluetooth...'

        assert self._cause(host) == 'resetting bluetooth...'


class TestButtonRegistration:
    """Registered only when wired; Setup must not move."""

    def _registered(self, callback):
        from gtach.display.manager import DisplayManager

        calls = []

        host = types.SimpleNamespace()
        host.logger = logging.getLogger('test.btreset')
        host._bluetooth_reset_callback = callback
        host._enter_setup_from_disconnected = lambda: None

        def _column(specs, width, top, **kwargs):
            specs = list(specs)
            calls.append(types.SimpleNamespace(
                specs=specs, width=width, top=top
            ))
            return ['rect-%d' % i for i in range(len(specs))]

        host._button_column = _column
        DisplayManager._register_disconnected_regions(host)
        return host, calls[0]

    def test_callback_unset_registers_only_setup(self):
        host, call = self._registered(None)

        assert [s[0] for s in call.specs] == ['disconnected_setup']
        assert host._disconnected_btn_bt_reset is None

    def test_callback_set_registers_both(self):
        host, call = self._registered(lambda: None)

        assert [s[0] for s in call.specs] == [
            'disconnected_setup', 'disconnected_bt_reset'
        ]
        assert host._disconnected_btn_bt_reset == 'rect-1'

    def test_setup_rect_identical_either_way(self):
        without, call_without = self._registered(None)
        with_button, call_with = self._registered(lambda: None)

        assert without._disconnected_btn_setup == with_button._disconnected_btn_setup
        assert call_without.width == call_with.width == 240
        assert call_without.top == call_with.top == 240

    def test_reset_spec_invokes_the_callback(self):
        pressed = []
        _host, call = self._registered(lambda: pressed.append(1))

        call.specs[1][2]((0, 0))

        assert pressed == [1]


class TestButtonRendering:
    """Drawn only when its rect exists; label fits the button."""

    def _render(self, bt_rect):
        from gtach.display.manager import DisplayManager

        drawn = []
        host = types.SimpleNamespace()
        host.logger = logging.getLogger('test.btreset')
        host._link_cause_callback = None
        host._disconnected_btn_setup = 'rect-0'
        host._disconnected_btn_bt_reset = bt_rect
        host._get_cached_font = lambda size: f'font-{size}'
        host._DISCONNECTED_BG_COLOUR = DisplayManager._DISCONNECTED_BG_COLOUR
        host._DISCONNECTED_TEXT_COLOUR = DisplayManager._DISCONNECTED_TEXT_COLOUR
        host._draw_status_indicator = lambda: None
        host._draw_button = lambda rect, label, fill, font: \
            drawn.append((rect, label))
        host._draw_reconnect_spinner = lambda: None
        host.rendering_engine = types.SimpleNamespace(
            clear_surface=lambda *a, **k: None,
            get_surface=lambda target: object(),
            render_text=lambda *a, **k: None,
        )

        DisplayManager._render_disconnected(host)
        return drawn

    def test_not_drawn_when_rect_is_none(self):
        drawn = self._render(None)

        assert drawn == [('rect-0', 'Setup')]

    def test_drawn_when_rect_exists(self):
        drawn = self._render('rect-1')

        assert drawn == [('rect-0', 'Setup'), ('rect-1', 'BT Reset')]

    def test_label_fits_the_button_width(self):
        """Measured, not assumed: the full label overflows at 300 px."""
        import pygame

        pygame.init()
        pygame.font.init()
        try:
            from gtach.display.typography import get_font_manager
            font = get_font_manager().get_font(28)
        except Exception:
            font = pygame.font.Font(None, 28)

        assert font.size('BT Reset')[0] <= 240
