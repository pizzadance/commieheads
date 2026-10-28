# Cut a floating head: zoom to the face region, re-run Vision foreground mask on the crop,
# then keep hair/face/beard and fade out neck & shoulders.
import json, subprocess, sys
import numpy as np
from PIL import Image, ImageFilter
FACE_H = 210                       # normalized face-box height in output px
DOWN = {"marx": 0.9, "engels": 0.8, "ho": 0.35, "castro": 0.4, "che": 0.22}   # head bottom below chin, in face heights
NECK = {"marx": 0.56, "engels": 0.5, "che": 0.46, "castro": 0.44, "ho": 0.36}
# per-photo tweaks, keyed "<fig>_<source index>": shorter beards / clean-shaven young photos
OVERRIDE = {"engels_00": {"down": 0.3, "neck": 0.4}, "engels_01": {"down": 0.5, "neck": 0.36},
            "engels_02": {"neck": 0.42}, "marx_00": {"neck": 0.5}, "marx_01": {"neck": 0.46}, "marx_02": {"down": 0.45, "neck": 0.42},
            "ho_01": {"down": 0.1, "neck": 0.36}, "ho_02": {"down": 0.1, "neck": 0.36},
            "trotsky_01": {"down": 0.3, "neck": 0.34}}
def zoom(fig, i):
    """Crop source around detected face, upscale to >=1400px tall, re-segment. Returns (img, mask, face)."""
    js = json.loads(subprocess.check_output(["tools/segment", f"raw/src/{fig}/{i}.jpg", f"raw/mask/{fig}_{i}.png"]))
    x, y, w, h = js["faces"][0]
    img = Image.open(f"raw/src/{fig}/{i}.jpg").convert("RGB")
    box = (max(0, int(x - 1.6 * w)), max(0, int(y - 1.4 * h)), min(img.width, int(x + 2.6 * w)), min(img.height, int(y + 2.6 * h)))
    crop = img.crop(box)
    s = max(1.0, 1400 / crop.height)
    crop = crop.resize((round(crop.width * s), round(crop.height * s)), Image.LANCZOS)
    p = f"raw/zoom/{fig}_{i}.png"; crop.save(p)
    js2 = json.loads(subprocess.check_output(["tools/segment", p, f"raw/zoom/{fig}_{i}_mask.png"]))
    face = js2["faces"][0] if js2["faces"] else [(x - box[0]) * s, (y - box[1]) * s, w * s, h * s]
    mask = Image.open(f"raw/zoom/{fig}_{i}_mask.png").convert("L").resize(crop.size)
    return crop, np.asarray(mask, dtype=np.float32) / 255, face
def build(fig, i):
    img, mask, (x, y, w, h) = zoom(fig, i)
    W, H = img.size
    o = OVERRIDE.get(f"{fig}_{i}", {})
    down, up = o.get("down", DOWN.get(fig, 0.1)), o.get("up", 1.1)
    top, bottom = y - up * h, y + h + down * h
    # head horizontal extent from the mask at brow level (hair, no shoulders there)
    row = mask[int(y + 0.25 * h)] > 0.5
    xs = np.nonzero(row)[0]
    l, r = (xs.min(), xs.max()) if len(xs) else (x - 0.3 * w, x + 1.3 * w)
    l, r = min(l, x) - 0.08 * w, max(r, x + w) + 0.08 * w
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    # below the chin, narrow the allowed band toward the face centre to drop shoulders
    chin = y + h
    t = np.clip((yy - (y + 0.55 * h)) / (0.55 * h), 0, 1) ** 0.8   # narrows from mouth level to just below chin
    cx = x + w / 2
    nw = o.get("neck", NECK.get(fig, 0.36)) * w                     # neck/beard half-width
    L = np.where(l < cx - nw, l + (cx - nw - l) * t, l)
    R = np.where(r > cx + nw, r + (cx + nw - r) * t, r)
    # below the chin the band keeps narrowing (beards taper), so clothing beside the beard tip is dropped
    t2 = np.clip((yy - chin) / max(1.0, bottom - chin), 0, 1)
    below = yy > chin
    L = np.where(below, np.maximum(L, cx - nw * (1 - 0.55 * t2)), L)
    R = np.where(below, np.minimum(R, cx + nw * (1 - 0.55 * t2)), R)
    soft = 0.06 * w
    horiz = np.clip((xx - L) / soft + 0.5, 0, 1) * np.clip((R - xx) / soft + 0.5, 0, 1)
    fade_start = chin + (down - 0.35) * h if down > 0.3 else y + 0.8 * h   # clean-shaven: fade from the mouth down
    vert = np.where(yy < fade_start, 1.0, np.clip(1 - (yy - fade_start) / max(1.0, bottom - fade_start), 0, 1) ** 0.8)
    vert *= np.clip((yy - top) / soft, 0, 1)
    alpha = mask * horiz * vert
    a8 = Image.fromarray((alpha * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0))
    rgba = img.copy(); rgba.putalpha(a8)
    rgba = rgba.crop(a8.point(lambda v: 255 if v > 8 else 0).getbbox())
    s = FACE_H / h
    return rgba.resize((max(1, round(rgba.width * s)), max(1, round(rgba.height * s))), Image.LANCZOS)
if __name__ == "__main__":
    import os; os.makedirs("raw/zoom", exist_ok=True)
    only = sys.argv[1:]
    for fig in sorted(os.listdir("raw/src")):
        for i in ("00", "01", "02"):
            if only and f"{fig}_{int(i)+1}" not in only: continue
            build(fig, i).save(f"assets/heads/{fig}_{int(i) + 1}.png", optimize=True)
    print("done")
