#!/bin/bash
set -euo pipefail

echo "Installing Work Timer..."

REPO="hgpt185/worktimer"
DMG_URL="https://github.com/$REPO/raw/main/Work%20Timer.dmg"
INSTALL_TMP=$(mktemp -d)
MOUNT_DIR="$INSTALL_TMP/mount"
cleanup() {
    if mount | grep -Fq " on $MOUNT_DIR ("; then
        hdiutil detach "$MOUNT_DIR" -quiet || true
    fi
    rm -rf "$INSTALL_TMP"
}
trap cleanup EXIT
mkdir "$MOUNT_DIR"

curl -fL -o "$INSTALL_TMP/Work Timer.dmg" "$DMG_URL"
hdiutil attach "$INSTALL_TMP/Work Timer.dmg" -nobrowse -readonly -mountpoint "$MOUNT_DIR" -quiet

if pgrep -x "Work Timer" >/dev/null; then
    osascript -e 'tell application "Work Timer" to quit'
fi
ditto "$MOUNT_DIR/Work Timer.app" "/Applications/Work Timer.app"

echo ""
echo "Work Timer installed to /Applications/Work Timer.app"
echo "Launching..."
open "/Applications/Work Timer.app"
echo "Done. Look for the ⏳ in your menu bar."
