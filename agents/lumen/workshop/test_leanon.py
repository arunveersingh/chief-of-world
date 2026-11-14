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

# tick 55: the printed report and the edges mutcheck found unasked (12 of 25 killed before this).
import contextlib, io
with tempfile.TemporaryDirectory() as d:
    os.chdir(d)
    try:
        w("agents/a/workshop/alpha.py", "")
        w("agents/a/workshop/test_alpha.py", "")
        w("agents/b/workshop/gamma.py", "")
        w("agents/b/workshop/delta.py", "")
        w("agents/b/workshop/notes.md", "")                 # not a tool
        w("chronicle/0030-old.md", "## Chief's rulings\ndelta.py\n")   # before --from
        w("chronicle/0041-a.md", "## Chief's rulings\nalpha.py and agents/b/workshop/gamma.py\n## What changed\ndelta.py\n")
        # a chronicle 0100 would be needed to kill the hundreds-digit glob mutant (see tick 55)
        w("chronicle/0050-b.md", "# t\ngamma.py in the preamble\n## Chief's rulings\ngamma.py\n")
        w("chronicle/0043-c.md", "delta.py before any heading is not a ruling\n")
        w("chronicle/notes.md", "## Chief's rulings\ndelta.py\n")      # not a numbered chronicle
        w("agents/a/actions/tick-41.md", "VOTE PROP-0002: no\nalpha.py\n")
        w("agents/a/actions/tick-39.md", "VOTE PROP-0001: yes\ndelta.py\n")   # before --from
        w("agents/a/actions/notes.md", "VOTE PROP-0003: yes\ndelta.py\n")     # not a tick file
        w("agents/b/actions/tick-42.md", "said VOTE PROP-0002: yes mid-line, delta.py\n")  # not a strict vote line
        rows = {x["tool"]: x for x in r.scan(41)}
        assert set(rows) == {"agents/a/workshop/alpha.py", "agents/b/workshop/gamma.py", "agents/b/workshop/delta.py"}, rows
        g, dl, al = rows["agents/b/workshop/gamma.py"], rows["agents/b/workshop/delta.py"], rows["agents/a/workshop/alpha.py"]
        assert g["owner"] == "b" and al["owner"] == "a"
        assert g["rulings"] == ["0041", "0050"], g      # full path counts; preamble doesn't
        assert dl["rulings"] == [] and dl["votes"] == [], dl
        assert al["votes"] == ["agents/a/actions/tick-41.md"] and al["test"] == "own"
        assert not g["ambiguous"]
        assert [x["tool"] for x in r.scan(41)] == ["agents/b/workshop/gamma.py", "agents/b/workshop/delta.py",
                                                  "agents/a/workshop/alpha.py"]
        sys.argv = ["leanon.py", "--from", "41"]
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            r.main()
        t = out.getvalue()
        assert t.startswith("reliance from chronicle 0041 on\n"), t
        assert "none   agents/b/workshop/gamma.py\n       rulings: 0041,0050\n       votes:   -\n" in t, t
        assert "own    agents/a/workshop/alpha.py\n       rulings: 0041\n       votes:   a/tick-41\n" in t, t
        assert "name shared" not in t, t
        assert "\n1 tool(s) without their own test are named in a ruling or a voting file:\n" in t, t
        assert "  agents/b/workshop/gamma.py  (2 ruling chronicles, 0 voting files)" in t, t
        assert "delta.py  (" not in t and "alpha.py  (" not in t, t
    finally:
        os.chdir(old)
print("test_leanon: report and edges passed")

# tick 56: a roll call is not reliance (Quill's LISTED rule), and a retired tool is not counted
old = os.getcwd()
with tempfile.TemporaryDirectory() as d:
    os.chdir(d)
    try:
        w("agents/a/workshop/kept.py", "")
        w("agents/a/workshop/rolled.py", "")
        w("agents/a/workshop/gone.py", "#!/usr/bin/env python3\n# RETIRED (a, tick 9): unused\n")
        w("agents/a/workshop/late.py", "x = 1\n\n# RETIRED on line three does not count\n")
        w("chronicle/0050-x.md", "## Chief's rulings\n"
          "1. **Count.** The untested tools are rolled.py and gone.py.\n"
          "2. **Reliance.** I checked the fund with kept.py and late.py.\n\n"
          "rolled.py retires in tick 51.\n\n"
          "kept.py again in a second paragraph mentioning nothing else.\n"
          "## What changed\ngone.py\n")
        w("chronicle/0051-y.md", "## Chief's rulings\n"
          "3. **Use.** gone.py checked the fund.\n"
          "4. **Notice.** kept.py is listed as untested.\n")
        rows = {x["tool"].split("/")[-1]: x for x in r.scan(50)}
        assert rows["kept.py"]["rulings"] == ["0050"] and rows["kept.py"]["listed"] == ["0051"], rows["kept.py"]
        assert rows["rolled.py"]["rulings"] == [] and rows["rolled.py"]["listed"] == ["0050"], rows["rolled.py"]
        assert rows["late.py"]["rulings"] == ["0050"] and not rows["late.py"]["retired"], rows["late.py"]
        assert rows["gone.py"]["retired"] and rows["gone.py"]["rulings"] == ["0051"] and rows["gone.py"]["listed"] == ["0050"], rows["gone.py"]
        assert not rows["kept.py"]["retired"] and not rows["rolled.py"]["retired"]
        assert [x["tool"].split("/")[-1] for x in r.scan(50)] == ["kept.py", "late.py", "rolled.py", "gone.py"]
        assert r.paragraphs("1. a\n2. b\n\nc\n  \nd") == ["1. a", "2. b", "c", "d"]
        sys.argv = ["leanon.py", "--from", "50"]
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            r.main()
        t = out.getvalue()
        assert "none   agents/a/workshop/kept.py\n       rulings: 0050\n       listed:  0051\n       votes:   -\n" in t, t
        assert "none   agents/a/workshop/rolled.py\n       rulings: -\n       listed:  0050\n       votes:   -\n" in t, t
        assert "none   agents/a/workshop/late.py\n       rulings: 0050\n       votes:   -\n" in t, t
        assert "retired  agents/a/workshop/gone.py\n       rulings: 0051\n       listed:  0050\n       votes:   -\n" in t, t
        assert "\n2 tool(s) without their own test are named in a ruling or a voting file:\n" in t, t
        assert t.endswith(":\n  agents/a/workshop/kept.py  (1 ruling chronicles, 0 voting files)\n  agents/a/workshop/late.py  (1 ruling chronicles, 0 voting files)\n"), t
        assert "rolled.py  (" not in t and "gone.py  (" not in t, t
    finally:
        os.chdir(old)
print("test_leanon: listed and retired passed")
