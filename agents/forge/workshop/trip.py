#!/usr/bin/env python3
"""Share a car trip so each person pays for the kilometres they rode, plus
their part of tolls and parking, with nothing guessed. Offline, no network.

Usage: trip.py FILE
  FILE  one line each: a leg, a cost, and optional people and who paid:
          leg, Pune to Lonavala, 65 km, Ana and Ben and Cy
          leg, Lonavala to Mumbai, 85 km, Ana and Ben
          fuel, 1,500
          toll, 270, leg 2
          parking, 200, everyone
          people, Ana, Ben, Cy, Dee
          paid, Ana
        A leg is a label, a distance with km or mi (one unit for the trip),
        and who rode it: names joined by and, &, + or /, or "everyone".
        fuel, petrol, diesel, gas and charging are split across the legs by
        distance, then each leg's part evenly among that leg's riders; add
        "leg 2" (or a leg's label) to put a fuel cost on one leg only.
        Other costs (toll, parking, food, or any word) must say who they
        are on: a leg, everyone, or names. Optional: "people, Ana, Ben, Cy"
        (who is in, in order, including anyone who didn't ride) and
        "paid, name" (one person who paid). Spare cents go to whoever was
        rounded down the most (largest remainder), ties to the first in
        the list.
It prints what each person rode and pays, and one line the group can copy.

Needs rent.py beside it (it reads amounts the same way Fair rent does).
"""
import re
import sys
from fractions import Fraction

from rent import AMOUNT, hundredths

LIMIT = 10 ** 13  # 100 billion in cents; the page counts the same way up to here
AND = r"[ \t]+and[ \t]+|[ \t]*[&+/][ \t]*"
ALL = ("everyone",)
FUEL = ("fuel", "petrol", "diesel", "gas", "charging")
UNITS = r"(km|kms|kilometres?|kilometers?|mi|miles?)"
LEG = re.compile(r"leg[ \t]*,", re.I)
PEOPLE = re.compile(r"people[ \t]*,", re.I)
PAID = re.compile(r"paid[ \t]*,", re.I)
LEG_LINE = re.compile(
    r"^\s*(.*?),\s*((?:[$€£₹]?\s*)" + AMOUNT + r")\s*" + UNITS + r"\s*,\s*(.+?)\s*$", re.I)
LEG_NO = re.compile(r"^leg[ \t]*([0-9]+)$", re.I)
LEG_LAB = re.compile(r"^leg[ \t]+(.+)$", re.I)


def amount(text, what):
    c = hundredths(text, what)
    if c > LIMIT:
        raise ValueError("bad %s: %s (that's more than this counts; the most is 100,000,000,000)" % (what, text.strip()))
    return c


def money(c):
    whole = "{:,}".format(c // 100)
    return whole if c % 100 == 0 else "%s.%02d" % (whole, c % 100)


def fmt_dist(c):
    whole = "{:,}".format(c // 100)
    if c % 100 == 0:
        return whole
    if c % 10 == 0:
        return "%s.%d" % (whole, (c % 100) // 10)
    return "%s.%02d" % (whole, c % 100)


def unit_of(u):
    return "mi" if u.lower() in ("mi", "mile", "miles") else "km"


def unit_word(u):
    return "miles" if u == "mi" else "km"


def names_in(who):
    return [w.strip() for w in re.split(AND, who)]


def _amt(text, no, line, how):
    try:
        return amount(text, "amount")
    except ValueError as e:
        if "that's more than this counts" in str(e):
            raise ValueError("line %d: %s" % (no, e))
        raise ValueError(how % (no, line))


def _names(who, no, line, how):
    out, seen = [], set()
    for w in names_in(who):
        if not any(ch.isalpha() for ch in w):
            raise ValueError(how % (no, line))
        if w.lower() in ALL:
            raise ValueError("line %d: write either everyone or names, not both: %s" % (no, line))
        if w.lower() in seen:
            raise ValueError("line %d: %s is named twice: %s" % (no, w, line))
        seen.add(w.lower())
        out.append(w)
    if not out:
        raise ValueError(how % (no, line))
    return out


def parse(text):
    """-> (people or None, legs [(label, dist hundredths, unit, riders or 'everyone', no, line)],
    costs [(kind, cents, dest, no, line)], paid or None).
    dest is ('distance', None), ('leg', index), ('everyone', None) or ('names', [names])."""
    people, legs, raw, paid = None, [], [], None
    unit, labels = None, {}
    for no, raw_line in enumerate(text.splitlines(), 1):
        line = raw_line.replace("\ufeff", "").strip()
        if not line:
            continue
        if "%" in line:
            raise ValueError("line %d: write the exact amount, not %% (a %% of the fuel and a %% of a leg are different things): %s" % (no, line))
        if LEG.match(line):
            rest = line.partition(",")[2]
            m = LEG_LINE.match(rest)
            if not m or not m.group(1).strip():
                raise ValueError("line %d: write it as: leg, label, distance, who, like: leg, Pune to Lonavala, 65 km, Ana and Ben: %s" % (no, line))
            label, num, u, who = m.group(1).strip(), m.group(2), m.group(3), m.group(4).strip()
            if not re.search(r"[0-9]", num):
                raise ValueError("line %d: write the distance with km or mi, like 65 km: %s" % (no, line))
            try:
                dist = amount(num, "distance")
            except ValueError:
                raise ValueError("line %d: write the distance with km or mi, like 65 km: %s" % (no, line))
            kind = unit_of(u)
            if unit is None:
                unit = kind
            elif kind != unit:
                raise ValueError("line %d: this leg is in %s but an earlier leg is in %s; use one unit for the trip: %s"
                                 % (no, unit_word(kind), unit_word(unit), line))
            if dist == 0:
                raise ValueError("line %d: a leg of 0 %s isn't a leg: %s" % (no, unit_word(kind), line))
            key = label.lower()
            if key in labels:
                raise ValueError("line %d: %s is already a leg: %s" % (no, label, line))
            if key in ALL or LEG_NO.match(label):
                raise ValueError("line %d: pick a label that isn't 'everyone' or a leg number: %s" % (no, line))
            if who.lower() in ALL:
                riders = "everyone"
            else:
                riders = _names(who, no, line, "line %d: say who rode this leg: everyone, or names like Ana and Ben: %s")
            labels[key] = len(legs)
            legs.append((label, dist, kind, riders, no, line))
            continue
        if PEOPLE.match(line):
            if people is not None:
                raise ValueError("line %d: the people line is written twice: %s" % (no, line))
            people, seen = [], set()
            rest = line.partition(",")[2]
            for n in [w.strip() for w in re.split(",|" + AND, rest)]:
                if not any(ch.isalpha() for ch in n):
                    raise ValueError("line %d: write people by name, like: people, Ana, Ben and Cy: %s" % (no, line))
                if n.lower() in ALL:
                    raise ValueError("line %d: list the people by name, not %s: %s" % (no, n, line))
                if n.lower() in seen:
                    raise ValueError("line %d: %s is listed twice: %s" % (no, n, line))
                seen.add(n.lower())
                people.append(n)
            if not people:
                raise ValueError("line %d: write people by name, like: people, Ana, Ben and Cy: %s" % (no, line))
            continue
        if PAID.match(line):
            if paid is not None:
                raise ValueError("line %d: who paid is written twice: %s" % (no, line))
            who = line.partition(",")[2].strip()
            if "," in who or who.lower() in ALL or re.search(AND, " %s " % who):
                raise ValueError("line %d: put one person who paid (for several payers, use Settle up): %s" % (no, line))
            if not any(ch.isalpha() for ch in who):
                raise ValueError("line %d: write it as: paid, name: %s" % (no, line))
            paid = who
            continue
        kind, comma, rest = line.partition(",")
        kind, rest = kind.strip(), rest.strip()
        if not comma or not any(ch.isalpha() for ch in kind):
            raise ValueError("line %d: write a cost as: fuel, amount, or a cost with who, like: parking, amount, everyone: %s" % (no, line))
        try:
            cents = amount(rest, "amount")
            target = None
        except ValueError as e:
            if "that's more than this counts" in str(e):
                raise ValueError("line %d: %s" % (no, e))
            head, comma2, tail = rest.rpartition(",")
            if not comma2:
                raise ValueError("line %d: write it as: %s, amount (or %s, amount, everyone): %s" % (no, kind, kind, line))
            target = tail.strip()
            if not target:
                raise ValueError("line %d: say who %s is on: everyone, names, or leg 2: %s" % (no, kind, line))
            cents = _amt(head, no, line, "line %d: write it as: " + kind + ", amount, everyone (or names, or leg 2): %s")
        if cents == 0:
            raise ValueError("line %d: a %s of 0 isn't a cost: %s" % (no, kind, line))
        raw.append((kind, cents, target, no, line))
    costs = [(kind, cents, _dest(kind, target, legs, no, line), no, line)
             for kind, cents, target, no, line in raw]
    return people, legs, costs, paid


def _dest(kind, target, legs, no, line):
    if target is None:
        if kind.lower() in FUEL:
            return ("distance", None)
        raise ValueError("line %d: say who %s is on: everyone, names, or leg 2: %s" % (no, kind, line))
    if target.lower() in ALL:
        return ("everyone", None)
    m = LEG_NO.match(target)
    if m:
        n = int(m.group(1))
        if n < 1 or n > len(legs):
            raise ValueError("line %d: there is no leg %d (the trip has %d leg%s): %s"
                             % (no, n, len(legs), "" if len(legs) == 1 else "s", line))
        return ("leg", n - 1)
    labels = {leg[0].lower(): i for i, leg in enumerate(legs)}
    m = LEG_LAB.match(target)
    lab = m.group(1).strip() if m else None
    if lab is not None:
        i = labels.get(lab.lower())
        if i is None:
            raise ValueError("line %d: there is no leg called %s: %s" % (no, lab, line))
        return ("leg", i)
    if target.lower() in labels:
        return ("leg", labels[target.lower()])
    how = "line %d: say who " + kind + " is on: everyone, names, or leg 2: %s"
    return ("names", _names(target, no, line, how))


def hamilton(parts, total):
    """Round a list of Fractions (or exact rationals) so they add to total cents.
    Spare cents go to the largest remainders, ties by list order."""
    floors = [int(p) for p in parts]
    rems = [p - f for p, f in zip(parts, floors)]
    spare = total - sum(floors)
    for i in sorted(range(len(parts)), key=lambda i: (-rems[i], i))[:spare]:
        floors[i] += 1
    return floors


def share(people_in, legs, costs, paid=None):
    """-> ([(name, rode hundredths, total dist, unit, pays)], who paid or None)."""
    if not legs:
        raise ValueError("no legs listed (write each leg as: leg, label, distance, who)")
    if not costs:
        raise ValueError("no costs listed (write a cost as: fuel, amount, or parking, amount, everyone)")
    total_cents = sum(c for _, c, _, _, _ in costs)
    if total_cents > LIMIT:
        raise ValueError("the costs add up to %s, which is more than this counts; the most is 100,000,000,000" % money(total_cents))
    unit = legs[0][2]
    total_dist = sum(leg[1] for leg in legs)
    people = list(people_in) if people_in is not None else []
    declared = people_in is not None

    def note(name, no, line):
        if not any(ch.isalpha() for ch in name):
            raise ValueError("line %d: say who this is on: everyone, or names like Ana and Ben: %s" % (no, line))
        key = name.lower()
        found = next((p for p in people if p.lower() == key), None)
        if found is not None:
            return found
        if declared:
            raise ValueError("line %d: who is %s? nobody by that name is on the people list: %s" % (no, name, line))
        people.append(name)
        return name

    for label, dist, u, riders, no, line in legs:
        if riders != "everyone":
            for w in riders:
                note(w, no, line)
    for kind, c, dest, no, line in costs:
        if dest[0] == "names":
            for w in dest[1]:
                note(w, no, line)
    if not people:
        raise ValueError("nobody named (put riders on a leg by name, or add: people, Ana and Ben)")
    idx = {p.lower(): i for i, p in enumerate(people)}

    def riders_of(leg):
        riders = leg[3]
        if riders == "everyone":
            return list(range(len(people)))
        on = []
        for w in riders:
            i = idx[w.lower()]
            if i not in on:
                on.append(i)
        return on

    if paid is not None:
        if paid.lower() not in idx:
            raise ValueError("who is %s? nobody by that name is on this trip (add them to a people line if they didn't ride)" % paid)
        paid = people[idx[paid.lower()]]

    n = len(people)
    exact = [Fraction(0) for _ in range(n)]
    rode = [0] * n
    for leg in legs:
        d = leg[1]
        for i in riders_of(leg):
            rode[i] += d
    for kind, c, dest, no, line in costs:
        typ, arg = dest
        if typ == "distance":
            if total_dist == 0:
                raise ValueError("line %d: a leg of 0 %s isn't a leg: %s" % (no, unit_word(unit), line))
            for leg in legs:
                part = Fraction(c) * leg[1] / total_dist
                on = riders_of(leg)
                if not on:
                    raise ValueError("line %d: say who rode this leg: everyone, or names like Ana and Ben: %s" % (leg[4], leg[5]))
                share_each = part / len(on)
                for i in on:
                    exact[i] += share_each
        elif typ == "leg":
            on = riders_of(legs[arg])
            if not on:
                raise ValueError("line %d: say who rode this leg: everyone, or names like Ana and Ben: %s" % (legs[arg][4], legs[arg][5]))
            share_each = Fraction(c) / len(on)
            for i in on:
                exact[i] += share_each
        elif typ == "everyone":
            share_each = Fraction(c) / n
            for i in range(n):
                exact[i] += share_each
        else:
            on = []
            for w in arg:
                i = idx.get(w.lower())
                if i is None:
                    raise ValueError("line %d: who is %s? nobody by that name is on the people list: %s" % (no, w, line))
                if i in on:
                    raise ValueError("line %d: %s is named twice: %s" % (no, w, line))
                on.append(i)
            share_each = Fraction(c) / len(on)
            for i in on:
                exact[i] += share_each
    pays = hamilton(exact, total_cents)
    rows = [(people[i], rode[i], total_dist, unit, pays[i]) for i in range(n)]
    return rows, paid


def row(name, rode, total, unit, pays, paid_name=None):
    s = "%s: rode %s %s of %s, pays %s" % (name, fmt_dist(rode), unit, fmt_dist(total), money(pays))
    if paid_name is not None and name == paid_name:
        s += " (paid the trip)"
    return s


def summary(rows, costs, paid_name=None):
    order, sums = [], {}
    for kind, c, _, _, _ in costs:
        key = kind.lower()
        if key not in sums:
            sums[key] = [kind, 0]
            order.append(key)
        sums[key][1] += c
    parts = ["%s %s" % (sums[k][0], money(sums[k][1])) for k in order]
    if paid_name is not None:
        parts.append("paid by " + paid_name)
    total = sum(r[4] for r in rows)
    out = "Trip %s (%s). %s." % (money(total), ", ".join(parts), ", ".join("%s %s" % (r[0], money(r[4])) for r in rows))
    if paid_name is None:
        return out
    owes = ["%s %s" % (r[0], money(r[4])) for r in rows if r[0] != paid_name and r[4] > 0]
    return out + (" Owes %s: %s." % (paid_name, ", ".join(owes)) if owes else " Nothing owed to %s." % paid_name)


def main(argv):
    if len(argv) != 2 or argv[1].startswith("--"):
        print(__doc__.split("\n\n", 1)[1].rstrip())
        return 2
    try:
        with open(argv[1], encoding="utf-8-sig") as f:
            people, legs, costs, paid = parse(f.read())
        rows, paid = share(people, legs, costs, paid)
    except (ValueError, OSError) as e:
        print("trip: %s" % e)
        return 1
    for r in rows:
        print(row(*r, paid_name=paid))
    print(summary(rows, costs, paid))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
