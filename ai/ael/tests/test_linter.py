"""
Unit tests for linter.py — Layer 1 Governance Linter.
No external services required; all fixtures use temporary directories.
"""

import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from linter import (
    Finding,
    check_coupling,
    check_links,
    check_naming,
    check_structure,
    check_yaml,
    run,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _write(dirpath: str, fname: str, content: str) -> str:
    """Write content to fname in dirpath; return full path."""
    path = os.path.join(dirpath, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def _minimal_md(extra: str = "") -> str:
    """Minimal valid governance markdown document."""
    return f"""Created: 2025-01-01

# Title

{extra}

## Version History

| Version | Date | Description |
| ------- | ---- | ----------- |
| 1.0     | 2025-01-01 | Initial |

Copyright (c) 2025 William Watson. MIT License.
"""


def _yaml_block(yaml_content: str) -> str:
    return f"```yaml\n{yaml_content}\n```"


_VALID_ISSUE_YAML = """\
issue_info:
  id: "issue-a1b2c3d4"
  title: "Test issue"
  date: "2025-01-01"
  status: "open"
  severity: "low"
  type: "bug"
  iteration: 1
  coupled_docs:
    change_ref: ""
    change_iteration: null
source:
  origin: "test_result"
  description: "test"
affected_scope:
  components:
    - name: "test"
      file_path: "src/test.py"
behavior:
  expected: "works"
  actual: "fails"
metadata:
  template_version: "1.0"
  schema_type: "t03_issue"
"""

_VALID_CHANGE_YAML = """\
change_info:
  id: "change-b2c3d4e5"
  title: "Test change"
  date: "2025-01-01"
  status: "proposed"
  priority: "low"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-a1b2c3d4"
    issue_iteration: 1
source:
  type: "issue"
  description: "test"
scope:
  summary: "test"
  affected_components:
    - name: "test"
      file_path: "src/test.py"
      change_type: "modify"
rational:
  problem_statement: "test"
  proposed_solution: "test"
technical_details:
  current_behavior: "test"
  proposed_behavior: "test"
  implementation_approach: "test"
metadata:
  template_version: "1.0"
  schema_type: "t02_change"
"""


# ── Check 1: naming ───────────────────────────────────────────────────────────

def test_naming_master_valid():
    findings = check_naming("design-myproject-master.md",
                            "/workspace/design-myproject-master.md")
    assert findings == []


def test_naming_normal_valid():
    findings = check_naming("change-a1b2c3d4-fix-parser.md",
                            "/workspace/change-a1b2c3d4-fix-parser.md")
    assert findings == []


def test_naming_readme_ignored():
    findings = check_naming("README.md", "/workspace/README.md")
    assert findings == []


def test_naming_name_registry_master_valid():
    findings = check_naming("design-myproject-name_registry-master.md",
                            "/workspace/design-myproject-name_registry-master.md")
    assert findings == []


def test_naming_unknown_class_master():
    findings = check_naming("widget-myproject-master.md",
                            "/workspace/widget-myproject-master.md")
    errors = [f for f in findings if f.severity == "ERROR" and f.check == "naming"]
    assert len(errors) == 1
    assert "widget" in errors[0].message


def test_naming_unknown_class_normal():
    findings = check_naming("widget-a1b2c3d4-thing.md",
                            "/workspace/widget-a1b2c3d4-thing.md")
    errors = [f for f in findings if f.severity == "ERROR" and f.check == "naming"]
    assert len(errors) == 1


# ── Check 2: structure ────────────────────────────────────────────────────────

def test_structure_valid():
    content = _minimal_md()
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
        f.write(content.encode())
        path = f.name
    try:
        findings = check_structure(path, content)
        assert findings == []
    finally:
        os.unlink(path)


def test_structure_missing_version_history():
    content = "Created: 2025-01-01\n\n# Title\n\nCopyright (c) 2025\n"
    findings = check_structure("/fake/path.md", content)
    errors = [f for f in findings if f.severity == "ERROR"]
    assert any("Version History" in f.message for f in errors)


def test_structure_missing_created():
    content = "# Title\n\n## Version History\n\nCopyright (c) 2025\n"
    findings = check_structure("/fake/path.md", content)
    warns = [f for f in findings if f.severity == "WARN"]
    assert any("Created" in f.message for f in warns)


def test_structure_missing_copyright():
    content = "Created: 2025-01-01\n\n# Title\n\n## Version History\n"
    findings = check_structure("/fake/path.md", content)
    warns = [f for f in findings if f.severity == "WARN"]
    assert any("copyright" in f.message.lower() for f in warns)


# ── Check 3: YAML field validity ──────────────────────────────────────────────

def test_yaml_no_block():
    findings, data, schema = check_yaml("/fake/path.md", "No YAML here.")
    assert findings == []
    assert data is None
    assert schema is None


def test_yaml_missing_schema_type():
    content = _yaml_block("metadata:\n  template_version: '1.0'\n")
    findings, data, schema = check_yaml("/fake/path.md", content)
    warns = [f for f in findings if f.severity == "WARN"]
    assert any("schema_type" in f.message for f in warns)
    assert schema is None


def test_yaml_valid_issue():
    content = _yaml_block(_VALID_ISSUE_YAML)
    findings, data, schema = check_yaml("/fake/issue-a1b2c3d4-test.md", content)
    errors = [f for f in findings if f.severity == "ERROR"]
    assert errors == []
    assert schema == "t03_issue"


def test_yaml_id_missing():
    yaml_content = _VALID_ISSUE_YAML.replace('id: "issue-a1b2c3d4"', 'id: ""')
    content = _yaml_block(yaml_content)
    findings, _, _ = check_yaml("/fake/issue-a1b2c3d4-test.md", content)
    errors = [f for f in findings if f.severity == "ERROR" and "issue_info.id" in f.message]
    assert len(errors) == 1


def test_yaml_id_wrong_pattern():
    yaml_content = _VALID_ISSUE_YAML.replace('"issue-a1b2c3d4"', '"issue-XXXXXXXX"')
    content = _yaml_block(yaml_content)
    findings, _, _ = check_yaml("/fake/issue-a1b2c3d4-test.md", content)
    errors = [f for f in findings if f.severity == "ERROR" and "pattern" in f.message]
    assert len(errors) == 1


def test_yaml_invalid_status_enum():
    yaml_content = _VALID_ISSUE_YAML.replace("status: \"open\"", "status: \"unknown_status\"")
    content = _yaml_block(yaml_content)
    findings, _, _ = check_yaml("/fake/issue-a1b2c3d4-test.md", content)
    errors = [f for f in findings if f.severity == "ERROR" and "status" in f.message]
    assert len(errors) == 1
    assert "unknown_status" in errors[0].message


def test_yaml_invalid_severity_enum():
    yaml_content = _VALID_ISSUE_YAML.replace("severity: \"low\"", "severity: \"extreme\"")
    content = _yaml_block(yaml_content)
    findings, _, _ = check_yaml("/fake/issue-a1b2c3d4-test.md", content)
    errors = [f for f in findings if "severity" in f.message]
    assert len(errors) == 1


def test_yaml_iteration_zero():
    yaml_content = _VALID_ISSUE_YAML.replace("iteration: 1", "iteration: 0")
    content = _yaml_block(yaml_content)
    findings, _, _ = check_yaml("/fake/issue-a1b2c3d4-test.md", content)
    errors = [f for f in findings if f.severity == "ERROR" and "iteration" in f.message]
    assert len(errors) == 1


def test_yaml_iteration_negative():
    yaml_content = _VALID_ISSUE_YAML.replace("iteration: 1", "iteration: -3")
    content = _yaml_block(yaml_content)
    findings, _, _ = check_yaml("/fake/issue-a1b2c3d4-test.md", content)
    errors = [f for f in findings if f.severity == "ERROR" and "iteration" in f.message]
    assert len(errors) == 1


def test_yaml_valid_change():
    content = _yaml_block(_VALID_CHANGE_YAML)
    findings, _, schema = check_yaml("/fake/change-b2c3d4e5-test.md", content)
    errors = [f for f in findings if f.severity == "ERROR"]
    assert errors == []
    assert schema == "t02_change"


# ── Check 4: coupling integrity ───────────────────────────────────────────────

def _parse_yaml_data(yaml_str: str) -> dict:
    import yaml as _yaml
    return _yaml.safe_load(yaml_str)


def test_coupling_valid_change_references_issue():
    change_data = _parse_yaml_data(_VALID_CHANGE_YAML)
    issue_data  = _parse_yaml_data(_VALID_ISSUE_YAML)
    doc_index = {"issue-a1b2c3d4": issue_data}
    findings = check_coupling("/fake/change-b2c3d4e5-test.md",
                              change_data, "t02_change", doc_index)
    errors = [f for f in findings if f.severity == "ERROR"]
    assert errors == []


def test_coupling_ref_not_found():
    change_data = _parse_yaml_data(_VALID_CHANGE_YAML)
    doc_index = {}  # issue absent
    findings = check_coupling("/fake/change-b2c3d4e5-test.md",
                              change_data, "t02_change", doc_index)
    errors = [f for f in findings if f.severity == "ERROR" and "not found" in f.message]
    assert len(errors) == 1


def test_coupling_empty_ref_warns():
    yaml_content = _VALID_CHANGE_YAML.replace(
        'issue_ref: "issue-a1b2c3d4"', 'issue_ref: ""')
    change_data = _parse_yaml_data(yaml_content)
    findings = check_coupling("/fake/change-b2c3d4e5-test.md",
                              change_data, "t02_change", {})
    warns = [f for f in findings if f.severity == "WARN" and "coupling" in f.check]
    assert len(warns) == 1


def test_coupling_iteration_mismatch():
    yaml_content = _VALID_CHANGE_YAML.replace(
        "issue_iteration: 1", "issue_iteration: 2")
    change_data = _parse_yaml_data(yaml_content)
    issue_data  = _parse_yaml_data(_VALID_ISSUE_YAML)
    doc_index = {"issue-a1b2c3d4": issue_data}
    findings = check_coupling("/fake/change-b2c3d4e5-test.md",
                              change_data, "t02_change", doc_index)
    errors = [f for f in findings if f.severity == "ERROR" and "mismatch" in f.message]
    assert len(errors) == 1


def test_coupling_no_coupling_for_issue():
    # t03_issue has no outgoing coupling to check — no findings expected
    issue_data = _parse_yaml_data(_VALID_ISSUE_YAML)
    findings = check_coupling("/fake/issue-a1b2c3d4-test.md",
                              issue_data, "t03_issue", {})
    assert findings == []


# ── Check 5: Obsidian link targets ────────────────────────────────────────────

def test_links_valid_anchor():
    content = (
        "## Installation\n\n"
        "[Installation](<#installation>)\n"
    )
    findings = check_links("/fake/doc.md", content, "/fake")
    warns = [f for f in findings if f.check == "links"]
    assert warns == []


def test_links_missing_anchor():
    content = "[Nonexistent](<#nonexistent section>)\n"
    findings = check_links("/fake/doc.md", content, "/fake")
    warns = [f for f in findings if f.check == "links"]
    assert len(warns) == 1
    assert "nonexistent" in warns[0].message.lower()


def test_links_valid_file_link():
    with tempfile.TemporaryDirectory() as tmpdir:
        target_path = os.path.join(tmpdir, "other.md")
        open(target_path, "w").close()
        content = "[Other](other.md)\n"
        findings = check_links(os.path.join(tmpdir, "doc.md"), content, tmpdir)
        warns = [f for f in findings if f.check == "links"]
        assert warns == []


def test_links_missing_file_link():
    with tempfile.TemporaryDirectory() as tmpdir:
        content = "[Missing](missing.md)\n"
        findings = check_links(os.path.join(tmpdir, "doc.md"), content, tmpdir)
        warns = [f for f in findings if f.check == "links"]
        assert len(warns) == 1
        assert "missing.md" in warns[0].message


# ── Integration: run() on a temp workspace ───────────────────────────────────

def test_run_empty_workspace():
    with tempfile.TemporaryDirectory() as tmpdir:
        findings = run(tmpdir)
        assert findings == []


def test_run_clean_workspace():
    """A workspace with one valid issue document produces no errors."""
    with tempfile.TemporaryDirectory() as tmpdir:
        content = _minimal_md(_yaml_block(_VALID_ISSUE_YAML))
        _write(tmpdir, "issue-a1b2c3d4-test-issue.md", content)
        findings = run(tmpdir)
        errors = [f for f in findings if f.severity == "ERROR"]
        assert errors == []


def test_run_detects_missing_version_history():
    with tempfile.TemporaryDirectory() as tmpdir:
        content = "Created: 2025-01-01\n\n# Title\n\nCopyright (c) 2025\n"
        content += "\n" + _yaml_block(_VALID_ISSUE_YAML)
        _write(tmpdir, "issue-a1b2c3d4-test-issue.md", content)
        findings = run(tmpdir)
        errors = [f for f in findings if f.severity == "ERROR" and f.check == "structure"]
        assert len(errors) == 1


def test_run_coupled_chain_valid():
    """Issue + change with valid coupling: no coupling errors."""
    with tempfile.TemporaryDirectory() as tmpdir:
        issue_content = _minimal_md(_yaml_block(_VALID_ISSUE_YAML))
        change_content = _minimal_md(_yaml_block(_VALID_CHANGE_YAML))
        _write(tmpdir, "issue-a1b2c3d4-test.md", issue_content)
        _write(tmpdir, "change-b2c3d4e5-test.md", change_content)
        findings = run(tmpdir)
        errors = [f for f in findings if f.severity == "ERROR" and f.check == "coupling"]
        assert errors == []


def test_run_coupled_chain_broken():
    """Change references non-existent issue: coupling error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        change_content = _minimal_md(_yaml_block(_VALID_CHANGE_YAML))
        _write(tmpdir, "change-b2c3d4e5-test.md", change_content)
        # No issue document written
        findings = run(tmpdir)
        errors = [f for f in findings if f.severity == "ERROR" and f.check == "coupling"]
        assert len(errors) == 1
        assert "issue-a1b2c3d4" in errors[0].message


def test_run_readme_not_checked():
    """README.md in workspace does not produce structure findings."""
    with tempfile.TemporaryDirectory() as tmpdir:
        _write(tmpdir, "README.md", "# Readme\nNo governance content here.\n")
        findings = run(tmpdir)
        struct_findings = [f for f in findings if f.check == "structure"]
        assert struct_findings == []
