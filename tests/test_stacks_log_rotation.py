#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""stacks.log run headers and once-per-process rotation.

Covers change-3b8c50f2. faulthandler's dumps carry no timestamp, PID or
run identifier, so dumps from successive process lifetimes concatenate
indistinguishably — worst in the very scenario the file exists for, a
watchdog-triggered restart. Every arm now writes an identifying header,
and the first arm of a process rotates the previous run's file.

Both additions are deliberately arming-time only: nothing here runs on
a timer, because a Python-side timer would stall in exactly the window
this file exists to capture.

As in tests/test_stack_dump_toggle.py, faulthandler is replaced by a
recording double and the module is fetched from sys.modules rather than
imported — gtach/__init__.py re-exports the main FUNCTION under the name
'main', so `from gtach import main` yields the function, whose namespace
has none of this module state (issue-c1d4b8e6).
"""

import os
import re
import sys
import types

import pytest

import gtach.main  # noqa: F401  — ensures the module is in sys.modules

gtach_main = sys.modules['gtach.main']

HEADER_RE = re.compile(r'^=== gtach \S+ pid (\d+) armed '
                       r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2} ===$')


class _FakeFaulthandler:
    """Records calls in order; performs no real arming."""

    def __init__(self):
        self.calls = []

    def enable(self, file=None):
        self.calls.append('enable')

    def disable(self):
        self.calls.append('disable')

    def dump_traceback_later(self, timeout, repeat=False, file=None):
        self.calls.append('dump_traceback_later')

    def cancel_dump_traceback_later(self):
        self.calls.append('cancel_dump_traceback_later')


@pytest.fixture
def armed(tmp_path, monkeypatch):
    """A disarmed, unrotated module pointed at a temporary log path."""
    fake = _FakeFaulthandler()
    monkeypatch.setattr(gtach_main, 'faulthandler', fake)
    monkeypatch.setattr(gtach_main, '_stacks_file', None)
    monkeypatch.setattr(gtach_main, '_stacks_rotated', False)
    path = tmp_path / 'stacks.log'
    monkeypatch.setattr(gtach_main, '_STACKS_LOG', str(path))

    yield types.SimpleNamespace(fake=fake, path=path, tmp=tmp_path)

    # Module-level state: reset regardless of what the test did with it.
    stacks = gtach_main._stacks_file
    if stacks is not None:
        try:
            stacks.close()
        except Exception:
            pass
    gtach_main._stacks_file = None
    gtach_main._stacks_rotated = False


def _generation(env, n):
    """Path of backup generation n."""
    return env.tmp / f'stacks.log.{n}'


def _headers(path):
    return [line for line in path.read_text().splitlines()
            if line.startswith('=== gtach ')]


class TestHeader:
    """Every arm writes exactly one identifying line, before arming."""

    def test_first_arm_writes_a_header_with_this_pid(self, armed):
        assert gtach_main.enable_stack_dumps() is True

        first_line = armed.path.read_text().splitlines()[0]
        match = HEADER_RE.match(first_line)
        assert match is not None, first_line
        assert int(match.group(1)) == os.getpid()

    def test_no_rotation_when_nothing_pre_existed(self, armed):
        gtach_main.enable_stack_dumps()

        assert armed.path.exists()
        assert not _generation(armed, 1).exists()

    def test_header_precedes_arming(self, armed, monkeypatch):
        """No dump may be written above the header identifying it."""
        order = []

        real_header = gtach_main._stacks_header

        def _tracking_header():
            order.append('header')
            return real_header()

        monkeypatch.setattr(gtach_main, '_stacks_header', _tracking_header)
        monkeypatch.setattr(
            armed.fake, 'dump_traceback_later',
            lambda *a, **k: order.append('arm')
        )

        gtach_main.enable_stack_dumps()

        assert order == ['header', 'arm']

    def test_version_failure_still_emits_a_header(self, armed, monkeypatch):
        import importlib.metadata

        def _boom(_name):
            raise importlib.metadata.PackageNotFoundError('gtach')

        monkeypatch.setattr(importlib.metadata, 'version', _boom)

        gtach_main.enable_stack_dumps()

        first_line = armed.path.read_text().splitlines()[0]
        assert HEADER_RE.match(first_line) is not None
        assert 'unknown' in first_line

    def test_write_failure_does_not_prevent_arming(self, armed, monkeypatch, capsys):
        real_open = open

        def _open_with_failing_write(*args, **kwargs):
            handle = real_open(*args, **kwargs)

            def _boom(_text):
                raise OSError('write exploded')

            handle.write = _boom
            return handle

        # A module global shadows the builtin for lookups inside the
        # module, so this reaches enable_stack_dumps's open() alone.
        monkeypatch.setattr(gtach_main, 'open', _open_with_failing_write,
                            raising=False)

        assert gtach_main.enable_stack_dumps() is True

        assert armed.fake.calls == ['enable', 'dump_traceback_later']
        assert 'WARNING' in capsys.readouterr().err

    def test_second_arm_without_disable_writes_one_header(self, armed):
        assert gtach_main.enable_stack_dumps() is True
        handle = gtach_main._stacks_file

        assert gtach_main.enable_stack_dumps() is True

        assert gtach_main._stacks_file is handle
        assert len(_headers(armed.path)) == 1

    def test_rearm_within_one_process_appends_a_second_header(self, armed):
        gtach_main.enable_stack_dumps()
        gtach_main.disable_stack_dumps()
        gtach_main.enable_stack_dumps()

        assert len(_headers(armed.path)) == 2


class TestRotation:
    """Once per process, never on re-arm, generations bounded at three."""

    def test_pre_existing_content_moves_to_generation_one(self, armed):
        armed.path.write_text('previous run dumps\n')

        gtach_main.enable_stack_dumps()

        assert _generation(armed, 1).read_text() == 'previous run dumps\n'
        assert armed.path.read_text().startswith('=== gtach ')

    def test_empty_file_is_not_rotated(self, armed):
        armed.path.write_text('')

        gtach_main.enable_stack_dumps()

        assert not _generation(armed, 1).exists()

    def test_rearm_does_not_rotate_again(self, armed):
        armed.path.write_text('previous run dumps\n')

        gtach_main.enable_stack_dumps()
        before = _generation(armed, 1).read_bytes()

        gtach_main.disable_stack_dumps()
        gtach_main.enable_stack_dumps()

        assert _generation(armed, 1).read_bytes() == before
        assert not _generation(armed, 2).exists()
        assert len(_headers(armed.path)) == 2

    def test_four_process_lifetimes_keep_three_backups(self, armed):
        """_stacks_rotated reset between arms simulates a relaunch."""
        for run in range(4):
            gtach_main._stacks_rotated = False
            gtach_main._stacks_file = None
            gtach_main.enable_stack_dumps()
            gtach_main._stacks_file.write(f'run-{run}\n')
            gtach_main.disable_stack_dumps()

        assert _generation(armed, 1).exists()
        assert _generation(armed, 2).exists()
        assert _generation(armed, 3).exists()
        assert not _generation(armed, 4).exists()

        # Newest backup is the run before last; run-0 has aged out.
        assert 'run-2' in _generation(armed, 1).read_text()
        assert 'run-1' in _generation(armed, 2).read_text()
        assert 'run-0' in _generation(armed, 3).read_text()
        assert 'run-3' in armed.path.read_text()

    def test_generations_shift_outward_by_exactly_one(self, armed):
        """Descending order; no generation overwrites its neighbour."""
        armed.path.write_text('live\n')
        _generation(armed, 1).write_text('gen1\n')
        _generation(armed, 2).write_text('gen2\n')

        gtach_main._rotate_stacks_log()

        assert not armed.path.exists()
        assert _generation(armed, 1).read_text() == 'live\n'
        assert _generation(armed, 2).read_text() == 'gen1\n'
        assert _generation(armed, 3).read_text() == 'gen2\n'
        assert not _generation(armed, 4).exists()

    def test_oldest_generation_is_discarded_without_raising(self, armed):
        """os.replace must overwrite an existing destination."""
        armed.path.write_text('live\n')
        for n in (1, 2, 3):
            _generation(armed, n).write_text(f'gen{n}\n')

        gtach_main._rotate_stacks_log()

        assert _generation(armed, 3).read_text() == 'gen2\n'
        assert not _generation(armed, 4).exists()

    def test_rotation_failure_still_arms(self, armed, monkeypatch, capsys):
        def _boom():
            raise OSError('rotation exploded')

        monkeypatch.setattr(gtach_main, '_rotate_stacks_log', _boom)

        assert gtach_main.enable_stack_dumps() is True

        assert gtach_main._stacks_rotated is True
        assert armed.fake.calls == ['enable', 'dump_traceback_later']
        assert armed.path.read_text().startswith('=== gtach ')
        assert 'WARNING' in capsys.readouterr().err

    def test_rotation_failure_is_not_retried(self, armed, monkeypatch):
        attempts = []

        def _boom():
            attempts.append(1)
            raise OSError('rotation exploded')

        monkeypatch.setattr(gtach_main, '_rotate_stacks_log', _boom)

        gtach_main.enable_stack_dumps()
        gtach_main.disable_stack_dumps()
        gtach_main.enable_stack_dumps()

        assert len(attempts) == 1


class TestNoPythonSideTimer:
    """The constraint that outranks every other in this change."""

    def test_no_timer_or_thread_introduced(self):
        import inspect

        source = inspect.getsource(gtach_main)
        code = '\n'.join(
            line for line in source.splitlines()
            if not line.lstrip().startswith('#')
        )
        assert 'threading' not in code
        assert 'time.sleep' not in code

    def test_dump_interval_unchanged(self, armed, monkeypatch):
        recorded = []
        monkeypatch.setattr(
            armed.fake, 'dump_traceback_later',
            lambda timeout, repeat=False, file=None: recorded.append(
                (timeout, repeat)
            )
        )

        gtach_main.enable_stack_dumps()

        assert recorded == [(15, True)]

    def test_stacks_log_path_and_backup_count(self):
        assert gtach_main._STACKS_LOG == '/opt/gtach/stacks.log'
        assert gtach_main._STACKS_BACKUPS == 3

    def test_rotation_flag_initialises_false(self):
        """Runtime state varies by test order; assert the initialiser."""
        import inspect

        source = inspect.getsource(gtach_main)
        assert '\n_stacks_rotated = False\n' in source
