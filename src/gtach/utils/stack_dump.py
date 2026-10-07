# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""On-request all-thread stack dump (issue-1a8f40ea).

SIGUSR1 appends one dump of every Python thread to stacks.log. The
handler is a Python-level signal handler: Python runs it on the main
thread between bytecodes, and it reads stacks through
sys._current_frames(), which returns reference-counted frame objects
taken under the GIL. Other threads may move on while the dump is
written, so a stack can be slightly stale, but nothing is read from
freed memory. faulthandler's C-level dumps (dump_traceback_later and
register) walk running threads' frames without the GIL and terminated
the process on the Pi (issue-fe755cfd, issue-1a8f40ea).

Limitation: a Python-level handler runs only when the main thread can
execute bytecode. A stall that holds the GIL in C code is not captured;
faulthandler.enable still records fatal errors.

The handler is installed for the life of the process, independent of
the debug setting, so SIGUSR1 never takes its default action (process
termination).
"""

import datetime
import os
import signal
import sys
import threading
from typing import Callable, Optional

_LOG_PATH_DEFAULT = "/opt/gtach/stacks.log"


def _version() -> str:
    """Return the installed gtach version, or 'unknown'."""
    try:
        import importlib.metadata

        return importlib.metadata.version("gtach")
    except Exception:
        return "unknown"


def format_all_threads() -> str:
    """Format every Python thread's stack, most recent call first.

    The layout follows faulthandler's ('Thread 0x... (most recent call
    first):' then '  File "...", line N in func'), with the thread name
    added, so existing readers of stacks.log continue to work.

    Returns:
        The dump text, starting with a run header.
    """
    names = {t.ident: t.name for t in threading.enumerate()}
    current = threading.get_ident()
    now = datetime.datetime.now().isoformat(timespec="seconds")
    lines = [f"=== gtach {_version()} pid {os.getpid()} dump {now} ==="]
    for ident, frame in sys._current_frames().items():
        label = "Current thread" if ident == current else "Thread"
        name = names.get(ident, "?")
        lines.append(f"{label} 0x{ident:016x} [{name}] (most recent call first):")
        while frame is not None:
            code = frame.f_code
            lines.append(
                f'  File "{code.co_filename}", line {frame.f_lineno} '
                f"in {code.co_name}"
            )
            frame = frame.f_back
        lines.append("")
    return "\n".join(lines) + "\n"


def make_handler(path_getter: Callable[[], str]) -> Callable:
    """Build the SIGUSR1 handler.

    Args:
        path_getter: Returns the stacks.log path at call time, so tests
            and gtach.main's module constant are honoured.

    Returns:
        A signal handler that appends one dump and never raises.
    """

    def _handler(signum, frame) -> None:
        try:
            text = format_all_threads()
            with open(path_getter(), "a", encoding="utf-8") as f:
                f.write(text)
        except Exception as e:
            try:
                print(f"[gtach] WARNING: stack dump failed: {e}", file=sys.stderr)
            except Exception:
                pass

    return _handler


def install(path_getter: Optional[Callable[[], str]] = None) -> bool:
    """Install the SIGUSR1 dump handler.

    Must be called from the main thread (signal.signal requires it).

    Args:
        path_getter: Returns the stacks.log path; defaults to
            /opt/gtach/stacks.log.

    Returns:
        True if installed; False where SIGUSR1 is unavailable or the
        call is not on the main thread.
    """
    signum = getattr(signal, "SIGUSR1", None)
    if signum is None:
        return False
    getter = path_getter or (lambda: _LOG_PATH_DEFAULT)
    try:
        signal.signal(signum, make_handler(getter))
        return True
    except ValueError:
        # Not on the main thread.
        return False
