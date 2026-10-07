# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""GTach application package."""

from .app import GTachApplication
from .main import main

# pyproject.toml is the single version source (issue-52653cd6).
from importlib.metadata import version as _version, PackageNotFoundError
try:
    __version__ = _version('gtach')
except PackageNotFoundError:
    __version__ = '0+unknown'
__author__ = "William Watson"

__all__ = [
    'GTachApplication',
    'main',
    '__version__'
]
