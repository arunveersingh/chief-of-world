"""Test fund_status.py on a fake state. Forge, tick 54."""
import json, os, subprocess, sys, tempfile
tool = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fund_status.py")
d = tempfile.mkdtemp(); os.makedirs(os.path.join(d, "world"))
json.dump({"tick": 9, "institutions": [{"id": "voluntary_project_fund", "balance": 7,
           "contributors": {"x": 6, "y": 4, "z": 2, "w": 1}, "spending_rules": ["LAW-0007"]}]},
          open(os.path.join(d, "world/state.json"), "w"))
r = subprocess.run([sys.executable, tool, "--repo", d], capture_output=True, text=True)
assert r.returncode == 0, r
L = r.stdout.splitlines()
assert L[0].startswith("Tick 9 | fund balance: 7 | votes: one per contributor"), L
assert "weight" not in r.stdout.replace("unweighted", ""), L        # no credit-weighted voting claim
# §7: 6*7//13=3, 4*7//13=2, 2*7//13=1, 1*7//13=0 (fractions stay in the fund)
assert [l.split()[-2] for l in L[1:5]] == ["3", "2", "1", "0"], L
assert L[1].split()[0] == "x" and L[4].split()[0] == "w", L
assert "LAW-0007" in L[5], L
assert subprocess.run([sys.executable, tool, "bad"], capture_output=True).returncode == 64
print("all fund_status tests pass")
