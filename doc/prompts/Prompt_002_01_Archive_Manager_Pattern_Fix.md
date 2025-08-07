# Claude Code Prompt - Archive Manager Pattern Fix

**Created**: 2025 08 07

## Prompt Summary

**Prompt ID**: Prompt_002_01_Archive_Manager_Pattern_Fix
**Task Type**: Bug Fix
**Complexity**: Simple
**Priority**: High

## Context

Test failure in ArchiveManager._should_exclude_file() where pattern `*.pyc` fails to match `file.pyc`. Glob-style wildcard patterns require proper implementation.

## Issue Description

Current pattern matching logic incorrectly handles wildcard patterns, causing test failure for basic file exclusion functionality.

## Claude Code Prompt

```
ITERATION: 002
TASK: Fix Archive Manager File Exclusion Pattern Matching
CONTEXT: Test failure - pattern `*.pyc` not matching `file.pyc`. Current logic fails on glob-style patterns.
PROTOCOL REVIEW REQUIRED:
- Review relevant project protocols from doc/protocol/
- Apply protocol requirements throughout implementation

ISSUE DESCRIPTION:
ArchiveManager._should_exclude_file() method fails test case where pattern `*.pyc` should match `file.pyc`. Current pattern matching logic incorrectly handles glob-style wildcard patterns.

SOLUTION STRATEGY:
Enhance pattern matching to properly handle glob-style patterns with wildcards, specifically `*.extension` format.

IMPLEMENTATION PLAN:
1. Modify _should_exclude_file() method in archive_manager.py
2. Fix wildcard pattern matching logic for `*.ext` format
3. Ensure existing functionality preserved
4. Maintain thread safety

SUCCESS CRITERIA:
- test_should_exclude_file passes
- Pattern `*.pyc` correctly matches `file.pyc`
- All other exclusion patterns continue working
- No regression in existing functionality

DEPENDENCIES:
- src/provisioning/archive_manager.py
- Maintain existing API interface
```

## Expected Outcome

Enhanced pattern matching correctly identifies files for exclusion using glob-style wildcards.

---

**Status**: Complete
**Result**: ✅ Success - Pattern matching fixed, test passes
