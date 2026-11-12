import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from renew import proposal, text_block, LAW
from lawdiff import textblock
law = LAW.read_text()
p = proposal(99, "Test", 40, "seventh", "LAW-0008,LAW-0020", law)
assert text_block(p) == text_block(law), "Text block is not byte-identical"
assert "LAW-0008 and LAW-0020" in p and "last voting tick is tick 42" in p
# tick 36: filed renewals are frozen, the law is not. Once an amendment (e.g. PROP-0036/0037)
# passes, LAW-0007 differs from PROP-0034 on purpose, so compare the two frozen copies with each
# other instead: the hand-scripted sixth (tick 28) and the renew.py-made seventh (tick 32).
props = LAW.parents[1] / "proposals"
six = (props / "PROP-0034-renew-one-rulebook-sixth.md").read_text()
seven = (props / "PROP-0035-renew-one-rulebook-seventh.md").read_text()
assert text_block(six) == text_block(seven), "sixth and seventh renewals differ"
assert textblock(p) == textblock(law), "lawdiff disagrees"
print("all renew tests pass")
