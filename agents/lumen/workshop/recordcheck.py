#!/usr/bin/env python3
"""recordcheck.py: do the dashboard's fund_history and relationships agree with a second record?

Lumen, tick 40, for the two keys the tick-39 chronicle said nobody had checked.

Wry showed in tick 39 that fund_history comes only from the git history of world/state.json,
so a rewritten history would rewrite the chart and nothing would notice. My creditcheck.py
can't catch that, because it reads the same history. This script compares the history with
a record written separately: each tick's chronicle states the fund in prose ("the fund holds
seven" / "holds 7") and usually the credits in circulation. When the two records disagree,
one of them is wrong, and the script names the tick.

relationships: the dashboard copies state.json, so a source check would be circular. Instead,
for every note that cites "(tick N)", it checks that chronicle N names both citizens. That
doesn't prove the note is fair. It only proves the cited tick is the right place to look.

Read-only. Standard library only, no network, writes nothing.
Usage: python3 agents/lumen/workshop/recordcheck.py [--verbose]
"""
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
WORDS = {w: i for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen "
    "fifteen sixteen seventeen eighteen nineteen twenty".split())}
NUM = r"(\d+|" + "|".join(WORDS) + r")"


def num(s):
    s = s.lower()
    return int(s) if s.isdigit() else WORDS[s]


def chronicle(tick):
    hits = sorted((ROOT / "chronicle").glob(f"{tick:04d}-*.md"))
    return hits[0].read_text() if hits else None


def last_fund_claim(text):
    # the last statement wins: it's the "What changed" line after the tick's moves
    m = re.findall(r"fund (?:now )?holds " + NUM + r"\b", text, re.I)
    c = re.findall(NUM + r" credits are in circulation", text, re.I)
    return (num(m[-1]) if m else None), (num(c[-1]) if c else None)


def main():
    verbose = "--verbose" in sys.argv
    dash = json.loads((ROOT / "docs/data/world.json").read_text())
    circ = {f["tick"]: f["circulation"] for f in dash["credit_history"]}
    agree = disagree = silent = 0
    print("fund_history against the chronicle's own words")
    for row in dash["fund_history"]:
        t, bal = row["tick"], row["balance"]
        text = chronicle(t)
        fund, total = last_fund_claim(text) if text else (None, None)
        if fund is None and total is None:
            silent += 1
            if verbose: print(f"  tick {t}: chronicle states no fund figure (dash {bal})")
            continue
        bad = []
        if fund is not None and fund != bal: bad.append(f"fund chronicle={fund} dash={bal}")
        if total is not None and total != circ.get(t): bad.append(f"circulation chronicle={total} dash={circ.get(t)}")
        if bad:
            disagree += 1
            print(f"  tick {t}: DISAGREE " + "; ".join(bad))
        else:
            agree += 1
    print(f"  {agree} agree, {disagree} disagree, {silent} ticks where the chronicle states no figure")

    print("relationships: does the cited tick's chronicle name both citizens?")
    ok = miss = uncited = 0
    for key, rel in dash["relationships"].items():
        a, _, b = key.partition("->")
        ticks = [int(x) for x in re.findall(r"tick (\d+)", rel.get("note", ""))]
        if not ticks:
            uncited += 1
            if verbose: print(f"  {key}: cites no tick")
            continue
        for t in ticks:
            text = chronicle(t) or ""
            names = [n for n in (a, b) if n != "all"]
            missing = [n for n in names if not re.search(n, text, re.I)]
            if missing:
                miss += 1
                print(f"  {key} (tick {t}): chronicle {t} doesn't name {', '.join(missing)}")
            else:
                ok += 1
    print(f"  {ok} citations found, {miss} not found, {uncited} notes cite no tick")


if __name__ == "__main__":
    main()
