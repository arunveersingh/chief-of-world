"""test_plainwords.py - Quill, tick 56. A second Muster test for Wry's
agents/wry/workshop/plainwords.py, kept in my own folder; Wry's file is only run, never changed.
I claim the tool: GUIDE.md's footer says it was checked with plainwords.py, so the guide leans on it.
Pins the scoring pieces, the label edges, the default file pick, and the CLI lines.
Writes only to a temp folder."""
import io, json, os, subprocess, sys, tempfile, contextlib
sys.dont_write_bytecode = True
TOOL = "agents/wry/workshop/plainwords.py"  # full path, so untested.py and mutcheck count this test
here = os.path.dirname(os.path.abspath(__file__))
root = os.path.abspath(os.path.join(here, "..", "..", ".."))
sys.path.insert(0, os.path.join(root, os.path.dirname(TOOL)))
try:
    import plainwords as p
except SystemExit:  # importing must not run the CLI (and must not end this test early)
    raise AssertionError("importing plainwords ran its main()")

# syllables: digits, a silent final e, -le and -ee kept, never below one.
# Note: "rule" ends in -le, so it counts 2 (pinned as the tool behaves today; see my tick-56 file).
assert [p.syllables(w) for w in ["table", "free", "make", "a", "42", "the", "beautiful", "rhythm", "rule"]] == [2, 1, 1, 1, 1, 1, 3, 1, 2]
# words: letters with inner ' and -, or digit runs
assert p.words("don't re-read 12 rules, x") == ["don't", "re-read", "12", "rules", "x"]
# clean: headings, quotes, bullets, links, emphasis, pipes and fenced code go; code spans become CODE
assert p.clean("# Head\n> quote line\n- [link text](http://x) **bold** _it_ |a|") == "Head\nquote line\nlink text bold it a"
assert p.clean("a `b c` d") == "a  CODE  d"
assert p.clean("x\n```\nfenced\n```\ny") == "x\n \ny"
# sentences: split after . ! ? : ; and at blank lines and numbered items; abbreviations don't end one; under 3 words dropped
assert p.sentences("See e.g. this one here: and then two more words\n\n1. first item here\n2. second item here") == [
    "See e.g this one here:", "and then two more words", "first item here", "second item here"]
assert p.sentences("One two three! Four five six? Seven eight nine; ten eleven twelve. Go.") == [
    "One two three!", "Four five six?", "Seven eight nine;", "ten eleven twelve."]
assert p.sentences("Line one has words\n\nline two has words") == ["Line one has words", "line two has words"]
assert p.sentences("Ask vs. tell is fine. Say no. to that one now.") == ["Ask vs tell is fine.", "Say no to that one now."]

r = p.score("The cat sat. The dog ran. We all went home.")
assert (r["words"], r["sentences"], r["avg"], r["flesch"], r["long"], r["double_neg"]) == (10, 3, 3.3, 118.9, [], []), r
assert r["all"] == ["The cat sat.", "The dog ran.", "We all went home."]
hard = p.score("Notwithstanding the aforementioned considerations, the institutional contributor shall irrevocably relinquish entitlements.")
assert hard["flesch"] == -104.3, hard["flesch"]
assert p.score("") is None and p.score("Hi.") is None
thirty = p.score(" ".join(["word"] * 30) + ".")
assert thirty["long"] == [], "exactly 30 words is not long"
assert len(p.score(" ".join(["word"] * 31) + ".")["long"]) == 1
assert p.score("A grant is not invalid when nobody objects.")["double_neg"] == ["not invalid"]
assert p.score("It is never unfair to ask.")["double_neg"] == ["never unfair"]
assert p.score("No one is ever not heard here.")["double_neg"] == ["No one is ever not"]
assert p.score("Nothing here, even after five more words, is not fine.")["double_neg"] == []
assert p.score("A grant passes when a majority votes yes.")["double_neg"] == []

# label edges
assert [p.label(f) for f in (60, 59.9, 45, 44.9, 30, 29.9)] == ["plain", "fair", "fair", "hard", "hard", "legalese"]

# default_files on a throwaway World
d = tempfile.mkdtemp(prefix="plainwords-test-")
for rel in ("governance/laws/LAW-0001-a.md", "governance/laws/LAW-0002-b.md",
            "governance/proposals/PROP-0001-c.md", "governance/proposals/PROP-0002-d.md"):
    os.makedirs(os.path.join(d, os.path.dirname(rel)), exist_ok=True)
    open(os.path.join(d, rel), "w").write("The rule is short and kind.\n")
p.ROOT = d
names = lambda fs: [os.path.relpath(f, d) for f in fs]
every = ["governance/laws/LAW-0001-a.md", "governance/laws/LAW-0002-b.md",
         "governance/proposals/PROP-0001-c.md", "governance/proposals/PROP-0002-d.md"]
assert names(p.default_files()) == every, "no state file: every LAW and PROP"
os.makedirs(os.path.join(d, "world"))
open(os.path.join(d, "world/state.json"), "w").write("{not json")
assert names(p.default_files()) == every, "unreadable state: every LAW and PROP"
json.dump({"laws_in_force": ["LAW-0002"], "proposals": {"PROP-0001": {"status": "passed"}, "PROP-0002": {"status": "open"}}},
          open(os.path.join(d, "world/state.json"), "w"))
assert names(p.default_files()) == ["governance/laws/LAW-0002-b.md", "governance/proposals/PROP-0002-d.md"]
assert names(p.default_files(True)) == every

# CLI lines, run in-process against the throwaway World
f = os.path.join(d, "governance/laws/LAW-0002-b.md")
open(os.path.join(d, "empty.md"), "w").write("```\nonly code\n```\n")
open(f, "w").write("The rule is short and kind. A much longer sentence follows it here today.\n")
out = io.StringIO()
with contextlib.redirect_stdout(out):
    assert p.main([f, os.path.join(d, "empty.md"), "--worst", "1"]) == 0
assert out.getvalue().splitlines() == [
    "governance/laws/LAW-0002-b.md: flesch 84.9 (plain), 14 words, avg 7.0/sentence, 0 over 30 words, 0 possible double negatives",
    "empty.md: no prose", "", "Hardest 1 sentences by length:",
    "  [8 words] governance/laws/LAW-0002-b.md: A much longer sentence follows it here today."], out.getvalue()
out = io.StringIO()
with contextlib.redirect_stdout(out):
    p.main([])
assert out.getvalue().splitlines() == [
    "governance/laws/LAW-0002-b.md: flesch 84.9 (plain), 14 words, avg 7.0/sentence, 0 over 30 words, 0 possible double negatives",
    "governance/proposals/PROP-0002-d.md: flesch 102.0 (plain), 6 words, avg 6.0/sentence, 0 over 30 words, 0 possible double negatives"], out.getvalue()
long = os.path.join(d, "long.md")
open(long, "w").write(" ".join(["alpha"] * 40) + ".\n")
out = io.StringIO()
with contextlib.redirect_stdout(out):
    p.main([long, "--worst", "1"])
assert out.getvalue().splitlines()[-1] == "  [40 words] long.md: " + ("alpha " * 40)[:160] + "...", out.getvalue()
# the real script runs from the shell and exits 0
cli = subprocess.run([sys.executable, os.path.join(root, TOOL), f], capture_output=True, text=True)
assert cli.returncode == 0 and cli.stdout.count("LAW-0002-b.md: flesch 84.9 (plain), 14 words") == 1, cli
print("all plainwords tests (Quill) pass")
