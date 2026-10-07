#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Terminal settings restoration for OBDII display application.
Handles saving and restoring terminal settings to ensure proper cleanup.
"""

import os
import sys
import logging
import termios
import atexit

class TerminalRestorer:
    """Manages terminal settings and ensures restoration on exit"""
    
    def __init__(self):
        """Initialize terminal settings backup"""
        self.logger = logging.getLogger('TerminalRestorer')
        self.original_termios = None
        
        # Backup terminal settings right away if we're in a TTY
        if os.isatty(sys.stdin.fileno()):
            try:
                self.original_termios = termios.tcgetattr(sys.stdin.fileno())
                self.logger.debug("Terminal settings backed up")
            except Exception as e:
                self.logger.warning(f"Failed to backup terminal settings: {e}")
        
        # Register cleanup handler to ensure restoration
        atexit.register(self.restore_terminal)
    
    def restore_terminal(self):
        """Restore terminal to original state"""
        if self.original_termios is not None:
            try:
                if os.isatty(sys.stdin.fileno()):
                    termios.tcsetattr(sys.stdin.fileno(), termios.TCSANOW, self.original_termios)
                    self.logger.debug("Terminal settings restored")
            except Exception as e:
                self.logger.error(f"Failed to restore terminal settings: {e}", exc_info=True)

