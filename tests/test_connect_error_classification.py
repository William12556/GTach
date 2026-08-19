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
    _SILENT_LINK_CAUSE,
    _WEDGED_LINK_CAUSE,
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

    @pytest.fixture(autouse=True)
    def _stub_fonts(self, monkeypatch):
        """Stub the font accessors _render_disconnected calls.

        The render obtains fonts from FontManager directly since
        change-ba672e81 removed DisplayManager._get_cached_font(), so
        the stub lives on the module rather than on the host object.
        """
        import gtach.display.manager as manager_module

        monkeypatch.setattr(
            manager_module, 'get_font_manager',
            lambda: types.SimpleNamespace(get_font=lambda size: f'font-{size}')
        )
        monkeypatch.setattr(manager_module, 'get_title_display_font',
                            lambda: 'font-36')
        monkeypatch.setattr(manager_module, 'get_label_small_font',
                            lambda: 'font-18')

    def _manager(self, cause_callback):
        """A DisplayManager stand-in exposing only what the render uses."""
        from gtach.display.manager import DisplayManager

        rendered = []

        host = types.SimpleNamespace()
        host.logger = __import__('logging').getLogger('test.render')
        host._link_cause_callback = cause_callback
        host._disconnected_btn_setup = None
        host._DISCONNECTED_BG_COLOUR = DisplayManager._DISCONNECTED_BG_COLOUR
        host._DISCONNECTED_TEXT_COLOUR = DisplayManager._DISCONNECTED_TEXT_COLOUR
        host._draw_status_indicator = lambda: None
        host._draw_reconnect_spinner = lambda: None
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

    # The one sanctioned host action, and the only exemption from the
    # scan below. change-4ab5ff88 replaced the DISCONNECTED screen's
    # Bluetooth Reset button with a Reset button that reboots the Pi;
    # the dispatch lives in app.py and reaches the host only through
    # utils.pi_reset, on an operator press. It is not automatic, and no
    # comm-layer diagnosis can reach it — which is the property
    # change-5e7a03c4 exists to protect. Matched as a whole line so
    # that any OTHER reboot reference in these files still fails.
    SANCTIONED = ('outcome = pi_reset.reboot_device()',)

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
                if line.strip() in self.SANCTIONED:
                    continue
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


# ---------------------------------------------------------------------
# change-5e7a03c4 iteration 2: a cause on link drop, and escalation to a
# wedge diagnosis after sustained connect failure. Everything above this
# line is iteration 1's and is unmodified.
# ---------------------------------------------------------------------


class TestDropLinkRecordsACause:
    """A link torn down for silence must explain itself too."""

    def test_default_cause_on_a_connected_transport(self, adapter_present):
        stub = _StubTransport()
        assert stub.connect() is True

        stub.drop_link()

        assert stub.last_failure_cause == _SILENT_LINK_CAUSE
        assert stub.state is TransportState.DISCONNECTED
        # Still the load-bearing assertion from iteration 1:
        # reconnection must remain possible.
        assert stub._shutdown.is_set() is False

    def test_explicit_cause_is_used(self):
        stub = _StubTransport()

        stub.drop_link('custom reason')

        assert stub.last_failure_cause == 'custom reason'

    def test_no_argument_call_sites_still_work(self):
        """Both existing callers pass nothing."""
        import inspect

        parameter = inspect.signature(OBDTransport.drop_link).parameters['cause']
        assert parameter.default is None

        stub = _StubTransport()
        stub.drop_link()  # must not raise

        assert stub.last_failure_cause == _SILENT_LINK_CAUSE

    def test_when_already_disconnected(self):
        stub = _StubTransport()

        stub.drop_link()
        stub.drop_link()

        assert stub.last_failure_cause == _SILENT_LINK_CAUSE
        assert stub._shutdown.is_set() is False

    def test_single_lock_acquisition(self):
        """The cause is set in the existing block, not a second one."""
        import inspect

        source = inspect.getsource(OBDTransport.drop_link)
        assert source.count('with self._lock:') == 1

    def test_still_never_touches_shutdown(self):
        code = '\n'.join(
            line for line in inspect_source_body(OBDTransport.drop_link)
        )
        assert '_shutdown' not in code


def inspect_source_body(func):
    """Executable lines of func, docstring and comments removed."""
    import ast
    import inspect
    import textwrap

    source = textwrap.dedent(inspect.getsource(func))
    tree = ast.parse(source).body[0]
    if (tree.body and isinstance(tree.body[0], ast.Expr)
            and isinstance(tree.body[0].value, ast.Constant)
            and isinstance(tree.body[0].value.value, str)):
        first = tree.body[1]
    else:
        first = tree.body[0]
    lines = source.splitlines()[first.lineno - 1:]
    return [line for line in lines
            if line.strip() and not line.lstrip().startswith('#')]


class TestWedgeEscalation:
    """Persistence is the only signal a wedged controller gives."""

    def _fail(self, stub, times, code=errno.EBUSY):
        for _ in range(times):
            stub._outcome = OSError(code, 'Device or resource busy')
            assert stub.connect() is False

    def test_threshold_constant(self):
        assert OBDTransport._MAX_CONSECUTIVE_CONNECT_FAILURES == 6

    def test_counter_starts_at_zero(self):
        assert _StubTransport()._consecutive_connect_failures == 0

    def test_five_failures_do_not_escalate(self, adapter_present):
        stub = _StubTransport()

        self._fail(stub, 5)

        assert stub.last_failure_cause == _CONNECT_FAULT_CAUSES[errno.EBUSY]

    def test_six_failures_escalate(self, adapter_present):
        stub = _StubTransport()

        self._fail(stub, 6)

        assert stub.last_failure_cause == _WEDGED_LINK_CAUSE

    def test_counter_latches_beyond_the_threshold(self, adapter_present):
        """Crossing must not reset it; the condition persists."""
        stub = _StubTransport()

        self._fail(stub, 8)

        assert stub.last_failure_cause == _WEDGED_LINK_CAUSE
        assert stub._consecutive_connect_failures == 8

    def test_absent_adapter_is_not_masked(self, adapter_absent):
        """The more specific fact wins over the wedge diagnosis."""
        stub = _StubTransport()

        self._fail(stub, 6)

        assert stub.last_failure_cause == 'no bluetooth controller'

    def test_adapter_becoming_absent_mid_run(self, monkeypatch):
        """The absent-controller cause wins from that point."""
        stub = _StubTransport()
        present = [True]
        monkeypatch.setattr(
            transport_module, '_bluetooth_adapter_present',
            lambda: present[0]
        )

        self._fail(stub, 6)
        assert stub.last_failure_cause == _WEDGED_LINK_CAUSE

        present[0] = False
        self._fail(stub, 1)

        assert stub.last_failure_cause == 'no bluetooth controller'

    def test_success_resets_the_counter(self, adapter_present):
        stub = _StubTransport()

        self._fail(stub, 5)
        stub._outcome = object()
        assert stub.connect() is True
        self._fail(stub, 5)

        assert stub.last_failure_cause == _CONNECT_FAULT_CAUSES[errno.EBUSY]

    def test_success_clears_cause_and_counter(self, adapter_present):
        stub = _StubTransport()

        self._fail(stub, 8)
        assert stub.last_failure_cause == _WEDGED_LINK_CAUSE

        stub._outcome = object()
        assert stub.connect() is True

        assert stub.last_failure_cause is None
        assert stub._consecutive_connect_failures == 0


class TestCountersAreIndependent:
    """Read timeouts and connect failures count different events."""

    def test_read_timeouts_do_not_touch_the_connect_counter(self, adapter_present):
        class _TimeoutStub(_StubTransport):
            _TIMEOUT_ERRORS = (TimeoutError,)

            def _open(self):
                return object()

            def _write(self, handle, data):
                pass

            def _set_timeout(self, handle, timeout):
                pass

            def _read(self, handle, size):
                raise TimeoutError('silent')

        stub = _TimeoutStub()
        assert stub.connect() is True

        drops = []
        original = stub.drop_link
        stub.drop_link = lambda cause=None: (drops.append(cause),
                                             original(cause))[1]

        for _ in range(OBDTransport._MAX_CONSECUTIVE_TIMEOUTS):
            assert stub.send_command('010C') is None

        assert len(drops) == 1
        assert stub._consecutive_connect_failures == 0

    def test_attributes_are_distinct(self):
        stub = _StubTransport()

        stub._consecutive_timeouts = 3
        stub._consecutive_connect_failures = 7

        assert stub._consecutive_timeouts == 3
        assert stub._consecutive_connect_failures == 7

    def test_timeout_threshold_unchanged(self):
        assert OBDTransport._MAX_CONSECUTIVE_TIMEOUTS == 5


class TestSuffixSuppression:
    """Stop emitting 'timed out (timed out)'."""

    def test_no_suffix_when_the_cause_duplicates_the_exception(
            self, adapter_present, caplog):
        # An errno-less exception: _classify_connect_error falls through
        # to str(exc), so cause == str(e).
        stub = _StubTransport(OSError('timed out'))

        with caplog.at_level('ERROR'):
            assert stub.connect() is False

        messages = [r.getMessage() for r in caplog.records]
        assert any(m == 'Failed to connect to stub-peer: timed out'
                   for m in messages), messages
        assert not any('(timed out)' in m for m in messages)
        # The cause is still recorded — the display has no other source.
        assert stub.last_failure_cause == 'timed out'

    def test_suffix_present_when_the_cause_adds_information(
            self, adapter_present, caplog):
        stub = _StubTransport(OSError(errno.EBUSY, 'Device or resource busy'))

        with caplog.at_level('ERROR'):
            assert stub.connect() is False

        messages = [r.getMessage() for r in caplog.records]
        expected = _CONNECT_FAULT_CAUSES[errno.EBUSY]
        assert any(f'({expected})' in m for m in messages), messages


class TestEveryCauseFitsTheDisplay:
    """480x480 leaves no room for a long line."""

    def test_all_causes_within_forty_characters(self):
        for text in (
            list(_CONNECT_FAULT_CAUSES.values())
            + [_SILENT_LINK_CAUSE, _WEDGED_LINK_CAUSE]
        ):
            assert len(text) <= 40, (text, len(text))
            assert text == text.strip()
            assert text
