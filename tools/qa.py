import glob, os
from PIL import Image, ImageDraw
files = sorted(glob.glob("assets/heads/*.png")); cols = 6; S = 300
rows = (len(files) + cols - 1) // cols
sheet = Image.new("RGB", (cols * S, rows * (S + 18)), "#992222"); dr = ImageDraw.Draw(sheet)
for k, f in enumerate(files):
    im = Image.open(f); sc = min(1, (S - 10) / max(im.size)); im = im.resize((int(im.width * sc), int(im.height * sc)))
    cx, cy = (k % cols) * S, (k // cols) * (S + 18)
    sheet.paste(im, (cx + (S - im.width) // 2, cy + (S - im.height) // 2), im)
    dr.text((cx + 4, cy + S + 2), f"{os.path.basename(f)} {Image.open(f).size}", fill="white")
sheet.save("raw/qa.jpg", quality=85)
