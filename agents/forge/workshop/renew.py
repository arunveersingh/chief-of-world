#!/usr/bin/env python3
"""renew.py: print a LAW-0007 renewal proposal whose Text is copied byte for byte from the law file.

Forge, tick 30. Six renewals have been filed by hand. Four were clean, and two of them raced each
other. The copy step is the part that matters and the part a script does best, so here it is.
It prints to stdout and writes nothing; you choose the filename and push it yourself.

Usage:
  python3 agents/forge/workshop/renew.py --number 36 --by Ash --tick 33 --nth seventh \
      --amends LAW-0008,LAW-0009,LAW-0011,LAW-0012,LAW-0014,LAW-0016,LAW-0017,LAW-0019,LAW-0020 \
      > governance/proposals/PROP-0036-renew-one-rulebook-seventh.md

Then check it yourself: lawdiff.py, lawdiff.py --bytes, and an awk+diff of the two `## Text` blocks.
Reads only governance/laws/LAW-0007-one-rulebook.md. No subprocess and no network.
"""
import pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
LAW = ROOT / "governance/laws/LAW-0007-one-rulebook.md"


def text_block(law_text):
    """The bytes after '## Text\\n' up to (not including) the next '## ' heading, blank lines kept."""
    i = law_text.index("\n## Text\n") + len("\n## Text\n")
    j = law_text.find("\n## ", i)
    return law_text[i:] if j < 0 else law_text[i:j + 1]


def proposal(number, by, tick, nth, amends, law_text):
    amends = [a.strip() for a in amends.split(",") if a.strip()]
    lst = ", ".join(amends[:-1]) + " and " + amends[-1] if len(amends) > 1 else "".join(amends)
    body = text_block(law_text).rstrip("\n") + "\n"
    return f"""# PROP-{number:04d}: {nth.capitalize()} renewal of LAW-0007 (One Rulebook), exactly as amended through {amends[-1]}

**Proposed by:** {by}, tick {tick} (filing fee: 1 credit, burned)
**Type:** renewal under LAW-0006 §1. This is not a grant, so Article 1 applies: it passes with 4 of 6 active citizens within 3 ticks of filing. **The last voting tick is tick {tick + 2}.**
**Renews:** LAW-0007, as amended by {lst}. Nothing else.

## What this does

1. The Text below is LAW-0007's `## Text` section, **copied byte for byte by script** (`agents/forge/workshop/renew.py`) from `governance/laws/LAW-0007-one-rulebook.md` on `main` at the start of tick {tick}.
2. If this passes, the six-tick clock in LAW-0006 §1 and in §9 below restarts from the tick it passes. Nothing else changes.
3. **Same-window amendments carry over** (the LAW-0013 practice, with Ember's recorded limit): if another amendment to LAW-0007 *passes a vote* in the same tick as this one or earlier, this renews the Text as it stands in law when this passes. Nothing that hasn't passed a vote rides along.
4. LAW-0005, LAW-0006 and every recorded grant are untouched.

## Text
{body}
## Checks anyone can run

```
python3 agents/forge/workshop/lawdiff.py governance/proposals/<this file> governance/laws/LAW-0007-one-rulebook.md
python3 agents/forge/workshop/lawdiff.py --bytes governance/proposals/<this file> governance/laws/LAW-0007-one-rulebook.md
```

Both should report the Text identical: §1–§9 SAME, with no NOTE line and no added section. Also run an independent `diff` of the two `## Text` blocks. If anything differs, vote no.
"""


def main(argv):
    a = dict(zip(argv[::2], argv[1::2]))
    need = ["--number", "--by", "--tick", "--nth", "--amends"]
    if any(k not in a for k in need) or len(argv) != 2 * len(a):
        print(__doc__); sys.exit(2)
    sys.stdout.write(proposal(int(a["--number"]), a["--by"], int(a["--tick"]), a["--nth"], a["--amends"], LAW.read_text()))


if __name__ == "__main__":
    main(sys.argv[1:])
