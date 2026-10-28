import json, re, sys
def words(s): return re.findall(r"[a-z0-9]+", s.lower().replace("’", "'"))
draft = json.load(open(sys.argv[1]))
for fig, qs in draft.items():
    txt = open(f"raw/wq/{fig}.txt").read()
    secs = [(m.start(), m.group(1)) for m in re.finditer(r"@@SECTION (.*)", txt)]
    W = words(txt); pos = []
    # map word index -> char offset approx via re
    offs = [m.start() for m in re.finditer(r"[a-z0-9]+", txt.lower().replace("’", "'"))]
    s = " ".join(W)
    print(f"=== {fig}")
    for q in qs:
        qw = words(q); best = (0, None)
        for n in range(len(qw), 2, -1):        # longest contiguous run present
            found = False
            for i in range(0, len(qw) - n + 1):
                k = s.find(" " + " ".join(qw[i:i + n]) + " ")
                if k >= 0:
                    wi = s[:k].count(" ") + 1; ch = offs[min(wi, len(offs) - 1)]
                    sec = [t for o, t in secs if o < ch]; best = (n, sec[-1].strip() if sec else "?"); found = True; break
            if found: break
        print(f"{best[0]:>3}/{len(qw):<3} [{best[1]}]  {q[:90]}")
