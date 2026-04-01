# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Package entry point for python -m gtach invocation."""

import sys
from .main import main

if __name__ == '__main__':
    sys.exit(main())
