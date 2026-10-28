import re, sys
fig, pat = sys.argv[1], sys.argv[2]
txt = re.sub(r"\s+", " ", open(f"raw/wq/{fig}.txt").read())
for m in list(re.finditer(pat, txt, re.I))[:int(sys.argv[3]) if len(sys.argv) > 3 else 2]:
    sec = re.findall(r"@@SECTION ([^@]*?) ", txt[:m.start()])
    print(f"[{sec[-1] if sec else '?'}] ...{txt[max(0,m.start()-250):m.end()+300]}...\n")
