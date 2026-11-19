#!/usr/bin/env python3
"""Split a flat's rent by room size. Offline, no network.

Usage: rent.py TOTAL SHARED_PERCENT FILE
  TOTAL           the whole month's rent, e.g. 2400 or 1,850.50
  SHARED_PERCENT  how much of the rent is for shared space (kitchen, living
                  room, hall), split equally; the rest is split by room size.
                  A whole number from 0 to 100. 30 is a common choice.
  FILE            one person per line: name, room size (any unit, same for all)
"""
import re
import sys

NUM = r"[$€£₹]?\s*((?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]*)(?:\.[0-9]{1,2})?)"


def hundredths(text, what):
    t = text.strip()
    m = re.fullmatch(NUM, t)
    if not m or not re.search(r"[0-9]", m.group(1)):
        raise ValueError("bad %s: %s (write 2400 or 1,850.50)" % (what, t))
    whole, _, frac = m.group(1).replace(",", "").partition(".")
    return int(whole or "0") * 100 + int((frac + "00")[:2])


def split(total, shared_pct, rooms):
    """total in cents, shared_pct 0..100, rooms = [(name, size in hundredths)].
    Returns {name: cents}. Shares always add up to total exactly."""
    if not rooms:
        raise ValueError("nobody listed")
    if not 0 <= shared_pct <= 100:
        raise ValueError("shared percent must be 0 to 100")
    area = sum(s for _, s in rooms)
    if area <= 0:
        raise ValueError("room sizes add up to zero")
    shared = total * shared_pct // 100
    by_size = total - shared
    names = sorted(n for n, _ in rooms)
    out = {n: shared // len(rooms) + by_size * s // area for n, s in rooms}
    spare = total - sum(out.values())
    i = 0
    while spare > 0:
        out[names[i % len(names)]] += 1
        spare -= 1
        i += 1
    return out


def parse(text):
    rooms, seen = [], set()
    for no, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        name, sep, size = line.partition(",")
        name = name.strip()
        if not sep or not name:
            raise ValueError("line %d: write it as: name, room size: %s" % (no, line))
        if re.fullmatch(r"[0-9.,]+", name):
            raise ValueError("line %d: %s looks like a number, not a name" % (no, name))
        if name in seen:
            raise ValueError("line %d: %s is listed twice" % (no, name))
        try:
            s = hundredths(size, "room size")
        except ValueError as e:
            raise ValueError("line %d: %s" % (no, e))
        if s == 0:
            raise ValueError("line %d: %s has a room of size 0" % (no, name))
        seen.add(name)
        rooms.append((name, s))
    return rooms


def money(c):
    return "%d.%02d" % (c // 100, c % 100)


def main(argv):
    if len(argv) != 4 or not re.fullmatch(r"[0-9]{1,3}", argv[2]):
        print(__doc__.split("\n\n", 1)[1], file=sys.stderr)
        return 2
    try:
        total = hundredths(argv[1], "rent")
        with open(argv[3], encoding="utf-8") as f:
            rooms = parse(f.read())
        shares = split(total, int(argv[2]), rooms)
    except (ValueError, OSError) as e:
        print("rent: %s" % e, file=sys.stderr)
        return 1
    for n, _ in rooms:
        print("%s pays %s" % (n, money(shares[n])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
