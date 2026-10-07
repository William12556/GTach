#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Configuration for GTach.

GTACH_HOME/config.yaml (flat schema) is the only configuration file and
ConfigStore its only owner (issue-5fbff586). load_engine_profile reads
the packaged engine profiles; SplashConfig configures the splash screen.
"""

import importlib.resources
import logging
import os
import sys
import threading
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

# Conditional import of yaml
try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    yaml = None
    YAML_AVAILABLE = False

from .home import gtach_home


def load_engine_profile(profile_name: str = "abarth_595_turismo"):
    """Load engine profile from engine_profiles.yaml.

    Args:
        profile_name: Name of the engine profile to load

    Returns:
        RPMBands instance with the loaded profile, or default on error

    Raises:
        ImportError: If RPMBands cannot be imported
    """
    logger = logging.getLogger(f"{__name__}.load_engine_profile")

    # Import RPMBands here to avoid circular imports
    try:
        from ..display.models import RPMBands
    except ImportError as e:
        logger.error(f"Cannot import RPMBands: {e}", exc_info=True)
        raise

    try:
        # Try to load engine_profiles.yaml from assets directory
        profile_path = None

        # Method 1: Try importlib.resources (Python 3.9+)
        try:
            if sys.version_info >= (3, 9):
                import importlib.resources as pkg_resources

                files = pkg_resources.files("gtach.assets")
                profile_path = files / "engine_profiles.yaml"
            else:
                # Fallback for older Python versions
                import pkg_resources as pkg_res

                profile_path = Path(
                    pkg_res.resource_filename("gtach.assets", "engine_profiles.yaml")
                )
        except Exception as e:
            logger.debug(f"importlib.resources failed: {e}")

        # Method 2: Try relative path from this file
        if profile_path is None or not Path(profile_path).exists():
            config_dir = Path(__file__).parent.parent / "assets"
            profile_path = config_dir / "engine_profiles.yaml"

        if not Path(profile_path).exists():
            logger.warning(
                f"Engine profiles file not found at {profile_path}, using defaults"
            )
            return RPMBands()

        # Load YAML file
        if not YAML_AVAILABLE:
            logger.warning("YAML not available, using default RPM bands")
            return RPMBands()

        with open(profile_path, "r") as f:
            data = yaml.safe_load(f)

        if not data or "profiles" not in data:
            logger.warning("Invalid engine profiles file format, using defaults")
            return RPMBands()

        # Get the requested profile
        profiles = data.get("profiles", {})
        if profile_name not in profiles:
            logger.warning(f"Profile '{profile_name}' not found, using defaults")
            return RPMBands()

        profile_data = profiles[profile_name]

        # Construct RPMBands from profile
        try:
            rpm_bands = RPMBands(
                idle_max=profile_data.get("idle_max", 999),
                torque_start=profile_data.get("torque_start", 3000),
                caution_start=profile_data.get("caution_start", 4500),
                warning_start=profile_data.get("warning_start", 5500),
                danger_start=profile_data.get("danger_start", 5800),
                redline_rpm=profile_data.get("redline_rpm", 6000),
            )
            logger.debug(f"Loaded engine profile '{profile_name}': {rpm_bands}")
            return rpm_bands

        except (KeyError, ValueError) as e:
            logger.error(
                f"Error constructing RPMBands from profile '{profile_name}': {e}",
                exc_info=True,
            )
            return RPMBands()

    except Exception as e:
        logger.error(f"Unexpected error loading engine profile: {e}", exc_info=True)
        return RPMBands()


@dataclass
class SplashConfig:
    """Splash screen configuration settings"""

    enabled: bool = True  # Enable/disable splash screen
    duration: float = 4.0  # Splash duration in seconds
    graphics_mode: str = (
        "automotive"  # Graphics mode: 'automotive', 'minimal', 'text_only'
    )
    animation_speed: float = 1.0  # Animation speed multiplier

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "enabled": self.enabled,
            "duration": self.duration,
            "graphics_mode": self.graphics_mode,
            "animation_speed": self.animation_speed,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SplashConfig":
        """Create instance from dictionary"""
        if not data:
            return cls()

        # Validate graphics_mode
        valid_modes = ["automotive", "minimal", "text_only"]
        graphics_mode = data.get("graphics_mode", "automotive")
        if graphics_mode not in valid_modes:
            graphics_mode = "automotive"

        # Validate duration (must be positive)
        duration = data.get("duration", 4.0)
        if duration <= 0:
            duration = 4.0

        # Validate animation_speed (must be positive)
        animation_speed = data.get("animation_speed", 1.0)
        if animation_speed <= 0:
            animation_speed = 1.0

        return cls(
            enabled=data.get("enabled", True),
            duration=duration,
            graphics_mode=graphics_mode,
            animation_speed=animation_speed,
        )


# Known config.yaml keys and accepted values (issue-5fbff586).
MODE_VALUES = ("RADIAL",)
LEGACY_MODE_VALUES = ("DIGITAL",)  # accepted on read, mapped to RADIAL
PALETTE_VALUES = ("day", "night")
FPS_LIMIT_RANGE = (1, 60)
TOUCH_LONG_PRESS_RANGE = (0.1, 5.0)


@dataclass
class AppConfig:
    """Persisted display settings: the flat keys of config.yaml."""

    mode: str = "RADIAL"
    palette: str = "day"
    engine_profile: str = "abarth_595_turismo"
    fps_limit: int = 30
    touch_long_press: float = 1.0
    rpm_warning: int = 6500
    rpm_danger: int = 7000


# Key -> type, in file order.
CONFIG_KEYS: Dict[str, type] = {
    "mode": str,
    "palette": str,
    "engine_profile": str,
    "fps_limit": int,
    "touch_long_press": float,
    "rpm_warning": int,
    "rpm_danger": int,
}


def _engine_profile_names() -> List[str]:
    """Names of the profiles in assets/engine_profiles.yaml.

    Resolves the file the way load_engine_profile does: the package
    resource first, then the path relative to this module.

    Returns:
        The profile names; empty if the file cannot be read.
    """
    profile_path = None
    try:
        profile_path = (
            importlib.resources.files("gtach.assets") / "engine_profiles.yaml"
        )
    except Exception:
        profile_path = None
    if profile_path is None or not Path(str(profile_path)).exists():
        profile_path = Path(__file__).parent.parent / "assets" / "engine_profiles.yaml"
    try:
        with open(profile_path, "r") as f:
            data = yaml.safe_load(f)
    except Exception:
        return []
    if not isinstance(data, dict) or not isinstance(data.get("profiles"), dict):
        return []
    return list(data["profiles"].keys())


class ConfigStore:
    """Sole owner of GTACH_HOME/config.yaml.

    load() never writes; save() writes atomically and keeps any keys it
    does not know. The lock guards the retained unknown keys; file I/O
    and logging happen outside it (CLAUDE.md §4 rule 8).
    """

    def __init__(self, path: Optional[Path] = None):
        """Create a store.

        Args:
            path: The configuration file. Defaults to
                gtach_home() / 'config.yaml'.
        """
        self.path = Path(path) if path is not None else gtach_home() / "config.yaml"
        self.logger = logging.getLogger(f"{__name__}.ConfigStore")
        self._lock = threading.Lock()
        self._unknown: Dict[str, Any] = {}

    def _read(self) -> Any:
        """Parse the file. Raises OSError or yaml.YAMLError."""
        with open(self.path, "r") as f:
            return yaml.safe_load(f)

    def load(self) -> AppConfig:
        """Read the configuration.

        A missing file gives the defaults and nothing is written. An
        unreadable file or invalid YAML gives the defaults and is logged.
        Invalid values are replaced by their defaults with a warning;
        'DIGITAL' is mapped to 'RADIAL'. Unknown keys are retained for
        save().

        Returns:
            The configuration.
        """
        defaults = AppConfig()
        if not self.path.exists():
            return defaults
        try:
            data = self._read()
        except (OSError, yaml.YAMLError) as e:
            self.logger.error(f"Cannot read {self.path}: {e}", exc_info=True)
            return defaults
        if data is None:
            data = {}
        if not isinstance(data, dict):
            self.logger.warning(f"{self.path} is not a mapping; using defaults")
            return defaults

        values: Dict[str, Any] = {}
        for key, kind in CONFIG_KEYS.items():
            if key not in data:
                continue
            try:
                values[key] = kind(data[key])
            except (TypeError, ValueError):
                self.logger.warning(
                    f"Invalid value for {key}: {data[key]!r}; using default "
                    f"{getattr(defaults, key)!r}"
                )
        if values.get("mode") in LEGACY_MODE_VALUES:
            values["mode"] = "RADIAL"
        # Out-of-range values are replaced too (issue-4005360c).
        for key, (low, high) in (
            ("fps_limit", FPS_LIMIT_RANGE),
            ("touch_long_press", TOUCH_LONG_PRESS_RANGE),
        ):
            if key in values and not low <= values[key] <= high:
                self.logger.warning(
                    f"Out-of-range value for {key}: {values[key]!r}; "
                    f"using default {getattr(defaults, key)!r}"
                )
                del values[key]

        unknown = {k: v for k, v in data.items() if k not in CONFIG_KEYS}
        with self._lock:
            self._unknown = unknown
        return AppConfig(**values)

    def save(self, config: AppConfig) -> bool:
        """Write the configuration atomically.

        Known fields are merged over the retained unknown keys, written
        to a temporary file in the same directory, flushed, fsync'd and
        moved into place. The directory is created if missing.

        Args:
            config: The configuration to write.

        Returns:
            True on success, False (logged) on failure.
        """
        with self._lock:
            data = dict(self._unknown)
        data.update(asdict(config))
        tmp_path = self.path.with_name(f".{self.path.name}.{os.getpid()}.tmp")
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(tmp_path, "w") as f:
                yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, self.path)
            return True
        except (OSError, yaml.YAMLError) as e:
            self.logger.error(f"Cannot save {self.path}: {e}", exc_info=True)
            try:
                tmp_path.unlink()
            except OSError:
                pass
            return False

    def validate(self) -> List[str]:
        """Check the file without changing it.

        A missing file is valid. 'DIGITAL' is an accepted legacy mode.

        Returns:
            One error string per problem; empty if valid.
        """
        if not self.path.exists():
            return []
        try:
            data = self._read()
        except (OSError, yaml.YAMLError) as e:
            return [f"{self.path}: cannot read: {e}"]
        if data is None:
            return []
        if not isinstance(data, dict):
            return [f"{self.path}: not a mapping"]

        errors: List[str] = []
        for key, value in data.items():
            if key not in CONFIG_KEYS:
                errors.append(f"unknown key: {key}")
                continue
            kind = CONFIG_KEYS[key]
            if kind is float:
                type_ok = isinstance(value, (int, float)) and not isinstance(
                    value, bool
                )
            elif kind is int:
                type_ok = isinstance(value, int) and not isinstance(value, bool)
            else:
                type_ok = isinstance(value, kind)
            if not type_ok:
                errors.append(f"{key}: expected {kind.__name__}, got {value!r}")
                continue
            if key == "mode" and value not in MODE_VALUES + LEGACY_MODE_VALUES:
                errors.append(f"mode: {value!r} not in {list(MODE_VALUES)}")
            elif key == "palette" and value not in PALETTE_VALUES:
                errors.append(f"palette: {value!r} not in {list(PALETTE_VALUES)}")
            elif key == "engine_profile" and value not in _engine_profile_names():
                errors.append(
                    f"engine_profile: {value!r} not defined in engine_profiles.yaml"
                )
            elif (
                key == "fps_limit"
                and not FPS_LIMIT_RANGE[0] <= value <= FPS_LIMIT_RANGE[1]
            ):
                errors.append(
                    f"fps_limit: {value} not in "
                    f"{FPS_LIMIT_RANGE[0]}..{FPS_LIMIT_RANGE[1]}"
                )
            elif key == "touch_long_press" and not (
                TOUCH_LONG_PRESS_RANGE[0] <= value <= TOUCH_LONG_PRESS_RANGE[1]
            ):
                errors.append(
                    f"touch_long_press: {value} not in "
                    f"{TOUCH_LONG_PRESS_RANGE[0]}..{TOUCH_LONG_PRESS_RANGE[1]}"
                )
        return errors
