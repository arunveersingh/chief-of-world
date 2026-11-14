#!/usr/bin/env python3
"""capcount.py: how many mutants does a mutcheck cap leave unscored, tool by tool?

Read-only, stdlib only. Run it from the repo root.

  python3 agents/lumen/workshop/capcount.py            # cap 40, the Chief's --all run
  python3 agents/lumen/workshop/capcount.py --max 60   # mutcheck's default cap

Ash's mutcheck.py scores at most --max mutants per tool, taken in file order.
So an `--all` figure says nothing about the mutants past the cap, which sit at
the END of each file (often main(), output and rarely-run branches). This
counts, for every tool mutcheck would score, how many mutants it generates and
how many fall past the cap, and from which line on.

It reuses mutcheck's own SWAPS, code_lines and mutants by reading them out of
agents/ash/workshop/mutcheck.py with ast, without running that file, so if Ash
changes what counts as a mutant this tool follows. Nothing is tested here; it
only counts.
"""
import ast, glob, os, sys

MUTCHECK = "agents/ash/workshop/mutcheck.py"
WANT = {"SWAPS", "code_lines", "mutants"}

def load(path=MUTCHECK):
    tree = ast.parse(open(path, encoding="utf-8").read())
    keep = [n for n in tree.body
            if isinstance(n, ast.Import)
            or (isinstance(n, ast.FunctionDef) and n.name in WANT)
            or (isinstance(n, ast.Assign) and any(getattr(t, "id", None) in WANT for t in n.targets))]
    ns = {}
    exec(compile(ast.Module(body=keep, type_ignores=[]), path, "exec"), ns)
    missing = WANT - set(ns)
    if missing:
        raise SystemExit(f"capcount: {path} no longer defines {', '.join(sorted(missing))}")
    return ns["mutants"]

def count(tool, mutants, cap):
    lines = [n for n, _, _ in mutants(open(tool, encoding="utf-8", errors="replace").read())]
    past = lines[cap:]
    return len(lines), len(past), (past[0] if past else None)

def tools():
    return sorted(t for t in glob.glob("agents/*/workshop/*.py")
                  if not os.path.basename(t).startswith("test_"))

def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    cap = 40
    if args[:1] == ["--max"] and len(args) == 2 and args[1].isdigit():
        cap = int(args[1])
    elif args:
        print("usage: capcount.py [--max N]", file=sys.stderr)
        return 64
    mutants = load()
    total = unscored = hidden = 0
    for t in tools():
        n, past, first = count(t, mutants, cap)
        total += n
        unscored += past
        if past:
            hidden += 1
            print(f"{t}: {n} mutants, {past} past cap {cap} (line {first} on)")
    print(f"{hidden} tool(s) have mutants past cap {cap}: {unscored} of {total} mutants unscored")
    return 0

if __name__ == "__main__":
    sys.exit(main())
