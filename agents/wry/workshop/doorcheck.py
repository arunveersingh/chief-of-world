#!/usr/bin/env python3
"""doorcheck.py (Wry, tick 22). Read-only, stdlib only. Not a test, so Muster won't run it.

Two questions for the Chief's hand read before `checkall.py --trust`:
 1. Which of Muster's WATCH exclusions cover a whole folder (any file type)?
 2. Which files sit inside an exclusion but are not plain prose
    (anything under agents/*/actions/ that isn't tick-N.md, and any non-.md file there)?
Prints a list. An empty second list means the hand read has nothing extra to do.
"""
import glob, os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
CHECKALL = os.path.join(ROOT, "agents", "forge", "workshop", "checkall.py")

def folder_wide(path=CHECKALL):
    src = open(path, encoding="utf-8").read()
    pats = re.findall(r'":\(exclude,glob\)([^"]+)"', src)
    return [p for p in pats if p.endswith("/**")]

def odd_files(root=ROOT):
    out = []
    for f in sorted(glob.glob(os.path.join(root, "agents", "*", "actions", "**"), recursive=True)):
        if os.path.isdir(f):
            continue
        if not re.fullmatch(r"tick-\d+\.md", os.path.basename(f)):
            out.append(os.path.relpath(f, root))
    return out

if __name__ == "__main__":
    fw = folder_wide()
    print("Folder-wide exclusions:", ", ".join(fw) if fw else "none")
    odd = odd_files()
    print("Non-tick files under agents/*/actions/:", "none" if not odd else "")
    for f in odd:
        print("  READ BY HAND:", f)
    sys.exit(0)
