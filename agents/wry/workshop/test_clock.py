import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import clock
root = clock.repo_root(os.path.dirname(__file__))
res, st = clock.main(["clock.py", "--repo", root])
assert res.get("LAW-0007") == 16, res
assert all(s[2] == "LAW-0007" for s in st)
assert not any(s[0] == "LAW-0007" for s in st), "header line must not count as stale"
print("all clock tests pass")
