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
cur = [os.path.basename(f) for f in p.default_files()]
assert not any(f.startswith(("LAW-0002", "LAW-0003", "LAW-0004")) for f in cur), "superseded laws should be skipped by default"
assert any(f.startswith("LAW-0007") for f in cur)
assert any(f.startswith("PROP-0017") for f in cur) or "PROP-0017" not in p.json.load(open(os.path.join(p.ROOT, "world/state.json")))["proposals"] or p.json.load(open(os.path.join(p.ROOT, "world/state.json")))["proposals"]["PROP-0017"]["status"] != "open"
assert len(p.default_files(True)) >= len(cur)
print("all plainwords tests pass")
