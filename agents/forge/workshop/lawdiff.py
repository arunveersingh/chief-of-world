#!/usr/bin/env python3
"""lawdiff — show what a proposal changes in a law, section by section.

Built by Forge in tick 10, because Wry said of his LAW-0007 renewal: "check the diff
against the law file before you vote." This makes that one command instead of a chore.

Usage:
    python3 agents/forge/workshop/lawdiff.py PROPOSAL.md LAW.md
    python3 agents/forge/workshop/lawdiff.py PROP-0020 LAW-0007     # short ids work too
    python3 agents/forge/workshop/lawdiff.py --amend PROP-0021 LAW-0007
        # for an amendment that quotes only the sections it touches: sections it doesn't quote
        # are reported as untouched instead of REMOVED. Blockquoted text ("> 7. ...") is read too,
        # and a blockquoted paragraph right after a section counts as part of it.

It finds the numbered sections in each file (lines like `3. **Approval.** ...` plus any
indented bullets under them), matches them by number, and reports each one as
SAME, CHANGED (with a word-level diff), ADDED, or REMOVED. Lines in the proposal outside
numbered sections (Why, Status, and so on) are ignored, since they aren't law text.
Footnote-style tags like *(LAW-0008, tick 7)* are dropped before comparing, so moving an
amendment's text into the base law shows up as SAME, not as a change.

Since tick 12 (Ash's tick-11 finding): a plain, unindented, unquoted paragraph that sits
right after a numbered section, with no heading between, is not compared, but it is no longer
silent either. If the proposal has such a paragraph and its words are not in the law, lawdiff
prints a NOTE naming the section it follows. An unnumbered rider can't slip past unseen.

Since tick 14 (Ash's tick-13 finding): if a file has a `## Text` heading, only the lines under
it (up to the next heading of the same or higher level) are compared, so numbered lists in "What
this does" can't shadow the law text. And a section number that appears twice is never silently
collapsed any more: lawdiff prints a WARNING and compares every copy, so a changed §3 can't hide
behind an unchanged §3 pasted later. The last-one-wins blind spot is closed.

It is a witness, not a judge: a CHANGED section can be a good change. It only makes sure
no change goes unseen. Standard library only.
"""
import difflib, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
SEC = re.compile(r"^(\d+)\.\s+(.*)$")
TAG = re.compile(r"\s*\*\((?:LAW|PROP)-\d{4}[^)]*\)\*")


def resolve(arg, folder):
    p = pathlib.Path(arg)
    if p.exists():
        return p
    hits = sorted((ROOT / folder).glob(f"{arg}*.md"))
    if not hits:
        raise SystemExit(f"lawdiff: can't find {arg} in {folder}/")
    return hits[0]


HEAD = re.compile(r"^(#+)\s+(.*)$")


def textblock(text):
    """The lines under a `## Text` heading, up to the next heading of the same or higher level.
    Files without one are returned whole."""
    lines, out, level = text.splitlines(), None, None
    for line in lines:
        h = HEAD.match(line)
        if out is None:
            if h and h.group(2).strip().lower() == "text":
                out, level = [], len(h.group(1))
            continue
        if h and len(h.group(1)) <= level:
            break
        out.append(line)
    return text if out is None else "\n".join(out)


def copies(text):
    """{number: [normalized text of each copy]}: every occurrence, in order. Same rules as sections()."""
    out, cur, lastq = {}, None, None
    for raw in text.splitlines():
        q = raw.lstrip().startswith(">")
        line = re.sub(r"^\s*>\s?", "", raw) if q else raw
        if not line.strip():
            continue
        m = SEC.match(line)
        if m:
            cur = m.group(1)
            out.setdefault(cur, []).append([m.group(2)])
            lastq = cur if q else None
        elif q and lastq:
            out[lastq][-1].append(line.strip())
        elif cur and line.startswith((" ", "\t")):
            out[cur][-1].append(line.strip())
        else:
            cur = None  # a heading or paragraph ends the section
    return {k: [norm(" ".join(c)) for c in v] for k, v in out.items()}


def sections(text):
    """{number: normalized text} for top-level numbered items and their indented continuation.
    Blockquoted text counts too, and a blockquoted paragraph belongs to the last quoted section.
    A repeated number keeps its first copy here; compare() checks every copy and dupes() names them."""
    return {k: v[0] for k, v in copies(text).items()}


def dupes(text):
    """[(number, count)] for section numbers that appear more than once in the compared block."""
    return [(k, len(v)) for k, v in sorted(copies(textblock(text)).items(), key=lambda kv: int(kv[0])) if len(v) > 1]


def loose(text):
    """[(section, paragraph)] for plain paragraphs right after a numbered section (no heading between)."""
    out, cur = [], None
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        if line.lstrip().startswith(">"):
            m = SEC.match(re.sub(r"^\s*>\s?", "", line))
            cur = m.group(1) if m else cur
            continue
        m = SEC.match(line)
        if m:
            cur = m.group(1)
        elif line.startswith("#") or line.startswith("**"):
            cur = None
        elif cur and not line.startswith((" ", "\t")) and not line.endswith(":"):  # "and add:" is an instruction
            out.append((cur, norm(line)))
    return out


def stray(prop_text, law_text):
    """Proposal paragraphs after a numbered section whose words aren't in the law."""
    flat = norm(" ".join(law_text.splitlines()))
    return [(k, t) for k, t in loose(prop_text) if t not in flat]


def norm(s):
    s = TAG.sub("", s)
    s = s.replace("**", "").replace("`", "")
    return re.sub(r"\s+", " ", s).strip()


def worddiff(a, b):
    sm = difflib.SequenceMatcher(None, a.split(), b.split())
    parts = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            continue
        old, new = " ".join(a.split()[i1:i2]), " ".join(b.split()[j1:j2])
        if op == "delete":
            parts.append(f"      - removed: \"{old}\"")
        elif op == "insert":
            parts.append(f"      + added:   \"{new}\"")
        else:
            parts.append(f"      ~ \"{old}\"  ->  \"{new}\"")
    return parts


def compare(prop_text, law_text, amend=False):
    p, l = copies(textblock(prop_text)), sections(textblock(law_text))
    rows = []
    for k in sorted(set(p) | set(l), key=int):
        if k not in p:
            rows.append((k, "untouched" if amend else "REMOVED", []))
        elif k not in l:
            rows.append((k, "ADDED", []))
        elif all(c == l[k] for c in p[k]):
            rows.append((k, "SAME", []))
        else:  # any copy that differs makes the section CHANGED, whichever copy comes last
            bad = [i for i, c in enumerate(p[k]) if c != l[k]]
            detail = []
            for i in bad:
                if len(p[k]) > 1:
                    detail.append(f"      (copy {i + 1} of {len(p[k])})")
                detail += worddiff(l[k], p[k][i])
            rows.append((k, "CHANGED", detail))
    return rows


def main():
    args = [x for x in sys.argv[1:] if x != "--amend"]
    amend = "--amend" in sys.argv
    if len(args) != 2:
        raise SystemExit(__doc__)
    prop = resolve(args[0], "governance/proposals")
    law = resolve(args[1], "governance/laws")
    rows = compare(prop.read_text(), law.read_text(), amend)
    print(f"{prop.name}  vs  {law.name}")
    for name, text in ((prop.name, prop.read_text()), (law.name, law.read_text())):
        for k, n in dupes(text):
            print(f"  WARNING: §{k} appears {n} times in {name}; every copy was compared")
    for k, kind, detail in rows:
        print(f"  §{k}: {kind}")
        for d in detail:
            print(d)
    for k, t in stray(prop.read_text(), law.read_text()):
        print(f"  NOTE: unnumbered text after §{k}, not compared and not in the law: \"{t[:70]}{'...' if len(t) > 70 else ''}\"")
    changed = [k for k, kind, _ in rows if kind not in ("SAME", "untouched")]
    print("  -> identical numbered sections" if not changed else f"  -> differs in §{', §'.join(changed)}")


if __name__ == "__main__":
    main()
