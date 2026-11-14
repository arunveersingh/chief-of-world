"""test_histcheck.py - Quill, tick 50. Muster test for histcheck.py on a synthetic repo.

Checks: a matching tick counts as MATCH, a wrong one prints a DIFF line, a tick whose
chronicle never names the fund counts as chronicle-silent, the last mention in a
chronicle wins, and relationships compare exactly. Standard library only, writes only to /tmp.
"""
import json, os, subprocess, sys, tempfile

here = os.path.dirname(os.path.abspath(__file__))
tool = os.path.join(here, "histcheck.py")


def repo(rel_same=True):
    d = tempfile.mkdtemp(prefix="histcheck-test-")
    for sub in ["docs/data", "world", "chronicle"]:
        os.makedirs(os.path.join(d, sub))
    rel = {"a|b": "ally"}
    dash = {"fund_history": [{"tick": 1, "balance": 5}, {"tick": 2, "balance": 7},
                             {"tick": 3, "balance": 9}, {"tick": 4, "balance": 3}, {"tick": 10, "balance": 2}],
            "relationships": rel}
    json.dump(dash, open(os.path.join(d, "docs/data/world.json"), "w"))
    json.dump({"relationships": rel if rel_same else {"a|b": "rival"}},
              open(os.path.join(d, "world/state.json"), "w"))
    open(os.path.join(d, "chronicle/0001-tick-1.md"), "w").write("The fund holds 5 now.\n")
    open(os.path.join(d, "chronicle/0002-tick-2.md"), "w").write("Fund holds 4 early.\nThe fund now holds 7.\n")
    open(os.path.join(d, "chronicle/0003-tick-3.md"), "w").write("The fund holds 8.\n")
    open(os.path.join(d, "chronicle/0004-tick-4.md"), "w").write("Nothing about money.\n")
    open(os.path.join(d, "chronicle/0010-tick-10.md"), "w").write("The fund holds 2.\n")  # tick 54: a tick ending in 0
    return d


out = subprocess.run([sys.executable, tool], cwd=repo(), capture_output=True, text=True)
assert out.returncode == 0, out
lines = out.stdout.strip().splitlines()
assert "tick 3: dashboard 9, chronicle says 8" in lines, lines
assert "fund_history: MATCH 3, DIFF 1, chronicle-silent 1, rows 5" in lines, lines  # tick 2: last mention wins
assert lines[-1] == "relationships: MATCH 1 pairs", lines

out = subprocess.run([sys.executable, tool], cwd=repo(rel_same=False), capture_output=True, text=True)
assert out.stdout.strip().splitlines()[-1] == "relationships: DIFF 1 pairs", out.stdout
print("all histcheck tests pass")
