#!/usr/bin/env python3
"""Split a shared bill (electricity, gas, internet) by the days each person
was actually living there. Offline, no network.

Usage: bills.py TOTAL DAYS FILE [--fixed AMOUNT]
  TOTAL  the whole bill, e.g. 3,120 or 84.50
  DAYS   how many days the bill covers, a whole number like 30 or 92
  FILE   one person per line: name, days they lived there in that period.
         A name alone means the whole period. e.g.
           Asha
           Ben, 12      (moved in on the 19th of a 30-day month)
           Cy, 0        (away the whole time, pays nothing)
           Di, 1-10, 21-30   (away in the middle: days 1 to 10 and 21 to 30)
         A couple is two lines, one per person.
  --fixed AMOUNT  the part of the bill that is charged whatever anyone uses
         (internet's monthly fee, a standing charge). It is split evenly
         among everyone listed, even people who were away; the rest is split
         by days. Leave it out to split the whole bill by days.

Needs rent.py beside it (it reads amounts the same way Fair rent does).
"""
import re
import sys

from rent import hundredths

DAYCOUNT = r"\s*([0-9]{1,4})\s*(?:days?)?\s*"
STRETCH = r"([0-9]{1,4})\s*(?:-|–|to)\s*([0-9]{1,4})"


def stretches(no, text, period):
    """'1-10, 21-30' -> number of days; day 1 is the first day of the bill."""
    spans = []
    for part in re.split(r",\s*|\s+and\s+", text.strip(), flags=re.I):
        m = re.fullmatch(STRETCH, part.strip(), re.I)
        if not m:
            raise ValueError("line %d: bad stretch: %s (write days like 1-10, 21-30)" % (no, part.strip()))
        a, b = int(m.group(1)), int(m.group(2))
        if a < 1 or b < a:
            raise ValueError("line %d: bad stretch: %s (days run from 1, and the first day comes first)" % (no, part.strip()))
        if b > period:
            raise ValueError("line %d: %s runs past day %d, the last day of the bill" % (no, part.strip(), period))
        spans.append((a, b))
    spans.sort()
    for (a1, b1), (a2, b2) in zip(spans, spans[1:]):
        if a2 <= b1:
            raise ValueError("line %d: the stretches %d-%d and %d-%d overlap" % (no, a1, b1, a2, b2))
    return sum(b - a + 1 for a, b in spans)


def split(total, people, fixed=0):
    """total and fixed in cents, people = [(name, days)]. The fixed part is
    split evenly among everyone listed; the rest in proportion to days.
    Spare cents go one each, alphabetically: the fixed part's to anyone
    listed, the rest's to people with days."""
    if fixed > total:
        raise ValueError("the fixed part is more than the whole bill")
    use = total - fixed
    days = sum(d for _, d in people)
    if days <= 0 and use > 0:
        raise ValueError("nobody was there for any days")
    each = fixed // len(people)
    out = {n: each + (use * d // days if use else 0) for n, d in people}
    everyone = sorted(n for n, _ in people)
    for i in range(fixed - each * len(people)):
        out[everyone[i % len(everyone)]] += 1
    present = sorted(n for n, d in people if d > 0)
    for i in range(total - sum(out.values())):
        out[present[i % len(present)]] += 1
    return out


def parse(text, period):
    people, seen = [], set()
    for no, raw in enumerate(text.splitlines(), 1):
        line = raw.replace("\ufeff", "").strip()
        if not line:
            continue
        name, comma, rest = line.partition(",")
        name = name.strip()
        if not name:
            raise ValueError("line %d: write it as: name, days: %s" % (no, line))
        if re.fullmatch(r"[0-9.,]+", name):
            raise ValueError("line %d: %s looks like a number, not a name" % (no, name))
        if name.lower() in seen:
            raise ValueError("line %d: %s is listed twice" % (no, name))
        if comma:
            m = re.fullmatch(DAYCOUNT, rest, re.I)
            if re.search(r"\b(?:people|persons?)\b", rest, re.I):
                raise ValueError("line %d: bad days: %s (put each person on their own line; a couple is two lines)" % (no, rest.strip()))
            if not m and re.search(r"[0-9]\s*(?:-|–|to)\s*[0-9]", rest, re.I):
                d = stretches(no, rest, period)
            elif not m:
                raise ValueError("line %d: bad days: %s (write a whole number of days, like 12)" % (no, rest.strip()))
            else:
                d = int(m.group(1))
        else:
            d = period
        if d > period:
            raise ValueError("line %d: %s was there %d days but the bill covers %d" % (no, name, d, period))
        seen.add(name.lower())
        people.append((name, d))
    if not people:
        raise ValueError("nobody listed")
    return people


def money(c):
    return "%d.%02d" % (c // 100, c % 100)


def main(argv):
    if len(argv) not in (4, 6) or (len(argv) == 6 and argv[4] != "--fixed") \
            or not re.fullmatch(r"[0-9]{1,4}", argv[2].strip()) or int(argv[2]) == 0:
        print(__doc__.split("\n\n", 1)[1].rstrip())
        if len(argv) in (4, 6):
            print("bills: DAYS is a whole number of days, at least 1, like 30")
        return 2
    try:
        total = hundredths(argv[1], "bill")
        fixed = hundredths(argv[5], "fixed part") if len(argv) == 6 else 0
        period = int(argv[2])
        with open(argv[3], encoding="utf-8-sig") as f:
            people = parse(f.read(), period)
        shares = split(total, people, fixed)
    except (ValueError, OSError) as e:
        print("bills: %s" % e)
        return 1
    for n, d in people:
        print("%s pays %s (%d of %d days)" % (n, money(shares[n]), d, period))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
