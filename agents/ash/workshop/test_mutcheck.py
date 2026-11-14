"""test_mutcheck.py (Ash, tick 53). Pins what mutcheck.py promises, in a throwaway git repo.

Builds a temp repo with one tiny tool (one mutable operator in code, one in a docstring,
one in a comment) and runs Ash's mutcheck.py, unchanged, from that repo. Checks:
  1. a test that pins the boundary KILLS the one mutant (1 of 1), so docstring and
     comment operators were not mutated;
  2. a test that only calls the tool lets it SURVIVE, and names the line and the swap;
  3. a test that already fails on HEAD is reported and skipped, not scored;
  4. a tool no test names says so;
  5. exit code is 0 in every case (a report, not a gate);
  6. the repo's working tree is untouched after the run.
Standard library; writes only under a temp folder."""
import os, pathlib, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent
MUT = HERE / "mutcheck.py"

TOOL = '''"""tiny tool: a == b is not code here"""
def ge(a, b):
    return a >= b  # a == b in a comment is not code either
'''
LOADER = '''import importlib.util, pathlib
p = pathlib.Path(__file__).resolve().parent / "tiny.py"
s = importlib.util.spec_from_file_location("tiny", p); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
'''

def repo(test_body, extra_tool=False):
    d = pathlib.Path(tempfile.mkdtemp())
    w = d / "agents" / "x" / "workshop"; w.mkdir(parents=True)
    (w / "tiny.py").write_text(TOOL)
    (w / "test_tiny.py").write_text(LOADER + test_body)
    if extra_tool:
        (w / "lonely.py").write_text("print(1 == 1)\n")
    g = ["git", "-c", "user.name=t", "-c", "user.email=t@t"]
    subprocess.run(["git", "init", "-q"], cwd=d, check=True)
    subprocess.run(g + ["add", "-A"], cwd=d, check=True)
    subprocess.run(g + ["commit", "-qm", "base"], cwd=d, check=True)
    return d

def run(d, *tools):
    r = subprocess.run([sys.executable, str(MUT), *tools], cwd=d, capture_output=True, text=True, timeout=120)
    status = subprocess.run(["git", "status", "--porcelain"], cwd=d, capture_output=True, text=True).stdout
    return r.returncode, r.stdout, status

T = "agents/x/workshop/tiny.py"

# 1. strong test kills the only code mutant (>= -> <); docstring/comment '==' untouched
code, out, st = run(repo("assert m.ge(2, 2) and not m.ge(1, 2)\n"), T)
assert code == 0, out
assert f"{T}: 1 of 1 mutants KILLED" in out, out
assert "SURVIVED" not in out, out
assert st == "", st

# 2. weak test lets it survive, with line and swap named
code, out, st = run(repo("m.ge(2, 2)\n"), T)
assert code == 0, out
assert f"{T}: 0 of 1 mutants KILLED" in out, out
assert "SURVIVED line 3: >= -> <" in out, out
assert st == "", st

# 3. a test failing on unmutated HEAD is skipped, not scored
code, out, st = run(repo("assert not m.ge(2, 2)\n"), T)
assert code == 0, out
assert "tests already fail on unmutated HEAD; skipping" in out, out
assert "KILLED" not in out, out

# 4. a tool no test names
code, out, st = run(repo("assert m.ge(2, 2)\n", extra_tool=True), "agents/x/workshop/lonely.py")
assert code == 0, out
assert "agents/x/workshop/lonely.py: no test names it" in out, out

print("test_mutcheck: 4 cases OK")
