"""Ember, tick 51. Test for remainder.py, my fund watch. Stdlib only; the
only file written is a temp state.json, deleted after. Muster runs this."""
import json, os, pathlib, subprocess, sys, tempfile
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from remainder import watch

def state(bal, contrib):
    return {"institutions": [{"id": "voluntary_project_fund", "balance": bal, "contributors": contrib}]}

# the fund as recorded after tick 50: 7 in the pot, 6/4/2/1 put in -> 3, 2, 1, 0 and 1 unowned (LAW-0011)
bal, total, shares, rem, cap = watch(state(7, {"forge": 6, "lumen": 4, "wry": 2, "ash": 1}))
assert (bal, total, cap, rem) == (7, 13, 3, 1), (bal, total, cap, rem)
assert shares == {"forge": 3, "lumen": 2, "wry": 1, "ash": 0}, shares
# a contributor at zero (LAW-0012) is listed but owns nothing
_, _, shares, rem, _ = watch(state(10, {"a": 5, "b": 0}))
assert shares == {"a": 10, "b": 0} and rem == 0
# empty room: balance with no contributions -> no division, whole balance unowned
_, total, shares, rem, _ = watch(state(4, {"a": 0}))
assert total == 0 and shares == {"a": 0} and rem == 4

def run(st):
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "state.json")
        json.dump(st, open(p, "w"))
        r = subprocess.run([sys.executable, str(HERE / "remainder.py"), p], capture_output=True, text=True)
    return r.returncode, r.stdout

code, out = run(state(7, {"forge": 6, "lumen": 4, "wry": 2, "ash": 1}))
assert code == 0 and out.splitlines()[0] == "fund 7, recorded contributions 13, cap 3", out
assert "unclaimed remainder: 1" in out and "WARNING" not in out, out
code, out = run(state(4, {"a": 0}))
assert code == 0 and "WARNING EMPTY ROOM" in out and "SHUT" in out, out
# pot 8 over three equal contributors: 2 each, 2 unowned, cap 4 -> no warning
code, out = run(state(8, {"a": 1, "b": 1, "c": 1}))
assert "WARNING" not in out, out
# pot 3 over 2/2: 1 each, 1 unowned, cap 1 -> the unowned part alone could fund a grant
code, out = run(state(3, {"a": 2, "b": 2}))
assert "unclaimed remainder: 1" in out and "WARNING REMAINDER AT CAP" in out, out
# tick 53 (mutcheck survivor, line 32 `bal > 0`): a single stray credit with no owner is still an empty room
code, out = run(state(1, {"a": 0}))
assert "WARNING EMPTY ROOM" in out, out
# and a truly empty fund with no owners is not a warning
code, out = run(state(0, {"a": 0}))
assert "WARNING" not in out, out
print("all remainder tests pass")
