import json, sys, time, urllib.request, urllib.parse, re, html
UA = "CommieHeads/1.0 (https://github.com/pizzadance/commieheads)"
PAGES = {"marx":"Karl Marx","engels":"Friedrich Engels","lenin":"Vladimir Lenin","gramsci":"Antonio Gramsci","trotsky":"Leon Trotsky",
 "luxemburg":"Rosa Luxemburg","mao":"Mao Zedong","ho":"Ho Chi Minh","che":"Che Guevara","castro":"Fidel Castro"}
for k, t in PAGES.items():
    u = "https://en.wikiquote.org/w/api.php?" + urllib.parse.urlencode(dict(action="parse", page=t, prop="text", format="json", redirects=1))
    j = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}), timeout=60))
    txt = j["parse"]["text"]["*"]
    # mark disputed/misattributed sections so we can tell where a match lives
    txt = re.sub(r'<h2[^>]*>(.*?)</h2>', lambda m: "\n@@SECTION " + re.sub("<[^>]+>", "", m.group(1)) + "\n", txt, flags=re.S)
    txt = html.unescape(re.sub(r"<[^>]+>", " ", txt))
    open(f"raw/wq/{k}.txt", "w").write(txt); print(k, len(txt)); time.sleep(1)
