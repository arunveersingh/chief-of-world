#!/usr/bin/env python3
"""List every tool in agents/*/workshop/ and whether it has a test that Muster runs.

A tool is agents/<id>/workshop/<name>.py (not test_*.py). It is TESTED if any
agents/*/workshop/test_<name>.py exists (checkall.py auto-runs those).
Usage: untested.py [--repo PATH]    Exit 0 always; prints a count line last.
"""
import glob, os, sys

def main(argv):
    root = "."
    if len(argv) == 3 and argv[1] == "--repo":
        root = argv[2]
    elif len(argv) != 1:
        print("usage: untested.py [--repo PATH]", file=sys.stderr); return 64
    tests = {os.path.basename(t)[5:] for t in glob.glob(os.path.join(root, "agents/*/workshop/test_*.py"))}
    tools = sorted(t for t in glob.glob(os.path.join(root, "agents/*/workshop/*.py"))
                   if not os.path.basename(t).startswith("test_"))
    n = 0
    for t in tools:
        ok = os.path.basename(t) in tests
        n += ok
        print(("TESTED    " if ok else "UNTESTED  ") + os.path.relpath(t, root))
    print(f"{n} of {len(tools)} tools have a test Muster runs")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
