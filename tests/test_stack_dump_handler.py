# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Python-level on-request stack dump (issue-1a8f40ea).

faulthandler's C-level all-thread dumps terminated the process on the
Pi, first on the 15 s timer (issue-fe755cfd) and then on SIGUSR1
(issue-1a8f40ea). gtach.utils.stack_dump replaces them with a Python
signal handler that reads stacks through sys._current_frames().
"""

import os
import signal
import threading

import pytest

from gtach.utils import stack_dump


@pytest.fixture
def parked_thread():
    """A named thread blocked in a known function until released."""
    release = threading.Event()

    def _parked_worker():
        release.wait(5.0)

    t = threading.Thread(target=_parked_worker, name="ParkedForDump", daemon=True)
    t.start()
    yield t
    release.set()
    t.join(5.0)


class TestFormat:

    def test_names_every_thread_and_its_function(self, parked_thread):
        text = stack_dump.format_all_threads()

        assert text.startswith("=== gtach ")
        assert f"pid {os.getpid()} dump " in text.splitlines()[0]
        assert "[ParkedForDump] (most recent call first):" in text
        assert "in _parked_worker" in text
        assert "Current thread 0x" in text

    def test_layout_matches_the_verify_script_parser(self, parked_thread):
        import re

        text = stack_dump.format_all_threads()
        heads = [
            line
            for line in text.splitlines()
            if re.match(r"(?:Current thread|Thread) (0x[0-9a-f]+)", line)
        ]
        assert len(heads) == len(threading.enumerate())


class TestHandler:

    def test_appends_one_dump_per_call(self, tmp_path, parked_thread):
        path = tmp_path / "stacks.log"
        handler = stack_dump.make_handler(lambda: str(path))

        handler(signal.SIGUSR1, None)
        handler(signal.SIGUSR1, None)

        text = path.read_text()
        assert text.count("=== gtach ") == 2
        assert text.count("[ParkedForDump]") == 2

    def test_unwritable_path_never_raises(self, tmp_path, capsys):
        handler = stack_dump.make_handler(lambda: str(tmp_path / "no" / "dir" / "s"))

        handler(signal.SIGUSR1, None)

        assert "stack dump failed" in capsys.readouterr().err


class TestInstall:

    def test_installs_for_sigusr1(self, monkeypatch, tmp_path):
        installed = {}
        monkeypatch.setattr(
            stack_dump.signal,
            "signal",
            lambda signum, handler: installed.setdefault(signum, handler),
        )

        assert stack_dump.install(lambda: str(tmp_path / "s.log")) is True
        assert signal.SIGUSR1 in installed
        assert callable(installed[signal.SIGUSR1])

    def test_off_main_thread_returns_false(self, tmp_path):
        result = []
        t = threading.Thread(
            target=lambda: result.append(
                stack_dump.install(lambda: str(tmp_path / "s.log"))
            )
        )
        t.start()
        t.join(5.0)

        assert result == [False]

    def test_real_signal_writes_a_dump_and_process_survives(
        self, tmp_path, parked_thread
    ):
        path = tmp_path / "stacks.log"
        previous = signal.getsignal(signal.SIGUSR1)
        try:
            assert stack_dump.install(lambda: str(path)) is True
            os.kill(os.getpid(), signal.SIGUSR1)
            # The Python handler runs at the next bytecode boundary.
            for _ in range(100):
                if path.exists() and "[ParkedForDump]" in path.read_text():
                    break
                threading.Event().wait(0.01)
        finally:
            signal.signal(signal.SIGUSR1, previous)

        assert "[ParkedForDump]" in path.read_text()


class TestMainInstallsHandler:

    def test_main_installs_before_running_the_app(self):
        import inspect
        import sys

        import gtach.main  # noqa: F401

        source = inspect.getsource(sys.modules["gtach.main"].main)
        assert "stack_dump.install(" in source
        assert source.index("stack_dump.install(") < source.index("app.run()")
