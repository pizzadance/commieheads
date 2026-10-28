# Extract top-level sourced quotes (with their source sub-bullet) from Wikiquote HTML.
import json, re, sys, time, html, urllib.request, urllib.parse
from html.parser import HTMLParser
sys.path.insert(0, "tools"); from wq import PAGES, UA
class P(HTMLParser):
    def __init__(s): super().__init__(); s.depth=0; s.sec=""; s.items=[]; s.cur=None; s.inh=False; s.hbuf=""; s.skip=0
    def handle_starttag(s, t, a):
        if t in ("h2","h3"): s.inh=True; s.hbuf=""
        if t in ("style","sup"): s.skip+=1
        if t=="ul": s.depth+=1
        if t=="li":
            if s.depth==1: s.cur={"sec":s.sec,"q":"","src":""}; s.items.append(s.cur)
    def handle_endtag(s, t):
        if t in ("h2","h3"): s.inh=False; s.sec=(s.sec.split(" / ")[0] if t=="h3" else "")+(" / " if t=="h3" else "")+s.hbuf.strip()
        if t in ("style","sup"): s.skip-=1
        if t=="ul": s.depth-=1
    def handle_data(s, d):
        if s.skip: return
        if s.inh: s.hbuf+=d; return
        if s.cur is not None:
            if s.depth==1: s.cur["q"]+=d
            elif s.depth==2 and len(s.cur["src"])<300: s.cur["src"]+=d
out={}
for k,t in PAGES.items():
    u="https://en.wikiquote.org/w/api.php?"+urllib.parse.urlencode(dict(action="parse",page=t,prop="text",format="json",redirects=1))
    h=json.load(urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":UA}),timeout=60))["parse"]["text"]["*"]
    h=re.sub(r'<(div|table)[^>]*class="[^"]*(toc|navbox|mw-references)[^"]*".*?</\1>','',h,flags=re.S)
    p=P(); p.feed(h)
    items=[dict(sec=i["sec"],q=re.sub(r"\s+"," ",i["q"]).strip(),src=re.sub(r"\s+"," ",i["src"]).strip()) for i in p.items if i["q"].strip()]
    out[k]=items; time.sleep(1)
json.dump(out,open("raw/wqlist.json","w"),indent=1,ensure_ascii=False)
for k,v in out.items(): print(k,len(v))
