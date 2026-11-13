"""Tests dashsums.py on a fake repo: one consistent state/dashboard pair passes, and each kind of drift is caught."""
import copy, json, os, shutil, subprocess, sys, tempfile
here = os.path.dirname(os.path.abspath(__file__))
STATE = {"agents": [{"id": "a", "credits": 5, "reputation": 1}, {"id": "b", "credits": 3, "reputation": 2}],
         "shared_resources": {"voluntary_project_fund": 2, "compute_credits_total_in_circulation": 10},
         "institutions": [{"id": "voluntary_project_fund", "contributors": {"a": 2}}],
         "laws_in_force": ["LAW-0001", "LAW-0002"]}
DASH = {"header": {"credits_in_circulation": 10, "fund_balance": 2},
        "fund": {"balance": 2, "contributors": {"a": 2}, "spending_rules": ["LAW-0001", "LAW-0002"]},
        "citizens": [{"id": "a", "credits": 5, "reputation": 1}, {"id": "b", "credits": 3, "reputation": 2}],
        "laws_in_force": ["LAW-0001", "LAW-0002"]}

def run(state, dash):
    d = tempfile.mkdtemp()
    for sub in ("world", "docs/data", "governance/laws", "agents/forge/workshop"): os.makedirs(os.path.join(d, sub))
    shutil.copy(os.path.join(here, "dashsums.py"), os.path.join(d, "agents/forge/workshop"))
    json.dump(state, open(os.path.join(d, "world/state.json"), "w"))
    json.dump(dash, open(os.path.join(d, "docs/data/world.json"), "w"))
    for f in ("LAW-0001-one-rulebook.md", "LAW-0002-renew-one-rulebook.md"):
        open(os.path.join(d, "governance/laws", f), "w").write("x\n")
    return subprocess.run([sys.executable, os.path.join(d, "agents/forge/workshop/dashsums.py")], capture_output=True, text=True)

r = run(STATE, DASH)
assert r.returncode == 0 and "BAD" not in r.stdout, r.stdout + r.stderr
def drift(fn):
    s, d = copy.deepcopy(STATE), copy.deepcopy(DASH); fn(s, d); r = run(s, d)
    assert r.returncode == 1 and "BAD" in r.stdout, r.stdout + r.stderr
drift(lambda s, d: s["agents"][0].update(credits=6))                      # credits + fund != circulation
drift(lambda s, d: d["citizens"][1].update(reputation=9))                 # per-citizen mismatch
drift(lambda s, d: d["fund"].update(balance=3))                           # fund balance mismatch
drift(lambda s, d: s["laws_in_force"].append("LAW-0003"))                 # law with no file
drift(lambda s, d: d["fund"].update(spending_rules=["LAW-0001"]))         # latest renewal missing
print("all dashsums tests pass")
