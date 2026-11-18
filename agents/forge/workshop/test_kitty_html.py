"""kitty.html must give the same money as kitty.py (Forge, tick 61).

Runs the page's LOGIC block in node and compares shares, spends and leaving orders with kitty.py on
fixed cases. If node isn't installed, it says so and exits 0: the page can't be checked here, and
kitty.py's own test still runs."""
import json, pathlib, shutil, subprocess, sys
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
from kitty import resolve, orders

page = (HERE / "kitty.html").read_text()
logic = page.split("// LOGIC START", 1)[1].split("\n", 1)[1].split("// LOGIC END", 1)[0]
assert "fetch(" not in page and "XMLHttpRequest" not in page and "localStorage" not in page and "http" not in page.split("<script>")[1], "page must stay offline and save nothing"
node = shutil.which("node")
if not node:
    print("SKIP kitty.html: node not installed (kitty.py is still tested)"); sys.exit(0)

CASES = [
    (40, {"Asha": 20, "Ben": 10, "Cy": 10}, ["Asha", "Ben", "Cy"], ["Ben"], [("paint", 15, "Asha", ["Cy"])]),
    (40, {"Asha": 20, "Ben": 10, "Cy": 10}, ["Asha", "Ben", "Cy", "Dev"], [], [("paint", 15, "Asha", ["Cy"]), ("tea", 5, "Cy", ["Asha", "Dev"])]),
    (3, {"f": 6, "l": 4, "w": 2, "a": 1}, ["f", "l", "w", "a"], ["f", "l"], [("x", 1, "w", ["a"])]),
    (7, {"a": 1}, ["a"], [], [("solo", 1, "a", [])]),
    (0, {"a": 0, "b": 0}, ["a", "b"], ["a"], []),
    (101, {"p": 3, "q": 3, "r": 1}, ["p", "q", "r"], ["p", "q", "r"], [("late", 0, "p", ["q"])]),
]
js = logic + "\nconst C = " + json.dumps([[p, u, pe, l, [list(s) for s in sp]] for p, u, pe, l, sp in CASES]) + """;
console.log(JSON.stringify(C.map(([p, u, pe, l, sp]) => [resolve(p, u, pe, l, sp), orders(p, u, l)])));"""
r = subprocess.run([node, "-e", js], capture_output=True, text=True, timeout=30)
assert r.returncode == 0, r.stderr
got = json.loads(r.stdout)
for (pot, put, people, leavers, spends), (res, ords) in zip(CASES, got):
    paid, out, left = resolve(pot, put, people, leavers, spends)
    want = [paid, [[n, a, ok, why] for n, a, ok, why in out], left]
    assert res == want, (pot, put, leavers, res, want)
    assert ords == orders(pot, put, leavers), (ords, orders(pot, put, leavers))
assert got[0][0][0] == {"Ben": 10} and got[0][0][2] == 15        # the page's own example: Ben gets 10, paint passes
print("all kitty.html tests pass")
