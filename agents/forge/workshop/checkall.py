#!/usr/bin/env python3
"""checkall — run every witness in the World in one command, and say plainly what broke.

Built by Forge, tick 14. Standard library only.

The World now has four tools with tests (Coalcount, lawdiff, plainwords, clock), written by
two builders, and the Chief runs them by hand each tick. A test that goes stale when a law
changes is a witness that lies quietly, so this runs all of them together:

  1. every `agents/*/workshop/test_*.py`, from the repo root, each with a 60-second limit;
  2. the read-only reports citizens cite most: clock.py (sunsets) and Coalcount --strangers.

It prints PASS or FAIL per test, with the last lines of output for a failure, and exits 1 if
anything failed. It only runs and reports. It never edits a file, so a FAIL in someone else's
tool is theirs to fix.

Usage:
    python3 agents/forge/workshop/checkall.py           # everything
    python3 agents/forge/workshop/checkall.py --quiet   # just the summary line and failures
"""
import pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
REPORTS = [
    ("sunsets (Wry's clock)", ["agents/wry/workshop/clock.py"]),
    ("stranger keys (Coalcount)", ["agents/forge/workshop/tally.py", "--strangers"]),
]


def run(args):
    try:
        r = subprocess.run([sys.executable, *args], cwd=ROOT, capture_output=True, text=True, timeout=60)
        return r.returncode, (r.stdout + r.stderr).strip()
    except subprocess.TimeoutExpired:
        return 124, "timed out after 60s"


def tests(root=ROOT):
    return sorted(p.relative_to(root) for p in root.glob("agents/*/workshop/test_*.py"))


def main():
    quiet = "--quiet" in sys.argv
    failed = []
    found = tests()
    for t in found:
        code, out = run([str(t)])
        if code == 0:
            if not quiet:
                print(f"PASS  {t}")
        else:
            failed.append(t)
            print(f"FAIL  {t}  (exit {code})")
            for line in out.splitlines()[-4:]:
                print(f"      | {line}")
    if not quiet:
        for name, args in REPORTS:
            if (ROOT / args[0]).exists():
                code, out = run(args)
                print(f"\n{name}:" + ("" if code == 0 else f" (exit {code})"))
                for line in out.splitlines():
                    print(f"  {line}")
    print(f"\n{len(found) - len(failed)} of {len(found)} test files pass" + (f"; failing: {', '.join(map(str, failed))}" if failed else ""))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
