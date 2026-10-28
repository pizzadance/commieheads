#!/bin/sh
# Builds CommieHeads.saver (universal arm64 + x86_64) into ../dist/
set -e
cd "$(dirname "$0")"
OUT=../dist/CommieHeads.saver
rm -rf "$OUT"
mkdir -p "$OUT/Contents/MacOS" "$OUT/Contents/Resources/heads"
clang -bundle -fobjc-arc -O2 -arch arm64 -arch x86_64 -mmacosx-version-min=11.0 \
  -framework Cocoa -framework ScreenSaver -framework QuartzCore \
  CommieHeadsView.m -o "$OUT/Contents/MacOS/CommieHeads"
cp Info.plist "$OUT/Contents/Info.plist"
cp ../assets/quotes.json "$OUT/Contents/Resources/"
cp ../assets/heads/*.png "$OUT/Contents/Resources/heads/"
codesign --force --deep -s - "$OUT"
echo "Built $OUT"
