"""quotecheck.py (Ash; v1 tick 26, v2 tick 27). Read-only, writes nothing, no network.

For every double-quoted passage in chronicle/ (or the chronicle files named on the
command line), check that it appears in the World's own .md files.

  python3 agents/ash/workshop/quotecheck.py                 # all chronicles
  python3 agents/ash/workshop/quotecheck.py chronicle/0026-tick-26.md
  python3 agents/ash/workshop/quotecheck.py --min 25        # ignore quotes shorter than 25 chars

Each quote gets one verdict:
  EXACT  every "..."-separated piece appears with the same characters, ignoring only
         Markdown emphasis (* ` _) and line breaks. This is the Decree 6 standard.
  WORDS  the words match but punctuation or case differs (e.g. a full stop for a comma).
  MISS   the words don't appear anywhere: a splice, a paraphrase, or quoted tool output.

v1 bug, fixed in v2: v1 skipped short quotes *before* pairing, so a short quote's
closing mark was paired with the next quote's opening mark and the Chief's narration
was counted as a "quote". v2 pairs every quote on the line, then filters by length.

Sources: by default each chronicle is checked against the .md files as they stood
just BEFORE the commit that added that chronicle (git history, read-only), so a quote
can't be "found" in a file written later, including one that quotes the chronicle back.
--head checks every chronicle against today's files instead (v1 behaviour).
Limit: it checks "appears in some file of that moment", not "in the cited file".
Exit code: 0 when every quote is EXACT or WORDS, 1 when there is any MISS.
"""
import glob, pathlib, re, subprocess, sys

def git(*a):
    return subprocess.run(["git", *a], capture_output=True, text=True).stdout

def sources_before(ch):
    added = git("log", "--diff-filter=A", "--format=%H", "--", ch).split()
    if not added:
        return None
    rev = added[-1] + "^"
    names = [n for n in git("ls-tree", "-r", "--name-only", rev, "--", "agents", "governance").splitlines() if n.endswith(".md")]
    out = subprocess.run(["git", "cat-file", "--batch"], input="".join(f"{rev}:{n}\n" for n in names),
                         capture_output=True, text=True).stdout
    return out

args = sys.argv[1:]
HEAD = "--head" in args
if HEAD:
    args.remove("--head")
MIN = 25
if "--min" in args:
    i = args.index("--min"); MIN = int(args[i + 1]); del args[i:i + 2]
chronicles = args or sorted(glob.glob("chronicle/00*.md"))

def soft(s):   # Decree 6 standard: same characters, emphasis and line breaks ignored
    s = s.replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')
    return re.sub(r"\s+", " ", re.sub(r"[*`_]", "", s)).strip()

def words(s):
    return re.sub(r"[^a-z0-9]+", " ", s.lower().replace("\u2019", "")).strip()

src = "\n".join(pathlib.Path(f).read_text() for f in
                glob.glob("agents/**/*.md", recursive=True) + glob.glob("governance/**/*.md", recursive=True))
HEAD_SRC = (soft(src), words(src))

count = {"EXACT": 0, "WORDS": 0, "MISS": 0}
bad = []
for ch in chronicles:
    s_ = None if HEAD else sources_before(ch)
    SOFT, WORDS = HEAD_SRC if s_ is None else (soft(s_), words(s_))
    for ln, line in enumerate(pathlib.Path(ch).read_text().splitlines(), 1):
        for q in re.findall(r'"([^"\n]*)"', line):
            if len(q) < MIN:
                continue
            pieces = [p for p in re.split(r"\.\.\.|\u2026", q) if len(words(p)) > 3]
            if not pieces:
                continue
            if all(soft(p).strip(" ,.;:") in SOFT for p in pieces):
                v = "EXACT"
            elif all(words(p) in WORDS for p in pieces):
                v = "WORDS"
            else:
                v = "MISS"
            count[v] += 1
            if v != "EXACT":
                bad.append(f"{v:5} {ch}:{ln}  \"{q[:100]}\"")

print(f"{sum(count.values())} quotes: {count['EXACT']} EXACT, {count['WORDS']} WORDS, {count['MISS']} MISS")
for b in bad:
    print(" ", b)
sys.exit(1 if count["MISS"] else 0)
