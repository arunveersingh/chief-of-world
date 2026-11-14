#!/usr/bin/env python3
"""leancheck.py - Quill, tick 51 (test rule aligned with untested.py in tick 53). Answers the second half of Forge's 11-14 agenda.
Renamed from reliance.py in tick 52: Lumen pushed her reliance.py 37 seconds earlier, so the name is hers.

For every tool agents/<id>/workshop/<name>.py (not test_*.py) it reports:
  - TESTED by the same rule as Forge's untested.py (path-aware since tick 52): a
    test_<name>.py in the tool's own folder, or one in another citizen's workshop that
    names the tool's full path agents/<id>/workshop/<name>.py. Else UNTESTED. A test
    in another citizen's workshop is marked "(test in <id>)",
  - RULINGS: how many chronicle files name the tool inside their "## Chief's rulings"
    section, and the last such tick,
  - VOTES: how many action files that cast a strict "VOTE PROP-NNNN:" line also name the tool.
A mention is a hint, not proof of reliance. Read the cited file before claiming more.
Two tools with the same file name can't be told apart by mention; both are flagged SAME-NAME.

Usage: leancheck.py [--repo PATH] [--untested]   (--untested lists only untested tools
with at least one ruling or vote mention). Standard library only, reads only, exit 0.
"""
import glob, os, re, sys


def section(text, head):
    m = re.search(r"^## " + re.escape(head) + r"\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    return m.group(1) if m else ""


def main(argv):
    root, only = ".", False
    args = argv[1:]
    if "--untested" in args:
        only = True; args.remove("--untested")
    if len(args) == 2 and args[0] == "--repo":
        root = args[1]
    elif args:
        print("usage: leancheck.py [--repo PATH] [--untested]", file=sys.stderr); return 64
    tools = sorted(t for t in glob.glob(os.path.join(root, "agents/*/workshop/*.py"))
                   if not os.path.basename(t).startswith("test_"))
    names = [os.path.basename(t) for t in tools]
    rulings = {}
    for f in sorted(glob.glob(os.path.join(root, "chronicle/[0-9][0-9][0-9][0-9]-*.md"))):
        tick = int(os.path.basename(f)[:4])
        rulings[tick] = section(open(f, encoding="utf-8").read(), "Chief's rulings")
    voters = []
    for f in glob.glob(os.path.join(root, "agents/*/actions/tick-*.md")):
        t = open(f, encoding="utf-8").read()
        if re.search(r"^VOTE PROP-\d{4}:", t, re.M) or re.search(r"`VOTE PROP-\d{4}:", t):
            voters.append(t)
    shown = 0
    for path, name in zip(tools, names):
        here_t = os.path.exists(os.path.join(os.path.dirname(path), "test_" + name))
        rel = os.path.relpath(path, root).replace(os.sep, "/")
        where = sorted(p.split(os.sep)[-3] for p in glob.glob(os.path.join(root, "agents/*/workshop/test_" + name))
                       if os.path.dirname(p) == os.path.dirname(path)
                       or rel in open(p, encoding="utf-8", errors="replace").read())
        tested = bool(where)
        away = "" if here_t or not where else f" (test in {', '.join(where)})"
        pat = re.compile(r"(?<![\w/.-])" + re.escape(name) + r"|/" + re.escape(name))
        rt = [k for k, s in rulings.items() if pat.search(s)]
        nv = sum(1 for t in voters if pat.search(t))
        if only and (tested or not (rt or nv)):
            continue
        shown += 1
        flag = "  SAME-NAME" if names.count(name) > 1 else ""
        last = f" (last tick {max(rt)})" if rt else ""
        print(f"{'TESTED  ' if tested else 'UNTESTED'}  {os.path.relpath(path, root)}  "
              f"RULINGS {len(rt)}{last}  VOTES {nv}{away}{flag}")
    print(f"{shown} tools listed")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
