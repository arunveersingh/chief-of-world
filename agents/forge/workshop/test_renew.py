import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from renew import proposal, text_block, LAW
from lawdiff import textblock
law = LAW.read_text()
p = proposal(99, "Test", 40, "seventh", "LAW-0008,LAW-0020", law)
assert text_block(p) == text_block(law), "Text block is not byte-identical"
assert "LAW-0008 and LAW-0020" in p and "last voting tick is tick 42" in p
# the tick-28 filing, made by hand-script, matches what renew.py would copy
prop = (LAW.parents[1] / "proposals/PROP-0034-renew-one-rulebook-sixth.md").read_text()
assert text_block(prop) == text_block(law)
assert textblock(p) == textblock(law), "lawdiff disagrees"
print("all renew tests pass")
