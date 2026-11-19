#!/usr/bin/env python3
"""Tests for receipt.py and the logic inside receipt.html (run in node when present).
Copy rent.py, receipt.py, receipt.html and this file together: receipt.py reads
amounts with rent.py's hundredths(), and the last part of this test reads receipt.html."""
import json
import os
import pathlib
import random
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import receipt  # noqa: E402


def eq(got, want, what):
    assert got == want, "%s: got %r want %r" % (what, got, want)


def err(fn, *a):
    try:
        fn(*a)
    except ValueError as e:
        return str(e)
    raise AssertionError("no error for %r" % (a,))


def go(text):
    return receipt.share(*receipt.parse(text))


def shares(text):
    return [r[4] for r in go(text)[0]]


EX = ("Pasta, 450, Ana\nBurger, 380, Ben\nThali, 320, Cy\nWine, 1,200, Ana and Ben\nGarlic bread, 150, everyone\n"
      "tax, 125\ntip, 250, by share\ndelivery fee, 60, evenly\ndiscount, 200, by share\ntotal, 2,735\npaid, Ana")
people, items, adjusts, total, paid = receipt.parse(EX)
eq(people, None, "no people line")
eq([i[:3] for i in items], [("Pasta", 45000, "Ana"), ("Burger", 38000, "Ben"), ("Thali", 32000, "Cy"),
                            ("Wine", 120000, "Ana and Ben"), ("Garlic bread", 15000, "everyone")], "items")
eq([a[:4] for a in adjusts], [("tax", 12500, "by share", False), ("tip", 25000, "by share", False),
                              ("delivery fee", 6000, "evenly", False), ("discount", 20000, "by share", True)], "adjusts")
eq(adjusts[0][4:], (6, "tax, 125"), "adjust line")
eq((total, paid), (273500, "Ana"), "total, paid")
rows, payer = receipt.share(people, items, adjusts, total, paid)
# by hand: items 1,100 / 1,030 / 370 of 2,500; tax+tip 375 by share is 165 / 154.50 / 55.50; delivery 20 each;
# discount 200 by share is 88 / 82.40 / 29.60
eq(rows, [("Ana", 110000, 18500, 8800, 119700), ("Ben", 103000, 17450, 8240, 112210), ("Cy", 37000, 7550, 2960, 41590)], "share")
eq(payer, "Ana", "payer")
eq(receipt.row(*rows[0], paid_name="Ana"), "Ana: items 1,100, added 185, off 88, share 1,197 (paid the bill)", "row payer")
eq(receipt.row(*rows[1], paid_name="Ana"), "Ben: items 1,030, added 174.50, off 82.40, share 1,122.10", "row")
eq(receipt.row("Cy", 500, 0, 0, 500), "Cy: items 5, share 5", "row bare")
eq(receipt.row("Cy", 500, 0, 7, 493), "Cy: items 5, off 0.07, share 4.93", "row off only")
eq(receipt.summary(rows, "Ana"), "Receipt 2,735 (items 2,500, added 435, off 200, paid by Ana). Shares: Ana 1,197, Ben 1,122.10, Cy 415.90. "
                                 "Owes Ana: Ben 1,122.10, Cy 415.90.", "summary")
eq(receipt.summary(rows), "Receipt 2,735 (items 2,500, added 435, off 200). Shares: Ana 1,197, Ben 1,122.10, Cy 415.90.", "summary no payer")
eq(receipt.summary([("Ana", 500, 0, 0, 500)], "Ana"), "Receipt 5 (items 5, paid by Ana). Shares: Ana 5. Nothing owed to Ana.", "nothing owed")
eq(receipt.summary([("Ana", 500, 0, 0, 500), ("Bo", 0, 0, 0, 0)], "Ana"), "Receipt 5 (items 5, paid by Ana). Shares: Ana 5, Bo 0. Nothing owed to Ana.", "zero share owes nothing")
eq(receipt.summary([("Ana", 500, 0, 0, 500), ("Bo", 0, 1, 0, 1)], "Ana"), "Receipt 5.01 (items 5, added 0.01, paid by Ana). Shares: Ana 5, Bo 0.01. Owes Ana: Bo 0.01.", "one cent owed")
eq(go("x, 1, Ana\npaid, ana")[1], "Ana", "paid matched case-blind, written as listed")
eq(go("x, 1, Ana")[1], None, "nobody paid")
for c, want in [(0, "0"), (5, "0.05"), (100, "1"), (123456789, "1,234,567.89"), (10 ** 13, "100,000,000,000")]:
    eq(receipt.money(c), want, "money %d" % c)

# spare cents: items and even splits go to the first in the list; by share to the largest remainder
eq(receipt.even(5, 3), [2, 2, 1], "even")
eq(receipt.even(0, 2), [0, 0], "even zero")
eq(receipt.prop(100, [1, 1, 1]), [34, 33, 33], "prop ties to the first")
eq(receipt.prop(10, [1, 2]), [3, 7], "prop largest remainder")
eq(receipt.prop(2, [1, 1, 1, 1]), [1, 1, 0, 0], "prop two spare")
eq(receipt.prop(7, [0, 3, 4]), [0, 3, 4], "prop zero weight")
eq(receipt.prop(1, [5, 0, 6]), [0, 0, 1], "prop one cent to the larger")
eq(receipt.prop(0, [1, 2]), [0, 0], "prop nothing")
eq(receipt.prop(3, [1, 1, 2, 2]), [1, 0, 1, 1], "prop spare by remainder then order")
eq(go("a, 0.05, Cy and Ana\nb, 1, Ben")[0], [("Cy", 3, 0, 0, 3), ("Ana", 2, 0, 0, 2), ("Ben", 100, 0, 0, 100)], "no people line: order of first mention")
eq(shares("people, Ana, Ben, Cy\na, 0.05, Cy and Ana"), [3, 0, 2], "item spare cents to the first on the people line, not the item line")
eq(shares("people, Ana, Ben\na, 0.03, ALL of us"), [2, 1], "all of us")
eq(shares("a, 0.03, everyone\nb, 1, Ben"), [103], "everyone is everyone named anywhere")
eq(shares("people, Ana, Ben, Cy\na, 0.05, everyone"), [2, 2, 1], "everyone on the people line")
eq(shares("a, 0.03, ben & cy + ana"), [1, 1, 1], "& and +")
eq(shares("a, 0.03, Ben/Ana"), [2, 1], "slash")
eq(go("a, 1, Ana\nb, 3, Ben\ntip, 0.03, evenly\nfee, 0.01, by share")[0], [("Ana", 100, 2, 0, 102), ("Ben", 300, 2, 0, 302)],
   "even spare to the first, by-share cent to the larger remainder")
eq(receipt.parse("\ufeff  Tea , ₹1,234.5 , Ben \nPEOPLE , ana &  Ben/Zoë\nTip , 1, BY   Share\nService  Charge, 2, Evenly\nDelivery, 3, evenly\n"
                 "service fee, 4, by share\nservice, 5, by share\nfee,6,evenly\ntax, 1,000\nTAX, 7, EVENLY\nTotal , 2,00,000\nPaid ,  Zoë "),
   (["ana", "Ben", "Zoë"], [("Tea", 123450, "Ben", 1, "Tea , ₹1,234.5 , Ben")],
    [("tip", 100, "by share", False, 3, "Tip , 1, BY   Share"), ("service charge", 200, "evenly", False, 4, "Service  Charge, 2, Evenly"),
     ("delivery", 300, "evenly", False, 5, "Delivery, 3, evenly"), ("service fee", 400, "by share", False, 6, "service fee, 4, by share"),
     ("service", 500, "by share", False, 7, "service, 5, by share"), ("fee", 600, "evenly", False, 8, "fee,6,evenly"),
     ("tax", 100000, "by share", False, 9, "tax, 1,000"), ("tax", 700, "evenly", False, 10, "TAX, 7, EVENLY")], 20000000, "Zoë"),
   "spaces, case, lakh, every kind")
eq(receipt.parse("Tip jar, 5, Ana\nTaxi, 3, everyone\nfees, 2, Ana\npeoples, 1, Ana\ntotally, 1, Ana and Ben")[1:3],
   ([("Tip jar", 500, "Ana", 1, "Tip jar, 5, Ana"), ("Taxi", 300, "everyone", 2, "Taxi, 3, everyone"), ("fees", 200, "Ana", 3, "fees, 2, Ana"),
     ("peoples", 100, "Ana", 4, "peoples, 1, Ana"), ("totally", 100, "Ana and Ben", 5, "totally, 1, Ana and Ben")], []), "only the bare keyword is bill-wide")
eq(receipt.parse("a, 100000000000, Ana")[1][0][1], 10 ** 13, "the most")
eq(receipt.parse("x, 1, Ann Andrews\ny, 2, Dand")[1][1][2], "Dand", "and only as a word")
L = "line 1: "
cases = {
    "Pasta": L + "write an item as: what, amount, who: Pasta",
    ", 5, Ana": L + "write an item as: what, amount, who: , 5, Ana",
    "Pasta, 450": L + "say who this item is on: everyone, or names like Ben and Cy: Pasta, 450",
    "Pasta, 1,000": L + "say who this item is on: everyone, or names like Ben and Cy: Pasta, 1,000",
    "Pasta, Ana": L + "say who this item is on: everyone, or names like Ben and Cy: Pasta, Ana",
    "Pasta, 4, 5": L + "say who this item is on: everyone, or names like Ben and Cy: Pasta, 4, 5",
    "Pasta, lots, Ana": L + "write an item as: what, amount, who (use 'and' between names): Pasta, lots, Ana",
    "Pasta, 3, Ana, Ben": L + "write an item as: what, amount, who (use 'and' between names): Pasta, 3, Ana, Ben",
    "Pasta, , Ana": L + "write an item as: what, amount, who (use 'and' between names): Pasta, , Ana",
    "Pasta, 100000000000.01, Ana": L + "write an item as: what, amount, who (use 'and' between names): Pasta, 100000000000.01, Ana",
    "Pasta, 0, Ana": L + "an item of 0 isn't a cost: Pasta, 0, Ana",
    "Pasta, 3, Ana &": L + "say who this item is on: everyone, or names like Ben and Cy: Pasta, 3, Ana &",
    "Pasta, 3, Ana and 7": L + "say who this item is on: everyone, or names like Ben and Cy: Pasta, 3, Ana and 7",
    "Pasta, 3, Ana & & Ben": L + "say who this item is on: everyone, or names like Ben and Cy: Pasta, 3, Ana & & Ben",
    "Pasta, 3, Ana and everyone": L + "write either everyone or names, not both: Pasta, 3, Ana and everyone",
    "Pasta, 3, all of us & Ben": L + "write either everyone or names, not both: Pasta, 3, all of us & Ben",
    "a, 1, Ana\npeople, Ana\npeople, Ana": "line 3: the people line is written twice: people, Ana",
    "people,": L + "write people by name, like: people, Ana, Ben and Cy: people,",
    "people, Ana,, Ben": L + "write people by name, like: people, Ana, Ben and Cy: people, Ana,, Ben",
    "people, Ana, 7": L + "write people by name, like: people, Ana, Ben and Cy: people, Ana, 7",
    "people, Ana and everyone": L + "list the people by name, not everyone: people, Ana and everyone",
    "people, All Of Us": L + "list the people by name, not All Of Us: people, All Of Us",
    "people, Ana, Ben & ana": L + "ana is listed twice: people, Ana, Ben & ana",
    "total, 5\ntotal, 5": "line 2: the total is written twice: total, 5",
    "total, lots": L + "write it as: total, amount: total, lots",
    "total, 100000000000.01": L + "write it as: total, amount: total, 100000000000.01",
    "paid, Ana\npaid, Ana": "line 2: who paid is written twice: paid, Ana",
    "paid, Ana, Ben": L + "put one person who paid (for several payers, use Settle up): paid, Ana, Ben",
    "paid, Ana and Ben": L + "put one person who paid (for several payers, use Settle up): paid, Ana and Ben",
    "paid, Ana+Ben": L + "put one person who paid (for several payers, use Settle up): paid, Ana+Ben",
    "paid, Everyone": L + "put one person who paid (for several payers, use Settle up): paid, Everyone",
    "paid,": L + "write it as: paid, name: paid,",
    "paid, 42": L + "write it as: paid, name: paid, 42",
    "tax, 10%": L + "write the exact amount from the receipt, not % (people argue over pre-tax vs post-tax %): tax, 10%",
    "tip, 15 %, by share": L + "write the exact amount from the receipt, not % (people argue over pre-tax vs post-tax %): tip, 15 %, by share",
    "service charge, 10%": L + "write the exact amount from the receipt, not % (people argue over pre-tax vs post-tax %): service charge, 10%",
    "tax, 5, somehow": L + 'say how to split tax: write "by share" or "evenly": tax, 5, somehow',
    "tax, 5, by shares": L + 'say how to split tax: write "by share" or "evenly": tax, 5, by shares',
    "tax, lots": L + "write it as: tax, amount, by share (or evenly): tax, lots",
    "tax, 1,00": L + "write it as: tax, amount, by share (or evenly): tax, 1,00",
    "tax, 0": L + "a tax of 0 changes nothing: tax, 0",
    "tax, 0.00, evenly": L + "a tax of 0 changes nothing: tax, 0.00, evenly",
    "tip, 250": L + 'say how to split tip: add ", by share" (with each person\'s items) or ", evenly" (same for everyone): tip, 250',
    "tip, 1,000": L + 'say how to split tip: add ", by share" (with each person\'s items) or ", evenly" (same for everyone): tip, 1,000',
    "tip, 250, Ana": L + 'say how to split tip: add ", by share" (with each person\'s items) or ", evenly" (same for everyone): tip, 250, Ana',
    "Delivery Fee, 60, even": L + 'say how to split delivery fee: add ", by share" (with each person\'s items) or ", evenly" (same for everyone): Delivery Fee, 60, even',
    "discount, 100": L + 'say how to split discount: add ", by share" (with each person\'s items) or ", evenly" (same for everyone): discount, 100',
    "tip, lots, evenly": L + "write it as: tip, amount, by share (or evenly): tip, lots, evenly",
    "fee, , evenly": L + "write it as: fee, amount, by share (or evenly): fee, , evenly",
    "service fee, 100000000000.01, evenly": L + "write it as: service fee, amount, by share (or evenly): service fee, 100000000000.01, evenly",
    "tip, 0, by share": L + "a tip of 0 changes nothing: tip, 0, by share",
    "discount, 0, evenly": L + "a discount of 0 changes nothing: discount, 0, evenly",
    "a, 1, Ana\n\nb, 2": "line 3: say who this item is on: everyone, or names like Ben and Cy: b, 2",
}
for t, want in cases.items():
    eq(err(receipt.parse, t), want, repr(t))
eq(receipt.parse("tip, 1,000, by share\ndiscount, 1,000.50, evenly\ntax, 1,000, evenly")[2],
   [("tip", 100000, "by share", False, 1, "tip, 1,000, by share"), ("discount", 100050, "evenly", True, 2, "discount, 1,000.50, evenly"),
    ("tax", 100000, "evenly", False, 3, "tax, 1,000, evenly")], "thousands and a mode")
refusals = {
    "": "no items listed (write each item as: what, amount, who)",
    "tax, 5\ntotal, 5\npeople, Ana": "no items listed (write each item as: what, amount, who)",
    "a, 5, everyone\nb, 1, all of us": "nobody named (put at least one item on a person's name, or add: people, Ana and Ben)",
    "people, Ana\na, 1, Bo": "line 2: who is Bo? nobody by that name is on the people list: a, 1, Bo",
    "people, Ana, Ben\na, 1, Ben and Bo": "line 2: who is Bo? nobody by that name is on the people list: a, 1, Ben and Bo",
    "people, Ana\na, 1, Ana and ana": "line 2: ana is named twice: a, 1, Ana and ana",
    "a, 1, Ana and ana": "line 1: ana is named twice: a, 1, Ana and ana",
    "b, 1, Ben\na, 1, Ana & Ben + ana": "line 2: ana is named twice: a, 1, Ana & Ben + ana",
    "a, 1, Ana\npaid, Bo": "who is Bo? nobody by that name is on the receipt (add them to a people line if they didn't order anything)",
    "people, Ana\na, 1, Ana\npaid, Bo": "who is Bo? nobody by that name is on the receipt (add them to a people line if they didn't order anything)",
    "a, 10, Ana\ndiscount, 10.01, by share": "discounts add up to 10.01, more than the 10 bill",
    "a, 10, Ana\ntip, 1, evenly\ndiscount, 6, by share\ndiscount, 5.01, evenly": "discounts add up to 11.01, more than the 11 bill",
    "a, 10, Ana\nb, 1, Ben\ndiscount, 4, evenly": "discount leaves Ben below zero (-1): split the discount by share instead of evenly",
    "a, 1, Ana\nb, 1, Ben\nc, 10, Cy\ndiscount, 3.50, evenly": "discount leaves Ana below zero (-0.17): split the discount by share instead of evenly",
    "people, Ana, Bo\na, 10, Ana\ndiscount, 0.03, evenly": "discount leaves Bo below zero (-0.01): split the discount by share instead of evenly",
    "a, 10, Ana\ntax, 1\ntotal, 11.01": "receipt says total 11.01, but lines add up to 11: 0.01 is missing (an item, tax, or tip?)",
    "a, 10, Ana\ntotal, 0": "receipt says total 0, which is 10 less than the 10 from the lines: is a discount missing or an item counted twice?",
    "a, 10, Ana\ndiscount, 1, by share\ntotal, 9.50": "receipt says total 9.50, but lines add up to 9: 0.50 is missing (an item, tax, or tip?)",
}
for t, want in refusals.items():
    eq(err(go, t), want, repr(t))
# what does add up
eq(go("people, Ana, Bo\na, 10, Ana\ntip, 2, evenly\ndiscount, 1, evenly\ntotal, 11\npaid, BO")[0],
   [("Ana", 1000, 100, 50, 1050), ("Bo", 0, 100, 50, 50)], "someone who had nothing still pays an even fee")
eq(go("people, Ana, Bo\na, 10, Ana\ntip, 2, evenly\ndiscount, 1, evenly\ntotal, 11\npaid, BO")[1], "Bo", "payer on the people line")
eq(shares("people, Ana, Bo\na, 10, Ana\ntax, 2\ntip, 1, by share"), [1300, 0], "by share skips who had nothing")
eq(shares("a, 10, Ana\nb, 1, Ben\ndiscount, 2, evenly"), [900, 0], "even discount down to exactly zero")
eq(shares("a, 10, Ana\ndiscount, 10, by share\ntotal, 0"), [0], "discount covers the whole bill")
eq(shares("a, 10, Ana\nb, 30, Ben\ndiscount, 4, by share\ntotal, 36"), [900, 2700], "by share discount")
eq(go("a, 10, Ana\nb, 30, Ben\ndiscount, 4, by share")[0], [("Ana", 1000, 0, 100, 900), ("Ben", 3000, 0, 300, 2700)], "off rows")
eq(shares("a, 10, Ana\ntax, 1\ntotal, 11"), [1100], "total matches")
eq(shares("a, 0.01, Ana\nb, 0.01, Ben\ntip, 0.01, by share"), [2, 1], "one cent by share to the first on a tie")
eq(shares("a, 0.01, Ana\nb, 0.02, Ben\ntip, 0.01, by share"), [1, 3], "one cent by share to the larger")
eq(receipt.share(["A", "B"], [("x", 1, "A", 1, "x")], [("tip", 1, "by share", False, 2, "t"), ("tip", 2, "by share", False, 3, "t")])[0],
   [("A", 1, 3, 0, 4), ("B", 0, 0, 0, 0)], "share() with a people list, by-share adds summed")
# 1e13 exact: the page must use BigInt for this
big = "a, 99999999999.99, Ana\nb, 0.01, Ben\nc, 0.01, Cy\ntip, 100000000000, by share\ndiscount, 99999999999.99, by share"
eq(go(big)[0], [("Ana", 9999999999999, 9999999999998, 9999999999997, 10000000000000), ("Ben", 1, 1, 1, 1), ("Cy", 1, 1, 1, 1)], "big by share")
eq(receipt.prop(10 ** 13, [10 ** 13 - 7, 3, 4]), [9999999999993, 3, 4], "big prop exact")
eq(receipt.prop(10 ** 13 - 1, [3333333333333, 3333333333333, 3333333333334]), [3333333333333, 3333333333333, 3333333333333], "big prop remainders")

rng = random.Random(74)


def random_receipt(r, big=False):
    n = r.randint(1, 7)
    names = ["P%d" % i for i in range(n)]
    lines, named = [], []
    top = 10 ** 13 if big else 10 ** 6
    for k in range(r.randint(1, 6)):
        on = r.sample(names, r.randint(1, n))
        who = "everyone" if r.random() < .3 else " and ".join(on)
        named += [] if who == "everyone" else [w for w in on if w not in named]
        lines.append("item%d, %s, %s" % (k, receipt.money(r.randint(1, top)), who))
    if r.random() < .4 or not named:
        lines.append("people, " + ", ".join(names))
        named = names
    for kind in r.sample(["tax", "tip", "service charge", "delivery fee", "fee", "discount", "discount"], r.randint(0, 4)):
        mode = r.choice(["by share", "evenly"]) if kind != "tax" or r.random() < .5 else None
        c = r.randint(1, top // 3 if kind == "discount" else top)
        lines.append("%s, %s" % (kind, receipt.money(c)) + (", " + mode if mode else ""))
    if r.random() < .3:
        lines.append("paid, " + r.choice(named).lower())
    r.shuffle(lines)
    return "\n".join(lines)


for _ in range(300):
    t = random_receipt(rng, big=rng.random() < .2)
    ppl, its, adj, tot, pd = receipt.parse(t)
    try:
        rs, payer = receipt.share(ppl, its, adj, tot, pd)
    except ValueError as e:
        assert str(e).startswith(("discount leaves", "discounts add up")), (t, e)
        continue
    cents = lambda off, mode=None: sum(c for _, c, m, o, _, _ in adj if o == off and mode in (None, m))
    eq(sum(r[1] for r in rs), sum(c for _, c, _, _, _ in its), "items add up")
    eq(sum(r[2] for r in rs), cents(False), "added adds up")
    eq(sum(r[3] for r in rs), cents(True), "off adds up")
    grand = sum(r[4] for r in rs)
    eq(grand, sum(c for _, c, _, _, _ in its) + cents(False) - cents(True), "grand")
    assert all(r[4] >= 0 for r in rs), rs
    assert all(r[1] + r[2] - r[3] == r[4] for r in rs), rs
    eq(len(set(r[0].lower() for r in rs)), len(rs), "each person once")
    items_all = [r[1] for r in rs]
    for mode_off in [False, True]:
        amt = cents(mode_off, "by share")
        got = receipt.prop(amt, items_all)
        for g, w in zip(got, items_all):
            assert amt * w // sum(items_all) <= g <= -(-amt * w // sum(items_all)), (amt, items_all, got)
    eq(receipt.share(ppl, its, adj, grand, pd)[0], rs, "the right total is accepted")
    assert "is missing" in err(receipt.share, ppl, its, adj, grand + 1, pd)
    if grand:
        assert "less than the" in err(receipt.share, ppl, its, adj, grand - 1, pd)
    if payer is not None:
        assert payer.lower() == pd.lower() and payer in [r[0] for r in rs]
        s = receipt.summary(rs, payer)
        assert ("Owes %s:" % payer in s) == any(r[4] > 0 and r[0] != payer for r in rs), s

with tempfile.TemporaryDirectory() as tmp:
    f = os.path.join(tmp, "r.txt")
    with open(f, "w", encoding="utf-8-sig") as fh:
        fh.write(EX + "\n")
    run = lambda *a: subprocess.run([sys.executable, str(HERE / "receipt.py"), *a], capture_output=True, text=True)
    r = run(f)
    eq((r.returncode, r.stdout), (0, "Ana: items 1,100, added 185, off 88, share 1,197 (paid the bill)\n"
                                     "Ben: items 1,030, added 174.50, off 82.40, share 1,122.10\n"
                                     "Cy: items 370, added 75.50, off 29.60, share 415.90\n"
                                     "Receipt 2,735 (items 2,500, added 435, off 200, paid by Ana). Shares: Ana 1,197, Ben 1,122.10, Cy 415.90. "
                                     "Owes Ana: Ben 1,122.10, Cy 415.90.\n"), "cli")
    with open(f, "w", encoding="utf-8") as fh:
        fh.write("a, 5, Ana\nb, 2, Ben\n")
    eq(run(f).stdout, "Ana: items 5, share 5\nBen: items 2, share 2\nReceipt 7 (items 7). Shares: Ana 5, Ben 2.\n", "cli no payer")
    with open(f, "w", encoding="utf-8") as fh:
        fh.write("a, 5, Ana\ntip, 1\n")
    r = run(f)
    eq((r.returncode, r.stdout), (1, 'receipt: line 2: say how to split tip: add ", by share" (with each person\'s items) or ", evenly" (same for everyone): tip, 1\n'), "cli refuse")
    with open(f, "w", encoding="utf-8") as fh:
        fh.write("a, 5, Ana\ntotal, 6\n")
    eq(run(f).stdout, "receipt: receipt says total 6, but lines add up to 5: 1 is missing (an item, tax, or tip?)\n", "cli share error")
    eq(run(os.path.join(tmp, "missing")).returncode, 1, "missing file")
    for a in [(), (f, f), ("--help",), ("--",)]:
        r = run(*a)
        eq(r.returncode, 2, "usage %r" % (a,))
        assert r.stdout.startswith("Usage: receipt.py"), r.stdout
    # the docstring's example is the page's example, and it adds up
    doc = "\n".join(l.strip() for l in receipt.__doc__.split("\n") if l.startswith("          "))
    eq(doc, EX, "docstring example")

page = (HERE / "receipt.html").read_text(encoding="utf-8")
eq(page.split('<textarea id="in">', 1)[1].split("</textarea>", 1)[0], EX, "page example")
script = page.split("<script>", 1)[1]
for banned in ["fetch", "XMLHttpRequest", "localStorage", "http"]:
    assert banned not in script, banned
node = shutil.which("node")
if not node:
    print("SKIP receipt.html: node not installed (receipt.py is tested)"); print("ok test_receipt"); sys.exit(0)
logic = page.split("// LOGIC START", 1)[1].split("\n", 1)[1].split("// LOGIC END", 1)[0]
js = logic + """
const texts = @TEXTS@, monies = @MONIES@, props = @PROPS@;
const tryit = f => { try { return f(); } catch (e) { return e.message; } };
console.log(JSON.stringify([
  texts.map(t => tryit(() => parse(t))),
  texts.map(t => tryit(() => { const [rs, payer] = share(...parse(t)); return [rs, payer, rs.map(r => row(...r, payer)), summary(rs, payer), summary(rs)]; })),
  monies.map(money),
  props.map(([a, w]) => prop(a, w))]));
"""
texts = list(cases) + list(refusals) + [EX, big, "a, 0.05, Cy and Ana\nb, 1, Ben", "people, Ana, Ben, Cy\na, 0.05, Cy and Ana",
    "people, Ana, Bo\na, 10, Ana\ntip, 2, evenly\ndiscount, 1, evenly\ntotal, 11\npaid, BO", "a, 10, Ana\nb, 1, Ben\ndiscount, 2, evenly",
    "a, 1, Ana\nb, 3, Ben\ntip, 0.03, evenly\nfee, 0.01, by share", "tip, 1,000, by share\ndiscount, 1,000.50, evenly\ntax, 1,000, evenly",
    "\ufeff  Tea , ₹1,234.5 , Ben \nPEOPLE , ana &  Ben/Zoë\nTip , 1, BY   Share\nService  Charge, 2, Evenly\nDelivery, 3, evenly\n"
    "service fee, 4, by share\nservice, 5, by share\nfee,6,evenly\ntax, 1,000\nTAX, 7, EVENLY\nTotal , 2,00,000\nPaid ,  Zoë ",
    "Tip jar, 5, Ana\nTaxi, 3, everyone\nfees, 2, Ana\npeoples, 1, Ana\ntotally, 1, Ana and Ben", "x, 1, Ann Andrews\ny, 2, Dand",
    "a\u00a0, 3, Ana\x0bb, 4, Ben\r\nc, 5, Ana\u20286, 1, Cy\x85tip, 1, by\tshare", "a, 1, Zoë\nb, 1, ZOË", "a, 1, Ana\tand\tBen",
    "a, 1, ²", "a, 1, Ana and ²", "paid, Ana\u00a0and Ben\na, 1, Ana", "people, Ana, Ben\na, 1, ana\npaid, BEN", "a, 1, Ana\ntax, 1, evenly ",
    "a, 1, Ana\ntax , 5 , by share", "a, 1, Ana\ntip,5,by\u00a0share", "a, 1, Ana\ntax, ٥", "a, 1, Ana\nDISCOUNT, 1, Evenly", "a, 1, Ana\nservice\tfee\t, 1, evenly"]
texts += [random_receipt(rng, big=rng.random() < .3) for _ in range(60)]
texts += ["\n".join(random_receipt(rng).split("\n") + ["total, %s" % receipt.money(rng.randint(0, 10 ** 7))]) for _ in range(20)]
monies = [0, 5, 100, 123456789, 10 ** 13, 999] + [rng.randint(0, 10 ** 13) for _ in range(20)]
props = [[10 ** 13, [10 ** 13 - 7, 3, 4]], [10 ** 13 - 1, [3333333333333, 3333333333333, 3333333333334]], [3, [1, 1, 2, 2]], [7, [0, 3, 4]]]
props += [[rng.randint(0, 10 ** 13), [rng.randint(0, 10 ** 13) for _ in range(rng.randint(1, 6))]] for _ in range(60)]
props = [[a, w] for a, w in props if sum(w)]
r = subprocess.run([node, "-e", js.replace("@TEXTS@", json.dumps(texts)).replace("@MONIES@", json.dumps(monies)).replace("@PROPS@", json.dumps(props))],
                   capture_output=True, text=True, timeout=30)
assert r.returncode == 0, r.stderr


def py(f):
    try:
        return f()
    except ValueError as e:
        return str(e)


def full(t):
    rs, payer = receipt.share(*receipt.parse(t))
    return [rs, payer, [receipt.row(*x, paid_name=payer) for x in rs], receipt.summary(rs, payer), receipt.summary(rs)]


want = [[py(lambda t=t: json.loads(json.dumps(receipt.parse(t)))) for t in texts],
        [py(lambda t=t: json.loads(json.dumps(full(t)))) for t in texts],
        [receipt.money(c) for c in monies],
        [receipt.prop(a, w) for a, w in props]]
got = json.loads(r.stdout)
for i, name in enumerate(["parse", "share", "money", "prop"]):
    eq(len(got[i]), len(want[i]), "node %s count" % name)
    for k, (g, w) in enumerate(zip(got[i], want[i])):
        eq(g, w, "node %s %r" % (name, texts[k] if i < 2 else k))
# the whole page in node with a stub document: the example shows the same lines as receipt.py
stub = """
const els = {};
const document = { getElementById: id => els[id] || (els[id] = { value: "", innerHTML: "", addEventListener() {} }),
                   createElement: () => { const d = { set textContent(s) { d.innerHTML = s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); } }; return d; } };
"""
body = page.split("<script>", 1)[1].split("</script>", 1)[0]
r2 = subprocess.run([node, "-e", stub + body.replace("run();\n", "") + """
console.log(JSON.stringify(@INS@.map(t => { els.in.value = t; run(); return els.out.innerHTML; })));
""".replace("@INS@", json.dumps([EX, "a, 1, Ana\ntip, 1", "a, 1, <b>"]))], capture_output=True, text=True, timeout=30)
assert r2.returncode == 0, r2.stderr
shown = json.loads(r2.stdout)
eq(shown[0], "<table>" + "".join("<tr><td>%s</td></tr>" % receipt.row(*x, paid_name="Ana") for x in rows) + "</table>"
   '<div class="line">%s</div>' % receipt.summary(rows, "Ana"), "page shows the example")
assert shown[1].startswith('<p class="err">line 2: say how to split tip'), shown[1]
assert "&lt;b&gt;" in shown[2] and "<b>" not in shown[2], shown[2]
assert len(texts) >= 80 + 80, len(texts)
assert sum(isinstance(w, list) for w in want[1]) >= 60, "too few receipts that add up"
print("ok test_receipt (%d texts, %d proportional splits checked against the page)" % (len(texts), len(props)))
