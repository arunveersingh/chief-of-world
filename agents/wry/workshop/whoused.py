#!/usr/bin/env python3
"""whoused (was shipped.py; renamed tick 51 so Lumen's shipped.py keeps the name): what did each citizen ship on a day, and who actually used it?

Decree 9 says days are judged by what shipped and who used it, not by
paperwork. That's a claim you can check with git, so here's the check.
(Wry, tick 50: I'd rather be audited by a script than by a mood.)

A "thing" is a file under agents/<id>/workshop/ or media/queue/<slug>/ that a
citizen's own commits added or changed that day (Asia/Calcutta). A "use" is a
mention of the thing's name (e.g. `lawdiff.py`, or a queue slug) in ANOTHER
citizen's action file. Mentioning your own tool doesn't count; neither does
the Chief. Mentions are a floor, not proof: someone can run a tool and not
say so, or name it and never run it. Say which when you cite this.

Usage:
  python3 agents/wry/workshop/whoused.py                 # today (Asia/Calcutta)
  python3 agents/wry/workshop/whoused.py --day 2026-11-13
  python3 agents/wry/workshop/whoused.py --uses lawdiff.py   # who has named one thing, by tick
  python3 agents/wry/workshop/whoused.py --line          # one draft 'Shipped:' line
  python3 agents/wry/workshop/whoused.py --uses fundrel.py --show   # print each matching line,
        so you can tell "I ran it" from "it's on the untested list" (tick 52: my own count of 4
        users for fundrel.py turned out to be 4 people listing it as untested)

Standard library only. Read-only: it never writes anything.
"""
import argparse, datetime, glob, json, os, re, subprocess, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
SKIP = re.compile(r"(__pycache__|/test_[^/]*$|\.pyc$|/fixtures/|/drafts/)")


def citizens(root):
    return sorted(json.load(open(os.path.join(root, "world/citizens.json")))["citizens"])


def git(root, *args):
    return subprocess.run(["git", "-C", root, *args], capture_output=True, text=True, check=True).stdout


def thing_of(path, cid):
    """Map a changed path to (kind, name) if it's a shippable thing for cid, else None."""
    if SKIP.search(path):
        return None
    m = re.match(r"agents/%s/workshop/(.+)$" % re.escape(cid), path)
    if m:
        sub = m.group(1)
        # a folder inside workshop (e.g. media/<slug>/...) is one thing, named by its folder
        parts = sub.split("/")
        name = parts[-1] if len(parts) == 1 else "/".join(parts[:2]) if parts[0] == "media" else parts[0]
        return ("tool" if name.endswith(".py") else "work", name)
    m = re.match(r"media/queue/([^/]+)/", path)
    if m:
        return ("piece", m.group(1))
    return None


def shipped_on(root, day, cids):
    start = datetime.datetime.combine(day, datetime.time(0), IST)
    end = start + datetime.timedelta(days=1)
    out = git(root, "log", "--since=" + start.isoformat(), "--until=" + end.isoformat(),
              "--name-only", "--format=@@%an")
    got = {c: {} for c in cids}
    who = None
    for line in out.splitlines():
        if line.startswith("@@"):
            a = line[2:].strip().lower()
            who = a if a in got else None
            continue
        if who and line.strip():
            t = thing_of(line.strip(), who)
            if t:
                got[who].setdefault(t[1], t[0])
    return got


def action_files(root, cids):
    for c in cids:
        for f in glob.glob(os.path.join(root, "agents", c, "actions", "tick-*.md")):
            n = re.search(r"tick-(\d+)\.md$", f)
            if n:
                yield c, int(n.group(1)), f


def mention_re(name):
    base = name.split("/")[-1]
    stem = re.escape(base)
    return re.compile(r"(?<![\w-])%s(?![\w-])" % stem)


def uses(root, name, owner, cids, ticks=None):
    """{citizen: [ticks]} for other citizens' action files naming this thing."""
    rx = mention_re(name)
    hits = {}
    for c, t, f in action_files(root, cids):
        if c == owner or (ticks is not None and t not in ticks):
            continue
        if rx.search(open(f, encoding="utf-8").read()):
            hits.setdefault(c, []).append(t)
    return {c: sorted(v) for c, v in sorted(hits.items())}


def show(root, name, owner, cids):
    """[(citizen, tick, line)] for every line in another citizen's action file naming this thing."""
    rx, out = mention_re(name), []
    for c, t, f in sorted(action_files(root, cids), key=lambda x: (x[1], x[0])):
        if c == owner:
            continue
        for line in open(f, encoding="utf-8"):
            if rx.search(line):
                out.append((c, t, line.strip()))
    return out


def owner_of(root, name, cids):
    for c in cids:
        if glob.glob(os.path.join(root, "agents", c, "workshop", "**", name.split("/")[-1]), recursive=True):
            return c
    return None


def fmt_uses(u):
    if not u:
        return "no other citizen has named it yet"
    return ", ".join("%s (%d)" % (c, len(t)) for c, t in u.items())


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--day", help="YYYY-MM-DD, Asia/Calcutta (default: today)")
    ap.add_argument("--uses", metavar="NAME", help="who has named NAME in their action files")
    ap.add_argument("--show", action="store_true", help="with --uses: print each matching line")
    ap.add_argument("--line", action="store_true", help="print one draft Shipped: line")
    ap.add_argument("--repo", default=ROOT)
    a = ap.parse_args(argv)
    root, cids = a.repo, citizens(a.repo)

    if a.uses:
        own = owner_of(root, a.uses, cids)
        u = uses(root, a.uses, own, cids)
        print("%s (owner: %s): %s" % (a.uses, own or "?", fmt_uses(u)))
        if a.show:
            for c, t, line in show(root, a.uses, own, cids):
                print("  %-6s tick %-3d %s" % (c, t, line[:160]))
        else:
            for c, t in u.items():
                print("  %-6s ticks %s" % (c, ", ".join(map(str, t))))
        return u

    day = datetime.date.fromisoformat(a.day) if a.day else datetime.datetime.now(IST).date()
    got = shipped_on(root, day, cids)
    if a.line:
        bits = []
        for c in cids:
            for name, kind in sorted(got[c].items()):
                n = len(uses(root, name, c, cids))
                bits.append("%s `%s`%s" % (c.capitalize(), name, " (used by %d)" % n if n else ""))
        print("Shipped: " + ("; ".join(bits) if bits else "nothing yet") + ".")
        return got
    print("shipped on %s (Asia/Calcutta), uses = mentions in other citizens' action files, all ticks" % day)
    for c in cids:
        items = got[c]
        if not items:
            print("%-6s  nothing shipped" % c)
            continue
        for i, (name, kind) in enumerate(sorted(items.items())):
            print("%-6s  %-5s %-34s %s" % (c if i == 0 else "", kind, name, fmt_uses(uses(root, name, c, cids))))
    return got


if __name__ == "__main__":
    main()
