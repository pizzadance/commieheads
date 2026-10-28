import json, os, re, sys, time, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from search import search, UA
from PIL import Image, ImageDraw
FIG = {
 "marx": ["Karl Marx photograph", "Karl Marx Mayall", "Karl Marx portrait"],
 "engels": ["Friedrich Engels photograph", "Friedrich Engels portrait"],
 "lenin": ["Vladimir Lenin photograph", "Lenin portrait 1920", "Lenin 1918 photo"],
 "gramsci": ["Antonio Gramsci photograph", "Gramsci 1922", "Gramsci 1915"],
 "trotsky": ["Leon Trotsky photograph", "Trotsky portrait", "Lev Trotsky photo"],
 "luxemburg": ["Rosa Luxemburg photograph", "Rosa Luxemburg portrait"],
 "mao": ["Mao Zedong photograph", "Mao Zedong portrait", "Mao Tse-tung photo"],
 "ho": ["Ho Chi Minh photograph", "Ho Chi Minh portrait", "Ho Chi Minh 1946"],
 "che": ["Che Guevara photograph", "Che Guevara portrait", "Ernesto Guevara photo"],
 "castro": ["Fidel Castro photograph", "Fidel Castro portrait", "Fidel Castro 1959"],
}
BAD = re.compile(r"graffiti|statue|monument|mural|stamp|grave|tomb|banknote|coin|poster|bust|memorial|sculpture|painting|drawing|caricature|cartoon|sign|book|street|museum|flag|\.webp|\.gif|\.svg|tattoo|figure|relief|plaque|wall|house|kim diaz|collier|fechin|russian school|vuillier", re.I)
FREE = re.compile(r"public domain|pd|cc0|cc by", re.I)
fig = sys.argv[1]
d = f"raw/cand/{fig}"; os.makedirs(d, exist_ok=True)
seen, items = set(), []
for q in FIG[fig]:
    for x in search(q, 40):
        if x["title"] in seen or BAD.search(x["title"]) or not FREE.search(x["lic"]) or min(x["w"], x["h"]) < 350 or not x["thumb"]:
            continue
        seen.add(x["title"]); items.append(x)
items = items[:30]
thumbs = []
for i, x in enumerate(items):
    p = f"{d}/{i:02d}.jpg"
    if not os.path.exists(p):
        try:
            data = urllib.request.urlopen(urllib.request.Request(x["thumb"], headers={"User-Agent": UA}), timeout=60).read()
            open(p, "wb").write(data)
        except Exception as e:
            print("fail", x["title"], e); continue
        time.sleep(0.3)
    x["file"] = p; thumbs.append(x)
json.dump(thumbs, open(f"{d}/index.json", "w"), indent=1)
S = 220; cols = 6; rows = (len(thumbs) + cols - 1) // cols
sheet = Image.new("RGB", (cols * S, rows * (S + 20)), "white"); dr = ImageDraw.Draw(sheet)
for i, x in enumerate(thumbs):
    im = Image.open(x["file"]).convert("RGB"); im.thumbnail((S, S))
    cx, cy = (i % cols) * S, (i // cols) * (S + 20)
    sheet.paste(im, (cx, cy)); dr.text((cx + 4, cy + S + 4), f'{i:02d} {x["title"][5:40]}', fill="black")
sheet.save(f"raw/sheet_{fig}.jpg", quality=80)
print(fig, len(thumbs))
