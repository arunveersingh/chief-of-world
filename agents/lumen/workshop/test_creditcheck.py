#!/usr/bin/env python3
"""Tests for creditcheck.py on a temp layout, with git show replaced by a stub. Stdlib only.

Lumen, tick 53: the last of my tools without a test.
"""
import io, json, os, sys, tempfile, pathlib, contextlib
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
import creditcheck as cc

# both state.json shapes (list and dict of agents), and both fund shapes (number and dict)
s_list = {"agents": [{"id": "a", "credits": 3}, {"id": "b", "credits": 4}],
          "shared_resources": {"voluntary_project_fund": 2, "compute_credits_total_in_circulation": 9}}
s_dict = {"agents": {"a": {"credits": 3}, "b": {"credits": 4}},
          "shared_resources": {"voluntary_project_fund": {"balance": 2}, "compute_credits_total_in_circulation": 9}}
assert cc.figures(s_list) == ({"a": 3, "b": 4}, 2, 9)
assert cc.figures(s_dict) == ({"a": 3, "b": 4}, 2, 9)

STATES = {
    "c1": s_list,                                               # matches its frame
    "c2": s_dict,                                               # dashboard misreports the fund
    "c3": {"agents": {"a": {"credits": 3}, "b": {"credits": 4}},  # state's own total doesn't add up
           "shared_resources": {"voluntary_project_fund": 2, "compute_credits_total_in_circulation": 10}},
    "c4": {"agents": {"a": {"credits": 3}, "b": {"credits": 4}},  # no fund yet (early ticks): counts as 0
           "shared_resources": {"compute_credits_total_in_circulation": 7}},
}
cc.state_at = lambda commit: STATES[commit]

with tempfile.TemporaryDirectory() as d:
    root = pathlib.Path(d)
    cc.ROOT = root
    (root / "docs/data").mkdir(parents=True)
    (root / "docs/data/world.json").write_text(json.dumps({"credit_history": [
        {"tick": 1, "commit": "c1", "credits": {"a": 3, "b": 4}, "fund": 2, "circulation": 9},
        {"tick": 2, "commit": "c2", "credits": {"a": 3, "b": 4}, "fund": 1, "circulation": 9},
        {"tick": 3, "commit": "c3", "credits": {"a": 3, "b": 4}, "fund": 2, "circulation": 10},
        {"tick": 4, "commit": "c4", "credits": {"a": 3, "b": 4}, "fund": None, "circulation": 7},
    ]}))
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        cc.main()
    s = out.getvalue()
    assert "tick 1:" not in s and "tick 4:" not in s, s
    assert "tick 2: fund dash=1 state=2" in s, s
    assert "tick 3: sum+fund=9 != circulation 10" in s, s
    assert "4 frames (ticks 1..4), 2 mismatches" in s, s

print("test_creditcheck: 6 checks pass")
