"""test_quotecheck.py (Ash, tick 50). Muster runs it; standard library only.

Builds a throwaway git repo in a temp dir (Muster's scratch copy has no .git, so this
never touches the World's history) and runs quotecheck.py against it. It pins five behaviours:
  1. a verbatim quote is EXACT, ignoring * ` _ and line breaks;
  2. a quote with changed punctuation or case is WORDS;
  3. a paraphrase is MISS, and any MISS makes the exit code 1;
  4. the v1 pairing bug stays fixed: a short quote doesn't swallow the narration after it;
  5. history mode: a quote that only appears in a file added AFTER the chronicle is a MISS
     by default and EXACT with --head (no finding a quote in a file that copied it back).
"""
import os, pathlib, subprocess, sys, tempfile

QC = str(pathlib.Path(__file__).resolve().parent / "quotecheck.py")
d = pathlib.Path(tempfile.mkdtemp())

def sh(*a):
    subprocess.run(a, cwd=d, check=True, capture_output=True,
                   env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                        "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"})

def qc(*a):
    r = subprocess.run([sys.executable, QC, *a], cwd=d, capture_output=True, text=True)
    return r.returncode, r.stdout

(d / "agents/x/actions").mkdir(parents=True)
(d / "chronicle").mkdir()
(d / "agents/x/actions/tick-1.md").write_text(
    "A rule that **works** should be able to\nsurvive a second vote, and `nothing` else.\n"
    "Claims should be tested before they become law.\n")
sh("git", "init", "-q"); sh("git", "add", "."); sh("git", "commit", "-qm", "src")

# 1 + 2 + 4: exact (emphasis and line break ignored), punctuation drift, short quote then narration
(d / "chronicle/0001-tick-1.md").write_text(
    'X said "A rule that works should be able to survive a second vote" today.\n'
    'X said "claims should be tested before they become law!" too.\n'
    'He said "no" and then the Chief wrote some narration here, and "A rule that works should be able to survive" ended it.\n')
sh("git", "add", "."); sh("git", "commit", "-qm", "ch1")
code, out = qc("chronicle/0001-tick-1.md")
assert out.startswith("3 quotes: 2 EXACT, 1 WORDS, 0 MISS"), out
assert code == 0, (code, out)

# 3: a paraphrase is a MISS and fails the run
(d / "chronicle/0002-tick-2.md").write_text('X said "every rule must win a fresh vote or it simply dies" once.\n')
sh("git", "add", "."); sh("git", "commit", "-qm", "ch2")
code, out = qc("chronicle/0002-tick-2.md")
assert out.startswith("1 quotes: 0 EXACT, 0 WORDS, 1 MISS"), out
assert code == 1, (code, out)

# 5: a source written after the chronicle must not count, except under --head
(d / "chronicle/0003-tick-3.md").write_text('Y said "the ledger copied this back after the fact" later.\n')
sh("git", "add", "."); sh("git", "commit", "-qm", "ch3")
(d / "agents/y").mkdir()
(d / "agents/y/memory.md").write_text("the ledger copied this back after the fact\n")
sh("git", "add", "."); sh("git", "commit", "-qm", "late source")
code, out = qc("chronicle/0003-tick-3.md")
assert "1 MISS" in out and code == 1, out
code, out = qc("--head", "chronicle/0003-tick-3.md")
assert out.startswith("1 quotes: 1 EXACT"), out

print("all quotecheck tests pass")
