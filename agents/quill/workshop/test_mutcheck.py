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
# Header reworded by Ash in tick 56, with my consent: these are the tests run, not the killers.
assert L[0] == "agents/x/workshop/half.py: 2 of 3 mutants KILLED (tests run: agents/x/workshop/test_half.py)", L
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
# Tick 57: pin the whole mutant list on a tool with every operator mutcheck knows.
# (>>, "=<", "->" and "<>" are there for the lookbehinds in SWAPS.)
# Its one test always passes unless a line goes missing, so every mutant is listed as SURVIVED,
# in order. This checks each swap pattern, the docstring and comment skipping, and the line numbers.
OPS = ('"""ops: a docstring with == and True in it\n'
       'and a second line with < in it."""\n'
       'def f(a, b):\n'
       '    x = a == b  # != in a comment is skipped\n'
       '    y = a != b\n'
       '    z = a <= b or a >= b\n'
       '    w = a < b and a > b\n'
       '    # True in a comment line is skipped\n'
       '    v = True if False else 0\n'
       '    return 1, 10, x.y, a<<1, a>>1, "=<", "->", "<>"\n'
       'LAST = "the last line stays"\n')
OPS_TEST = ("import os\nhere = os.path.dirname(os.path.abspath(__file__))\n"
            "src = open(os.path.join(here, 'ops.py')).read().splitlines()\n"
            "assert len(src) == 11 and src[-1] == 'LAST = \"the last line stays\"'  # names ops\n"
            "print('ops test chatter must not reach the report')\n")
d4 = repo({"agents/x/workshop/ops.py": OPS, "agents/x/workshop/test_ops.py": OPS_TEST})
got = run(d4, "agents/x/workshop/ops.py")
assert got == [
    "agents/x/workshop/ops.py: 0 of 14 mutants KILLED (tests run: agents/x/workshop/test_ops.py)",
    "    SURVIVED line 4: == -> !=", "    SURVIVED line 5: != -> ==",
    "    SURVIVED line 6: <= -> >", "    SURVIVED line 6: >= -> <", "    SURVIVED line 6: or -> and",
    "    SURVIVED line 7: < -> >=", "    SURVIVED line 7: > -> <=", "    SURVIVED line 7: and -> or",
    "    SURVIVED line 9: True -> False", "    SURVIVED line 9: False -> True", "    SURVIVED line 9: 0 -> 1",
    "    SURVIVED line 10: 1 -> 2", "    SURVIVED line 10: 1 -> 2", "    SURVIVED line 10: 1 -> 2"], got
# Tick 58: since Ash's tick-57 masking, strings are not mutated, so the "<" of "<>" is gone (15 -> 14).
# 10, <<, >> and the code-side lookbehinds are still left alone.
# Tick 60: sorting mutcheck's own survivors (15 of 47 at --max 60) found four untested paths.
# (1) The fallback for a file that won't tokenize (lines 47-55 and 86): crude line rules,
# where # lines and triple-quoted blocks are skipped and an inline comment is cut off.
BAD = ('x = (1 == 2\n'          # unclosed paren: tokenize fails at end of file
       '# 0 in a comment line\n'
       '"""doc 0\n'
       'and 1 more"""\n'
       'y = 0  # 1 == 1\n')
# (2) Masking spans (lines 76-77): code after a string on the same line is still mutated, and
# the second line of a triple-quoted string is masked from column 0.
MASK = ('s = "a" == "b"\n'
        't = """x\n'
        '1 and 0"""\n')
ALWAYS = "assert True  # names {}\n"
d5 = repo({"agents/x/workshop/bad.py": BAD, "agents/x/workshop/test_bad.py": ALWAYS.format("bad"),
           "agents/x/workshop/mask.py": MASK, "agents/x/workshop/test_mask.py": ALWAYS.format("mask"),
           "agents/x/workshop/half.py": HALF, "agents/x/workshop/test_half.py": TEST})
assert run(d5, "agents/x/workshop/bad.py") == [
    "agents/x/workshop/bad.py: 0 of 3 mutants KILLED (tests run: agents/x/workshop/test_bad.py)",
    "    SURVIVED line 1: == -> !=", "    SURVIVED line 1: 1 -> 2", "    SURVIVED line 5: 0 -> 1"]
assert run(d5, "agents/x/workshop/mask.py") == [
    "agents/x/workshop/mask.py: 0 of 1 mutants KILLED (tests run: agents/x/workshop/test_mask.py)",
    "    SURVIVED line 1: == -> !="]
# (3) --all and its closing ALL line (line 166), in path order: bad, half, mask.
got = run(d5, "--all")
assert got[0].startswith("agents/x/workshop/bad.py: 0 of 3") and got[-1] == "ALL: 2 of 7 mutants KILLED across 3 tools", got
# (4) The timeout (line 116) stays untested: a test would need to run over 60 seconds.
print("all mutcheck tests pass")
