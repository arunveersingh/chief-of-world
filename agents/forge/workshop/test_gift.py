#!/usr/bin/env python3
"""Tests for gift.py and the logic inside gift.html (run in node when present).
Copy rent.py, gift.py, gift.html and this file together: gift.py reads
amounts with rent.py's hundredths(), and the last part of this test reads gift.html."""
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
import gift  # noqa: E402


def eq(got, want, what):
    assert got == want, "%s: got %r want %r" % (what, got, want)


def err(fn, *a):
    try:
        fn(*a)
    except ValueError as e:
        return str(e)
    raise AssertionError("no error for %r" % (a,))


def go(text):
    return gift.share(*gift.parse(text))


EX = "gift, 6,000\nAna, 1,000\nBen, up to 800\nCy\nDee, even\npaid, Ana"
gift_c, people, paid = gift.parse(EX)
eq(gift_c, 600000, "gift")
eq([(n, k, c) for n, k, c, _, _ in people],
   [("Ana", "fixed", 100000), ("Ben", "cap", 80000), ("Cy", "even", None), ("Dee", "even", None)], "people")
eq(paid, "Ana", "paid")
rows, payer = gift.share(gift_c, people, paid)
eq(rows, [("Ana", "fixed", 100000, 100000), ("Ben", "cap", 80000, 80000),
          ("Cy", "even", None, 210000), ("Dee", "even", None, 210000)], "share")
eq(payer, "Ana", "payer")
eq(gift.row(*rows[0], paid_name="Ana"), "Ana: fixed, pays 1,000 (paid the gift)", "row payer")
eq(gift.row(*rows[1], paid_name="Ana"), "Ben: up to 800, pays 800 (capped)", "row capped")
eq(gift.row(*rows[2], paid_name="Ana"), "Cy: even, pays 2,100", "row even")
eq(gift.row("Ben", "cap", 80000, 50000), "Ben: up to 800, pays 500", "row under cap")
eq(gift.row("Ana", "fixed", 100000, 100000), "Ana: fixed, pays 1,000", "row fixed no paid")
eq(gift.summary(rows, "Ana"),
   "Gift 6,000. Ana 1,000, Ben 800, Cy 2,100, Dee 2,100. Owes Ana: Ben 800, Cy 2,100, Dee 2,100.", "summary")
eq(gift.summary(rows), "Gift 6,000. Ana 1,000, Ben 800, Cy 2,100, Dee 2,100.", "summary no payer")
eq(go("COST, 6,000\nAna, 1,000\nBen, up to 800\nCy\nDee, even\npaid, ana")[1], "Ana", "cost synonym, paid case-blind")
eq(go(EX)[0], rows, "go example")

# worked examples
eq(go("gift, 1\nA\nB\nC")[0],
   [("A", "even", None, 34), ("B", "even", None, 33), ("C", "even", None, 33)], "all even spare to first")
eq(go("gift, 1,000\nAna, 1,000")[0], [("Ana", "fixed", 100000, 100000)], "one person covers")
eq(gift.summary(go("gift, 1,000\nAna, 1,000\npaid, Ana")[0], "Ana"),
   "Gift 1,000. Ana 1,000. Nothing owed to Ana.", "nothing owed")
# fixed amounts exactly cover the gift; others listed as even pay 0, and the summary says so
rows0, _ = go("gift, 1,000\nAna, 1,000\nCy\nDee, even")
eq(rows0, [("Ana", "fixed", 100000, 100000), ("Cy", "even", None, 0), ("Dee", "even", None, 0)], "fixed covers, evens 0")
eq(gift.summary(rows0, "Ana"),
   "Gift 1,000. Ana 1,000, Cy 0, Dee 0. The fixed amounts cover the gift, so everyone else pays 0.",
   "fixed covers summary")
eq(gift.row(*rows0[1]), "Cy: even, pays 0", "even pays 0")
# a cap person who doesn't hit the cap
eq(go("gift, 100\nAna, up to 80\nBen")[0],
   [("Ana", "cap", 8000, 5000), ("Ben", "even", None, 5000)], "cap not reached")
eq(gift.row("Ana", "cap", 8000, 5000, paid_name="Ana"),
   "Ana: up to 80, pays 50 (paid the gift)", "cap under and paid")
# water-filling, spare cents go to the first *uncapped* in list order
eq(go("gift, 0.10\nAna, up to 0.01\nBen\nCy")[0],
   [("Ana", "cap", 1, 1), ("Ben", "even", None, 5), ("Cy", "even", None, 4)], "spare after cap")
# several caps fire in one round; remainder split among the rest
eq(go("gift, 100\nA, up to 20\nB, up to 20\nC")[0],
   [("A", "cap", 2000, 2000), ("B", "cap", 2000, 2000), ("C", "even", None, 6000)], "two caps then even")
# caps exactly reach the gift
eq(go("gift, 10\nA, up to 4\nB, up to 3\nC, up to 3")[0],
   [("A", "cap", 400, 400), ("B", "cap", 300, 300), ("C", "cap", 300, 300)], "caps exactly reach")
# a cap that lands exactly on the even share is marked capped
r = go("gift, 0.03\nA, up to 0.01\nB, up to 0.01\nC, up to 0.01")[0]
eq(r, [("A", "cap", 1, 1), ("B", "cap", 1, 1), ("C", "cap", 1, 1)], "even share equals cap")
eq(gift.row(*r[0]), "A: up to 0.01, pays 0.01 (capped)", "equals cap is capped")
# only even people, one person
eq(go("gift, 50\nAna")[0], [("Ana", "even", None, 5000)], "one even")
eq(gift.summary(go("gift, 50\nAna\npaid, Ana")[0], "Ana"), "Gift 50. Ana 50. Nothing owed to Ana.", "one even paid")
# zeros in the owes list are skipped
eq(gift.summary([("Ana", "fixed", 100, 100), ("Bo", "even", None, 0), ("Cy", "even", None, 50)], "Ana"),
   "Gift 1.50. Ana 1, Bo 0, Cy 0.50. Owes Ana: Cy 0.50.", "zero share owes nothing")
# cost, spaces, case, lakh, currency, most
eq(gift.parse("\ufeff COST , ₹1,234.5 \nCAME, even\nBen, Up  To  2,00,000\nAnn Lee, 100000000000")[0],
   123450, "spaces, case, lakh, most gift")
g, ppl, pd = gift.parse("\ufeff COST , ₹1,234.5 \nCAME, even\nBen, Up  To  2,00,000\nAnn Lee, 100000000000")
eq([(n, k, c) for n, k, c, _, _ in ppl],
   [("CAME", "even", None), ("Ben", "cap", 20000000), ("Ann Lee", "fixed", 10 ** 13)], "spaces people")
eq(pd, None, "no paid")
# a person named Gifted is not the gift line; a person named Costco is not cost
eq(gift.parse("gift, 5\nGifted, 3\nCostco")[1][0][:3], ("Gifted", "fixed", 300), "gifted is a name")
for c, want in [(0, "0"), (5, "0.05"), (100, "1"), (123456789, "1,234,567.89"), (10 ** 13, "100,000,000,000")]:
    eq(gift.money(c), want, "money %d" % c)
eq(gift.even(5, 3), [2, 2, 1], "even")
eq(gift.even(0, 2), [0, 0], "even zero")
eq(gift.even(3, 3), [1, 1, 1], "even exact")
eq(gift.even(1, 1), [1], "even one")
# a cap exceeded only by a spare cent must be applied (so k < spare in the over-check matters)
eq(go("gift, 0.16\nA, up to 0.05\nB, up to 1\nC, up to 1")[0],
   [("A", "cap", 5, 5), ("B", "cap", 100, 6), ("C", "cap", 100, 5)], "spare cent exceeds cap")
# one cent short, only fixed people (left > 0, not left > 1)
eq(err(go, "gift, 10\nAna, 9.99"),
   "the fixed amounts add up to 9.99, which is 0.01 short of the 10 gift (add someone to split what's left, or raise a fixed amount)",
   "one cent short fixed")
# one cent short, everyone capped (left > 0 after fill, not left > 1)
eq(err(go, "gift, 0.10\nA, up to 0.03\nB, up to 0.03\nC, up to 0.03"),
   "the caps can't reach the gift: all together (with any fixed amounts) they add up to 0.09, which is 0.01 short of 0.10 (raise a cap, or add someone)",
   "one cent short caps")
# one cent owed is still owed (r[3] > 0, not r[3] > 1)
eq(gift.summary([("Ana", "fixed", 100, 100), ("Bo", "even", None, 1)], "Ana"),
   "Gift 1.01. Ana 1, Bo 0.01. Owes Ana: Bo 0.01.", "one cent owed")
# count=1 in the 'up to' strip: a second 'up to' is not an amount
eq(err(gift.parse, "gift, 5\nBen, up to up to 800"),
   "line 2: write how much they will go up to, like: Ben, up to 800: Ben, up to up to 800",
   "up to twice")

cases = {
    "gift, 5\nAna, lots": "line 2: write it as: name, amount (or name, up to amount, or a bare name): Ana, lots",
    ", 5": "line 1: a line with an amount needs a name: , 5",
    "1,000": "line 1: a line with an amount needs a name: 1,000",
    "up to 800": "line 1: a line with an amount needs a name: up to 800",
    ", up to 800": "line 1: a line with an amount needs a name: , up to 800",
    "gift, 5\nAna, 1\nana, 2": "line 3: ana is listed twice: ana, 2",
    "gift, 5\nAna\nANA, even": "line 3: ANA is listed twice: ANA, even",
    "gift, x": "line 1: write it as: gift, amount: gift, x",
    "gift, 5\ngift, 6": "line 2: the gift is written twice: gift, 6",
    "cost, 5\ngift, 6": "line 2: the gift is written twice: gift, 6",
    "gift, 0": "line 1: a gift of 0 isn't a gift: gift, 0",
    "gift, 5\nAna, 0": "line 2: a fixed amount of 0 isn't chipping in; leave them off: Ana, 0",
    "gift, 5\nBen, up to 0": "line 2: up to 0 means they're not chipping in; leave them off: Ben, up to 0",
    "gift, 5\nBen, up to": "line 2: write how much they will go up to, like: Ben, up to 800: Ben, up to",
    "gift, 5\nBen, up to   ": "line 2: write how much they will go up to, like: Ben, up to 800: Ben, up to",
    "gift, 5\nBen, up to lots": "line 2: write how much they will go up to, like: Ben, up to 800: Ben, up to lots",
    "gift, 10%": "line 1: write the exact amount, not % (a % of the gift and a % of what's left are different things): gift, 10%",
    "gift, 5\nAna, 10%": "line 2: write the exact amount, not % (a % of the gift and a % of what's left are different things): Ana, 10%",
    "paid, Ana": "line 1: write it as: paid, name: paid, Ana" if False else None,  # placeholder, filled below after thinking
    "gift, 5\npaid,": "line 2: write it as: paid, name: paid,",
    "gift, 5\npaid, 123": "line 2: write it as: paid, name: paid, 123",
    "gift, 5\nAna\npaid, Ana\npaid, Ana": "line 4: who paid is written twice: paid, Ana",
    "gift, 100000000000.01": "line 1: bad amount: 100000000000.01 (that's more than this counts; the most is 100,000,000,000)",
    "gift, 5\nAna, 100000000000.01": "line 2: bad amount: 100000000000.01 (that's more than this counts; the most is 100,000,000,000)",
    "gift, 5\nBen, up to 100000000000.01": "line 2: bad amount: 100000000000.01 (that's more than this counts; the most is 100,000,000,000)",
}
# paid-only line is a parse of "paid, Ana" with no gift/people — parse succeeds; share refuses
del cases["paid, Ana"]
for t, want in cases.items():
    eq(err(gift.parse, t), want, repr(t))
# LIMIT itself is accepted
eq(gift.parse("gift, 100000000000")[0], 10 ** 13, "LIMIT ok")

shares = {
    "": "the gift price is missing (write it as: gift, amount)",
    "Ana, 5": "the gift price is missing (write it as: gift, amount)",
    "gift, 5": "nobody listed (write who is chipping in, like Ana, 1,000, or a bare name)",
    "gift, 5\npaid, Ana": "nobody listed (write who is chipping in, like Ana, 1,000, or a bare name)",
    "gift, 5\nAna, 1\npaid, Bo": "who is Bo? nobody by that name is chipping in",
    "gift, 10\nAna, 12": "the fixed amounts add up to 12, which is 2 more than the 10 gift",
    "gift, 10\nAna, 10.01": "the fixed amounts add up to 10.01, which is 0.01 more than the 10 gift",
    "gift, 10\nAna, 4": "the fixed amounts add up to 4, which is 6 short of the 10 gift (add someone to split what's left, or raise a fixed amount)",
    "gift, 10\nA, up to 3\nB, up to 3\nC, up to 3": "the caps can't reach the gift: all together (with any fixed amounts) they add up to 9, which is 1 short of 10 (raise a cap, or add someone)",
    "gift, 10\nAna, 2\nA, up to 3\nB, up to 3": "the caps can't reach the gift: all together (with any fixed amounts) they add up to 8, which is 2 short of 10 (raise a cap, or add someone)",
}
for t, want in shares.items():
    eq(err(go, t), want, repr(t))
eq(err(gift.share, None, [], None), "the gift price is missing (write it as: gift, amount)", "share no gift")
eq(err(gift.share, 100, [], None), "nobody listed (write who is chipping in, like Ana, 1,000, or a bare name)", "share nobody")

rng = random.Random(75)
ok_random = 0
for _ in range(300):
    n = rng.randint(1, 8)
    price = rng.randint(1, 10 ** 8)
    ppl = []
    for i in range(n):
        kind = rng.choice(["fixed", "cap", "even", "even"])
        if kind == "even":
            ppl.append(("p%d" % i, "even", None, i + 1, "x"))
        else:
            ppl.append(("p%d" % i, kind, rng.randint(1, 10 ** 7), i + 1, "x"))
    try:
        rs, _ = gift.share(price, ppl)
    except ValueError as e:
        msg = str(e)
        assert "more than the" in msg or "short of" in msg or "can't reach" in msg, msg
        continue
    ok_random += 1
    eq(sum(r[3] for r in rs), price, "sum == gift")
    for r in rs:
        if r[1] == "fixed":
            eq(r[3], r[2], "fixed exact")
        if r[1] == "cap":
            assert r[3] <= r[2], (r, "above cap")
    uncapped = [r[3] for r in rs if r[1] != "fixed" and not (r[1] == "cap" and r[3] == r[2])]
    if len(uncapped) >= 2:
        assert max(uncapped) - min(uncapped) <= 1, uncapped
    elif len(uncapped) == 1:
        pass
    for r in rs:
        if r[1] == "cap" and r[3] == r[2] and uncapped:
            assert all(r[2] <= u + 1 for u in uncapped), (r, uncapped)
assert ok_random >= 50, "too few random groups that add up: %d" % ok_random

with tempfile.TemporaryDirectory() as tmp:
    f = os.path.join(tmp, "g.txt")
    with open(f, "w", encoding="utf-8-sig") as fh:
        fh.write(EX + "\n")
    run = lambda *a: subprocess.run([sys.executable, str(HERE / "gift.py"), *a], capture_output=True, text=True)
    r = run(f)
    eq((r.returncode, r.stdout), (0, "Ana: fixed, pays 1,000 (paid the gift)\n"
                                     "Ben: up to 800, pays 800 (capped)\n"
                                     "Cy: even, pays 2,100\n"
                                     "Dee: even, pays 2,100\n"
                                     "Gift 6,000. Ana 1,000, Ben 800, Cy 2,100, Dee 2,100. "
                                     "Owes Ana: Ben 800, Cy 2,100, Dee 2,100.\n"), "cli")
    with open(f, "w", encoding="utf-8") as fh:
        fh.write("gift, 5\nAna, lots\n")
    r = run(f)
    eq((r.returncode, r.stdout), (1, "gift: line 2: write it as: name, amount (or name, up to amount, or a bare name): Ana, lots\n"), "cli refuse")
    with open(f, "w", encoding="utf-8") as fh:
        fh.write("gift, 10\nAna, 12\n")
    eq(run(f).stdout, "gift: the fixed amounts add up to 12, which is 2 more than the 10 gift\n", "cli share error")
    eq(run(os.path.join(tmp, "missing")).returncode, 1, "missing file")
    for a in [(), (f, f), ("--help",), ("--",)]:
        r = run(*a)
        eq(r.returncode, 2, "usage %r" % (a,))
        eq(r.stdout, gift.__doc__.split("\n\n", 1)[1].rstrip() + "\n", "usage text %r" % (a,))
        assert "Needs rent.py beside it" in r.stdout, r.stdout
    # the docstring's example is the page's example, and it adds up
    doc = "\n".join(l.strip() for l in gift.__doc__.split("\n") if l.startswith("          "))
    eq(doc, EX, "docstring example")

page = (HERE / "gift.html").read_text(encoding="utf-8")
eq(page.split('<textarea id="in">', 1)[1].split("</textarea>", 1)[0], EX, "page example")
script = page.split("<script>", 1)[1]
for banned in ["fetch", "XMLHttpRequest", "localStorage", "http"]:
    assert banned not in script, banned
node = shutil.which("node")
if not node:
    print("SKIP gift.html: node not installed (gift.py is tested)"); print("ok test_gift"); sys.exit(0)
logic = page.split("// LOGIC START", 1)[1].split("\n", 1)[1].split("// LOGIC END", 1)[0]
js = logic + """
const texts = @TEXTS@, monies = @MONIES@;
const tryit = f => { try { return f(); } catch (e) { return e.message; } };
console.log(JSON.stringify([
  texts.map(t => tryit(() => parse(t))),
  texts.map(t => tryit(() => { const [rs, payer] = share(...parse(t)); return [rs, payer, rs.map(r => row(...r, payer)), summary(rs, payer), summary(rs)]; })),
  monies.map(money)]));
"""
texts = list(cases) + list(shares) + [EX, "COST, 6,000\nAna, 1,000\nBen, up to 800\nCy\nDee, even\npaid, ana",
    "gift, 0.16\nA, up to 0.05\nB, up to 1\nC, up to 1", "gift, 10\nAna, 9.99",
    "gift, 0.10\nA, up to 0.03\nB, up to 0.03\nC, up to 0.03", "gift, 5\nBen, up to up to 800",
    "gift, 1\nA\nB\nC", "gift, 1,000\nAna, 1,000\nCy\nDee, even\npaid, Ana", "gift, 100\nAna, up to 80\nBen",
    "gift, 0.10\nAna, up to 0.01\nBen\nCy", "gift, 100\nA, up to 20\nB, up to 20\nC",
    "gift, 10\nA, up to 4\nB, up to 3\nC, up to 3", "gift, 0.03\nA, up to 0.01\nB, up to 0.01\nC, up to 0.01",
    "gift, 50\nAna\npaid, Ana", "gift, 1,000\nAna, 1,000",
    "\ufeff COST , ₹1,234.5 \nCAME, even\nBen, Up  To  2,00,000\nAnn Lee, 100000000000",
    "gift, 5\nGifted, 3\nCostco", "gift, 5\nZoë\npaid, ZOË",
    "gift, 1\nAnn Andrews\nDand, even", "gift\u00a0,\u00a03\x0bAna\r\nBen, even\u2028paid, Ana",
    "Gift, 5\nANA, Even\nBen, UP TO 1", "gift, 5\nAna,even", "cost,5\nBo",
    "gift, 0.05\nA, up to 0.02\nB, up to 0.02\nC, up to 0.02", "gift, 100000000000\nAna"]
for _ in range(100):
    n = rng.randint(1, 6)
    lines = ["gift, %s" % gift.money(rng.randint(1, 10 ** 7))]
    seen = set()
    for i in range(n):
        name = "p%d" % i
        kind = rng.choice(["fixed", "cap", "even", "even", "bare"])
        if kind == "fixed":
            lines.append("%s, %s" % (name, gift.money(rng.randint(1, 10 ** 6))))
        elif kind == "cap":
            lines.append("%s, up to %s" % (name, gift.money(rng.randint(1, 10 ** 6))))
        elif kind == "bare":
            lines.append(name)
        else:
            lines.append("%s, even" % name)
        seen.add(name)
    if rng.random() < .4:
        lines.append("paid, %s" % rng.choice(list(seen) + ["q"]))
    if rng.random() < .3:
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
    rs, payer = gift.share(*gift.parse(t))
    return [rs, payer, [gift.row(*x, paid_name=payer) for x in rs], gift.summary(rs, payer), gift.summary(rs)]


want = [[py(lambda t=t: json.loads(json.dumps(gift.parse(t)))) for t in texts],
        [py(lambda t=t: json.loads(json.dumps(full(t)))) for t in texts],
        [gift.money(c) for c in monies]]
got = json.loads(r.stdout)
for i, name in enumerate(["parse", "share", "money"]):
    eq(len(got[i]), len(want[i]), "node %s count" % name)
    for k, (g, w) in enumerate(zip(got[i], want[i])):
        eq(g, w, "node %s %r" % (name, texts[k] if i < 2 else monies[k]))
# the whole page in node with a stub document: the example shows the same lines as gift.py
stub = """
const els = {};
const document = { getElementById: id => els[id] || (els[id] = { value: "", innerHTML: "", addEventListener() {} }),
                   createElement: () => { const d = { set textContent(s) { d.innerHTML = s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); } }; return d; } };
"""
body = page.split("<script>", 1)[1].split("</script>", 1)[0]
r2 = subprocess.run([node, "-e", stub + body.replace("run();\n", "") + """
console.log(JSON.stringify(@INS@.map(t => { els.in.value = t; run(); return els.out.innerHTML; })));
""".replace("@INS@", json.dumps([EX, "gift, 5\nAna, lots", "gift, 5\n<a>"]))], capture_output=True, text=True, timeout=30)
assert r2.returncode == 0, r2.stderr
shown = json.loads(r2.stdout)
eq(shown[0], "<table>" + "".join("<tr><td>%s</td></tr>" % gift.row(*x, paid_name="Ana") for x in rows) + "</table>"
   '<div class="line">%s</div>' % gift.summary(rows, "Ana"), "page shows the example")
assert shown[1].startswith('<p class="err">line 2: write it as: name, amount'), shown[1]
assert "&lt;a&gt;" in shown[2] and "<a>" not in shown[2], shown[2]
assert len(texts) >= 150, len(texts)
print("ok test_gift (%d texts, %d random groups that added up)" % (len(texts), ok_random))
