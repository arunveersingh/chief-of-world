#!/usr/bin/env python3
"""Keep one running count of a loan paid back in parts, so the lender and the
borrower see the same balance. Offline, no network.

Usage: payback.py AMOUNT FILE
       payback.py AMOUNT --plan N
  AMOUNT  what was lent, e.g. 5,000 or 840.50
  FILE    one payment per line, oldest first: when, amount. e.g.
            Dec, 1,000
            Jan, 600
            Feb, 1,000
          A line with only an amount is a payment with no date.
  --plan N  split AMOUNT into N equal parts instead (1 to 120). Any spare
          cents go one each on the first parts.
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
    if len(argv) == 4 and argv[2] == "--plan":
        try:
            lent = amount(argv[1], "amount lent")
            if not re.fullmatch(r"[0-9]{1,3}", argv[3].strip()) or not 1 <= int(argv[3]) <= 120:
                raise ValueError("bad number of parts: %s (write a whole number from 1 to 120)" % argv[3].strip())
            parts = plan(lent, int(argv[3]))
        except ValueError as e:
            print("payback: %s" % e)
            return 1
        for i, c in enumerate(parts, 1):
            print("Part %d of %d: %s" % (i, len(parts), money(c)))
        print("Together: %s" % money(sum(parts)))
        return 0
    if len(argv) != 3 or argv[2].startswith("--"):
        print(__doc__.split("\n\n", 1)[1].rstrip())
        return 2
    try:
        lent = amount(argv[1], "amount lent")
        with open(argv[2], encoding="utf-8-sig") as f:
            payments = parse(f.read())
        after = count(lent, payments)
    except (ValueError, OSError) as e:
        print("payback: %s" % e)
        return 1
    for i, ((lb, c), left) in enumerate(zip(payments, after), 1):
        print("%s: paid %s, left %s" % (lb or "payment %d" % i, money(c), money(left)))
    print(summary(lent, payments))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
