#!/usr/bin/env python3
"""Tests for capcount.py. Stdlib only. Uses a fake mutcheck so the counts are exact."""
import contextlib, io, os, sys, tempfile
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
import capcount as c

def w(p, s):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w").write(s)

FAKE = r'''import re
print("running mutcheck at import would be a bug in capcount")
raise SystemExit(3)
SWAPS = [(r"\x3d\x3d", "!" + "=")]  # no literal double-equals, so this fake has no mutants of its own
def code_lines(text):
    return [n for n, l in enumerate(text.splitlines()) if not l.startswith("#")]
def helper(text):
    return code_lines(text)
def mutants(text):
    lines = text.splitlines(keepends=True)
    for n in helper(text):          # a helper capcount was never told about (tick 58)
        for pat, rep in SWAPS:
            for m in re.finditer(pat, lines[n]):
                yield n + 1, rep, ""
'''
old = os.getcwd()
with tempfile.TemporaryDirectory() as d:
    os.chdir(d)
    try:
        w(c.MUTCHECK, FAKE)
        w("agents/a/workshop/big.py", "a == b\n# c == d\nx == y == z\np == q\n")   # 4 mutants, lines 1,3,3,4
        w("agents/a/workshop/small.py", "a == b\n")                             # 1 mutant
        w("agents/a/workshop/test_big.py", "big == 1\n")                       # tests are not tools
        w("agents/b/workshop/none.py", "pass\n")                               # 0 mutants
        m = c.load()
        assert c.count("agents/a/workshop/big.py", m, 2) == (4, 2, 3), c.count("agents/a/workshop/big.py", m, 2)
        assert c.count("agents/a/workshop/big.py", m, 4) == (4, 0, None)
        assert c.count("agents/a/workshop/big.py", m, 3) == (4, 1, 4)
        assert c.count("agents/a/workshop/small.py", m, 0) == (1, 1, 1)
        assert c.tools() == ["agents/a/workshop/big.py", "agents/a/workshop/small.py", "agents/ash/workshop/mutcheck.py",
                           "agents/b/workshop/none.py"]   # mutcheck is a tool too
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            assert c.main(["--max", "1"]) == 0
        assert out.getvalue() == ("agents/a/workshop/big.py: 4 mutants, 3 past cap 1 (line 3 on)\n"
                                  "1 tool(s) have mutants past cap 1: 3 of 5 mutants unscored\n"), out.getvalue()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            assert c.main([]) == 0                                              # default cap is 40
        assert out.getvalue() == "0 tool(s) have mutants past cap 40: 0 of 5 mutants unscored\n", out.getvalue()
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            assert c.main(["--max"]) == 64
            assert c.main(["--max", "x"]) == 64
            assert c.main(["--min", "3"]) == 64
            assert c.main(["--max", "3", "extra"]) == 64
        assert err.getvalue().count("usage: capcount.py") == 4
        w(c.MUTCHECK, "SWAPS = []\ndef code_lines(t):\n    return []\ndef mutantz(t):\n    return []\n")
        try:
            c.load()
            raise AssertionError("missing mutants() should stop capcount")
        except SystemExit as e:
            assert "no longer defines mutants" in str(e), e
    finally:
        os.chdir(old)
print("test_capcount: passed")
