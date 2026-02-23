#!/usr/bin/env bash
# ABOUTME: Build script for macOS .app bundle and DMG.
# ABOUTME: Creates make-audiobook.app using py2app and packages as DMG.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VERSION="${1:-$(git describe --tags --abbrev=0 2>/dev/null || echo "0.1.0")}"
VERSION="${VERSION#v}"  # Strip leading 'v' if present
APP_NAME="make-audiobook"
BUILD_DIR="$PROJECT_DIR/build"
DIST_DIR="$PROJECT_DIR/dist"

echo "Building $APP_NAME version $VERSION"

cd "$PROJECT_DIR"

# Clean previous builds
rm -rf "$BUILD_DIR" "$DIST_DIR"
mkdir -p "$BUILD_DIR" "$DIST_DIR"

# Create clean virtual environment for build
echo "Creating build environment..."
python3 -m venv "$BUILD_DIR/venv"
source "$BUILD_DIR/venv/bin/activate"

# Install build dependencies
pip install --upgrade pip
pip install py2app PySide6 requests

# Install project dependencies
if [[ -f requirements-gui.txt ]]; then
    pip install -r requirements-gui.txt
fi

# Create py2app setup file
cat > "$BUILD_DIR/setup.py" << 'SETUP_EOF'
"""py2app build configuration for make-audiobook."""
from setuptools import setup

APP = ['gui/app.py']
DATA_FILES = [
    ('scripts', ['make-audiobook', 'piper-voices-setup', 'install-dependencies']),
]
OPTIONS = {
    'argv_emulation': False,
    'packages': ['gui', 'PySide6', 'requests'],
    'includes': [
        'gui.app',
        'gui.models',
        'gui.views',
        'gui.workers',
        'gui.utils',
    ],
    'excludes': ['tkinter', 'matplotlib', 'numpy', 'scipy', 'packaging', 'setuptools'],
    'iconfile': 'resources/icon.icns' if __import__('os').path.exists('resources/icon.icns') else None,
    'plist': {
        'CFBundleName': 'make-audiobook',
        'CFBundleDisplayName': 'make-audiobook',
        'CFBundleIdentifier': 'com.tigger04.make-audiobook',
        'CFBundleVersion': '__VERSION__',
        'CFBundleShortVersionString': '__VERSION__',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
        'LSMinimumSystemVersion': '10.15',
    }
}

setup(
    name='make-audiobook',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
SETUP_EOF

# Replace version placeholder (portable: avoids sed -i which differs between GNU/macOS)
sed "s/__VERSION__/$VERSION/g" "$BUILD_DIR/setup.py" > "$BUILD_DIR/setup.py.tmp"
mv "$BUILD_DIR/setup.py.tmp" "$BUILD_DIR/setup.py"

# Copy setup.py to project root for py2app
cp "$BUILD_DIR/setup.py" "$PROJECT_DIR/setup.py"

# Build the app
echo "Building .app bundle..."
python setup.py py2app --dist-dir "$DIST_DIR"

# Clean up setup.py from project root
rm -f "$PROJECT_DIR/setup.py"

# Verify the app was created
if [[ ! -d "$DIST_DIR/$APP_NAME.app" ]]; then
    echo "Error: App bundle was not created"
    exit 1
fi

echo "App bundle created: $DIST_DIR/$APP_NAME.app"

# Create DMG if create-dmg is available
if command -v create-dmg &>/dev/null; then
    echo "Creating DMG..."

    DMG_NAME="${APP_NAME}-${VERSION}.dmg"

    # Remove existing DMG if present
    rm -f "$DIST_DIR/$DMG_NAME"

    # Build create-dmg command
    CREATE_DMG_ARGS=(
        --volname "$APP_NAME"
        --window-pos 200 120
        --window-size 600 400
        --icon-size 100
        --icon "$APP_NAME.app" 150 200
        --app-drop-link 450 200
        --hide-extension "$APP_NAME.app"
    )

    # Add volicon if icon exists
    if [[ -f "$PROJECT_DIR/resources/icon.icns" ]]; then
        CREATE_DMG_ARGS+=(--volicon "$PROJECT_DIR/resources/icon.icns")
    fi

    create-dmg "${CREATE_DMG_ARGS[@]}" \
        "$DIST_DIR/$DMG_NAME" \
        "$DIST_DIR/$APP_NAME.app"

    echo "DMG created: $DIST_DIR/$DMG_NAME"

    # Calculate SHA256 for Homebrew cask
    SHA256=$(shasum -a 256 "$DIST_DIR/$DMG_NAME" | awk '{print $1}')
    echo ""
    echo "SHA256: $SHA256"
    echo ""
    echo "Update homebrew/Casks/make-audiobook.rb with:"
    echo "  version \"$VERSION\""
    echo "  sha256 \"$SHA256\""
else
    echo ""
    echo "Note: create-dmg not found. Install with: brew install create-dmg"
    echo "Skipping DMG creation. App bundle is available at: $DIST_DIR/$APP_NAME.app"
fi

# Deactivate virtual environment
deactivate

echo ""
echo "Build complete!"
