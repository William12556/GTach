"""
Unit tests for protocol_checker.py — Layer 2 Protocol Checker.
No external services required; all fixtures use in-memory data structures.
"""

import os
import sys
import tempfile

import pytest
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from protocol_checker import (
    WorkspaceDoc,
    check_bidirectional,
    check_lifecycle_placement,
    check_one_to_one,
    check_prompt_self_contained,
    check_status_consistency,
    check_uuid_chain,
    load_workspace,
    run,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _doc(path: str, schema_type: str, doc_id: str,
         data: dict, in_closed: bool = False) -> WorkspaceDoc:
    """Construct a WorkspaceDoc directly (no filesystem needed)."""
    return WorkspaceDoc(path, data, schema_type, doc_id, in_closed)


def _issue(uuid: str, status: str = "open",
           change_ref: str = "") -> dict:
    return {
        "issue_info": {
            "id": f"issue-{uuid}",
            "title": "test",
            "date": "2025-01-01",
            "status": status,
            "severity": "low",
            "type": "bug",
            "iteration": 1,
            "coupled_docs": {
                "change_ref": change_ref,
                "change_iteration": 1 if change_ref else None,
            },
        },
        "source":        {"origin": "test_result", "description": "test"},
        "affected_scope": {"components": [{"name": "x", "file_path": "src/x.py"}]},
        "behavior":      {"expected": "works", "actual": "fails"},
        "metadata":      {"template_version": "1.0", "schema_type": "t03_issue"},
    }


def _change(uuid: str, status: str = "proposed",
            issue_ref: str = "") -> dict:
    return {
        "change_info": {
            "id": f"change-{uuid}",
            "title": "test",
            "date": "2025-01-01",
            "status": status,
            "priority": "low",
            "iteration": 1,
            "coupled_docs": {
                "issue_ref": issue_ref or f"issue-{uuid}",
                "issue_iteration": 1,
            },
        },
        "source":          {"type": "issue", "description": "test"},
        "scope":           {"summary": "test", "affected_components": []},
        "rational":        {"problem_statement": "x", "proposed_solution": "y"},
        "technical_details": {
            "current_behavior": "a",
            "proposed_behavior": "b",
            "implementation_approach": "c",
        },
        "metadata": {"template_version": "1.0", "schema_type": "t02_change"},
    }


def _prompt(uuid: str, change_ref: str = "",
            spec_desc: str = "Implement the login module.",
            components: list | None = None,
            files: list | None = None) -> dict:
    return {
        "prompt_info": {
            "id": f"prompt-{uuid}",
            "task_type": "code_generation",
            "source_ref": f"change-{uuid}",
            "date": "2025-01-01",
            "priority": "low",
            "iteration": 1,
            "coupled_docs": {
                "change_ref": change_ref or f"change-{uuid}",
                "change_iteration": 1,
            },
        },
        "specification": {
            "description": spec_desc,
            "requirements": {"functional": ["do the thing"]},
        },
        "design": {
            "components": components if components is not None
                          else [{"name": "MyModule", "type": "module",
                                 "purpose": "core logic"}],
        },
        "deliverable": {
            "files": files if files is not None
                     else [{"path": "src/mymodule.py", "content": ""}],
        },
        "metadata": {"template_version": "1.0", "schema_type": "t04_prompt"},
    }


# ── Check 1: UUID chain ───────────────────────────────────────────────────────

UUID = "a1b2c3d4"
OTHER = "b2c3d4e5"


def test_uuid_chain_valid():
    issue  = _doc(f"/ws/issue-{UUID}-x.md",  "t03_issue",  f"issue-{UUID}",
                  _issue(UUID), in_closed=False)
    change = _doc(f"/ws/change-{UUID}-x.md", "t02_change", f"change-{UUID}",
                  _change(UUID, issue_ref=f"issue-{UUID}"), in_closed=False)
    findings = check_uuid_chain([issue, change])
    errors = [f for f in findings if f.severity == "ERROR"]
    assert errors == []


def test_uuid_chain_mismatch():
    # change-{UUID} references issue-{OTHER}: UUID mismatch
    change = _doc(f"/ws/change-{UUID}-x.md", "t02_change", f"change-{UUID}",
                  _change(UUID, issue_ref=f"issue-{OTHER}"))
    findings = check_uuid_chain([change])
    errors = [f for f in findings if f.severity == "ERROR" and f.check == "uuid_chain"]
    assert len(errors) == 1
    assert UUID in errors[0].message
    assert OTHER in errors[0].message


def test_uuid_chain_no_ref_ignored():
    # change with empty issue_ref — uuid_chain does not flag (linter handles missing refs)
    data = _change(UUID)
    data["change_info"]["coupled_docs"]["issue_ref"] = ""
    change = _doc(f"/ws/change-{UUID}-x.md", "t02_change", f"change-{UUID}", data)
    findings = check_uuid_chain([change])
    errors = [f for f in findings if f.check == "uuid_chain"]
    assert errors == []


def test_uuid_chain_prompt_references_matching_change():
    prompt = _doc(f"/ws/prompt-{UUID}-x.md", "t04_prompt", f"prompt-{UUID}",
                  _prompt(UUID, change_ref=f"change-{UUID}"))
    findings = check_uuid_chain([prompt])
    errors = [f for f in findings if f.check == "uuid_chain"]
    assert errors == []


def test_uuid_chain_prompt_references_wrong_change():
    prompt = _doc(f"/ws/prompt-{UUID}-x.md", "t04_prompt", f"prompt-{UUID}",
                  _prompt(UUID, change_ref=f"change-{OTHER}"))
    findings = check_uuid_chain([prompt])
    errors = [f for f in findings if f.check == "uuid_chain"]
    assert len(errors) == 1


# ── Check 2: Bidirectional coupling ──────────────────────────────────────────

def test_bidirectional_valid():
    issue_data  = _issue(UUID, change_ref=f"change-{UUID}")
    change_data = _change(UUID, issue_ref=f"issue-{UUID}")
    issue  = _doc(f"/ws/issue-{UUID}-x.md",  "t03_issue",  f"issue-{UUID}",  issue_data)
    change = _doc(f"/ws/change-{UUID}-x.md", "t02_change", f"change-{UUID}", change_data)
    findings = check_bidirectional([issue, change])
    errors = [f for f in findings if f.severity == "ERROR"]
    assert errors == []


def test_bidirectional_missing_back_ref_mandatory():
    # Issue has no change_ref — mandatory back-reference missing
    issue_data  = _issue(UUID, change_ref="")
    change_data = _change(UUID, issue_ref=f"issue-{UUID}")
    issue  = _doc(f"/ws/issue-{UUID}-x.md",  "t03_issue",  f"issue-{UUID}",  issue_data)
    change = _doc(f"/ws/change-{UUID}-x.md", "t02_change", f"change-{UUID}", change_data)
    findings = check_bidirectional([issue, change])
    errors = [f for f in findings if f.severity == "ERROR" and f.check == "bidirectional"]
    assert len(errors) == 1


def test_bidirectional_wrong_back_ref():
    # Issue back-ref points to a different change
    issue_data  = _issue(UUID, change_ref=f"change-{OTHER}")
    change_data = _change(UUID, issue_ref=f"issue-{UUID}")
    issue  = _doc(f"/ws/issue-{UUID}-x.md",  "t03_issue",  f"issue-{UUID}",  issue_data)
    change = _doc(f"/ws/change-{UUID}-x.md", "t02_change", f"change-{UUID}", change_data)
    findings = check_bidirectional([issue, change])
    errors = [f for f in findings if f.severity == "ERROR" and f.check == "bidirectional"]
    assert len(errors) == 1
    assert OTHER in errors[0].message


def test_bidirectional_target_not_in_index():
    # change references issue not in doc list — skipped (linter catches missing refs)
    change_data = _change(UUID, issue_ref=f"issue-{UUID}")
    change = _doc(f"/ws/change-{UUID}-x.md", "t02_change", f"change-{UUID}", change_data)
    findings = check_bidirectional([change])
    errors = [f for f in findings if f.check == "bidirectional"]
    assert errors == []


# ── Check 3: One-to-one ───────────────────────────────────────────────────────

def test_one_to_one_valid():
    change1 = _doc(f"/ws/change-{UUID}-x.md",  "t02_change", f"change-{UUID}",
                   _change(UUID,  issue_ref=f"issue-{UUID}"))
    change2 = _doc(f"/ws/change-{OTHER}-x.md", "t02_change", f"change-{OTHER}",
                   _change(OTHER, issue_ref=f"issue-{OTHER}"))
    findings = check_one_to_one([change1, change2])
    errors = [f for f in findings if f.severity == "ERROR"]
    assert errors == []


def test_one_to_one_violated_two_changes_same_issue():
    shared_issue = f"issue-{UUID}"
    change1 = _doc(f"/ws/change-{UUID}-x.md",  "t02_change", f"change-{UUID}",
                   _change(UUID,  issue_ref=shared_issue))
    change2 = _doc(f"/ws/change-{OTHER}-x.md", "t02_change", f"change-{OTHER}",
                   _change(OTHER, issue_ref=shared_issue))
    findings = check_one_to_one([change1, change2])
    errors = [f for f in findings if f.severity == "ERROR" and f.check == "one_to_one"]
    assert len(errors) == 1
    assert "2" in errors[0].message


def test_one_to_one_single_change_valid():
    change = _doc(f"/ws/change-{UUID}-x.md", "t02_change", f"change-{UUID}",
                  _change(UUID, issue_ref=f"issue-{UUID}"))
    findings = check_one_to_one([change])
    errors = [f for f in findings if f.severity == "ERROR"]
    assert errors == []


# ── Check 4: Status consistency ───────────────────────────────────────────────

def test_status_consistency_resolved_and_implemented_valid():
    issue  = _doc("/ws/issue.md",  "t03_issue",  f"issue-{UUID}",
                  _issue(UUID, status="resolved", change_ref=f"change-{UUID}"))
    change = _doc("/ws/change.md", "t02_change", f"change-{UUID}",
                  _change(UUID, status="implemented", issue_ref=f"issue-{UUID}"))
    findings = check_status_consistency([issue, change])
    errors = [f for f in findings if f.severity == "ERROR"]
    assert errors == []


def test_status_consistency_closed_and_verified_valid():
    issue  = _doc("/ws/issue.md",  "t03_issue",  f"issue-{UUID}",
                  _issue(UUID, status="closed", change_ref=f"change-{UUID}"))
    change = _doc("/ws/change.md", "t02_change", f"change-{UUID}",
                  _change(UUID, status="verified", issue_ref=f"issue-{UUID}"))
    findings = check_status_consistency([issue, change])
    errors = [f for f in findings if f.severity == "ERROR"]
    assert errors == []


def test_status_consistency_resolved_but_change_proposed():
    issue  = _doc("/ws/issue.md",  "t03_issue",  f"issue-{UUID}",
                  _issue(UUID, status="resolved", change_ref=f"change-{UUID}"))
    change = _doc("/ws/change.md", "t02_change", f"change-{UUID}",
                  _change(UUID, status="proposed", issue_ref=f"issue-{UUID}"))
    findings = check_status_consistency([issue, change])
    errors = [f for f in findings if f.severity == "ERROR" and f.check == "status_consistency"]
    assert len(errors) >= 1
    assert "proposed" in errors[0].message


def test_status_consistency_change_implemented_issue_open():
    issue  = _doc("/ws/issue.md",  "t03_issue",  f"issue-{UUID}",
                  _issue(UUID, status="open", change_ref=f"change-{UUID}"))
    change = _doc("/ws/change.md", "t02_change", f"change-{UUID}",
                  _change(UUID, status="implemented", issue_ref=f"issue-{UUID}"))
    findings = check_status_consistency([issue, change])
    errors = [f for f in findings if f.severity == "ERROR" and f.check == "status_consistency"]
    assert len(errors) >= 1
    assert "open" in errors[0].message


def test_status_consistency_open_and_proposed_valid():
    # Both open/proposed — no violation
    issue  = _doc("/ws/issue.md",  "t03_issue",  f"issue-{UUID}",
                  _issue(UUID, status="open"))
    change = _doc("/ws/change.md", "t02_change", f"change-{UUID}",
                  _change(UUID, status="proposed", issue_ref=f"issue-{UUID}"))
    findings = check_status_consistency([issue, change])
    errors = [f for f in findings if f.severity == "ERROR"]
    assert errors == []


# ── Check 5: Lifecycle placement ──────────────────────────────────────────────

def test_lifecycle_closed_with_terminal_status_valid():
    issue = _doc("/ws/issues/closed/issue-x.md", "t03_issue", f"issue-{UUID}",
                 _issue(UUID, status="closed"), in_closed=True)
    findings = check_lifecycle_placement([issue])
    errors = [f for f in findings if f.severity == "ERROR" and f.check == "lifecycle"]
    assert errors == []


def test_lifecycle_closed_with_non_terminal_status():
    issue = _doc("/ws/issues/closed/issue-x.md", "t03_issue", f"issue-{UUID}",
                 _issue(UUID, status="open"), in_closed=True)
    findings = check_lifecycle_placement([issue])
    errors = [f for f in findings if f.severity == "ERROR" and f.check == "lifecycle"]
    assert len(errors) == 1
    assert "open" in errors[0].message


def test_lifecycle_active_with_non_terminal_status_valid():
    issue = _doc("/ws/issues/issue-x.md", "t03_issue", f"issue-{UUID}",
                 _issue(UUID, status="investigating"), in_closed=False)
    findings = check_lifecycle_placement([issue])
    assert findings == []


def test_lifecycle_active_with_terminal_status_warns():
    issue = _doc("/ws/issues/issue-x.md", "t03_issue", f"issue-{UUID}",
                 _issue(UUID, status="closed"), in_closed=False)
    findings = check_lifecycle_placement([issue])
    warns = [f for f in findings if f.severity == "WARN" and f.check == "lifecycle"]
    assert len(warns) == 1


def test_lifecycle_change_closed_verified_valid():
    change = _doc("/ws/change/closed/change-x.md", "t02_change", f"change-{UUID}",
                  _change(UUID, status="verified"), in_closed=True)
    findings = check_lifecycle_placement([change])
    errors = [f for f in findings if f.severity == "ERROR"]
    assert errors == []


def test_lifecycle_change_closed_non_terminal():
    change = _doc("/ws/change/closed/change-x.md", "t02_change", f"change-{UUID}",
                  _change(UUID, status="approved"), in_closed=True)
    findings = check_lifecycle_placement([change])
    errors = [f for f in findings if f.severity == "ERROR" and f.check == "lifecycle"]
    assert len(errors) == 1


# ── Check 6: Prompt self-containment ──────────────────────────────────────────

def test_prompt_self_contained_valid():
    prompt = _doc("/ws/prompt-x.md", "t04_prompt", f"prompt-{UUID}",
                  _prompt(UUID))
    findings = check_prompt_self_contained([prompt])
    errors = [f for f in findings if f.severity == "ERROR"]
    assert errors == []


def test_prompt_empty_spec_description():
    prompt = _doc("/ws/prompt-x.md", "t04_prompt", f"prompt-{UUID}",
                  _prompt(UUID, spec_desc=""))
    findings = check_prompt_self_contained([prompt])
    errors = [f for f in findings if f.check == "prompt_self_contained"
              and "specification.description" in f.message]
    assert len(errors) == 1


def test_prompt_empty_components():
    prompt = _doc("/ws/prompt-x.md", "t04_prompt", f"prompt-{UUID}",
                  _prompt(UUID, components=[]))
    findings = check_prompt_self_contained([prompt])
    errors = [f for f in findings if f.check == "prompt_self_contained"
              and "components" in f.message]
    assert len(errors) == 1


def test_prompt_empty_files():
    prompt = _doc("/ws/prompt-x.md", "t04_prompt", f"prompt-{UUID}",
                  _prompt(UUID, files=[]))
    findings = check_prompt_self_contained([prompt])
    errors = [f for f in findings if f.check == "prompt_self_contained"
              and "files" in f.message]
    assert len(errors) == 1


def test_prompt_all_three_empty():
    prompt = _doc("/ws/prompt-x.md", "t04_prompt", f"prompt-{UUID}",
                  _prompt(UUID, spec_desc="", components=[], files=[]))
    findings = check_prompt_self_contained([prompt])
    errors = [f for f in findings if f.check == "prompt_self_contained"]
    assert len(errors) == 3


def test_prompt_non_prompt_doc_ignored():
    issue = _doc("/ws/issue-x.md", "t03_issue", f"issue-{UUID}", _issue(UUID))
    findings = check_prompt_self_contained([issue])
    assert findings == []


# ── Integration: run() on temp workspace ─────────────────────────────────────

def _write_yaml_doc(dirpath: str, fname: str, data: dict) -> None:
    """Write a minimal valid governance markdown doc with embedded YAML."""
    yaml_str = yaml.dump(data, default_flow_style=False)
    content = (
        f"Created: 2025-01-01\n\n# Title\n\n"
        f"```yaml\n{yaml_str}```\n\n"
        f"## Version History\n\n| Version | Date | Description |\n"
        f"| ------- | ---- | ----------- |\n"
        f"| 1.0 | 2025-01-01 | Initial |\n\n"
        f"Copyright (c) 2025 William Watson. MIT License.\n"
    )
    path = os.path.join(dirpath, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def test_run_empty_workspace():
    with tempfile.TemporaryDirectory() as tmpdir:
        findings = run(tmpdir)
        assert findings == []


def test_run_clean_coupled_pair():
    with tempfile.TemporaryDirectory() as tmpdir:
        issue_data  = _issue(UUID, status="open", change_ref=f"change-{UUID}")
        change_data = _change(UUID, status="proposed", issue_ref=f"issue-{UUID}")
        _write_yaml_doc(tmpdir, f"issue-{UUID}-x.md",  issue_data)
        _write_yaml_doc(tmpdir, f"change-{UUID}-x.md", change_data)
        findings = run(tmpdir)
        errors = [f for f in findings if f.severity == "ERROR"]
        assert errors == []


def test_run_detects_uuid_mismatch():
    with tempfile.TemporaryDirectory() as tmpdir:
        # change-{UUID} references issue-{OTHER}: UUID mismatch
        change_data = _change(UUID, issue_ref=f"issue-{OTHER}")
        _write_yaml_doc(tmpdir, f"change-{UUID}-x.md", change_data)
        findings = run(tmpdir)
        errors = [f for f in findings if f.check == "uuid_chain"]
        assert len(errors) == 1


def test_run_detects_one_to_one_violation():
    with tempfile.TemporaryDirectory() as tmpdir:
        change1_data = _change(UUID,  issue_ref=f"issue-{UUID}")
        change2_data = _change(OTHER, issue_ref=f"issue-{UUID}")  # same issue
        _write_yaml_doc(tmpdir, f"change-{UUID}-x.md",  change1_data)
        _write_yaml_doc(tmpdir, f"change-{OTHER}-x.md", change2_data)
        findings = run(tmpdir)
        errors = [f for f in findings if f.check == "one_to_one"]
        assert len(errors) == 1


def test_run_detects_lifecycle_violation():
    with tempfile.TemporaryDirectory() as tmpdir:
        closed_dir = os.path.join(tmpdir, "closed")
        os.makedirs(closed_dir)
        issue_data = _issue(UUID, status="open")  # non-terminal in closed/
        _write_yaml_doc(closed_dir, f"issue-{UUID}-x.md", issue_data)
        findings = run(tmpdir)
        errors = [f for f in findings if f.check == "lifecycle"]
        assert len(errors) == 1
