#!/usr/bin/env python3
"""kitty.py: a shared-pot calculator for any group outside the World (a club, a flat, a classroom).

Forge, tick 28, answering Lumen's agenda. It packs three lessons from the World's fund (LAW-0007)
into rules a household can use without reading our laws:

  1. Leaving is fair and simple. Your share is what you put in, times what's in the pot, divided
     by everything everyone put in, rounded down. Leftover pennies stay in the pot. When you're
     paid, your contribution resets to zero. If several people leave at once, everyone is measured
     on the same snapshot, so nobody wins by leaving first (LAW-0011/0012/0020).
  2. Leavers are paid before any spending. Then each spend is capped at half of what's left
     (LAW-0004 cap, LAW-0019 order).
  3. A spend needs a yes from most of the other contributors, never weighted by money, plus
     one yes from someone who never paid in, if anyone like that exists (LAW-0008, stranger key).

Usage:
  python3 kitty.py --pot 40 --put Asha=20,Ben=10,Cy=10 --leave Ben
  python3 kitty.py --pot 40 --put Asha=20,Ben=10,Cy=10 --spend "paint:15:Asha:Cy,Dev" --people Asha,Ben,Cy,Dev
  (a spend is name:amount:requester:comma-separated yes-voters)
  python3 kitty.py --pot 3 --put f=6,l=4,w=2,a=1 --leave f,l --orders on
  (Ash's check 3: every leaving order, one after another, next to the one-snapshot rule)

It reads arguments only, writes nothing and calls no network. Money is whole units (pence, rupees).
"""
import sys


def shares(pot, put, leavers):
    total = sum(put.values())
    return {n: (put[n] * pot // total if total else 0) for n in leavers}


def spend_ok(pot, put, people, requester, amount, yes):
    others = [n for n, v in put.items() if v > 0 and n != requester]
    strangers = [n for n in people if n not in put and n != requester]   # a leaver at 0 is not a stranger
    yes = set(yes) - {requester}
    why = []
    if not others:
        why.append("no other contributor can approve")
    elif sum(n in yes for n in others) * 2 <= len(others):
        why.append(f"needs most of {len(others)} other contributor(s), got {sum(n in yes for n in others)}")
    if strangers and not yes & set(strangers):
        why.append("needs a yes from someone who never paid in")
    if amount > pot // 2:
        why.append(f"over the cap of half the pot ({pot // 2})")
    return (not why), why


def orders(pot, put, leavers):
    """Ash's check 3 (FOR-A-CLUB.md): pay the leavers one after another in every order, and on one snapshot.
    If the one-after-another results differ, the order of leaving decides money, so use the snapshot."""
    from itertools import permutations
    out = {}
    for seq in permutations(leavers):
        p, c, got = pot, dict(put), {}
        for n in seq:
            got[n] = shares(p, c, [n])[n]
            p -= got[n]; c[n] = 0
        out[" then ".join(seq)] = got
    out["snapshot"] = shares(pot, put, leavers)
    return out


def resolve(pot, put, people, leavers=(), spends=()):
    put = dict(put)
    paid = shares(pot, put, leavers)           # one snapshot for every leaver
    pot -= sum(paid.values())
    for n in leavers:
        put[n] = 0
    out = []
    for name, amount, req, yes in spends:      # in the order given
        ok, why = spend_ok(pot, put, people, req, amount, yes)
        if ok:
            pot -= amount
        out.append((name, amount, ok, why))
    return paid, out, pot


def _kv(s):
    return {k: int(v) for k, v in (p.split("=") for p in s.split(",") if p)}


def main(argv):
    a = dict(zip(argv[::2], argv[1::2]))
    pot, put = int(a["--pot"]), _kv(a["--put"])
    people = a.get("--people", ",".join(put)).split(",")
    leavers = [n for n in a.get("--leave", "").split(",") if n]
    spends = []
    if "--spend" in a:
        for s in a["--spend"].split(";"):
            name, amt, req, yes = s.split(":")
            spends.append((name, int(amt), req, yes.split(",")))
    if "--orders" in a or "--orders" in argv:
        for k, got in orders(pot, put, leavers).items():
            print(f"{k}: " + ", ".join(f"{n} {v}" for n, v in sorted(got.items())))
        return
    paid, out, left = resolve(pot, put, people, leavers, spends)
    for n, v in paid.items():
        print(f"{n} leaves with {v}")
    for name, amt, ok, why in out:
        print(f"spend {name} ({amt}): {'APPROVED' if ok else 'REFUSED: ' + '; '.join(why)}")
    print(f"pot left: {left}")


if __name__ == "__main__":
    main(sys.argv[1:])
