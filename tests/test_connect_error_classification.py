#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Closing failed sockets and reporting why a connect failed.

Covers change-5e7a03c4. On target an adapter fault and a missing OBD
dongle produced identical logs and an identical DISCONNECTED screen;
establishing which it was took a full session of manual hcitool work to
recover information errno already carried. The socket that failed to
connect was also abandoned open, holding its ACL reference.

This change REPORTS and must not ACT on the host. TestNoHostActions
below asserts that no recovery action, shell invocation or Bluetooth
tool parsing was introduced into any file this change edits.
"""

import errno
import types

import pytest

from gtach.comm import transport as transport_module
from gtach.comm.transport import (
    _CONNECT_FAULT_CAUSES,
    OBDTransport,
    TransportState,
    _bluetooth_adapter_present,
)


def _code_only(path):
    """Return the file's source with comments and strings blanked.

    Source-level assertions below describe the CODE. Both the comments
    and the docstrings in this change legitimately name the very tools
    and actions they exist to explain NOT using, and must stay free to.
    Blanking rather than deleting preserves line numbers, so an
    offender is reported at its real location.

    Blanking string literals loses nothing: every construct these
    assertions hunt for is a call, and the callable is a NAME token
    that survives.
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


class _StubTransport(OBDTransport):
    """A transport whose _open outcome is scripted."""

    _IO_ERRORS = (OSError,)

    def __init__(self, outcome=None):
        super().__init__()
        # Either an exception instance to raise, or a handle to return.
        self._outcome = outcome
        self.closed_handles = []

    def _describe(self) -> str:
        return 'stub-peer'

    def _open(self):
        if isinstance(self._outcome, BaseException):
            raise self._outcome
        return self._outcome if self._outcome is not None else object()

    def _close(self, handle) -> None:
        self.closed_handles.append(handle)


@pytest.fixture
def adapter_present(monkeypatch):
    """Force the sysfs probe to report a controller present."""
    monkeypatch.setattr(
        transport_module, '_bluetooth_adapter_present', lambda: True
    )


@pytest.fixture
def adapter_absent(monkeypatch):
    monkeypatch.setattr(
        transport_module, '_bluetooth_adapter_present', lambda: False
    )


class TestSocketClosedOnFailure:
    """RFCOMMTransport._open must not abandon a socket that failed."""

    def _open_with(self, monkeypatch, connect_raises, close_raises=None):
        """Drive RFCOMMTransport._open against a fake socket module."""
        import gtach.comm.rfcomm as rfcomm_module

        record = types.SimpleNamespace(closed=0, timeouts=[])

        class _FakeSocket:
            def settimeout(self, value):
                record.timeouts.append(value)

            def connect(self, address):
                if connect_raises is not None:
                    raise connect_raises

            def close(self):
                record.closed += 1
                if close_raises is not None:
                    raise close_raises

        fake_socket_module = types.SimpleNamespace(
            AF_BLUETOOTH=31,
            SOCK_STREAM=1,
            BTPROTO_RFCOMM=3,
            socket=lambda *a, **k: _FakeSocket(),
        )
        monkeypatch.setattr(rfcomm_module, 'socket', fake_socket_module)

        transport = rfcomm_module.RFCOMMTransport.__new__(
            rfcomm_module.RFCOMMTransport
        )
        transport._mac_address = 'AA:BB:CC:DD:EE:FF'
        transport._channel = 1
        return transport, record

    def test_socket_closed_when_connect_raises(self, monkeypatch):
        failure = OSError(errno.EBUSY, 'Device or resource busy')
        transport, record = self._open_with(monkeypatch, failure)

        with pytest.raises(OSError) as caught:
            transport._open()

        assert record.closed == 1
        # The original exception, with its errno intact.
        assert caught.value is failure
        assert caught.value.errno == errno.EBUSY

    def test_close_error_is_swallowed(self, monkeypatch):
        failure = OSError(errno.ETIMEDOUT, 'Connection timed out')
        transport, record = self._open_with(
            monkeypatch, failure, close_raises=OSError('close exploded')
        )

        with pytest.raises(OSError) as caught:
            transport._open()

        assert caught.value is failure
        assert record.closed == 1

    def test_socket_not_closed_on_success(self, monkeypatch):
        transport, record = self._open_with(monkeypatch, None)

        result = transport._open()

        assert result is not None
        assert record.closed == 0
        # settimeout(10) before connect, settimeout(None) after.
        assert record.timeouts == [10, None]

    def test_base_exception_also_closes(self, monkeypatch):
        """A KeyboardInterrupt must not leak the socket either."""
        transport, record = self._open_with(monkeypatch, KeyboardInterrupt())

        with pytest.raises(KeyboardInterrupt):
            transport._open()

        assert record.closed == 1


class TestClassifyConnectError:
    """errno resolves to a named cause; nothing raises."""

    def test_ebusy_maps_to_the_busy_string(self, adapter_present):
        stub = _StubTransport()

        cause = stub._classify_connect_error(
            OSError(errno.EBUSY, 'Device or resource busy')
        )

        assert cause == _CONNECT_FAULT_CAUSES[errno.EBUSY]
        assert len(cause) <= 40

    def test_ehostdown_maps_to_unreachable(self, adapter_present):
        stub = _StubTransport()

        cause = stub._classify_connect_error(
            OSError(errno.EHOSTDOWN, 'Host is down')
        )

        assert cause == 'adapter not reachable'

    def test_missing_adapter_overrides_the_errno_mapping(self, adapter_absent):
        """The more specific and more actionable fact wins."""
        stub = _StubTransport()

        for code in (errno.EBUSY, errno.ETIMEDOUT, errno.ECONNREFUSED):
            cause = stub._classify_connect_error(OSError(code, 'whatever'))
            assert cause == 'no bluetooth controller', code

    def test_unmapped_errno_returns_its_name(self, adapter_present):
        stub = _StubTransport()

        cause = stub._classify_connect_error(
            OSError(errno.EPERM, 'Operation not permitted')
        )

        assert cause == 'EPERM'

    def test_errno_none_does_not_raise(self, adapter_present):
        stub = _StubTransport()

        cause = stub._classify_connect_error(OSError('no errno at all'))

        assert isinstance(cause, str)
        assert cause

    def test_never_raises_for_hostile_input(self, adapter_present):
        """A diagnostic must not become a new failure source."""
        stub = _StubTransport()

        class _Hostile(OSError):
            @property
            def errno(self):
                raise RuntimeError('errno exploded')

            def __str__(self):
                raise RuntimeError('str exploded')

        cause = stub._classify_connect_error(_Hostile())

        assert isinstance(cause, str)
        assert cause

    def test_every_mapped_cause_fits_the_display(self):
        """480x480 leaves no room for a long line."""
        for code, text in _CONNECT_FAULT_CAUSES.items():
            assert len(text) <= 40, (code, text, len(text))
            assert text == text.strip()
            assert text


class TestAdapterProbe:
    """sysfs only, and optimistic when it cannot answer."""

    def test_absent_path_returns_true(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            transport_module, '_BLUETOOTH_SYSFS', str(tmp_path / 'nope')
        )

        assert _bluetooth_adapter_present() is True

    def test_empty_directory_returns_false(self, tmp_path, monkeypatch):
        empty = tmp_path / 'bluetooth'
        empty.mkdir()
        monkeypatch.setattr(transport_module, '_BLUETOOTH_SYSFS', str(empty))

        assert _bluetooth_adapter_present() is False

    def test_populated_directory_returns_true(self, tmp_path, monkeypatch):
        populated = tmp_path / 'bluetooth'
        populated.mkdir()
        (populated / 'hci0').mkdir()
        monkeypatch.setattr(
            transport_module, '_BLUETOOTH_SYSFS', str(populated)
        )

        assert _bluetooth_adapter_present() is True

    def test_probe_failure_returns_true(self, monkeypatch):
        """An unknown state must never read as a hardware fault."""
        def _boom(_path):
            raise RuntimeError('sysfs exploded')

        monkeypatch.setattr(transport_module.os.path, 'isdir', _boom)

        assert _bluetooth_adapter_present() is True


class TestLastFailureCause:
    """Set on failure, cleared on success, read under the lock."""

    def test_none_before_any_attempt(self):
        assert _StubTransport().last_failure_cause is None

    def test_set_after_a_failed_connect(self, adapter_present):
        stub = _StubTransport(OSError(errno.EBUSY, 'Device or resource busy'))

        assert stub.connect() is False

        assert stub.last_failure_cause == _CONNECT_FAULT_CAUSES[errno.EBUSY]
        assert stub.state is TransportState.DISCONNECTED

    def test_cleared_after_a_successful_connect(self, adapter_present):
        stub = _StubTransport(OSError(errno.EBUSY, 'busy'))
        assert stub.connect() is False
        assert stub.last_failure_cause is not None

        stub._outcome = object()
        assert stub.connect() is True

        assert stub.last_failure_cause is None

    def test_repeated_failures_overwrite_rather_than_accumulate(self, adapter_present):
        stub = _StubTransport(OSError(errno.EBUSY, 'busy'))

        for _ in range(3):
            stub.connect()

        assert stub.last_failure_cause == _CONNECT_FAULT_CAUSES[errno.EBUSY]

    def test_existing_log_content_is_retained(self, adapter_present, caplog):
        """The cause is added to the message, not substituted for it."""
        stub = _StubTransport(OSError(errno.EBUSY, 'Device or resource busy'))

        with caplog.at_level('ERROR'):
            stub.connect()

        messages = [r.getMessage() for r in caplog.records]
        assert any('Failed to connect to stub-peer' in m for m in messages)
        assert any(_CONNECT_FAULT_CAUSES[errno.EBUSY] in m for m in messages)

    def test_property_is_read_only(self):
        stub = _StubTransport()

        with pytest.raises(AttributeError):
            stub.last_failure_cause = 'nope'


class TestDisconnectedStatusLine:
    """The cause reaches the screen without moving the buttons."""

    def _manager(self, cause_callback):
        """A DisplayManager stand-in exposing only what the render uses."""
        from gtach.display.manager import DisplayManager

        rendered = []

        host = types.SimpleNamespace()
        host.logger = __import__('logging').getLogger('test.render')
        host._link_cause_callback = cause_callback
        host._disconnected_btn_setup = None
        host._draw_retry_arc = lambda: None
        host._get_cached_font = lambda size: f'font-{size}'
        host._draw_shift_border = lambda colour: None
        host.rendering_engine = types.SimpleNamespace(
            clear_surface=lambda *a, **k: None,
            render_text=lambda target, text, font, colour, pos, center=False:
                rendered.append((text, pos)),
        )
        host.rendered = rendered
        host._render = DisplayManager._render_disconnected
        return host

    def test_no_line_when_callback_unset(self):
        host = self._manager(None)

        host._render(host)

        texts = [text for text, _ in host.rendered]
        assert texts == ['Disconnected', 'OBD connection not available']

    def test_no_line_when_cause_is_none(self):
        host = self._manager(lambda: None)

        host._render(host)

        texts = [text for text, _ in host.rendered]
        assert texts == ['Disconnected', 'OBD connection not available']

    def test_line_drawn_above_the_button_column(self):
        host = self._manager(lambda: 'no bluetooth controller')

        host._render(host)

        drawn = dict((text, pos) for text, pos in host.rendered)
        assert 'no bluetooth controller' in drawn
        _x, y = drawn['no bluetooth controller']
        # Below the message at y=180, above the column top at 240
        # (_register_disconnected_regions).
        assert 180 < y < 240

    def test_render_error_does_not_escape(self):
        """The screen must still draw when the callback misbehaves."""
        def _boom():
            raise RuntimeError('cause exploded')

        host = self._manager(_boom)

        host._render(host)  # must not raise

    def test_button_geometry_untouched(self):
        import inspect

        from gtach.display.manager import DisplayManager

        source = inspect.getsource(
            DisplayManager._register_disconnected_regions
        )
        assert 'top=240' in source
        assert 'width=240' in source


class TestNoHostActions:
    """The critical constraint: this change reports, it does not act."""

    # Scoped to the files this change edits, matching the prompt's
    # validation wording ("no match INTRODUCED by this change").
    #
    # A repo-wide assertion is not available: gtach.comm.system_bluetooth
    # drives bluetoothctl and hcitool for device DISCOVERY during setup,
    # utils.platform shells out for capability detection, and
    # utils.terminal runs `stty sane`. All predate this change, all are
    # out of its scope, and none is a recovery action.
    EDITED_FILES = (
        'gtach/comm/transport.py',
        'gtach/comm/rfcomm.py',
        'gtach/display/manager.py',
        'gtach/app.py',
    )

    def test_no_shell_or_bluetooth_tooling_introduced(self):
        import pathlib
        import re

        forbidden = re.compile(
            r'subprocess|os\.system|os\.popen|hcitool|hciconfig|btmgmt|rfkill'
        )
        root = pathlib.Path(__file__).resolve().parents[1] / 'src'

        offenders = []
        for relative in self.EDITED_FILES:
            for number, line in enumerate(
                _code_only(root / relative).splitlines(), 1
            ):
                if forbidden.search(line):
                    offenders.append(f'{relative}:{number}: {line.strip()}')

        assert offenders == [], offenders

    def test_no_recovery_action_introduced(self):
        """Reset, cycle, restart and reload must appear nowhere."""
        import pathlib
        import re

        forbidden = re.compile(
            r'hciuart|modprobe|insmod|rmmod|systemctl|reboot', re.IGNORECASE
        )
        root = pathlib.Path(__file__).resolve().parents[1] / 'src'

        offenders = []
        for relative in self.EDITED_FILES:
            for number, line in enumerate(
                _code_only(root / relative).splitlines(), 1
            ):
                if forbidden.search(line):
                    offenders.append(f'{relative}:{number}: {line.strip()}')

        assert offenders == [], offenders

    def test_probe_only_reads_sysfs(self):
        import inspect

        source = inspect.getsource(_bluetooth_adapter_present)
        assert 'os.path.isdir' in source
        assert 'os.listdir' in source
        for verb in ('write', 'system', 'Popen', 'run('):
            assert verb not in source, verb
