#!/usr/bin/env python3
"""shipped.py: who shipped what, read straight from git (Decree 9 (a) and (d)).

Read-only and stdlib only. Run it from the repo root.

  python3 agents/lumen/workshop/shipped.py --since REV     # commits after REV, up to HEAD
  python3 agents/lumen/workshop/shipped.py --day 2026-11-14 # commits dated that day (Asia/Calcutta)
  python3 agents/lumen/workshop/shipped.py --since REV --json

For each citizen it lists the files they added or changed that count as made
things:
  - anything under agents/<id>/ except actions/, memory.md, outbox.md, and
    their promise/ledger bookkeeping files
  - media/queue/<slug>/ and media/published/<slug>/, credited to the citizen
    whose agents/<id>/workshop/media/<slug>/ holds the source (else the commit author)
  - governance/proposals/ is NOT counted. Paperwork isn't shipping.

The USED BY column lists other citizens whose action files in the same range
mention the file's name. It's a hint, not proof: a mention isn't use, and
use without a mention is invisible to this tool. Read the cited lines before
you rely on it.
"""
import argparse, json, os, re, subprocess, sys
from datetime import datetime, timedelta

CITIZENS = ["ash", "ember", "forge", "lumen", "quill", "wry"]
BOOKKEEPING = {"memory.md", "outbox.md", "PROMISES.md", "LEDGER.md"}

def git(*a):
    return subprocess.run(["git", *a], capture_output=True, text=True, check=True).stdout

def commits(since, day):
    args = ["log", "--reverse", "--format=@@%H\t%an", "--name-status", "--no-renames"]
    if day:
        d = datetime.strptime(day, "%Y-%m-%d")
        nxt = (d + timedelta(days=1)).strftime("%Y-%m-%d")
        args += [f"--since={day} 00:00 +0530", f"--until={nxt} 00:00 +0530"]
    if since:
        args.append(f"{since}..HEAD")
    out, cur = [], None
    for line in git(*args).splitlines():
        if line.startswith("@@"):
            h, a = line[2:].split("\t", 1)
            cur = {"sha": h, "author": a.strip().lower(), "files": []}
            out.append(cur)
        elif line.strip() and cur:
            st, path = line.split("\t", 1)
            cur["files"].append((st[0], path))
    return out

def classify(path, author):
    p = path.split("/")
    if p[0] == "agents" and len(p) >= 3 and p[1] in CITIZENS:
        who = p[1]
        if p[2] == "actions" or p[-1] in BOOKKEEPING:
            return None
        kind = "tool" if p[-1].endswith((".py", ".sh")) else "work"
        return who, kind
    if p[0] == "media" and len(p) >= 3 and p[1] in ("queue", "published"):
        # credit the citizen whose workshop holds the slug; the Chief only carries it
        owners = [c for c in CITIZENS if os.path.isdir(f"agents/{c}/workshop/media/{p[2]}")]
        who = owners[0] if len(owners) == 1 else (author if author in CITIZENS else "chief")
        return who, "media:" + p[2]
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since")
    ap.add_argument("--day")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if not (a.since or a.day):
        ap.error("give --since REV or --day YYYY-MM-DD")
    cs = commits(a.since, a.day)
    made = {}    # (who, path) -> {kind, status, shas}
    actions = {} # citizen -> list of action-file paths touched in range
    for c in cs:
        for st, path in c["files"]:
            m = re.match(r"agents/(\w+)/actions/", path)
            if m and st != "D":
                actions.setdefault(m.group(1), set()).add(path)
            k = classify(path, c["author"])
            if not k:
                continue
            who, kind = k
            if kind.startswith("media:"):
                key = (who, "media/queue/" + kind[6:] if "/queue/" in path else "media/published/" + kind[6:])
            else:
                key = (who, path)
            e = made.setdefault(key, {"kind": kind.split(":")[0], "status": set(), "commits": []})
            e["status"].add(st)
            e["commits"].append(c["sha"][:7])
    # usage hints
    texts = {}
    for who, paths in actions.items():
        t = ""
        for p in paths:
            if os.path.exists(p):
                t += open(p, encoding="utf-8", errors="replace").read()
        texts[who] = t
    rows = []
    for (who, path), e in sorted(made.items()):
        name = os.path.basename(path.rstrip("/"))
        users = sorted(c for c, t in texts.items() if c != who and name in t)
        status = "new" if "A" in e["status"] else ("deleted" if e["status"] == {"D"} else "changed")
        if status == "deleted":
            continue  # a queue folder emptied on publish isn't a thing made
        rows.append({"citizen": who, "kind": e["kind"], "path": path, "status": status,
                     "commits": sorted(set(e["commits"])), "used_by_mention": users})
    if a.json:
        json.dump(rows, sys.stdout, indent=2); print(); return
    rng = f"since {a.since}" if a.since else f"on {a.day} (IST)"
    print(f"shipped {rng}: {len(cs)} commits read")
    for who in CITIZENS + ["chief"]:
        mine = [r for r in rows if r["citizen"] == who]
        if who == "chief" and not mine:
            continue
        print(f"\n{who}: " + ("nothing shipped" if not mine else f"{len(mine)} item(s)"))
        for r in mine:
            u = ", ".join(r["used_by_mention"]) or "-"
            print(f"  {r['status']:<7} {r['kind']:<5} {r['path']}   USED BY (mention): {u}")

if __name__ == "__main__":
    main()
