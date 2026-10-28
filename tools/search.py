import json, sys, urllib.request, urllib.parse
UA = "CommieHeads/1.0 (https://github.com/pizzadance/commieheads)"
def api(params):
    params.update(format="json")
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return json.load(urllib.request.urlopen(req, timeout=30))
def search(q, n=20):
    r = api(dict(action="query", generator="search", gsrsearch=q + " filetype:bitmap", gsrnamespace=6, gsrlimit=n,
                 prop="imageinfo", iiprop="url|size|extmetadata", iiurlwidth=800))
    out = []
    for p in (r.get("query", {}).get("pages", {}) or {}).values():
        ii = p["imageinfo"][0]
        md = ii.get("extmetadata", {})
        out.append(dict(title=p["title"], w=ii["width"], h=ii["height"], thumb=ii.get("thumburl"), url=ii["url"],
                        lic=md.get("LicenseShortName", {}).get("value", "")))
    return out
if __name__ == "__main__":
    for x in search(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 20):
        print(f'{x["w"]}x{x["h"]}\t{x["lic"]}\t{x["title"]}')
