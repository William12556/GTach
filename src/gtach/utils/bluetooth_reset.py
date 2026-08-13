#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Operator-initiated Bluetooth controller reset.

This module is the ONLY place in GTach permitted to invoke an external
command. `subprocess` is imported here and nowhere else, and in
particular nowhere under `gtach.comm`, where change-5e7a03c4
established that the transport reports faults and never acts on the
host.

That boundary is the entire basis on which host action is permitted at
all. :func:`reset_adapter` has exactly one call site — the DISCONNECTED
screen's Bluetooth Reset button, through
``GTachApplication._on_bluetooth_reset``. Nothing invokes it
automatically: not a wedge diagnosis, not a retry count, not startup,
not a timer. An operator presses a button, or it does not run
(issue-8a63d5f1).

Three further rules hold the privileged surface small:

* No ``shell=True``, anywhere. A fixed argument list is invoked with an
  absolute path, and no value derived from configuration, the network
  or the operator reaches the command line.
* ``hciconfig hci0 reset`` only. The obvious alternative,
  ``hciconfig hci0 down`` followed by ``up``, was attempted on target:
  the down succeeded, the up returned ETIMEDOUT, and the controller
  could not be brought back. That sequence must not be used.
* No systemctl, hciuart, rfkill or kernel module operations.

Every function here returns a short string rather than raising, because
the caller writes the result straight to a 480x480 display.
"""

import logging
import shutil
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)

# The controller GTach uses. Fixed, not configurable: a configurable
# value would be a value reaching a command line.
_ADAPTER = 'hci0'

# Outcome strings. All 40 characters or fewer, to render on the
# DISCONNECTED screen's cause line alongside the transport's own.
_OK = 'bluetooth adapter reset'
_DOWN = 'adapter down - reboot required'
_TIMED_OUT = 'bluetooth reset timed out'
_NOT_PERMITTED = 'bluetooth reset not permitted'
_NOT_FOUND = 'hciconfig not found'
_FAILED = 'bluetooth reset failed'

# Substring hciconfig prints for a controller that is up and running.
_UP_MARKER = 'UP RUNNING'


def _hciconfig_path() -> Optional[str]:
    """Resolve an absolute path to hciconfig.

    Returns:
        The resolved path, or None when hciconfig cannot be found. A
        None return is reported to the operator rather than raising.
    """
    resolved = shutil.which('hciconfig')
    if resolved:
        return resolved

    # PATH under systemd is minimal and need not include sbin, where
    # hciconfig usually lives. Re-querying with an explicit directory
    # also confirms the file is executable, which a bare exists() check
    # would not.
    return shutil.which('hciconfig', path='/usr/bin')


def _adapter_is_up(path: str, timeout: float) -> bool:
    """Report whether the adapter shows as up and running.

    Unexpected output is treated as "not up", so a parsing surprise
    causes one extra recovery attempt rather than an exception.

    Args:
        path: Absolute path to hciconfig.
        timeout: Seconds before the query is killed.

    Returns:
        True only when hciconfig's output contains the up marker.
    """
    completed = subprocess.run(
        [path, _ADAPTER],
        capture_output=True, timeout=timeout, check=False,
    )
    logger.debug("hciconfig %s -> rc=%d", _ADAPTER, completed.returncode)
    stdout = completed.stdout.decode('utf-8', errors='ignore')
    return _UP_MARKER in stdout


def reset_adapter(timeout: float = 10.0) -> str:
    """Reset the Bluetooth controller and report the outcome.

    Blocking. The caller MUST run this on a worker thread: 'display' is
    a watchdog critical thread at a 45 s timeout, and since
    change-2ac1c602 a critical timeout terminates the process, so
    running this synchronously in a touch callback would turn the
    button into an application restart.

    Never raises, for any input or environment. Every path returns a
    non-empty string of 40 characters or fewer.

    Args:
        timeout: Seconds before an individual hciconfig invocation is
            killed. Applied per command, not to the whole sequence.

    Returns:
        A short outcome string suitable for the DISCONNECTED screen's
        cause line.
    """
    try:
        path = _hciconfig_path()
        if path is None:
            logger.debug("hciconfig could not be resolved; reset not attempted")
            return _NOT_FOUND

        completed = subprocess.run(
            [path, _ADAPTER, 'reset'],
            capture_output=True, timeout=timeout, check=False,
        )
        logger.debug("hciconfig %s reset -> rc=%d", _ADAPTER,
                     completed.returncode)

        if _adapter_is_up(path, timeout):
            return _OK

        # One up attempt, then re-verify. A reset that leaves the
        # controller down is the state the manual attempt on this host
        # produced, so it is worth one try before giving up.
        completed = subprocess.run(
            [path, _ADAPTER, 'up'],
            capture_output=True, timeout=timeout, check=False,
        )
        logger.debug("hciconfig %s up -> rc=%d", _ADAPTER,
                     completed.returncode)

        if _adapter_is_up(path, timeout):
            return _OK

        # Deliberately blunt, and not to be softened. The controller is
        # down and this code cannot bring it back; the operator needs
        # to be told plainly rather than left to infer it.
        return _DOWN

    except subprocess.TimeoutExpired:
        # subprocess.run has already killed the child. Do not add a
        # second kill.
        logger.error("hciconfig timed out after %.1fs", timeout, exc_info=True)
        return _TIMED_OUT
    except PermissionError:
        logger.error("hciconfig requires privileges GTach does not have",
                     exc_info=True)
        return _NOT_PERMITTED
    except FileNotFoundError:
        logger.error("hciconfig vanished between resolution and invocation",
                     exc_info=True)
        return _NOT_FOUND
    except Exception as e:
        logger.error("Bluetooth reset failed: %s", e, exc_info=True)
        return _FAILED
