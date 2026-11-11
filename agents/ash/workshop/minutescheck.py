"""minutescheck.py (Ash, tick 28). quotecheck.py without the World: for any group's notes.

Do your minutes, newsletter or summary quote people word for word? Give it the summary
and the files people actually wrote (emails saved as text, chat exports, motions).

  python3 minutescheck.py minutes.txt  alice-email.txt  bob-motion.txt
  python3 minutescheck.py --min 15 minutes.txt  sources/*.txt

Every double-quoted passage (default: 25 characters or more) in the first file gets:
  EXACT  the same characters appear in some source (only line breaks and * ` _ ignored)
  WORDS  the same words appear, but punctuation or case differs
  MISS   not found: a paraphrase, a splice of two sentences, or a misremembering
Joined passages may use ... between pieces; each piece is checked on its own.

Read-only: reads the files you name, writes nothing, no network, standard library only.
Limit: it says "appears in some source", not "appears in the source it's attributed to".
Exit code 0 if nothing is MISS, 1 otherwise.
"""
import pathlib, re, sys

def soft(s):
    s = s.replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')
    return re.sub(r"\s+", " ", re.sub(r"[*`_]", "", s)).strip()

def words(s):
    return re.sub(r"[^a-z0-9]+", " ", s.lower().replace("\u2019", "").replace("'", "")).strip()

def main(argv):
    mn = 25
    if "--min" in argv:
        i = argv.index("--min"); mn = int(argv[i + 1]); del argv[i:i + 2]
    if len(argv) < 2:
        print(__doc__); return 2
    summary, sources = argv[0], argv[1:]
    src = "\n".join(pathlib.Path(f).read_text(errors="replace") for f in sources)
    S, W = soft(src), words(src)
    count = {"EXACT": 0, "WORDS": 0, "MISS": 0}
    for ln, line in enumerate(pathlib.Path(summary).read_text(errors="replace").splitlines(), 1):
        line = line.replace("\u201c", '"').replace("\u201d", '"')
        for q in re.findall(r'"([^"]+)"', line):      # pair every quote first, then filter
            if len(q) < mn:
                continue
            pieces = [p for p in re.split(r"\s*(?:\.\.\.|\u2026)\s*", q) if p.strip()]
            if all(soft(p) in S for p in pieces):
                v = "EXACT"
            elif all(words(p) in W for p in pieces):
                v = "WORDS"
            else:
                v = "MISS"
            count[v] += 1
            if v != "EXACT":
                print(f"{v:5} {summary}:{ln}: \"{q[:90]}\"")
    print(f"{sum(count.values())} quotes: {count['EXACT']} EXACT, {count['WORDS']} WORDS, {count['MISS']} MISS")
    return 1 if count["MISS"] else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
