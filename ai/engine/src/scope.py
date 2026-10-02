"""
Write-tool classification and worker write scope (design-14e05e35 §7.0; change-bdc6820f).

One source for which MCP tools write (audit-5bcd46ad L-09): the scope check,
the loop's deliverable tracking and mcp_client's read-only filter all use
is_write_tool / is_readonly_tool. Classification is fail-closed: a tool is a
write tool when its name is a known write tool or contains a write verb.

For a T03 prompt task the worker may write only (FR-05-01):
    - the prompt's deliverable.files paths (exact files),
    - the governance model manifest's writable_paths (prefixes),
    - the state directory.
Directory creation is allowed for ancestors of those paths. Free-text tasks
and task files that are not T03 prompts keep project-root containment.

change-82dbf16a (audit-14e05e35): engine signal files in the state directory
are never writable by the worker (H-01); a write call with no recognised path
argument is refused (M-01); paths are compared after symlink resolution (L-02).
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field

import yaml

# Known write tools (filesystem-mcp 1.x names and 2.x names, change-c37198be)
WRITE_TOOLS = frozenset({
    "write", "write_file", "create_file",
    "edit", "edit_file",
    "delete", "remove", "delete_file", "remove_file",
    "move", "rename", "move_file", "rename_file",
    "mkdir", "create_directory", "makedirs",
    "create", "patch", "replace_text", "search_and_replace",
})
WRITE_NAME_PATTERNS = (r"replace", r"write", r"edit", r"create", r"delete",
                       r"remove", r"move", r"rename", r"patch", r"mkdir")
READONLY_TOOL_PATTERNS = (r"^read", r"^list", r"^grep", r"^search", r"^stat",
                          r"^get_file_info", r"^find", r"^head", r"^tail", r"^cat")

PATH_KEYS = ("path", "file_path", "destination", "new_path", "source",
             "from", "to", "src", "dst", "target", "newPath")
DEST_KEYS = ("destination", "new_path", "newPath", "to", "dst", "target")
MOVE_TOOLS = ("move", "rename", "move_file", "rename_file")
DELETE_TOOLS = ("delete", "remove", "delete_file", "remove_file")
DIRECTORY_TOOLS = ("mkdir", "create_directory", "makedirs")


def is_write_tool(name: str) -> bool:
    """Fail-closed: a known write tool, or any name containing a write verb."""
    return name in WRITE_TOOLS or any(re.search(p, name) for p in WRITE_NAME_PATTERNS)


def is_readonly_tool(name: str) -> bool:
    """A read-only tool: no write verb, and a read-only name pattern."""
    if is_write_tool(name):
        return False
    return any(re.match(p, name) for p in READONLY_TOOL_PATTERNS)


def path_values(obj: dict, keys: tuple) -> list[str]:
    return [obj[k] for k in keys if isinstance(obj.get(k), str) and obj[k]]


def scope_targets(arguments: dict) -> list[str]:
    """Every path a write call names, including those nested in files/paths/moves/edits."""
    targets = path_values(arguments, PATH_KEYS)
    for item in arguments.get("paths") or []:
        if isinstance(item, str) and item:
            targets.append(item)
    for key in ("files", "moves", "edits"):
        for item in arguments.get(key) or []:
            if isinstance(item, dict):
                targets += path_values(item, PATH_KEYS)
    return targets


def written_targets(tool_name: str, arguments: dict) -> list[str]:
    """
    Paths a successful write call leaves as files: move/rename destinations,
    otherwise the paths written. Delete calls produce no deliverable.
    """
    if tool_name in DELETE_TOOLS:
        return []
    if tool_name in MOVE_TOOLS:
        dests = path_values(arguments, DEST_KEYS)
        for item in arguments.get("moves") or []:
            if isinstance(item, dict):
                dests += path_values(item, DEST_KEYS)
        if dests:
            return dests
        return path_values(arguments, ("path", "file_path"))[:1]
    written = path_values(arguments, ("path", "file_path", "destination"))[:1]
    for item in arguments.get("files") or []:
        if isinstance(item, dict):
            written += path_values(item, ("path", "file_path"))[:1]
    return written


def extract_deliverable_paths(raw: str) -> list[str] | None:
    """
    deliverable.files[].path of a T03 prompt document.

    Returns None when no fenced YAML block carries prompt_info (the task is
    not a T03 prompt), otherwise the declared paths (possibly empty).
    """
    is_prompt = False
    paths: list[str] = []
    for block in re.findall(r"```yaml\n(.*?)```", raw, re.DOTALL):
        try:
            doc = yaml.safe_load(block)
        except yaml.YAMLError:
            continue
        if not isinstance(doc, dict):
            continue
        if "prompt_info" in doc:
            is_prompt = True
        files = (doc.get("deliverable") or {}).get("files") if isinstance(doc.get("deliverable"), dict) else None
        for item in files or []:
            if isinstance(item, dict) and isinstance(item.get("path"), str) and item["path"].strip():
                paths.append(item["path"].strip())
    return paths if is_prompt else None


# Engine-owned state files the worker must not write (change-82dbf16a, H-01).
# work-summary.txt, work-complete.txt and BLOCKED.md stay writable: the work
# recipes instruct the worker to write them, and none can produce SHIP.
SIGNAL_FILES = ("review-result.txt", "review-feedback.txt", ".complete", ".timeout",
                "awaiting-approval.md", "mcp-run.json", "iteration.txt", "task.md",
                "context-budget.md")


def signal_files(state_dir: str) -> frozenset[str]:
    """
    Resolved absolute paths of the engine signal files in state_dir,
    case-folded (F-05: macOS volumes are normally case-insensitive).
    """
    return frozenset(_real(os.path.join(state_dir, f)).casefold() for f in SIGNAL_FILES)


def _real(path: str) -> str:
    """Absolute path with symlinks resolved (L-02)."""
    return os.path.realpath(os.path.abspath(path))


def _within(path: str, root: str) -> bool:
    return path == root or path.startswith(root.rstrip(os.sep) + os.sep)


@dataclass
class WriteScope:
    project_root: str
    files: set[str] = field(default_factory=set)      # absolute deliverable files
    prefixes: list[str] = field(default_factory=list)  # absolute directories (writable_paths, state dir)

    def allows(self, path: str, directory: bool = False) -> bool:
        if path in self.files or any(_within(path, p) for p in self.prefixes):
            return True
        # Creating a directory on the way to an allowed path
        return directory and any(_within(target, path) for target in list(self.files) + self.prefixes)

    def describe(self) -> str:
        rel = sorted(os.path.relpath(p, self.project_root) for p in self.files)
        rel += [os.path.relpath(p, self.project_root).rstrip(os.sep) + "/" for p in self.prefixes]
        return ", ".join(rel) or "(nothing)"


def build_write_scope(project_root: str, deliverables: list[str], writable_paths: list[str],
                      state_dir: str) -> WriteScope:
    """Resolve declared paths against the project root."""
    root = _real(project_root)

    def absolute(p: str) -> str:
        return _real(p if os.path.isabs(p) else os.path.join(root, p))

    return WriteScope(project_root=root,
                      files={absolute(p) for p in deliverables},
                      prefixes=[absolute(p) for p in writable_paths] + [_real(state_dir)])


@dataclass
class Violation:
    path: str
    reason: str
    message: str


def check(tool_name: str, arguments: dict, project_root: str,
          write_scope: WriteScope | None = None,
          protected: frozenset[str] = frozenset()) -> Violation | None:
    """
    Pre-dispatch check of one tool call. None when allowed or not a write tool.
    Every path a call touches is checked (change-d1f4a83b N2), including the
    source and destination of a move. protected holds resolved paths no write
    may touch (engine signal files, change-82dbf16a H-01). A write call with no
    recognised path argument is refused (M-01).
    """
    if not is_write_tool(tool_name):
        return None
    targets = scope_targets(arguments)
    if not targets:
        return Violation("(none)", "no recognised path argument",
                         f"write refused: tool '{tool_name}' was called without a recognised "
                         f"path argument ({', '.join(PATH_KEYS)}, paths, files, moves, edits)")
    root = _real(project_root)
    for target in targets:
        try:
            resolved = _real(target)
        except Exception:
            continue  # malformed path: left to the MCP server
        if not _within(resolved, root):
            return Violation(target, "outside the project root",
                             f"Scope violation: path '{target}' is outside the project root "
                             f"'{project_root}'. All writes must target paths within the project.")
        # F-04, F-05: a target equal to a signal file, or a directory holding
        # one (tools such as replace_text rewrite under a directory), is refused.
        folded = resolved.casefold()
        if any(p == folded or _within(p, folded) for p in protected):
            return Violation(target, "engine signal file",
                             f"write refused: {target} is or contains an engine signal file; "
                             f"only the engine writes it")
        if write_scope is not None and not write_scope.allows(resolved, tool_name in DIRECTORY_TOOLS):
            return Violation(target, "outside the declared scope",
                             f"write outside the declared scope: {target}; "
                             f"allowed: {write_scope.describe()}")
    return None
