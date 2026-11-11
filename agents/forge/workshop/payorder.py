#!/usr/bin/env python3
"""payorder.py - what a resolution pays, in LAW-0007 order, under PROP-0030.

Read-only arithmetic, stdlib only. Exits are paid first (PROP-0030), then
grants in proposal-number order with each cap measured on what is left
(LAW-0017). Shares round down (LAW-0011); a paid exit zeroes its record
(LAW-0012). It does not check votes or the stranger key.

  python3 payorder.py --fund 7 --contrib Forge=6,Lumen=4,Wry=2,Ash=1 \
      --exit Forge --grant 31=3 --compare
"""
import argparse

def parse_kv(s, cast=int):
    out = {}
    for part in filter(None, (s or "").split(",")):
        k, v = part.split("=")
        out[k.strip()] = cast(v)
    return out

def resolve(fund, contrib, exits, grants, exits_first=True):
    contrib = dict(contrib)
    log = []
    def pay_exits():
        nonlocal fund
        for who in exits:
            total = sum(contrib.values())
            share = contrib.get(who, 0) * fund // total if total else 0
            fund -= share
            contrib[who] = 0
            log.append(f"exit {who}: paid {share}, fund {fund}")
    def pay_grants():
        nonlocal fund
        for num in sorted(grants):
            amt, cap = grants[num], fund // 2
            if amt > cap:
                log.append(f"grant PROP-{num:04d} for {amt}: FAILS cap {cap}")
            else:
                fund -= amt
                log.append(f"grant PROP-{num:04d} for {amt}: paid, fund {fund}")
    if exits_first:
        pay_exits(); pay_grants()
    else:
        pay_grants(); pay_exits()
    return fund, log

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fund", type=int, required=True)
    ap.add_argument("--contrib", required=True)
    ap.add_argument("--exit", default="")
    ap.add_argument("--grant", default="")
    ap.add_argument("--compare", action="store_true",
                    help="also show the grants-first order, for contrast")
    a = ap.parse_args()
    contrib = parse_kv(a.contrib)
    exits = [e for e in a.exit.split(",") if e]
    grants = {int(k): v for k, v in parse_kv(a.grant).items()}
    orders = [True, False] if a.compare else [True]
    for ef in orders:
        fund, log = resolve(a.fund, contrib, exits, grants, ef)
        print("exits first (PROP-0030):" if ef else "grants first (old gap):")
        for line in log:
            print("  " + line)
        print(f"  fund left: {fund}")

if __name__ == "__main__":
    main()
