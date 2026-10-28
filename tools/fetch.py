# usage: fetch.py outdir width "File:A" "File:B" ...  -> outdir/<n>.jpg + meta.json
import json, os, sys, time, urllib.request, urllib.parse
sys.path.insert(0, os.path.dirname(__file__))
from search import api, UA
out, width, titles = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
os.makedirs(out, exist_ok=True)
meta = json.load(open(f"{out}/meta.json")) if os.path.exists(f"{out}/meta.json") else {}
for t in titles:
    r = api(dict(action="query", titles=t, prop="imageinfo", iiprop="url|extmetadata", iiurlwidth=width))
    p = next(iter(r["query"]["pages"].values()))
    ii = p["imageinfo"][0]; md = ii.get("extmetadata", {})
    name = f"{len(meta):02d}" if t not in meta else meta[t]["name"]
    src = ii.get("thumburl") or ii["url"]
    for attempt in range(5):
        try:
            data = urllib.request.urlopen(urllib.request.Request(src, headers={"User-Agent": UA}), timeout=60).read(); break
        except Exception as e:
            print("retry", t, e); time.sleep(5 * (attempt + 1))
    open(f"{out}/{name}.jpg", "wb").write(data)
    meta[t] = dict(name=name, page=ii["descriptionurl"], file=ii["url"], license=md.get("LicenseShortName", {}).get("value", ""),
                   artist=md.get("Artist", {}).get("value", ""))
    print(name, t); time.sleep(1.5)
json.dump(meta, open(f"{out}/meta.json", "w"), indent=1)
