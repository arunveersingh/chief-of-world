#!/usr/bin/env python3
"""Print voluntary_project_fund status from world/state.json.
Each contributor's line shows their recorded contribution and their LAW-0007 §7 unspent share
(contribution x balance / total contributions, rounded down). Tick 54 fix: votes on grants are one per
contributor, never weighted by credits (LAW-0007 §3), so the old "spend-vote weight" column was wrong.
Usage: python3 agents/forge/workshop/fund_status.py [--repo PATH]   (exit 64 on a bad argument)"""
import json, pathlib, sys

def report(root):
    state = json.loads((pathlib.Path(root) / "world/state.json").read_text())
    out = []
    for inst in state.get("institutions", []):
        if inst["id"] != "voluntary_project_fund":
            continue
        bal, contrib = inst["balance"], inst["contributors"]
        total = sum(contrib.values())
        out.append(f"Tick {state['tick']} | fund balance: {bal} | votes: one per contributor, unweighted (LAW-0007 §3)")
        for who, amt in sorted(contrib.items(), key=lambda x: (-x[1], x[0])):
            share = amt * bal // total if total else 0
            out.append(f"  {who:<8} {amt:>3} contributed  unspent share {share} (§7)")
        out.append(f"  spending rules: {inst['spending_rules'] or 'NONE'}")
    return out

if __name__ == "__main__":
    a = sys.argv[1:]
    if a and (len(a) != 2 or a[0] != "--repo"):
        print("usage: fund_status.py [--repo PATH]", file=sys.stderr); sys.exit(64)
    print("\n".join(report(a[1] if a else pathlib.Path(__file__).resolve().parents[3])))
