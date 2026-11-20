#!/usr/bin/env python3
"""Tests for deposit.py and the logic inside deposit.html (run in node when present).
Copy rent.py, deposit.py, deposit.html and this file together: deposit.py reads
amounts with rent.py's hundredths(), and the last part of this test reads deposit.html."""
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
import deposit  # noqa: E402


def eq(got, want, what):
    assert got == want, "%s: got %r want %r" % (what, got, want)


def err(fn, *a):
    try:
        fn(*a)
    except ValueError as e:
        return str(e)
    raise AssertionError("no error for %r" % (a,))


def go(text):
    p, c, b = deposit.parse(text)
    return deposit.share(p, c, b)


EX = "Ana, 15,000\nBen, 15,000\nCy, 10,000\nkept cleaning, 3,000, everyone\nkept broken door, 2,400, Ben\ncame back, 34,600"
people, costs, back = deposit.parse(EX)
eq(people, [("Ana", 1500000), ("Ben", 1500000), ("Cy", 1000000)], "people")
eq([c[:3] for c in costs], [("cleaning", 300000, "everyone"), ("broken door", 240000, "Ben")], "costs")
eq(back, 3460000, "back")
rows = deposit.share(people, costs, back)
eq(rows, [("Ana", 1500000, 100000), ("Ben", 1500000, 340000), ("Cy", 1000000, 100000)], "share")
eq(deposit.row(*rows[1]), "Ben: put in 15,000, kept 3,400, gets back 11,600", "row")
eq(deposit.summary(rows, costs), "Deposit 40,000, kept 5,400 (cleaning 3,000 on everyone, broken door 2,400 on Ben). Back: Ana 14,000, Ben 11,600, Cy 9,000.", "summary")
eq(deposit.share(people, costs), rows, "no came back line")
# spare cents go to the first people named in the list, not in the cost line
eq(go("Ana, 1\nBen, 1\nCy, 1\nkept x, 0.05, Cy and Ana"), [("Ana", 100, 3), ("Ben", 100, 0), ("Cy", 100, 2)], "spare cents")
eq(go("Ana, 1\nBen, 1\nCy, 1\nkept x, 0.02, ALL OF US"), [("Ana", 100, 1), ("Ben", 100, 1), ("Cy", 100, 0)], "all of us")
eq(go("Ana, 1\nBen, 1\nCy, 1\nkept x, 0.03, ben & cy + ana"), [("Ana", 100, 1), ("Ben", 100, 1), ("Cy", 100, 1)], "& and +")
eq(go("Ana, 1\nBen, 1\nkept x, 0.03, Ben/Ana"), [("Ana", 100, 2), ("Ben", 100, 1)], "slash")
# someone whose costs are more than they put in owes the pot
r = go("Ana, 100\nBen, 0\nkept door, 0.05, Ana and Ben\nkept wall, 3, Ben")
eq(r, [("Ana", 10000, 3), ("Ben", 0, 302)], "owes")
eq(deposit.row(*r[1]), "Ben: put in 0, kept 3.02, owes 3.02 into the pot", "owes row")
eq(deposit.summary(r, deposit.parse("Ana, 100\nBen, 0\nkept door, 0.05, Ana and Ben\nkept wall, 3, Ben")[1]),
   "Deposit 100, kept 3.05 (door 0.05 on Ana and Ben, wall 3 on Ben). Back: Ana 99.97, Ben owes 3.02.", "owes summary")
eq(go("Ana, 10\nBen, 10\nkept all, 20, everyone"), [("Ana", 1000, 1000), ("Ben", 1000, 1000)], "all kept")
eq(deposit.summary(go("Ana, 10"), []), "Deposit 10, kept 0. Back: Ana 10.", "nothing kept")
eq(deposit.row("A", 5, 5), "A: put in 0.05, kept 0.05, gets back 0", "even")
# Ash's break-it (tick 75): put > 0 and kept > put, so kept-put and kept+put differ
r = go("Ana, 1,000\nBen, 3,000\nkept repairs, 3,000.50, Ana")
eq(r, [("Ana", 100000, 300050), ("Ben", 300000, 0)], "owes after putting in")
eq(deposit.row(*r[0]), "Ana: put in 1,000, kept 3,000.50, owes 2,000.50 into the pot", "owes row with put")
eq(deposit.summary(r, deposit.parse("Ana, 1,000\nBen, 3,000\nkept repairs, 3,000.50, Ana")[1]),
   "Deposit 4,000, kept 3,000.50 (repairs 3,000.50 on Ana). Back: Ana owes 2,000.50, Ben 3,000.", "owes summary with put")
eq(deposit.parse("\ufeff Kept  paint , ₹1,234.5 , Ben \nCAME  back , 2,00,000\nBen,0\nAnn Lee, 100000000000"),
   ([("Ben", 0), ("Ann Lee", 10 ** 13)], [("paint", 123450, "Ben", 1, "Kept  paint , ₹1,234.5 , Ben")], 20000000), "spaces, case, lakh, most")
for c, want in [(0, "0"), (5, "0.05"), (100, "1"), (123456789, "1,234,567.89")]:
    eq(deposit.money(c), want, "money %d" % c)
cases = {
    "Ana": "line 1: write it as: name, amount put in: Ana",
    ", 5": "line 1: write it as: name, amount put in: , 5",
    "Ana, lots": "line 1: write it as: name, amount put in: Ana, lots",
    "Ana, 1\nana, 2": "line 2: ana is listed twice: ana, 2",
    "Everyone, 5": "line 1: give each person their own line, with a name that isn't everyone and has no and, &, + or /: Everyone, 5",
    "Ann and Bo, 5": "line 1: give each person their own line, with a name that isn't everyone and has no and, &, + or /: Ann and Bo, 5",
    "Ann & Bo, 5": "line 1: give each person their own line, with a name that isn't everyone and has no and, &, + or /: Ann & Bo, 5",
    "kept cleaning": "line 1: write a cost as: kept what, amount, who: kept cleaning",
    "kept , 5, Ben": "line 1: write a cost as: kept what, amount, who: kept , 5, Ben",
    "kept cleaning, 3,000": "line 1: say who this cost is on: everyone, or names like Ben and Cy: kept cleaning, 3,000",
    "kept cleaning, 300": "line 1: say who this cost is on: everyone, or names like Ben and Cy: kept cleaning, 300",
    "kept cleaning, lots, Ben": "line 1: write a cost as: kept what, amount, who: kept cleaning, lots, Ben",
    "kept cleaning, 0, Ben": "line 1: a cost of 0 isn't a cost: kept cleaning, 0, Ben",
    "kept x, 100000000000.01, Ben": "line 1: write a cost as: kept what, amount, who: kept x, 100000000000.01, Ben",
    "came back, 5\ncame back, 5": "line 2: what came back is written twice: came back, 5",
    "came back, x": "line 1: write it as: came back, amount: came back, x",
}
for t, want in cases.items():
    eq(err(deposit.parse, t), want, repr(t))
eq(deposit.parse("Ana, 0.5\nkept x, 1, Ana"), ([("Ana", 50)], [("x", 100, "Ana", 2, "kept x, 1, Ana")], None), "kept counts more than put")
eq(deposit.parse("Ann Andrews, 5\nkeptwell, 3\nDand, 1")[0], [("Ann Andrews", 500), ("keptwell", 300), ("Dand", 100)], "and only as a word")
shares = {
    "": "nobody listed (write who put in what, like Ana, 15,000)",
    "kept x, 5, everyone": "nobody listed (write who put in what, like Ana, 15,000)",
    "Ana, 5\nkept x, 1, Bo": "line 2: who is Bo? nobody by that name put in: kept x, 1, Bo",
    "Ana, 5\nBen, 5\nkept x, 1, Ben and Bo": "line 3: who is Bo? nobody by that name put in: kept x, 1, Ben and Bo",
    "Ana, 5\nkept x, 1, Ana and ana": "line 2: ana is named twice: kept x, 1, Ana and ana",
    "Ana, 5\nBen, 5\nkept x, 6, Ana\nkept y, 5, everyone": "the costs add up to 11, more than the 10 put in (a landlord can't keep more than the deposit; anything above it is a separate bill)",
    "Ana, 15,000\nkept x, 1,000, Ana\ncame back, 13,500": "13,500 came back, but 15,000 put in minus 1,000 kept is 14,000: 500 is missing, and no cost line explains it",
    "Ana, 15,000\nkept x, 1,000, Ana\ncame back, 14,000.01": "14,000.01 came back, which is 0.01 more than 15,000 put in minus 1,000 kept: is a cost listed that wasn't kept?",
    "Ana, 15,000\ncame back, 0": "0 came back, but 15,000 put in minus 0 kept is 15,000: 15,000 is missing, and no cost line explains it",
}
for t, want in shares.items():
    eq(err(go, t), want, repr(t))
eq(go("Ana, 15,000\nkept x, 15,000, Ana\ncame back, 0"), [("Ana", 1500000, 1500000)], "nothing came back")

rng = random.Random(73)
for _ in range(300):
    n = rng.randint(1, 8)
    ppl = [("p%d" % i, rng.randint(0, 10 ** 8)) for i in range(n)]
    cs = []
    for k in range(rng.randint(0, 5)):
        on = sorted(rng.sample(range(n), rng.randint(1, n)))
        who = "everyone" if rng.random() < .3 else " and ".join("p%d" % i for i in rng.sample(on, len(on)))
        cs.append(("c%d" % k, rng.randint(1, 10 ** 7), who, k + 1, "x"))
    if sum(c for _, c, _, _, _ in cs) <= sum(c for _, c in ppl):
        rs = deposit.share(ppl, cs)
        eq(sum(k for _, _, k in rs), sum(c for _, c, _, _, _ in cs), "kept adds up")
        deposit.share(ppl, cs, sum(c for _, c in ppl) - sum(k for _, _, k in rs))
    else:
        assert "more than the" in err(deposit.share, ppl, cs)

with tempfile.TemporaryDirectory() as tmp:
    f = os.path.join(tmp, "d.txt")
    with open(f, "w", encoding="utf-8-sig") as fh:
        fh.write(EX + "\n")
    run = lambda *a: subprocess.run([sys.executable, str(HERE / "deposit.py"), *a], capture_output=True, text=True)
    r = run(f)
    eq((r.returncode, r.stdout), (0, "Ana: put in 15,000, kept 1,000, gets back 14,000\nBen: put in 15,000, kept 3,400, gets back 11,600\n"
                                     "Cy: put in 10,000, kept 1,000, gets back 9,000\n"
                                     "Deposit 40,000, kept 5,400 (cleaning 3,000 on everyone, broken door 2,400 on Ben). Back: Ana 14,000, Ben 11,600, Cy 9,000.\n"), "cli")
    with open(f, "w", encoding="utf-8") as fh:
        fh.write("Ana, 5\nkept x, 1\n")
    r = run(f)
    eq((r.returncode, r.stdout), (1, "deposit: line 2: say who this cost is on: everyone, or names like Ben and Cy: kept x, 1\n"), "cli refuse")
    with open(f, "w", encoding="utf-8") as fh:
        fh.write("Ana, 5\nkept x, 6, Ana\n")
    eq(run(f).returncode, 1, "cli share error")
    eq(run(os.path.join(tmp, "missing")).returncode, 1, "missing file")
    for a in [(), (f, f), ("--help",)]:
        r = run(*a)
        eq(r.returncode, 2, "usage %r" % (a,))
        eq(r.stdout, deposit.__doc__.split("\n\n", 1)[1].rstrip() + "\n", "usage text %r" % (a,))
        assert "Needs rent.py beside it" in r.stdout, r.stdout

page = (HERE / "deposit.html").read_text(encoding="utf-8")
script = page.split("<script>", 1)[1]
for banned in ["fetch", "XMLHttpRequest", "localStorage", "http"]:
    assert banned not in script, banned
node = shutil.which("node")
if not node:
    print("SKIP deposit.html: node not installed (deposit.py is tested)"); print("ok test_deposit"); sys.exit(0)
logic = page.split("// LOGIC START", 1)[1].split("\n", 1)[1].split("// LOGIC END", 1)[0]
js = logic + """
const texts = @TEXTS@, monies = @MONIES@;
const tryit = f => { try { return f(); } catch (e) { return e.message; } };
console.log(JSON.stringify([
  texts.map(t => tryit(() => parse(t))),
  texts.map(t => tryit(() => { const [p, c, b] = parse(t), rs = share(p, c, b); return [rs, rs.map(r => row(...r)), summary(rs, c)]; })),
  monies.map(money)]));
"""
texts = list(cases) + list(shares) + [EX, "Ana, 1\nBen, 1\nCy, 1\nkept x, 0.05, Cy and Ana", "Ana, 1\nBen, 1\nCy, 1\nkept x, 0.03, ben & cy + ana",
                                      "Ana, 100\nBen, 0\nkept door, 0.05, Ana and Ben\nkept wall, 3, Ben", "Ana, 10",
                                      "\ufeff Kept  paint , ₹1,234.5 , Ben \nCAME  back , 2,00,000\nBen,0\nAnn Lee, 100000000000",
                                      "Ann Andrews, 5\nkeptwell, 3\nDand, 1", "Ana, 1\nkept x, 1, ²", "Ana\u00a0, 3\x0bBen, 4\r\nkept y, 5, Ana\u20286",
                                      "Ana, 1\nkept x, 0.5, ana\u00a0and Ana", "Zoë, 5\nkept x, 1, ZOË", "Ana, 15,000\nkept x, 15,000, Ana\ncame back, 0"]
for _ in range(40):
    n = rng.randint(1, 6)
    lines = ["p%d, %s" % (i, deposit.money(rng.randint(0, 10 ** 7))) for i in range(n)]
    for k in range(rng.randint(0, 4)):
        who = "everyone" if rng.random() < .3 else " and ".join(rng.sample(["p%d" % i for i in range(n)] + ["q"], rng.randint(1, n)))
        lines.append("kept c%d, %s, %s" % (k, deposit.money(rng.randint(1, 10 ** 6)), who))
    if rng.random() < .5:
        lines.append("came back, %s" % deposit.money(rng.randint(0, 10 ** 7)))
    rng.shuffle(lines)
    texts.append("\n".join(lines))
monies = [0, 5, 100, 123456789, 10 ** 13, 999] + [rng.randint(0, 10 ** 13) for _ in range(20)]
r = subprocess.run([node, "-e", js.replace("@TEXTS@", json.dumps(texts)).replace("@MONIES@", json.dumps(monies))],
                   capture_output=True, text=True, timeout=30)
assert r.returncode == 0, r.stderr


def py(f):
    try:
        return f()
    except ValueError as e:
        return str(e)


def full(t):
    p, c, b = deposit.parse(t)
    rs = deposit.share(p, c, b)
    return [[list(x) for x in rs], [deposit.row(*x) for x in rs], deposit.summary(rs, c)]


want = [[py(lambda t=t: json.loads(json.dumps(deposit.parse(t)))) for t in texts],
        [py(lambda t=t: full(t)) for t in texts],
        [deposit.money(c) for c in monies]]
got = json.loads(r.stdout)
for i, name in enumerate(["parse", "share", "money"]):
    for k, (g, w) in enumerate(zip(got[i], want[i])):
        eq(g, w, "node %s %r" % (name, texts[k] if i < 2 else monies[k]))
print("ok test_deposit")
