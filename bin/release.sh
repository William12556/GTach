#!/bin/bash
# GTach Release Script
# Creates a versioned GitHub release with dist artefacts.
# Requires: gh CLI authenticated, dist/ built via build.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# ---------------------------------------------------------------------------
# gh CLI check
# ---------------------------------------------------------------------------
if ! command -v gh >/dev/null 2>&1; then
    echo "ERROR: gh CLI not found"
    echo "Install: https://cli.github.com"
    exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
    echo "ERROR: gh not authenticated"
    echo "Run: gh auth login"
    exit 1
fi

# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------
VERSION=$(grep '^version = ' pyproject.toml | cut -d'"' -f2)

if [ -z "$VERSION" ]; then
    echo "ERROR: Could not extract version from pyproject.toml"
    exit 1
fi

TAG="v${VERSION}"

# ---------------------------------------------------------------------------
# Dist artefacts
# ---------------------------------------------------------------------------
WHEEL="dist/gtach-${VERSION}-py3-none-any.whl"
TARBALL="dist/gtach-${VERSION}.tar.gz"

if [ ! -f "$WHEEL" ]; then
    echo "ERROR: Wheel not found: $WHEEL"
    echo "Run: ./bin/build.sh"
    exit 1
fi

if [ ! -f "$TARBALL" ]; then
    echo "ERROR: Tarball not found: $TARBALL"
    echo "Run: ./bin/build.sh"
    exit 1
fi

# ---------------------------------------------------------------------------
# Uncommitted changes warning
# ---------------------------------------------------------------------------
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "WARNING: Uncommitted changes in working tree"
    read -r -p "Continue? [y/N] " CONFIRM
    case "$CONFIRM" in
        [yY]) ;;
        *) echo "Aborted."; exit 1 ;;
    esac
fi

# ---------------------------------------------------------------------------
# Release
# ---------------------------------------------------------------------------
echo "==> Creating release $TAG"

gh release create "$TAG" \
    --title "$TAG" \
    --notes "GTach $TAG" \
    --latest \
    "$WHEEL" \
    "$TARBALL"

echo ""
echo "✓ Release $TAG published"
