#!/usr/bin/env python3
"""Tests for rent.py and the logic inside rent.html (run in node when present)."""
import json, os, random, shutil, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rent

def eq(a, b, what):
    assert a == b, "%s: got %r, want %r" % (what, a, b)

def refuses(fn, frag):
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
for bad in ["", "abc", "1.234", "12,00", "١٢", "-5", "1e3", "."]:
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

# parsing
eq(rent.parse("\n Ann , 12.5 \n\nBo,$3\n"), [("Ann", 1250), ("Bo", 300)], "parse")
for text, frag in [("Ann 12", "line 1: write it as"), (", 12", "write it as"),
                   ("Ann, 12\n12, 4", "line 2: 12 looks like a number"),
                   ("Ann, 1\nAnn, 2", "listed twice"), ("Ann, big", "line 1: bad room size"),
                   ("Ann, 0", "size 0"), ("Ann, 1, 2", "bad room size")]:
    refuses(lambda t=text: rent.parse(t), frag)

# CLI
with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, "f.txt")
    open(p, "w").write("Asha, 14\nBen, 10\nCy, 9.5\n")
    run = lambda *a: subprocess.run([sys.executable, os.path.join(HERE, "rent.py"), *a], capture_output=True, text=True)
    r = run("2400", "30", p)
    eq((r.returncode, r.stdout), (0, "Asha pays 942.09\nBen pays 741.50\nCy pays 716.41\n"), "cli ok")
    r = run("lots", "30", p)
    eq(r.returncode, 1, "cli err"); assert "rent: bad rent" in r.stderr and "Traceback" not in r.stderr, r.stderr
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
const errs = @TEXTS@.map(t => { try { parse(t); return null; } catch (e) { return e.message; } });
const amts = @AMTS@.map(t => { try { return hundredths(t, "rent"); } catch (e) { return e.message; } });
console.log(JSON.stringify([out, errs, amts, split(240000, 30, parse("Asha, 14\\nBen, 10\\nCy, 9.5"))]));
"""
texts = ["Ann 12", "Ann, 12\n12, 4", "Ann, 1\nAnn, 2", "Ann, big", "Ann, 0", "Ann, 1, 2"]
amts = ["2400", "1,850.50", " $9.5 ", "₹12,000", "12,00", "١٢", "1.234"]
r = subprocess.run([node, "-e", js.replace("@CASES@", json.dumps(cases)).replace("@TEXTS@", json.dumps(texts)).replace("@AMTS@", json.dumps(amts))],
                   capture_output=True, text=True, timeout=30)
assert r.returncode == 0, r.stderr
got_split, got_errs, got_amts, got_ex = json.loads(r.stdout)
eq(got_split, [c[3] for c in cases], "node split")
want_errs = []
for t in texts:
    try: rent.parse(t); want_errs.append(None)
    except ValueError as e: want_errs.append(str(e))
eq(got_errs, want_errs, "node errors")
want_amts = []
for t in amts:
    try: want_amts.append(rent.hundredths(t, "rent"))
    except ValueError as e: want_amts.append(str(e))
eq(got_amts, want_amts, "node amounts")
eq(got_ex, ex, "node page example")
print("ok test_rent")
