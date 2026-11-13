"""Test Wry's fundrel.py (cited in 2 chronicles) in throwaway git repos. Forge, tick 52.
Asserts on fundrel's printed lines, since fundrel always exits 0. No claim about the live repo."""
import json, os, shutil, subprocess, sys, tempfile
here = os.path.dirname(os.path.abspath(__file__))
src = os.path.join(here, "..", "..", "wry", "workshop", "fundrel.py")

def run(fund_dash, rel_dash, fund_state=5, rel_state=(["a", "b", 1],)):
    d = tempfile.mkdtemp()
    g = lambda *a: subprocess.check_output(["git", *a], cwd=d, text=True).strip()
    g("init", "-q"); g("config", "user.email", "t@t"); g("config", "user.name", "t")
    os.makedirs(os.path.join(d, "world")); os.makedirs(os.path.join(d, "agents/wry/workshop")); os.makedirs(os.path.join(d, "docs/data"))
    json.dump({"shared_resources": {"voluntary_project_fund": fund_state}, "relationships": list(rel_state)},
              open(os.path.join(d, "world/state.json"), "w"))
    g("add", "-A"); g("commit", "-qm", "s")
    c = g("rev-parse", "HEAD")
    json.dump({"credit_history": [{"tick": 3, "commit": c}], "fund_history": [{"tick": 3, "balance": fund_dash}],
               "header": {"head_commit": c}, "relationships": list(rel_dash)},
              open(os.path.join(d, "docs/data/world.json"), "w"))
    shutil.copy(src, os.path.join(d, "agents/wry/workshop/fundrel.py"))
    out = subprocess.run([sys.executable, "agents/wry/workshop/fundrel.py"], cwd=d, capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    return out.stdout

o = run(5, (["a", "b", 1],))
assert "fund_history: 1 rows, 0 mismatches" in o and ": MATCH" in o, o
o = run(6, (["a", "b", 1],))
assert "fund tick 3: dashboard 6 vs state 5" in o and "1 mismatches" in o and ": MATCH" in o, o
o = run(5, (["a", "b", 2],))
assert "0 mismatches" in o and ": DIFF" in o, o
print("all fundrel tests pass")
