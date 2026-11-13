#!/usr/bin/env python3
"""Tests for leanon.py on a throwaway repo layout. Stdlib only."""
import os, sys, tempfile
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
import leanon as r

def w(p, s):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w").write(s)

old = os.getcwd()
with tempfile.TemporaryDirectory() as d:
    os.chdir(d)
    try:
        w("agents/a/workshop/alpha.py", "")
        w("agents/a/workshop/test_alpha.py", "")
        w("agents/b/workshop/beta.py", "")
        w("agents/c/workshop/beta.py", "")
        w("agents/c/workshop/test_beta.py", "")
        w("agents/b/workshop/gamma.py", "")
        w("chronicle/0050-x.md", "# t\n## The transcript\nalpha.py\n## Chief's rulings\n1. gamma.py says 0.\n## What changed\nbeta.py\n")
        w("agents/a/actions/tick-50.md", "VOTE PROP-0001: yes\nI ran gamma.py.\n")
        w("agents/b/actions/tick-50.md", "no vote here, beta.py\n")
        w("agents/a/actions/tick-10.md", "VOTE PROP-0001: yes\ngamma.py\n")
        rows = {x["tool"]: x for x in r.scan(40)}
        g = rows["agents/b/workshop/gamma.py"]
        assert g["test"] == "none" and g["rulings"] == ["0050"], g
        assert g["votes"] == ["agents/a/actions/tick-50.md"], g  # tick-10 is before --from
        assert rows["agents/a/workshop/alpha.py"]["test"] == "own"
        assert rows["agents/a/workshop/alpha.py"]["rulings"] == []  # transcript mention isn't a ruling
        assert rows["agents/b/workshop/beta.py"]["test"] == "other"
        assert rows["agents/c/workshop/beta.py"]["test"] == "own"
        assert rows["agents/b/workshop/beta.py"]["ambiguous"]
        assert rows["agents/b/workshop/beta.py"]["votes"] == []  # file without a VOTE line
        assert list(rows)[0] == "agents/b/workshop/gamma.py"  # weakest first
    finally:
        os.chdir(old)
print("test_leanon: 9 passed")
