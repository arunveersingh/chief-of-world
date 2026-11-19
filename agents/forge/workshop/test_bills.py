#!/usr/bin/env python3
"""Tests for bills.py and the logic inside bills.html (run in node when present).
Copy rent.py, bills.py, bills.html and this file together: bills.py reads amounts
with rent.py's hundredths(), and the last part of this test reads bills.html."""
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
import bills  # noqa: E402

F = "day 1 is the bill's first day, not the 1st of the month"


def eq(got, want, what):
    assert got == want, "%s: got %r want %r" % (what, got, want)


def err(fn, *a):
    try:
        fn(*a)
    except ValueError as e:
        return str(e)
    raise AssertionError("no error for %r" % (a,))


# the page example: 3,120 over 30 days, Asha all month, Ben 12 days, Cy away
ex = bills.split(312000, bills.parse("Asha\nBen, 12 days\nCy, 0", 30))
eq(ex, {"Asha": 222858, "Ben": 89142, "Cy": 0}, "page example")
eq(bills.split(10000, [("Asha", 30), ("Ben", 12), ("Cy", 0)]), {"Asha": 7143, "Ben": 2857, "Cy": 0}, "spare cent")
eq(bills.split(100, [("b", 1), ("a", 1), ("c", 1)]), {"a": 34, "b": 33, "c": 33}, "alphabetical spare")
eq(bills.split(2, [("z", 0), ("a", 5), ("b", 5)]), {"z": 0, "a": 1, "b": 1}, "nobody with 0 days gets a cent")
eq(bills.split(1, [("z", 0), ("b", 5), ("a", 5)]), {"z": 0, "b": 0, "a": 1}, "one cent")
eq(err(bills.split, 100, [("a", 0)]), "nobody was there for any days", "all away")
eq(bills.parse("Ann, 12 days\nBo, 1 day\nCy,3days\nDi, 0\nEd, 0 days", 30), [("Ann", 12), ("Bo", 1), ("Cy", 3), ("Di", 0), ("Ed", 0)], "day words")
eq(bills.parse("\ufeffAnn\n\n  Bo  ", 92), [("Ann", 92), ("Bo", 92)], "whole period")
cases = {
    "Ann, 31": "line 1: Ann was there 31 days but the bill covers 30",
    "Ann, 1 day\nann, 2 days": "line 2: ann is listed twice",
    "12, 4": "line 1: 12 looks like a number, not a name",
    ", 4": "line 1: write it as: name, days: , 4",
    "Ann, 1.5": "line 1: bad days: 1.5 (write a whole number of days, like 12 days)",
    "Ann, 12, 3": "line 1: bad days: 12, 3 (write a whole number of days, like 12 days)",
    "Ann, half": "line 1: bad days: half (write a whole number of days, like 12 days)",
    "Ann, -3": "line 1: bad days: -3 (write a whole number of days, like 12 days)",
    "Ann, day": "line 1: bad days: day (write a whole number of days, like 12 days)",
    "Ann, days 3 days": "line 1: bad stretch: 3 days (write days like 1-10, 21-30, or day 15)",
    "": "nobody listed",
}
# the fixed part: split evenly among everyone listed, even the away flatmate
eq(bills.split(312000, [("Asha", 30), ("Ben", 12), ("Cy", 0)], 60000), {"Asha": 200000, "Ben": 92000, "Cy": 20000}, "fixed")
eq(bills.split(100000, [("Asha", 30), ("Ben", 12), ("Cy", 0)], 100000), {"Asha": 33334, "Ben": 33333, "Cy": 33333}, "all fixed")
eq(bills.split(500, [("c", 0), ("b", 0), ("a", 0)], 500), {"a": 167, "b": 167, "c": 166}, "all away, all fixed")
eq(bills.split(10, [("b", 0), ("a", 3), ("c", 3)], 4), {"a": 5, "b": 1, "c": 4}, "fixed spare to anyone, use spare to present")
eq(bills.split(312000, [("Asha", 30), ("Ben", 12), ("Cy", 0)], 0), ex, "fixed 0 is the old split")
eq(err(bills.split, 100, [("a", 1)], 101), "the fixed part is more than the whole bill", "fixed over")
eq(err(bills.split, 100, [("a", 0)], 99), "nobody was there for any days", "away with usage left")
# stretches: someone away in the middle, or out and back in
eq(bills.parse("Di, 1-10, 21-30\nEd, 5 to 5 and 7–8\nFi, 21-30, 1-10", 30), [("Di", 20), ("Ed", 3), ("Fi", 20)], "stretches")
eq(bills.parse("Di, 1-30", 30), [("Di", 30)], "whole stretch")
# Wry's tick-70 break: a lone day, phone dashes, and day words before stretches
eq(bills.parse("Di, day 15\nEd, 1-10, 12\nFi, Day 3 and 5\nGo, days 1-10, 21-30", 30), [("Di", 1), ("Ed", 11), ("Fi", 2), ("Go", 20)], "lone days")
eq(bills.parse("Di, 1\u201410, 21\u201430\nEd, 1\u221210\nFi, 1\u201110\nGu, 1\u20122", 30), [("Di", 20), ("Ed", 10), ("Fi", 10), ("Gu", 2)], "phone dashes")
eq(bills.split(300000, bills.parse("Asha\nDi, day 15", 30)), {"Asha": 290323, "Di": 9677}, "one night")
eq(bills.split(300000, bills.parse("Ann, 1-10\nBo, 10-30", 30)), {"Ann": 96775, "Bo": 203225}, "moving day counts for both")
cases.update({
    "Di, 1-10, 21-31": "line 1: 21-31 runs past day 30, the last day of the bill (%s)" % F,
    "Di, 12-31": "line 1: 12-31 runs past day 30, the last day of the bill (%s)" % F,
    "Di, day 31": "line 1: 31 runs past day 30, the last day of the bill (%s)" % F,
    "Di, day 0": "line 1: bad stretch: 0 (%s, and the first day comes first)" % F,
    "Di, 15": "line 1: Di, 15 could mean 15 days or only day 15 (write 15 days, or day 15)",
    "Di, 1": "line 1: Di, 1 could mean 1 day or only day 1 (write 1 day, or day 1)",
    "Di, 30": "line 1: Di, 30 could mean 30 days or only day 30 (write 30 days, or day 30)",
    "Di, 1-10, 10": "line 1: the stretches 1-10 and 10-10 overlap",
    "Di, 1-10, 10-12": "line 1: the stretches 1-10 and 10-12 overlap",
    "Di, 21-30, 1-21": "line 1: the stretches 1-21 and 21-30 overlap",
    "Di, 12-3": "line 1: bad stretch: 12-3 (%s, and the first day comes first)" % F,
    "Di, 28-5": "line 1: bad stretch: 28-5 (%s, and the first day comes first)" % F,
    "Di, 0-3": "line 1: bad stretch: 0-3 (%s, and the first day comes first)" % F,
    "Di, 1-10, half": "line 1: bad stretch: half (write days like 1-10, 21-30, or day 15)",
    "Ann & Bo, 30, 2 people": "line 1: bad days: 30, 2 people (put each person on their own line; a couple is two lines)",
    "Ann & Bo, 1-10, two persons": "line 1: bad days: 1-10, two persons (put each person on their own line; a couple is two lines)",
})
for t, want in cases.items():
    eq(err(bills.parse, t, 30), want, repr(t))

# random bills: shares always add to the total, never more than a cent from the exact share
rng = random.Random(68)
for _ in range(400):
    period = rng.randint(1, 120)
    people = [("p%d" % i, rng.randint(0, period)) for i in range(rng.randint(1, 7))]
    if not any(d for _, d in people):
        people[0] = ("p0", 1)
    total = rng.randint(0, 10 ** 7)
    sh = bills.split(total, people)
    eq(sum(sh.values()), total, "sum")
    days = sum(d for _, d in people)
    for n, d in people:
        assert abs(sh[n] * days - total * d) <= days, (total, people)
        if d == 0:
            eq(sh[n], 0, "zero days")
    fixed = rng.randint(0, total)
    shf = bills.split(total, people, fixed)
    eq(sum(shf.values()), total, "sum with fixed")
    k = len(people)
    for n, d in people:
        exact = fixed * days + (total - fixed) * d * k  # times k*days
        assert abs(shf[n] * k * days - exact) <= 2 * k * days, (total, fixed, people)

# the command line
with tempfile.TemporaryDirectory() as tmp:
    f = os.path.join(tmp, "b.txt")
    with open(f, "w", encoding="utf-8-sig") as fh:
        fh.write("Asha\nBen, 12 days\nCy, 0\n")
    run = lambda *a: subprocess.run([sys.executable, str(HERE / "bills.py"), *a], capture_output=True, text=True)
    r = run("3,120", "30", f)
    eq((r.returncode, r.stdout), (0, "Asha pays 2228.58 (30 of 30 days)\nBen pays 891.42 (12 of 30 days)\nCy pays 0.00 (0 of 30 days)\n"), "cli")
    r = run("3,120", "0", f)
    eq(r.returncode, 2, "zero days exit")
    assert r.stdout.startswith("Usage: bills.py") and "bills: DAYS is a whole number" in r.stdout, r.stdout
    r = run("3,120")
    eq(r.returncode, 2, "short exit")
    assert "bills: DAYS" not in r.stdout
    eq((run("lots", "30", f).returncode, run("lots", "30", f).stdout), (1, "bills: bad bill: lots (write 2400 or 1,850.50)\n"), "bad bill")
    eq(run("10", "10", f).stdout, "bills: line 2: Ben was there 12 days but the bill covers 10\n", "period")
    f3 = os.path.join(tmp, "lone.txt")
    with open(f3, "w") as fh:
        fh.write("Asha\nDi, 15\n")
    eq((run("3000", "30", f3).returncode, run("3000", "30", f3).stdout), (1, "bills: line 2: Di, 15 could mean 15 days or only day 15 (write 15 days, or day 15)\n"), "cli lone day")
    eq(run("10", "10", os.path.join(tmp, "missing")).returncode, 1, "missing file")
    r = run("3,120", "30", f, "--fixed", "600")
    eq((r.returncode, r.stdout), (0, "Asha pays 2000.00 (30 of 30 days)\nBen pays 920.00 (12 of 30 days)\nCy pays 200.00 (0 of 30 days)\n"), "cli fixed")
    eq(run("3,120", "30", f, "--fixed", "4000").stdout, "bills: the fixed part is more than the whole bill\n", "cli fixed over")
    eq(run("3,120", "30", f, "--fixed", "lots").stdout, "bills: bad fixed part: lots (write 2400 or 1,850.50)\n", "cli fixed bad")
    r = run("3,120", "30", f, "--fxed", "600")
    eq(r.returncode, 2, "misspelt flag")
    assert "bills: DAYS" in r.stdout and r.stdout.startswith("Usage:"), r.stdout
    eq(run("3,120", "30", f, "--fixed").returncode, 2, "flag without amount")
    f2 = os.path.join(tmp, "away.txt")
    with open(f2, "w") as fh:
        fh.write("Asha, 0\nBen\n")
    eq(run("1", "30", f2).stdout, "Asha pays 0.00 (0 of 30 days)\nBen pays 1.00 (30 of 30 days)\n", "no flag means no fixed part")

page = (HERE / "bills.html").read_text(encoding="utf-8")
script = page.split("<script>", 1)[1]
for banned in ["fetch", "XMLHttpRequest", "localStorage", "http"]:
    assert banned not in script, banned
node = shutil.which("node")
if not node:
    print("SKIP bills.html: node not installed (bills.py is tested)"); print("ok test_bills"); sys.exit(0)
logic = page.split("// LOGIC START", 1)[1].split("\n", 1)[1].split("// LOGIC END", 1)[0]
js = logic + """
const texts = @TEXTS@, splits = @SPLITS@;
const p = texts.map(t => { try { return parse(t, 30); } catch (e) { return e.message; } });
const s = splits.map(([t, ppl, fx]) => { try { return split(t, ppl, fx); } catch (e) { return e.message; } });
const ex = split(312000, parse("Asha\\nBen, 12 days\\nCy, 0", 30));
console.log(JSON.stringify([p, s, ex]));
"""
texts = list(cases) + ["Ann, 12 days\nBo, 1 day\nCy,3", "\ufeffAnn\n\n  Bo  ", "Ann\u00a0, 3 days\x0bBo", "__proto__, 5 days\nCy",
                       "Ann, 30 days\r\nBo, 0", "Ann ,  7 DAYS ", "Ann, 0012",
                       "Di, 1-10, 21-30\nEd, 5 to 5 and 7–8\nFi, 21-30, 1-10", "Di, 1-30", "Di, day 15\nEd, 1-10, 12\nFi, Day 3 and 5\nGo, days 1-10, 21-30",
                       "Di, 1\u201410, 21\u201430\nEd, 1\u221210\nFi, 1\u201110\nGu, 1\u20122", "Ann, 1-10\nBo, 10-30", "Di, DAYS 2", "Di, 0012 days", "Di, 31", "Di, 0", "Di,1 TO 3 AND 5-6", "Di, 3-4,5-6", "Di, 1-2,  3-4"]
splits = [[10000, [["Asha", 30], ["Ben", 12], ["Cy", 0]]], [100, [["b", 1], ["a", 1], ["c", 1]]], [1, [["z", 0], ["b", 5], ["a", 5]]],
          [100, [["a", 0]]], [10 ** 12 + 7, [["x", 7], ["y", 11], ["w", 13]]],
          [312000, [["Asha", 30], ["Ben", 12], ["Cy", 0]], 60000], [500, [["c", 0], ["b", 0], ["a", 0]], 500],
          [10, [["b", 0], ["a", 3], ["c", 3]], 4], [100, [["a", 1]], 101], [100, [["a", 0]], 99], [7, [["__proto__", 0], ["z", 2]], 3]]
for _ in range(30):
    ppl = [["p%d" % i, rng.randint(0, 90)] for i in range(rng.randint(1, 6))]
    t = rng.randint(0, 10 ** 9)
    splits.append([t, ppl, rng.choice([0, rng.randint(0, t)])])
r = subprocess.run([node, "-e", js.replace("@TEXTS@", json.dumps(texts)).replace("@SPLITS@", json.dumps(splits))],
                   capture_output=True, text=True, timeout=30)
assert r.returncode == 0, r.stderr
got_p, got_s, got_ex = json.loads(r.stdout)
want_p = []
for t in texts:
    try: want_p.append([list(x) for x in bills.parse(t, 30)])
    except ValueError as e: want_p.append(str(e))
eq(got_p, want_p, "node parse")
want_s = []
for t, ppl, *fx in splits:
    try: want_s.append(bills.split(t, [tuple(x) for x in ppl], *fx))
    except ValueError as e: want_s.append(str(e))
eq(got_s, want_s, "node split")
eq(got_ex, ex, "node page example")
print("ok test_bills")
