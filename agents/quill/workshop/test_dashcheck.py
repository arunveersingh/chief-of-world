"""test_dashcheck.py - Quill, tick 50. Muster test for dashcheck.py --sources on a synthetic repo.

dashcheck.py finds the repo root three folders above itself, so the test copies it into a
synthetic repo under /tmp. It checks that matching sources print four MATCH lines, and that
a wrong fund balance or a missing proposal file each turn exactly one line to DIFF.
The generator half (no --sources) needs the real repo and git history, so it isn't covered here.
Standard library only, writes only to /tmp.
"""
import json, os, shutil, subprocess, sys, tempfile

here = os.path.dirname(os.path.abspath(__file__))


def repo(balance=7, drop_prop=False):
    d = tempfile.mkdtemp(prefix="dashcheck-test-")
    for sub in ["agents/quill/workshop", "docs/data", "world", "logs", "governance/proposals", "governance/laws"]:
        os.makedirs(os.path.join(d, sub))
    shutil.copy(os.path.join(here, "dashcheck.py"), os.path.join(d, "agents/quill/workshop/dashcheck.py"))
    ev = [{"tick": 1, "type": "a"}, {"tick": 2, "type": "b"}]
    open(os.path.join(d, "logs/events.jsonl"), "w").write("".join(json.dumps(e) + "\n" for e in ev))
    state = {"shared_resources": {"voluntary_project_fund": 7},
             "institutions": [{"id": "voluntary_project_fund", "contributors": {"x": 7}}],
             "proposals": [{"id": "PROP-0001", "status": "passed"}],
             "laws_in_force": ["LAW-0001"], "laws_superseded": ["LAW-0002"]}
    json.dump(state, open(os.path.join(d, "world/state.json"), "w"))
    dash = {"fund": {"balance": balance, "contributors": {"x": 7}}, "events": ev,
            "proposals": [{"id": "PROP-0001", "status": "passed"}], "laws_in_force": ["LAW-0001"]}
    json.dump(dash, open(os.path.join(d, "docs/data/world.json"), "w"))
    if not drop_prop:
        open(os.path.join(d, "governance/proposals/PROP-0001-x.md"), "w").close()
    for law in ["LAW-0001-a.md", "LAW-0002-b.md"]:
        open(os.path.join(d, "governance/laws", law), "w").close()
    return os.path.join(d, "agents/quill/workshop/dashcheck.py")


def run(tool):
    out = subprocess.run([sys.executable, tool, "--sources"], capture_output=True, text=True)
    assert out.returncode == 0, out
    return {l.split(":")[0]: l.split()[1] for l in out.stdout.strip().splitlines()}


assert run(repo()) == {"fund": "MATCH", "events": "MATCH", "proposals": "MATCH", "laws_in_force": "MATCH"}
r = run(repo(balance=6))
assert r["fund"] == "DIFF" and list(r.values()).count("DIFF") == 1, r
r = run(repo(drop_prop=True))
assert r["proposals"] == "DIFF" and list(r.values()).count("DIFF") == 1, r
print("all dashcheck tests pass")
