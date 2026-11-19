#!/usr/bin/env python3
"""Keep one running count of a loan paid back in parts, so the lender and the
borrower see the same balance. Offline, no network.

Usage: payback.py AMOUNT FILE
       payback.py AMOUNT --plan N
       payback.py AMOUNT FILE --plan N   (or AMOUNT --plan N FILE)
  AMOUNT  what was lent, e.g. 5,000 or 840.50
  FILE    one payment per line, oldest first: when, amount. e.g.
            Dec, 1,000
            Jan, 600
            Feb, 1,000
          A line with only an amount is a payment with no date. Write a
          decimal with a dot (12.50): a line like 12,50 is refused, because
          it could be the 12th and a payment of 50.
  --plan N  split into N equal parts instead (1 to 120). Without FILE it
          splits the whole AMOUNT; with FILE it splits only what is left
          after the payments in FILE. Any spare cents go one each on the
          first parts.
It prints the balance after each payment and one line you can both copy:
  Paid 1,000 (Dec), 600 (Jan), 1,000 (Feb). Left: 2,400 of 5,000.

Needs rent.py beside it (it reads amounts the same way Fair rent does).
"""
import re
import sys

from rent import hundredths

LIMIT = 10 ** 13  # 100 billion in cents; the page counts the same way up to here


def amount(text, what):
    c = hundredths(text, what)
    if c > LIMIT:
        raise ValueError("bad %s: %s (that's more than this counts; the most is 100,000,000,000)" % (what, text.strip()))
    return c


def money(c):
    whole = "{:,}".format(c // 100)
    return whole if c % 100 == 0 else "%s.%02d" % (whole, c % 100)


def parse(text):
    """-> [(label or '', cents)], oldest first."""
    out = []
    for no, raw in enumerate(text.splitlines(), 1):
        line = raw.replace("\ufeff", "").strip()
        if not line:
            continue
        try:
            label, c = "", amount(line, "payment")
        except ValueError:
            label, comma, rest = line.partition(",")
            label = label.strip()
            if not comma or not label:
                raise ValueError("line %d: write it as: when, amount: %s" % (no, line))
            if re.search(r"[0-9]$", label) and re.match(r"[0-9]{3}(?![0-9])", rest.strip()):
                raise ValueError("line %d: put a comma between when and the amount, like Dec, 2,000: %s" % (no, line))
            if re.fullmatch(r"[$€£₹][ \t]*[0-9.]+|[0-9]+|[0-9]{1,3}(?:\.[0-9]{3})+", label):
                if re.fullmatch(r"[0-9]{1,2}", rest.strip()):
                    raise ValueError("line %d: is %s a decimal? write it with a dot like 12.50, or put the date first like 12 Dec, 50" % (no, line))
                raise ValueError("line %d: %s looks like a number, not a date (write a word in the date, like 12 Dec, 50): %s" % (no, label, line))
            try:
                c = amount(rest, "payment")
            except ValueError:
                raise ValueError("line %d: write it as: when, amount: %s" % (no, line))
        if c == 0:
            raise ValueError("line %d: a payment of 0 isn't a payment: %s" % (no, line))
        out.append((label, c))
    return out


def count(lent, payments):
    """-> list of what is left after each payment; refuses paying back too much."""
    if lent == 0:
        raise ValueError("nothing was lent (write what was lent, like 5,000)")
    left, after = lent, []
    for _, c in payments:
        left -= c
        after.append(left)
    if left < 0:
        raise ValueError("the payments add up to %s, which is %s more than the %s lent"
                         % (money(lent - left), money(-left), money(lent)))
    return after


def summary(lent, payments):
    left = lent - sum(c for _, c in payments)
    if not payments:
        return "Nothing paid yet. Left: %s of %s." % (money(left), money(lent))
    paid = ", ".join(money(c) + (" (%s)" % lb if lb else "") for lb, c in payments)
    if left == 0:
        return "Paid %s. Paid back in full: %s." % (paid, money(lent))
    return "Paid %s. Left: %s of %s." % (paid, money(left), money(lent))


def plan(lent, n):
    if lent == 0:
        raise ValueError("nothing was lent (write what was lent, like 5,000)")
    if n > lent:
        raise ValueError("%s can't be split into %d parts of at least one cent" % (money(lent), n))
    each, spare = divmod(lent, n)
    return [each + (1 if i < spare else 0) for i in range(n)]


def main(argv):
    a, name, n = argv[1:], None, None
    if len(a) == 3 and a[1] == "--plan":
        n = a[2]
    elif len(a) == 4 and a[2] == "--plan" and not a[1].startswith("--"):
        name, n = a[1], a[3]
    elif len(a) == 4 and a[1] == "--plan" and not a[3].startswith("--"):
        name, n = a[3], a[2]
    elif len(a) != 2 or a[1].startswith("--"):
        print(__doc__.split("\n\n", 1)[1].rstrip())
        return 2
    else:
        name = a[1]
    try:
        lent = amount(a[0], "amount lent")
        if n is not None and (not re.fullmatch(r"[0-9]{1,3}", n.strip()) or not 1 <= int(n) <= 120):
            raise ValueError("bad number of parts: %s (write a whole number from 1 to 120)" % n.strip())
        payments = []
        if name is not None:
            with open(name, encoding="utf-8-sig") as f:
                payments = parse(f.read())
        after = count(lent, payments)
        left = lent - sum(c for _, c in payments)
        parts = plan(left, int(n)) if n is not None and left else []
    except (ValueError, OSError) as e:
        print("payback: %s" % e)
        return 1
    if n is None:
        for i, ((lb, c), rest) in enumerate(zip(payments, after), 1):
            print("%s: paid %s, left %s" % (lb or "payment %d" % i, money(c), money(rest)))
        print(summary(lent, payments))
        return 0
    if not parts:
        print("Paid back in full: %s (nothing left to plan)." % money(lent))
        return 0
    for i, c in enumerate(parts, 1):
        print("Part %d of %d: %s" % (i, len(parts), money(c)))
    if name is None:
        print("Together: %s" % money(sum(parts)))
    else:
        print("Together: %s (what's left of %s)" % (money(sum(parts)), money(lent)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
