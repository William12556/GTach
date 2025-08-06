"""OBDII RPM Display application package."""

from .app import OBDIIApplication
from .main import main

__version__ = "0.1.0"
__author__ = "Your Name"

__all__ = [
    'OBDIIApplication',
    'main',
    '__version__'
]