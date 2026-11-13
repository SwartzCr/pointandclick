#!/bin/bash
# Hotel Paradiso Arcade: install or update to the newest version.
#
# Downloads the latest disk image from GitHub, puts "Hotel Paradiso Arcade.app" in
# /Applications (replacing the old one), unblocks it, and copies the profile and the set-up
# guide into /Users/Shared/Hotel Paradiso Arcade. Run it from an administrator account.
#
# Double-click it in Finder (the first time: right-click it, choose Open, then Open), or in
# Terminal:
#   curl -fsSL https://raw.githubusercontent.com/SwartzCr/pointandclick/main/arcade/update-arcade.command | bash

set -euo pipefail

URL="https://github.com/SwartzCr/pointandclick/releases/download/arcade/Hotel-Paradiso-Arcade.dmg"
APP_NAME="Hotel Paradiso Arcade.app"
DEST="/Applications/$APP_NAME"
SHARED="/Users/Shared/Hotel Paradiso Arcade"

say() { printf '\n\033[1m%s\033[0m\n' "$*"; }

WORK=$(mktemp -d /tmp/hp-arcade.XXXXXX)
MOUNT="$WORK/mnt"
cleanup() {
  [ -d "$MOUNT" ] && hdiutil detach "$MOUNT" -quiet -force >/dev/null 2>&1 || true
  rm -rf "$WORK"
}
trap cleanup EXIT

# Is the arcade running (in this account or the Arcade account)? It has to close first.
if pgrep -x HotelParadisoArcade >/dev/null 2>&1; then
  say "The arcade is running (maybe in the Arcade account)."
  printf 'Close it now so it can be updated? Anyone playing will lose their place. [y/N] '
  read -r answer < /dev/tty || answer=n
  case "$answer" in
    y|Y|yes|YES)
      echo "Closing it (you may be asked for your password)..."
      sudo pkill -x HotelParadisoArcade || true
      sudo pkill -x scummvm || true
      sudo pkill -x LateCheckout || true
      sudo pkill -x DoNotDisturb || true
      sleep 2
      ;;
    *)
      echo "Left it alone. Log the Arcade account out, then run this again."
      exit 1
      ;;
  esac
fi

say "Downloading the newest Hotel Paradiso Arcade..."
curl -fL --progress-bar -o "$WORK/arcade.dmg" "$URL"

say "Opening the disk image..."
mkdir -p "$MOUNT"
hdiutil attach "$WORK/arcade.dmg" -nobrowse -readonly -noautoopen -mountpoint "$MOUNT" -quiet
if [ ! -d "$MOUNT/$APP_NAME" ]; then
  echo "Couldn't find $APP_NAME on the disk image." >&2
  exit 1
fi

# /Applications is normally writable by administrators; if not, use sudo for the copy
SUDO=""
if [ ! -w /Applications ] || { [ -e "$DEST" ] && [ ! -w "$DEST" ]; }; then
  SUDO="sudo"
  echo "Your password is needed to write to /Applications."
fi

say "Installing it in /Applications..."
$SUDO rm -rf "$DEST"
$SUDO ditto "$MOUNT/$APP_NAME" "$DEST"
# not from the App Store and not signed by a registered developer: tell macOS it's fine
$SUDO xattr -dr com.apple.quarantine "$DEST" 2>/dev/null || true

say "Copying the profile and the set-up guide to $SHARED..."
mkdir -p "$SHARED" 2>/dev/null || $SUDO mkdir -p "$SHARED"
for f in "Hotel Paradiso Arcade.mobileconfig" "Set up the arcade Mac.html" "update-arcade.command"; do
  if [ -e "$MOUNT/$f" ]; then
    cp -f "$MOUNT/$f" "$SHARED/" 2>/dev/null || $SUDO cp -f "$MOUNT/$f" "$SHARED/"
  fi
done
chmod -R a+rX "$SHARED" 2>/dev/null || $SUDO chmod -R a+rX "$SHARED" || true
chmod a+x "$SHARED/update-arcade.command" 2>/dev/null || true

VERSION=$(defaults read "$DEST/Contents/Info" CFBundleVersion 2>/dev/null || echo "?")
say "Done. Hotel Paradiso Arcade (build $VERSION) is in /Applications."
echo "If the Arcade account was logged in, log it out and back in to start the new version."
