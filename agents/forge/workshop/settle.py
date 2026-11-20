"""Settle up a shared trip, flat or dinner: who pays whom, in as few payments as a simple rule finds (Forge, tick 62).

Each spend is: who paid, amount, and who it was for (empty = everyone). Money is kept in whole cents.
A split that doesn't divide evenly gives the leftover cents, one each, to the people it was for in
alphabetical order, so the total always matches. Then the person owed most is paid by the person who
owes most, repeatedly; that never takes more than (people - 1) payments.

Usage: python3 settle.py FILE   (lines: payer, amount, name name ...   # comments ok; 1,000 and $20 are fine)
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
    total = sum(bal.values())
    if total != 0:
        shown = money(total) if total >= 0 else "-" + money(-total)
        raise ValueError("balances must add up to zero (they add up to %s)" % shown)
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

LINE = re.compile(r"([^,]*),\s*[$€£₹]?\s*((?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]*)(?:\.[0-9]*)?)\s*(?:,(.*))?")
NUMBERISH = re.compile(r"[0-9.,]+")

def parse(text):
    """Lines "payer, amount, names". The amount may carry one leading $ € £ or ₹ and thousands
    commas ("1,000"). A name that is only digits is refused, so "1,00" can't invent a person "00"."""
    people, spends = [], []
    for num, line in enumerate(text.splitlines(), 1):
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        m = LINE.fullmatch(line)
        if "," not in line or not line.split(",", 1)[0].strip():
            raise ValueError("line %d: write it as: who paid, amount, who it was for: %s" % (num, line))
        if not m:
            raise ValueError("line %d: bad amount: %s (write 12.50 or 1,000)" % (num, line.split(",", 1)[1].strip()))
        payer, amount, rest = m.group(1).strip(), m.group(2), m.group(3) or ""
        try:
            amt = cents(amount.replace(",", ""))
        except ValueError:
            raise ValueError("line %d: bad amount: %s (write 12.50 or 1,000)" % (num, amount or line.split(",", 1)[1].strip()))
        who = rest.split()
        for n in [payer] + who:
            if NUMBERISH.fullmatch(n):
                raise ValueError("line %d: %s looks like part of a number, not a name (write amounts like 1000 or 1,000)" % (num, n))
        spends.append((payer, amt, who))
        for n in [payer] + who:
            if n not in people:
                people.append(n)
    return people, spends

def money(c):
    return "%d.%02d" % divmod(c, 100)

def main(argv):
    if len(argv) != 2:
        print(__doc__.strip().splitlines()[-1]); return 2
    try:
        people, spends = parse(open(argv[1], encoding="utf-8").read())
    except ValueError as e:
        print("settle: %s" % e, file=sys.stderr); return 1
    for a, b, x in settle(balances(people, spends)):
        print("%s pays %s %s" % (a, b, money(x)))
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
