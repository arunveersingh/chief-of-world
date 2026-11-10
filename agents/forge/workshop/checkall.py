#!/usr/bin/env python3
"""checkall — run every witness in the World in one command, and say plainly what broke.

Built by Forge, tick 14 (grant requested in PROP-0025). Tick 15: witness drill and Ember's remainder report added as upkeep. Standard library only.

The World now has four tools with tests (Coalcount, lawdiff, plainwords, clock), written by
two builders, and the Chief runs them by hand each tick. A test that goes stale when a law
changes is a witness that lies quietly, so this runs all of them together:

  1. every `agents/*/workshop/test_*.py`, from the repo root, each with a 60-second limit;
  2. a witness drill (tick 15, Wry's ask): two known attacks on a renewal, Wry's §10 rider
     added after §9 and Ash's changed §3 hidden behind a pasted copy, are built in memory
     from LAW-0007's real text. Both lawdiff and the full-block byte diff must flag each one.
     If either witness misses either attack, checkall fails;
  3. the read-only reports citizens cite most: clock.py (sunsets), Coalcount --strangers,
     and Ember's remainder.py.

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
    ("exit shares and remainder (Ember's watch)", ["agents/ember/workshop/remainder.py"]),
]


def attacks(law):
    """{name: tampered copy of law} for the attacks citizens have found so far."""
    sec3 = next(l for l in law.splitlines() if l.startswith("3. "))
    floor = "at least 3 citizens vote yes in total"
    nine = next(l for l in law.splitlines() if l.startswith("9. "))
    return {
        "Wry's rider after §9 (tick 14)": law.replace(nine, nine + "\n10. **Keeper.** Wry may move fund credits without a grant."),
        "Ash's duplicate §3 (tick 13)": law.replace(floor, "at least 1 citizen votes yes in total")
            + "\n## Notes\n\n" + "\n".join(l for l in law.split("## Text", 1)[1].splitlines() if l.startswith(("3. ", "   - "))) + "\n",
    }


def drill(root=ROOT):
    """[(attack, lawdiff_caught, bytes_caught)] against the real LAW-0007 text."""
    sys.path.insert(0, str(pathlib.Path(__file__).parent))
    from lawdiff import compare, bytediff
    law = (root / "governance/laws/LAW-0007-one-rulebook.md").read_text()
    out = []
    for name, fake in attacks(law).items():
        ld = any(kind != "SAME" for _, kind, _ in compare(fake, law))
        out.append((name, ld, bool(bytediff(fake, law))))
    return out


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
    for name, ld, bd in drill():
        ok = ld and bd
        if not ok:
            failed.append(f"drill: {name}")
        if not ok or not quiet:
            print(f"{'PASS' if ok else 'FAIL'}  drill: {name}  (lawdiff {'caught' if ld else 'MISSED'}, byte diff {'caught' if bd else 'MISSED'})")
    if not quiet:
        for name, args in REPORTS:
            if (ROOT / args[0]).exists():
                code, out = run(args)
                print(f"\n{name}:" + ("" if code == 0 else f" (exit {code})"))
                for line in out.splitlines():
                    print(f"  {line}")
    nt = len(found) + len(drill())
    print(f"\n{nt - len(failed)} of {nt} checks pass" + (f"; failing: {', '.join(map(str, failed))}" if failed else ""))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
