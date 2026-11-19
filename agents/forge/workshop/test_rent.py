#!/usr/bin/env python3
"""Tests for rent.py and the logic inside rent.html (run in node when present)."""
import json, os, random, shutil, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rent

def eq(a, b, what):
    assert a == b, "%s: got %r, want %r" % (what, a, b)

def refuses(fn, frag):
    if frag is None:
        fn(); return
    try:
        fn()
    except ValueError as e:
        assert frag in str(e), "message %r lacks %r" % (str(e), frag); return
    raise AssertionError("no error, wanted %r" % frag)

# amounts
eq(rent.hundredths("2400", "rent"), 240000, "plain")
eq(rent.hundredths("1,850.50", "rent"), 185050, "comma")
eq(rent.hundredths(" $9.5 ", "rent"), 950, "dollar")
eq(rent.hundredths("₹12,000", "rent"), 1200000, "rupee")
eq(rent.hundredths(".5", "x"), 50, "dot")
eq(rent.hundredths("₹1,00,000", "rent"), 10000000, "lakh")
eq(rent.hundredths("12,34,567.5", "rent"), 123456750, "lakhs")
for bad in ["", "abc", "1.234", "12,00", "١٢", "-5", "1e3", ".", "1,00", "1,0,000", "1,00,00"]:
    refuses(lambda b=bad: rent.hundredths(b, "rent"), "bad rent")

# the page example
ex = rent.split(240000, 30, rent.parse("Asha, 14\nBen, 10\nCy, 9.5\n"))
eq(ex, {"Asha": 94209, "Ben": 74150, "Cy": 71641}, "page example")
# 0% is purely by size, 100% equal; spare cents go alphabetically
eq(rent.split(1000, 0, [("a", 1), ("b", 3)]), {"a": 250, "b": 750}, "by size")
eq(rent.split(100, 100, [("c", 1), ("b", 9), ("a", 5)]), {"a": 34, "b": 33, "c": 33}, "equal + spare")
eq(rent.split(100, 0, [("b", 1), ("a", 1), ("c", 1)]), {"a": 34, "b": 33, "c": 33}, "size spare")
eq(rent.split(7, 50, [("z", 1)]), {"z": 7}, "one person")
eq(rent.split(0, 30, [("a", 1), ("b", 2)]), {"a": 0, "b": 0}, "zero rent")
eq(rent.split(5, 0, [("b", 1), ("a", 1)]), {"a": 3, "b": 2}, "two spare")
refuses(lambda: rent.split(100, 101, [("a", 1)]), "0 to 100")
refuses(lambda: rent.split(100, -1, [("a", 1)]), "0 to 100")
refuses(lambda: rent.split(100, 10, []), "nobody")
refuses(lambda: rent.split(100, 10, [("a", 0)]), "zero")

# random flats: shares add up, bigger room never pays less
rng = random.Random(65)
cases = []
for _ in range(80):
    n = rng.randint(1, 6)
    rooms = [("p%d" % i, rng.randint(1, 4000)) for i in range(n)]
    total, pct = rng.randint(0, 10**9), rng.randint(0, 100)
    sh = rent.split(total, pct, rooms)
    eq(sum(sh.values()), total, "adds up")
    for a, sa in rooms:
        for b, sb in rooms:
            if sa > sb:
                assert sh[a] >= sh[b] - 1, (a, b, sh)
    cases.append([total, pct, rooms, sh])

# random flats with perks: still adds up, nobody below their extra
for _ in range(60):
    n = rng.randint(1, 6)
    total = rng.randint(0, 10**7)
    rooms = [("p%d" % i, rng.randint(1, 4000), rng.randint(0, total // (2 * n) + 1), rng.randint(1, 3)) for i in range(n)]
    if sum(r[2] for r in rooms) > total:
        continue
    sh = rent.split(total, rng.randint(0, 100), rooms)
    eq(sum(sh.values()), total, "adds up with perks")
    assert all(sh[r[0]] >= r[2] for r in rooms)
    cases.append([total, rng.randint(0, 100), rooms, None])
cases = [[t_, p_, r_, rent.split(t_, p_, r_)] for t_, p_, r_, _ in cases]

# parsing
eq(rent.parse("\n Ann , 12.5 \n\nBo,3\n"), [("Ann", 1250, 0, 1), ("Bo", 300, 0, 1)], "parse")
# perks and people: parts after a comma and a space; 1,200 stays one size
eq(rent.parse("Ann, 14, 50\nBo, 1,200\nCy, 10, +50\nDi, 2, $1,000.5\nEd & Flo, 9, 2 people, extra 5\nGus, 3, people 3"),
   [("Ann", 1400, 5000, 1), ("Bo", 120000, 0, 1), ("Cy", 1000, 5000, 1), ("Di", 200, 100050, 1),
    ("Ed & Flo", 900, 500, 2), ("Gus", 300, 0, 3)], "parse extras and people")
# units, written any common way, but one unit for everyone
eq([r[1] for r in rent.parse("A, 14 m2\nB, 9.5m²\nC, 10 sqm\nD, 3 sq. m\nE, 2 square metres")], [1400, 950, 1000, 300, 200], "metres")
eq([r[1] for r in rent.parse("A, 150 sq ft\nB, 1,200 ft²\nC, 99sqft\nD, 3 SQUARE FEET")], [15000, 120000, 9900, 300], "feet")
# Wry's finding 4: a byte-order mark and case can't sneak a duplicate past
refuses(lambda: rent.parse("\ufeffAsha, 14\nAsha, 10"), "line 2: Asha is listed twice")
refuses(lambda: rent.parse("Ann, 1\nann, 2"), "ann is listed twice")
# Wry's and Lumen's finding 1: a couple pays two shares of the shared space only when the page is told
eq(rent.split(240000, 30, rent.parse("Ann & Bo, 14\nCy, 10")), {"Ann & Bo": 134000, "Cy": 106000}, "couple as one")
eq(rent.split(240000, 30, rent.parse("Ann & Bo, 14, 2 people\nCy, 10")), {"Ann & Bo": 146000, "Cy": 94000}, "couple as two")
eq(rent.parse("Ann & Bo, 14, two people\nCy, 10, One person\nDi, 3, people THREE"),
   [("Ann & Bo", 1400, 0, 2), ("Cy", 1000, 0, 1), ("Di", 300, 0, 3)], "people in words")
eq(rent.split(240000, 30, rent.parse("Ann, 7\nBo, 7\nCy, 10")), {"Ann": 73000, "Bo": 73000, "Cy": 94000}, "couple split")
eq(rent.split(10, 100, [("a", 1, 0, 1), ("b", 1, 0, 2)]), {"a": 4, "b": 6}, "people spare")
eq(rent.split(9, 100, [("a", 1, 0, 2), ("b", 1, 0, 1)]), {"a": 6, "b": 3}, "people share")
eq(rent.split(10, 100, [("a", 1), ("b", 1, 0, 2)]), {"a": 4, "b": 6}, "short row counts as 1 person")
# the misread the Chief found: 10,5 is refused with a hint, never read as size 10 plus 5.00
refuses(lambda: rent.parse("Ann, 10,5"), "write it with a dot, like 10.5; for a perk, write 10, +5")
refuses(lambda: rent.parse("Ann, 10,50"), "like 10.5")
refuses(lambda: rent.parse("Ann, 1,200,50"), "write 14, 9.5 or 150 sq ft")
ex2 = rent.split(240000, 30, rent.parse("Asha, 14, 50\nBen, 10\nCy, 9.5\n"))
eq(ex2, {"Asha": 97247, "Ben": 72604, "Cy": 70149}, "page example with a perk")
eq(rent.split(1000, 0, [("a", 1, 200), ("b", 1, 0)]), {"a": 600, "b": 400}, "extra on top")
eq(rent.split(1000, 50, [("a", 1, 1000), ("b", 3, 0)]), {"a": 1000, "b": 0}, "extras take it all")
refuses(lambda: rent.split(1000, 0, [("a", 1, 600), ("b", 1, 401)]), "more than the rent")
for text, frag in [("Ann 12", "line 1: write it as"), (", 12", "write it as"),
                   ("Ann, 12\n12, 4", "line 2: 12 looks like a number"),
                   ("Ann, 1\nAnn, 2", "listed twice"), ("Ann, big", "line 1: bad room size"),
                   ("Ann, 0", "size 0"), ("Ann, 1, lots", "line 1: bad extra"),
                   ("Ann, 1 2", "bad room size"), ("Ann, 1.2.3", "bad room size"), ("Ann, 1, 2, 3", "only one extra"),
                   ("Ann, 14 m2\nBo, 150 sq ft", "line 2: Bo's room is in square feet but Ann's is in square metres"),
                   ("Ann, 14 parsecs", "write 14, 9.5"), ("Ann, 14, 0 people", "at least 1 person"), ("Ann, 14, zero people", "at least 1 person"),
                   ("Ann, 14, twelve people", "bad number of people: twelve people (write it like 2 people or two people)"),
                   ("Ann, 14, a few people", "bad number of people"), ("Ann, 14, 2 persons, +5, 3 people", "people given twice"),
                   ("Ann, 14, 2 people, people 3", "people given twice"), ("Ann, m2", "bad room size"),
                   ("Ann, 14, 1,00,000", None)]:
    refuses(lambda t=text: rent.parse(t), frag)

# CLI
with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, "f.txt")
    open(p, "w").write("Asha, 14\nBen, 10\nCy, 9.5\n")
    run = lambda *a: subprocess.run([sys.executable, os.path.join(HERE, "rent.py"), *a], capture_output=True, text=True)
    r = run("2400", "30", p)
    eq((r.returncode, r.stdout), (0, "Asha pays 942.09\nBen pays 741.50\nCy pays 716.41\n"), "cli ok")
    open(p, "w").write("Asha, 14, 50\nBen, 10\nCy, 9.5\n")
    r = run("2400", "30", p)
    eq(r.stdout, "Asha pays 972.47 (includes 50.00 extra)\nBen pays 726.04\nCy pays 701.49\n", "cli perk")
    open(p, "w").write("Asha, 1, 3000\n")
    r = run("2400", "30", p)
    eq(r.returncode, 1, "cli over"); assert "more than the rent" in r.stderr
    r = run("lots", "30", p)
    eq(r.returncode, 1, "cli err"); assert "rent: bad rent" in r.stderr and "Traceback" not in r.stderr, r.stderr
    open(p, "w").write("Asha, 14\nBen, 10\nCy, 9.5\n")
    r = run("2400", "30%", p)
    eq((r.returncode, r.stdout), (0, "Asha pays 942.09\nBen pays 741.50\nCy pays 716.41\n"), "cli 30%")
    r = run("2400", " 30 % ", p)
    eq(r.returncode, 0, "cli 30 %")
    open(p, "w", encoding="utf-8").write("\ufeffAsha, 14\nAsha, 10\n")
    r = run("2400", "30", p)
    eq(r.returncode, 1, "cli bom"); assert "line 2: Asha is listed twice" in r.stderr, r.stderr
    open(p, "w").write("Ann & Bo, 14, 2 people, +50\nCy, 10\n")
    r = run("2400", "30", p)
    eq(r.stdout, "Ann & Bo pays 1479.59 (2 people, includes 50.00 extra)\nCy pays 920.41\n", "cli couple")
    r = run("2400", "x", p)
    assert "whole number, like 30" in r.stderr, r.stderr
    r = run("2400", "30")
    eq(r.returncode, 2, "few args"); assert "rent: the shared percent" not in r.stderr
    r = run("2400", "x", p)
    eq(r.returncode, 2, "usage"); assert "Usage:" in r.stderr
    r = run("2400", "300", p)
    eq(r.returncode, 1, "pct"); assert "0 to 100" in r.stderr

# the page
page = open(os.path.join(HERE, "rent.html"), encoding="utf-8").read()
script = page.split("<script>", 1)[1]
for banned in ["fetch", "XMLHttpRequest", "localStorage", "http"]:
    assert banned not in script, banned
node = shutil.which("node")
if not node:
    print("SKIP rent.html: node not installed (rent.py is tested)"); print("ok test_rent"); sys.exit(0)
logic = page.split("// LOGIC START", 1)[1].split("\n", 1)[1].split("// LOGIC END", 1)[0]
js = logic + """
const cases = @CASES@, out = [];
for (const [t, p, rooms, want] of cases) out.push(split(t, p, rooms));
const errs = @TEXTS@.map(t => { try { return parse(t); } catch (e) { return e.message; } });
const amts = @AMTS@.map(t => { try { return hundredths(t, "rent"); } catch (e) { return e.message; } });
const ex2 = split(240000, 30, parse("Asha, 14, 50\\nBen, 10\\nCy, 9.5"));
let over = null; try { split(1000, 0, [["a", 1, 600], ["b", 1, 401]]); } catch (e) { over = e.message; }
console.log(JSON.stringify([out, errs, amts, split(240000, 30, parse("Asha, 14\\nBen, 10\\nCy, 9.5")), ex2, over]));
"""
texts = ["Ann 12", "Ann, 12\n12, 4", "Ann, 1\nAnn, 2", "Ann, big", "Ann, 0", "Ann, 1, lots",
         "Ann, 1 2", "Ann, 1.2.3", "Ann, 1, 2, 3", "Ann, 14, 50\nBo, 1,200\nCy, 10, +50\nDi, 2, $1,000.5",
         "Ed & Flo, 9, 2 people, extra 5\nGus, 3, people 3", "Ann, 10,5", "Ann, 10,50", "Ann, 1,200,50",
         "A, 14 m2\nB, 9.5m²\nC, 10 sqm\nD, 3 sq. m\nE, 2 square metres", "A, 150 sq ft\nB, 1,200 ft²\nC, 99sqft\nD, 3 SQUARE FEET",
         "Ann, 14 m2\nBo, 150 sq ft", "\ufeffAsha, 14\nAsha, 10", "Ann, 1\nann, 2", "Ann, 14, 0 people",
         "Ann, 14, 2 people, people 3", "Ann, 14 parsecs", "Ann\u00a0, 3\x0bBo, 4", "__proto__, 5\nCy, 5",
         "Ann & Bo, 14, two people\nCy, 10, One person\nDi, 3, people THREE", "Ann, 14, twelve people", "Ann, 14, a few people",
         "Ann, 14, zero people", "Ann, 14, +5, peoples 2", "Ann, 14, nine persons"]
amts = ["2400", "1,850.50", " $9.5 ", "₹12,000", "12,00", "١٢", "1.234", "₹1,00,000", "12,34,567.5", "1,00", "1,0,000"]
r = subprocess.run([node, "-e", js.replace("@CASES@", json.dumps(cases)).replace("@TEXTS@", json.dumps(texts)).replace("@AMTS@", json.dumps(amts))],
                   capture_output=True, text=True, timeout=30)
assert r.returncode == 0, r.stderr
got_split, got_errs, got_amts, got_ex, got_ex2, got_over = json.loads(r.stdout)
eq(got_ex2, ex2, "node perk example")
eq(got_over, "the extras add up to more than the rent", "node over")
eq(got_split, [c[3] for c in cases], "node split")
want_errs = []
for t in texts:
    try: want_errs.append([list(r) for r in rent.parse(t)])
    except ValueError as e: want_errs.append(str(e))
eq(got_errs, want_errs, "node errors")
want_amts = []
for t in amts:
    try: want_amts.append(rent.hundredths(t, "rent"))
    except ValueError as e: want_amts.append(str(e))
eq(got_amts, want_amts, "node amounts")
eq(got_ex, ex, "node page example")
print("ok test_rent")
