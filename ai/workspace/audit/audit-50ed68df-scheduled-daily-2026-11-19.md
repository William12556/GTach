Created: 2026 November 19

# GTach Scheduled Daily Audit — 2026-11-19 (audit-50ed68df)

---

## Table of Contents

- [1.0 Purpose](<#1.0 purpose>)
- [2.0 Method](<#2.0 method>)
- [3.0 Activity Summary](<#3.0 activity summary>)
- [4.0 Finding F-01: Substring write-verb matching misclassifies read-only tools](<#4.0 finding f-01: substring write-verb matching misclassifies read-only tools>)
- [5.0 Observations](<#5.0 observations>)
- [6.0 Changes Reviewed Without Finding](<#6.0 changes reviewed without finding>)
- [7.0 Recommendations](<#7.0 recommendations>)
- [Version History](<#version history>)

---

## 1.0 Purpose

This report records the scheduled daily code-review audit of the default branch of William12556/GTach for commits dated 2026-11-18 02:06 UTC to 2026-11-19 02:06 UTC.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Method

- The GitHub MCP route was used for the commit list, commit metadata, tags, file contents, issues and pull requests.
- `get_commit` returned file statistics without patches for both commits. All patches were therefore read via the fallback `git_show` on the local clone, which contained both commits: `ai/engine/config.template.yaml`, `ai/engine/src/approve.py`, `gates.py`, `linter.py`, `manifest.py`, `mcp_client.py`, `orchestrator.py`, `protocol_checker.py`, `providers.py`, `scope.py`, `stages.py`, `ai/governance/software-engineering/manifest.yaml`, `recipes/audit-review.yaml` and `ai/webui/src/overwatch.py`.
- Full files at commit f09aa22 were fetched with `get_file_contents` for `orchestrator.py`, `scope.py`, `mcp_client.py` and `overwatch.py` to check for orphaned references to removed symbols (`uuid`, `Rule`, `pct_str`) and to confirm imports (`datetime` in `overwatch.py`). None were orphaned.
- Documentation (`*.md`) changes were counted, not reviewed.
- Open issues: none. Open pull requests: none.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Activity Summary

| Commit | Author | Date (UTC) | Subject | Files | Insertions | Deletions |
|---|---|---|---|---|---|---|
| f09aa22 | William12556 | 2026-11-18 09:55 | chore(ai): propagate AI-G&O framework v0.3.0 | 32 | 1798 | 451 |
| 73957c1 | William12556 | 2026-11-18 09:58 | docs(audit): Daily scheduled audit. | 2 | 119 | 0 |
| **Total** | | | 2 commits, no merge commits | 34 | 1917 | 451 |

New tags in the window: none.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Finding F-01: Substring write-verb matching misclassifies read-only tools

- Classification: Speculative (the classification is deterministic and visible in the patch; the effect depends on which MCP tools are configured at runtime).
- Severity: Low.
- Location: `ai/engine/src/scope.py`, `WRITE_NAME_PATTERNS`, `is_readonly_tool`, `is_write_tool` (commit f09aa22; change-a5bd4fe1, change-b8c75bac).

The commit makes classification fail-closed and widens the write-verb list:

```python
WRITE_NAME_PATTERNS = (..., r"append", r"copy", r"truncate", r"save", r"update",
                       r"upload", r"set", r"put", r"insert")
...
def is_write_tool(name: str) -> bool:
    return not is_readonly_tool(name)
...
    if name in WRITE_TOOLS or any(re.search(p, name, re.IGNORECASE) for p in WRITE_NAME_PATTERNS):
        return False
```

The verbs are matched as unanchored substrings. `put` matches inside `input` and `output`; `set` matches inside `reset`, `offset`, `asset` and `dataset`. Evaluated with the patched rules, `read_output`, `list_inputs`, `list_assets`, `read_offset` and `search_dataset` are classified as write tools. A read-only tool whose name matches no read-only prefix, such as the reference filesystem server's `directory_tree`, is also now a write tool; before this commit it was neither.

Effect for a tool so classified:

- The reviewer phase does not receive it (`get_openai_tools(readonly=True)`), and `_dispatch_refusal` refuses it.
- In the worker phase `scope.check` applies write rules to it. A directory argument that contains the state directory is refused as "is or contains an engine signal file"; for a T03 prompt task any path outside the deliverables is refused as outside the declared scope.

No tool named in the current engine sources is affected (`read`, `stat`, `diff`, `search`, `count-matches`, `list-files` and `get_file_info` classify as read-only). The defect becomes observable only when a configured MCP server offers such a name.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Observations

- `orchestrator._write_run_record` creates its temporary file with `tempfile.NamedTemporaryFile` and does not apply `_keep_mode`, so `run.json` is written with mode 0600, whereas other state files written by `_write_atomic` receive `0o666 & ~umask`. Overwatch reads the file as the same user; no defect results.
- `main_async` now treats any existing path under `ai/workspace/` as tracked regardless of a work-item UUID. The success message after `prerun_missing` still calls `escape(work_item)`; with `work_item` None this would raise, but `task_document_error` refuses a file name without a UUID, so the branch appears unreachable.

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Changes Reviewed Without Finding

- Atomic writes with `tempfile.mkstemp` and preserved permission bits in `approve.py`, `orchestrator.write_state` and `overwatch._write_text_atomic`, with temporary-file removal on failure.
- `approve.py` rollback of the approvals file and its index entry when `git add` or `git commit` fails.
- `gates.compile_file` with a temporary `PYTHONPYCACHEPREFIX`; project-root containment in `syntax_check` and `run_preflight_check`; `add_collection_pass` status combination (worst of UNCHECKED, FAIL, PASS).
- Syntax gate FAIL now overrides SHIP in `run_loop`.
- `linter.resolve_class` and the class-word rule tables; type checks before membership tests; parse-error reporting in `_parse_yaml_block`; matching updates in `protocol_checker.py`.
- YAML loader hardening (`ValueError`, `TypeError`, `OverflowError`, `RecursionError`) in `manifest.py`, `orchestrator.py`, `scope.py` and `stages.py`.
- Configuration validation before any state write: `_load_config`, `loop.state_dir`, `loop.max_iterations`, `validate_timeout` (maximum 86400 s), `_check_config_blocks`, `_validate_context_windows`, gate `timeout_seconds`, Anthropic `max_tokens`.
- Context-window tier reorder (per-model entry before live query).
- Run record (`run.json`) start and end writes, `rc` assignment before early returns, and exception capture in the `finally` block.
- Rich markup escaping of `[engine]` and `[y/N]`; provider error text escaped in the retry message.
- `stages.is_tracked_task` and `_in_workspace` containment by file identity; non-regular evidence files skipped; `HEAD:./` approvals path.
- `mcp_client` duplicate-tool warning; `_archive_audit_artifacts` non-overwriting archive names.
- Overwatch run-record status logic, marker staleness check, nested class-directory exclusion and FR-02-06 file-identity comparison.
- `audit-review.yaml` 1.2.1: duration-limit exception removed from the coverage check.

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Recommendations

1. F-01: Match write verbs at word boundaries (for example `(^|[_\-.])verb` or a tokenised name) rather than as substrings, and add `^directory_tree` or `^tree` to `READONLY_TOOL_PATTERNS` if such tools are expected. Add unit cases for `read_output`, `list_assets` and `directory_tree`.
2. Optionally apply `_keep_mode` in `_write_run_record` for consistency with the other atomic writes.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-19 | Initial scheduled daily audit report. |

---

Copyright (c) 2026 William Watson. MIT License.
