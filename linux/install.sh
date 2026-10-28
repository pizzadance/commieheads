#!/bin/sh
# Install CommieHeads for the current user (Debian / any X11 desktop with xscreensaver).
#   sudo apt install xscreensaver python3-pygame
#   ./install.sh
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
SRC_ASSETS="$HERE/assets"; [ -d "$SRC_ASSETS" ] || SRC_ASSETS="$HERE/../assets"
DEST="$HOME/.local/share/commieheads"
mkdir -p "$DEST" "$HOME/.local/bin"
cp "$HERE/commieheads.py" "$DEST/"
rm -rf "$DEST/assets"; cp -R "$SRC_ASSETS" "$DEST/assets"
chmod +x "$DEST/commieheads.py"
ln -sf "$DEST/commieheads.py" "$HOME/.local/bin/commieheads"
python3 -c "import pygame" 2>/dev/null || echo "WARNING: pygame missing -> sudo apt install python3-pygame"
cat <<MSG
Installed to $DEST  (command: ~/.local/bin/commieheads)

Try it now:   ~/.local/bin/commieheads -window

Add it to xscreensaver: run xscreensaver-settings once (creates ~/.xscreensaver), close it,
then in ~/.xscreensaver add this line inside the "programs:" list (keep the trailing \\n\\):

  "CommieHeads"  $HOME/.local/bin/commieheads -root  \\n\\

Re-open xscreensaver-settings, choose "CommieHeads" (mode: Only One Screen Saver).
MSG
