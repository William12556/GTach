#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Detecting a dead link and reconnecting for the life of the process.

Covers change-9c2f41d8. A read timeout left the transport reporting
connected against a dead peer, so OBDProtocol polled a closed-at-the-far-
end socket at ~1 Hz indefinitely, and reconnect_indefinitely was never
re-entered because its only two call sites were at startup in threads
that returned on first success.

The load-bearing distinction under test is drop_link versus disconnect.
disconnect() sets _shutdown, which reconnect_indefinitely loops on and
which nothing ever clears; using it to tear down a dead link would
permanently disable reconnection while still passing any check that
merely asserts the transport went not-connected. Several tests below
assert _shutdown is NOT set for exactly that reason.
"""

import threading
import time

import pytest

from gtach.comm.transport import OBDTransport, TransportState

# Bound on every blocking assertion. A regression in the supervising
# loop manifests as a thread that never returns, so an unbounded wait
# would turn a failure into a hung run with no diagnostic.
JOIN_TIMEOUT = 5.0


class _StubTimeout(Exception):
    """Stands in for a transport-specific read timeout."""


class _StubTransport(OBDTransport):
    """A transport whose I/O primitives are scripted.

    _TIMEOUT_ERRORS is overridden so the timeout branch can be driven
    without a real socket. The four handle primitives are supplied
    because send_command exercises the whole skeleton.
    """

    _TIMEOUT_ERRORS = (_StubTimeout,)
    _IO_ERRORS = (OSError,)

    def __init__(self, reads=None):
        super().__init__()
        # Each entry is either the bytes to return or an exception
        # instance to raise from _read.
        self._reads = list(reads or [])
        self.closed_handles = []
        self.connect_calls = 0

    def _describe(self) -> str:
        return 'stub-peer'

    def _open(self):
        self.connect_calls += 1
        return object()

    def _close(self, handle) -> None:
        self.closed_handles.append(handle)

    def _write(self, handle, data) -> None:
        pass

    def _set_timeout(self, handle, timeout) -> None:
        pass

    def _read(self, handle, size):
        if not self._reads:
            raise _StubTimeout('no script left')
        item = self._reads.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def _executable_lines(func):
    """Source lines of func with the docstring and comments removed.

    Source-level assertions below describe the CODE. The docstrings
    legitimately name _shutdown and time.sleep while explaining what
    the code deliberately does not do, and must stay free to.
    """
    import ast
    import inspect
    import textwrap

    source = textwrap.dedent(inspect.getsource(func))
    tree = ast.parse(source).body[0]
    if (tree.body and isinstance(tree.body[0], ast.Expr)
            and isinstance(tree.body[0].value, ast.Constant)
            and isinstance(tree.body[0].value.value, str)):
        body = tree.body[1:]
    else:
        body = tree.body

    lines = source.splitlines()
    start = body[0].lineno - 1
    return [line for line in lines[start:]
            if line.strip() and not line.lstrip().startswith('#')]


def _timeouts(n):
    return [_StubTimeout('silent') for _ in range(n)]


def _ok():
    return b'41 0C 1A F8>'


@pytest.fixture
def transport():
    return _StubTransport()


class TestTimeoutThreshold:
    """Consecutive silences drop the link; any answer resets the count."""

    def test_threshold_is_five(self):
        assert OBDTransport._MAX_CONSECUTIVE_TIMEOUTS == 5

    def test_counter_starts_at_zero(self, transport):
        assert transport._consecutive_timeouts == 0

    def test_four_timeouts_then_success_does_not_drop(self, transport, monkeypatch):
        drops = []
        monkeypatch.setattr(transport, 'drop_link', lambda: drops.append(1))
        transport._reads = _timeouts(4) + [_ok()]
        transport.connect()

        for _ in range(4):
            assert transport.send_command('010C') is None
        assert transport.send_command('010C') is not None

        assert drops == []
        assert transport._consecutive_timeouts == 0

    def test_five_timeouts_drops_the_link(self, transport, caplog):
        transport._reads = _timeouts(5)
        transport.connect()
        assert transport.is_connected() is True

        with caplog.at_level('ERROR'):
            for _ in range(5):
                assert transport.send_command('010C') is None

        assert transport.is_connected() is False
        assert any('dropping link' in r.message or 'dropping link' in r.getMessage()
                   for r in caplog.records)
        # The load-bearing assertion: reconnection must remain possible.
        assert transport._shutdown.is_set() is False

    def test_three_one_three_does_not_drop(self, transport, monkeypatch):
        drops = []
        monkeypatch.setattr(transport, 'drop_link', lambda: drops.append(1))
        transport._reads = _timeouts(3) + [_ok()] + _timeouts(3)
        transport.connect()

        for _ in range(7):
            transport.send_command('010C')

        assert drops == []

    def test_six_timeouts_drop_once_not_twice(self, transport, monkeypatch):
        drops = []
        monkeypatch.setattr(transport, 'drop_link', lambda: drops.append(1))
        transport._reads = _timeouts(6)
        transport.connect()

        for _ in range(6):
            transport.send_command('010C')

        assert drops == [1]
        assert transport._consecutive_timeouts == 1

    def test_timeout_branch_precedes_io_branch(self):
        """socket.timeout is an OSError subclass; order is load-bearing."""
        import inspect

        source = inspect.getsource(OBDTransport.send_command)
        assert (source.index('except self._TIMEOUT_ERRORS')
                < source.index('except self._IO_ERRORS'))

    def test_success_resets_the_counter(self, transport):
        transport._reads = _timeouts(2) + [_ok()]
        transport.connect()

        transport.send_command('010C')
        transport.send_command('010C')
        assert transport._consecutive_timeouts == 2

        transport.send_command('010C')
        assert transport._consecutive_timeouts == 0


class TestDropLinkVersusDisconnect:
    """drop_link must never do what disconnect does."""

    def test_drop_link_closes_the_handle_without_shutdown(self, transport):
        transport.connect()
        handle = transport._handle

        transport.drop_link()

        assert transport.closed_handles == [handle]
        assert transport._state is TransportState.DISCONNECTED
        assert transport._shutdown.is_set() is False

    def test_drop_link_when_already_disconnected(self, transport):
        transport.drop_link()

        assert transport._state is TransportState.DISCONNECTED
        assert transport._shutdown.is_set() is False

    def test_disconnect_still_sets_shutdown(self, transport):
        transport.connect()

        transport.disconnect()

        assert transport._shutdown.is_set() is True
        assert transport._state is TransportState.DISCONNECTED

    def test_drop_link_source_never_touches_shutdown(self):
        """The docstring names _shutdown; the body must not touch it."""
        code = '\n'.join(_executable_lines(OBDTransport.drop_link))

        assert '_shutdown' not in code


class TestSupervisingLoop:
    """reconnect_indefinitely returns only when _shutdown is set."""

    def _run(self, transport, **kwargs):
        thread = threading.Thread(
            target=transport.reconnect_indefinitely,
            kwargs=kwargs, daemon=True,
        )
        thread.start()
        return thread

    def test_does_not_return_on_successful_connect(self, transport):
        thread = self._run(transport, retry_delay=0.05)

        deadline = time.time() + JOIN_TIMEOUT
        while not transport.is_connected() and time.time() < deadline:
            time.sleep(0.01)
        assert transport.is_connected() is True

        thread.join(timeout=0.3)
        assert thread.is_alive() is True, 'returned on a successful connect'

        transport.disconnect()
        thread.join(timeout=JOIN_TIMEOUT)
        assert thread.is_alive() is False

    def test_reconnects_after_a_drop(self, transport):
        """Drop from another thread; the loop must connect a second time."""
        thread = self._run(transport, retry_delay=0.05)

        deadline = time.time() + JOIN_TIMEOUT
        while transport.connect_calls < 1 and time.time() < deadline:
            time.sleep(0.01)

        transport.drop_link()

        while transport.connect_calls < 2 and time.time() < deadline:
            time.sleep(0.01)
        assert transport.connect_calls >= 2

        assert thread.is_alive() is True, 'returned between the two connects'

        transport.disconnect()
        thread.join(timeout=JOIN_TIMEOUT)
        assert thread.is_alive() is False

    def test_shutdown_while_connected_returns_promptly(self, transport):
        """Without waiting out retry_delay."""
        thread = self._run(transport, retry_delay=30.0)

        deadline = time.time() + JOIN_TIMEOUT
        while not transport.is_connected() and time.time() < deadline:
            time.sleep(0.01)

        started = time.time()
        transport.disconnect()
        thread.join(timeout=JOIN_TIMEOUT)

        assert thread.is_alive() is False
        assert time.time() - started < 3.0

    def test_shutdown_while_retrying_returns_promptly(self, monkeypatch):
        stub = _StubTransport()
        monkeypatch.setattr(stub, '_open', lambda: None)
        thread = self._run(stub, retry_delay=30.0)

        time.sleep(0.1)
        assert stub.is_connected() is False

        started = time.time()
        stub.disconnect()
        thread.join(timeout=JOIN_TIMEOUT)

        assert thread.is_alive() is False
        assert time.time() - started < 3.0

    def test_no_return_reachable_while_shutdown_is_unset(self):
        """Every return in the loop must be guarded by a _shutdown test."""
        lines = _executable_lines(OBDTransport.reconnect_indefinitely)

        returns = [i for i, line in enumerate(lines)
                   if line.strip() == 'return']
        # Two: the heartbeat helper's guard on `heartbeat is None`, and
        # the loop's own exit.
        assert len(returns) == 2, [lines[i] for i in returns]

        guard = lines[returns[-1] - 1].strip()
        assert guard == 'if self._shutdown.is_set():', guard

    def test_every_wait_is_on_shutdown(self):
        code = '\n'.join(_executable_lines(OBDTransport.reconnect_indefinitely))

        assert 'time.sleep' not in code
        # Supervising poll, post-drop delay, failed-connect delay.
        assert code.count('self._shutdown.wait(') == 3

    def test_signature_is_unchanged(self):
        import inspect

        params = inspect.signature(
            OBDTransport.reconnect_indefinitely
        ).parameters
        assert list(params) == ['self', 'retry_delay', 'heartbeat']
        assert params['retry_delay'].default == 5.0
        assert params['heartbeat'].default is None


class TestSupervisingLoopHeartbeat:
    """Liveness must be reported in both phases."""

    def test_beats_while_connected_and_while_retrying(self, monkeypatch):
        stub = _StubTransport()
        beats = []

        # Fail the first connect, succeed the second, so both phases
        # are exercised in one run.
        outcomes = [None, object()]

        def _open():
            stub.connect_calls += 1
            result = outcomes.pop(0) if outcomes else object()
            return result

        monkeypatch.setattr(stub, '_open', _open)

        thread = threading.Thread(
            target=stub.reconnect_indefinitely,
            kwargs={'retry_delay': 0.05,
                    'heartbeat': lambda: beats.append(stub.is_connected())},
            daemon=True,
        )
        thread.start()

        deadline = time.time() + JOIN_TIMEOUT
        while not (any(beats) and not all(beats)) and time.time() < deadline:
            time.sleep(0.01)

        stub.disconnect()
        thread.join(timeout=JOIN_TIMEOUT)

        assert any(b is False for b in beats), 'no beat while retrying'
        assert any(b is True for b in beats), 'no beat while connected'

    def test_raising_heartbeat_does_not_break_the_loop(self, transport):
        calls = []

        def _boom():
            calls.append(1)
            raise RuntimeError('heartbeat exploded')

        thread = threading.Thread(
            target=transport.reconnect_indefinitely,
            kwargs={'retry_delay': 0.05, 'heartbeat': _boom},
            daemon=True,
        )
        thread.start()

        deadline = time.time() + JOIN_TIMEOUT
        while len(calls) < 3 and time.time() < deadline:
            time.sleep(0.01)

        assert len(calls) >= 3
        assert thread.is_alive() is True

        transport.disconnect()
        thread.join(timeout=JOIN_TIMEOUT)
        assert thread.is_alive() is False

    def test_no_heartbeat_argument(self, transport):
        thread = threading.Thread(
            target=transport.reconnect_indefinitely,
            kwargs={'retry_delay': 0.05}, daemon=True,
        )
        thread.start()

        deadline = time.time() + JOIN_TIMEOUT
        while not transport.is_connected() and time.time() < deadline:
            time.sleep(0.01)
        assert transport.is_connected() is True

        transport.disconnect()
        thread.join(timeout=JOIN_TIMEOUT)
        assert thread.is_alive() is False


class TestNoBusySpin:
    """A link that drops immediately must not spin the loop."""

    def test_repeated_instant_drops_are_rate_limited(self, monkeypatch):
        stub = _StubTransport()

        def _open():
            stub.connect_calls += 1
            # Connect, then drop before the supervisor can observe it.
            threading.Timer(0.0, stub.drop_link).start()
            return object()

        monkeypatch.setattr(stub, '_open', _open)

        thread = threading.Thread(
            target=stub.reconnect_indefinitely,
            kwargs={'retry_delay': 0.2}, daemon=True,
        )
        thread.start()

        time.sleep(0.6)
        stub.disconnect()
        thread.join(timeout=JOIN_TIMEOUT)

        # At 0.2 s per cycle, 0.6 s admits a handful of attempts. A
        # busy-spin would produce hundreds.
        assert stub.connect_calls <= 10, stub.connect_calls
        assert thread.is_alive() is False
