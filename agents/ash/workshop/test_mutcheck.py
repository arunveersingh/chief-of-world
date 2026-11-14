"""test_mutcheck.py (Ash, tick 53). Pins what mutcheck.py promises, in a throwaway git repo.

Builds a temp repo with one tiny tool (one mutable operator in code, one in a docstring,
one in a comment) and runs Ash's mutcheck.py, unchanged, from that repo. Checks:
  1. a test that pins the boundary KILLS the one mutant (1 of 1), so docstring and
     comment operators were not mutated;
  2. a test that only calls the tool lets it SURVIVE, and names the line and the swap;
  3. a test that already fails on HEAD is reported and skipped, not scored;
  4. a tool no test names says so;
  5. each of the 12 swaps in the table fires exactly once on a line made for it;
  6. --max caps the count;
and in every case the exit code is 0 (a report, not a gate) and the scratch work
leaves the repo's working tree clean.
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


# 5. every swap in the table fires once on its own line, and nothing else does
SWAPS = [("==", "!="), ("!=", "=="), ("<=", ">"), (">=", "<"), ("<", ">="), (">", "<="),
         ("and", "or"), ("or", "and"), ("True", "False"), ("False", "True"), ("0", "1"), ("1", "2")]
ALL = "a, b = 3, 4\n" + "".join(f"r = {o}\n" if o in ("True", "False", "0", "1") else f"r = a {o} b\n"
                                for o, _ in SWAPS)
d = repo("m.ge(2, 2)\n")
(d / "agents/x/workshop/all.py").write_text(ALL)
(d / "agents/x/workshop/test_all.py").write_text("import runpy, pathlib\nrunpy.run_path(str(pathlib.Path(__file__).parent / 'all.py'))\n")
subprocess.run(["git", "add", "-A"], cwd=d, check=True)
subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "all"], cwd=d, check=True)
code, out, st = run(d, "agents/x/workshop/all.py")
assert code == 0, out
assert f"agents/x/workshop/all.py: 0 of {len(SWAPS)} mutants KILLED" in out, out
for n, (o, rep) in enumerate(SWAPS, start=2):
    assert f"SURVIVED line {n}: {o} -> {rep}" in out, (o, out)

# 6. --max caps the mutants tried
code, out, st = run(d, "--max", "3", "agents/x/workshop/all.py")
assert code == 0 and "0 of 3 mutants KILLED" in out, out

print("test_mutcheck: 6 cases OK")
