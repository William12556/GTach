#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Update discovery helpers for the OPTIONS update screen.

Pure filesystem logic: scan the drop directory for a wheel strictly newer
than the installed version, validate zip integrity, and stage the pending
install marker consumed by gtach-preflight.sh. No display dependencies.
"""

import logging
import os
import zipfile
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

UPDATES_DIR = "/opt/gtach/updates"
PENDING_MARKER = os.path.join(UPDATES_DIR, ".install-pending")


def _parse_version_str(s: str) -> Optional[Tuple[int, ...]]:
    try:
        return tuple(int(p) for p in s.strip().split("."))
    except (ValueError, AttributeError):
        return None


def get_installed_version() -> Optional[Tuple[int, ...]]:
    """Installed wheel version as an int tuple, or None."""
    try:
        from importlib.metadata import version as _pkg_version
        return _parse_version_str(_pkg_version("gtach"))
    except Exception:
        return None


def parse_wheel_version(filename: str) -> Optional[Tuple[int, ...]]:
    """Extract the version tuple from a wheel filename.

    e.g. 'gtach-0.2.61-py3-none-any.whl' -> (0, 2, 61).
    """
    parts = filename.split("-")
    if len(parts) < 2:
        return None
    return _parse_version_str(parts[1])


def validate_wheel(path: str) -> bool:
    """True if the file is a complete, readable zip (wheel)."""
    try:
        if not zipfile.is_zipfile(path):
            return False
        with zipfile.ZipFile(path) as zf:
            return zf.testzip() is None
    except Exception:
        return False


def find_available_update() -> Optional[Tuple[str, str]]:
    """Return (filename, version_str) of the newest valid wheel strictly
    newer than the installed version, or None.
    """
    try:
        installed = get_installed_version()
        if installed is None:
            return None
        if not os.path.isdir(UPDATES_DIR):
            return None
        best = None  # (version_tuple, filename, raw_version_str)
        for name in os.listdir(UPDATES_DIR):
            if not name.endswith(".whl"):
                continue
            ver = parse_wheel_version(name)
            if ver is None or ver <= installed:
                continue
            if not validate_wheel(os.path.join(UPDATES_DIR, name)):
                logger.warning(f"Skipping invalid wheel: {name}")
                continue
            raw = name.split("-")[1]
            if best is None or ver > best[0]:
                best = (ver, name, raw)
        if best is None:
            return None
        return (best[1], best[2])
    except Exception as e:
        logger.error(f"Update scan error: {e}", exc_info=True)
        return None


def stage_pending(filename: str) -> bool:
    """Write the install-pending marker for the boot-time supervisor."""
    try:
        os.makedirs(UPDATES_DIR, exist_ok=True)
        with open(PENDING_MARKER, "w", encoding="utf-8") as f:
            f.write(filename)
        logger.info(f"Staged pending install: {filename}")
        return True
    except Exception as e:
        logger.error(f"Failed to stage pending install: {e}", exc_info=True)
        return False
