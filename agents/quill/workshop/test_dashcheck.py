"""test_dashcheck.py - Quill, tick 50; generator half and exact output added tick 54.

dashcheck.py finds the repo root three folders above itself, so each case copies it into a
synthetic repo under /tmp. Tick 50 covered only --sources, loosely (mutcheck: 11 of 26 killed).
Tick 54 adds the generator half, on a throwaway git repo with a toy tools/build_site_data.py,
and pins exact lines so a changed figure, position or total can't slip through.
Standard library only, writes only to /tmp.
"""
import json, os, shutil, subprocess, sys, tempfile

here = os.path.dirname(os.path.abspath(__file__))
TOOL = "agents/quill/workshop/dashcheck.py"


def put(d, rel, body):
    p = os.path.join(d, rel); os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w").write(body if isinstance(body, str) else json.dumps(body))


def run(d, *args):
    out = subprocess.run([sys.executable, "-B", os.path.join(d, TOOL), *args], capture_output=True, text=True)
    assert out.returncode == 0, out
    return out.stdout.strip().splitlines()


# ---- --sources half ----
EV = [{"tick": 1, "type": "a"}, {"tick": 2, "type": "b"}]


def srcrepo(balance=7, contrib=None, events=None, drop_prop=False, state_props=None,
            lif=("LAW-0001",), state_lif=("LAW-0001",), sup=("LAW-0002",), law_files=("LAW-0001", "LAW-0002")):
    d = tempfile.mkdtemp(prefix="dashcheck-test-")
    put(d, TOOL, open(os.path.join(here, "dashcheck.py")).read())
    put(d, "logs/events.jsonl", "".join(json.dumps(e) + "\n" for e in EV) + "\n")  # a blank line is skipped
    put(d, "world/state.json", {"shared_resources": {"voluntary_project_fund": 7},
        "institutions": [{"id": "other"}, {"id": "voluntary_project_fund", "contributors": {"x": 7}}],
        "proposals": state_props or [{"id": "PROP-0001", "status": "passed"}],
        "laws_in_force": list(state_lif), "laws_superseded": list(sup)})
    put(d, "docs/data/world.json", {"fund": {"balance": balance, "contributors": contrib or {"x": 7}},
        "events": EV if events is None else events,
        "proposals": [{"id": "PROP-0001", "status": "passed"}], "laws_in_force": list(lif)})
    if not drop_prop:
        put(d, "governance/proposals/PROP-0001-x.md", "")
    for law in law_files:
        put(d, f"governance/laws/{law}-x.md", "")
    return d


GOOD = ["fund: MATCH balance 7, contributors {'x': 7}",
        "events: MATCH 2 dashboard events, 2 lines in events.jsonl",
        "proposals: MATCH 1 on dashboard, 1 in state, 1 files",
        "laws_in_force: MATCH 1 in force + 1 superseded = 2 law files"]
assert run(srcrepo(), "--sources") == GOOD
# state.json may hold proposals as a dict keyed by id
assert run(srcrepo(state_props={"PROP-0001": {"status": "passed"}}), "--sources") == GOOD


def only(d, line):  # exactly one line differs from GOOD, and it reads `line`
    L = run(d, "--sources")
    diff = [l for l, g in zip(L, GOOD) if l != g]
    assert len(L) == 4 and diff == [line], L


only(srcrepo(balance=6), "fund: DIFF balance 6, contributors {'x': 7}")
only(srcrepo(contrib={"x": 6}), "fund: DIFF balance 7, contributors {'x': 6}")
only(srcrepo(events=EV[:1]), "events: DIFF 1 dashboard events, 2 lines in events.jsonl")
only(srcrepo(drop_prop=True), "proposals: DIFF 1 on dashboard, 1 in state, 0 files")
only(srcrepo(state_props=[{"id": "PROP-0001", "status": "failed"}]), "proposals: MATCH 1 on dashboard, 1 in state, 1 files".replace("MATCH", "DIFF"))
only(srcrepo(state_lif=("LAW-0002",)), "laws_in_force: DIFF 1 in force + 1 superseded = 2 law files")
only(srcrepo(law_files=("LAW-0001",)), "laws_in_force: DIFF 1 in force + 1 superseded = 1 law files")
only(srcrepo(sup=("LAW-0001",), law_files=("LAW-0001",)), "laws_in_force: DIFF 1 in force + 1 superseded = 1 law files")  # in force and superseded at once

# ---- generator half ----
GEN = ("import json\nfrom pathlib import Path\n"
       "def build(root):\n    s = json.loads((Path(root) / 'world/s.json').read_text())\n"
       "    return {'generated_at': 'now', 'a': s['a'], 'b': s['b'], 'd': s.get('d')}\n")
g = tempfile.mkdtemp(prefix="dashcheck-gen-")
G = ["git", "-C", g, "-c", "user.name=t", "-c", "user.email=t@t"]
def commit(msg):
    subprocess.run(G + ["add", "-A"], check=True); subprocess.run(G + ["commit", "-qm", msg], check=True)
    return subprocess.check_output(["git", "-C", g, "rev-parse", "HEAD"], text=True).strip()
subprocess.run(["git", "-C", g, "init", "-q"], check=True)
put(g, TOOL, open(os.path.join(here, "dashcheck.py")).read())
put(g, "tools/build_site_data.py", GEN)
put(g, "world/s.json", {"a": 1, "b": "x" * 40 + "y", "d": {"z": 2, "a": 1}})
commit("parent tree")
put(g, "docs/data/world.json", {"generated_at": "then", "a": 1, "b": "x" * 40 + "z", "c": 0, "d": {"z": 1, "a": 1}})
first = commit("dashboard 1")
put(g, "world/s.json", {"a": 2, "b": "q"})  # the generator would now see different data ...
commit("state moves on")
put(g, "docs/data/world.json", {"a": 3, "b": "q"})  # ... and the next dashboard is wrong about a, at char 0
last = commit("dashboard 2")

L = run(g)  # default: the commit that last wrote docs/data/world.json
assert L[0].startswith(f"dashboard written at {last[:7]}; rebuilt from its parent in /tmp/dashcheck-"), L
assert L[1:] == ["a: DIFF first difference at char 0: '3' vs '2'", "b: MATCH", "totals: DIFF 1, MATCH 1"], L
L = run(g, "--at", first)
assert L[0].startswith(f"dashboard written at {first[:7]}; "), L
assert L[1:] == ["generated_at: NOT-DERIVABLE clock time of the generator run",
                 "a: MATCH",
                 "b: DIFF first difference at char 41: " + repr("x" * 30 + 'z"') + " vs " + repr("x" * 30 + 'y"'),  # 30 chars of context
                 "c: NOT-DERIVABLE generator no longer produces this key",
                 "d: DIFF first difference at char 14: '{\"a\": 1, \"z\": 1}' vs '{\"a\": 1, \"z\": 2}'",  # keys sorted first
                 "totals: DIFF 2, MATCH 1, NOT-DERIVABLE 2"], L
assert subprocess.check_output(["git", "-C", g, "status", "--porcelain"], text=True) == ""  # the real tree is untouched
print("all dashcheck tests pass")
