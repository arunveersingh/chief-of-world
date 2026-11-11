# quotecheck.py (Ash, tick 26): read-only. For every "quoted" passage of 25+ chars in chronicle/, checks whether its words (punctuation ignored, ... splits allowed) appear in any agents/ or governance/ .md file. Misses include false alarms where narration sits between two quotes; read them by hand.
import re,glob,pathlib
tot=hit=0; misses=[]
norm=lambda s:re.sub(r"[^a-z0-9]+"," ",s.lower().replace("’","")).strip()
ALL=norm("".join(pathlib.Path(f).read_text() for f in glob.glob("agents/**/*.md",recursive=True)+glob.glob("governance/**/*.md",recursive=True)))
for ch in sorted(glob.glob("chronicle/00*.md")):
    n=int(pathlib.Path(ch).name[:4])
    for line in pathlib.Path(ch).read_text().splitlines():
        for q in re.findall(r'"([^"]{25,})"', line):
            tot+=1
            parts=[p for p in re.split(r"\.\.\.|…|\[[^\]]*\]",q) if len(norm(p))>12]
            if all(norm(p) in ALL for p in parts): hit+=1
            else: misses.append((n,q[:90]))
print(tot,hit,tot-hit)
for m in misses: print(m)
