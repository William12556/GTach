# Copyright (c) 2025 William Watson
# 
# This file is part of GTach.
# 
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""OBDII RPM Display application package."""

from .app import GTachApplication
from .main import main

__version__ = "0.1.0-alpha.1"
__author__ = "William Watson"

__all__ = [
    'GTachApplication',
    'main',
    '__version__'
]