#!/usr/bin/env python3
"""CommieHeads — floating heads with speech bubbles (xscreensaver hack / standalone).

One head at a time drifts across a #992222 background and bounces off the edges.
Each head is on screen for 2 s per word of its quote, then a different (random) head appears.

Usage:
  commieheads.py                 fullscreen (any key / mouse click quits)
  commieheads.py -window         in a 1280x800 window
  commieheads.py -root           draw on the root window (xscreensaver)
  commieheads.py -window-id ID   draw into an existing X window (xscreensaver)
xscreensaver also passes $XSCREENSAVER_WINDOW, which is honoured automatically.
"""
import json, math, os, random, sys, time

FADE_IN, BUBBLE_POP, FADE_OUT, FLIP = 0.5, 0.35, 0.6, 0.3
HERE = os.path.dirname(os.path.realpath(__file__))
ASSETS = next((p for p in (os.environ.get("COMMIEHEADS_ASSETS"), os.path.join(HERE, "assets"),
                           os.path.join(HERE, "..", "assets"), "/usr/local/share/commieheads", "/usr/share/commieheads")
               if p and os.path.isfile(os.path.join(p, "quotes.json"))), None)


def parse_args(argv):
    opts = {"mode": "fullscreen", "window_id": None, "snapshot": None, "at": 6.0, "size": (1280, 800)}
    i = 0
    while i < len(argv):
        a = argv[i].lstrip("-")
        if a == "root":
            opts["mode"] = "root"
        elif a == "window-id" and i + 1 < len(argv):
            opts["mode"], opts["window_id"] = "embed", argv[i + 1]; i += 1
        elif a == "window":
            opts["mode"] = "window"
        elif a == "snapshot" and i + 2 < len(argv):   # testing: render offscreen, save a frame at a given second
            opts["snapshot"], opts["at"] = argv[i + 1], float(argv[i + 2]); i += 2
        elif a == "size" and i + 1 < len(argv):
            opts["size"] = tuple(int(v) for v in argv[i + 1].lower().split("x")); i += 1
        i += 1
    # xscreensaver draws on its own window and passes it in $XSCREENSAVER_WINDOW, even with -root
    if opts["mode"] in ("fullscreen", "root") and os.environ.get("XSCREENSAVER_WINDOW") and not opts["snapshot"]:
        opts["mode"], opts["window_id"] = "embed", os.environ["XSCREENSAVER_WINDOW"]
    return opts


def root_window_id():
    """Root window id of the default X screen (for -root)."""
    import ctypes, ctypes.util
    x11 = ctypes.cdll.LoadLibrary(ctypes.util.find_library("X11") or "libX11.so.6")
    x11.XOpenDisplay.restype = ctypes.c_void_p
    x11.XDefaultRootWindow.restype = ctypes.c_ulong
    x11.XDefaultRootWindow.argtypes = [ctypes.c_void_p]
    dpy = x11.XOpenDisplay(None)
    if not dpy:
        sys.exit("commieheads: cannot open X display")
    return x11.XDefaultRootWindow(dpy)


opts = parse_args(sys.argv[1:])
if opts["snapshot"]:
    os.environ["SDL_VIDEODRIVER"] = "dummy"
elif opts["mode"] in ("embed", "root"):
    wid = int(opts["window_id"], 0) if opts["mode"] == "embed" else root_window_id()
    os.environ["SDL_WINDOWID"] = str(wid)
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame  # noqa: E402  (must come after SDL_* environment variables are set)


def ease_out_back(t):
    c1 = 1.70158
    return 1 + (c1 + 1) * (t - 1) ** 3 + c1 * (t - 1) ** 2


def wrap(font, text, width):
    lines, cur = [], ""
    for word in text.split():
        trial = word if not cur else cur + " " + word
        if font.size(trial)[0] <= width or not cur:
            cur = trial
        else:
            lines.append(cur); cur = word
    if cur:
        lines.append(cur)
    return lines


class Saver:
    def __init__(self, surface):
        if not ASSETS:
            sys.exit("commieheads: assets (quotes.json + heads/) not found")
        cfg = json.load(open(os.path.join(ASSETS, "quotes.json"), encoding="utf-8"))
        self.figures = cfg["figures"]
        self.spw = float(cfg.get("secondsPerWord", 2))
        self.bg = pygame.Color(cfg.get("background", "#992222"))
        self.surface = surface
        self.W, self.H = surface.get_size()
        self.unit = self.H
        self.head_scale = self.unit * 0.2 / 210.0       # heads are normalized so the face is 210 px tall
        self.fs = max(9, int(self.unit * 0.03))
        self.qfont = pygame.font.SysFont("georgia,dejavuserif,liberationserif,freeserif,serif", self.fs)
        self.nfont = pygame.font.SysFont("avenirnext,dejavusans,liberationsans,freesans,sans", int(self.fs * 0.72), bold=True)
        self.sfont = pygame.font.SysFont("avenirnext,dejavusans,liberationsans,freesans,sans", int(self.fs * 0.58), italic=True)
        self.cache = {}
        self.last_quote = {}
        self.fig_index = -1
        self.head = None
        self.flip_start = None

    def image(self, name):
        if name not in self.cache:
            img = pygame.image.load(os.path.join(ASSETS, "heads", name + ".png")).convert_alpha()
            w, h = img.get_size()
            self.cache[name] = pygame.transform.smoothscale(img, (max(1, round(w * self.head_scale)), max(1, round(h * self.head_scale))))
        return self.cache[name]

    def next_head(self, now):
        idx = self.fig_index
        while idx == self.fig_index and len(self.figures) > 1:
            idx = random.randrange(len(self.figures))
        self.fig_index = idx
        fig = self.figures[idx]
        self.head = self.image(f"{fig['id']}_{random.randint(1, 3)}")
        quotes = fig["quotes"]
        q = self.last_quote.get(fig["id"], -1)
        while q == self.last_quote.get(fig["id"], -1) and len(quotes) > 1:
            q = random.randrange(len(quotes))
        self.last_quote[fig["id"]] = q
        self.quote, self.source, self.name = quotes[q]["text"], quotes[q]["source"], fig["name"]
        # the whole appearance (fades included) lasts exactly secondsPerWord x words;
        # a word is a token containing a letter or digit (a lone dash is not a word)
        words = sum(1 for w in self.quote.split() if any(c.isalnum() for c in w))
        self.hold = max(1.0, self.spw * words - (FADE_IN + BUBBLE_POP + FADE_OUT))
        hw, hh = self.head.get_size()
        self.x = random.uniform(0, max(0, self.W - hw))
        self.y = random.uniform(0, max(0, self.H - hh))
        angle = random.uniform(0.35, 1.2) + math.pi / 2 * random.randint(0, 3)   # avoid near-axis paths
        speed = self.unit * 0.07
        self.vx, self.vy = math.cos(angle) * speed, math.sin(angle) * speed
        self.bubble_right = self.x + hw / 2 < self.W / 2
        self.flip_start = None
        self.bubble = self.render_bubble()
        self.start = now

    def update(self, now, dt):
        if self.head is None or now - self.start > FADE_IN + BUBBLE_POP + self.hold + FADE_OUT:
            self.next_head(now)
        hw, hh = self.head.get_size()
        self.x += self.vx * dt; self.y += self.vy * dt
        if self.x < 0: self.x, self.vx = 0, abs(self.vx)
        if self.y < 0: self.y, self.vy = 0, abs(self.vy)
        if self.x + hw > self.W: self.x, self.vx = self.W - hw, -abs(self.vx)
        if self.y + hh > self.H: self.y, self.vy = self.H - hh, -abs(self.vy)
        # keep the bubble on the roomier side; hysteresis avoids flapping around the centre line
        cx, band = self.x + hw / 2, self.W * 0.08
        want = self.bubble_right
        if cx < self.W / 2 - band: want = True
        elif cx > self.W / 2 + band: want = False
        # never keep the bubble on a side where it no longer fits beside the head
        bw, gap, margin = self.bubble.get_width(), self.fs * 1.6, self.fs
        fits_right = self.x + hw + gap + bw <= self.W - margin
        fits_left = self.x - gap - bw >= margin
        if want and not fits_right and fits_left: want = False
        elif not want and not fits_left and fits_right: want = True
        if self.flip_start is None and want != self.bubble_right:
            self.flip_start, self.flip_target = now, want
        if self.flip_start is not None and now - self.flip_start >= FLIP / 2:
            self.bubble_right = self.flip_target
        if self.flip_start is not None and now - self.flip_start >= FLIP:
            self.flip_start = None

    def render_bubble(self):
        """Pre-render the bubble body (without tail) for the current quote."""
        fs = self.fs
        pad, spacing = int(fs * 0.9), int(fs * 0.6)
        max_text = int(min(self.W * 0.34, fs * 22))
        ink, muted = (33, 15, 15), (115, 77, 77)
        qlines = wrap(self.qfont, "“" + self.quote + "”", max_text)
        slines = wrap(self.sfont, self.source, max_text)
        lh = self.qfont.get_linesize() + int(fs * 0.15)
        rendered = [self.qfont.render(l, True, ink) for l in qlines]
        name = self.nfont.render("— " + self.name, True, ink)
        src = [self.sfont.render(l, True, muted) for l in slines]
        tw = max([r.get_width() for r in rendered + src] + [name.get_width()])
        th = lh * len(rendered) + spacing + name.get_height() + sum(s.get_height() for s in src)
        surf = pygame.Surface((tw + 2 * pad, th + 2 * pad), pygame.SRCALPHA)
        pygame.draw.rect(surf, (255, 251, 245), surf.get_rect(), border_radius=int(fs * 0.8))
        y = pad
        for r in rendered:
            surf.blit(r, (pad, y)); y += lh
        y += spacing
        surf.blit(name, (pad, y)); y += name.get_height()
        for s in src:
            surf.blit(s, (pad, y)); y += s.get_height()
        return surf

    def draw(self, now):
        self.surface.fill(self.bg)
        if self.head is None:
            return
        t, end = now - self.start, FADE_IN + BUBBLE_POP + self.hold
        fade_out = max(0.0, 1 - (t - end) / FADE_OUT) if t > end else 1.0
        head_alpha = min(1.0, t / FADE_IN) * fade_out
        head = self.head.copy()
        head.set_alpha(int(255 * head_alpha))
        self.surface.blit(head, (round(self.x), round(self.y)))

        pop = (t - FADE_IN) / BUBBLE_POP
        if pop <= 0:
            return
        scale = 1.0 if pop >= 1 else 0.6 + 0.4 * ease_out_back(pop)
        alpha = min(1.0, pop) * fade_out
        if self.flip_start is not None:
            alpha *= abs(1 - 2 * min(1.0, (now - self.flip_start) / FLIP))
        self.draw_bubble(alpha, scale)

    def draw_bubble(self, alpha, scale):
        fs, margin, gap = self.fs, self.fs, int(self.fs * 1.6)
        hw, hh = self.head.get_size()
        hx, hy = self.x, self.y
        bw, bh = self.bubble.get_size()
        bx = hx + hw + gap if self.bubble_right else hx - gap - bw
        bx = max(margin, min(self.W - margin - bw, bx))
        by = hy - bh * 0.25                                   # beside the upper part of the head
        by = max(margin, min(self.H - margin - bh, by))
        radius = fs * 0.8
        mouth = (hx + hw - hw * 0.28 if self.bubble_right else hx + hw * 0.28, hy + hh * 0.58)
        edge_x = bx if self.bubble_right else bx + bw
        base_y = max(by + radius + fs * 0.6, min(by + bh - radius - fs * 0.6, mouth[1] - fs))
        dx, dy = mouth[0] - edge_x, mouth[1] - base_y
        length = math.hypot(dx, dy) or 1.0
        reach = min(length * 0.7, fs * 2.6)
        tip = (edge_x + dx / length * reach, base_y + dy / length * reach)
        inset = radius if self.bubble_right else -radius

        # compose bubble + tail on one layer so they fade/scale together
        left, top = min(bx, tip[0]) - fs, min(by, tip[1]) - fs
        right, bottom = max(bx + bw, tip[0]) + fs, max(by + bh, tip[1]) + fs
        layer = pygame.Surface((int(right - left), int(bottom - top)), pygame.SRCALPHA)
        shadow = pygame.Surface(layer.get_size(), pygame.SRCALPHA)
        off = (-left, -top)
        tail = [(edge_x + inset + off[0], base_y - fs * 0.55 + off[1]), (tip[0] + off[0], tip[1] + off[1]),
                (edge_x + inset + off[0], base_y + fs * 0.55 + off[1])]
        sh = int(fs * 0.2)
        pygame.draw.rect(shadow, (50, 0, 0, 90), pygame.Rect(bx + off[0], by + off[1] + sh, bw, bh), border_radius=int(radius))
        pygame.draw.polygon(shadow, (50, 0, 0, 90), [(px, py + sh) for px, py in tail])
        layer.blit(shadow, (0, 0))
        pygame.draw.polygon(layer, (255, 251, 245), tail)
        layer.blit(self.bubble, (bx + off[0], by + off[1]))

        if scale != 1.0:                                      # pop scales out from the tail
            w, h = layer.get_size()
            sw, sh2 = max(1, int(w * scale)), max(1, int(h * scale))
            ax, ay = edge_x - left, base_y - top
            layer = pygame.transform.smoothscale(layer, (sw, sh2))
            left, top = edge_x - ax * scale, base_y - ay * scale
        layer.set_alpha(int(255 * alpha))
        self.surface.blit(layer, (round(left), round(top)))


def main():
    pygame.display.init()
    pygame.font.init()
    if opts["snapshot"]:
        screen = pygame.display.set_mode(opts["size"])
    elif opts["mode"] == "window":
        screen = pygame.display.set_mode(opts["size"])
        pygame.display.set_caption("CommieHeads")
    elif opts["mode"] in ("embed", "root"):
        screen = pygame.display.set_mode((0, 0))
    else:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.mouse.set_visible(False)
    saver = Saver(screen)
    clock = pygame.time.Clock()

    if opts["snapshot"]:                                     # deterministic offscreen render for testing
        t, dt = 0.0, 1 / 60
        while t < opts["at"]:
            saver.update(t, dt); t += dt
        saver.draw(t)
        pygame.image.save(screen, opts["snapshot"])
        return

    start = last = time.monotonic()
    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return
            if opts["mode"] in ("fullscreen", "window") and ev.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                return
        now = time.monotonic()
        saver.update(now - start, min(0.1, now - last))
        last = now
        saver.draw(now - start)
        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
