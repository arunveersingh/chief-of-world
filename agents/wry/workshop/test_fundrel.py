import json, os, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(__file__))
import fundrel

d = tempfile.mkdtemp()
env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@x", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@x")
run = lambda *a: subprocess.check_output(a, cwd=d, text=True, env=env).strip()
os.makedirs(os.path.join(d, "world")); os.makedirs(os.path.join(d, "docs/data"))
run("git", "init", "-q")
commits = []
for fund in (0, 3, 7):  # three ticks of history
    json.dump({"shared_resources": {"voluntary_project_fund": fund}, "relationships": [{"a": "wry", "b": "ash"}]},
              open(os.path.join(d, "world/state.json"), "w"))
    run("git", "add", "-A"); run("git", "commit", "-qm", "t%d" % fund)
    commits.append(run("git", "rev-parse", "HEAD"))

def dash(balances, rel):
    json.dump({"credit_history": [{"tick": i, "commit": c} for i, c in enumerate(commits)],
               "fund_history": [{"tick": i, "balance": b} for i, b in enumerate(balances)],
               "header": {"head_commit": commits[-1]}, "relationships": rel},
              open(os.path.join(d, "docs/data/world.json"), "w"))

dash([0, 3, 7], [{"a": "wry", "b": "ash"}])
lines, n, bad, ok = fundrel.check(d)
assert (n, bad, ok) == (3, 0, True), lines
dash([0, 4, 7], [{"a": "wry", "b": "ash"}])   # one wrong balance, read at its own commit, not HEAD
lines, n, bad, ok = fundrel.check(d)
assert bad == 1 and "fund tick 1: dashboard 4 vs state 3" in lines[0], lines
dash([7, 7, 7], [{"a": "wry", "b": "ash"}])   # using today's balance for old rows is wrong twice
assert fundrel.check(d)[2] == 2
dash([0, 3, 7], [])                            # relationships must match head, exactly
assert fundrel.check(d)[3] is False

# tick 55: the CLI exit code, each fault on its own (kills `or -> and` on the exit line)
cli = lambda: subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "fundrel.py"), d],
                             capture_output=True, text=True, cwd=tempfile.gettempdir())
dash([0, 3, 7], [{"a": "wry", "b": "ash"}]); r = cli()
assert r.returncode == 0 and "0 mismatches" in r.stdout, r
dash([0, 4, 7], [{"a": "wry", "b": "ash"}]); assert cli().returncode == 1   # fund mismatch, relationships MATCH
dash([0, 3, 7], []); r = cli(); assert r.returncode == 1 and "DIFF" in r.stdout, r  # DIFF only, no fund mismatch
print("all fundrel tests pass")
