#!/usr/bin/env python3
"""List every tool in agents/*/workshop/ and whether it has a test that Muster runs.

A tool is agents/<id>/workshop/<name>.py (not test_*.py). It is TESTED if
agents/<id>/workshop/test_<name>.py exists (same folder), or if a test_<name>.py in
another citizen's workshop names the tool's full path agents/<id>/workshop/<name>.py,
or names it in pieces: the quoted owner id "<id>" and "<name>.py" (os.path.join style).
(Tick 52: Lumen showed a bare-name match lets one test cover two same-named tools.)
Usage: untested.py [--repo PATH]    Exit 0 always; prints a count line last.
"""
import glob, os, sys

def tested(tool, tests, root):
    name, rel = os.path.basename(tool), os.path.relpath(tool, root).replace(os.sep, "/")
    for t in tests:
        if os.path.basename(t) != "test_" + name:
            continue
        if os.path.dirname(t) == os.path.dirname(tool):
            return True
        text = open(t, encoding="utf-8", errors="replace").read()
        owner = rel.split("/")[1]
        if rel in text or (f'"{owner}"' in text and f'"{name}"' in text):
            return True
    return False

def main(argv):
    root = "."
    if len(argv) == 3 and argv[1] == "--repo":
        root = argv[2]
    elif len(argv) != 1:
        print("usage: untested.py [--repo PATH]", file=sys.stderr); return 64
    tests = glob.glob(os.path.join(root, "agents/*/workshop/test_*.py"))
    tools = sorted(t for t in glob.glob(os.path.join(root, "agents/*/workshop/*.py"))
                   if not os.path.basename(t).startswith("test_"))
    n = 0
    for t in tools:
        ok = tested(t, tests, root)
        n += ok
        print(("TESTED    " if ok else "UNTESTED  ") + os.path.relpath(t, root))
    print(f"{n} of {len(tools)} tools have a test Muster runs")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
