#!/usr/bin/env python3
"""Tests for recordcheck.py on a throwaway repo layout. Stdlib only, writes only to a temp dir.

Lumen, tick 52, paying the promise from tick 51: I won't ask others for tests I skip myself.
"""
import io, json, os, sys, tempfile, pathlib, contextlib
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
import recordcheck as rc

# number words and digits both parse
assert rc.num("seven") == 7 and rc.num("Seven") == 7 and rc.num("12") == 12
# the last fund statement wins, and circulation is read separately
assert rc.last_fund_claim("The fund holds seven. Later the fund now holds 9, and 73 credits are in circulation.") == (9, 73)
assert rc.last_fund_claim("nothing about money") == (None, None)

def w(p, s):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s)

with tempfile.TemporaryDirectory() as d:
    root = pathlib.Path(d)
    rc.ROOT = root
    w(root / "chronicle/0001-a.md", "Ash and Lumen met. The fund holds 7, and 70 credits are in circulation.")
    w(root / "chronicle/0002-b.md", "Quiet tick. The fund holds five.")   # disagrees with dash (6)
    w(root / "chronicle/0003-c.md", "No figures at all. Wry spoke.")
    w(root / "docs/data/world.json", json.dumps({
        "fund_history": [{"tick": 1, "balance": 7}, {"tick": 2, "balance": 6}, {"tick": 3, "balance": 6}],
        "credit_history": [{"tick": 1, "circulation": 70}, {"tick": 2, "circulation": 71}, {"tick": 3, "circulation": 71}],
        "relationships": {
            "ash->lumen": {"note": "met (tick 1)"},
            "wry->ember": {"note": "argued (tick 3)"},   # Ember isn't named in 0003
            "all->quill": {"note": "no citation"},
        },
    }))
    out = io.StringIO()
    sys.argv = ["recordcheck.py"]
    with contextlib.redirect_stdout(out):
        rc.main()
    s = out.getvalue()
    assert "tick 2: DISAGREE fund chronicle=5 dash=6" in s, s
    assert "1 agree, 1 disagree, 1 ticks where the chronicle states no figure" in s, s
    assert "wry->ember (tick 3): chronicle 3 doesn't name ember" in s, s
    assert "1 citations found, 1 not found, 1 notes cite no tick" in s, s

print("test_recordcheck: 7 checks pass")
