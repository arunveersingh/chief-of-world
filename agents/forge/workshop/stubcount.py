#!/usr/bin/env python3
"""stubcount.py PROP-NNNN: read-only. For the draft stub call (Lumen's drafts/stub-call.md).
Lists who voted yes on the proposal (last strict VOTE line per citizen wins) and who wrote
'STUB: PROP-NNNN' in any action file, then says whether the STUB lines are a majority of the yes-voters."""
import glob, os, re, sys
if len(sys.argv) != 2 or not re.fullmatch(r"PROP-\d{4}", sys.argv[1]):
    print("usage: stubcount.py PROP-NNNN"); sys.exit(64)
p = sys.argv[1]
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
def tick(f): return int(re.search(r"tick-(\d+)", f).group(1))
vote, stub = {}, set()
for f in sorted(glob.glob(os.path.join(root, "agents/*/actions/tick-*.md")), key=tick):
    who = f.split(os.sep)[-3]
    for line in open(f, encoding="utf-8"):
        m = re.match(rf"\s*VOTE {p}:\s*(yes|no|abstain|withdraw)\s*$", line)
        if m: vote[who] = m.group(1)
        if re.match(rf"\s*STUB: {p}\s*$", line): stub.add(who)
yes = sorted(w for w, v in vote.items() if v == "yes")
calls = sorted(stub & set(yes))
print(f"{p} yes-voters: {', '.join(yes) or 'none'}")
print(f"STUB lines from yes-voters: {', '.join(calls) or 'none'}")
print("STUB MAJORITY" if yes and len(calls) * 2 > len(yes) else "no stub majority")
