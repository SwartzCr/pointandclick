#!/bin/bash
# Puts Hotel Paradiso Arcade.app together and packs it into a disk image. Runs on macOS (in
# GitHub Actions, see .github/workflows/arcade-mac.yml).
#
#   arcade/assemble.sh <ScummVM.app> <Do Not Disturb mac zip> <Do Not Disturb main menu image> <out dir>
set -euo pipefail
SCUMMVM_APP=$1
VN_ZIP=$2
VN_MENU=$3
OUT=$4
ROOT=$(cd "$(dirname "$0")/.." && pwd)
NAME="Hotel Paradiso Arcade"
WORK=$(mktemp -d)
APP="$WORK/$NAME.app"
MIN_OS=10.15

mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources/games/hotel-paradiso" "$APP/Contents/Resources/games/sacra-pasta"

# ---- the launcher itself
sed "s/BUILD_NUMBER/${GITHUB_RUN_NUMBER:-1}/" "$ROOT/arcade/launcher/Info.plist" > "$APP/Contents/Info.plist"
printf 'APPL????' > "$APP/Contents/PkgInfo"
xcrun swiftc -O -swift-version 5 -target x86_64-apple-macos$MIN_OS \
  "$ROOT/arcade/launcher/main.swift" -o "$APP/Contents/MacOS/HotelParadisoArcade"

# ---- pictures and the icon
python3 -c "import PIL" 2>/dev/null || python3 -m pip install --quiet --break-system-packages pillow || python3 -m pip install --quiet pillow
python3 "$ROOT/arcade/make_art.py" "$WORK/art-out" "$VN_MENU"
cp -R "$WORK/art-out/art" "$APP/Contents/Resources/art"
iconutil -c icns "$WORK/art-out/AppIcon.iconset" -o "$APP/Contents/Resources/AppIcon.icns"

# ---- the games
cp "$ROOT/hotel-paradiso-scummc/dist/tentacle.000" "$ROOT/hotel-paradiso-scummc/dist/tentacle.001" \
   "$APP/Contents/Resources/games/hotel-paradiso/"
cp "$ROOT/hotel-paradiso-sacra-pasta/dist/sacrapasta.ags" "$APP/Contents/Resources/games/sacra-pasta/"
ditto "$SCUMMVM_APP" "$APP/Contents/Resources/ScummVM.app"
mkdir "$WORK/vn"
ditto -x -k "$VN_ZIP" "$WORK/vn"
VN_APP=$(find "$WORK/vn" -maxdepth 3 -name '*.app' -type d | head -n 1)
if [ -z "$VN_APP" ]; then echo "No .app in $VN_ZIP" >&2; find "$WORK/vn" -maxdepth 3; exit 1; fi
ditto "$VN_APP" "$APP/Contents/Resources/DoNotDisturb.app"

# ---- will every program in here run on macOS $MIN_OS? (each Mach-O file's minimum macOS)
echo "Minimum macOS of each program in the app:"
bad=0
while IFS= read -r -d '' f; do
  if file "$f" | grep -q 'Mach-O'; then
    for arch in $(lipo -archs "$f" 2>/dev/null || echo x86_64); do
      v=$(otool -arch "$arch" -l "$f" 2>/dev/null | awk '/LC_BUILD_VERSION/{b=1} b&&/minos/{print $2; exit} /LC_VERSION_MIN_MACOSX/{m=1} m&&/version/{print $2; exit}')
      [ -z "$v" ] && continue
      echo "  $v  $arch  ${f#$APP/}"
      if [ "$arch" = x86_64 ] && [ "$(printf '%s\n%s\n' "$v" "$MIN_OS" | sort -V | tail -n 1)" != "$MIN_OS" ]; then
        echo "::error title=Too new for macOS $MIN_OS::${f#$APP/} needs macOS $v"
        bad=1
      fi
    done
  fi
done < <(find "$APP" -type f -print0)
# any library outside the app and the system would be missing on the arcade Mac
while IFS= read -r -d '' f; do
  if file "$f" | grep -q 'Mach-O'; then
    otool -L "$f" | tail -n +2 | awk '{print $1}' | grep -v -E '^(/System/|/usr/lib/|@executable_path|@loader_path|@rpath)' \
      | sed "s#^#::error title=Missing library::${f#$APP/} uses #" || true
    if otool -L "$f" | tail -n +2 | awk '{print $1}' | grep -q -v -E '^(/System/|/usr/lib/|@executable_path|@loader_path|@rpath)'; then bad=1; fi
  fi
done < <(find "$APP/Contents/MacOS" "$APP/Contents/Resources/ScummVM.app/Contents/MacOS" -type f -print0)
[ $bad = 0 ] || exit 1

# ---- sign it (ad hoc: no developer account, but macOS wants every program signed somehow)
codesign --force --deep --sign - "$APP/Contents/Resources/DoNotDisturb.app"
codesign --force --deep --sign - "$APP/Contents/Resources/ScummVM.app"
codesign --force --deep --sign - "$APP"
codesign --verify --deep --strict "$APP" && echo "Signature OK"

# ---- the disk image: the app, the profile and the set-up guide
mkdir -p "$OUT"
STAGE="$WORK/dmg"
mkdir "$STAGE"
ditto "$APP" "$STAGE/$NAME.app"
ln -s /Applications "$STAGE/Applications"
cp "$ROOT/arcade/profile/Hotel Paradiso Arcade.mobileconfig" "$STAGE/"
cp "$ROOT/arcade/SETUP.html" "$STAGE/Set up the arcade Mac.html"
# hdiutil sometimes fails with "Resource busy" on GitHub's Macs; try a few times
for i in 1 2 3 4 5; do
  if hdiutil create -volname "$NAME" -srcfolder "$STAGE" -ov -format UDZO "$OUT/Hotel-Paradiso-Arcade.dmg"; then break; fi
  [ $i = 5 ] && exit 1
  sleep $((i * 10))
done
ls -la "$OUT"
