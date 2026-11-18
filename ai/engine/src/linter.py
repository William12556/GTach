"""
Layer 1 Governance Linter — Static validation of workspace documents.

Checks:
  1. File naming conventions  (P00.10)
  2. Markdown structure       (Version History, Created timestamp, copyright)
  3. YAML field validity      (schema_type, id pattern, enum values, iteration)
  4. UUID coupling integrity  (P04.2, P03.7, P15.12, P13.2)
  5. Internal link targets    (P12.9; GitHub heading anchors)

Usage:
    python linter.py <workspace_dir>
    python -m pytest tests/engine/test_linter.py -v

Exit codes:
    0  — no errors (warnings may be present)
    1  — one or more ERROR findings
"""

import argparse
import os
import re
import sys
import unicodedata
from dataclasses import dataclass
from typing import Optional

import yaml

# ── Constants ─────────────────────────────────────────────────────────────────

VALID_CLASSES = frozenset({
    "design", "change", "issue", "prompt",
    "test", "result", "audit", "trace", "requirements",
    "proposal", "report",
})

MASTER_RE    = re.compile(r"^([a-z]+)-(.+)-master\.md$")
NORMAL_RE    = re.compile(r"^([a-z]+)-([0-9a-f]{8})-(.+)\.md$")
YAML_BLOCK_RE = re.compile(r"```yaml\n(.*?)```", re.DOTALL)
HEADING_RE   = re.compile(r"^#{1,6}\s+(.+)$", re.MULTILINE)
VH_HEADING_RE = re.compile(r"^#{1,6}\s+version history\s*$", re.IGNORECASE | re.MULTILINE)
VH_KEY_RE    = re.compile(r"^\s*version_history:", re.MULTILINE)
LINK_RE      = re.compile(r"\[[^\]]*\]\(<([^>]*)>|\[[^\]]*\]\(([^)]+)\)")

# Document classes named by metadata.schema_type (change-e4428fd5, audit-caab2052
# M-03; operator decisions 2026-11-05, 2026-11-07). Numbered values of both
# schemes (t0N_<class>) are accepted as aliases.
CLASS_WORDS = ("requirements", "design", "prompt", "test",
               "result", "issue", "change", "audit")

# Root key → class, used when metadata.schema_type is absent (change-e4428fd5;
# T03 prompts carry no governance metadata).
ROOT_KEYS = {
    "prompt_info": "prompt",
    "test_info":   "test",
    "result_info": "result",
    "issue_info":  "issue",
    "change_info": "change",
    "audit_info":  "audit",
}

NUMBERED_SCHEMA_RE = re.compile(
    r"^t0[1-8]_(requirements|design|prompt|test|result|issue|change|audit)$")

MISSING_SCHEMA_TYPE = "YAML block present but metadata.schema_type is missing"

# Rule tables below are keyed by class word (change-e4428fd5, audit-caab2052 M-03).

# Enum constraints per class (P00.10, template schemas)
_ENUMS: dict[str, dict[str, frozenset]] = {
    "change": {
        "change_info.status":   frozenset({"proposed", "approved", "implemented", "verified", "rejected"}),
        "change_info.priority": frozenset({"critical", "high", "medium", "low"}),
    },
    "issue": {
        "issue_info.status":   frozenset({"open", "investigating", "resolved", "verified", "closed", "deferred"}),
        "issue_info.severity": frozenset({"critical", "high", "medium", "low"}),
        "issue_info.type":     frozenset({"bug", "defect", "error", "performance", "security",
                                           "enhancement", "requirement_change"}),
    },
    "prompt": {
        "prompt_info.task_type": frozenset({"code_generation", "debug", "refactor", "optimization"}),
        "prompt_info.priority":  frozenset({"critical", "high", "medium", "low"}),
    },
    "test": {
        # change-e4428fd5 (GTach observation 2026-10-08): superseded is terminal
        "test_info.status":   frozenset({"planned", "in_progress", "executed", "passed", "failed",
                                         "blocked", "superseded"}),
        "test_info.type":     frozenset({"unit", "integration", "system", "acceptance", "regression", "performance"}),
        "test_info.priority": frozenset({"critical", "high", "medium", "low"}),
    },
    "result": {
        "result_info.status": frozenset({"passed", "failed", "blocked", "partial"}),
    },
}

# ID field path and regex pattern per class
_ID_FIELDS: dict[str, tuple[str, str]] = {
    "change": ("change_info.id",  r"^change-[0-9a-f]{8}$"),
    "issue":  ("issue_info.id",   r"^issue-[0-9a-f]{8}$"),
    "prompt": ("prompt_info.id",  r"^prompt-[0-9a-f]{8}$"),
    "test":   ("test_info.id",    r"^test-[0-9a-f]{8}$"),
    "result": ("result_info.id",  r"^result-[0-9a-f]{8}$"),
}

# Iteration field path per class
_ITER_FIELDS: dict[str, str] = {
    "change": "change_info.iteration",
    "issue":  "issue_info.iteration",
    "prompt": "prompt_info.iteration",
    "test":   "test_info.iteration",
    "result": "result_info.iteration",
}

# Outgoing coupling reference per class:
#   (ref_field_path, own_iteration_path, coupled_iteration_path)
_COUPLING: dict[str, tuple[str, str, str]] = {
    "change": (
        "change_info.coupled_docs.issue_ref",
        "change_info.iteration",
        "change_info.coupled_docs.issue_iteration",
    ),
    "prompt": (
        "prompt_info.coupled_docs.change_ref",
        "prompt_info.iteration",
        "prompt_info.coupled_docs.change_iteration",
    ),
    "test": (
        "test_info.coupled_docs.prompt_ref",
        "test_info.iteration",
        "test_info.coupled_docs.prompt_iteration",
    ),
    "result": (
        "result_info.coupled_docs.test_ref",
        "result_info.iteration",
        "result_info.coupled_docs.test_iteration",
    ),
}


# ── Data types ────────────────────────────────────────────────────────────────

@dataclass
class Finding:
    severity: str  # ERROR | WARN
    path:     str
    check:    str
    message:  str

    def __str__(self) -> str:
        return f"{self.severity:<5} [{self.check}] {self.path}: {self.message}"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get(obj: dict, dotpath: str):
    """Traverse dotted key path in nested dict; return None on any miss."""
    for key in dotpath.split("."):
        if not isinstance(obj, dict):
            return None
        obj = obj.get(key)
    return obj


# change-f68d51c2 (audit-9377f9b9-followup F-01): exceptions PyYAML's
# constructors raise for scalars they cannot convert
_YAML_VALUE_ERRORS = (ValueError, TypeError, OverflowError)


def _parse_yaml_block(content: str) -> tuple[object | None, str | None]:
    """Parse the first YAML fenced block in markdown content.

    change-9377f9b9 (audit-e4428fd5 F-01, F-02). Returns (data, problem):
    (None, None) without a fenced YAML block; (data, None) for a block that
    loads; (None, problem) for a block that does not parse, problem being
    the YAMLError's problem text (or the first line of its message), or
    'nesting too deep' for a RecursionError. Never raises.
    """
    m = YAML_BLOCK_RE.search(content)
    if not m:
        return None, None
    try:
        return yaml.safe_load(m.group(1)), None
    except yaml.YAMLError as e:
        problem = getattr(e, "problem", None)
        if not isinstance(problem, str) or not problem:
            problem = (str(e).splitlines() or [""])[0]
        return None, problem
    except RecursionError:
        return None, "nesting too deep"
    except _YAML_VALUE_ERRORS as e:
        # change-f68d51c2 (audit-9377f9b9-followup F-01): a scalar the
        # constructor cannot convert (an invalid date, for one)
        return None, (str(e).splitlines() or [type(e).__name__])[0]


def _extract_yaml(content: str) -> Optional[dict]:
    """Parse first YAML fenced block in markdown content.

    change-9377f9b9 (audit-e4428fd5 F-01, F-02): the data element of
    _parse_yaml_block, so it never raises; None when no block parses.
    """
    return _parse_yaml_block(content)[0]


def _github_slug(text: str) -> str:
    """Return the GitHub heading anchor for a heading text.

    Lowercase; inline links reduced to their text; backslashes, asterisks
    and backticks removed; every character that is not a letter, digit,
    space, hyphen or underscore removed; each space becomes a hyphen.
    """
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[\\*`]", "", text).strip().lower()
    text = "".join(c for c in text
                   if c in "-_ " or unicodedata.category(c)[0] in "LN")
    return text.replace(" ", "-")


def _headings(content: str) -> frozenset:
    """Return the GitHub heading anchors of the headings in markdown content.

    Repeated headings receive the suffixes -1, -2, ... as on GitHub.
    """
    anchors: set[str] = set()
    seen: dict[str, int] = {}
    for m in HEADING_RE.finditer(content):
        slug = _github_slug(m.group(1).strip().rstrip("#").strip())
        n = seen.get(slug, 0)
        seen[slug] = n + 1
        anchors.add(slug if n == 0 else f"{slug}-{n}")
    return frozenset(anchors)


def resolve_class(data: dict,
                  path: Optional[str] = None) -> tuple[Optional[str], Optional[str]]:
    """
    Resolve a governance document's class from its first YAML block.

    change-e4428fd5 (audit-caab2052 M-03; operator decisions 2026-11-05,
    2026-11-07). With metadata.schema_type present: a class word gives that
    class; a numbered value t01_ to t08_ followed by a class word gives the
    class word; any other value gives no class and a message. With
    schema_type absent: the class of the first top-level key in ROOT_KEYS.
    change-e4428fd5 amendment 1 (operator decision 2026-11-07, option V3):
    when path is given, the root-key class is used only if no component of
    path is 'closed' and the file name's prefix before the first '-' equals
    that class; otherwise the schema_type is reported missing. With path
    None the root-key rule applies without these conditions.
    Returns (class, message); message is set when class is None.
    """
    schema_type = _get(data, "metadata.schema_type")
    if schema_type is not None:
        if not isinstance(schema_type, str):
            return None, "metadata.schema_type must be a string"
        if schema_type in CLASS_WORDS:
            return schema_type, None
        m = NUMBERED_SCHEMA_RE.fullmatch(schema_type)
        if m:
            return m.group(1), None
        return None, f"unknown schema_type '{schema_type}'"
    for key in data:
        if key in ROOT_KEYS:
            doc_class = ROOT_KEYS[key]
            # change-e4428fd5 amendment 1 (operator decision 2026-11-07)
            if path is not None:
                parts = re.split(r"[\\/]", path)
                if ("closed" in parts
                        or parts[-1].split("-", 1)[0] != doc_class):
                    return None, MISSING_SCHEMA_TYPE
            return doc_class, None
    return None, MISSING_SCHEMA_TYPE


def _is_governance_doc(fname: str) -> bool:
    return bool(MASTER_RE.match(fname) or NORMAL_RE.match(fname))


# ── Check 1: file naming (P00.10) ───────────────────────────────────────

def check_naming(fname: str, path: str) -> list[Finding]:
    """Verify document class is recognised in master and normal naming patterns."""
    findings = []
    master = MASTER_RE.match(fname)
    normal = NORMAL_RE.match(fname)

    if master:
        doc_class = master.group(1)
        if doc_class not in VALID_CLASSES:
            findings.append(Finding("ERROR", path, "naming",
                f"unknown document class '{doc_class}'"))
    elif normal:
        doc_class = normal.group(1)
        if doc_class not in VALID_CLASSES:
            findings.append(Finding("ERROR", path, "naming",
                f"unknown document class '{doc_class}'"))
    # Non-governance files (README.md, etc.) are silently ignored.

    return findings


# ── Check 2: markdown structure ───────────────────────────────────────────────

def check_structure(path: str, content: str, fname: str = "") -> list[Finding]:
    """
    Verify mandatory markdown sections are present.

    change-51f1aef0: version history is satisfied by a markdown heading or a
    YAML version_history key; prompt documents are exempt (single-use,
    versioned by their iteration field and git).
    """
    findings = []
    lower = content.lower()
    m = MASTER_RE.match(fname) or NORMAL_RE.match(fname)
    doc_class = m.group(1) if m else None

    if (doc_class != "prompt"
            and not VH_HEADING_RE.search(content)
            and not VH_KEY_RE.search(content)):
        findings.append(Finding("ERROR", path, "structure",
            "missing 'Version History' section"))

    if not re.search(r"^created:", content, re.IGNORECASE | re.MULTILINE):
        findings.append(Finding("WARN", path, "structure",
            "missing 'Created:' timestamp"))

    if "copyright" not in lower:
        findings.append(Finding("WARN", path, "structure",
            "missing copyright line"))

    return findings


# ── Check 3: YAML field validity (template schemas) ───────────────────────────

def check_yaml(path: str, content: str,
               workspace_dir: Optional[str] = None,
               ) -> tuple[list[Finding], Optional[dict], Optional[str]]:
    """
    Extract and validate first YAML block.
    Returns (findings, parsed_data, doc_class).

    change-e4428fd5 (audit-caab2052 M-03, L-11): the class is resolved by
    resolve_class and returned in place of the raw schema_type; a class
    without rules (requirements, design, audit) gives no finding; a value
    of the wrong type gives a finding instead of raising.

    change-9377f9b9: the location path is path relative to workspace_dir
    when workspace_dir is given, else path. A first YAML block that does
    not parse gives 'YAML block does not parse: <problem>', ERROR, or WARN
    ending ' (closed record)' when a component of the location path is
    'closed' (audit-e4428fd5 F-01, F-02). resolve_class receives the
    location path (report-e4428fd5 §8.6 item 2).
    """
    findings = []
    # change-9377f9b9 (report-e4428fd5 §8.6 item 2): workspace-relative path
    loc_path = (os.path.relpath(path, workspace_dir)
                if workspace_dir is not None else path)
    data, problem = _parse_yaml_block(content)
    # change-9377f9b9 (audit-e4428fd5 F-01, F-02): report a parse problem
    if problem is not None:
        in_closed = "closed" in re.split(r"[\\/]", loc_path)
        findings.append(Finding(
            "WARN" if in_closed else "ERROR", path, "yaml",
            f"YAML block does not parse: {problem}"
            + (" (closed record)" if in_closed else "")))
        return findings, None, None
    if data is None:
        return findings, None, None

    # change-e4428fd5 (audit-caab2052 L-11): non-mapping top level
    if not isinstance(data, dict):
        findings.append(Finding("ERROR", path, "yaml",
            "YAML block top level must be a mapping"))
        return findings, None, None

    # change-e4428fd5 amendment 1: path limits root-key inference;
    # change-9377f9b9 (report-e4428fd5 §8.6 item 2): location path
    doc_class, message = resolve_class(data, loc_path)
    if doc_class is None:
        findings.append(Finding("WARN", path, "yaml", message))
        return findings, data, None

    # change-e4428fd5: only when schema_type is present (an inferred class,
    # e.g. a T03 prompt, carries no governance metadata)
    if (_get(data, "metadata.schema_type") is not None
            and not _get(data, "metadata.template_version")):
        findings.append(Finding("WARN", path, "yaml",
            "missing metadata.template_version"))

    # ID: presence, type (change-e4428fd5, audit-caab2052 L-11) and pattern
    if doc_class in _ID_FIELDS:
        id_path, pattern = _ID_FIELDS[doc_class]
        id_val = _get(data, id_path)
        if id_val is None or id_val == "":
            findings.append(Finding("ERROR", path, "yaml",
                f"required field '{id_path}' is missing or empty"))
        elif not isinstance(id_val, str):
            findings.append(Finding("ERROR", path, "yaml",
                f"'{id_path}' must be a string"))
        elif not re.match(pattern, id_val):
            findings.append(Finding("ERROR", path, "yaml",
                f"'{id_path}' value '{id_val}' does not match pattern '{pattern}'"))

    # Enum values (only when field is present); type check before the
    # membership test (change-e4428fd5, audit-caab2052 L-11)
    for field_path, valid in _ENUMS.get(doc_class, {}).items():
        val = _get(data, field_path)
        if val is None:
            continue
        if not isinstance(val, str):
            findings.append(Finding("ERROR", path, "yaml",
                f"'{field_path}' value must be a string"))
        elif val not in valid:
            findings.append(Finding("ERROR", path, "yaml",
                f"'{field_path}' value '{val}' not in {sorted(valid)}"))

    # Iteration must be integer ≥ 1
    if doc_class in _ITER_FIELDS:
        iter_val = _get(data, _ITER_FIELDS[doc_class])
        if iter_val is not None:
            # change-9377f9b9 (audit-e4428fd5 F-08): bool is not an iteration
            if (isinstance(iter_val, bool) or not isinstance(iter_val, int)
                    or iter_val < 1):
                findings.append(Finding("ERROR", path, "yaml",
                    f"iteration must be integer ≥ 1, got '{iter_val}'"))

    return findings, data, doc_class


# ── Check 4: coupling integrity ───────────────────────────────────────────────

def check_coupling(
    path: str,
    data: dict,
    doc_class: str,
    doc_index: dict[str, dict],
) -> list[Finding]:
    """
    Verify outgoing document reference resolves in doc_index
    and that iteration numbers are synchronised.

    change-e4428fd5: keyed by class word; a reference that is not a string
    is an ERROR (audit-caab2052 L-11).
    """
    findings = []
    if doc_class not in _COUPLING:
        return findings

    ref_path, iter_self_path, iter_ref_path = _COUPLING[doc_class]
    ref_val = _get(data, ref_path)

    if ref_val is None or ref_val == "":
        findings.append(Finding("WARN", path, "coupling",
            f"'{ref_path}' is empty — coupling incomplete"))
        return findings

    if not isinstance(ref_val, str):
        findings.append(Finding("ERROR", path, "coupling",
            f"'{ref_path}' must be a string"))
        return findings

    if ref_val not in doc_index:
        findings.append(Finding("ERROR", path, "coupling",
            f"referenced document '{ref_val}' not found in workspace"))
        return findings

    # Iteration synchronisation
    iter_self = _get(data, iter_self_path)
    iter_ref  = _get(data, iter_ref_path)
    if (iter_self is not None and iter_ref is not None
            and isinstance(iter_self, int) and isinstance(iter_ref, int)
            and iter_self != iter_ref):
        findings.append(Finding("ERROR", path, "coupling",
            f"iteration mismatch: own={iter_self}, coupled_docs={iter_ref}"))

    return findings


# ── Check 5: internal link targets (P12.9) ───────────────────────────────

def check_links(path: str, content: str, workspace_dir: str) -> list[Finding]:
    """
    Verify internal anchor links resolve within the document
    and file links resolve on the filesystem.
    """
    findings = []
    doc_headings = _headings(content)
    doc_dir = os.path.dirname(path)

    for m in LINK_RE.finditer(content):
        target = (m.group(1) or m.group(2) or "").strip()
        if not target:
            continue

        if target.startswith("#"):
            anchor = target[1:].lower()
            if anchor and anchor not in doc_headings:
                findings.append(Finding("WARN", path, "links",
                    f"anchor '{target}' not found in document headings"))

        elif target.endswith(".md"):
            resolved = (
                os.path.join(doc_dir, target)
                if not os.path.isabs(target)
                else target
            )
            if not os.path.exists(resolved):
                alt = os.path.join(workspace_dir, target)
                if not os.path.exists(alt):
                    findings.append(Finding("WARN", path, "links",
                        f"linked file '{target}' not found"))

    return findings


# ── Runner ────────────────────────────────────────────────────────────────────

def run(workspace_dir: str) -> list[Finding]:
    """
    Walk workspace_dir, run all checks, return findings.
    Two-pass: first pass builds doc_index; second pass checks coupling.
    """
    findings:  list[Finding] = []
    doc_index: dict[str, dict] = {}
    deferred:  list[tuple[str, dict, str]] = []  # (path, data, doc_class)

    for root, _dirs, files in os.walk(workspace_dir):
        for fname in sorted(files):
            if not fname.endswith(".md"):
                continue
            path = os.path.join(root, fname)
            content = open(path, encoding="utf-8", errors="replace").read()

            findings.extend(check_naming(fname, path))

            if not _is_governance_doc(fname):
                continue

            findings.extend(check_structure(path, content, fname))

            # change-51f1aef0: index by filename so prose-format documents
            # (no YAML id) resolve as coupling targets.
            _nm = NORMAL_RE.match(fname)
            if _nm:
                doc_index.setdefault(f"{_nm.group(1)}-{_nm.group(2)}", {})
            findings.extend(check_links(path, content, workspace_dir))

            # change-e4428fd5: doc_class is the class resolved by check_yaml;
            # change-9377f9b9: workspace_dir gives the location path
            yaml_findings, data, doc_class = check_yaml(path, content,
                                                        workspace_dir)
            findings.extend(yaml_findings)

            if data and doc_class and doc_class in _ID_FIELDS:
                id_val = _get(data, _ID_FIELDS[doc_class][0])
                if id_val:
                    doc_index[str(id_val)] = data
                deferred.append((path, data, doc_class))

    # Coupling pass — requires complete doc_index
    for path, data, doc_class in deferred:
        findings.extend(check_coupling(path, data, doc_class, doc_index))

    return findings


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    p = argparse.ArgumentParser(description="Layer 1 Governance Linter")
    p.add_argument("workspace", help="Path to workspace/ directory")
    args = p.parse_args()

    if not os.path.isdir(args.workspace):
        print(f"ERROR: not a directory: {args.workspace}", file=sys.stderr)
        sys.exit(1)

    findings = run(args.workspace)
    errors   = sum(1 for f in findings if f.severity == "ERROR")
    warnings = sum(1 for f in findings if f.severity == "WARN")

    for f in sorted(findings, key=lambda x: (x.path, x.check)):
        print(f)

    print(f"\n{'─' * 60}")
    print(f"  {errors} error(s)  {warnings} warning(s)  {len(findings)} total")

    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
