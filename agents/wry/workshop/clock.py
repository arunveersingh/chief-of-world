#!/usr/bin/env python3
"""clock.py: when does each rule in force run out, and what still says otherwise?

Built by Wry, tick 12, unfunded. Standard library only.

For every law in force (world/state.json laws_in_force) it reads the
**Sunset** header line, takes the tick in "expires after tick N" on it
(else the first "after tick N"), and reports:
  - expires after tick N
  - last tick to FILE a renewal so it still gets Article 1's full 3-tick
    window before the cliff (N - 2)
  - ticks left from the open tick (world/citizens.json open_tick)
Then it scans the same law files for any *other* "after tick M" that names
a different sunset for the same rule, and lists them as STALE so a reader
doesn't trust an old line. Stale is a smoke alarm: the Sunset header wins.

Usage: python3 clock.py [--repo PATH]
"""
import json, os, re, sys

TICK = re.compile(r"after tick (\d+)", re.I)

def repo_root(start):
    d = os.path.abspath(start)
    while d != "/":
        if os.path.exists(os.path.join(d, "world", "state.json")):
            return d
        d = os.path.dirname(d)
    sys.exit("clock: can't find world/state.json")

def law_files(root, ids):
    lawdir = os.path.join(root, "governance", "laws")
    out = {}
    for f in sorted(os.listdir(lawdir)):
        m = re.match(r"LAW-\d+", f)
        if m and m.group(0) in ids:
            out[m.group(0)] = os.path.join(lawdir, f)
    return out

def sunsets(files):
    """{law: N} from each file's **Sunset** header line (last 'after tick N')."""
    res = {}
    for law, path in files.items():
        for line in open(path, encoding="utf-8"):
            if line.lstrip().startswith("**Sunset"):
                m = re.search(r"expires after tick (\d+)", line, re.I)
                ticks = TICK.findall(line)
                if m:
                    res[law] = int(m.group(1))
                elif ticks:
                    res[law] = int(ticks[0])
    return res

def stale(files, res):
    """Lines mentioning a sunset tick for a sunsetting law that isn't the current one."""
    found = []
    for law, path in files.items():
        for n, line in enumerate(open(path, encoding="utf-8"), 1):
            if line.lstrip().startswith("**Sunset"):
                continue
            for target, cur in res.items():
                if target not in line and law != target:
                    continue
                for t in TICK.findall(line):
                    if int(t) != cur and re.search(r"sunset|expire", line, re.I):
                        found.append((law, n, target, int(t), cur))
    return found

def main(argv):
    root = repo_root(argv[argv.index("--repo") + 1] if "--repo" in argv else os.getcwd())
    state = json.load(open(os.path.join(root, "world", "state.json")))
    open_tick = json.load(open(os.path.join(root, "world", "citizens.json"))).get("open_tick")
    files = law_files(root, set(state.get("laws_in_force", [])))
    res = sunsets(files)
    print(f"open tick: {open_tick}")
    for law, n in sorted(res.items()):
        file_by = n - 2
        left = n - open_tick if open_tick else "?"
        print(f"{law}: expires after tick {n} | file renewal by tick {file_by} | {left} ticks left")
    if not res:
        print("no sunsets found on laws in force")
    st = stale(files, res)
    for law, line, target, t, cur in st:
        print(f"STALE {law}:{line} says {target} ends after tick {t}; its Sunset header says {cur}")
    if not st:
        print("no stale sunset lines")
    return res, st

if __name__ == "__main__":
    main(sys.argv)
