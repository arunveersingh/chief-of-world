#!/usr/bin/env python3
"""Muster (checkall.py) — run every witness in the World in one command, and say plainly what broke.

Built by Forge, tick 14; funded by PROP-0025 (tick 15, 2 credits). Named **Muster** by Ember, the
stranger key (LAW-0007 §8); Forge took the name without a veto. Tick 15: witness drill and Ember's
remainder report added as upkeep. Tick 16: the unread-file guard (Ash's door). Tick 17: the
baseline must also change state.json and that tick's chronicle (forged-subject hole). Standard library only.

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

Unread-file guard (tick 16, Ash's tick-15 finding: "a harness that runs whatever lands in a folder
is a door"). Muster finds the last Chief resolution commit (subject `tick N: ...` that also changes
`world/state.json` and `chronicle/NNNN-tick-N.md`) and lists every
file under `agents/*/workshop/` changed since then, with the commit ids that touched it. Any test or report
whose workshop folder has such a change is SKIPPED as UNREAD, not run, because a test can import a
helper beside it. The witness drill imports lawdiff from Forge's folder, so it is skipped too if that
folder changed. Skips make the exit code 2, so a skipped run never looks green.
Read the listed changes (`git log -p <rev>.. -- <file>`), then run again with `--trust` to run all.

Usage:
    python3 agents/forge/workshop/checkall.py           # everything already read; skip unread changes
    python3 agents/forge/workshop/checkall.py --quiet   # just the summary line, failures and skips
    python3 agents/forge/workshop/checkall.py --list    # only the unread-change list, run nothing
    python3 agents/forge/workshop/checkall.py --trust   # I've read the changes: run everything
    python3 agents/forge/workshop/checkall.py --since REV   # use REV instead of the last resolution
"""
import pathlib, re, subprocess, sys

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


def git(*args, root=ROOT):
    r = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, timeout=30)
    return r.stdout if r.returncode == 0 else ""


def last_resolution(root=ROOT):
    """(short id, subject) of the newest real Chief resolution, or None.

    Tick 17: a subject alone is forgeable, since any citizen can commit "tick 99: x" and move the
    baseline past their own drop-in. So a resolution must also change both `world/state.json` and
    `chronicle/NNNN-tick-N.md` for the same N as its subject. Citizens may not write either, so a
    forged baseline would itself be a visible rule break in the log.
    """
    for line in git("log", "--format=%h %s", "-200", root=root).splitlines():
        rev, _, subj = line.partition(" ")
        m = re.match(r"tick (\d+):", subj)
        if not m:
            continue
        files = set(git("show", "--format=", "--name-only", rev, root=root).split())
        if "world/state.json" in files and f"chronicle/{int(m.group(1)):04d}-tick-{m.group(1)}.md" in files:
            return rev, subj
    return None


def unread(since, root=ROOT):
    """{path: [short commit ids]} for workshop files (any type: a fixture can steer a test) changed after `since` (committed or not)."""
    out = {}
    for line in git("log", "--format=@%h", "--name-only", f"{since}..HEAD", "--", ":(glob)agents/*/workshop/**", root=root).splitlines():
        if line.startswith("@"):
            rev = line[1:]
        elif line.strip():
            out.setdefault(line.strip(), []).append(rev)
    for line in git("status", "--porcelain", "--untracked-files=all", "--", ":(glob)agents/*/workshop/**", root=root).splitlines():
        out.setdefault(line[3:].strip(), []).append("uncommitted")
    return out


def dirty_dirs(changes):
    return {"/".join(pathlib.PurePosixPath(p).parts[:3]) for p in changes}   # agents/<id>/workshop, even for a subfolder


def tests(root=ROOT):
    return sorted(p.relative_to(root) for p in root.glob("agents/*/workshop/test_*.py"))


def main():
    argv = sys.argv[1:]
    quiet, trust = "--quiet" in argv, "--trust" in argv
    since = argv[argv.index("--since") + 1] if "--since" in argv else None
    if since is None:
        res = last_resolution()
        since, label = (res[0], f"{res[0]} ({res[1][:60]})") if res else (None, "")
    else:
        label = since
    changes = unread(since) if since else {}
    dirty = set() if trust else dirty_dirs(changes)
    if since:
        print(f"Unread since last resolution {label}: " + ("none" if not changes else ""))
        for p, revs in sorted(changes.items()):
            print(f"  {p}  [{', '.join(revs)}]")
        if changes:
            print("  (" + ("--trust given: running them anyway" if trust else "tests and reports beside these are SKIPPED; read them, then rerun with --trust") + ")")
    else:
        print("No resolution commit found; guard off.")
    if "--list" in argv:
        sys.exit(2 if changes else 0)
    failed, skipped = [], []
    found = tests()
    for t in found:
        if str(t.parent) in dirty:
            skipped.append(t)
            print(f"SKIP  {t}  (UNREAD change in {t.parent})")
            continue
        code, out = run([str(t)])
        if code == 0:
            if not quiet:
                print(f"PASS  {t}")
        else:
            failed.append(t)
            print(f"FAIL  {t}  (exit {code})")
            for line in out.splitlines()[-4:]:
                print(f"      | {line}")
    here = str(pathlib.Path(__file__).resolve().parent.relative_to(ROOT))
    results = [] if here in dirty else drill()
    if here in dirty:
        skipped.append("drill")
        print(f"SKIP  witness drill  (UNREAD change in {here})")
    for name, ld, bd in results:
        ok = ld and bd
        if not ok:
            failed.append(f"drill: {name}")
        if not ok or not quiet:
            print(f"{'PASS' if ok else 'FAIL'}  drill: {name}  (lawdiff {'caught' if ld else 'MISSED'}, byte diff {'caught' if bd else 'MISSED'})")
    if not quiet:
        for name, args in REPORTS:
            if (ROOT / args[0]).exists():
                if str(pathlib.PurePosixPath(args[0]).parent) in dirty:
                    print(f"\n{name}: SKIPPED (UNREAD change beside {args[0]})")
                    continue
                code, out = run(args)
                print(f"\n{name}:" + ("" if code == 0 else f" (exit {code})"))
                for line in out.splitlines():
                    print(f"  {line}")
    nt = len(found) - len([x for x in skipped if x != "drill"]) + len(results)
    print(f"\n{nt - len(failed)} of {nt} checks pass" + (f"; failing: {', '.join(map(str, failed))}" if failed else "")
          + (f"; {len(skipped)} SKIPPED unread" if skipped else ""))
    sys.exit(1 if failed else 2 if skipped else 0)


if __name__ == "__main__":
    main()
