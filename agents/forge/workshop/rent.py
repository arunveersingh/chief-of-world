#!/usr/bin/env python3
"""Split a flat's rent by room size. Offline, no network.

Usage: rent.py TOTAL SHARED_PERCENT FILE
  TOTAL           the whole month's rent, e.g. 2400, 1,850.50 or 1,00,000
  SHARED_PERCENT  how much of the rent is for shared space (kitchen, living
                  room, hall), split per person; the rest is split by room
                  size. A whole number from 0 to 100, like 30 or 30%.
  FILE            one room per line: name, room size (any unit, the same for
                  everyone; "14", "14 m2" or "150 sq ft" are all fine).
                  Optional parts after a comma and a space:
                    +50        a fixed monthly extra for a perk (en-suite,
                               balcony); extras come off the top
                    2 people   a couple sharing the room pays two shares of
                               the shared space (the room itself is one room)
                  e.g. "Ann & Bo, 14, 2 people, +50"
"""
import re
import sys

AMOUNT = r"(?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]{1,2}(?:,[0-9]{2})*,[0-9]{3}|[0-9]*)(?:\.[0-9]{1,2})?"
NUM = r"[$€£₹]?\s*(" + AMOUNT + r")"
UNIT = r"(m2|m²|sqm|sq\.?\s*m|ft2|ft²|sqft|sq\.?\s*ft|square\s+(?:metres|meters|feet))?"
SIZE = r"\s*((?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]*)(?:\.[0-9]{1,2})?)\s*" + UNIT + r"\s*"
PEOPLE = r"(?:([0-9]{1,2})\s*(?:people|persons?)|people\s*([0-9]{1,2}))"


def hundredths(text, what):
    t = text.strip()
    m = re.fullmatch(NUM, t)
    if not m or not re.search(r"[0-9]", m.group(1)):
        raise ValueError("bad %s: %s (write 2400 or 1,850.50)" % (what, t))
    whole, _, frac = m.group(1).replace(",", "").partition(".")
    return int(whole or "0") * 100 + int((frac + "00")[:2])


def split(total, shared_pct, rooms):
    """total in cents, shared_pct 0..100, rooms = [(name, size[, extra[, people]])],
    size in hundredths, extra in cents. Each extra is paid on top by that room;
    the shared part is split per person, the rest by room size.
    Returns {name: cents}, which always adds up to total."""
    if not rooms:
        raise ValueError("nobody listed")
    if not 0 <= shared_pct <= 100:
        raise ValueError("shared percent must be 0 to 100")
    area = sum(r[1] for r in rooms)
    if area <= 0:
        raise ValueError("room sizes add up to zero")
    extras = {r[0]: (r[2] if len(r) > 2 else 0) for r in rooms}
    people = {r[0]: (r[3] if len(r) > 3 else 1) for r in rooms}
    if sum(extras.values()) > total:
        raise ValueError("the extras add up to more than the rent")
    rest = total - sum(extras.values())
    shared = rest * shared_pct // 100
    by_size = rest - shared
    heads = sum(people.values())
    out = {r[0]: shared * people[r[0]] // heads + by_size * r[1] // area for r in rooms}
    names = sorted(out)
    spare = rest - sum(out.values())
    i = 0
    while spare > 0:
        out[names[i % len(names)]] += 1
        spare -= 1
        i += 1
    for n in out:
        out[n] += extras[n]
    return out


def parse(text):
    rooms, seen, units = [], set(), {}
    for no, raw in enumerate(text.splitlines(), 1):
        line = raw.replace("\ufeff", "").strip()
        if not line:
            continue
        name, sep, rest = line.partition(",")
        name = name.strip()
        if not sep or not name:
            raise ValueError("line %d: write it as: name, room size: %s" % (no, line))
        if re.fullmatch(r"[0-9.,]+", name):
            raise ValueError("line %d: %s looks like a number, not a name" % (no, name))
        if name.lower() in seen:
            raise ValueError("line %d: %s is listed twice" % (no, name))
        parts = re.split(r",\s+", rest)
        m = re.fullmatch(SIZE, parts[0], re.I)
        if not m or not re.search(r"[0-9]", m.group(1)):
            hint = ("if you mean a decimal, write it with a dot, like 10.5; "
                    "for a perk, write 10, +5") if re.fullmatch(r"\s*[0-9]+,[0-9]{1,2}\s*", parts[0]) \
                else "write 14, 9.5 or 150 sq ft"
            raise ValueError("line %d: bad room size: %s (%s)" % (no, parts[0].strip(), hint))
        if m.group(2):
            kind = "square feet" if "f" in m.group(2).lower() else "square metres"
            units.setdefault(kind, name)
            if len(units) > 1:
                other = [k for k in units if k != kind][0]
                raise ValueError("line %d: %s's room is in %s but %s's is in %s; use one unit for everyone"
                                 % (no, name, kind, units[other], other))
        size = hundredths(m.group(1), "room size")
        if size == 0:
            raise ValueError("line %d: %s has a room of size 0" % (no, name))
        extra, heads = None, None
        for part in parts[1:]:
            p = part.strip()
            pm = re.fullmatch(PEOPLE, p, re.I)
            if pm:
                if heads is not None:
                    raise ValueError("line %d: people given twice" % no)
                heads = int(pm.group(1) or pm.group(2))
                if heads == 0:
                    raise ValueError("line %d: a room needs at least 1 person" % no)
                continue
            if extra is not None:
                raise ValueError("line %d: bad part: %s (only one extra per room)" % (no, p))
            try:
                extra = hundredths(re.sub(r"^(?:\+|extra\s+)", "", p, flags=re.I), "extra")
            except ValueError as e:
                raise ValueError("line %d: %s" % (no, e))
        seen.add(name.lower())
        rooms.append((name, size, extra or 0, heads or 1))
    return rooms


def money(c):
    return "%d.%02d" % (c // 100, c % 100)


def main(argv):
    pct = argv[2].strip().rstrip("%").strip() if len(argv) == 4 else ""
    if not re.fullmatch(r"[0-9]{1,3}", pct):
        print(__doc__.split("\n\n", 1)[1], file=sys.stderr)
        if len(argv) == 4:
            print("rent: the shared percent is a whole number, like 30", file=sys.stderr)
        return 2
    try:
        total = hundredths(argv[1], "rent")
        with open(argv[3], encoding="utf-8-sig") as f:
            rooms = parse(f.read())
        shares = split(total, int(pct), rooms)
    except (ValueError, OSError) as e:
        print("rent: %s" % e, file=sys.stderr)
        return 1
    for n, _, extra, heads in rooms:
        notes = (["%d people" % heads] if heads > 1 else []) + \
                (["includes %s extra" % money(extra)] if extra else [])
        print("%s pays %s%s" % (n, money(shares[n]), " (%s)" % ", ".join(notes) if notes else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
