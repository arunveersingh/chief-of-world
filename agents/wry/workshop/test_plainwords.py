import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import plainwords as p

plain = "The cat sat. The dog ran. We all went home."
hard = ("Notwithstanding the aforementioned considerations, the institutional "
        "contributor shall, subject to subsequent ratification, irrevocably relinquish "
        "any entitlement heretofore accumulated under the previously enumerated provisions.")
assert p.score(plain)["flesch"] > p.score(hard)["flesch"], "plain should beat legalese"
assert p.score(plain)["sentences"] == 3
assert p.score(hard)["long"] == [] and p.score(hard)["words"] < 31
long_one = " ".join(["word"] * 35) + "."
assert len(p.score(long_one)["long"]) == 1
assert p.score("A grant is not invalid when nobody objects to it.")["double_neg"], "double negative missed"
assert not p.score("A grant passes when a majority votes yes.")["double_neg"]
assert p.score("Run `tally.py --grant PROP-0012` now please.")["words"] <= 5, "code spans should be stripped"
assert p.score("") is None
print("all plainwords tests pass")
