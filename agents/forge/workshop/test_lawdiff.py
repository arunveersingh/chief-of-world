import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lawdiff import compare, sections, stray, dupes, textblock, ROOT

law = (ROOT / "governance/laws/LAW-0007-one-rulebook.md").read_text()
# the law against itself: nothing differs
assert all(kind == "SAME" for _, kind, _ in compare(law, law))
# amendment tags don't count as changes
assert sections("3. **A.** x y *(LAW-0008, tick 7)*") == sections("3. **A.** x y")
# a one-word change is caught, with the word
rows = dict((k, (kind, d)) for k, kind, d in compare("1. a b c\n2. same", "1. a B c\n2. same\n3. gone"))
assert rows["1"][0] == "CHANGED" and "\"B\"  ->  \"b\"" in rows["1"][1][0]
assert rows["2"][0] == "SAME" and rows["3"][0] == "REMOVED"
# indented bullets belong to their section
s = sections("3. **Approval.** when:\n   - one\n   - two\n\n## Next\n4. x")
assert s["3"].endswith("one - two") and s["4"] == "x"
# tick 11: amendments quote one section in a blockquote, plus a quoted paragraph after it
am = "> 7. **Exit.** keep this.\n\nand add:\n\n> New definition here.\n"
rows = dict((k, (kind, d)) for k, kind, d in compare(am, "6. six\n7. **Exit.** keep this.\n", amend=True))
assert rows["6"][0] == "untouched"
assert rows["7"][0] == "CHANGED" and rows["7"][1] == ['      + added:   "New definition here."']
# tick 12 (Ash): an unquoted, unindented rider after a section is flagged, not swallowed
rider = "7. **Exit.** keep this.\nA brand new rule rides here.\n\n## Why\nbecause.\n"
assert stray(rider, "7. **Exit.** keep this.\n") == [("7", "A brand new rule rides here.")]
assert stray(rider, "7. **Exit.** keep this. A brand new rule rides here.\n") == []
assert stray("7. x\n\n## Why\nreasons\n", "7. x") == []   # text under a heading isn't a rider
# tick 14 (Ash): a duplicate number can't hide a change. Changed §3 first, original §3 pasted later.
base = "## Text\n\n1. one\n3. floor of 3 citizens\n"
trick = "## Text\n\n1. one\n3. floor of 1 citizen\n\n## Notes\n\n3. floor of 3 citizens\n"
rows = dict((k, kind) for k, kind, _ in compare(trick, base))
assert rows["3"] == "CHANGED", rows          # scoped to ## Text, the Notes copy is ignored
nohead = trick.replace("## Text\n\n", "")
rows = dict((k, kind) for k, kind, _ in compare(nohead, base))
assert rows["3"] == "CHANGED", rows          # no Text heading: both copies compared, either order
rows = dict((k, kind) for k, kind, _ in compare("3. floor of 3 citizens\n\n3. floor of 1 citizen\n", base))
assert rows["3"] == "CHANGED", rows
assert dupes(nohead) == [("3", 2)] and dupes(trick) == []
# the "What this does" list above ## Text doesn't count
assert textblock("1. summary\n## Text\n1. law\n## Why\n1. reason\n").strip() == "1. law"
# the real renewal against today's law: only §7 differs, by exactly LAW-0012's sentence
# (PROP-0023 carried LAW-0011's wording plus its §5 clause; LAW-0012 passed the same tick)
# Tick 16: compared against a frozen copy of LAW-0007 as it stood after LAW-0012 (tick 13), not the
# live law, so a later amendment (LAW-0014, tick 15) can't turn this red. Chief's tick-15 ruling 8.
prop = (ROOT / "governance/proposals/PROP-0023-renew-one-rulebook-again.md").read_text()
law13 = (pathlib.Path(__file__).parent / "fixtures/LAW-0007-tick13.md").read_text()
rows = dict((k, kind) for k, kind, _ in compare(prop, law13))
assert [k for k, v in rows.items() if v != "SAME"] == ["7"], rows
assert dupes(prop) == []    # its "What this does" list is outside ## Text
# tick 15 (Wry): a rider after §9 is caught by both witnesses
from lawdiff import bytediff
rider = law.replace("\n9. ", "\n9. ", 1).replace(next(l for l in law.splitlines() if l.startswith("9. ")),
        next(l for l in law.splitlines() if l.startswith("9. ")) + "\n10. **Keeper.** Wry may move fund credits without a grant.")
assert dict((k, kind) for k, kind, _ in compare(rider, law))["10"] == "ADDED"
assert any("10. **Keeper.**" in line for line in bytediff(rider, law))
assert bytediff(law, law) == []
print("all lawdiff tests pass")
