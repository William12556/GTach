#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""SimTransport lifecycle: start, link loss, reconnect, shutdown.

audit-36b6ea95 Phase 4 (F01). Runs the real ThreadManager, SimTransport,
OBDProtocol and WatchdogMonitor together, wired as app.py wires them: a
'transport' thread running reconnect_indefinitely with
stop_func=transport.disconnect, and the OBD protocol thread. Every wait
is bounded.
"""

import importlib.util
import logging
import os
import queue
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from gtach.comm.obd import OBDProtocol
from gtach.comm.sim_transport import SimTransport
from gtach.core.thread import ThreadManager
from gtach.core.watchdog import WatchdogMonitor

RETRY_DELAY_S = 0.2
POLL_INTERVAL_S = 0.02
SAMPLE_WAIT_S = 3.0
STOP_TIMEOUT_S = 2.0


class _Harness:
    """The app.py wiring of transport and OBD protocol threads."""

    def __init__(self):
        self.thread_manager = ThreadManager()
        self.transport = SimTransport()
        self.transport_thread = threading.Thread(
            target=self.transport.reconnect_indefinitely,
            kwargs={
                "retry_delay": RETRY_DELAY_S,
                "heartbeat": lambda: self.thread_manager.update_heartbeat("transport"),
            },
            name="transport",
            daemon=True,
        )
        self.thread_manager.register_thread(
            "transport", self.transport_thread, stop_func=self.transport.disconnect
        )
        self.obd = OBDProtocol(
            self.transport,
            self.thread_manager,
            poll_interval_s=POLL_INTERVAL_S,
            adapter_pre_initialised=True,
        )

    def start(self):
        self.transport_thread.start()
        self.obd.start()

    def stop(self):
        """Stop as _re_enter_setup does: transport, then obd_protocol."""
        stopped = (
            self.thread_manager.stop_thread("transport", timeout=STOP_TIMEOUT_S),
            self.thread_manager.stop_thread("obd_protocol", timeout=STOP_TIMEOUT_S),
        )
        return stopped

    def wait_for_samples(self, count, timeout=SAMPLE_WAIT_S):
        """Drain the message queue until count samples arrive or timeout."""
        received = 0
        deadline = time.monotonic() + timeout
        while received < count and time.monotonic() < deadline:
            try:
                self.thread_manager.message_queue.get(timeout=0.05)
                received += 1
            except queue.Empty:
                pass
        return received

    def drain(self):
        while True:
            try:
                self.thread_manager.message_queue.get_nowait()
            except queue.Empty:
                return


@pytest.fixture
def harness():
    h = _Harness()
    h.start()
    yield h
    h.stop()
    h.thread_manager.shutdown(timeout=5.0)


def _wait_until(predicate, timeout):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return predicate()


class TestStart:

    def test_samples_arrive(self, harness):
        assert harness.wait_for_samples(5) >= 5


class TestLinkLoss:

    def test_drop_is_observed_and_link_reconnects(self, harness):
        assert harness.wait_for_samples(5) >= 5

        harness.transport.drop_link()

        assert harness.transport.is_connected() is False
        assert _wait_until(harness.transport.is_connected, SAMPLE_WAIT_S)
        harness.drain()
        assert harness.wait_for_samples(5) >= 5

    def test_samples_flow_after_drop_link(self, harness):
        assert harness.wait_for_samples(5) >= 5

        harness.transport.drop_link()

        assert _wait_until(harness.transport.is_connected, SAMPLE_WAIT_S)
        harness.drain()
        assert harness.wait_for_samples(5) >= 5


class TestHeartbeatBound:

    def test_largest_obd_gap_below_two_seconds(self, harness):
        info = harness.thread_manager.threads["obd_protocol"]
        stamps = []
        start = time.monotonic()
        dropped = False
        while time.monotonic() - start < 3.0:
            stamps.append(info.last_heartbeat)
            harness.drain()
            if not dropped and time.monotonic() - start > 1.5:
                harness.transport.drop_link()
                dropped = True
            time.sleep(0.05)
        stamps.append(time.monotonic())  # the gap still open at the end

        gaps = [b - a for a, b in zip(stamps, stamps[1:]) if b != a]
        # Distinct heartbeat values: the gap is between successive ones.
        distinct = sorted(set(stamps))
        largest = max(b - a for a, b in zip(distinct, distinct[1:]))
        assert gaps
        assert largest < 2.0, largest


@pytest.fixture
def watchdog_run(harness, caplog):
    """Scenarios 1-2 for 4 s under a fast WatchdogMonitor."""
    calls = []
    watchdog = WatchdogMonitor(
        harness.thread_manager,
        check_interval=0.2,
        warning_timeout=1.0,
        recovery_timeout=2.0,
        critical_timeout=3.0,
        shutdown_callback=lambda: calls.append("shutdown"),
    )
    with caplog.at_level(logging.WARNING, logger="WatchdogMonitor"):
        watchdog.start()
        try:
            start = time.monotonic()
            assert harness.wait_for_samples(5) >= 5
            harness.transport.drop_link()
            while time.monotonic() - start < 4.0:
                harness.drain()
                time.sleep(0.05)
        finally:
            watchdog.stop()
    obd_warnings = [
        r
        for r in caplog.records
        if "obd_protocol" in r.getMessage() and "unresponsive" in r.getMessage()
    ]
    return calls, obd_warnings


class TestWatchdogQuiet:

    def test_no_shutdown(self, watchdog_run):
        calls, _ = watchdog_run
        assert calls == []

    def test_no_obd_unresponsive_warning(self, watchdog_run):
        _, obd_warnings = watchdog_run
        assert obd_warnings == []


class TestShutdown:

    def test_orderly_stop(self, harness):
        assert harness.wait_for_samples(5) >= 5

        assert harness.stop() == (True, True)
        assert not harness.transport_thread.is_alive()
        assert not harness.obd.obd_thread.is_alive()

        start = time.monotonic()
        harness.thread_manager.shutdown(timeout=5.0)
        assert time.monotonic() - start < 5.0

    def test_stop_while_reconnecting(self, harness):
        assert harness.wait_for_samples(5) >= 5
        harness.transport.drop_link()

        start = time.monotonic()
        harness.stop()
        harness.transport_thread.join(STOP_TIMEOUT_S)
        harness.obd.obd_thread.join(STOP_TIMEOUT_S)

        assert not harness.transport_thread.is_alive()
        assert not harness.obd.obd_thread.is_alive()
        assert time.monotonic() - start < 2.0 * STOP_TIMEOUT_S


@pytest.mark.skipif(
    importlib.util.find_spec("pygame") is None or Path("/opt/gtach").exists(),
    reason="needs pygame, and must not run where /opt/gtach exists",
)
class TestProcessExit:

    def test_sigterm_ends_simtcp_process(self, tmp_path):
        env = dict(os.environ, SDL_VIDEODRIVER="dummy", GTACH_HOME=str(tmp_path))
        proc = subprocess.Popen(
            [sys.executable, "-m", "gtach", "--transport", "simtcp"],
            cwd=tmp_path,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            time.sleep(3.0)
            assert proc.poll() is None, "process exited before SIGTERM"
            proc.send_signal(signal.SIGTERM)
            assert proc.wait(timeout=10.0) is not None
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait(timeout=5.0)
