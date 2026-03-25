"""
Layer 4 Regression Tests — Framework/skel consistency.

Validates that the live repository state matches governance.md declarations.
Runs against the actual filesystem; no temp directories.

Checks:
  1. Template file existence       (P00 §1.1.17)
  2. Skel workspace structure      (P01 §1.2.6)
  3. Skel AEL source files         (P01 §1.2.8, §1.1.11)
  4. Framework/skel template parity

These tests fail when:
  - A template is added to governance but not created on disk
  - skel/workspace/ diverges from the closed/ structure in governance
  - A template is updated in framework/ but not mirrored to skel/
  - AEL source files are renamed or removed from skel/
"""

import os

import pytest

# ── Repository root ───────────────────────────────────────────────────────────

# Resolve relative to this test file: tests/ → ael/ → ai/ → framework/ → repo root
_HERE     = os.path.dirname(__file__)
_REPO     = os.path.normpath(os.path.join(_HERE, "..", "..", "..", ".."))
_FRAMEWORK = os.path.join(_REPO, "framework", "ai")
_SKEL      = os.path.join(_REPO, "skel")


# ── Check 1: Template file existence (P00 §1.1.17) ───────────────────────────

# Canonical template list from governance.md §1.1.17
_TEMPLATES = [
    "T01-design.md",
    "T02-change.md",
    "T03-issue.md",
    "T04-prompt.md",
    "T05-test.md",
    "T06-result.md",
    "T07-requirements.md",
]


@pytest.mark.parametrize("template", _TEMPLATES)
def test_template_exists_in_framework(template: str):
    """Each governance template must exist in framework/ai/templates/."""
    path = os.path.join(_FRAMEWORK, "templates", template)
    assert os.path.isfile(path), \
        f"Template missing from framework/ai/templates/: {template}"


@pytest.mark.parametrize("template", _TEMPLATES)
def test_template_exists_in_skel(template: str):
    """Each governance template must exist in skel/ai/templates/."""
    path = os.path.join(_SKEL, "ai", "templates", template)
    assert os.path.isfile(path), \
        f"Template missing from skel/ai/templates/: {template}"


# ── Check 2: Skel workspace structure (P01 §1.2.6) ───────────────────────────

# Canonical closed/ subdirectory set from governance.md §1.1.14.5 and §1.2.6
_WORKSPACE_DIRS = [
    "requirements",
    "design",
    "change",
    "change/closed",
    "issues",
    "issues/closed",
    "knowledge",
    "prompt",
    "prompt/closed",
    "trace",
    "audit",
    "audit/closed",
    "test",
    "test/closed",
    "test/result",
    "test/result/closed",
]


@pytest.mark.parametrize("subdir", _WORKSPACE_DIRS)
def test_skel_workspace_subdir_exists(subdir: str):
    """Each workspace subdirectory mandated by governance must exist in skel."""
    path = os.path.join(_SKEL, "workspace", subdir)
    assert os.path.isdir(path), \
        f"Workspace directory missing from skel/workspace/: {subdir}"


# ── Check 3: Skel AEL source files (P01 §1.2.8, §1.1.11) ────────────────────

# Tactical Domain runtime contract — these files define the AEL interface
_AEL_SOURCES = [
    "orchestrator.py",
    "mcp_client.py",
    "parser.py",
]


@pytest.mark.parametrize("source", _AEL_SOURCES)
def test_skel_ael_source_exists(source: str):
    """Each AEL source file must be present in skel/ai/ael/src/."""
    path = os.path.join(_SKEL, "ai", "ael", "src", source)
    assert os.path.isfile(path), \
        f"AEL source file missing from skel/ai/ael/src/: {source}"


# ── Check 4: Framework/skel template parity ───────────────────────────────────

@pytest.mark.parametrize("template", _TEMPLATES)
def test_template_content_parity(template: str):
    """
    Templates in framework/ai/templates/ and skel/ai/templates/ must be
    byte-identical. A divergence indicates skel was not updated after a
    framework template change.
    """
    framework_path = os.path.join(_FRAMEWORK, "templates", template)
    skel_path      = os.path.join(_SKEL, "ai", "templates", template)

    if not os.path.isfile(framework_path):
        pytest.skip(f"Framework template absent (caught by Check 1): {template}")
    if not os.path.isfile(skel_path):
        pytest.skip(f"Skel template absent (caught by Check 1): {template}")

    framework_content = open(framework_path, "rb").read()
    skel_content      = open(skel_path, "rb").read()

    assert framework_content == skel_content, (
        f"Template content mismatch between framework/ and skel/: {template}\n"
        f"framework: {len(framework_content)} bytes  "
        f"skel: {len(skel_content)} bytes"
    )
