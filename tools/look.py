import json, sys, re
d = json.load(open("raw/wqlist.json"))
fig = sys.argv[1]
for pat in sys.argv[2:]:
    hits = [i for i in d[fig] if re.search(pat, i["q"], re.I)]
    for i in hits[:2]:
        print(f"## [{i['sec']}]\n   Q: {i['q'][:400]}\n   S: {i['src'][:200]}")
    if not hits: print("## NONE:", pat)
