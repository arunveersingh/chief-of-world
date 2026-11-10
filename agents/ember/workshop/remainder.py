#!/usr/bin/env python3
"""Ember's watch: the unclaimed remainder of the voluntary project fund.

Unfunded. Reads world/state.json only; writes nothing.
Shares follow LAW-0011: contribution * balance // total contributions.
A contributor at 0 (LAW-0012) is still listed but holds no share.
Prints each share, the remainder nobody owns, and two warnings:
  - REMAINDER AT CAP: the remainder alone reaches the grant cap (half the fund, rounded down)
  - EMPTY ROOM: every recorded contribution is zero, so no one can claim the balance.
    Since LAW-0014 (tick 15) this means SHUT, not unguarded: no grant passes until someone deposits.
"""
import json, sys, pathlib

def watch(state):
    fund = next(i for i in state["institutions"] if i["id"] == "voluntary_project_fund")
    bal = fund["balance"]
    contrib = fund.get("contributors", {})
    total = sum(contrib.values())
    shares = {k: (v * bal // total if total else 0) for k, v in contrib.items()}
    remainder = bal - sum(shares.values())
    cap = bal // 2
    return bal, total, shares, remainder, cap

def main():
    root = pathlib.Path(__file__).resolve().parents[3]
    path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else root / "world" / "state.json"
    bal, total, shares, remainder, cap = watch(json.loads(path.read_text()))
    print(f"fund {bal}, recorded contributions {total}, cap {cap}")
    for k, v in sorted(shares.items(), key=lambda kv: -kv[1]):
        print(f"  {k}: {v}")
    print(f"unclaimed remainder: {remainder}")
    if total == 0 and bal > 0:
        print("WARNING EMPTY ROOM: the balance has no contributors to claim it; under LAW-0014 the fund is SHUT until someone deposits")
    elif cap and remainder >= cap:
        print("WARNING REMAINDER AT CAP: the unowned part alone could fund a full grant")

if __name__ == "__main__":
    main()
