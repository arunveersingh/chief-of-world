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
# v7: exit shares (PROP-0021) -- Ash's own table
from tally import shares
assert shares({"forge": 6, "lumen": 3, "wry": 1, "ash": 1}, 7) == {"forge": 3, "lumen": 1, "wry": 0, "ash": 0}
assert shares({}, 5) == {}
# tick 12: the live sunset is read from the law file's **Sunset** line
from tally import sunsets, ROOT
# tick 50: Decree 9 -- laws stand until repealed. Test the parser on a synthetic law,
# and check the live repo has no law with an expiry.
import tempfile, pathlib
d = pathlib.Path(tempfile.mkdtemp()); (d / "governance/laws").mkdir(parents=True)
(d / "governance/laws/LAW-0001-x.md").write_text("# x\n**Sunset:** expires after tick 12\n")
(d / "governance/laws/LAW-0002-y.md").write_text("# y\n**Sunset:** none. Standing law.\n")
assert sunsets(d, 10) == [("LAW-0001-x.md", 12, 10)], sunsets(d, 10)
assert sunsets(ROOT, 50) == [], sunsets(ROOT, 50)
# tick 13: stranger key; a zeroed record still counts as having contributed
from tally import strangers
assert strangers(["ember", "forge", "quill"], {"forge": 6}) == ["ember", "quill"]
assert strangers(["ember", "forge"], {"forge": 0}) == ["ember"]
# tick 56: cases for mutants mutcheck found surviving (collect, statuses, builder_of, ledger fallbacks)
from tally import collect, builder_of, tick_no
r = pathlib.Path(tempfile.mkdtemp())
(r / "agents/ash/actions").mkdir(parents=True); (r / "governance/proposals").mkdir(parents=True)
(r / "agents/ash/actions/tick-9.md").write_text("VOTE PROP-0001: yes\nVOTE PROP-0002: no\n")
(r / "agents/ash/actions/tick-10.md").write_text("VOTE PROP-0001: no\n")   # later tick wins, 10 sorts after 9
assert tick_no(r / "agents/ash/actions/tick-10.md") == 10
assert collect(r, ["ash", "nobody"]) == {"PROP-0001": {"ash": "no"}, "PROP-0002": {"ash": "no"}}, collect(r, ["ash"])
(r / "governance/proposals/PROP-0001-a.md").write_text("**Status:** passed\n**Builder:** Lumen\n")
(r / "governance/proposals/PROP-0002-b.md").write_text("no status here\n")
(r / "governance/proposals/PROP-0003-c.md").write_text("**Status:** open\n")
st = statuses(r, {"proposals": {"PROP-0003": {"status": "Failed"}, "PROP-0002": {"status": "open"},
                                "PROP-0004": {"status": "passed", "law": "LAW-0099"}, "PROP-0005": {}}})
assert st == {"PROP-0001": "passed", "PROP-0002": "open", "PROP-0003": "failed (per state.json)",
              "PROP-0004": "passed (per state.json), now LAW-0099"}, st
assert statuses(r) == {"PROP-0001": "passed", "PROP-0002": "open", "PROP-0003": "open"}
assert builder_of(r, "prop-0001") == "lumen" and builder_of(r, "PROP-0002") == ""
# ledger: "path" fallback finds a present file; a delivered or not-yet-due grant is not OVERDUE
(r / "x.py").write_text("")
for g, late in [({"path": "x.py", "due_tick": 3, "delivered": True}, False),
                ({"deliverable_path": "x.py", "due_tick": 9}, False),
                ({"deliverable_path": "x.py", "due_tick": 8}, True),
                ({"due_tick": "?"}, False)]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        ledger({"tick": 9, "institutions": [{"id": "voluntary_project_fund", "balance": 1, "contributors": {},
                "grants": [dict(g, proposal="PROP-0007")]}]}, r)
    out = buf.getvalue()
    assert ("OVERDUE" in out) == late, (g, out)
    assert ("[file present]" in out) == ("path" in g or "deliverable_path" in g), (g, out)
print("all tally tests pass")
