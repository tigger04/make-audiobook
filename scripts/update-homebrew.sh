#!/usr/bin/env bash
# ABOUTME: Update Homebrew formula and cask templates with new version and SHA256.
# ABOUTME: Called by `make release` after building the DMG.

set -euo pipefail
IFS=$'\n\t'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

VERSION="${1:?Usage: update-homebrew.sh VERSION [DMG_SHA256]}"
DMG_SHA256="${2:-}"

CASK_FILE="$PROJECT_DIR/homebrew/Casks/make-audiobook.rb"
FORMULA_FILE="$PROJECT_DIR/homebrew/Formula/make-audiobook.rb"

if [[ ! -f "$CASK_FILE" ]]; then
    echo "Error: Cask file not found: $CASK_FILE" >&2
    exit 1
fi

if [[ ! -f "$FORMULA_FILE" ]]; then
    echo "Error: Formula file not found: $FORMULA_FILE" >&2
    exit 1
fi

echo "Updating Homebrew files to version $VERSION..."

# Update cask: version and SHA256
# Use temp files for portable sed (works on both macOS and Linux)
tmp_cask="$(mktemp)"
awk -v ver="$VERSION" -v sha="$DMG_SHA256" '
    /^  version / { print "  version \"" ver "\""; next }
    /^  sha256 / && sha != "" { print "  sha256 \"" sha "\""; next }
    { print }
' "$CASK_FILE" > "$tmp_cask"
mv "$tmp_cask" "$CASK_FILE"

echo "  Updated cask: version=$VERSION${DMG_SHA256:+ sha256=$DMG_SHA256}"

# Update formula: version in URL and SHA256 placeholder
tmp_formula="$(mktemp)"
awk -v ver="$VERSION" '
    /url "https:\/\/github.com\/tigger04\/make-audiobook\/archive\/refs\/tags\/v/ {
        print "  url \"https://github.com/tigger04/make-audiobook/archive/refs/tags/v" ver ".tar.gz\""
        next
    }
    { print }
' "$FORMULA_FILE" > "$tmp_formula"
mv "$tmp_formula" "$FORMULA_FILE"

echo "  Updated formula: url points to v$VERSION"
echo ""
echo "Note: Formula tarball SHA256 will be updated by CI after the tag is pushed."
echo "      Cask SHA256 will also be verified by CI from the release DMG."
