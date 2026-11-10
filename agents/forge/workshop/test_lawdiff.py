import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lawdiff import compare, sections, ROOT

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
print("all lawdiff tests pass")
