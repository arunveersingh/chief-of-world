#!/usr/bin/env python3
"""tworecords.py: for every grant in world/state.json, check that it also appears
in logs/events.jsonl (an event of type grant/grant_passed naming the proposal)
and in chronicle/NNNN-tick-N.md for its approved tick. Read-only. Wry, tick 34.
Exit 1 if any record is missing; print WARN when the event lacks the strict
fields type=grant_passed + proposal."""
import json, glob, sys
s = json.load(open("world/state.json"))
fund = [i for i in s["institutions"] if i["id"] == "voluntary_project_fund"][0]
events = [json.loads(l) for l in open("logs/events.jsonl") if l.strip()]
bad = 0
for g in fund["grants"]:
    p, t = g["proposal"], g["approved_tick"]
    evs = [e for e in events if e.get("type") in ("grant", "grant_passed")
           and (e.get("proposal") == p or p in e.get("summary", ""))]
    strict = any(e.get("type") == "grant_passed" and e.get("proposal") == p for e in evs)
    f = glob.glob(f"chronicle/{int(t):04d}-tick-{t}.md")
    chron = bool(f) and p in open(f[0]).read()
    line = f"{p} tick {t}: state yes, event {'yes' if evs else 'NO'}, chronicle {'yes' if chron else 'NO'}"
    if evs and not strict: line += "  WARN event not in strict form (type grant_passed + proposal field)"
    print(line)
    bad += (not evs) + (not chron)
print(f"{len(fund['grants'])} grants, {bad} missing records")
sys.exit(1 if bad else 0)
