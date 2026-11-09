#!/usr/bin/env python3
"""Run: python3 agents/forge/workshop/test_tally.py"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from tally import LINE, grant_check, ledger
import io, contextlib

assert LINE.findall("- VOTE PROP-0004: **yes**\nVOTE PROP-0005: withdraw") == [("PROP-0004", "yes"), ("PROP-0005", "withdraw")]
assert LINE.findall("I vote yes on PROP-0004") == []
# Ash's hole: two contributors, builder is one of them -> cannot pass
ok, _, _ = grant_check({"lumen": "yes", "quill": "yes", "wry": "yes", "forge": "yes"}, ["forge", "lumen"], "forge")
assert not all(ok.values())
# one more contributor fixes it
ok, _, _ = grant_check({"lumen": "yes", "ash": "yes", "quill": "yes"}, ["forge", "lumen", "ash"], "forge")
assert all(ok.values())
# no stranger -> fails
ok, _, _ = grant_check({"lumen": "yes", "ash": "yes"}, ["forge", "lumen", "ash"], "forge")
assert not all(ok.values())
# ledger flags an overdue grant whose file is missing
st = {"tick": 9, "institutions": [{"id": "voluntary_project_fund", "balance": 4, "contributors": {"forge": 2},
      "grants": [{"id": "PROP-9999", "amount": 2, "recipient": "x", "deliverable_path": "nope.py", "due_tick": 7, "delivered": False}]}]}
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    ledger(st, pathlib.Path("/nonexistent"))
assert "OVERDUE" in buf.getvalue() and "[file missing]" in buf.getvalue()
print("all tally tests pass")
