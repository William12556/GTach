#!/usr/bin/env python3
"""
Terminal settings restoration for OBDII display application.
Handles saving and restoring terminal settings to ensure proper cleanup.
"""

import os
import sys
import logging
import termios
import atexit
import fcntl
import struct

class TerminalRestorer:
    """Manages terminal settings and ensures restoration on exit"""
    
    def __init__(self):
        """Initialize terminal settings backup"""
        self.logger = logging.getLogger('TerminalRestorer')
        self.original_termios = None
        self.original_fb_settings = None
        self.fb_fd = None
        
        # Backup terminal settings right away if we're in a TTY
        if os.isatty(sys.stdin.fileno()):
            try:
                self.original_termios = termios.tcgetattr(sys.stdin.fileno())
                self.logger.debug("Terminal settings backed up")
            except Exception as e:
                self.logger.warning(f"Failed to backup terminal settings: {e}")
        
        # Register cleanup handler to ensure restoration
        atexit.register(self.restore_terminal)
    
    def backup_framebuffer_settings(self, fb_path='/dev/fb0'):
        """Backup framebuffer settings if possible"""
        try:
            if os.path.exists(fb_path):
                self.fb_fd = os.open(fb_path, os.O_RDWR)
                # Attempt to get current framebuffer variable screen info
                # FBIOGET_VSCREENINFO = 0x4600
                self.original_fb_settings = fcntl.ioctl(self.fb_fd, 0x4600, struct.pack('64s', b'\0' * 64))
                self.logger.debug("Framebuffer settings backed up")
        except Exception as e:
            self.logger.warning(f"Failed to backup framebuffer settings: {e}")
    
    def restore_terminal(self):
        """Restore terminal to original state"""
        if self.original_termios is not None:
            try:
                if os.isatty(sys.stdin.fileno()):
                    termios.tcsetattr(sys.stdin.fileno(), termios.TCSANOW, self.original_termios)
                    self.logger.debug("Terminal settings restored")
            except Exception as e:
                self.logger.error(f"Failed to restore terminal settings: {e}")
        
        # Restore framebuffer settings if we have them
        if self.original_fb_settings is not None and self.fb_fd is not None:
            try:
                # FBIOPUT_VSCREENINFO = 0x4601
                fcntl.ioctl(self.fb_fd, 0x4601, self.original_fb_settings)
                self.logger.debug("Framebuffer settings restored")
            except Exception as e:
                self.logger.error(f"Failed to restore framebuffer settings: {e}")
        
        # Close framebuffer if open
        if self.fb_fd is not None:
            try:
                os.close(self.fb_fd)
                self.fb_fd = None
            except Exception as e:
                self.logger.error(f"Failed to close framebuffer: {e}")
        
        # Reset terminal settings directly using stty if all else fails
        try:
            os.system('stty sane')
        except Exception as e:
            self.logger.error(f"Failed to reset terminal with stty: {e}")
