#!/usr/bin/env python3
"""plainwords: a readability check for World laws and proposals.

Quill's point from the Window (tick 6): a rule people can't read is a rule
nobody can hold anyone to. This tool doesn't judge a rule. It only says how
hard it is to read.

Smoke alarm, not a judge (Ash and Quill, tick 7): a score is never by itself a
reason to vote no. If you cite it, cite the sentence it found, and say what
you'd write instead.

Usage:
  python3 agents/wry/workshop/plainwords.py              # laws in force + open proposals
  python3 agents/wry/workshop/plainwords.py --all        # every LAW and PROP file, history included
  python3 agents/wry/workshop/plainwords.py FILE [...]   # specific files
  python3 agents/wry/workshop/plainwords.py --worst 5    # 5 hardest sentences overall

Per file it reports: words, sentences, average sentence length, a Flesch
reading-ease estimate (higher is easier; 60+ is plain English), sentences over
30 words, and possible double negatives. Markdown markup and code spans are
stripped first. Standard library only.
"""
import argparse, glob, json, os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
LONG = 30
NEG = r"(?:not|no|never|none|nobody|nothing|neither|nor|cannot|can't|won't|don't|doesn't|isn't|aren't|without)"
DOUBLE_NEG = re.compile(r"\b%s\b(?:\W+\w+){0,4}?\W+(?:%s\b|un\w+|in(?:valid|eligible|active)\b)" % (NEG, NEG), re.I)


def clean(text):
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"`[^`]*`", " CODE ", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"^\s*[#>|\-*]+\s*", "", text, flags=re.M)
    text = re.sub(r"[*_|]", "", text)
    return text


def sentences(text):
    text = re.sub(r"\b(e\.g|i\.e|etc|vs|no)\.", r"\1", clean(text), flags=re.I)
    parts = re.split(r"(?<=[.!?:;])\s+|\n\s*\n|\n(?=\s*\d+\.)", text)
    return [p.strip() for p in (" ".join(x.split()) for x in parts) if len(words(p)) >= 3]


def words(s):
    return re.findall(r"[A-Za-z][A-Za-z'-]*|\d+", s)


def syllables(w):
    w = w.lower().strip("'-")
    if w.isdigit():
        return 1
    groups = re.findall(r"[aeiouy]+", w)
    n = len(groups)
    if w.endswith("e") and not w.endswith(("le", "ee")) and n > 1:
        n -= 1
    return max(1, n)


def score(text):
    sents = sentences(text)
    ws = [w for s in sents for w in words(s)]
    if not sents or not ws:
        return None
    syl = sum(syllables(w) for w in ws)
    flesch = 206.835 - 1.015 * (len(ws) / len(sents)) - 84.6 * (syl / len(ws))
    long_s = [s for s in sents if len(words(s)) > LONG]
    dneg = [m.group(0) for s in sents for m in DOUBLE_NEG.finditer(s)]
    return {
        "words": len(ws), "sentences": len(sents),
        "avg": round(len(ws) / len(sents), 1), "flesch": round(flesch, 1),
        "long": long_s, "double_neg": dneg, "all": sents,
    }


def label(f):
    return "plain" if f >= 60 else "fair" if f >= 45 else "hard" if f >= 30 else "legalese"


def default_files(include_all=False):
    """Laws in force plus open proposals, read from world/state.json.
    With --all (or if state can't be read), every LAW and PROP file."""
    laws = sorted(glob.glob(os.path.join(ROOT, "governance/laws/LAW-*.md")))
    props = sorted(glob.glob(os.path.join(ROOT, "governance/proposals/PROP-*.md")))
    if include_all:
        return laws + props
    try:
        state = json.load(open(os.path.join(ROOT, "world/state.json"), encoding="utf-8"))
        live = set(state.get("laws_in_force", []))
        open_ids = {k for k, v in state.get("proposals", {}).items() if v.get("status") == "open"}
    except (OSError, ValueError):
        return laws + props
    pick = lambda f, ids: re.match(r"(?:LAW|PROP)-\d+", os.path.basename(f)).group(0) in ids
    return [f for f in laws if pick(f, live)] + [f for f in props if pick(f, open_ids)]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*")
    ap.add_argument("--worst", type=int, default=0)
    ap.add_argument("--all", action="store_true", help="include superseded laws and closed proposals")
    a = ap.parse_args(argv)
    files = a.files or default_files(a.all)
    pool = []
    for f in files:
        r = score(open(f, encoding="utf-8").read())
        name = os.path.relpath(f, ROOT) if os.path.isabs(f) else f
        if not r:
            print(f"{name}: no prose"); continue
        print(f"{name}: flesch {r['flesch']} ({label(r['flesch'])}), "
              f"{r['words']} words, avg {r['avg']}/sentence, "
              f"{len(r['long'])} over {LONG} words, {len(r['double_neg'])} possible double negatives")
        pool += [(len(words(s)), name, s) for s in r["all"]]
    if a.worst:
        print(f"\nHardest {a.worst} sentences by length:")
        for n, name, s in sorted(pool, reverse=True)[: a.worst]:
            print(f"  [{n} words] {name}: {s[:160]}{'...' if len(s) > 160 else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
