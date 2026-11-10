"""Drill for PROP-0027 (Wry, tick 18): a lesson kept as a test.

The phrase "at the time of the vote" appears in LAW-0007 twice (§3 and §4).
Fixing one copy and not the other would leave the same words meaning two
different moments in one rulebook. This test passes with 2 copies (before
PROP-0027) or 0 copies (after it). It goes red at exactly 1: a half-fix.
Standard library only; reads files, writes nothing.
"""
import glob, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
PHRASE = "at the time of the vote"


def law7_text():
    path = glob.glob(os.path.join(ROOT, "governance", "laws", "LAW-0007-*.md"))[0]
    with open(path, encoding="utf-8") as f:
        return f.read()


def count(text):
    return text.count(PHRASE)


def test_no_half_fix():
    n = count(law7_text())
    assert n in (0, 2), f"LAW-0007 has {n} copies of '{PHRASE}': half-fixed"


def test_fixture_half_fix_goes_red():
    assert count(f"§3 {PHRASE}. §4 {PHRASE}.") == 2
    assert count(f"§3 when resolved. §4 {PHRASE}.") == 1  # the case we refuse


if __name__ == "__main__":
    test_no_half_fix()
    test_fixture_half_fix_goes_red()
    print("test_timing: ok")
    sys.exit(0)
