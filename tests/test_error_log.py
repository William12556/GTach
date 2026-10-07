#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""The always-on error.log handler.

Covers change-269871a0 EDIT A. With debug off, start.log is silenced
after startup and debug.log is suppressed, so nothing at all was
persisted after startup. error.log records WARNING and above for the
life of the process, is size-rotated only, and is never rotated at
start, so the record of a fault that caused a restart survives it.

Every test redirects all three log paths to tmp_path; nothing here may
write under /opt/gtach.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler

import pytest

import gtach.main  # noqa: F401  — ensures the module is in sys.modules

# gtach/__init__.py re-exports the main FUNCTION under the name 'main';
# the module is fetched from sys.modules (issue-c1d4b8e6).
gtach_main = sys.modules["gtach.main"]


@pytest.fixture
def logs(tmp_path, monkeypatch):
    """Redirect every log path and restore the root logger afterwards."""
    paths = {
        "start": tmp_path / "start.log",
        "debug": tmp_path / "debug.log",
        "error": tmp_path / "error.log",
    }
    monkeypatch.setattr(gtach_main, "_START_LOG", str(paths["start"]))
    monkeypatch.setattr(gtach_main, "_DEBUG_LOG", str(paths["debug"]))
    monkeypatch.setattr(gtach_main, "_ERROR_LOG", str(paths["error"]))
    # Module-level handler references: restored by monkeypatch.
    for name in ("_start_handler", "_debug_handler", "_error_handler"):
        monkeypatch.setattr(gtach_main, name, None)

    root = logging.getLogger()
    before = list(root.handlers)
    level = root.level
    yield paths
    for handler in list(root.handlers):
        if handler not in before:
            root.removeHandler(handler)
            try:
                handler.close()
            except Exception:
                pass
    root.setLevel(level)


def _flush():
    for handler in logging.getLogger().handlers:
        handler.flush()


class TestErrorLogHandler:
    """WARNING and above, always on, never rotated at start."""

    def test_constants(self):
        assert gtach_main._ERROR_MAX_BYTES == 1048576
        assert gtach_main._ERROR_BACKUPS == 5

    def test_records_warning_and_error_but_not_info(self, logs):
        gtach_main.setup_logging(debug=False)
        logger = logging.getLogger("test.error_log")

        logger.info("info-line")
        logger.warning("warning-line")
        logger.error("error-line")
        _flush()

        text = logs["error"].read_text(encoding="utf-8")
        assert "warning-line" in text
        assert "error-line" in text
        assert "info-line" not in text

    def test_handler_is_rotating_at_warning(self, logs):
        gtach_main.setup_logging(debug=False)

        handler = gtach_main._error_handler
        assert isinstance(handler, RotatingFileHandler)
        assert handler.level == logging.WARNING
        assert handler.maxBytes == gtach_main._ERROR_MAX_BYTES
        assert handler.backupCount == gtach_main._ERROR_BACKUPS

    def test_records_errors_after_start_log_is_silenced(self, logs):
        """The production case: startup complete, debug off."""
        gtach_main.setup_logging(debug=False)
        gtach_main._start_handler.setLevel(logging.CRITICAL + 1)

        logging.getLogger("test.error_log").error("after-startup")
        _flush()

        assert "after-startup" in logs["error"].read_text(encoding="utf-8")
        assert "after-startup" not in logs["start"].read_text(encoding="utf-8")

    def test_not_rotated_at_start(self, logs):
        logs["error"].write_text("previous-run fault\n", encoding="utf-8")

        gtach_main.setup_logging(debug=False)
        _flush()

        assert "previous-run fault" in logs["error"].read_text(encoding="utf-8")
        assert not (logs["error"].parent / "error.log.1").exists()

    def test_unopenable_path_does_not_raise(self, logs, tmp_path, monkeypatch, capsys):
        missing = tmp_path / "no" / "such" / "dir" / "error.log"
        monkeypatch.setattr(gtach_main, "_ERROR_LOG", str(missing))

        gtach_main.setup_logging(debug=False)

        assert gtach_main._error_handler is None
        assert "could not open" in capsys.readouterr().err
