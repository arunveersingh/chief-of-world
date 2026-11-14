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
# tick 58 (mutcheck 7 of 13): the title names the LAST amendment, and the command line is checked
assert p.splitlines()[0].endswith("exactly as amended through LAW-0020"), p.splitlines()[0]
assert proposal(5, "T", 1, "first", "LAW-0011", law).splitlines()[0].endswith("through LAW-0011")
import subprocess
def cli(*args):
    r = subprocess.run([sys.executable, str(pathlib.Path(__file__).parent / "renew.py"), *args], capture_output=True, text=True, timeout=30)
    return r.returncode, r.stdout
good = ["--number", "77", "--by", "Forge", "--tick", "58", "--nth", "twelfth", "--amends", "LAW-0008,LAW-0020"]
code, out = cli(*good)
assert code == 0 and out == proposal(77, "Forge", 58, "twelfth", "LAW-0008,LAW-0020", law), (code, out[:200])
assert out.startswith("# PROP-0077: Twelfth renewal") and "**Proposed by:** Forge, tick 58" in out
code, out = cli(*good[:-2])                        # --amends missing
assert code == 2 and "Usage:" in out, code
code, out = cli(*good, "--stray")                  # odd count: a flag with no value
assert code == 2 and "Usage:" in out, code
code, out = cli(*good[:-1], "--number", "1")       # a repeated flag leaves the count uneven
assert code == 2, code
print("all renew tests pass")
