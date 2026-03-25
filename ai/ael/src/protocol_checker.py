"""
Layer 2 Protocol Checker — Multi-document workflow invariant validation.

Checks (require a complete workspace; multi-document):
  1. UUID chain integrity      (P09 §1.10.2)
  2. Bidirectional coupling    (P03 §1.4.2, P04 §1.5.7)
  3. One-to-one constraint     (P03 §1.4.2)
  4. Status consistency        (P04 §1.5.7)
  5. Lifecycle placement       (P00 §1.1.14)
  6. Prompt self-containment   (P09 §1.10.2)

Usage:
    python protocol_checker.py <workspace_dir>
    python -m pytest tests/test_protocol.py -v

Exit codes:
    0  — no errors (warnings may be present)
    1  — one or more ERROR findings
"""

import argparse
import os
import re
import sys

# Shared utilities from Layer 1 linter
sys.path.insert(0, os.path.dirname(__file__))
from linter import Finding, _extract_yaml, _get, MASTER_RE, NORMAL_RE

# ── Constants ─────────────────────────────────────────────────────────────────

# Terminal status values that satisfy closure criteria (P00 §1.1.14.3)
_TERMINAL_STATUS: dict[str, frozenset] = {
    "t02_change": frozenset({"verified"}),
    "t03_issue":  frozenset({"closed"}),
    "t04_prompt": frozenset({}),          # prompts have no terminal status field
    "t05_test":   frozenset({"passed"}),
    "t06_result": frozenset({"passed"}),
}

# Status field path per schema_type
_STATUS_FIELD: dict[str, str] = {
    "t02_change": "change_info.status",
    "t03_issue":  "issue_info.status",
    "t05_test":   "test_info.status",
    "t06_result": "result_info.status",
}

# ID field path per schema_type (mirrored from linter for clarity)
_ID_FIELD: dict[str, str] = {
    "t02_change": "change_info.id",
    "t03_issue":  "issue_info.id",
    "t04_prompt": "prompt_info.id",
    "t05_test":   "test_info.id",
    "t06_result": "result_info.id",
}

# Outgoing coupling reference per schema_type: (ref_field, back_ref_field_on_target)
# ref_field:             path in source doc pointing to target doc id
# back_ref_field:        path in target doc that should point back to source
_COUPLING_PAIRS: dict[str, tuple[str, str]] = {
    "t02_change": (
        "change_info.coupled_docs.issue_ref",     # change → issue
        "issue_info.coupled_docs.change_ref",     # issue → change (back)
    ),
    "t04_prompt": (
        "prompt_info.coupled_docs.change_ref",    # prompt → change
        "change_info.coupled_docs.prompt_ref",    # change → prompt (back) [optional field]
    ),
    "t05_test": (
        "test_info.coupled_docs.prompt_ref",      # test → prompt
        "prompt_info.coupled_docs.test_ref",      # prompt → test (back) [optional field]
    ),
    "t06_result": (
        "result_info.coupled_docs.test_ref",      # result → test
        "test_info.coupled_docs.result_ref",      # test → result (back)
    ),
}

# UUID extraction from document ID value
_UUID_RE = re.compile(r"-([0-9a-f]{8})$")


def _uuid_from_id(doc_id: str) -> str | None:
    """Extract the 8-char UUID suffix from a document ID string."""
    m = _UUID_RE.search(doc_id)
    return m.group(1) if m else None


def _doc_type_from_id(doc_id: str) -> str | None:
    """Extract the type prefix (e.g. 'issue', 'change') from a document ID."""
    parts = doc_id.split("-")
    return parts[0] if parts else None


# ── Document loading ──────────────────────────────────────────────────────────

class WorkspaceDoc:
    """Parsed governance document with path, data, schema_type, and ID."""
    __slots__ = ("path", "data", "schema_type", "doc_id", "in_closed")

    def __init__(self, path: str, data: dict, schema_type: str,
                 doc_id: str, in_closed: bool):
        self.path       = path
        self.data       = data
        self.schema_type = schema_type
        self.doc_id     = doc_id
        self.in_closed  = in_closed


def load_workspace(workspace_dir: str) -> tuple[list[WorkspaceDoc], list[Finding]]:
    """
    Walk workspace_dir, parse all governance markdown documents.
    Returns (docs, parse_warnings).
    """
    docs: list[WorkspaceDoc] = []
    warnings: list[Finding]  = []

    for root, _dirs, files in os.walk(workspace_dir):
        in_closed = "closed" in root.replace(workspace_dir, "").split(os.sep)
        for fname in sorted(files):
            if not fname.endswith(".md"):
                continue
            if not (MASTER_RE.match(fname) or NORMAL_RE.match(fname)):
                continue
            path = os.path.join(root, fname)
            content = open(path, encoding="utf-8", errors="replace").read()
            data = _extract_yaml(content)
            if data is None:
                continue
            schema_type = _get(data, "metadata.schema_type")
            if not schema_type or schema_type not in _ID_FIELD:
                continue
            doc_id = _get(data, _ID_FIELD[schema_type])
            if not doc_id:
                continue
            docs.append(WorkspaceDoc(path, data, schema_type,
                                     str(doc_id), in_closed))

    return docs, warnings


# ── Check 1: UUID chain integrity (P09 §1.10.2) ───────────────────────────────

def check_uuid_chain(docs: list[WorkspaceDoc]) -> list[Finding]:
    """
    For each document with an outgoing coupling reference, verify the
    referenced document's UUID suffix matches the source document's UUID suffix.

    All documents in a workflow chain must share the same 8-char UUID.
    """
    findings: list[Finding] = []
    by_id = {d.doc_id: d for d in docs}

    for doc in docs:
        if doc.schema_type not in _COUPLING_PAIRS:
            continue
        ref_field, _ = _COUPLING_PAIRS[doc.schema_type]
        ref_val = _get(doc.data, ref_field)
        if not ref_val:
            continue

        src_uuid = _uuid_from_id(doc.doc_id)
        tgt_uuid = _uuid_from_id(ref_val)

        if src_uuid and tgt_uuid and src_uuid != tgt_uuid:
            findings.append(Finding("ERROR", doc.path, "uuid_chain",
                f"UUID mismatch: '{doc.doc_id}' → '{ref_val}' "
                f"(expected shared UUID '{src_uuid}')"))

    return findings


# ── Check 2: Bidirectional coupling (P03 §1.4.2, P04 §1.5.7) ─────────────────

def check_bidirectional(docs: list[WorkspaceDoc]) -> list[Finding]:
    """
    For every A→B coupling reference, verify B→A back-reference exists
    and is non-empty where the template defines the field.

    Back-reference fields that are optional (prompt→test, prompt→change)
    produce warnings rather than errors when absent.
    """
    findings: list[Finding] = []
    by_id = {d.doc_id: d for d in docs}

    # Back-reference is mandatory only for the change↔issue pair (P03 §1.4.2)
    MANDATORY_BACK = {"t02_change"}

    for doc in docs:
        if doc.schema_type not in _COUPLING_PAIRS:
            continue
        ref_field, back_field = _COUPLING_PAIRS[doc.schema_type]
        ref_val = _get(doc.data, ref_field)
        if not ref_val:
            continue

        target = by_id.get(ref_val)
        if target is None:
            # Already reported by linter coupling check; skip here
            continue

        back_val = _get(target.data, back_field)
        if not back_val:
            sev = "ERROR" if doc.schema_type in MANDATORY_BACK else "WARN"
            findings.append(Finding(sev, target.path, "bidirectional",
                f"missing back-reference '{back_field}' → '{doc.doc_id}'"))
        elif back_val != doc.doc_id:
            findings.append(Finding("ERROR", target.path, "bidirectional",
                f"back-reference '{back_field}' = '{back_val}' "
                f"does not match source '{doc.doc_id}'"))

    return findings


# ── Check 3: One-to-one constraint (P03 §1.4.2) ───────────────────────────────

def check_one_to_one(docs: list[WorkspaceDoc]) -> list[Finding]:
    """
    No two change documents may reference the same issue UUID.
    No two prompt documents may reference the same change UUID.
    """
    findings: list[Finding] = []

    ref_owners: dict[str, list[str]] = {}

    for doc in docs:
        if doc.schema_type not in _COUPLING_PAIRS:
            continue
        ref_field, _ = _COUPLING_PAIRS[doc.schema_type]
        ref_val = _get(doc.data, ref_field)
        if not ref_val:
            continue
        # Key = (schema_type, ref_val) — track per coupling type
        key = f"{doc.schema_type}:{ref_val}"
        ref_owners.setdefault(key, []).append(doc.path)

    for key, owners in ref_owners.items():
        if len(owners) > 1:
            schema_type, ref_val = key.split(":", 1)
            findings.append(Finding("ERROR", owners[0], "one_to_one",
                f"'{ref_val}' referenced by {len(owners)} {schema_type} documents "
                f"(one-to-one violated): {owners}"))

    return findings


# ── Check 4: Status consistency (P04 §1.5.7) ──────────────────────────────────

def check_status_consistency(docs: list[WorkspaceDoc]) -> list[Finding]:
    """
    Issue/change status must be consistent:
      - issue 'resolved' requires coupled change 'implemented' or 'verified'
      - issue 'closed'   requires coupled change 'verified'
      - change 'implemented' or 'verified' requires issue 'resolved' or 'closed'
    """
    findings: list[Finding] = []
    by_id = {d.doc_id: d for d in docs}

    for doc in docs:
        if doc.schema_type != "t02_change":
            continue

        change_status = _get(doc.data, "change_info.status")
        issue_ref     = _get(doc.data, "change_info.coupled_docs.issue_ref")
        if not issue_ref:
            continue

        issue_doc = by_id.get(issue_ref)
        if issue_doc is None:
            continue

        issue_status = _get(issue_doc.data, "issue_info.status")

        # Rule: resolved issue → change must be implemented/verified
        if issue_status == "resolved" and change_status not in (
                "implemented", "verified", None):
            findings.append(Finding("ERROR", issue_doc.path, "status_consistency",
                f"issue is 'resolved' but coupled change '{doc.doc_id}' "
                f"has status '{change_status}' (expected 'implemented' or 'verified')"))

        # Rule: closed issue → change must be verified
        if issue_status == "closed" and change_status != "verified":
            findings.append(Finding("ERROR", issue_doc.path, "status_consistency",
                f"issue is 'closed' but coupled change '{doc.doc_id}' "
                f"has status '{change_status}' (expected 'verified')"))

        # Rule: change implemented/verified → issue must be resolved/closed
        if change_status in ("implemented", "verified") and issue_status not in (
                "resolved", "closed", None):
            findings.append(Finding("ERROR", doc.path, "status_consistency",
                f"change is '{change_status}' but coupled issue '{issue_ref}' "
                f"has status '{issue_status}' (expected 'resolved' or 'closed')"))

    return findings


# ── Check 5: Lifecycle placement (P00 §1.1.14) ────────────────────────────────

def check_lifecycle_placement(docs: list[WorkspaceDoc]) -> list[Finding]:
    """
    Documents in closed/ subdirectories must carry terminal status values.
    Documents outside closed/ must not carry terminal status values.
    """
    findings: list[Finding] = []

    for doc in docs:
        status_field = _STATUS_FIELD.get(doc.schema_type)
        if not status_field:
            continue
        terminal = _TERMINAL_STATUS.get(doc.schema_type, frozenset())
        status   = _get(doc.data, status_field)

        if doc.in_closed and status not in terminal:
            findings.append(Finding("ERROR", doc.path, "lifecycle",
                f"document in closed/ has non-terminal status '{status}' "
                f"(expected one of {sorted(terminal)})"))

        if not doc.in_closed and status in terminal:
            findings.append(Finding("WARN", doc.path, "lifecycle",
                f"document outside closed/ has terminal status '{status}' "
                f"— should be moved to closed/"))

    return findings


# ── Check 6: Prompt self-containment (P09 §1.10.2) ───────────────────────────

def check_prompt_self_contained(docs: list[WorkspaceDoc]) -> list[Finding]:
    """
    T04 prompt documents must be self-contained:
      - specification.description must be non-empty
      - design.components must contain at least one entry
      - deliverable.files must contain at least one entry
    """
    findings: list[Finding] = []

    for doc in docs:
        if doc.schema_type != "t04_prompt":
            continue

        spec_desc = _get(doc.data, "specification.description")
        if not spec_desc or not str(spec_desc).strip():
            findings.append(Finding("ERROR", doc.path, "prompt_self_contained",
                "specification.description is empty — prompt is not self-contained"))

        components = _get(doc.data, "design.components")
        if not components or not isinstance(components, list) or len(components) == 0:
            findings.append(Finding("ERROR", doc.path, "prompt_self_contained",
                "design.components is empty — prompt is not self-contained"))

        files = _get(doc.data, "deliverable.files")
        if not files or not isinstance(files, list) or len(files) == 0:
            findings.append(Finding("ERROR", doc.path, "prompt_self_contained",
                "deliverable.files is empty — no output target specified"))

    return findings


# ── Runner ────────────────────────────────────────────────────────────────────

def run(workspace_dir: str) -> list[Finding]:
    """Load workspace and run all protocol checks. Returns all findings."""
    docs, load_warnings = load_workspace(workspace_dir)
    findings = list(load_warnings)

    findings.extend(check_uuid_chain(docs))
    findings.extend(check_bidirectional(docs))
    findings.extend(check_one_to_one(docs))
    findings.extend(check_status_consistency(docs))
    findings.extend(check_lifecycle_placement(docs))
    findings.extend(check_prompt_self_contained(docs))

    return findings


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    p = argparse.ArgumentParser(description="Layer 2 Protocol Checker")
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
