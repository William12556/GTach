"""
Unit tests for parser.py — Mistral tool call parser.
No external dependencies; runs without oMLX or MCP.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from parser import parse_tool_calls


# ── No tool calls ──────────────────────────────────────────────────────────────

def test_empty_string():
    assert parse_tool_calls("") == []


def test_no_marker():
    assert parse_tool_calls("The answer is 42.") == []


def test_unrelated_brackets():
    assert parse_tool_calls("[RESULT] something") == []


# ── Format 1: official Mistral JSON array ─────────────────────────────────────

def test_format1_single_call():
    content = '[TOOL_CALLS] [{"name": "list_directory", "arguments": {"path": "/tmp"}}]'
    result = parse_tool_calls(content)
    assert len(result) == 1
    assert result[0]["name"] == "list_directory"
    assert result[0]["arguments"] == {"path": "/tmp"}


def test_format1_multiple_calls():
    content = (
        '[TOOL_CALLS] ['
        '{"name": "read_file", "arguments": {"path": "/a"}},'
        '{"name": "write_file", "arguments": {"path": "/b", "content": "x"}}'
        ']'
    )
    result = parse_tool_calls(content)
    assert len(result) == 2
    assert result[0]["name"] == "read_file"
    assert result[1]["name"] == "write_file"


def test_format1_empty_arguments():
    content = '[TOOL_CALLS] [{"name": "list_roots", "arguments": {}}]'
    result = parse_tool_calls(content)
    assert result[0]["arguments"] == {}


def test_format1_missing_arguments_key():
    content = '[TOOL_CALLS] [{"name": "list_roots"}]'
    result = parse_tool_calls(content)
    assert result[0]["name"] == "list_roots"
    assert result[0]["arguments"] == {}


def test_format1_malformed_json_falls_through_to_format2():
    # Malformed JSON in format 1 — parser falls through; no format-2 marker so returns []
    content = '[TOOL_CALLS] [{"name": "bad" INVALID}]'
    result = parse_tool_calls(content)
    assert result == []


# ── Format 2: plain-text variant ──────────────────────────────────────────────

def test_format2_single_call():
    content = '[TOOL_CALLS]grep_search[ARGS]{"pattern": "foo", "path": "/tmp"}'
    result = parse_tool_calls(content)
    assert len(result) == 1
    assert result[0]["name"] == "grep_search"
    assert result[0]["arguments"] == {"pattern": "foo", "path": "/tmp"}


def test_format2_multiple_calls():
    content = (
        '[TOOL_CALLS]read_file[ARGS]{"path": "/a"}'
        '[TOOL_CALLS]write_file[ARGS]{"path": "/b", "content": "hello"}'
    )
    result = parse_tool_calls(content)
    assert len(result) == 2
    assert result[0]["name"] == "read_file"
    assert result[1]["name"] == "write_file"


def test_format2_malformed_args_returns_empty_dict():
    # Non-JSON without braces: raw_decode fails, arguments fallback to {}
    content = '[TOOL_CALLS]some_tool[ARGS]NOT_JSON'
    result = parse_tool_calls(content)
    assert result[0]["name"] == "some_tool"
    assert result[0]["arguments"] == {}


def test_format2_malformed_args_with_braces_returns_empty_dict():
    # Malformed JSON inside braces: name parsed, arguments fallback to {}
    content = '[TOOL_CALLS]some_tool[ARGS]{NOT_JSON}'
    result = parse_tool_calls(content)
    assert result[0]["name"] == "some_tool"
    assert result[0]["arguments"] == {}


def test_format2_nested_arguments():
    content = '[TOOL_CALLS]create_file[ARGS]{"path": "/tmp/x.txt", "content": "line1\\nline2"}'
    result = parse_tool_calls(content)
    assert result[0]["arguments"]["content"] == "line1\nline2"


# ── Tool call ID not present in parser output ─────────────────────────────────

def test_no_id_in_parser_output():
    content = '[TOOL_CALLS] [{"name": "tool", "arguments": {}}]'
    result = parse_tool_calls(content)
    assert "id" not in result[0]


# ── Surrounding text ──────────────────────────────────────────────────────────

def test_format1_with_surrounding_text():
    content = 'I will call the tool now.\n[TOOL_CALLS] [{"name": "ping", "arguments": {}}]\nDone.'
    result = parse_tool_calls(content)
    assert result[0]["name"] == "ping"


def test_format2_with_surrounding_text():
    content = 'Calling tool:\n[TOOL_CALLS]ping[ARGS]{}\nDone.'
    result = parse_tool_calls(content)
    assert result[0]["name"] == "ping"


# ── Format 1 improvements ─────────────────────────────────────────────────────

def test_format1_nested_array_in_arguments():
    # Nested array value must not truncate at first ']'
    content = '[TOOL_CALLS] [{"name": "grep", "arguments": {"paths": ["/a", "/b"]}}]'
    result = parse_tool_calls(content)
    assert len(result) == 1
    assert result[0]["arguments"]["paths"] == ["/a", "/b"]


def test_format1_bare_object():
    # Single bare object (not wrapped in array)
    content = '[TOOL_CALLS] {"name": "list_roots", "arguments": {}}'
    result = parse_tool_calls(content)
    assert len(result) == 1
    assert result[0]["name"] == "list_roots"


def test_format1_parallel_calls_multiple_blocks():
    # Parallel calls emitted as separate [TOOL_CALLS] blocks
    content = (
        '[TOOL_CALLS] [{"name": "tool1", "arguments": {"a": 1}}]\n\n'
        '[TOOL_CALLS] [{"name": "tool2", "arguments": {"b": 2}}]'
    )
    result = parse_tool_calls(content)
    assert len(result) == 2
    assert result[0]["name"] == "tool1"
    assert result[1]["name"] == "tool2"


# ── Format 2 whitespace tolerance ─────────────────────────────────────────────

def test_format2_whitespace_between_markers():
    # Space between [TOOL_CALLS] and tool name must be tolerated
    content = '[TOOL_CALLS] grep_search[ARGS]{"pattern": "foo"}'
    result = parse_tool_calls(content)
    assert len(result) == 1
    assert result[0]["name"] == "grep_search"
