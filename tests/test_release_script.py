"""Release kind chosen by bin/release.sh.

Covers audit-bce0d69a finding M02: a version other than X.Y.Z is
published as a pre-release and never as the latest release, which
bin/pi-install.sh installs.
"""

import re
import shutil
import subprocess
from pathlib import Path

import pytest

RELEASE_SH = Path(__file__).resolve().parent.parent / "bin" / "release.sh"


def _release_kind_block() -> str:
    """The if/else block of release.sh that sets RELEASE_KIND."""
    text = RELEASE_SH.read_text()
    match = re.search(r'^if \[\[ "\$VERSION" =~ .*?^fi$', text, re.M | re.S)
    assert match is not None, "RELEASE_KIND block not found in release.sh"
    return match.group(0)


def test_release_passes_the_computed_kind_only():
    text = RELEASE_SH.read_text()
    assert '"$RELEASE_KIND" \\' in text
    assert "    --latest \\" not in text


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
@pytest.mark.parametrize(
    "version, kind",
    [
        ("1.0.0", "--latest"),
        ("0.5.0", "--latest"),
        ("1.0.0rc1", "--prerelease"),
        ("1.0.0b2", "--prerelease"),
        ("1.0.0.dev1", "--prerelease"),
        ("1.0", "--prerelease"),
    ],
)
def test_release_kind_for_version(version, kind):
    script = f'VERSION="{version}"\n{_release_kind_block()}\necho "$RELEASE_KIND"\n'
    result = subprocess.run(
        ["bash", "-c", script], capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == kind
