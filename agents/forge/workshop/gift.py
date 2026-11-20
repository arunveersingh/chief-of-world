#!/usr/bin/env python3
"""Chip in for a shared gift (a farewell, a wedding, a teacher's gift) so
each person knows what they pay, with caps respected and nothing guessed.
Offline, no network.

Usage: gift.py FILE
  FILE  the price, then one person per line (fixed, a cap, or even):
          gift, 6,000
          Ana, 1,000
          Ben, up to 800
          Cy
          Dee, even
          paid, Ana
        "gift" (or "cost") is the price, written once. A name and an amount
        is a fixed share: they pay exactly that. "up to" is a cap: they pay
        an even share of what's left, but never more than this. A bare name,
        or a name and "even", splits what's left evenly. Fixed amounts come
        off first; what's left is split among everyone with a cap or an even
        share. If someone's even share would go over their cap, they pay the
        cap and the rest is split again among the others. Spare cents go one
        each to the first people in the list who aren't capped. The optional
        "paid, name" line is the one person who paid for the gift.
It prints what each person pays and one line the group can copy.

Needs rent.py beside it (it reads amounts the same way Fair rent does).
"""
import re
import sys

from rent import hundredths

LIMIT = 10 ** 13  # 100 billion in cents; the page counts the same way up to here
UPTO = re.compile(r"up[ \t]+to\b[ \t]*", re.I)
GIFT = re.compile(r"(gift|cost)[ \t]*,", re.I)
PAID = re.compile(r"paid[ \t]*,", re.I)


def amount(text, what):
    c = hundredths(text, what)
    if c > LIMIT:
        raise ValueError("bad %s: %s (that's more than this counts; the most is 100,000,000,000)" % (what, text.strip()))
    return c


def money(c):
    whole = "{:,}".format(c // 100)
    return whole if c % 100 == 0 else "%s.%02d" % (whole, c % 100)


def _amt(text, no, line, how):
    try:
        return amount(text, "amount")
    except ValueError as e:
        if "that's more than this counts" in str(e):
            raise ValueError("line %d: %s" % (no, e))
        raise ValueError(how % (no, line))


def even(amt, n):
    each, spare = divmod(amt, n)
    return [each + (1 if i < spare else 0) for i in range(n)]


def parse(text):
    """-> (gift cents or None, people [(name, kind, cents or None, line no, line)], paid or None).
    kind is 'fixed', 'cap', or 'even'."""
    gift, people, paid, seen = None, [], None, set()
    for no, raw in enumerate(text.splitlines(), 1):
        line = raw.replace("\ufeff", "").strip()
        if not line:
            continue
        if "%" in line:
            raise ValueError("line %d: write the exact amount, not %% (a %% of the gift and a %% of what's left are different things): %s" % (no, line))
        if GIFT.match(line):
            if gift is not None:
                raise ValueError("line %d: the gift is written twice: %s" % (no, line))
            gift = _amt(line.partition(",")[2], no, line, "line %d: write it as: gift, amount: %s")
            if gift == 0:
                raise ValueError("line %d: a gift of 0 isn't a gift: %s" % (no, line))
            continue
        if PAID.match(line):
            if paid is not None:
                raise ValueError("line %d: who paid is written twice: %s" % (no, line))
            who = line.partition(",")[2].strip()
            if not who or not any(ch.isalpha() for ch in who):
                raise ValueError("line %d: write it as: paid, name: %s" % (no, line))
            paid = who
            continue
        name, comma, rest = line.partition(",")
        name, rest = name.strip(), rest.strip()
        if not any(ch.isalpha() for ch in name) or (not comma and UPTO.match(name)):
            raise ValueError("line %d: a line with an amount needs a name: %s" % (no, line))
        if not comma:
            kind, cents = "even", None
        elif re.fullmatch(r"even", rest, re.I):
            kind, cents = "even", None
        elif UPTO.match(rest):
            after = UPTO.sub("", rest, count=1).strip()
            if not after:
                raise ValueError("line %d: write how much they will go up to, like: Ben, up to 800: %s" % (no, line))
            cents = _amt(after, no, line, "line %d: write how much they will go up to, like: Ben, up to 800: %s")
            if cents == 0:
                raise ValueError("line %d: up to 0 means they're not chipping in; leave them off: %s" % (no, line))
            kind = "cap"
        else:
            cents = _amt(rest, no, line, "line %d: write it as: name, amount (or name, up to amount, or a bare name): %s")
            if cents == 0:
                raise ValueError("line %d: a fixed amount of 0 isn't chipping in; leave them off: %s" % (no, line))
            kind = "fixed"
        if name.lower() in seen:
            raise ValueError("line %d: %s is listed twice: %s" % (no, name, line))
        seen.add(name.lower())
        people.append((name, kind, cents, no, line))
    return gift, people, paid


def share(gift, people, paid=None):
    """-> ([(name, kind, cents or None, pays)], who paid or None); refuses what doesn't add up."""
    if gift is None:
        raise ValueError("the gift price is missing (write it as: gift, amount)")
    if not people:
        raise ValueError("nobody listed (write who is chipping in, like Ana, 1,000, or a bare name)")
    names = {n.lower(): n for n, _, _, _, _ in people}
    if paid is not None:
        if paid.lower() not in names:
            raise ValueError("who is %s? nobody by that name is chipping in" % paid)
        paid = names[paid.lower()]
    fixed_sum = sum(c for _, kind, c, _, _ in people if kind == "fixed")
    if fixed_sum > gift:
        raise ValueError("the fixed amounts add up to %s, which is %s more than the %s gift"
                         % (money(fixed_sum), money(fixed_sum - gift), money(gift)))
    left = gift - fixed_sum
    pays = [c if kind == "fixed" else 0 for _, kind, c, _, _ in people]
    others = [i for i, p in enumerate(people) if p[1] != "fixed"]
    if not others:
        if left > 0:
            raise ValueError("the fixed amounts add up to %s, which is %s short of the %s gift (add someone to split what's left, or raise a fixed amount)"
                             % (money(fixed_sum), money(left), money(gift)))
    else:
        remaining = list(others)
        while remaining:
            would = even(left, len(remaining))
            over = [i for k, i in enumerate(remaining)
                    if people[i][1] == "cap" and would[k] > people[i][2]]
            if not over:
                for k, i in enumerate(remaining):
                    pays[i] = would[k]
                left = 0
                break
            for i in over:
                pays[i] = people[i][2]
                left -= people[i][2]
            remaining = [i for i in remaining if i not in over]
        if left > 0:
            pledged = fixed_sum + sum(people[i][2] for i in others if people[i][1] == "cap")
            raise ValueError("the caps can't reach the gift: all together (with any fixed amounts) they add up to %s, which is %s short of %s (raise a cap, or add someone)"
                             % (money(pledged), money(gift - pledged), money(gift)))
    rows = [(n, kind, c, pays[i]) for i, (n, kind, c, _, _) in enumerate(people)]
    return rows, paid


def row(name, kind, amt, pays, paid_name=None):
    if kind == "fixed":
        head = "fixed, pays %s" % money(pays)
    elif kind == "cap":
        head = "up to %s, pays %s" % (money(amt), money(pays))
        if pays == amt:
            head += " (capped)"
    else:
        head = "even, pays %s" % money(pays)
    if paid_name is not None and name == paid_name:
        head += " (paid the gift)"
    return "%s: %s" % (name, head)


def summary(rows, paid_name=None):
    total = sum(r[3] for r in rows)
    out = "Gift %s. %s." % (money(total), ", ".join("%s %s" % (r[0], money(r[3])) for r in rows))
    if any(r[1] != "fixed" for r in rows) and all(r[3] == 0 for r in rows if r[1] != "fixed"):
        return out + " The fixed amounts cover the gift, so everyone else pays 0."
    if paid_name is None:
        return out
    owes = ["%s %s" % (r[0], money(r[3])) for r in rows if r[0] != paid_name and r[3] > 0]
    return out + (" Owes %s: %s." % (paid_name, ", ".join(owes)) if owes else " Nothing owed to %s." % paid_name)


def main(argv):
    if len(argv) != 2 or argv[1].startswith("--"):
        print(__doc__.split("\n\n", 1)[1].rstrip())
        return 2
    try:
        with open(argv[1], encoding="utf-8-sig") as f:
            gift, people, paid = parse(f.read())
        rows, paid = share(gift, people, paid)
    except (ValueError, OSError) as e:
        print("gift: %s" % e)
        return 1
    for r in rows:
        print(row(*r, paid_name=paid))
    print(summary(rows, paid))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
