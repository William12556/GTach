#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Clock-step-safe timed wait on a threading.Event (issue-4f671d09).

Before Python 3.11, CPython implements a timed lock acquire on Linux
with sem_timedwait against CLOCK_REALTIME. The absolute deadline is
fixed when the wait starts, so a backward wall-clock step of S seconds
extends a timed ``Event.wait`` already in progress by S. Slicing the
wait does not help: each slice has its own CLOCK_REALTIME deadline.

``wait_for_event`` therefore never calls ``Event.wait`` or any other
timed lock acquire. It polls ``is_set()`` between ``time.sleep``
slices against a ``time.monotonic()`` deadline; ``time.sleep`` uses a
relative timeout that the kernel measures on a monotonic clock.
"""

import threading
import time

# Upper bound on wake-up latency after the event is set.
_POLL_SLICE_S: float = 0.1


def wait_for_event(event: threading.Event, timeout: float) -> bool:
    """Wait until ``event`` is set or ``timeout`` seconds have elapsed.

    Args:
        event: Event to observe. Only ``is_set()`` is used.
        timeout: Seconds of elapsed (monotonic) time to wait.

    Returns:
        True if the event is set, otherwise False.
    """
    if event.is_set():
        return True
    deadline = time.monotonic() + timeout
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return event.is_set()
        time.sleep(min(_POLL_SLICE_S, remaining))
        if event.is_set():
            return True
