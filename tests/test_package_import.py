# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Importing gtach does not import gtach.app or pygame (issue-2b3a1547).

Each check runs in a fresh interpreter, since this test process has
already imported both.
"""

import subprocess
import sys


def _run(*args):
    return subprocess.run(
        [sys.executable, *args], capture_output=True, text=True, timeout=60
    )


def test_import_main_does_not_import_app_or_pygame():
    result = _run(
        "-c",
        "import sys, gtach.main; "
        "assert 'pygame' not in sys.modules and 'gtach.app' not in sys.modules",
    )
    assert result.returncode == 0, result.stderr


def test_version_is_available():
    result = _run("-c", "import gtach; print(gtach.__version__)")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip()


def test_module_entry_point_version():
    result = _run("-m", "gtach", "--version")
    assert result.returncode == 0, result.stderr
