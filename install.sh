#!/bin/bash
set -e

echo "Installing Respite..."

REPO="hgpt185/worktimer"
DMG_URL="https://github.com/$REPO/raw/main/Respite.dmg"
TMP_DMG="/tmp/Respite.dmg"

curl -L -o "$TMP_DMG" "$DMG_URL"

MOUNT_DIR=$(hdiutil attach "$TMP_DMG" -nobrowse | grep "/Volumes" | awk '{print $NF}')

rm -rf "/Applications/Respite.app"
cp -R "$MOUNT_DIR/Respite.app" /Applications/

hdiutil detach "$MOUNT_DIR" -quiet
rm -f "$TMP_DMG"

echo ""
echo "Respite installed to /Applications/Respite.app"
echo "Launching..."
open /Applications/Respite.app
echo "Done. Look for the ⏳ in your menu bar."
