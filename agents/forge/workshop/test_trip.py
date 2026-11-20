#!/usr/bin/env python3
"""Tests for trip.py and the logic inside trip.html (run in node when present).
Copy rent.py, trip.py, trip.html and this file together: trip.py reads
amounts with rent.py's hundredths(), and the last part of this test reads trip.html."""
import json
import os
import pathlib
import random
import shutil
import subprocess
import sys
import tempfile
from fractions import Fraction

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import trip  # noqa: E402


def eq(got, want, what):
    assert got == want, "%s: got %r want %r" % (what, got, want)


def err(fn, *a):
    try:
        fn(*a)
    except ValueError as e:
        return str(e)
    raise AssertionError("no error for %r" % (a,))


def go(text):
    return trip.share(*trip.parse(text))


EX = ("leg, Pune to Lonavala, 65 km, Ana and Ben and Cy\n"
      "leg, Lonavala to Mumbai, 85 km, Ana and Ben\n"
      "fuel, 1,500\n"
      "toll, 270, leg 2\n"
      "parking, 200, everyone\n"
      "people, Ana, Ben, Cy, Dee\n"
      "paid, Ana")

# Hand arithmetic, in cents. Fuel 150,000 is split by distance, then by riders:
#   leg 1 (65 of 150): 65,000, among Ana, Ben, Cy  -> 65,000/3 each
#   leg 2 (85 of 150): 85,000, among Ana, Ben      -> 42,500 each
# Toll 27,000 on leg 2: 13,500 each for Ana, Ben.
# Parking 20,000 among four people (everyone, including Dee who rode 0): 5,000 each.
# Ana = Ben = 65,000/3 + 42,500 + 13,500 + 5,000 = 248,000/3 = 82,666 + 2/3
# Cy = 65,000/3 + 5,000 = 80,000/3 = 26,666 + 2/3
# Dee = 5,000
# Spare 2 cents, largest remainders, ties by list order: Ana and Ben.
people, legs, costs, paid = trip.parse(EX)
eq(paid, "Ana", "paid")
eq(len(legs), 2, "two legs")
eq(legs[0][:4], ("Pune to Lonavala", 6500, "km", ["Ana", "Ben", "Cy"]), "leg 1")
eq(legs[1][:4], ("Lonavala to Mumbai", 8500, "km", ["Ana", "Ben"]), "leg 2")
eq([(k, c, d) for k, c, d, _, _ in costs],
   [("fuel", 150000, ("distance", None)), ("toll", 27000, ("leg", 1)),
    ("parking", 20000, ("everyone", None))], "costs")
eq(people, ["Ana", "Ben", "Cy", "Dee"], "people")
rows, payer = trip.share(people, legs, costs, paid)
eq(rows, [("Ana", 15000, 15000, "km", 82667), ("Ben", 15000, 15000, "km", 82667),
          ("Cy", 6500, 15000, "km", 26666), ("Dee", 0, 15000, "km", 5000)], "share")
eq(payer, "Ana", "payer")
eq(trip.row(*rows[0], paid_name="Ana"), "Ana: rode 150 km of 150, pays 826.67 (paid the trip)", "row payer")
eq(trip.row(*rows[1], paid_name="Ana"), "Ben: rode 150 km of 150, pays 826.67", "row ben")
eq(trip.row(*rows[2]), "Cy: rode 65 km of 150, pays 266.66", "row cy")
eq(trip.row(*rows[3]), "Dee: rode 0 km of 150, pays 50", "row dee")
eq(trip.summary(rows, costs, "Ana"),
   "Trip 1,970 (fuel 1,500, toll 270, parking 200, paid by Ana). "
   "Ana 826.67, Ben 826.67, Cy 266.66, Dee 50. "
   "Owes Ana: Ben 826.67, Cy 266.66, Dee 50.", "summary")
eq(trip.summary(rows, costs),
   "Trip 1,970 (fuel 1,500, toll 270, parking 200). "
   "Ana 826.67, Ben 826.67, Cy 266.66, Dee 50.", "summary no payer")
eq(go(EX)[0], rows, "go example")

# without a people line, everyone is the three riders (Dee is not in)
EX3 = ("leg, Pune to Lonavala, 65 km, Ana and Ben and Cy\n"
       "leg, Lonavala to Mumbai, 85 km, Ana and Ben\n"
       "fuel, 1,500\n"
       "toll, 270, leg 2\n"
       "parking, 200, everyone\n"
       "paid, Ana")
# Ana = Ben = 65,000/3 + 42,500 + 13,500 + 20,000/3 = 253,000/3 = 84,333 + 1/3
# Cy = 65,000/3 + 20,000/3 = 85,000/3 = 28,333 + 1/3
# One spare cent, all remainders equal: Ana.
rows3, payer3 = go(EX3)
eq(rows3, [("Ana", 15000, 15000, "km", 84334), ("Ben", 15000, 15000, "km", 84333),
           ("Cy", 6500, 15000, "km", 28333)], "no people line")
eq(payer3, "Ana", "payer 3")
eq(trip.summary(rows3, trip.parse(EX3)[2], "Ana"),
   "Trip 1,970 (fuel 1,500, toll 270, parking 200, paid by Ana). "
   "Ana 843.34, Ben 843.33, Cy 283.33. Owes Ana: Ben 843.33, Cy 283.33.", "summary 3")

# one leg, two people, fuel 100: 50 each (4,000 / 2 wait: 100 -> 10,000 cents, 5,000 each)
eq(go("leg, A to B, 100 km, Ana and Ben\nfuel, 100")[0],
   [("Ana", 10000, 10000, "km", 5000), ("Ben", 10000, 10000, "km", 5000)], "even fuel")

# uneven riders, fuel 40. Leg 1: 10 km Ana and Ben; leg 2: 30 km Ana.
# Fuel 4,000 cents. Leg 1 part 1,000 / 2 = 500; leg 2 part 3,000 to Ana.
# Ana 3,500 (35), Ben 500 (5).
eq(go("leg, Start, 10 km, Ana and Ben\nleg, End, 30 km, Ana\nfuel, 40")[0],
   [("Ana", 4000, 4000, "km", 3500), ("Ben", 1000, 4000, "km", 500)], "uneven fuel")

# 10 cents among 3 people, all equal remainders: spare goes to the first.
eq(go("leg, A, 1 km, Ana\nleg, B, 1 km, Ben\nleg, C, 1 km, Cy\nfuel, 0.10")[0],
   [("Ana", 100, 300, "km", 4), ("Ben", 100, 300, "km", 3), ("Cy", 100, 300, "km", 3)],
   "hamilton ties by order")

# Dee rode nothing: fuel does not charge her; parking everyone does.
# Fuel 90 -> 9,000 cents, all to Ana and Ben equally (one 10 km leg) = 4,500 each.
# Parking 12 -> 1,200 cents / 3 = 400 each.
eq(go("people, Ana, Ben, Dee\nleg, Town, 10 km, Ana and Ben\nfuel, 90\nparking, 12, everyone")[0],
   [("Ana", 1000, 1000, "km", 4900), ("Ben", 1000, 1000, "km", 4900),
    ("Dee", 0, 1000, "km", 400)], "dee rode nothing")

# 1 cent among 2: first person gets it.
eq(go("leg, A, 5 km, Ana and Ben\nparking, 0.01, everyone")[0],
   [("Ana", 500, 500, "km", 1), ("Ben", 500, 500, "km", 0)], "one cent everyone")

# fuel on one leg only; toll by exact label; petrol synonym; joiner characters
# leg 1 20 km Ana+Ben, leg 2 20 km Ana. petrol 10 on leg 1: 5 each. toll 6 on "East": Ana 6.
eq(go("leg, West, 20 km, Ana & Ben\nleg, East, 20 km, Ana\npetrol, 10, leg 1\ntoll, 6, East")[0],
   [("Ana", 4000, 4000, "km", 1100), ("Ben", 2000, 4000, "km", 500)], "fuel on one leg, toll by label")

# gas / charging / diesel are distance fuels; miles display; 'leg Label' target
rows_m, _ = go("leg, Coast, 10 miles, Ana and Ben\ndiesel, 8\ncharging, 2, leg Coast")
eq(rows_m, [("Ana", 1000, 1000, "mi", 500), ("Ben", 1000, 1000, "mi", 500)], "miles and fuel synonyms")
eq(trip.row(*rows_m[0]), "Ana: rode 10 mi of 10, pays 5", "row miles")

# first spelling wins (people line, then riders / paid case-blind)
rows_c, payer_c = go("people, Ana, Ben\nleg, A, 10 km, ANA and ben\nfuel, 10\npaid, ana")
eq([r[0] for r in rows_c], ["Ana", "Ben"], "first spelling")
eq(payer_c, "Ana", "paid case-blind")

# two fuel lines are summed in the summary; a named food cost; nothing owed
rows_f, _ = go("leg, A, 10 km, Ana\nfuel, 3\nFuel, 2\nfood, 1, Ana\npaid, Ana")
eq(rows_f[0][4], 600, "two fuels plus food")
eq(trip.summary(rows_f, trip.parse("leg, A, 10 km, Ana\nfuel, 3\nFuel, 2\nfood, 1, Ana\npaid, Ana")[2], "Ana"),
   "Trip 6 (fuel 5, food 1, paid by Ana). Ana 6. Nothing owed to Ana.", "summary merge fuel, nothing owed")

# zero share is listed but not owed; a person with a 0 share
eq(trip.summary([("Ana", 1000, 1000, "km", 500), ("Bo", 0, 1000, "km", 0), ("Cy", 1000, 1000, "km", 50)],
                [("fuel", 550, ("distance", None), 1, "fuel, 5.50")], "Ana"),
   "Trip 5.50 (fuel 5.50, paid by Ana). Ana 5, Bo 0, Cy 0.50. Owes Ana: Cy 0.50.", "zero share owes nothing")

# one cent owed is still owed
eq(trip.summary([("Ana", 100, 100, "km", 100), ("Bo", 100, 100, "km", 1)],
                [("fuel", 101, ("distance", None), 1, "fuel, 1.01")], "Ana"),
   "Trip 1.01 (fuel 1.01, paid by Ana). Ana 1, Bo 0.01. Owes Ana: Bo 0.01.", "one cent owed")

# spaces, case, currency, lakh, most, kilometres, joiners
ppl, lgs, cts, pd = trip.parse(
    "\ufeff PEOPLE , Ana, Ben and Cy \nLEG , Highway, ₹1,200 km, Ana + Ben / Cy\nGAS, 2,00,000\npaid, ANA")
eq(ppl, ["Ana", "Ben", "Cy"], "spaces people")
eq(lgs[0][:4], ("Highway", 120000, "km", ["Ana", "Ben", "Cy"]), "lakh-size distance, joiners")
eq(cts[0][1], 20000000, "lakh gas")
eq(go("\ufeff PEOPLE , Ana, Ben and Cy \nLEG , Highway, ₹1,200 km, Ana + Ben / Cy\nGAS, 2,00,000\npaid, ANA")[1],
   "Ana", "paid after first spelling")

for c, want in [(0, "0"), (5, "0.05"), (100, "1"), (123456789, "1,234,567.89"), (10 ** 13, "100,000,000,000")]:
    eq(trip.money(c), want, "money %d" % c)
for c, want in [(0, "0"), (500, "5"), (550, "5.5"), (555, "5.55"), (120000, "1,200")]:
    eq(trip.fmt_dist(c), want, "fmt_dist %d" % c)
eq(trip.hamilton([Fraction(10, 3), Fraction(10, 3), Fraction(10, 3)], 10), [4, 3, 3], "hamilton")
eq(trip.hamilton([Fraction(0), Fraction(5)], 5), [0, 5], "hamilton exact")
eq(trip.unit_of("Miles"), "mi", "unit miles")
eq(trip.unit_of("kilometres"), "km", "unit km")

# a cost named after a reserved word's prefix is still a cost, not a leg
eq(go("leg, A, 10 km, Ana\nlegacy, 5, Ana")[0][0][4], 500, "legacy is a cost")
# a person only named on a cost (not a rider, no people line) is still in the split
eq(go("leg, A, 10 km, Ana\nfuel, 10\nfood, 6, Ben")[0],
   [("Ana", 1000, 1000, "km", 1000), ("Ben", 0, 1000, "km", 600)], "named cost adds a person")

cases = {
    "parking, 200, everyone": "no legs listed (write each leg as: leg, label, distance, who)",
    "leg, A, 10 km, Ana": "no costs listed (write a cost as: fuel, amount, or parking, amount, everyone)",
    "leg, A, 10 km, everyone\nfuel, 1": "nobody named (put riders on a leg by name, or add: people, Ana and Ben)",
    "leg, A, 0 km, Ana\nfuel, 1": "line 1: a leg of 0 km isn't a leg: leg, A, 0 km, Ana",
    "leg, A, 0 miles, Ana\nfuel, 1": "line 1: a leg of 0 miles isn't a leg: leg, A, 0 miles, Ana",
    "leg, A, 10 km, Ana\nleg, B, 10 mi, Ana\nfuel, 1":
        "line 2: this leg is in miles but an earlier leg is in km; use one unit for the trip: leg, B, 10 mi, Ana",
    "leg, A, 10 miles, Ana\nleg, B, 10 km, Ana\nfuel, 1":
        "line 2: this leg is in km but an earlier leg is in miles; use one unit for the trip: leg, B, 10 km, Ana",
    "leg, A, 10 km, Ana\nleg, A, 5 km, Ben\nfuel, 1": "line 2: A is already a leg: leg, A, 5 km, Ben",
    "leg, a, 10 km, Ana\nleg, A, 5 km, Ben\nfuel, 1": "line 2: A is already a leg: leg, A, 5 km, Ben",
    "leg, everyone, 10 km, Ana\nfuel, 1": "line 1: pick a label that isn't 'everyone' or a leg number: leg, everyone, 10 km, Ana",
    "leg, leg 1, 10 km, Ana\nfuel, 1": "line 1: pick a label that isn't 'everyone' or a leg number: leg, leg 1, 10 km, Ana",
    "leg, A, 10 km, Ana\nleg, B, 10 km, Ben\ntoll, 5, leg 5":
        "line 3: there is no leg 5 (the trip has 2 legs): toll, 5, leg 5",
    "leg, A, 10 km, Ana\ntoll, 5, leg 0":
        "line 2: there is no leg 0 (the trip has 1 leg): toll, 5, leg 0",
    "leg, A, 10 km, Ana\ntoll, 5, leg Nowhere":
        "line 2: there is no leg called Nowhere: toll, 5, leg Nowhere",
    "leg, A, 10 km, Ana\ntoll, 5": "line 2: say who toll is on: everyone, names, or leg 2: toll, 5",
    "leg, A, 10 km, Ana\nparking, 5": "line 2: say who parking is on: everyone, names, or leg 2: parking, 5",
    "leg, A, 10 km, Ana\nsnack, 5": "line 2: say who snack is on: everyone, names, or leg 2: snack, 5",
    "leg, A, 10 km, Ana\nparking, 5,": "line 2: say who parking is on: everyone, names, or leg 2: parking, 5,",
    "leg, A, 10 km, Ana and ana\nfuel, 1": "line 1: ana is named twice: leg, A, 10 km, Ana and ana",
    "leg, A, 10 km, Ana & ANA\nfuel, 1": "line 1: ANA is named twice: leg, A, 10 km, Ana & ANA",
    "leg, A, 10 km, everyone and Ana\nfuel, 1":
        "line 1: write either everyone or names, not both: leg, A, 10 km, everyone and Ana",
    "leg, A, 10 km, Ana\nfood, 5, Ana and ana": "line 2: ana is named twice: food, 5, Ana and ana",
    "leg, A, 10 km, Ana\nfood, 5, everyone and Ben":
        "line 2: write either everyone or names, not both: food, 5, everyone and Ben",
    "people, Ana\nleg, A, 10 km, Ben\nfuel, 1":
        "line 2: who is Ben? nobody by that name is on the people list: leg, A, 10 km, Ben",
    "people, Ana\nleg, A, 10 km, Ana\nfood, 1, Ben":
        "line 3: who is Ben? nobody by that name is on the people list: food, 1, Ben",
    "leg, A, 10 km, Ana\nfuel, 1\npaid, Bo":
        "who is Bo? nobody by that name is on this trip (add them to a people line if they didn't ride)",
    "leg, A, 10 km, Ana\nfuel, 1%\n": 
        "line 2: write the exact amount, not % (a % of the fuel and a % of a leg are different things): fuel, 1%",
    "leg, A, 10 km, Ana\nfuel, 0": "line 2: a fuel of 0 isn't a cost: fuel, 0",
    "leg, A, 10 km, Ana\nparking, 0, everyone": "line 2: a parking of 0 isn't a cost: parking, 0, everyone",
    "leg, A, 10 km, Ana\nfuel, lots": "line 2: write it as: fuel, amount (or fuel, amount, everyone): fuel, lots",
    "leg, A, 10 km, Ana\nfood, lots, everyone":
        "line 2: write it as: food, amount, everyone (or names, or leg 2): food, lots, everyone",
    "just a name":
        "line 1: write a cost as: fuel, amount, or a cost with who, like: parking, amount, everyone: just a name",
    ", 5":
        "line 1: write a cost as: fuel, amount, or a cost with who, like: parking, amount, everyone: , 5",
    "leg, 10 km, Ana\nfuel, 1":
        "line 1: write it as: leg, label, distance, who, like: leg, Pune to Lonavala, 65 km, Ana and Ben: leg, 10 km, Ana",
    "leg, A, 10, Ana\nfuel, 1":
        "line 1: write it as: leg, label, distance, who, like: leg, Pune to Lonavala, 65 km, Ana and Ben: leg, A, 10, Ana",
    "leg, A, 10 km\nfuel, 1":
        "line 1: write it as: leg, label, distance, who, like: leg, Pune to Lonavala, 65 km, Ana and Ben: leg, A, 10 km",
    "leg, A, 10 km, \nfuel, 1":
        "line 1: write it as: leg, label, distance, who, like: leg, Pune to Lonavala, 65 km, Ana and Ben: leg, A, 10 km,",
    "people, Ana\npeople, Ben\nleg, A, 10 km, Ana\nfuel, 1":
        "line 2: the people line is written twice: people, Ben",
    "people, Ana, ana\nleg, A, 10 km, Ana\nfuel, 1": "line 1: ana is listed twice: people, Ana, ana",
    "people, everyone\nleg, A, 10 km, Ana\nfuel, 1":
        "line 1: list the people by name, not everyone: people, everyone",
    "people,\nleg, A, 10 km, Ana\nfuel, 1":
        "line 1: write people by name, like: people, Ana, Ben and Cy: people,",
    "leg, A, 10 km, Ana\nfuel, 1\npaid, Ana\npaid, Ben":
        "line 4: who paid is written twice: paid, Ben",
    "leg, A, 10 km, Ana\nfuel, 1\npaid, Ana and Ben":
        "line 3: put one person who paid (for several payers, use Settle up): paid, Ana and Ben",
    "leg, A, 10 km, Ana\nfuel, 1\npaid, Ana, Ben":
        "line 3: put one person who paid (for several payers, use Settle up): paid, Ana, Ben",
    "leg, A, 10 km, Ana\nfuel, 1\npaid, everyone":
        "line 3: put one person who paid (for several payers, use Settle up): paid, everyone",
    "leg, , 10 km, Ana\nfuel, 1":
        "line 1: write it as: leg, label, distance, who, like: leg, Pune to Lonavala, 65 km, Ana and Ben: leg, , 10 km, Ana",
    "leg, A, 10 km, Ana\nfuel, 1\npaid,":
        "line 3: write it as: paid, name: paid,",
    "leg, A, 10 km, 123\nfuel, 1":
        "line 1: say who rode this leg: everyone, or names like Ana and Ben: leg, A, 10 km, 123",
}

# over-limit single amount and summed costs
over = "leg, A, 10 km, Ana\nfuel, 100,000,000,000.01"
cases[over] = "line 2: bad amount: 100,000,000,000.01 (that's more than this counts; the most is 100,000,000,000)"
# two costs of 100 billion each: each is at the limit, the sum is over
sum_over = "leg, A, 10 km, Ana\nfuel, 100,000,000,000\nparking, 0.01, Ana"
# 10**13 + 1 > LIMIT
cases[sum_over] = "the costs add up to 100,000,000,000.01, which is more than this counts; the most is 100,000,000,000"

for text, want in cases.items():
    eq(err(lambda t=text: go(t)), want, "refuse %r" % text)

# a 0.01 cost and a 0.01 km leg are accepted (so a == 0 test is not == 1)
eq(go("leg, A, 0.01 km, Ana\nfuel, 0.01")[0][0][4], 1, "one-cent cost, tiny leg")
# leg 1 and leg 2 must point at different legs (so n-1 is not n-2)
eq(go("leg, A, 10 km, Ana\nleg, B, 10 km, Ben\ntoll, 10, leg 1\nparking, 4, leg 2")[0],
   [("Ana", 1000, 2000, "km", 1000), ("Ben", 1000, 2000, "km", 400)], "leg 1 vs leg 2")
# a single-leg trip reports "1 leg" not "1 legs"
eq(err(go, "leg, A, 10 km, Ana\ntoll, 5, leg 2"),
   "line 2: there is no leg 2 (the trip has 1 leg): toll, 5, leg 2", "singular leg")


def exact_of(people_names, legs, costs):
    idx = {p.lower(): i for i, p in enumerate(people_names)}
    n = len(people_names)
    exact = [Fraction(0)] * n
    total_dist = sum(leg[1] for leg in legs)

    def riders(leg):
        if leg[3] == "everyone":
            return list(range(n))
        return [idx[w.lower()] for w in leg[3]]

    for _, c, dest, _, _ in costs:
        typ, arg = dest
        if typ == "distance":
            for leg in legs:
                on = riders(leg)
                part = Fraction(c) * leg[1] / total_dist / len(on)
                for i in on:
                    exact[i] += part
        elif typ == "leg":
            on = riders(legs[arg])
            part = Fraction(c) / len(on)
            for i in on:
                exact[i] += part
        elif typ == "everyone":
            part = Fraction(c) / n
            for i in range(n):
                exact[i] += part
        else:
            on = [idx[w.lower()] for w in arg]
            part = Fraction(c) / len(on)
            for i in on:
                exact[i] += part
    return exact


def check_invariants(text):
    ppl, lgs, cts, pd = trip.parse(text)
    rs, payer = trip.share(ppl, lgs, cts, pd)
    total = sum(c for _, c, _, _, _ in cts)
    eq(sum(r[4] for r in rs), total, "shares sum to total")
    names = [r[0] for r in rs]
    exact = exact_of(names, lgs, cts)
    for r, e in zip(rs, exact):
        assert abs(r[4] - e) < 1, (r, e, text)
        assert int(e) <= r[4] <= int(e) + 1, (r, e, text)
    idx = {p.lower(): i for i, p in enumerate(names)}

    def named_part(i):
        s = Fraction(0)
        for _, c, dest, _, _ in cts:
            if dest[0] == "names":
                on = [idx[w.lower()] for w in dest[1]]
                if i in on:
                    s += Fraction(c) / len(on)
        return s

    def rode_legs(i):
        out = []
        for k, leg in enumerate(lgs):
            riders = list(range(len(names))) if leg[3] == "everyone" else [idx[w.lower()] for w in leg[3]]
            if i in riders:
                out.append(k)
        return tuple(out)

    # someone on no leg pays only everyone / named costs
    for i, r in enumerate(rs):
        if r[1] == 0:
            only = named_part(i)
            for _, c, dest, _, _ in cts:
                if dest[0] == "everyone":
                    only += Fraction(c) / len(names)
            assert abs(r[4] - only) < 1, (r, only, text)

    # people who rode the same legs (equal riding) pay equal ±1, after named costs
    groups = {}
    for i in range(len(names)):
        groups.setdefault(rode_legs(i), []).append(i)
    for members in groups.values():
        leftover = [rs[i][4] - named_part(i) for i in members]
        if len(leftover) >= 2:
            assert max(leftover) - min(leftover) < 2, (leftover, text)
    if payer is not None:
        assert payer in names
    return rs


check_invariants(EX)
check_invariants(EX3)

rng = random.Random(76)
ok_random = 0
random_texts = []
NAMES = ["Ana", "Ben", "Cy", "Dee", "Eve"]
for _ in range(300):
    npeople = rng.randint(2, 5)
    folks = NAMES[:npeople]
    leftover = rng.random() < 0.4  # last person on no named leg
    riders_pool = folks[:-1] if leftover else folks
    lines = []
    use_people = leftover or rng.random() < 0.5
    if use_people:
        lines.append("people, " + ", ".join(folks))
    nlegs = rng.randint(1, 4)
    unit = rng.choice(["km", "mi", "miles", "kilometres", "kms"])
    appeared = set()
    for i in range(nlegs):
        d = rng.choice([1, 2, 5, 8, 10, 13, 20, 50, 65, 85, 100, 150])
        if leftover:
            who_list = [r for r in riders_pool if rng.random() < 0.7] or [riders_pool[0]]
            who = " and ".join(who_list)
            appeared.update(who_list)
        else:
            if use_people and rng.random() < 0.15:
                who = "everyone"
                appeared.update(folks)
            else:
                who_list = [r for r in folks if rng.random() < 0.7] or [folks[0]]
                who = " and ".join(who_list)
                appeared.update(who_list)
        lines.append("leg, L%d, %s %s, %s" % (i + 1, d, unit, who))
    nc = rng.randint(1, 4)
    kinds = ["fuel", "petrol", "diesel", "gas", "charging", "toll", "tolls", "parking", "food", "other"]
    for _c in range(nc):
        kind = rng.choice(kinds)
        a = trip.money(rng.randint(1, 200000))
        if kind.lower() in trip.FUEL:
            if rng.random() < 0.25:
                lines.append("%s, %s, leg %d" % (kind, a, rng.randint(1, nlegs)))
            else:
                lines.append("%s, %s" % (kind, a))
        elif rng.random() < 0.35:
            lines.append("%s, %s, everyone" % (kind, a))
        elif rng.random() < 0.5:
            on = [p for p in (riders_pool if leftover else folks) if rng.random() < 0.6] or [folks[0]]
            joiner = rng.choice([" and ", " & ", " + ", " / "])
            lines.append("%s, %s, %s" % (kind, a, joiner.join(on)))
            appeared.update(on)
        else:
            if rng.random() < 0.5:
                lines.append("%s, %s, leg %d" % (kind, a, rng.randint(1, nlegs)))
            else:
                lines.append("%s, %s, L%d" % (kind, a, rng.randint(1, nlegs)))
    if rng.random() < 0.4:
        known = folks if use_people else sorted(appeared)
        lines.append("paid, " + rng.choice(known))
    text = "\n".join(lines)
    check_invariants(text)
    random_texts.append(text)
    ok_random += 1
assert ok_random == 300, ok_random

with tempfile.TemporaryDirectory() as tmp:
    f = os.path.join(tmp, "t.txt")
    with open(f, "w", encoding="utf-8-sig") as fh:
        fh.write(EX + "\n")
    run = lambda *a: subprocess.run([sys.executable, str(HERE / "trip.py"), *a], capture_output=True, text=True)
    r = run(f)
    eq((r.returncode, r.stdout), (0, "Ana: rode 150 km of 150, pays 826.67 (paid the trip)\n"
                                     "Ben: rode 150 km of 150, pays 826.67\n"
                                     "Cy: rode 65 km of 150, pays 266.66\n"
                                     "Dee: rode 0 km of 150, pays 50\n"
                                     "Trip 1,970 (fuel 1,500, toll 270, parking 200, paid by Ana). "
                                     "Ana 826.67, Ben 826.67, Cy 266.66, Dee 50. "
                                     "Owes Ana: Ben 826.67, Cy 266.66, Dee 50.\n"), "cli")
    with open(f, "w", encoding="utf-8") as fh:
        fh.write("leg, A, 10 km, Ana\nBen, 2\n")
    r = run(f)
    eq((r.returncode, r.stdout),
       (1, "trip: line 2: say who Ben is on: everyone, names, or leg 2: Ben, 2\n"), "cli refuse")
    with open(f, "w", encoding="utf-8") as fh:
        fh.write("leg, A, 10 km, Ana\nfuel, 1\npaid, Bo\n")
    eq(run(f).stdout,
       "trip: who is Bo? nobody by that name is on this trip (add them to a people line if they didn't ride)\n",
       "cli share error")
    eq(run(os.path.join(tmp, "missing")).returncode, 1, "missing file")
    for a in [(), (f, f), ("--help",), ("--",)]:
        r = run(*a)
        eq(r.returncode, 2, "usage %r" % (a,))
        eq(r.stdout, trip.__doc__.split("\n\n", 1)[1].rstrip() + "\n", "usage text %r" % (a,))
        assert "Needs rent.py beside it" in r.stdout, r.stdout
    doc = "\n".join(l.strip() for l in trip.__doc__.split("\n") if l.startswith("          "))
    eq(doc, EX, "docstring example")

page = (HERE / "trip.html").read_text(encoding="utf-8")
eq(page.split('<textarea id="in">', 1)[1].split("</textarea>", 1)[0], EX, "page example")
script = page.split("<script>", 1)[1]
for banned in ["fetch", "XMLHttpRequest", "localStorage", "http"]:
    assert banned not in script, banned
assert "receipt.html" in page and "gift.html" in page and "settle.html" in page, "page links"
node = shutil.which("node")
if not node:
    print("SKIP trip.html: node not installed (trip.py is tested)"); print("ok test_trip (%d random trips)" % ok_random); sys.exit(0)
logic = page.split("// LOGIC START", 1)[1].split("\n", 1)[1].split("// LOGIC END", 1)[0]
js = logic + """
const texts = @TEXTS@, monies = @MONIES@;
const tryit = f => { try { return f(); } catch (e) { return e.message; } };
console.log(JSON.stringify([
  texts.map(t => tryit(() => parse(t))),
  texts.map(t => tryit(() => { const [p,l,c,pd] = parse(t); const [rs, payer] = share(p,l,c,pd); return [rs, payer, rs.map(r => row(...r, payer)), summary(rs, c, payer), summary(rs, c)]; })),
  monies.map(money)]));
"""
texts = list(cases) + [EX, EX3,
    "leg, A to B, 100 km, Ana and Ben\nfuel, 100",
    "leg, Start, 10 km, Ana and Ben\nleg, End, 30 km, Ana\nfuel, 40",
    "leg, A, 1 km, Ana\nleg, B, 1 km, Ben\nleg, C, 1 km, Cy\nfuel, 0.10",
    "people, Ana, Ben, Dee\nleg, Town, 10 km, Ana and Ben\nfuel, 90\nparking, 12, everyone",
    "leg, A, 5 km, Ana and Ben\nparking, 0.01, everyone",
    "leg, West, 20 km, Ana & Ben\nleg, East, 20 km, Ana\npetrol, 10, leg 1\ntoll, 6, East",
    "leg, Coast, 10 miles, Ana and Ben\ndiesel, 8\ncharging, 2, leg Coast",
    "people, Ana, Ben\nleg, A, 10 km, ANA and ben\nfuel, 10\npaid, ana",
    "leg, A, 10 km, Ana\nfuel, 3\nFuel, 2\nfood, 1, Ana\npaid, Ana",
    "\ufeff PEOPLE , Ana, Ben and Cy \nLEG , Highway, ₹1,200 km, Ana + Ben / Cy\nGAS, 2,00,000\npaid, ANA",
    "leg, A, 10 km, Ana\nlegacy, 5, Ana",
    "leg, A, 10 km, Ana\nfuel, 10\nfood, 6, Ben",
    "leg, A, 0.01 km, Ana\nfuel, 0.01",
    "leg, A, 10 km, Ana\nleg, B, 10 km, Ben\ntoll, 10, leg 1\nparking, 4, leg 2",
    "leg, A, 10 km, Ana\ntoll, 5, leg 2",
    "gift\u00a0,\u00a03\x0bleg, A, 10 km, Ana\r\nfuel, 1\u2028paid, Ana",
    "LEG, A, 10 KM, Ana\nFUEL, 5\nPAID, ANA"]
texts += random_texts[:120]
monies = [0, 5, 100, 123456789, 10 ** 13, 999] + [rng.randint(0, 10 ** 13) for _ in range(20)]
r = subprocess.run([node, "-e", js.replace("@TEXTS@", json.dumps(texts)).replace("@MONIES@", json.dumps(monies))],
                   capture_output=True, text=True, timeout=60)
assert r.returncode == 0, r.stderr


def py(f):
    try:
        return f()
    except ValueError as e:
        return str(e)


def full(t):
    ppl, lgs, cts, pd = trip.parse(t)
    rs, payer = trip.share(ppl, lgs, cts, pd)
    return [rs, payer, [trip.row(*x, paid_name=payer) for x in rs], trip.summary(rs, cts, payer), trip.summary(rs, cts)]


want = [[py(lambda t=t: json.loads(json.dumps(trip.parse(t)))) for t in texts],
        [py(lambda t=t: json.loads(json.dumps(full(t)))) for t in texts],
        [trip.money(c) for c in monies]]
got = json.loads(r.stdout)
for i, name in enumerate(["parse", "share", "money"]):
    eq(len(got[i]), len(want[i]), "node %s count" % name)
    for k, (g, w) in enumerate(zip(got[i], want[i])):
        eq(g, w, "node %s %r" % (name, texts[k] if i < 2 else monies[k]))
stub = """
const els = {};
const document = { getElementById: id => els[id] || (els[id] = { value: "", innerHTML: "", addEventListener() {} }),
                   createElement: () => { const d = { set textContent(s) { d.innerHTML = s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); } }; return d; } };
"""
body = page.split("<script>", 1)[1].split("</script>", 1)[0]
r2 = subprocess.run([node, "-e", stub + body.replace("run();\n", "") + """
console.log(JSON.stringify(@INS@.map(t => { els.in.value = t; run(); return els.out.innerHTML; })));
""".replace("@INS@", json.dumps([EX, "leg, A, 10 km, Ana\nparking, 5", "leg, A, 10 km, <a>\nfuel, 1"]))],
                   capture_output=True, text=True, timeout=30)
assert r2.returncode == 0, r2.stderr
shown = json.loads(r2.stdout)
eq(shown[0], "<table>" + "".join("<tr><td>%s</td></tr>" % trip.row(*x, paid_name="Ana") for x in rows) + "</table>"
   '<div class="line">%s</div>' % trip.summary(rows, costs, "Ana"), "page shows the example")
assert shown[1].startswith('<p class="err">line 2: say who parking is on'), shown[1]
assert "&lt;a&gt;" in shown[2] and "<a>" not in shown[2], shown[2]
assert len(texts) >= 150, len(texts)
print("ok test_trip (%d texts, %d random trips)" % (len(texts), ok_random))
