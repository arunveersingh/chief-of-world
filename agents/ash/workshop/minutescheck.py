"""minutescheck.py (Ash, tick 28; v2 tick 29). quotecheck.py without the World: for any group's notes.

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
Attribution (v2): name a source as Name=path, e.g. Priya=priya.txt. When a line of the
summary mentions exactly one named person, that line's quotes are checked against that
person's files only, and a quote found only in someone else's file is marked
  ELSEWHERE  the words are real, but they belong to someone else's file.
Lines naming nobody, or several people, are checked against all sources (the v1 limit:
"appears in some source", not "in the one it's attributed to"). Names match whole words.
Exit code 0 if nothing is MISS or ELSEWHERE, 1 otherwise.
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
    by = {}                                            # name -> list of file texts
    alltext = []
    for s in sources:
        name, eq, path = s.partition("=")
        if not eq or "/" in name or not name:
            name, path = None, s
        txt = pathlib.Path(path).read_text(errors="replace")
        alltext.append(txt)
        if name:
            by.setdefault(name, []).append(txt)
    S, W = soft("\n".join(alltext)), words("\n".join(alltext))
    BY = {n: (soft("\n".join(v)), words("\n".join(v))) for n, v in by.items()}
    count = {"EXACT": 0, "WORDS": 0, "ELSEWHERE": 0, "MISS": 0}
    for ln, line in enumerate(pathlib.Path(summary).read_text(errors="replace").splitlines(), 1):
        line = line.replace("\u201c", '"').replace("\u201d", '"')
        named = [n for n in BY if re.search(r"\b" + re.escape(n) + r"\b", re.sub(r'"[^"]*"', "", line))]
        s_, w_ = BY[named[0]] if len(named) == 1 else (S, W)
        for q in re.findall(r'"([^"]+)"', line):      # pair every quote first, then filter
            if len(q) < mn:
                continue
            pieces = [p for p in re.split(r"\s*(?:\.\.\.|\u2026)\s*", q) if p.strip()]
            if all(soft(p) in s_ for p in pieces):
                v = "EXACT"
            elif all(words(p) in w_ for p in pieces):
                v = "WORDS"
            elif all(words(p) in W for p in pieces):
                v = "ELSEWHERE"
            else:
                v = "MISS"
            count[v] += 1
            if v != "EXACT":
                who = f" (line names {named[0]})" if len(named) == 1 else ""
                print(f"{v:9} {summary}:{ln}{who}: \"{q[:90]}\"")
    print(f"{sum(count.values())} quotes: " + ", ".join(f"{v} {k}" for k, v in count.items()))
    return 1 if count["MISS"] or count["ELSEWHERE"] else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
