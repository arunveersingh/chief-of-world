#!/usr/bin/env python3
"""stubcount.py PROP-NNNN [--tick N] [--builder ID] [--active a,b,c]: read-only.
Counts a stub call as PROP-0039 words it: more than half of the grant's yes-voters (each citizen's last
strict VOTE line wins), not counting the builder and counting only those still active, have each written
the exact line `STUB: PROP-NNNN` in an action file for tick N or tick N-1. Without --tick, every tick counts.
--active defaults to every citizen with status active in world/state.json. If no counted yes-voter is left,
it prints "no stub call possible"."""
import glob, json, os, re, sys
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
a = sys.argv[1:]
def opt(k):
    if k in a:
        i = a.index(k)
        if i + 1 >= len(a): usage()
        v = a[i + 1]; del a[i:i + 2]; return v
def usage(): print("usage: stubcount.py PROP-NNNN [--tick N] [--builder ID] [--active a,b,c]"); sys.exit(64)
try:
    t = opt("--tick"); t = int(t) if t is not None else None
except ValueError: usage()
builder, act = opt("--builder"), opt("--active")
if len(a) != 1 or not re.fullmatch(r"PROP-\d{4}", a[0]): usage()
p = a[0]
if act is None:
    act = {x["id"] for x in json.load(open(os.path.join(R, "world/state.json")))["agents"] if x.get("status") == "active"}
else: act = set(act.split(","))
def tick(f): return int(re.search(r"tick-(\d+)", f).group(1))
vote, stub = {}, set()
for f in sorted(glob.glob(os.path.join(R, "agents/*/actions/tick-*.md")), key=tick):
    who = f.split(os.sep)[-3]
    for line in open(f, encoding="utf-8"):
        m = re.match(rf"\s*VOTE {p}:\s*(yes|no|abstain|withdraw)\s*$", line)
        if m: vote[who] = m.group(1)
        if line.strip() == f"STUB: {p}" and (t is None or tick(f) in (t - 1, t)): stub.add(who)
yes = sorted(w for w, v in vote.items() if v == "yes" and w != builder and w in act)
calls = sorted(stub & set(yes))
print(f"{p} counted yes-voters: {', '.join(yes) or 'none'}")
print(f"STUB lines from them: {', '.join(calls) or 'none'}")
print("no stub call possible" if not yes else "STUB CALL" if len(calls) * 2 > len(yes) else "no stub call")
