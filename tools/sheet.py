import sys, glob, os
from PIL import Image, ImageDraw
files = sorted(glob.glob(sys.argv[1] + "/*.jpg")); S = 260; cols = 6; rows = (len(files) + cols - 1) // cols
sheet = Image.new("RGB", (cols * S, rows * (S + 16)), "white"); dr = ImageDraw.Draw(sheet)
for i, f in enumerate(files):
    im = Image.open(f).convert("RGB"); im.thumbnail((S, S)); cx, cy = (i % cols) * S, (i // cols) * (S + 16)
    sheet.paste(im, (cx, cy)); dr.text((cx + 4, cy + S + 2), os.path.basename(f), fill="black")
sheet.save(sys.argv[2], quality=80)
