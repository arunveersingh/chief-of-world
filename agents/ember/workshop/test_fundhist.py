"""Ember, tick 52. Test for fundhist.py: each dashboard fund_history frame against
the fund balance in world/state.json at the commit credit_history names.
Builds a throwaway git repo in a temp folder and runs fundhist.py there.
Stdlib plus the git binary; writes nothing outside the temp folder."""
import json, os, pathlib, subprocess, sys, tempfile
TOOL = pathlib.Path(__file__).resolve().parent / "fundhist.py"

def git(d, *a):
    return subprocess.run(["git", "-C", d, *a], capture_output=True, text=True, check=True).stdout.strip()

def commit_state(d, fund):
    os.makedirs(os.path.join(d, "world"), exist_ok=True)
    json.dump({"shared_resources": {"voluntary_project_fund": fund}}, open(os.path.join(d, "world/state.json"), "w"))
    git(d, "add", "-A"); git(d, "commit", "-qm", "s")
    return git(d, "rev-parse", "HEAD")

def run(d, credit, fund):
    os.makedirs(os.path.join(d, "docs/data"), exist_ok=True)
    json.dump({"credit_history": credit, "fund_history": fund}, open(os.path.join(d, "docs/data/world.json"), "w"))
    r = subprocess.run([sys.executable, str(TOOL)], cwd=d, capture_output=True, text=True)
    assert r.returncode == 0 and "Traceback" not in r.stderr, r.stderr
    return r.stdout.splitlines()

with tempfile.TemporaryDirectory() as d:
    git(d, "init", "-q"); git(d, "config", "user.email", "t@t"); git(d, "config", "user.name", "t")
    c1 = commit_state(d, 7)                      # balance as a bare number
    c2 = commit_state(d, {"balance": 3})         # balance inside a dict (the older shape)
    credit = [{"tick": 1, "commit": c1}, {"tick": 2, "commit": c2}, {"tick": 3, "commit": "0" * 40}]
    # every frame matches its commit; tick 3's commit doesn't exist, tick 4 has none -> both skipped
    out = run(d, credit, [{"tick": 1, "balance": 7}, {"tick": 2, "balance": 3}, {"tick": 3, "balance": 9}, {"tick": 4, "balance": 1}])
    assert out == ["fund_history: 2 OK, 0 BAD, 2 skipped"], out
    # a dashboard frame that disagrees with the record is named, not hidden
    out = run(d, credit, [{"tick": 1, "balance": 6}, {"tick": 2, "balance": 3}])
    assert out == ["BAD tick 1 dash 6 state 7", "fund_history: 1 OK, 1 BAD, 0 skipped"], out
print("all fundhist tests pass")
