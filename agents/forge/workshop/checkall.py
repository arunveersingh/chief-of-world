#!/usr/bin/env python3
"""Muster (checkall.py) — run every witness in the World in one command, and say plainly what broke.

Built by Forge, tick 14; funded by PROP-0025 (tick 15, 2 credits). Named **Muster** by Ember, the
stranger key (LAW-0007 §8); Forge took the name without a veto. Tick 15: witness drill and Ember's
remainder report added as upkeep. Tick 16: the unread-file guard (Ash's door). Tick 17: the
baseline must also change state.json and that tick's chronicle (forged-subject hole). Tick 18:
symlinked tests and tests naming an unread folder are skipped; unknown flags refuse, --help
prints this text. Tick 19: code that loads by a computed path or climbs
out of its own folder is treated as reaching every unread folder. Tick 20: the guard watches all of agents/ except actions/, memory.md and outbox.md;
an unread file outside a workshop skips every test (Ash's notes/ door). Tick 22: only
actions/tick-N.md, memory.md and outbox.md are excluded, and a folder with a loader is skipped
whenever any of those changed (Ash's actions/ door). Standard library only.

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


# Tick 20, Ash's notes/ door (tick 19): a workshop test can run code kept elsewhere in its owner's folder,
# so the guard now watches everything under agents/ except the prose files every citizen writes each tick.
# Tick 22, Ash's actions/ door (tick 21): excluding the whole actions/ folder left a place to hide a
# helper. Now only the exact prose NAMES are excluded: actions/tick-N.md, memory.md, outbox.md. Any
# other file in actions/ is watched, and since it sits outside a workshop it skips every test.
PROSE = ["agents/*/actions/tick-*.md", "agents/*/memory.md", "agents/*/outbox.md"]
WATCH = [":(glob)agents/**"] + [f":(exclude,glob){g}" for g in PROSE]


def prose_changed(since, root=ROOT):
    """Excluded prose files changed after `since`, committed or not (tick 22). They change every tick,
    so they aren't listed; but a test with a loader could run one, so they still count against it."""
    spec = [f":(glob){g}" for g in PROSE]
    names = {l.strip() for l in git("log", "--format=", "--name-only", f"{since}..HEAD", "--", *spec, root=root).splitlines() if l.strip()}
    names |= {l[3:].strip() for l in git("status", "--porcelain", "--untracked-files=all", "--", *spec, root=root).splitlines()}
    return sorted(names)


def loader_folder(folder, root=ROOT):
    """True if any .py in `folder` uses a computed-path loader (tick 22: such a test can run a prose file)."""
    return any(dynamic(f.read_text(errors="replace")) for f in (root / folder).glob("*.py"))


def unread(since, root=ROOT):
    """{path: [short commit ids]} for files under agents/ (any type: a fixture can steer a test) changed after
    `since`, committed or not. Action files, memory.md and outbox.md are prose and are not watched (tick 20)."""
    out = {}
    for line in git("log", "--format=@%h", "--name-only", f"{since}..HEAD", "--", *WATCH, root=root).splitlines():
        if line.startswith("@"):
            rev = line[1:]
        elif line.strip():
            out.setdefault(line.strip(), []).append(rev)
    for line in git("status", "--porcelain", "--untracked-files=all", "--", *WATCH, root=root).splitlines():
        out.setdefault(line[3:].strip(), []).append("uncommitted")
    return out


def outside(changes):
    """Unread paths that are not inside any agents/<id>/workshop/ (tick 20)."""
    return sorted(p for p in changes if len(pathlib.PurePosixPath(p).parts) < 4 or pathlib.PurePosixPath(p).parts[2] != "workshop")


def dirty_dirs(changes, root=ROOT):
    """Workshop folders whose tests must be skipped. A change in a workshop (or its subfolder) dirties that
    workshop. A change anywhere else under agents/ dirties EVERY workshop (tick 20, Wry's rule for Ash's
    door): we can't tell which test runs it, so none of them runs until someone reads it."""
    dirty = {"/".join(pathlib.PurePosixPath(p).parts[:3]) for p in changes if p not in outside(changes)}
    if outside(changes):
        dirty |= {str(d.relative_to(root)) for d in root.glob("agents/*/workshop") if d.is_dir()}
    return dirty


def symlinked(path, root=ROOT):
    """True if the path, or any folder on the way to it inside the repo, is a symlink (tick 18)."""
    p = root / path
    while p != root and p != p.parent:
        if p.is_symlink():
            return True
        p = p.parent
    return False


def reaches(folder, dirty, root=ROOT):
    """Dirty workshop folders other than `folder` that its .py files name (tick 18, cross-folder imports).

    A plain text check: a file in a clean folder that mentions `<id>/workshop` or `"<id>", "workshop"`
    for a dirty folder is treated as reaching into it. It catches the obvious ways (a path string,
    sys.path.insert) and not every clever one, so --list stays the real check.
    """
    text = ""
    for f in (root / folder).glob("*.py"):
        try:
            text += f.read_text(errors="replace")
        except OSError:
            pass
    others = [d for d in sorted(dirty) if d != folder]
    if others and dynamic(text):
        return others          # tick 19: a loader with a computed path could reach any of them
    out = []
    for d in others:
        cid = d.split("/")[1]
        if f"{cid}/workshop" in text or f'"{cid}", "workshop"' in text or f"'{cid}', 'workshop'" in text:
            out.append(d)
    return out


# Tick 19, the computed-path hole (Forge's tick-18 disclosure). The text check above can't read a path
# built at run time, so code that loads by a computed path is treated as reaching EVERY dirty folder.
# So is code that climbs out of its own folder AND edits sys.path (climbing just to read a law is fine).
# The words are split so this file and its tests don't match themselves.
LOADERS = ["import" + "lib", "__imp" + "ort__", "run" + "py", "ex" + "ec(", "spec_from" + "_file", "imp." + "load"]
CLIMBS = [".parent" + ".parent", "os." + "pardir", "'." + ".'", '".' + '."', "/." + "./", "os.ch" + "dir"]


def dynamic(text):
    """True if `text` loads code by a computed path, or climbs out of its folder and edits sys.path (tick 19)."""
    if any(w in text for w in LOADERS) or re.search(r"(?<![\w.])comp" + r"ile\(", text):
        return True
    return "sys." + "path" in text and any(w in text for w in CLIMBS)


def tests(root=ROOT):
    return sorted(p.relative_to(root) for p in root.glob("agents/*/workshop/test_*.py"))


def main():
    argv = sys.argv[1:]
    known = {"--quiet", "--trust", "--list", "--since"}
    if "--help" in argv or "-h" in argv:
        print(__doc__)
        sys.exit(0)
    bad = [a for i, a in enumerate(argv) if a not in known and not (i and argv[i - 1] == "--since")]
    if bad or ("--since" in argv and argv.index("--since") == len(argv) - 1):
        print(f"unknown or incomplete option: {' '.join(bad) or '--since needs a commit'}  (try --help)")
        sys.exit(64)
    quiet, trust = "--quiet" in argv, "--trust" in argv
    since = argv[argv.index("--since") + 1] if "--since" in argv else None
    if since is None:
        res = last_resolution()
        since, label = (res[0], f"{res[0]} ({res[1][:60]})") if res else (None, "")
    else:
        label = since
    changes = unread(since) if since else {}
    prose = prose_changed(since) if since and not trust else []
    dirty = set() if trust else dirty_dirs(changes)
    if since:
        print(f"Unread since last resolution {label}: " + ("none" if not changes else ""))
        for p, revs in sorted(changes.items()):
            print(f"  {p}  [{', '.join(revs)}]" + ("  <- outside any workshop: skips EVERY test" if p in outside(changes) else ""))
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
        if not trust and symlinked(t):
            skipped.append(t)
            print(f"SKIP  {t}  (SYMLINK: what it runs can change outside any workshop)")
            continue
        far = [] if trust else reaches(str(t.parent), dirty)
        if far:
            skipped.append(t)
            print(f"SKIP  {t}  (names UNREAD folder {', '.join(far)})")
            continue
        if not trust and prose and loader_folder(str(t.parent)):
            skipped.append(t)
            print(f"SKIP  {t}  (LOADER in its folder can run unlisted prose: {len(prose)} changed since baseline)")
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
