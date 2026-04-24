#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Acknowledgement State Manager for GTach RPM colour band system.

Manages operator acknowledgement state for RPM thresholds, using hash-based
validation to detect configuration changes. State is persisted independently
from the main YAML configuration file.
"""

import hashlib
import logging
import os
import uuid
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    yaml = None
    YAML_AVAILABLE = False

from .home import get_home_path


class AcknowledgementStateManager:
    """
    Manages operator acknowledgement state for RPM thresholds.

    Uses SHA256 hash of threshold values and profile ID to detect configuration
    changes. State is persisted to a separate YAML file independent of the main
    configuration.
    """

    def __init__(self, state_file_path: Optional[Path] = None):
        """
        Initialize acknowledgement state manager.

        Args:
            state_file_path: Path to state file. If None, uses default path
                           in config directory: ~/.config/gtach/ack_state.yaml
        """
        self.logger = logging.getLogger(f'{__name__}.AcknowledgementStateManager')

        if state_file_path is None:
            # Default to config directory
            config_dir = get_home_path() / 'config'
            config_dir.mkdir(parents=True, exist_ok=True)
            self.state_file_path = config_dir / 'ack_state.yaml'
        else:
            self.state_file_path = Path(state_file_path)

    def _compute_threshold_hash(self, rpm_bands: 'RPMBands', profile_id: str) -> str:
        """
        Compute SHA256 hash of RPM thresholds and profile ID.

        Args:
            rpm_bands: RPMBands instance with threshold values
            profile_id: Engine profile identifier

        Returns:
            SHA256 hash as hexadecimal string
        """
        # Create sorted tuple of threshold values for consistent hashing
        threshold_values = (
            rpm_bands.idle_max,
            rpm_bands.torque_start,
            rpm_bands.caution_start,
            rpm_bands.warning_start,
            rpm_bands.danger_start,
            rpm_bands.redline_rpm,
            profile_id
        )

        # Create hash input string
        hash_input = '|'.join(str(v) for v in threshold_values)

        # Compute SHA256 hash
        hash_obj = hashlib.sha256(hash_input.encode('utf-8'))
        return hash_obj.hexdigest()

    def is_acknowledged(self, rpm_bands: 'RPMBands', profile_id: str) -> bool:
        """
        Check if current thresholds have been acknowledged.

        Args:
            rpm_bands: Current RPM threshold configuration
            profile_id: Current engine profile ID

        Returns:
            True if acknowledged and hash matches, False otherwise
        """
        if not YAML_AVAILABLE:
            self.logger.warning("PyYAML not available - cannot check acknowledgement state")
            return False

        if not self.state_file_path.exists():
            self.logger.debug("Acknowledgement state file not found - not acknowledged")
            return False

        try:
            # Load state file
            with open(self.state_file_path, 'r') as f:
                state = yaml.safe_load(f)

            if not state or not isinstance(state, dict):
                self.logger.debug("Invalid acknowledgement state file - not acknowledged")
                return False

            # Check acknowledged flag
            if not state.get('acknowledged', False):
                self.logger.debug("Acknowledged flag is False")
                return False

            # Compute current hash
            current_hash = self._compute_threshold_hash(rpm_bands, profile_id)

            # Compare with stored hash
            stored_hash = state.get('threshold_hash', '')
            stored_profile = state.get('profile_id', '')

            if current_hash != stored_hash:
                self.logger.debug(f"Threshold hash mismatch - not acknowledged (profile: {profile_id} vs {stored_profile})")
                return False

            self.logger.debug(f"Thresholds acknowledged for profile '{profile_id}'")
            return True

        except Exception as e:
            self.logger.error(f"Failed to check acknowledgement state: {e}", exc_info=True)
            return False

    def set_acknowledged(self, rpm_bands: 'RPMBands', profile_id: str) -> bool:
        """
        Set thresholds as acknowledged.

        Uses atomic write (temp file + rename) to ensure consistency.

        Args:
            rpm_bands: RPM threshold configuration to acknowledge
            profile_id: Engine profile ID

        Returns:
            True if successfully saved, False otherwise
        """
        if not YAML_AVAILABLE:
            self.logger.error("PyYAML not available - cannot save acknowledgement state")
            return False

        try:
            # Ensure state directory exists
            self.state_file_path.parent.mkdir(parents=True, exist_ok=True)

            # Compute hash
            threshold_hash = self._compute_threshold_hash(rpm_bands, profile_id)

            # Create state data
            state = {
                'acknowledged': True,
                'threshold_hash': threshold_hash,
                'profile_id': profile_id,
                'idle_max': rpm_bands.idle_max,
                'torque_start': rpm_bands.torque_start,
                'caution_start': rpm_bands.caution_start,
                'warning_start': rpm_bands.warning_start,
                'danger_start': rpm_bands.danger_start,
                'redline_rpm': rpm_bands.redline_rpm
            }

            # Atomic write using temp file + rename
            temp_path = self.state_file_path.with_suffix(f'.tmp.{uuid.uuid4().hex[:8]}')

            try:
                with open(temp_path, 'w') as f:
                    yaml.dump(state, f, default_flow_style=False, sort_keys=False)
                    f.flush()
                    os.fsync(f.fileno())

                # Atomic rename
                if os.name == 'nt':  # Windows
                    if self.state_file_path.exists():
                        self.state_file_path.unlink()
                temp_path.rename(self.state_file_path)

                self.logger.debug(f"Acknowledgement state saved for profile '{profile_id}'")
                return True

            except Exception as e:
                # Clean up temp file on error
                if temp_path.exists():
                    temp_path.unlink()
                raise e

        except Exception as e:
            self.logger.error(f"Failed to save acknowledgement state: {e}", exc_info=True)
            return False

    def clear(self) -> bool:
        """
        Clear acknowledgement state (force re-acknowledgement).

        Returns:
            True if state cleared successfully, False otherwise
        """
        try:
            if self.state_file_path.exists():
                self.state_file_path.unlink()
                self.logger.debug("Acknowledgement state cleared")
                return True
            return True

        except Exception as e:
            self.logger.error(f"Failed to clear acknowledgement state: {e}", exc_info=True)
            return False

    def get_state_info(self) -> Optional[Dict[str, Any]]:
        """
        Get current acknowledgement state information.

        Returns:
            Dictionary with state info, or None if state file doesn't exist
        """
        if not YAML_AVAILABLE or not self.state_file_path.exists():
            return None

        try:
            with open(self.state_file_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"Failed to read state info: {e}", exc_info=True)
            return None
