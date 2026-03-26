"""
Mistral tool call parser.

Parses tool calls from model response content field.
Handles two observed formats:

  1. Official Mistral JSON array (single or multiple blocks, array or bare object):
       [TOOL_CALLS] [{"name": "func", "arguments": {"k": "v"}}]
       [TOOL_CALLS] {"name": "func", "arguments": {"k": "v"}}

     Parallel calls may appear as multiple [TOOL_CALLS] blocks:
       [TOOL_CALLS] [{"name": "tool1", "arguments": {...}}]
       [TOOL_CALLS] [{"name": "tool2", "arguments": {...}}]

  2. Plain-text variant (observed with Devstral via oMLX):
       [TOOL_CALLS]tool_name[ARGS]{"k": "v"}
"""

import json
import re
from typing import Any


def _sanitize_json_string(s: str) -> str:
    """
    Replace literal newlines/carriage-returns inside JSON string literals
    with their escape sequences. Devstral emits multi-line argument values
    with bare newlines which cause JSONDecodeError in raw_decode.
    """
    result = []
    in_string = False
    escaped = False
    for ch in s:
        if escaped:
            result.append(ch)
            escaped = False
        elif ch == '\\':
            result.append(ch)
            escaped = True
        elif ch == '"':
            in_string = not in_string
            result.append(ch)
        elif in_string and ch == '\n':
            result.append('\\n')
        elif in_string and ch == '\r':
            result.append('\\r')
        else:
            result.append(ch)
    return ''.join(result)


def parse_tool_calls(content: str) -> list[dict[str, Any]]:
    """
    Extract tool calls from content string.
    Returns list of {"name": str, "arguments": dict}.
    Returns empty list if no tool calls found.
    """
    if "[TOOL_CALLS]" not in content:
        return []

    decoder = json.JSONDecoder()
    results: list[dict[str, Any]] = []
    seen: set[tuple] = set()

    def _append(name: str, arguments: dict) -> None:
        key = (name, json.dumps(arguments, sort_keys=True))
        if key not in seen:
            seen.add(key)
            results.append({"name": name, "arguments": arguments})

    # Format 1: [TOOL_CALLS] followed by a JSON array or bare object.
    # Use raw_decode for bracket-balanced extraction — handles nested arrays in
    # argument values and parallel calls emitted as separate [TOOL_CALLS] blocks.
    f1_consumed: set[int] = set()
    for m in re.finditer(r"\[TOOL_CALLS\]\s*", content):
        start = m.end()
        if start >= len(content):
            continue
        # Only attempt if the next non-whitespace char starts a JSON value
        peek = content[start] if start < len(content) else ""
        if peek not in ('[', '{'):
            continue
        try:
            value, _ = decoder.raw_decode(content, start)
        except json.JSONDecodeError:
            continue
        if isinstance(value, list):
            for c in value:
                if isinstance(c, dict) and "name" in c:
                    _append(c["name"], c.get("arguments") or {})
                    f1_consumed.add(m.start())
        elif isinstance(value, dict) and "name" in value:
            _append(value["name"], value.get("arguments") or {})
            f1_consumed.add(m.start())

    if results:
        return results

    # Format 2: plain-text variant [TOOL_CALLS]name[ARGS]{...}
    # Whitespace between markers is tolerated.
    for match in re.finditer(r"\[TOOL_CALLS\]\s*(\w+)\s*\[ARGS\]", content):
        name = match.group(1)
        start = match.end()
        while start < len(content) and content[start] in " \t\n":
            start += 1
        try:
            arguments, _ = decoder.raw_decode(content, start)
        except json.JSONDecodeError:
            try:
                sanitized = _sanitize_json_string(content[start:])
                arguments, _ = decoder.raw_decode(sanitized, 0)
            except json.JSONDecodeError:
                arguments = {}
        _append(name, arguments)

    return results
