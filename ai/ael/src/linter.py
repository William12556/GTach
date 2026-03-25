"""
Layer 1 Governance Linter — Static validation of workspace documents.

Checks:
  1. File naming conventions  (P00 §1.1.10)
  2. Markdown structure       (Version History, Created timestamp, copyright)
  3. YAML field validity      (schema_type, id pattern, enum values, iteration)
  4. UUID coupling integrity  (P03 §1.4.2, P04 §1.5.7, P06 §1.7.12, P09 §1.10.2)
  5. Obsidian link targets    (P02 §1.3.9)

Usage:
    python linter.py <workspace_dir>
    python -m pytest tests/test_linter.py -v

Exit codes:
    0  — no errors (warnings may be present)
    1  — one or more ERROR findings
"""

import argparse
import os
import re
import sys
from dataclasses import dataclass
from typing import Optional

import yaml

# ── Constants ─────────────────────────────────────────────────────────────────

VALID_CLASSES = frozenset({
    "design", "change", "issue", "prompt",
    "test", "result", "audit", "trace", "requirements",
})

MASTER_RE    = re.compile(r"^([a-z]+)-(.+)-master\.md$")
NORMAL_RE    = re.compile(r"^([a-z]+)-([0-9a-f]{8})-(.+)\.md$")
YAML_BLOCK_RE = re.compile(r"```yaml\n(.*?)```", re.DOTALL)
HEADING_RE   = re.compile(r"^#{1,6}\s+(.+)$", re.MULTILINE)
LINK_RE      = re.compile(r"\[[^\]]*\]\(<([^>]*)>|\[[^\]]*\]\(([^)]+)\)")

# Enum constraints per schema_type (P00 §1.1.10, template schemas)
_ENUMS: dict[str, dict[str, frozenset]] = {
    "t02_change": {
        "change_info.status":   frozenset({"proposed", "approved", "implemented", "verified", "rejected"}),
        "change_info.priority": frozenset({"critical", "high", "medium", "low"}),
    },
    "t03_issue": {
        "issue_info.status":   frozenset({"open", "investigating", "resolved", "verified", "closed", "deferred"}),
        "issue_info.severity": frozenset({"critical", "high", "medium", "low"}),
        "issue_info.type":     frozenset({"bug", "defect", "error", "performance", "security"}),
    },
    "t04_prompt": {
        "prompt_info.task_type": frozenset({"code_generation", "debug", "refactor", "optimization"}),
        "prompt_info.priority":  frozenset({"critical", "high", "medium", "low"}),
    },
    "t05_test": {
        "test_info.status":   frozenset({"planned", "in_progress", "executed", "passed", "failed", "blocked"}),
        "test_info.type":     frozenset({"unit", "integration", "system", "acceptance", "regression", "performance"}),
        "test_info.priority": frozenset({"critical", "high", "medium", "low"}),
    },
    "t06_result": {
        "result_info.status": frozenset({"passed", "failed", "blocked", "partial"}),
    },
}

# ID field path and regex pattern per schema_type
_ID_FIELDS: dict[str, tuple[str, str]] = {
    "t02_change": ("change_info.id",  r"^change-[0-9a-f]{8}$"),
    "t03_issue":  ("issue_info.id",   r"^issue-[0-9a-f]{8}$"),
    "t04_prompt": ("prompt_info.id",  r"^prompt-[0-9a-f]{8}$"),
    "t05_test":   ("test_info.id",    r"^test-[0-9a-f]{8}$"),
    "t06_result": ("result_info.id",  r"^result-[0-9a-f]{8}$"),
}

# Iteration field path per schema_type
_ITER_FIELDS: dict[str, str] = {
    "t02_change": "change_info.iteration",
    "t03_issue":  "issue_info.iteration",
    "t04_prompt": "prompt_info.iteration",
    "t05_test":   "test_info.iteration",
    "t06_result": "result_info.iteration",
}

# Outgoing coupling reference per schema_type:
#   (ref_field_path, own_iteration_path, coupled_iteration_path)
_COUPLING: dict[str, tuple[str, str, str]] = {
    "t02_change": (
        "change_info.coupled_docs.issue_ref",
        "change_info.iteration",
        "change_info.coupled_docs.issue_iteration",
    ),
    "t04_prompt": (
        "prompt_info.coupled_docs.change_ref",
        "prompt_info.iteration",
        "prompt_info.coupled_docs.change_iteration",
    ),
    "t05_test": (
        "test_info.coupled_docs.prompt_ref",
        "test_info.iteration",
        "test_info.coupled_docs.prompt_iteration",
    ),
    "t06_result": (
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


def _extract_yaml(content: str) -> Optional[dict]:
    """Parse first YAML fenced block in markdown content."""
    m = YAML_BLOCK_RE.search(content)
    if not m:
        return None
    try:
        return yaml.safe_load(m.group(1))
    except yaml.YAMLError:
        return None


def _headings(content: str) -> frozenset:
    """Return lowercase heading texts found in markdown content."""
    return frozenset(m.group(1).strip().lower() for m in HEADING_RE.finditer(content))


def _is_governance_doc(fname: str) -> bool:
    return bool(MASTER_RE.match(fname) or NORMAL_RE.match(fname))


# ── Check 1: file naming (P00 §1.1.10) ───────────────────────────────────────

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

def check_structure(path: str, content: str) -> list[Finding]:
    """Verify mandatory markdown sections are present."""
    findings = []
    lower = content.lower()

    if "version history" not in lower:
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

def check_yaml(path: str, content: str) -> tuple[list[Finding], Optional[dict], Optional[str]]:
    """
    Extract and validate first YAML block.
    Returns (findings, parsed_data, schema_type).
    """
    findings = []
    data = _extract_yaml(content)
    if data is None:
        return findings, None, None

    schema_type = _get(data, "metadata.schema_type")
    if not schema_type:
        findings.append(Finding("WARN", path, "yaml",
            "YAML block present but metadata.schema_type is missing"))
        return findings, data, None

    if not _get(data, "metadata.template_version"):
        findings.append(Finding("WARN", path, "yaml",
            "missing metadata.template_version"))

    # ID: presence and pattern
    if schema_type in _ID_FIELDS:
        id_path, pattern = _ID_FIELDS[schema_type]
        id_val = _get(data, id_path)
        if not id_val:
            findings.append(Finding("ERROR", path, "yaml",
                f"required field '{id_path}' is missing or empty"))
        elif not re.match(pattern, str(id_val)):
            findings.append(Finding("ERROR", path, "yaml",
                f"'{id_path}' value '{id_val}' does not match pattern '{pattern}'"))

    # Enum values (only when field is present)
    for field_path, valid in _ENUMS.get(schema_type, {}).items():
        val = _get(data, field_path)
        if val is not None and val not in valid:
            findings.append(Finding("ERROR", path, "yaml",
                f"'{field_path}' value '{val}' not in {sorted(valid)}"))

    # Iteration must be integer ≥ 1
    if schema_type in _ITER_FIELDS:
        iter_val = _get(data, _ITER_FIELDS[schema_type])
        if iter_val is not None:
            if not isinstance(iter_val, int) or iter_val < 1:
                findings.append(Finding("ERROR", path, "yaml",
                    f"iteration must be integer ≥ 1, got '{iter_val}'"))

    return findings, data, schema_type


# ── Check 4: coupling integrity ───────────────────────────────────────────────

def check_coupling(
    path: str,
    data: dict,
    schema_type: str,
    doc_index: dict[str, dict],
) -> list[Finding]:
    """
    Verify outgoing document reference resolves in doc_index
    and that iteration numbers are synchronised.
    """
    findings = []
    if schema_type not in _COUPLING:
        return findings

    ref_path, iter_self_path, iter_ref_path = _COUPLING[schema_type]
    ref_val = _get(data, ref_path)

    if not ref_val:
        findings.append(Finding("WARN", path, "coupling",
            f"'{ref_path}' is empty — coupling incomplete"))
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


# ── Check 5: Obsidian link targets (P02 §1.3.9) ───────────────────────────────

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
    deferred:  list[tuple[str, dict, str]] = []

    for root, _dirs, files in os.walk(workspace_dir):
        for fname in sorted(files):
            if not fname.endswith(".md"):
                continue
            path = os.path.join(root, fname)
            content = open(path, encoding="utf-8", errors="replace").read()

            findings.extend(check_naming(fname, path))

            if not _is_governance_doc(fname):
                continue

            findings.extend(check_structure(path, content))
            findings.extend(check_links(path, content, workspace_dir))

            yaml_findings, data, schema_type = check_yaml(path, content)
            findings.extend(yaml_findings)

            if data and schema_type and schema_type in _ID_FIELDS:
                id_val = _get(data, _ID_FIELDS[schema_type][0])
                if id_val:
                    doc_index[str(id_val)] = data
                deferred.append((path, data, schema_type))

    # Coupling pass — requires complete doc_index
    for path, data, schema_type in deferred:
        findings.extend(check_coupling(path, data, schema_type, doc_index))

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
