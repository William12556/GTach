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
import re
import zipfile
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

UPDATES_DIR = "/opt/gtach/updates"
PENDING_MARKER = os.path.join(UPDATES_DIR, ".install-pending")


# Normalised PEP 440 release with an optional pre-release segment, the
# form importlib.metadata and wheel file names carry (issue-c41037ea).
_VERSION_RE = re.compile(r"^(\d+(?:\.\d+)*)(?:(a|b|rc)(\d+))?$")

# Pre-release phases order below the final release, which ranks 0.
_PRE_RELEASE_RANK: Dict[str, int] = {"a": -3, "b": -2, "rc": -1}

# Releases are padded to this many components, so 1.0 equals 1.0.0.
_MIN_RELEASE_PARTS = 3


def _parse_version_str(s: str) -> Optional[Tuple[int, ...]]:
    """Build the order key of a version string.

    Args:
        s: A version such as '1.0.0' or '1.0.0rc1'.

    Returns:
        The release numbers padded to _MIN_RELEASE_PARTS, then the phase
        rank and the pre-release number, (0, 0) for a final release; so
        1.0.0rc1 orders below 1.0.0. None for any other form, including
        development, post-release and local versions.
    """
    try:
        match = _VERSION_RE.match(s.strip())
    except (AttributeError, TypeError):
        return None
    if match is None:
        return None
    release = tuple(int(part) for part in match.group(1).split("."))
    release += (0,) * (_MIN_RELEASE_PARTS - len(release))
    phase = match.group(2)
    if phase is None:
        return release + (0, 0)
    return release + (_PRE_RELEASE_RANK[phase], int(match.group(3)))


def get_installed_version() -> Optional[Tuple[int, ...]]:
    """Order key of the installed version (_parse_version_str), or None."""
    try:
        from importlib.metadata import version as _pkg_version

        return _parse_version_str(_pkg_version("gtach"))
    except Exception:
        return None


def parse_wheel_version(filename: str) -> Optional[Tuple[int, ...]]:
    """Order key of the version in a wheel filename, or None.

    e.g. 'gtach-0.2.61-py3-none-any.whl' -> the key of 0.2.61.
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
            logger.warning("Installed version not recognised; update check skipped")
            return None
        if not os.path.isdir(UPDATES_DIR):
            return None
        best = None  # (version_tuple, filename, raw_version_str)
        for name in os.listdir(UPDATES_DIR):
            if not name.endswith(".whl"):
                continue
            ver = parse_wheel_version(name)
            if ver is None:
                logger.debug(f"Skipping wheel with unrecognised version: {name}")
                continue
            if ver <= installed:
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
