#!/usr/bin/env python3
"""histcheck.py - Quill. Checks the dashboard's history keys against a second record.

fund_history comes from git history of world/state.json. This compares each tick's
balance with what that tick's chronicle says the fund holds ("The fund holds N" or
"fund holds N" in the chronicle file for that tick). It also checks that the
dashboard's relationships equal world/state.json's relationships exactly.
Standard library only, no network, writes nothing. Run from the repo root.
"""
import json, re, glob, os

d = json.load(open("docs/data/world.json"))
state = json.load(open("world/state.json"))
said = {}
for f in sorted(glob.glob("chronicle/[0-9][0-9][0-9][0-9]-*.md")):
    tick = int(os.path.basename(f)[:4])
    m = re.findall(r"[Ff]und (?:now )?holds (\d+)", open(f).read())
    if m:
        said[tick] = int(m[-1])  # last mention = the tick's closing figure
match = diff = nosay = 0
for row in d["fund_history"]:
    t, b = row["tick"], row["balance"]
    if t not in said:
        nosay += 1
        continue
    if said[t] == b:
        match += 1
    else:
        diff += 1
        print(f"tick {t}: dashboard {b}, chronicle says {said[t]}")
print(f"fund_history: MATCH {match}, DIFF {diff}, chronicle-silent {nosay}, rows {len(d['fund_history'])}")
r_ok = d["relationships"] == (state.get("relationships") or {})
print(f"relationships: {'MATCH' if r_ok else 'DIFF'} {len(d['relationships'])} pairs")
