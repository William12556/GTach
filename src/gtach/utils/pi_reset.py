#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Operator-initiated reboot of the host.

This module is the only part of GTach that acts on the host.
``subprocess`` is also used read-only, for Bluetooth discovery
(comm/system_bluetooth.py) and platform detection (utils/platform.py);
neither changes host state (issue-042dd7ff).

:func:`reboot_device` has one call site, the DISCONNECTED screen's
Reset button through ``GTachApplication._on_reset_pi``; nothing invokes
it automatically (issue-4ab5ff88).

* No ``shell=True``. A fixed argument list is invoked by absolute path,
  and no value from configuration, the network or the operator reaches
  the command line.
* ``/sbin/reboot`` at that literal path, with no arguments, for the
  deployed OS (Debian 11 on a Raspberry Pi Zero 2W).

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
_REBOOT_PATH = "/sbin/reboot"

# Outcome strings. All 40 characters or fewer, so a future caller can
# render one on the 480x480 display without measuring it.
_OK = "reboot initiated"
_TIMED_OUT = "reboot timed out"
_NOT_PERMITTED = "reboot not permitted"
_NOT_FOUND = "reboot command not found"
_FAILED = "reboot failed"
_COMMAND_FAILED = "reboot command failed"


def _first_line(output: object) -> str:
    """Return the first line of captured output, decoded, or ''."""
    if isinstance(output, bytes):
        output = output.decode("utf-8", errors="replace")
    if not isinstance(output, str):
        return ""
    lines = output.strip().splitlines()
    return lines[0] if lines else ""


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
            logger.debug("%s does not exist; reboot not attempted", _REBOOT_PATH)
            return _NOT_FOUND

        completed = subprocess.run(
            [_REBOOT_PATH],
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        returncode = completed.returncode
        if returncode == 0:
            return _OK

        logger.warning(
            "%s returned %d: %s",
            _REBOOT_PATH,
            returncode,
            _first_line(completed.stderr),
        )
        # A negative code means the command was ended by a signal: the
        # host is already stopping (issue-042dd7ff).
        if returncode < 0:
            return _OK
        return _COMMAND_FAILED

    except subprocess.TimeoutExpired:
        # subprocess.run has already killed the child. Do not add a
        # second kill.
        logger.error("reboot timed out after %.1fs", timeout, exc_info=True)
        return _TIMED_OUT
    except PermissionError:
        logger.error("reboot requires privileges GTach does not have", exc_info=True)
        return _NOT_PERMITTED
    except FileNotFoundError:
        logger.error(
            "reboot vanished between the existence check and invocation",
            exc_info=True,
        )
        return _NOT_FOUND
    except Exception as e:
        logger.error("Reboot failed: %s", e, exc_info=True)
        return _FAILED
