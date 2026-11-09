#!/usr/bin/env python3
"""Print voluntary_project_fund status from world/state.json. Usage: python3 agents/forge/workshop/fund_status.py"""
import json, pathlib
root = pathlib.Path(__file__).resolve().parents[3]
state = json.loads((root / "world/state.json").read_text())
for inst in state.get("institutions", []):
    if inst["id"] != "voluntary_project_fund":
        continue
    total = sum(inst["contributors"].values()) or 1
    print(f"Tick {state['tick']} | fund balance: {inst['balance']}")
    for who, amt in sorted(inst["contributors"].items(), key=lambda x: -x[1]):
        print(f"  {who:<8} {amt:>3} credits  ({amt/total:.0%} spend-vote weight)")
    print(f"  spending rules: {inst['spending_rules'] or 'NONE (see PROP-0001)'}")
