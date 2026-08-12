#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""The heartbeat hook on OBDTransport.reconnect_indefinitely.

Covers change-2ac1c602: the reconnect loop must be able to report
liveness to a monitor without that report ever being able to stop it
reconnecting, and must behave exactly as before when no hook is given.
"""

import inspect

from gtach.comm.transport import OBDTransport


class _StubTransport(OBDTransport):
    """A transport whose connect() returns a scripted sequence.

    Only the reconnect skeleton is under test, so the four handle
    primitives are never reached and are not supplied.
    """

    def __init__(self, results):
        super().__init__()
        self._results = list(results)
        self.connect_calls = 0

    def connect(self) -> bool:
        self.connect_calls += 1
        if self._results:
            return self._results.pop(0)
        # Never leave the loop unbounded if the script runs dry.
        self._shutdown.set()
        return False


class TestHeartbeatHook:
    """heartbeat is optional, invoked per iteration, and fully guarded."""

    def test_signature_defaults_to_none(self):
        parameter = inspect.signature(
            OBDTransport.reconnect_indefinitely
        ).parameters['heartbeat']
        assert parameter.default is None

    def test_invoked_on_both_iterations(self):
        """One failed connect then a successful one."""
        transport = _StubTransport([False, True])
        beats = []

        transport.reconnect_indefinitely(
            retry_delay=0.01, heartbeat=lambda: beats.append(transport.connect_calls)
        )

        assert transport.connect_calls == 2
        # At least one beat attributable to each iteration: beats
        # recorded before the first connect (0) and after the second (2).
        assert 0 in beats and 2 in beats
        assert len(set(beats)) >= 2

    def test_raising_heartbeat_does_not_break_the_loop(self):
        """A faulty observer degrades diagnostics, not reconnection."""
        transport = _StubTransport([False, True])
        calls = []

        def _boom():
            calls.append(1)
            raise RuntimeError('heartbeat exploded')

        transport.reconnect_indefinitely(retry_delay=0.01, heartbeat=_boom)

        assert transport.connect_calls == 2
        assert len(calls) >= 2

    def test_no_heartbeat_argument_behaves_as_before(self):
        transport = _StubTransport([False, True])

        transport.reconnect_indefinitely(retry_delay=0.01)

        assert transport.connect_calls == 2

    def test_shutdown_before_entry_skips_the_loop(self):
        transport = _StubTransport([True])
        transport._shutdown.set()
        beats = []

        transport.reconnect_indefinitely(retry_delay=0.01, heartbeat=lambda: beats.append(1))

        assert transport.connect_calls == 0
        assert beats == []
