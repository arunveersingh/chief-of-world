import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import clock
root = clock.repo_root(os.path.dirname(__file__))
res, st = clock.main(["clock.py", "--repo", root])
assert res.get("LAW-0007") == 16, res
assert all(s[2] == "LAW-0007" for s in st)
assert not any(s[0] == "LAW-0007" for s in st), "header line must not count as stale"
# v2: annotated lines are not stale
import tempfile
d = tempfile.mkdtemp(); law = os.path.join(d, "LAW-9.md")
open(law, "w").write("**Sunset:** expires after tick 16\n**Effect:** sunset (after tick 12; since LAW-0010: after tick 16)\n**Effect:** this expires after tick 12\n")
got = clock.stale({"LAW-9": law}, {"LAW-9": 16})
assert [g[1] for g in got] == [3], got
assert not any(s[0] in ("LAW-0008", "LAW-0009") for s in st), "Chief's annotations must read clean"
print("all clock tests pass")
