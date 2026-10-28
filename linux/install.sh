#!/bin/sh
# Install CommieHeads on Debian/Ubuntu/Kali (X11).
#   sudo apt install python3-pygame
#   sh linux/install.sh
#
# Screensaver hosts (xfce4-screensaver, mate-screensaver) only run programs that live in their
# hack directories, so the program is installed system-wide (sudo) into /usr/local/share/commieheads
# and linked into the xscreensaver hack directory.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
SRC_ASSETS="$HERE/assets"; [ -d "$SRC_ASSETS" ] || SRC_ASSETS="$HERE/../assets"
[ -f "$SRC_ASSETS/quotes.json" ] || { echo "assets not found next to $0"; exit 1; }
python3 -c "import pygame" 2>/dev/null || echo "WARNING: pygame missing -> sudo apt install python3-pygame"

SHARE=/usr/local/share/commieheads
HACKDIR=/usr/libexec/xscreensaver
[ -d "$HACKDIR" ] || HACKDIR=/usr/lib/xscreensaver
sudo mkdir -p "$SHARE" "$HACKDIR"
sudo rm -rf "$SHARE/assets"
sudo cp "$HERE/commieheads.py" "$SHARE/"
sudo cp -R "$SRC_ASSETS" "$SHARE/assets"
sudo chmod 755 "$SHARE/commieheads.py"
sudo ln -sf "$SHARE/commieheads.py" "$HACKDIR/commieheads"
sudo ln -sf "$SHARE/commieheads.py" /usr/local/bin/commieheads

# XFCE / MATE screensaver: theme entry
sudo mkdir -p /usr/share/applications/screensavers
sudo tee /usr/share/applications/screensavers/commieheads.desktop >/dev/null <<EOF
[Desktop Entry]
Name=CommieHeads
Exec=$HACKDIR/commieheads --root
TryExec=$HACKDIR/commieheads
Comment=Floating heads of communist and socialist figures quoting themselves.
StartupNotify=false
Terminal=false
Type=Application
Categories=Screensaver;
OnlyShowIn=MATE;
EOF

# xscreensaver: add to ~/.xscreensaver if that file exists and doesn't list it yet
if [ -f "$HOME/.xscreensaver" ] && ! grep -q '"CommieHeads"' "$HOME/.xscreensaver"; then
  sed -i '/^programs:/a\  "CommieHeads"  commieheads --root  \\n\\' "$HOME/.xscreensaver"
  echo "Added CommieHeads to ~/.xscreensaver"
fi

cat <<MSG
Installed. Try it:  commieheads -window

XFCE / MATE: open Settings -> Screensaver (reopen it if it was already open) and pick "CommieHeads".
xscreensaver: run xscreensaver-settings and pick "CommieHeads". If ~/.xscreensaver did not exist yet,
  open xscreensaver-settings once, close it, and run this script again.
GNOME on Wayland cannot run X11 screensavers.
MSG
