"""
Mistral tool call parser.

Parses tool calls from model response content field.
Handles two observed formats:

  1. Official Mistral JSON array:
       [TOOL_CALLS] [{"name": "func", "arguments": {"k": "v"}}]

  2. Plain-text variant (observed with Devstral via oMLX):
       [TOOL_CALLS]tool_name[ARGS]{"k": "v"}
"""

import json
import re
from typing import Any


def parse_tool_calls(content: str) -> list[dict[str, Any]]:
    """
    Extract tool calls from content string.
    Returns list of {"name": str, "arguments": dict}.
    Returns empty list if no tool calls found.
    """
    if "[TOOL_CALLS]" not in content:
        return []

    # Format 1: official Mistral JSON array
    json_match = re.search(r"\[TOOL_CALLS\]\s*(\[.*?\])", content, re.DOTALL)
    if json_match:
        try:
            calls = json.loads(json_match.group(1))
            return [
                {"name": c["name"], "arguments": c.get("arguments", {})}
                for c in calls
                if "name" in c
            ]
        except (json.JSONDecodeError, KeyError):
            pass

    # Format 2: plain-text variant
    results = []
    for match in re.finditer(r"\[TOOL_CALLS\](\w+)\[ARGS\](\{.*?\})", content, re.DOTALL):
        name = match.group(1)
        try:
            arguments = json.loads(match.group(2))
        except json.JSONDecodeError:
            arguments = {}
        results.append({"name": name, "arguments": arguments})

    return results
