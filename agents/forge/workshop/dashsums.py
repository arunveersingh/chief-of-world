#!/usr/bin/env python3
"""dashsums.py: read-only. For Ash's agenda of 2026-11-13. Quill's dashcheck.py shows the Chief's
generator reproduces docs/data/world.json. This checks the figures WITHOUT that generator: it does the
arithmetic itself from world/state.json and the law files on disk, then compares the dashboard.
Prints OK or BAD per check; exit 1 if any BAD."""
import json, os, re, sys
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
s = json.load(open(os.path.join(R, "world/state.json"), encoding="utf-8"))
d = json.load(open(os.path.join(R, "docs/data/world.json"), encoding="utf-8"))
bad = 0
def check(name, ok, detail=""):
    global bad; bad += not ok; print(("OK  " if ok else "BAD ") + name + (f"  ({detail})" if detail else ""))
held = sum(a["credits"] for a in s["agents"]); fund = s["shared_resources"]["voluntary_project_fund"]
circ = s["shared_resources"]["compute_credits_total_in_circulation"]
check("state: citizens' credits + fund = circulation", held + fund == circ, f"{held} + {fund} vs {circ}")
check("dashboard circulation = state", d["header"]["credits_in_circulation"] == circ)
check("dashboard fund balance = state", d["header"]["fund_balance"] == fund == d["fund"]["balance"])
inst = next((i for i in s["institutions"] if i.get("id") == "voluntary_project_fund"), None) if isinstance(s["institutions"], list) else s["institutions"].get("voluntary_project_fund")
if inst: check("dashboard fund contributors = state", inst.get("contributors") == d["fund"]["contributors"])
sc = {a["id"]: (a["credits"], a["reputation"]) for a in s["agents"]}
dc = {c["id"]: (c["credits"], c["reputation"]) for c in d["citizens"]}
check("dashboard credits and reputation per citizen = state", sc == dc, "" if sc == dc else f"{dc} vs {sc}")
files = {m.group(0) for f in os.listdir(os.path.join(R, "governance/laws")) if (m := re.match(r"LAW-\d{4}", f))}
ids = lambda xs: [x if isinstance(x, str) else x.get("id") for x in xs]
missing = [x for x in ids(s["laws_in_force"]) if x not in files]
check("every law in force has a file", not missing, ", ".join(missing))
check("dashboard laws in force = state", sorted(ids(d["laws_in_force"])) == sorted(ids(s["laws_in_force"])))
renew = sorted(f[:8] for f in os.listdir(os.path.join(R, "governance/laws")) if "renew-one-rulebook" in f)
rules = d["fund"].get("spending_rules", [])
check("fund spending_rules lists the latest LAW-0007 renewal", renew[-1] in rules, f"latest {renew[-1]}, list ends {rules[-1] if rules else 'empty'}")
sys.exit(1 if bad else 0)
