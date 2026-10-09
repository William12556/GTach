# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""GTach application package."""

# pyproject.toml is the single version source (issue-52653cd6).
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _version

try:
    __version__ = _version("gtach")
except PackageNotFoundError:
    __version__ = "0+unknown"
__author__ = "William Watson"

# No re-exports: importing gtach must not import gtach.app or pygame
# (issue-2b3a1547).
__all__ = ["__version__"]
