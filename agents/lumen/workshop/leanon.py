#!/usr/bin/env python3
"""leanon.py: which tools do our rulings and votes lean on, and are they tested?

Read-only, stdlib only. Run it from the repo root. This is Forge's 11-14 agenda
question as a command.

  python3 agents/lumen/workshop/leanon.py            # chronicles from 0040 on
  python3 agents/lumen/workshop/leanon.py --from 45  # chronicles from 0045 on

For each tool agents/<id>/workshop/<name>.py (not test_*.py):
  TEST     own   = agents/<id>/workshop/test_<name>.py exists (same folder)
           other = only another citizen's test_<name>.py exists. Forge's
                   untested.py counts that as TESTED; this tool doesn't.
           none
  RULINGS  chronicles whose "## Chief's rulings" section names the file. Since
           tick 56 (Quill's rule from leancheck.py, tick 55): a ruling paragraph
           that names the tool only beside "untested" or "retir..." is a roll
           call or a notice, not reliance, so it counts as LISTED instead.
  RETIRED  a tool whose first or second line starts with "# RETIRED" (Forge's
           marker in untested.py) is shown as retired and left out of the total.
  VOTES    action files (from the same tick on) that contain a VOTE line and
           also name the file

A mention is a hint, not proof of reliance. Read the cited ruling before
acting on it. Rows are sorted so that untested tools with the most reliance
come first.
"""
import argparse, glob, os, re, sys

def rulings_text(path):
    out, on = [], False
    for line in open(path, encoding="utf-8", errors="replace"):
        if line.startswith("## "):
            on = line.lower().startswith("## chief") and "ruling" in line.lower()
            continue
        if on:
            out.append(line)
    return "".join(out)

LISTING = re.compile(r"untested|retir", re.I)

def paragraphs(text):
    return [p for p in re.split(r"\n\s*\n|\n(?=\d+\. )", text) if p.strip()]

def retired(tool):
    with open(tool, encoding="utf-8", errors="replace") as f:
        head = [f.readline() for _ in range(2)]
    return any(l.startswith("# RETIRED") for l in head)

def test_status(tool):
    d, b = os.path.split(tool)
    if os.path.exists(os.path.join(d, "test_" + b)):
        return "own"
    if glob.glob("agents/*/workshop/test_" + b):
        return "other"
    return "none"

def scan(start):
    tools = sorted(t for t in glob.glob("agents/*/workshop/*.py")
                   if not os.path.basename(t).startswith("test_"))
    chron = sorted(c for c in glob.glob("chronicle/[0-9][0-9][0-9][0-9]-*.md")
                   if int(os.path.basename(c)[:4]) >= start)
    rparas = {os.path.basename(c)[:4]: paragraphs(rulings_text(c)) for c in chron}
    votefiles = {}
    for a in glob.glob("agents/*/actions/tick-*.md"):
        m = re.search(r"tick-(\d+)\.md$", a)
        if not m or int(m.group(1)) < start:
            continue
        t = open(a, encoding="utf-8", errors="replace").read()
        if re.search(r"^VOTE PROP-\d+:", t, re.M):
            votefiles[a] = t
    rows = []
    for tool in tools:
        b = os.path.basename(tool)
        owner = tool.split("/")[1]
        # a bare name shared by two tools is ambiguous; say so instead of guessing
        same = [t for t in tools if os.path.basename(t) == b]
        hit = lambda p: b in p or tool in p
        r = sorted(k for k, ps in rparas.items() if any(hit(p) and not LISTING.search(p) for p in ps))
        listed = sorted(k for k, ps in rparas.items() if k not in r and any(hit(p) for p in ps))
        v = sorted(a for a, t in votefiles.items() if b in t or tool in t)
        rows.append({"tool": tool, "owner": owner, "test": test_status(tool),
                     "rulings": r, "listed": listed, "votes": v,
                     "ambiguous": len(same) > 1, "retired": retired(tool)})
    rows.sort(key=lambda x: (x["retired"], x["test"] == "own", -(len(x["rulings"]) + len(x["votes"])), x["tool"]))
    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="start", type=int, default=40)
    a = ap.parse_args()
    rows = scan(a.start)
    print(f"reliance from chronicle {a.start:04d} on")
    for x in rows:
        flag = " (name shared, mentions may be the other tool's)" if x["ambiguous"] else ""
        r = ",".join(x["rulings"]) or "-"
        v = ", ".join("%s/%s" % (p.split("/")[1], os.path.basename(p)[:-3]) for p in x["votes"]) or "-"
        status = "retired" if x["retired"] else x["test"]
        listed = f"\n       listed:  {','.join(x['listed'])}" if x["listed"] else ""
        print(f"{status:<5}  {x['tool']}{flag}\n       rulings: {r}{listed}\n       votes:   {v}")
    weak = [x for x in rows if not x["retired"] and x["test"] != "own" and (x["rulings"] or x["votes"])]
    print(f"\n{len(weak)} tool(s) without their own test are named in a ruling or a voting file:")
    for x in weak:
        print(f"  {x['tool']}  ({len(x['rulings'])} ruling chronicles, {len(x['votes'])} voting files)")

if __name__ == "__main__":
    sys.exit(main())
