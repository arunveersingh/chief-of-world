#!/usr/bin/env python3
"""Tests for payback.py and the logic inside payback.html (run in node when present).
Copy rent.py, payback.py, payback.html and this file together: payback.py reads
amounts with rent.py's hundredths(), and the last part of this test reads payback.html."""
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
import payback  # noqa: E402


def eq(got, want, what):
    assert got == want, "%s: got %r want %r" % (what, got, want)


def err(fn, *a):
    try:
        fn(*a)
    except ValueError as e:
        return str(e)
    raise AssertionError("no error for %r" % (a,))


# Lumen's example: 5,000 lent, paid 1,000, 600, 1,000
ex = payback.parse("Dec, 1,000\nJan, 600\nFeb, 1,000")
eq(ex, [("Dec", 100000), ("Jan", 60000), ("Feb", 100000)], "parse")
eq(payback.count(500000, ex), [400000, 340000, 240000], "count")
eq(payback.summary(500000, ex), "Paid 1,000 (Dec), 600 (Jan), 1,000 (Feb). Left: 2,400 of 5,000.", "summary")
eq(payback.summary(500000, []), "Nothing paid yet. Left: 5,000 of 5,000.", "nothing paid")
eq(payback.summary(260000, ex), "Paid 1,000 (Dec), 600 (Jan), 1,000 (Feb). Paid back in full: 2,600.", "in full")
eq(payback.count(260000, ex), [160000, 100000, 0], "count to zero")
eq(payback.parse("\ufeff840.50\n\n  12 Jan 2027 , ₹1,234.5 \n2,00,000"), [("", 84050), ("12 Jan 2027", 123450), ("", 20000000)], "no label, dates, lakh")
eq(payback.summary(10 ** 8, [("", 5), ("x, y", 123456)]), "Paid 0.05, 1,234.56 (x, y). Left: 998,765.39 of 1,000,000.", "cents")
for c, want in [(0, "0"), (5, "0.05"), (100, "1"), (123456789, "1,234,567.89"), (100000000, "1,000,000")]:
    eq(payback.money(c), want, "money %d" % c)
eq(payback.plan(500000, 3), [166667, 166667, 166666], "plan")
eq(payback.plan(100, 1), [100], "plan one")
eq(payback.plan(3, 3), [1, 1, 1], "plan cents")
cases = {
    "Dec": "line 1: write it as: when, amount: Dec",
    ", 500": "line 1: write it as: when, amount: , 500",
    "Dec, lots": "line 1: write it as: when, amount: Dec, lots",
    "Dec, -500": "line 1: write it as: when, amount: Dec, -500",
    "Dec 2,000": "line 1: put a comma between when and the amount, like Dec, 2,000: Dec 2,000",
    "Jan 5 2,000": "line 1: put a comma between when and the amount, like Dec, 2,000: Jan 5 2,000",
    "Dec, 0": "line 1: a payment of 0 isn't a payment: Dec, 0",
    "0.00": "line 1: a payment of 0 isn't a payment: 0.00",
    "Dec, 1\nJan, 200000000000": "line 2: write it as: when, amount: Jan, 200000000000",
}
for t, want in cases.items():
    eq(err(payback.parse, t), want, repr(t))
eq(payback.parse("Jan 5, 2,000\nJan 5, 20000"), [("Jan 5", 200000), ("Jan 5", 2000000)], "date then amount")
eq(payback.parse("100000000000"), [("", 10 ** 13)], "the most")
eq(err(payback.amount, "100000000000.01", "amount lent"), "bad amount lent: 100000000000.01 (that's more than this counts; the most is 100,000,000,000)", "too big")
eq(err(payback.count, 200000, ex), "the payments add up to 2,600, which is 600 more than the 2,000 lent", "overpaid")
eq(err(payback.count, 0, []), "nothing was lent (write what was lent, like 5,000)", "nothing lent")
eq(err(payback.plan, 0, 2), "nothing was lent (write what was lent, like 5,000)", "plan nothing")
eq(err(payback.plan, 2, 3), "0.02 can't be split into 3 parts of at least one cent", "plan too fine")
eq(payback.plan(3, 3), [1, 1, 1], "plan exactly cents")

rng = random.Random(72)
for _ in range(400):
    lent = rng.randint(1, 10 ** 9)
    n = rng.randint(1, min(120, lent))
    parts = payback.plan(lent, n)
    eq(sum(parts), lent, "plan sum")
    assert max(parts) - min(parts) <= 1 and parts == sorted(parts, reverse=True), parts
    pays = [("", rng.randint(1, 10 ** 7)) for _ in range(rng.randint(0, 6))]
    paid = sum(c for _, c in pays)
    if paid <= lent:
        after = payback.count(lent, pays)
        eq(after[-1] if after else lent, lent - paid, "left")
    else:
        assert "more than the" in err(payback.count, lent, pays)

with tempfile.TemporaryDirectory() as tmp:
    f = os.path.join(tmp, "p.txt")
    with open(f, "w", encoding="utf-8-sig") as fh:
        fh.write("Dec, 1,000\nJan, 600\n1,000\n")
    run = lambda *a: subprocess.run([sys.executable, str(HERE / "payback.py"), *a], capture_output=True, text=True)
    r = run("5,000", f)
    eq((r.returncode, r.stdout), (0, "Dec: paid 1,000, left 4,000\nJan: paid 600, left 3,400\npayment 3: paid 1,000, left 2,400\n"
                                     "Paid 1,000 (Dec), 600 (Jan), 1,000. Left: 2,400 of 5,000.\n"), "cli")
    eq((run("2,000", f).returncode, run("2,000", f).stdout), (1, "payback: the payments add up to 2,600, which is 600 more than the 2,000 lent\n"), "cli over")
    eq(run("lots", f).stdout, "payback: bad amount lent: lots (write 2400 or 1,850.50)\n", "cli bad lent")
    eq(run("10", os.path.join(tmp, "missing")).returncode, 1, "missing file")
    r = run("5000", "--plan", "3")
    eq((r.returncode, r.stdout), (0, "Part 1 of 3: 1,666.67\nPart 2 of 3: 1,666.67\nPart 3 of 3: 1,666.66\nTogether: 5,000\n"), "cli plan")
    eq(run("5000", "--plan", "120").returncode, 0, "plan 120")
    eq(run("5000", "--plan", " 1 ").stdout, "Part 1 of 1: 5,000\nTogether: 5,000\n", "plan 1")
    eq(run("5000", "--plan", "0").returncode, 1, "plan 0 exit")
    for bad in ["0", "121", "2.5", "x", "1000"]:
        eq(run("5000", "--plan", bad).stdout, "payback: bad number of parts: %s (write a whole number from 1 to 120)\n" % bad, "plan " + bad)
    eq(run("lots", "--plan", "2").stdout, "payback: bad amount lent: lots (write 2400 or 1,850.50)\n", "plan bad lent")
    eq(run("0.01", "--plan", "2").stdout, "payback: 0.01 can't be split into 2 parts of at least one cent\n", "plan fine")
    for a in [("5000",), ("5000", "--plan"), ("5000", "--plna", "3"), ("5000", "--plan", "3", "x"), ("5000", "--x")]:
        r = run(*a)
        eq(r.returncode, 2, "usage %r" % (a,))
        assert r.stdout.startswith("Usage: payback.py"), r.stdout

page = (HERE / "payback.html").read_text(encoding="utf-8")
script = page.split("<script>", 1)[1]
for banned in ["fetch", "XMLHttpRequest", "localStorage", "http"]:
    assert banned not in script, banned
node = shutil.which("node")
if not node:
    print("SKIP payback.html: node not installed (payback.py is tested)"); print("ok test_payback"); sys.exit(0)
logic = page.split("// LOGIC START", 1)[1].split("\n", 1)[1].split("// LOGIC END", 1)[0]
js = logic + """
const texts = @TEXTS@, counts = @COUNTS@, plans = @PLANS@, monies = @MONIES@;
const tryit = f => { try { return f(); } catch (e) { return e.message; } };
console.log(JSON.stringify([
  texts.map(t => tryit(() => parse(t))),
  counts.map(([l, p]) => tryit(() => [count(l, p), summary(l, p)])),
  plans.map(([l, n]) => tryit(() => plan(l, n))),
  monies.map(money),
  ["5,000", "0", "lots", "100000000000.01", "100000000000", " ₹ 2,00,000.5 "].map(t => tryit(() => amount(t, "amount lent")))]));
"""
texts = list(cases) + ["Dec, 1,000\nJan, 600\nFeb, 1,000", "\ufeff840.50\n\n  12 Jan 2027 , ₹1,234.5 \n2,00,000", "a, b, 7",
                       "Jan 5, 2,000\nJan 5, 20000", "100000000000", "Dec\u00a0, 3\x0b4\r\n5\u20286", "1,000 (Dec)", "Dec 12, 345"]
counts = [[500000, [["Dec", 100000], ["Jan", 60000], ["Feb", 100000]]], [500000, []], [260000, [["a", 260000]]],
          [200000, [["", 260000]]], [0, []], [10 ** 8, [["", 5], ["x, y", 123456]]]]
plans = [[500000, 3], [100, 1], [3, 3], [2, 3], [0, 2]]
monies = [0, 5, 100, 123456789, 10 ** 13, 999]
for _ in range(40):
    l = rng.randint(1, 10 ** 10)
    counts.append([l, [[rng.choice(["", "m%d" % i]), rng.randint(1, 10 ** 9)] for i in range(rng.randint(0, 5))]])
    plans.append([l, rng.randint(1, 120)])
    monies.append(rng.randint(0, 10 ** 13))
r = subprocess.run([node, "-e", js.replace("@TEXTS@", json.dumps(texts)).replace("@COUNTS@", json.dumps(counts))
                    .replace("@PLANS@", json.dumps(plans)).replace("@MONIES@", json.dumps(monies))],
                   capture_output=True, text=True, timeout=30)
assert r.returncode == 0, r.stderr


def py(f):
    try:
        return f()
    except ValueError as e:
        return str(e)


want = [[py(lambda t=t: [list(x) for x in payback.parse(t)]) for t in texts],
        [py(lambda l=l, p=p: [payback.count(l, [tuple(x) for x in p]), payback.summary(l, [tuple(x) for x in p])]) for l, p in counts],
        [py(lambda l=l, n=n: payback.plan(l, n)) for l, n in plans],
        [payback.money(c) for c in monies],
        [py(lambda t=t: payback.amount(t, "amount lent")) for t in ["5,000", "0", "lots", "100000000000.01", "100000000000", " ₹ 2,00,000.5 "]]]
got = json.loads(r.stdout)
for i, name in enumerate(["parse", "count", "plan", "money", "amount"]):
    eq(got[i], want[i], "node " + name)
print("ok test_payback")
