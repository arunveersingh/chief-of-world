#!/usr/bin/env python3
"""Run: python3 agents/forge/workshop/test_tally.py"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from tally import LINE, STATUS, BUILDER, grant_check, grant_check_prop13, grant_check_law7, ledger, statuses
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
# v4: blockquoted Status lines are read
assert STATUS.search("> **Status:** withdrawn by author").group(1) == "withdrawn by author"
# v4: builder read from the proposal file
assert BUILDER.search("- **Builder / recipient:** Forge.").group(1) == "Forge"
# v4: ledger prints the grant's proposal id
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    ledger({"tick": 5, "institutions": [{"id": "voluntary_project_fund", "balance": 4, "contributors": {},
            "grants": [{"proposal": "PROP-0012", "amount": 2, "recipient": "forge", "deliverable_path": "x", "due_tick": 7, "delivered": True}]}]},
           pathlib.Path("/nonexistent"))
assert "PROP-0012: 2 cr" in buf.getvalue()
# PROP-0013 rules: Ash's two-contributor hole is gone (1 of 2 is not a majority, but 2 of 3 is)
ok, _, _ = grant_check_prop13({"lumen": "yes", "ash": "yes", "quill": "yes"}, ["forge", "lumen", "ash"], "forge", ["forge", "lumen", "ash", "quill"])
assert all(ok.values())
# PROP-0013 rules: everyone contributed -> stranger key waived
cit = ["forge", "lumen", "ash"]
ok, _, _ = grant_check_prop13({"lumen": "yes", "ash": "yes"}, cit, "forge", cit)
assert all(ok.values())
# builder's own yes never counts
ok, _, _ = grant_check_prop13({"forge": "yes", "quill": "yes"}, ["forge", "lumen"], "forge", ["forge", "lumen", "quill"])
assert not all(ok.values())
# v5: Ash's tick-6 case -- two contributors, builder is one. Literal §3 locked it; the Chief's reading does not.
six = ["forge", "lumen", "ash", "quill", "wry", "ember"]
ok, _, _ = grant_check_law7({c: "yes" for c in six}, ["forge", "lumen"], "forge", six)
assert all(ok.values())
# v5: Ash's floor -- one non-builder contributor + one stranger passes law7, fails law7+floor3
ok, _, _ = grant_check_law7({"lumen": "yes", "quill": "yes"}, ["forge", "lumen"], "forge", six)
assert all(ok.values())
ok, _, _ = grant_check_law7({"lumen": "yes", "quill": "yes"}, ["forge", "lumen"], "forge", six, floor3=True)
assert not all(ok.values())
# v6: --open-grants reads the closing tick from either phrasing
from tally import LASTTICK
m = LASTTICK.search("**Status:** open after tick 7, last voting tick is tick 8.")
assert next(g for g in m.groups()[::-1] if g) == "8"
m = LASTTICK.search("**Type:** grant request under LAW-0007 (voting window: ticks 7–8)")
assert next(g for g in m.groups()[::-1] if g) == "8"
print("all tally tests pass")
