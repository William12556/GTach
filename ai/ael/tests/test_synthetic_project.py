"""
Layer 3 Synthetic Project Acceptance Test.

Assembles a complete, minimal governance workspace for the synthetic
project 'synth-adder' and validates it against both the Layer 1 linter
and Layer 2 protocol checker.

All documents share UUID chain 'c0ffee01'. The workspace represents a
complete governance workflow:
  P10 requirements → P02 design → P04 issue → P03 change →
  P09 prompt → P06 test → P06 result

No external services required; all operations use temporary directories.
"""

import copy
import os
import sys
import tempfile

import pytest
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import linter
import protocol_checker

# ── Shared UUID ───────────────────────────────────────────────────────────────

UUID = "c0ffee01"


# ── Document content builders ─────────────────────────────────────────────────

def _md(title: str, yaml_data: dict | None = None, extra_body: str = "") -> str:
    """
    Produce a minimal valid governance markdown document.
    Embeds YAML block when yaml_data is provided.
    """
    yaml_block = ""
    if yaml_data is not None:
        yaml_str = yaml.dump(yaml_data, default_flow_style=False, allow_unicode=True)
        yaml_block = f"```yaml\n{yaml_str}```\n\n"

    return (
        f"Created: 2025-01-01\n\n"
        f"# {title}\n\n"
        f"{yaml_block}"
        f"{extra_body}\n"
        f"## Version History\n\n"
        f"| Version | Date | Description |\n"
        f"| ------- | ---- | ----------- |\n"
        f"| 1.0 | 2025-01-01 | Initial |\n\n"
        f"Copyright (c) 2025 William Watson. MIT License.\n"
    )


def _requirements_data() -> dict:
    return {
        "project_info": {
            "name": "synth-adder",
            "version": "0.1.0",
            "date": "2025-01-01",
            "author": "test",
            "status": "approved",
        },
        "functional_requirements": [
            {
                "id": f"{UUID}",
                "type": "functional",
                "description": "add(a, b) returns a + b",
                "acceptance_criteria": ["add(1, 2) == 3"],
                "source": "stakeholder",
                "rationale": "core capability",
                "dependencies": [],
            }
        ],
        "non_functional_requirements": [],
        "version_history": [{"version": "1.0", "date": "2025-01-01",
                              "author": "test", "changes": ["Initial"]}],
        "metadata": {
            "copyright": "Copyright (c) 2025 William Watson.",
            "template_version": "1.0",
            "schema_type": "t07_requirements",
        },
    }


def _design_master_data() -> dict:
    return {
        "project_info": {"name": "synth-adder", "version": "0.1.0",
                         "date": "2025-01-01", "author": "test"},
        "scope":           {"purpose": "Adds two integers."},
        "system_overview": {"description": "Single function add(a,b)."},
        "architecture":    {"pattern": "functional",
                            "technology_stack": {"language": "Python"}},
        "components":      [{"name": "adder", "purpose": "add(a,b)"}],
        "version_history": [{"version": "1.0", "date": "2025-01-01",
                              "author": "test", "changes": ["Initial"]}],
        "metadata": {
            "copyright": "Copyright (c) 2025 William Watson.",
            "template_version": "1.0",
            "schema_type": "t01_design",
        },
    }


def _issue_data(change_ref: str = f"change-{UUID}") -> dict:
    return {
        "issue_info": {
            "id": f"issue-{UUID}",
            "title": "adder returns wrong value",
            "date": "2025-01-01",
            "reporter": "test",
            "status": "resolved",
            "severity": "low",
            "type": "bug",
            "iteration": 1,
            "coupled_docs": {
                "change_ref": change_ref,
                "change_iteration": 1,
            },
        },
        "source": {"origin": "test_result", "description": "add(1,2) returned 0"},
        "affected_scope": {
            "components": [{"name": "adder", "file_path": "src/adder.py"}]
        },
        "behavior": {"expected": "3", "actual": "0"},
        "metadata": {
            "copyright": "Copyright (c) 2025 William Watson.",
            "template_version": "1.0",
            "schema_type": "t03_issue",
        },
    }


def _change_data(issue_ref: str = f"issue-{UUID}") -> dict:
    return {
        "change_info": {
            "id": f"change-{UUID}",
            "title": "fix adder return value",
            "date": "2025-01-01",
            "author": "test",
            "status": "implemented",
            "priority": "low",
            "iteration": 1,
            "coupled_docs": {
                "issue_ref": issue_ref,
                "issue_iteration": 1,
            },
        },
        "source": {"type": "issue", "description": "fix off-by-one"},
        "scope": {
            "summary": "correct return statement",
            "affected_components": [
                {"name": "adder", "file_path": "src/adder.py", "change_type": "modify"}
            ],
        },
        "rational": {
            "problem_statement": "return 0 instead of a+b",
            "proposed_solution": "return a + b",
        },
        "technical_details": {
            "current_behavior": "returns 0",
            "proposed_behavior": "returns a + b",
            "implementation_approach": "fix return statement",
        },
        "metadata": {
            "copyright": "Copyright (c) 2025 William Watson.",
            "template_version": "1.0",
            "schema_type": "t02_change",
        },
    }


def _prompt_data(spec_desc: str = "Implement add(a, b) -> int.",
                 components: list | None = None,
                 files: list | None = None) -> dict:
    return {
        "prompt_info": {
            "id": f"prompt-{UUID}",
            "task_type": "code_generation",
            "source_ref": f"change-{UUID}",
            "date": "2025-01-01",
            "priority": "low",
            "iteration": 1,
            "coupled_docs": {
                "change_ref": f"change-{UUID}",
                "change_iteration": 1,
            },
        },
        "specification": {
            "description": spec_desc,
            "requirements": {"functional": ["add(1,2) == 3"]},
        },
        "design": {
            "components": components if components is not None else [
                {"name": "adder", "type": "function", "purpose": "add two ints"}
            ],
        },
        "deliverable": {
            "files": files if files is not None else [
                {"path": "src/adder.py", "content": ""}
            ],
        },
        "metadata": {
            "copyright": "Copyright (c) 2025 William Watson.",
            "template_version": "1.0",
            "schema_type": "t04_prompt",
        },
    }


def _test_data() -> dict:
    return {
        "test_info": {
            "id": f"test-{UUID}",
            "title": "adder unit tests",
            "date": "2025-01-01",
            "author": "test",
            "status": "passed",
            "type": "unit",
            "priority": "low",
            "iteration": 1,
            "coupled_docs": {
                "prompt_ref": f"prompt-{UUID}",
                "prompt_iteration": 1,
                "result_ref": f"result-{UUID}",
            },
        },
        "source": {"test_target": "adder"},
        "scope": {"description": "Unit tests for add()"},
        "test_cases": [
            {
                "case_id": "TC-001",
                "description": "add(1,2) returns 3",
                "category": "positive",
            }
        ],
        "metadata": {
            "copyright": "Copyright (c) 2025 William Watson.",
            "template_version": "1.0",
            "schema_type": "t05_test",
        },
    }


def _result_data() -> dict:
    return {
        "result_info": {
            "id": f"result-{UUID}",
            "title": "adder unit test results",
            "date": "2025-01-01",
            "executor": "test",
            "status": "passed",
            "iteration": 1,
            "coupled_docs": {
                "test_ref": f"test-{UUID}",
                "test_iteration": 1,
            },
        },
        "execution": {"timestamp": "2025-01-01T00:00:00Z"},
        "summary": {"total_cases": 1, "passed": 1, "failed": 0},
        "metadata": {
            "copyright": "Copyright (c) 2025 William Watson.",
            "template_version": "1.0",
            "schema_type": "t06_result",
        },
    }


# ── Workspace factory ─────────────────────────────────────────────────────────

def _write(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def build_workspace(root: str) -> None:
    """
    Write a complete, valid synthetic project workspace to root/.
    Mirrors the skel workspace/ structure.
    """
    w = root  # workspace root

    # Requirements
    _write(f"{w}/requirements/requirements-synth-master.md",
           _md("synth-adder Requirements", _requirements_data()))

    # Design master
    _write(f"{w}/design/design-synth-master.md",
           _md("synth-adder Master Design", _design_master_data()))

    # Traceability matrix master (no YAML required)
    _write(f"{w}/trace/trace-traceability-matrix-master.md",
           _md("Traceability Matrix"))

    # Issue (status resolved — not yet closed, appropriate for active workspace)
    _write(f"{w}/issues/issue-{UUID}-adder-wrong-value.md",
           _md("Issue: adder wrong value", _issue_data()))

    # Change
    _write(f"{w}/change/change-{UUID}-fix-adder.md",
           _md("Change: fix adder", _change_data()))

    # Prompt
    _write(f"{w}/prompt/prompt-{UUID}-implement-adder.md",
           _md("Prompt: implement adder", _prompt_data()))

    # Test (status passed, outside closed/ — triggers lifecycle WARN not ERROR)
    _write(f"{w}/test/test-{UUID}-adder-unit.md",
           _md("Test: adder unit", _test_data()))

    # Result
    _write(f"{w}/test/result/result-{UUID}-adder-unit.md",
           _md("Result: adder unit", _result_data()))

    # closed/ subdirectories (empty — required by skel structure)
    for d in ("issues/closed", "change/closed", "prompt/closed",
              "audit/closed", "test/closed", "test/result/closed",
              "requirements/closed"):
        os.makedirs(f"{w}/{d}", exist_ok=True)


# ── Tests: clean workspace ────────────────────────────────────────────────────

def test_clean_workspace_linter():
    """L1 linter produces zero errors against a complete valid workspace."""
    with tempfile.TemporaryDirectory() as tmpdir:
        build_workspace(tmpdir)
        findings = linter.run(tmpdir)
        errors = [f for f in findings if f.severity == "ERROR"]
        assert errors == [], \
            f"Expected no linter errors. Got:\n" + "\n".join(str(f) for f in errors)


def test_clean_workspace_protocol():
    """L2 protocol checker produces zero errors against a complete valid workspace."""
    with tempfile.TemporaryDirectory() as tmpdir:
        build_workspace(tmpdir)
        findings = protocol_checker.run(tmpdir)
        errors = [f for f in findings if f.severity == "ERROR"]
        assert errors == [], \
            f"Expected no protocol errors. Got:\n" + "\n".join(str(f) for f in errors)


# ── Tests: deliberately broken workspaces ─────────────────────────────────────

def test_broken_uuid_chain():
    """
    Change document references an issue with a different UUID.
    L2 must report a uuid_chain error.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        build_workspace(tmpdir)
        # Overwrite change doc with wrong issue UUID reference
        bad_change = _change_data(issue_ref="issue-deadbeef")
        _write(f"{tmpdir}/change/change-{UUID}-fix-adder.md",
               _md("Change: fix adder", bad_change))

        findings = protocol_checker.run(tmpdir)
        errors = [f for f in findings if f.check == "uuid_chain"]
        assert len(errors) >= 1, "Expected uuid_chain error"
        assert any("deadbeef" in f.message for f in errors)


def test_broken_bidirectional():
    """
    Issue back-reference to change is empty.
    L2 must report a bidirectional error (mandatory for change↔issue pair).
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        build_workspace(tmpdir)
        # Overwrite issue doc with empty change_ref
        bad_issue = _issue_data(change_ref="")
        _write(f"{tmpdir}/issues/issue-{UUID}-adder-wrong-value.md",
               _md("Issue: adder wrong value", bad_issue))

        findings = protocol_checker.run(tmpdir)
        errors = [f for f in findings if f.check == "bidirectional"]
        assert len(errors) >= 1, "Expected bidirectional error"


def test_broken_lifecycle_placement():
    """
    An issue document with non-terminal status ('open') placed in closed/.
    L2 must report a lifecycle error.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        build_workspace(tmpdir)
        open_issue = _issue_data()
        open_issue["issue_info"]["status"] = "open"
        open_issue["issue_info"]["coupled_docs"]["change_ref"] = ""
        _write(f"{tmpdir}/issues/closed/issue-{UUID}-adder-wrong-value.md",
               _md("Issue: adder wrong value (closed)", open_issue))

        findings = protocol_checker.run(tmpdir)
        errors = [f for f in findings if f.check == "lifecycle" and f.severity == "ERROR"]
        assert len(errors) >= 1, "Expected lifecycle ERROR for non-terminal status in closed/"


def test_broken_prompt_self_contained():
    """
    Prompt document has empty specification.description.
    L2 must report a prompt_self_contained error.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        build_workspace(tmpdir)
        bad_prompt = _prompt_data(spec_desc="")
        _write(f"{tmpdir}/prompt/prompt-{UUID}-implement-adder.md",
               _md("Prompt: implement adder", bad_prompt))

        findings = protocol_checker.run(tmpdir)
        errors = [f for f in findings if f.check == "prompt_self_contained"]
        assert len(errors) >= 1, "Expected prompt_self_contained error"


def test_broken_document_structure():
    """
    A governance document is missing its Version History section.
    L1 must report a structure error.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        build_workspace(tmpdir)
        # Overwrite change doc without Version History
        no_history = (
            "Created: 2025-01-01\n\n# Change: fix adder\n\n"
            + "```yaml\n" + yaml.dump(_change_data()) + "```\n\n"
            + "Copyright (c) 2025 William Watson. MIT License.\n"
        )
        _write(f"{tmpdir}/change/change-{UUID}-fix-adder.md", no_history)

        findings = linter.run(tmpdir)
        errors = [f for f in findings if f.check == "structure" and f.severity == "ERROR"]
        assert len(errors) >= 1, "Expected structure ERROR for missing Version History"


def test_broken_status_consistency():
    """
    Issue is 'closed' but coupled change is still 'proposed'.
    L2 must report a status_consistency error.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        build_workspace(tmpdir)

        closed_issue = _issue_data(change_ref=f"change-{UUID}")
        closed_issue["issue_info"]["status"] = "closed"
        _write(f"{tmpdir}/issues/issue-{UUID}-adder-wrong-value.md",
               _md("Issue: adder wrong value", closed_issue))

        proposed_change = _change_data(issue_ref=f"issue-{UUID}")
        proposed_change["change_info"]["status"] = "proposed"
        _write(f"{tmpdir}/change/change-{UUID}-fix-adder.md",
               _md("Change: fix adder", proposed_change))

        findings = protocol_checker.run(tmpdir)
        errors = [f for f in findings if f.check == "status_consistency"]
        assert len(errors) >= 1, "Expected status_consistency error"
        assert any("proposed" in f.message for f in errors)
