#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Engine Profile Loader for GTach RPM colour band system.

Loads and manages engine profiles from engine_profiles.yaml, providing
RPMBands instances for selected profiles.
"""

import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    yaml = None
    YAML_AVAILABLE = False


class EngineProfileLoader:
    """
    Loads engine profiles from YAML and provides RPMBands instances.

    Profiles are loaded from engine_profiles.yaml in the application data
    directory. Each profile defines six RPM thresholds for the colour band system.
    """

    def __init__(self, profiles_path: Optional[Path] = None):
        """
        Initialize engine profile loader.

        Args:
            profiles_path: Path to engine_profiles.yaml. If None, uses default
                          path in src/gtach/data/engine_profiles.yaml
        """
        self.logger = logging.getLogger(f'{__name__}.EngineProfileLoader')

        if profiles_path is None:
            # Default to data directory in package
            package_root = Path(__file__).parent.parent
            self.profiles_path = package_root / 'data' / 'engine_profiles.yaml'
        else:
            self.profiles_path = Path(profiles_path)

        self._profiles: Dict[str, Dict[str, Any]] = {}
        self._loaded = False

    def load(self) -> bool:
        """
        Load engine profiles from YAML file.

        Returns:
            True if profiles loaded successfully, False otherwise
        """
        if not YAML_AVAILABLE:
            self.logger.warning("PyYAML not available - cannot load engine profiles")
            return False

        if not self.profiles_path.exists():
            self.logger.warning(f"Engine profiles file not found: {self.profiles_path}")
            return False

        try:
            with open(self.profiles_path, 'r') as f:
                data = yaml.safe_load(f)

            if not data or 'profiles' not in data:
                self.logger.warning(f"Invalid engine profiles YAML: missing 'profiles' key")
                return False

            self._profiles = data['profiles']
            self._loaded = True
            self.logger.debug(f"Loaded {len(self._profiles)} engine profiles from {self.profiles_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to load engine profiles: {e}", exc_info=True)
            return False

    def get_profile(self, profile_id: str) -> Optional['RPMBands']:
        """
        Get RPMBands for a specific profile.

        Args:
            profile_id: Profile identifier (e.g., 'abarth_595_turismo')

        Returns:
            RPMBands instance if profile found and valid, None otherwise
        """
        if not self._loaded:
            self.logger.warning("Profiles not loaded - call load() first")
            return None

        if profile_id not in self._profiles:
            self.logger.warning(f"Profile '{profile_id}' not found in engine profiles")
            return None

        try:
            # Import here to avoid circular dependency
            from ..display.models import RPMBands

            profile_data = self._profiles[profile_id]
            bands = RPMBands.from_dict(profile_data)

            # Validate the profile
            if not bands.is_valid():
                self.logger.warning(f"Profile '{profile_id}' has invalid threshold ordering")
                return None

            return bands

        except Exception as e:
            self.logger.error(f"Failed to create RPMBands from profile '{profile_id}': {e}", exc_info=True)
            return None

    def list_profiles(self) -> List[str]:
        """
        List available profile IDs.

        Returns:
            List of profile IDs. Empty list if profiles not loaded.
        """
        if not self._loaded:
            return []
        return list(self._profiles.keys())

    def get_profile_name(self, profile_id: str) -> Optional[str]:
        """
        Get human-readable name for a profile.

        Args:
            profile_id: Profile identifier

        Returns:
            Profile name if found, None otherwise
        """
        if not self._loaded or profile_id not in self._profiles:
            return None

        return self._profiles[profile_id].get('name', profile_id)

    def get_profile_info(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """
        Get complete profile information.

        Args:
            profile_id: Profile identifier

        Returns:
            Dictionary with profile data, or None if not found
        """
        if not self._loaded or profile_id not in self._profiles:
            return None

        return self._profiles[profile_id].copy()
