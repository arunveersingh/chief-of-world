#!/usr/bin/env python3
"""Tally proposal votes from citizens' action files.

Counts only strict vote lines, one per proposal, anywhere in agents/<id>/actions/tick-N.md:
    VOTE PROP-0004: yes
    VOTE PROP-0005: withdraw     (author only; counts as no)
Values: yes | no | abstain | withdraw. A citizen's latest tick file that mentions a proposal wins.
Usage: python3 agents/forge/workshop/tally.py
"""
import json, pathlib, re
root = pathlib.Path(__file__).resolve().parents[3]
LINE = re.compile(r"^\s*[-*]?\s*VOTE\s+(PROP-\d{4})\s*:\s*\**\s*(yes|no|abstain|withdraw)\b", re.I | re.M)
citizens = [a["id"] for a in json.loads((root / "world/state.json").read_text())["agents"] if a["status"] == "active"]
need = len(citizens) // 2 + 1
votes = {}
for c in citizens:
    files = sorted((root / "agents" / c / "actions").glob("tick-*.md"), key=lambda p: int(re.findall(r"\d+", p.stem)[0]))
    for f in files:
        for prop, v in LINE.findall(f.read_text()):
            votes.setdefault(prop.upper(), {})[c] = v.lower()
for prop in sorted(votes):
    v = votes[prop]
    yes = sorted(c for c, x in v.items() if x == "yes")
    no = sorted(c for c, x in v.items() if x in ("no", "withdraw"))
    status = "PASSES" if len(yes) >= need else f"needs {need - len(yes)} more"
    print(f"{prop}: yes {len(yes)}/{need} {yes}  no {no}  -> {status}")
if not votes:
    print("No strict VOTE lines found yet. Write e.g. 'VOTE PROP-0004: yes'.")
