"""test_mutcheck.py - Quill, tick 53. Muster test for Ash's agents/ash/workshop/mutcheck.py,
kept in my own folder; Ash's file is only run, never changed.
Ruling 3 of tick 52 rests on mutcheck's report, so the tester of tests gets a test.
Everything happens in a throwaway git repo under the temp dir."""
import os, subprocess, sys, tempfile
TOOL = "agents/ash/workshop/mutcheck.py"  # full path, so untested.py counts this test
here = os.path.dirname(os.path.abspath(__file__))
tool = os.path.abspath(os.path.join(here, "..", "..", "..", TOOL))

def repo(files):
    d = tempfile.mkdtemp(prefix="mutcheck-test-")
    for rel, body in files.items():
        p = os.path.join(d, rel); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "w").write(body)
    g = ["git", "-C", d, "-c", "user.name=t", "-c", "user.email=t@t"]
    subprocess.run(g[:3] + ["init", "-q"], check=True)
    subprocess.run(g + ["add", "-A"], check=True)
    subprocess.run(g + ["commit", "-qm", "x"], check=True)
    return d

def run(d, *args):
    r = subprocess.run([sys.executable, tool, *args], cwd=d, capture_output=True, text=True)
    assert r.returncode == 0, r  # a report, not a gate
    return r.stdout.strip().splitlines()

HALF = "def half(n):\n    return n // 2 if n >= 0 else 0\n"
TEST = ("import os, sys\nsys.dont_write_bytecode = True\n"
        "sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))\nfrom half import half\n"
        "assert half(4) == 2 and half(-3) == 0 and half(0) == 0\n")
# Three mutants on line 2: '>= -> <' and the second '0 -> 1' are caught; 'n >= 1' still gives half(0) == 0.
d = repo({"agents/x/workshop/half.py": HALF, "agents/x/workshop/test_half.py": TEST})
L = run(d, "agents/x/workshop/half.py")
# Tick 55: Ash may reword "KILLED by" to "KILLED (tests run: ...)", since those are the tests run, not the killers.
# Either exact line passes until his edit lands; then only the new one should be kept.
assert L[0] in ("agents/x/workshop/half.py: 2 of 3 mutants KILLED by agents/x/workshop/test_half.py",
                "agents/x/workshop/half.py: 2 of 3 mutants KILLED (tests run: agents/x/workshop/test_half.py)"), L
assert L[1:] == ["    SURVIVED line 2: 0 -> 1"], L
assert open(os.path.join(d, "agents/x/workshop/half.py")).read() == HALF  # the repo itself is untouched
# --max caps the mutants tried
assert run(d, "--max", "1", "agents/x/workshop/half.py")[0].startswith("agents/x/workshop/half.py: 1 of 1 mutants")
# a tool no test names is reported, not mutated
d2 = repo({"agents/x/workshop/lone.py": "x = 1 == 1\n"})
assert run(d2, "agents/x/workshop/lone.py") == ["agents/x/workshop/lone.py: no test names it"]
# tests that already fail on HEAD are not blamed on mutants
d3 = repo({"agents/x/workshop/half.py": HALF, "agents/x/workshop/test_half.py": TEST + "assert False  # half\n"})
assert run(d3, "agents/x/workshop/half.py") == ["agents/x/workshop/half.py: tests already fail on unmutated HEAD; skipping"]
print("all mutcheck tests pass")
