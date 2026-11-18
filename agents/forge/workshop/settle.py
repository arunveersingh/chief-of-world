"""Settle up a shared trip, flat or dinner: who pays whom, in as few payments as a simple rule finds (Forge, tick 62).

Each spend is: who paid, amount, and who it was for (empty = everyone). Money is kept in whole cents.
A split that doesn't divide evenly gives the leftover cents, one each, to the people it was for in
alphabetical order, so the total always matches. Then the person owed most is paid by the person who
owes most, repeatedly; that never takes more than (people - 1) payments.

Usage: python3 settle.py FILE   (lines: payer, amount, name name ...   # comments ok)
"""
import re, sys

def cents(text):
    m = re.fullmatch(r"([0-9]*)(?:\.([0-9]{1,2}))?", text.strip())
    if not m or not (m.group(1) or m.group(2)):
        raise ValueError("bad amount: " + text.strip())
    return int(m.group(1) or 0) * 100 + int(((m.group(2) or "") + "00")[:2])

def balances(people, spends):
    """spends: (payer, cents, [names] or []) -> {name: cents}; positive means they are owed."""
    bal = {p: 0 for p in people}
    for payer, amt, who in spends:
        who = sorted(set(who)) if who else sorted(people)
        for n in [payer] + who:
            bal.setdefault(n, 0)
        bal[payer] += amt
        base, extra = divmod(amt, len(who))
        for i, n in enumerate(who):
            bal[n] -= base + (1 if i < extra else 0)
    return bal

def steps(people, spends):
    """The working, one row per spend: (payer, cents, [who, sorted], each, spare, for_everyone).
    The first `spare` names in `who` pay one cent more than `each`. Same split as balances()."""
    out = []
    for payer, amt, who in spends:
        names = sorted(set(who)) if who else sorted(people)
        each, spare = divmod(amt, len(names))
        out.append((payer, amt, names, each, spare, not who))
    return out

def settle(bal):
    """-> [(from, to, cents)]; greedy largest-owes pays largest-owed, ties by name."""
    bal = dict(bal)
    out = []
    while True:
        owed = sorted((n for n in bal if bal[n] > 0), key=lambda n: (-bal[n], n))
        owes = sorted((n for n in bal if bal[n] < 0), key=lambda n: (bal[n], n))
        if not owed or not owes:
            return out
        a, b = owes[0], owed[0]
        x = min(-bal[a], bal[b])
        out.append((a, b, x))
        bal[a] += x
        bal[b] -= x

def parse(text):
    people, spends = [], []
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 2 or not parts[0]:
            raise ValueError("need: payer, amount, names: " + line)
        who = parts[2].split() if len(parts) > 2 else []
        spends.append((parts[0], cents(parts[1]), who))
        for n in [parts[0]] + who:
            if n not in people:
                people.append(n)
    return people, spends

def money(c):
    return "%d.%02d" % divmod(c, 100)

def main(argv):
    if len(argv) != 2:
        print(__doc__.strip().splitlines()[-1]); return 2
    people, spends = parse(open(argv[1]).read())
    for a, b, x in settle(balances(people, spends)):
        print("%s pays %s %s" % (a, b, money(x)))
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
