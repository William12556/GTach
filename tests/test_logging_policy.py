#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Tracebacks on every error logged from a broad exception handler.

Covers change-269871a0 EDIT B and CLAUDE.md §4 rule 6: unexpected
exceptions are logged with ``logger.error(msg, exc_info=True)``.

A handler is broad if its type is absent (bare ``except:``),
``Exception``, ``BaseException``, or a tuple containing either. Every
``<expr>.error(...)`` or ``<expr>.critical(...)`` call in such a
handler's body must pass an ``exc_info`` keyword. An explicit
``exc_info=False`` is a deliberate choice and is not a violation.
"""

import ast
import pathlib
from typing import List

SRC_ROOT = pathlib.Path(__file__).resolve().parents[1] / 'src' / 'gtach'

_BROAD_NAMES = {'Exception', 'BaseException'}
_LOG_METHODS = {'error', 'critical'}

# Calls matching the rule that are not logger calls, as 'path:line'
# relative to src/gtach. Each entry must say what the call is.
NON_LOGGER_ALLOWLIST: set = set()


def _is_broad(handler: ast.ExceptHandler) -> bool:
    """Whether an except clause catches Exception or wider."""
    exc_type = handler.type
    if exc_type is None:
        return True
    if isinstance(exc_type, ast.Name):
        return exc_type.id in _BROAD_NAMES
    if isinstance(exc_type, ast.Tuple):
        return any(isinstance(e, ast.Name) and e.id in _BROAD_NAMES
                   for e in exc_type.elts)
    return False


def find_violations(source: str, filename: str = '<string>') -> List[str]:
    """Return 'filename:line' for each error/critical call lacking exc_info.

    Args:
        source: Python source text.
        filename: Label used in the returned entries.

    Returns:
        Sorted, de-duplicated violation locations.
    """
    tree = ast.parse(source, filename=filename)
    found = set()
    for handler in ast.walk(tree):
        if not isinstance(handler, ast.ExceptHandler) or not _is_broad(handler):
            continue
        for statement in handler.body:
            for node in ast.walk(statement):
                if not isinstance(node, ast.Call):
                    continue
                func = node.func
                if not (isinstance(func, ast.Attribute) and func.attr in _LOG_METHODS):
                    continue
                if any(kw.arg == 'exc_info' for kw in node.keywords):
                    continue
                found.add((node.lineno, f'{filename}:{node.lineno}'))
    return [label for _line, label in sorted(found)]


def _source_files():
    return sorted(SRC_ROOT.rglob('*.py'))


def test_no_broad_handler_logs_an_error_without_a_traceback():
    violations = []
    for path in _source_files():
        relative = path.relative_to(SRC_ROOT).as_posix()
        for label in find_violations(path.read_text(encoding='utf-8'), relative):
            if label not in NON_LOGGER_ALLOWLIST:
                violations.append(label)

    assert violations == [], (
        f'{len(violations)} error/critical call(s) in broad handlers lack '
        f'exc_info:\n' + '\n'.join(violations)
    )


def test_checker_detects_a_synthetic_violation():
    source = (
        'import logging\n'
        'logger = logging.getLogger(__name__)\n'
        'try:\n'
        '    pass\n'
        'except Exception as e:\n'
        '    logger.error(f"failed: {e}")\n'
        'try:\n'
        '    pass\n'
        'except ValueError:\n'
        '    logger.error("narrow handlers are not checked")\n'
        'try:\n'
        '    pass\n'
        'except Exception:\n'
        '    logger.error("explicit choice", exc_info=False)\n'
    )

    assert find_violations(source, 'synthetic.py') == ['synthetic.py:6']


def test_checker_covers_bare_tuple_and_nested_handlers():
    source = (
        'try:\n'
        '    pass\n'
        'except:\n'
        '    log.critical("bare")\n'
        'try:\n'
        '    pass\n'
        'except (OSError, Exception):\n'
        '    try:\n'
        '        pass\n'
        '    except BaseException:\n'
        '        log.error("nested")\n'
    )

    assert find_violations(source, 's.py') == ['s.py:4', 's.py:11']
