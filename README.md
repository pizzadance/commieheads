# CommieHeads screensaver (macOS + Debian/Linux)

A single floating head drifts across a `#992222` background, bounces off the edges and
says one of its quotes in a speech bubble. The bubble stays up for **2 seconds per word**,
then a different, randomly chosen head appears (never the same figure twice in a row).
Each figure has 3 photos and 10 quotes; photo and quote are both picked at random,
and a quote is never repeated back-to-back for the same figure.

Figures: Marx, Engels, Lenin, Gramsci, Trotsky, Luxemburg, Mao, Ho Chi Minh, Che Guevara, Castro.

## macOS
    ./macos/build.sh                       # -> dist/CommieHeads.saver (universal arm64 + x86_64)
Double-click `dist/CommieHeads.saver` (or copy it to `~/Library/Screen Savers/`), then pick
**CommieHeads** in System Settings -> Screen Saver.

## Debian / Linux (xscreensaver)
    sudo apt install xscreensaver python3-pygame
    tar xzf commieheads-linux.tar.gz && cd commieheads-linux && ./install.sh
`install.sh` prints the one line to add to `~/.xscreensaver`. To try it without xscreensaver:
`~/.local/bin/commieheads -window` (or no flag for fullscreen; any key quits).
Note: GNOME on Wayland does not run xscreensaver hacks — use an X11 session (or XFCE/MATE/LXDE etc.).

## Layout
- `assets/heads/<id>_{1,2,3}.png` — head cut-outs, all normalized to the same face height
- `assets/quotes.json` — figures, quotes and their sources (shared by both platforms)
- `macos/` — Objective-C `ScreenSaverView`; `linux/commieheads.py` — pygame port with identical behaviour
- `tools/` — pipeline used to build the assets (Commons download, macOS Vision segmentation, head cut)
- `CREDITS.md` — photo sources and licenses (several are CC BY / CC BY-SA and require attribution)

Quotes were checked against sourced (not "disputed"/"misattributed") entries on English Wikiquote
or against the primary texts on marxists.org.

## Downloads
Prebuilt `CommieHeads.saver.zip` (macOS) and `commieheads-linux.tar.gz` are attached to the GitHub Releases.
The `.saver` is ad-hoc signed, not notarized: on first use macOS may block it — right-click it and choose
**Open**, or allow it under System Settings -> Privacy & Security.

## Rebuilding the assets (optional, macOS only)
The `tools/` scripts download the source photos from Wikimedia Commons into `raw/`, segment them with
macOS Vision (`tools/segment.m`, compile with clang) and cut the heads (`tools/head.py`, needs Pillow + NumPy).

## License
Code: MIT (see `LICENSE`). Photos keep their original licenses — public domain, CC0, CC BY and CC BY-SA;
see `CREDITS.md`. Derived head images from CC BY-SA sources are shared under the same CC BY-SA license.
