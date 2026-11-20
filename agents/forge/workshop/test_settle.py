"""settle.py and settle.html must give the same payments, and the payments must make everyone even (Forge, tick 62)."""
import itertools, json, os, pathlib, random, shutil, subprocess, sys, tempfile
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
from settle import cents, balances, steps, settle, parse, money, main

# amounts
assert [cents(t) for t in ["1", "1.5", ".25", "12.50", " 3.07 ", "0"]] == [100, 150, 25, 1250, 307, 0]
for bad in ["", ".", "1.234", "a", "-1", "1,5", "١"]:
    try: cents(bad); raise AssertionError(bad)
    except ValueError as e: assert "bad amount" in str(e)
assert money(5) == "0.05" and money(1250) == "12.50"

# the page's example
p, s = parse("Asha, 90, \nBen, 30, Ben Cy\nCy, 12.50, Asha Cy")
assert p == ["Asha", "Ben", "Cy"] and s[0] == ("Asha", 9000, [])
b = balances(p, s)
assert b == {"Asha": 5375, "Ben": -1500, "Cy": -3875}, b
assert settle(b) == [("Cy", "Asha", 3875), ("Ben", "Asha", 1500)]
# leftover cents go one each, alphabetically; total always balances
assert balances(["c", "a", "b"], [("a", 100, [])]) == {"c": -33, "a": 66, "b": -33}
assert balances(["x"], [("x", 101, ["z", "y"])]) == {"x": 101, "z": -50, "y": -51}
assert balances(["a", "b"], [("a", 10, ["b", "b"])]) == {"a": 10, "b": -10}     # repeated name counts once
# the working: one row per spend, same split as balances
assert steps(["c", "a", "b"], [("a", 100, []), ("b", 7, ["c", "c"]), ("c", 5, ["b", "a"])]) == [
    ("a", 100, ["a", "b", "c"], 33, 1, True), ("b", 7, ["c"], 7, 0, False), ("c", 5, ["a", "b"], 2, 1, False)]
# ties broken by name; already even means no payments
assert settle({"b": -5, "a": -5, "z": 10}) == [("a", "z", 5), ("b", "z", 5)]
assert settle({"a": 0, "b": 0}) == [] and settle({}) == []
assert settle({"a": -1, "b": 1}) == [("a", "b", 1)]          # a single cent still gets paid
assert settle({"a": -7, "b": 3, "c": 4}) == [("a", "c", 4), ("a", "b", 3)]

def settle_err(bal):
    try:
        settle(bal)
    except ValueError as e:
        return str(e)
    raise AssertionError("no error for %r" % (bal,))

assert settle_err({"a": 0, "b": 5}) == "balances must add up to zero (they add up to 0.05)"
assert settle_err({"a": 5}) == "balances must add up to zero (they add up to 0.05)"
assert settle_err({"a": -5}) == "balances must add up to zero (they add up to -0.05)"
assert settle_err({"a": 500}) == "balances must add up to zero (they add up to 5.00)"
assert settle_err({"a": -500}) == "balances must add up to zero (they add up to -5.00)"
assert settle_err({"a": 100, "b": 250}) == "balances must add up to zero (they add up to 3.50)"
assert settle_err({"a": 5, "b": -3}) == "balances must add up to zero (they add up to 0.02)"
assert settle({"a": 0, "b": 0, "c": 0}) == []
# comments, blank lines, bad lines
assert parse("# trip\n\nA, 1 # snack\n") == (["A"], [("A", 100, [])])
# Wry's break-it log (tick 63): a thousands comma and a currency sign
assert parse("Ann, 1,000") == (["Ann"], [("Ann", 100000, [])])
assert parse("Ann, $20\nBen, 0") == (["Ann", "Ben"], [("Ann", 2000, []), ("Ben", 0, [])])
assert parse("Ann, 1,000, Ben Cy")[1] == [("Ann", 100000, ["Ben", "Cy"])]
assert parse("Ann, €3.5, Bo")[1] == [("Ann", 350, ["Bo"])] and parse("Ann, ₹1,234,567.89")[1] == [("Ann", 123456789, [])]
assert parse("Ann, 5,")[1] == [("Ann", 500, [])] and parse("Ann,5,Bo")[1] == [("Ann", 500, ["Bo"])]
for bad, words in [("Ann, 1,00", "00 looks like part of a number"), ("Ann, 1, 000 Ben", "000 looks like"),
                   ("Ann, 1,0000", "0000 looks like"), ("Ann, 12.345", "bad amount: 12.345"), ("Ann, x", "bad amount: x"),
                   ("Ann, $$5", "bad amount"), ("Ann", "write it as"), ("\n, 5", "line 2: write it as"), ("1, 5", "1 looks like"),
                   ("Ann, x, Bo", "bad amount: x, Bo ("), ("Ann, 1., Bo", "bad amount: 1. ("), ("Ann, $, Bo, Cy", "bad amount: $, Bo, Cy (")]:
    try: parse(bad); raise AssertionError(bad)
    except ValueError as e: assert words in str(e) and str(e).startswith("line "), (bad, str(e))
for bad in ["A", ", 5", "A, x"]:
    try: parse(bad); raise AssertionError(bad)
    except ValueError: pass

# random: payments make everyone even, never more than people - 1
rng = random.Random(62)
CASES = []
for _ in range(60):
    names = rng.sample(["Asha", "Ben", "Cy", "Dev", "Eli", "Fay"], rng.randint(1, 6))
    lines = []
    for _ in range(rng.randint(0, 6)):
        who = " ".join(rng.sample(names, rng.randint(0, len(names))))
        lines.append("%s, %d.%02d, %s" % (rng.choice(names), rng.randint(0, 200), rng.randint(0, 99), who))
    text = "\n".join(lines)
    CASES.append(text)
    pe, sp = parse(text)
    bal = balances(pe, sp)
    assert sum(bal.values()) == 0
    pays = settle(bal)
    assert len(pays) <= max(len(bal) - 1, 0) and all(x > 0 for _, _, x in pays)
    after = dict(bal)
    for a, c, x in pays:
        after[a] += x; after[c] -= x
    assert set(after.values()) <= {0}, (text, pays)
    rebuilt = {n: 0 for n in pe}
    for payer, amt, names, each, spare, _ in steps(pe, sp):
        rebuilt[payer] += amt
        for i, n in enumerate(names):
            rebuilt[n] -= each + (i < spare)
    assert rebuilt == bal, text

# CLI
with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
    f.write("Asha, 90, \nBen, 30, Ben Cy\nCy, 12.50, Asha Cy\n")
r = subprocess.run([sys.executable, str(HERE / "settle.py"), f.name], capture_output=True, text=True)
assert r.returncode == 0 and r.stdout == "Cy pays Asha 38.75\nBen pays Asha 15.00\n", r.stdout
with open(f.name, "w") as g:
    g.write("Ann, 1,000\nBen, 0\n")
r = subprocess.run([sys.executable, str(HERE / "settle.py"), f.name], capture_output=True, text=True)
assert r.returncode == 0 and r.stdout == "Ben pays Ann 500.00\n" and "000 pays" not in r.stdout, r.stdout
with open(f.name, "w") as g:
    g.write("Ann, 20 dollars\n")
r = subprocess.run([sys.executable, str(HERE / "settle.py"), f.name], capture_output=True, text=True)
assert r.returncode == 1 and r.stderr == "settle: line 1: bad amount: 20 dollars (write 12.50 or 1,000)\n" and "Traceback" not in r.stderr, r.stderr
r = subprocess.run([sys.executable, str(HERE / "settle.py")], capture_output=True, text=True)
assert r.returncode == 2 and "Usage:" in r.stdout
os.unlink(f.name)

# the page: offline, and same logic as settle.py
page = (HERE / "settle.html").read_text()
script = page.split("<script>")[1]
assert "fetch(" not in page and "XMLHttpRequest" not in page and "localStorage" not in page and "http" not in script
node = shutil.which("node")
if not node:
    print("SKIP settle.html: node not installed (settle.py is tested)"); sys.exit(0)
logic = page.split("// LOGIC START", 1)[1].split("\n", 1)[1].split("// LOGIC END", 1)[0]
ALL = CASES + ["Ann, 1,000", "Ann, $20\nBen, 0", "Ann, 1,000, Ben Cy", "Ann, €3.5, Bo", "Ann, ₹1,234,567.89\nBo, 1", "Ann,5,Bo", "Ann, 5,", "Asha, 90, \nBen, 30, Ben Cy\nCy, 12.50, Asha Cy", "a, 1.00, c b a", "x, 101, z y", "a, 10, b b"]
js = logic + "\nconst C = " + json.dumps(ALL) + """;
console.log(JSON.stringify(C.map(t => { const [p, s] = parse(t); const b = balances(p, s); return [p, b, settle(b), steps(p, s)]; })));"""
r = subprocess.run([node, "-e", js], capture_output=True, text=True, timeout=30)
assert r.returncode == 0, r.stderr
for text, (p, b, pays, st) in zip(ALL, json.loads(r.stdout)):
    pe, sp = parse(text)
    bal = balances(pe, sp)
    assert p == pe and b == bal and pays == [list(t) for t in settle(bal)], (text, pays)
    assert st == [list(r) for r in steps(pe, sp)], (text, st)
js = logic + '\nfor (const t of ["", ".", "1.234", "a", "-1"]) { try { cents(t); console.log("ok " + t); } catch (e) { console.log(e.message); } }'
r = subprocess.run([node, "-e", js], capture_output=True, text=True, timeout=30)
assert r.stdout.count("bad amount") == 5, r.stdout
BAD = ["Ann, 1,00", "Ann, 1, 000 Ben", "Ann, 1,0000", "Ann, 12.345", "Ann, x", "Ann, $$5", "Ann", "\n, 5", "1, 5", "Ann, 20 dollars", "Ann, .", "Ann, x, Bo", "Ann, 1., Bo", "Ann, $, Bo, Cy"]
js = logic + "\nfor (const t of " + json.dumps(BAD) + ") { try { parse(t); console.log('ok'); } catch (e) { console.log(e.message); } }"
r = subprocess.run([node, "-e", js], capture_output=True, text=True, timeout=30)
want = []
for b in BAD:
    try: parse(b); want.append("ok")
    except ValueError as e: want.append(str(e))
assert r.stdout.splitlines() == want, (r.stdout, want)
# the page's settle() must refuse the same non-zero-sum dicts
js = logic + """
const tryit = f => { try { return JSON.parse(JSON.stringify(f())); } catch (e) { return e.message; } };
const cases = [{a: 0, b: 5}, {a: 5}, {a: -5}, {a: 500}, {a: -500}, {a: 100, b: 250}, {a: 5, b: -3}, {a: 0, b: 0}, {}, {a: 0, b: 0, c: 0}, {a: -1, b: 1}];
console.log(JSON.stringify(cases.map(b => tryit(() => settle(b)))));
"""
r = subprocess.run([node, "-e", js], capture_output=True, text=True, timeout=30)
assert r.returncode == 0, r.stderr
want = []
for b in [{"a": 0, "b": 5}, {"a": 5}, {"a": -5}, {"a": 500}, {"a": -500}, {"a": 100, "b": 250}, {"a": 5, "b": -3}, {"a": 0, "b": 0}, {}, {"a": 0, "b": 0, "c": 0}, {"a": -1, "b": 1}]:
    try:
        want.append([list(t) for t in settle(b)])
    except ValueError as e:
        want.append(str(e))
assert json.loads(r.stdout) == want, (r.stdout, want)
print("all settle tests pass")
