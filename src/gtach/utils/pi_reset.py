#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Operator-initiated reboot of the host.

This module is the ONLY place in GTach permitted to invoke an external
command. `subprocess` is imported here and nowhere else, and in
particular nowhere under `gtach.comm`, where change-5e7a03c4
established that the transport reports faults and never acts on the
host.

That boundary is the entire basis on which host action is permitted at
all. :func:`reboot_device` has exactly one call site — the DISCONNECTED
screen's Reset button, through ``GTachApplication._on_reset_pi``.
Nothing invokes it automatically: not a wedge diagnosis, not a retry
count, not startup, not a timer. An operator presses a button, or it
does not run (issue-4ab5ff88).

Two further rules hold the privileged surface small:

* No ``shell=True``, anywhere. A fixed argument list is invoked with an
  absolute path, and no value derived from configuration, the network
  or the operator reaches the command line.
* ``/sbin/reboot`` at that literal path, with no arguments. The path is
  not resolved through PATH, and neither ``systemctl reboot`` nor
  ``shutdown -r now`` is used. That is an explicit choice for the
  deployed OS (Debian 11 on a Raspberry Pi Zero 2W), not an oversight.

The predecessor of this module reset the Bluetooth controller with
``hciconfig hci0 reset``; on target that frequently left the adapter
down, and only a reboot recovered the link (issue-4ab5ff88).

:func:`reboot_device` returns a short string rather than raising,
because the caller runs on a worker thread whose only report is the
log.
"""

import logging
import os
import subprocess

logger = logging.getLogger(__name__)

# Fixed, not configurable: a configurable value would be a value
# reaching a command line.
_REBOOT_PATH = '/sbin/reboot'

# Outcome strings. All 40 characters or fewer, so a future caller can
# render one on the 480x480 display without measuring it.
_OK = 'reboot initiated'
_TIMED_OUT = 'reboot timed out'
_NOT_PERMITTED = 'reboot not permitted'
_NOT_FOUND = 'reboot command not found'
_FAILED = 'reboot failed'
_COMMAND_FAILED = 'reboot command failed'


def reboot_device(timeout: float = 10.0) -> str:
    """Reboot the host and report the outcome.

    Blocking. The caller MUST run this on a worker thread: 'display' is
    a watchdog critical thread at a 45 s timeout, and since
    change-2ac1c602 a critical timeout terminates the process, so
    running this synchronously in a touch callback would race the
    reboot against the watchdog.

    Never raises, for any input or environment. Every path returns a
    non-empty string of 40 characters or fewer.

    Args:
        timeout: Seconds before the reboot invocation is killed.

    Returns:
        A short outcome string, suitable for a log line or the
        DISCONNECTED screen's cause line.
    """
    try:
        if not os.path.exists(_REBOOT_PATH):
            logger.debug("%s does not exist; reboot not attempted",
                         _REBOOT_PATH)
            return _NOT_FOUND

        completed = subprocess.run(
            [_REBOOT_PATH],
            capture_output=True, timeout=timeout, check=False,
        )
        logger.debug("%s -> rc=%d", _REBOOT_PATH, completed.returncode)

        if completed.returncode == 0:
            return _OK

        # A non-zero return is a failure, not a reboot already under
        # way: it must not be reported as success.
        return _COMMAND_FAILED

    except subprocess.TimeoutExpired:
        # subprocess.run has already killed the child. Do not add a
        # second kill.
        logger.error("reboot timed out after %.1fs", timeout, exc_info=True)
        return _TIMED_OUT
    except PermissionError:
        logger.error("reboot requires privileges GTach does not have",
                     exc_info=True)
        return _NOT_PERMITTED
    except FileNotFoundError:
        logger.error("reboot vanished between the existence check and "
                     "invocation", exc_info=True)
        return _NOT_FOUND
    except Exception as e:
        logger.error("Reboot failed: %s", e, exc_info=True)
        return _FAILED
