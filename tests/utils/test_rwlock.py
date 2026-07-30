#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Unit tests for RWLock notification symmetry, reader concurrency and
writer exclusivity.

Generated from ai/workspace/test/test-1143427b-rwlock-notification-defect.md
per P06 §1.7.3. Covers change-1143427b, which corrects core review §3.1:
RWLock._release_read notified only _write_ready, so a writer blocked in
the second stage of _acquire_write — which waits on _read_ready — was
never woken by a departing reader.

Every blocking assertion is bounded by ACQUIRE_TIMEOUT. A lost wakeup
manifests as a thread that never returns, so an unbounded acquire in a
test would turn a regression into a hung suite with no diagnostic.
Assertions are therefore made on Event.is_set() and Thread.is_alive()
rather than on a call returning.
"""

import ast
import inspect
import textwrap
import threading
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from gtach.utils.config import RWLock

# Kept local rather than imported from conftest so the module is runnable
# in isolation; conftest defines the same value for the wider suite.
ACQUIRE_TIMEOUT = 2.0

CONFIG_SOURCE = (
    Path(__file__).resolve().parents[2] / "src" / "gtach" / "utils" / "config.py"
)


# ---------------------------------------------------------------------------
# Fixtures and helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def lock():
    """A fresh RWLock, asserted drained at teardown."""
    rw = RWLock()
    yield rw
    stats = rw.get_stats()
    assert stats["active_readers"] == 0, "test leaked a reader"
    assert stats["active_writers"] == 0, "test leaked a writer"


def _count_notifications(rw):
    """Wrap both conditions' notify_all so calls can be counted.

    MagicMock(wraps=...) preserves the real behaviour, so the lock stays
    functional while the calls are recorded.
    """
    rw._write_ready.notify_all = MagicMock(wraps=rw._write_ready.notify_all)
    rw._read_ready.notify_all = MagicMock(wraps=rw._read_ready.notify_all)
    return rw._write_ready.notify_all, rw._read_ready.notify_all


class _ReaderInjectingCondition:
    """Proxy for _read_ready that admits a reader as the writer arrives.

    _acquire_write waits on _write_ready in stage one and on _read_ready
    in stage two. Reaching the stage-two wait requires _readers to be zero
    when stage one tests it and non-zero when stage two does — the race
    described in issue-1143427b, in which a reader passes _acquire_read's
    _writers check before the writer increments _writers.

    Rather than override _acquire_write and test a copy of it, this proxy
    increments _readers exactly once, on the first acquisition of
    _read_ready, which is the moment the real _acquire_write enters stage
    two. Everything else delegates to the real condition, so the method
    under test — _release_read — and the writer path are both genuine.
    """

    def __init__(self, real, rw, injected):
        self._real = real
        self._rw = rw
        self._injected = injected

    def __enter__(self):
        if not self._injected.is_set():
            with self._rw._readers_lock:
                self._rw._readers += 1
            self._injected.set()
        return self._real.__enter__()

    def __exit__(self, *exc):
        return self._real.__exit__(*exc)

    def __getattr__(self, name):
        return getattr(self._real, name)


def _method_ast(method):
    """Parse a bound method's source into a FunctionDef node.

    textwrap.dedent, not inspect.cleandoc: the latter is written for
    docstrings and leaves the method body's indentation inconsistent with
    its def line, which ast.parse rejects.
    """
    tree = ast.parse(textwrap.dedent(inspect.getsource(method)))
    return next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))


def _context_names(with_node):
    """The attribute names of a with-statement's context expressions."""
    return [
        item.context_expr.attr
        for item in with_node.items
        if isinstance(item.context_expr, ast.Attribute)
    ]


# ---------------------------------------------------------------------------
# TC-001 — the reported interleaving
# ---------------------------------------------------------------------------


def test_tc001_writer_in_stage_two_is_woken_by_departing_reader(lock):
    """TC-001: a reader entering between the writer's two stages.

    This is the discriminating case. Against the pre-change
    _release_read — which notifies only _write_ready — the writer stays
    blocked on _read_ready and this test times out.
    """
    injected = threading.Event()
    acquired = threading.Event()

    lock._read_ready = _ReaderInjectingCondition(lock._read_ready, lock, injected)

    def writer():
        lock._acquire_write()
        acquired.set()

    thread = threading.Thread(target=writer, daemon=True)
    thread.start()

    # The writer clears stage one (no readers, no writers), increments
    # _writers, then enters stage two — at which point the proxy admits a
    # reader, so stage two observes _readers == 1 and waits.
    assert injected.wait(timeout=ACQUIRE_TIMEOUT), "writer never reached stage two"

    # Give the writer a moment to settle into the wait, then confirm it is
    # genuinely blocked rather than merely slow.
    assert not acquired.wait(timeout=0.2), "writer did not block in stage two"

    # The method under test. The departing reader must wake the writer.
    lock._release_read()

    assert acquired.wait(timeout=ACQUIRE_TIMEOUT), (
        "writer was not woken by the last reader's departure — "
        "_release_read did not notify _read_ready"
    )

    thread.join(timeout=ACQUIRE_TIMEOUT)
    assert not thread.is_alive()

    lock._release_write()


# ---------------------------------------------------------------------------
# TC-002 / TC-003 — notification symmetry and confinement
# ---------------------------------------------------------------------------


def test_tc002_last_reader_notifies_both_conditions(lock):
    """TC-002: the departing final reader signals both conditions."""
    write_notify, read_notify = _count_notifications(lock)

    lock._acquire_read()
    lock._release_read()

    assert write_notify.call_count == 1, "_write_ready not notified"
    assert read_notify.call_count == 1, (
        "_read_ready not notified — this is the defect corrected by change-1143427b"
    )


def test_tc003_non_final_reader_release_notifies_nothing(lock):
    """TC-003: notification is confined to the _readers == 0 branch."""
    write_notify, read_notify = _count_notifications(lock)

    for _ in range(3):
        lock._acquire_read()

    lock._release_read()
    assert (write_notify.call_count, read_notify.call_count) == (0, 0)

    lock._release_read()
    assert (write_notify.call_count, read_notify.call_count) == (0, 0)

    lock._release_read()
    assert (write_notify.call_count, read_notify.call_count) == (1, 1)


# ---------------------------------------------------------------------------
# TC-004 to TC-007 — the lock's defining properties
# ---------------------------------------------------------------------------


def test_tc004_readers_proceed_concurrently(lock):
    """TC-004: the fix must not turn the lock into a mutex.

    A two-party barrier inside the read lock completes only if both
    readers hold it simultaneously; it would time out if reads were
    serialised.
    """
    barrier = threading.Barrier(2, timeout=ACQUIRE_TIMEOUT)
    both_inside = threading.Event()
    failures = []

    def reader():
        try:
            with lock.read_lock():
                barrier.wait()
                both_inside.set()
        except Exception as exc:  # pragma: no cover - failure path
            failures.append(exc)

    threads = [threading.Thread(target=reader, daemon=True) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=ACQUIRE_TIMEOUT)

    assert not failures, f"reader raised: {failures}"
    assert both_inside.is_set(), "readers did not hold the lock concurrently"
    assert all(not t.is_alive() for t in threads)


def test_tc005_writer_excludes_readers(lock):
    """TC-005: a held write lock blocks a reader until released."""
    writer_holding = threading.Event()
    release_writer = threading.Event()
    reader_acquired = threading.Event()

    def writer():
        with lock.write_lock():
            writer_holding.set()
            release_writer.wait(timeout=ACQUIRE_TIMEOUT)

    def reader():
        with lock.read_lock():
            reader_acquired.set()

    wt = threading.Thread(target=writer, daemon=True)
    wt.start()
    assert writer_holding.wait(timeout=ACQUIRE_TIMEOUT)

    rt = threading.Thread(target=reader, daemon=True)
    rt.start()

    assert not reader_acquired.wait(timeout=0.2), "reader entered while a writer held the lock"

    release_writer.set()
    assert reader_acquired.wait(timeout=ACQUIRE_TIMEOUT), "reader never acquired after release"

    for t in (wt, rt):
        t.join(timeout=ACQUIRE_TIMEOUT)
        assert not t.is_alive()


def test_tc006_reader_excludes_writer(lock):
    """TC-006: the simple case of the fix — one reader, one writer."""
    reader_holding = threading.Event()
    release_reader = threading.Event()
    writer_acquired = threading.Event()

    def reader():
        with lock.read_lock():
            reader_holding.set()
            release_reader.wait(timeout=ACQUIRE_TIMEOUT)

    def writer():
        with lock.write_lock():
            writer_acquired.set()

    rt = threading.Thread(target=reader, daemon=True)
    rt.start()
    assert reader_holding.wait(timeout=ACQUIRE_TIMEOUT)

    wt = threading.Thread(target=writer, daemon=True)
    wt.start()

    assert not writer_acquired.wait(timeout=0.2), "writer entered while a reader held the lock"

    release_reader.set()
    assert writer_acquired.wait(timeout=ACQUIRE_TIMEOUT), "writer never acquired after release"

    for t in (rt, wt):
        t.join(timeout=ACQUIRE_TIMEOUT)
        assert not t.is_alive()


def test_tc007_uncontended_acquisition_is_immediate(lock):
    """TC-007: no leak or block in the common uncontended path."""
    with lock.write_lock():
        assert lock.get_stats()["active_writers"] == 1

    with lock.read_lock():
        assert lock.get_stats()["active_readers"] == 1

    stats = lock.get_stats()
    assert stats == {"active_readers": 0, "active_writers": 0}


# ---------------------------------------------------------------------------
# TC-008 — mixed load
# ---------------------------------------------------------------------------


def test_tc008_mixed_reader_writer_load(lock):
    """TC-008: exercises the interleaving stochastically.

    Writers hold exclusive access, so no increment can be lost. A lost
    wakeup would leave a thread blocked and fail the join.
    """
    cycles = 50
    counter = {"value": 0}
    failures = []

    def reader():
        try:
            for _ in range(cycles):
                with lock.read_lock():
                    _ = counter["value"]
        except Exception as exc:  # pragma: no cover - failure path
            failures.append(exc)

    def writer():
        try:
            for _ in range(cycles):
                with lock.write_lock():
                    counter["value"] += 1
        except Exception as exc:  # pragma: no cover - failure path
            failures.append(exc)

    threads = [threading.Thread(target=reader, daemon=True) for _ in range(4)]
    threads += [threading.Thread(target=writer, daemon=True) for _ in range(2)]

    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=ACQUIRE_TIMEOUT * 5)

    assert not failures, f"thread raised: {failures}"
    assert all(not t.is_alive() for t in threads), "a thread blocked — possible lost wakeup"
    assert counter["value"] == cycles * 2, "lost increment under the write lock"


# ---------------------------------------------------------------------------
# TC-009 / TC-010 — structural assertions
# ---------------------------------------------------------------------------


def test_tc009_readers_lock_not_held_while_a_condition_is_acquired():
    """TC-009: the change's second correction.

    The pre-change method nested the _write_ready acquisition inside
    _readers_lock. The two condition blocks must now be siblings, and
    neither may sit inside the _readers_lock block.
    """
    func = _method_ast(RWLock._release_read)
    context_names = _context_names

    readers_lock_blocks = [
        n
        for n in ast.walk(func)
        if isinstance(n, ast.With) and "_readers_lock" in context_names(n)
    ]
    assert len(readers_lock_blocks) == 1, "expected exactly one _readers_lock block"

    nested = [
        n
        for n in ast.walk(readers_lock_blocks[0])
        if isinstance(n, ast.With)
        and set(context_names(n)) & {"_read_ready", "_write_ready"}
    ]
    assert not nested, (
        "a condition variable is acquired while _readers_lock is held; "
        "the decrement and the notifications must be separated"
    )

    condition_blocks = [
        n
        for n in func.body
        if isinstance(n, ast.With) and set(context_names(n)) & {"_read_ready", "_write_ready"}
    ]
    condition_blocks += [
        n
        for stmt in func.body
        if isinstance(stmt, ast.If)
        for n in stmt.body
        if isinstance(n, ast.With) and set(context_names(n)) & {"_read_ready", "_write_ready"}
    ]
    acquired = {name for n in condition_blocks for name in context_names(n)}
    assert acquired == {"_write_ready", "_read_ready"}, (
        f"expected both conditions acquired as siblings, found {acquired}"
    )


def test_tc010_no_other_rwlock_method_changed():
    """TC-010: the change is confined to _release_read.

    _acquire_write's two stages in particular must survive — stage two
    closes a genuine reader-entry window and removing it would reintroduce
    a race.
    """
    expected = {
        "read_lock",
        "write_lock",
        "_acquire_read",
        "_acquire_write",
        "_release_read",
        "_release_write",
        "get_stats",
    }
    assert expected.issubset(set(dir(RWLock))), "an RWLock method is missing"

    func = _method_ast(RWLock._acquire_write)
    stages = [n for n in func.body if isinstance(n, ast.With)]
    assert len(stages) == 2, "_acquire_write must retain both stages"

    contexts = [name for stage in stages for name in _context_names(stage)]
    assert contexts == ["_write_ready", "_read_ready"], (
        f"_acquire_write stage order changed: {contexts}"
    )


# ---------------------------------------------------------------------------
# TC-011 — the consumer is unaffected
# ---------------------------------------------------------------------------


def test_tc011_configmanager_still_guards_its_io_with_the_lock():
    """TC-011: the consumer's use of the lock is unchanged.

    Asserted structurally rather than behaviourally. ConfigManager is a
    process-wide singleton whose construction calls ensure_directories()
    against OBDII_HOME, so a round-trip test writes outside the temporary
    directory unless the home resolver is also isolated. That belongs in
    an integration test, not here; the T05 records the deferral.

    What matters for change-1143427b is that load_config and save_config
    still take the lock this module tests — if they did not, the defect
    would have been confined to dead code.
    """
    source = CONFIG_SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source)

    config_manager = next(
        n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == "ConfigManager"
    )
    methods = {n.name: n for n in config_manager.body if isinstance(n, ast.FunctionDef)}

    for name, expected in (("load_config", {"read_lock", "write_lock"}), ("save_config", {"write_lock"})):
        assert name in methods, f"ConfigManager.{name} is missing"
        used = {
            n.func.attr
            for n in ast.walk(methods[name])
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
        }
        assert used & expected, (
            f"ConfigManager.{name} no longer acquires the reader-writer lock; "
            f"expected one of {sorted(expected)}"
        )

    init = methods.get("__init__")
    assert init is not None
    assigns_rwlock = any(
        isinstance(n, ast.Call)
        and isinstance(n.func, ast.Name)
        and n.func.id == "RWLock"
        for n in ast.walk(init)
    )
    assert assigns_rwlock, "ConfigManager.__init__ no longer constructs an RWLock"
