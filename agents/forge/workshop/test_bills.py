#!/usr/bin/env python3
"""Tests for bills.py and the logic inside bills.html (run in node when present)."""
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


def eq(got, want, what):
    assert got == want, "%s: got %r want %r" % (what, got, want)


def err(fn, *a):
    try:
        fn(*a)
    except ValueError as e:
        return str(e)
    raise AssertionError("no error for %r" % (a,))


# the page example: 3,120 over 30 days, Asha all month, Ben 12 days, Cy away
ex = bills.split(312000, bills.parse("Asha\nBen, 12\nCy, 0", 30))
eq(ex, {"Asha": 222858, "Ben": 89142, "Cy": 0}, "page example")
eq(bills.split(10000, [("Asha", 30), ("Ben", 12), ("Cy", 0)]), {"Asha": 7143, "Ben": 2857, "Cy": 0}, "spare cent")
eq(bills.split(100, [("b", 1), ("a", 1), ("c", 1)]), {"a": 34, "b": 33, "c": 33}, "alphabetical spare")
eq(bills.split(2, [("z", 0), ("a", 5), ("b", 5)]), {"z": 0, "a": 1, "b": 1}, "nobody with 0 days gets a cent")
eq(bills.split(1, [("z", 0), ("b", 5), ("a", 5)]), {"z": 0, "b": 0, "a": 1}, "one cent")
eq(err(bills.split, 100, [("a", 0)]), "nobody was there for any days", "all away")
eq(bills.parse("Ann, 12 days\nBo, 1 day\nCy,3", 30), [("Ann", 12), ("Bo", 1), ("Cy", 3)], "day words")
eq(bills.parse("\ufeffAnn\n\n  Bo  ", 92), [("Ann", 92), ("Bo", 92)], "whole period")
cases = {
    "Ann, 31": "line 1: Ann was there 31 days but the bill covers 30",
    "Ann, 1\nann, 2": "line 2: ann is listed twice",
    "12, 4": "line 1: 12 looks like a number, not a name",
    ", 4": "line 1: write it as: name, days: , 4",
    "Ann, 1.5": "line 1: bad days: 1.5 (write a whole number of days, like 12)",
    "Ann, 12, 3": "line 1: bad days: 12, 3 (write a whole number of days, like 12)",
    "Ann, half": "line 1: bad days: half (write a whole number of days, like 12)",
    "Ann, -3": "line 1: bad days: -3 (write a whole number of days, like 12)",
    "": "nobody listed",
}
# stretches: someone away in the middle, or out and back in
eq(bills.parse("Di, 1-10, 21-30\nEd, 5 to 5 and 7–8\nFi, 21-30, 1-10", 30), [("Di", 20), ("Ed", 3), ("Fi", 20)], "stretches")
eq(bills.parse("Di, 1-30", 30), [("Di", 30)], "whole stretch")
cases.update({
    "Di, 1-10, 21-31": "line 1: 21-31 runs past day 30, the last day of the bill",
    "Di, 1-10, 10-12": "line 1: the stretches 1-10 and 10-12 overlap",
    "Di, 21-30, 1-21": "line 1: the stretches 1-21 and 21-30 overlap",
    "Di, 12-3": "line 1: bad stretch: 12-3 (days run from 1, and the first day comes first)",
    "Di, 0-3": "line 1: bad stretch: 0-3 (days run from 1, and the first day comes first)",
    "Di, 1-10, 12": "line 1: bad stretch: 12 (write days like 1-10, 21-30)",
    "Di, 1-10, half": "line 1: bad stretch: half (write days like 1-10, 21-30)",
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

# the command line
with tempfile.TemporaryDirectory() as tmp:
    f = os.path.join(tmp, "b.txt")
    with open(f, "w", encoding="utf-8-sig") as fh:
        fh.write("Asha\nBen, 12\nCy, 0\n")
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
    eq(run("10", "10", os.path.join(tmp, "missing")).returncode, 1, "missing file")

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
const s = splits.map(([t, ppl]) => { try { return split(t, ppl); } catch (e) { return e.message; } });
const ex = split(312000, parse("Asha\\nBen, 12\\nCy, 0", 30));
console.log(JSON.stringify([p, s, ex]));
"""
texts = list(cases) + ["Ann, 12 days\nBo, 1 day\nCy,3", "\ufeffAnn\n\n  Bo  ", "Ann\u00a0, 3\x0bBo", "__proto__, 5\nCy",
                       "Ann, 30\r\nBo, 0", "Ann ,  7 DAYS ", "Ann, 0012",
                       "Di, 1-10, 21-30\nEd, 5 to 5 and 7–8\nFi, 21-30, 1-10", "Di, 1-30", "Di,1 TO 3 AND 5-6", "Di, 3-4,5-6", "Di, 1-2,  3-4"]
splits = [[10000, [["Asha", 30], ["Ben", 12], ["Cy", 0]]], [100, [["b", 1], ["a", 1], ["c", 1]]], [1, [["z", 0], ["b", 5], ["a", 5]]],
          [100, [["a", 0]]], [10 ** 12 + 7, [["x", 7], ["y", 11], ["w", 13]]]]
for _ in range(30):
    ppl = [["p%d" % i, rng.randint(0, 90)] for i in range(rng.randint(1, 6))]
    splits.append([rng.randint(0, 10 ** 9), ppl])
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
for t, ppl in splits:
    try: want_s.append(bills.split(t, [tuple(x) for x in ppl]))
    except ValueError as e: want_s.append(str(e))
eq(got_s, want_s, "node split")
eq(got_ex, ex, "node page example")
print("ok test_bills")
