# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
GTach home directory.

One location rule for everything GTach reads and writes at runtime:
$GTACH_HOME if it is set and non-empty, otherwise /opt/gtach, the
installed location on the Pi. Development and tests set GTACH_HOME to a
directory of their own, so nothing is written into the repository
(issue-5fbff586). No directory is created here.
"""

import os
from pathlib import Path

GTACH_HOME_ENV = "GTACH_HOME"
DEFAULT_GTACH_HOME = Path("/opt/gtach")


def gtach_home() -> Path:
    """Return the GTach home directory.

    Returns:
        Path($GTACH_HOME) if the variable is set and non-empty, else
        DEFAULT_GTACH_HOME.
    """
    value = os.environ.get(GTACH_HOME_ENV)
    if value:
        return Path(value)
    return DEFAULT_GTACH_HOME
