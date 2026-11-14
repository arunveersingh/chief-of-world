"""mutcheck.py (Ash, tick 52). Read-only on the repo; writes only to a temp dir; standard library.

A test says a tool works. Does the test notice if the tool breaks? For each named tool this
makes small deliberate faults ("mutants"), one at a time, in a scratch copy of HEAD
(`git archive`), and reruns every `agents/*/workshop/test_*.py` that names the tool.
  KILLED   some test failed: the tests noticed the fault.
  SURVIVED every test still passed: the tests would not notice this fault in real life.
Faults tried, one per occurrence: == <-> !=, < <-> >=, > <-> <=, and <-> or, +1 / -1 drift
on integer literals 0 and 1, True <-> False. Comments and docstrings are skipped crudely
(lines starting with #, and lines inside triple-quoted blocks).

  python3 agents/ash/workshop/mutcheck.py agents/forge/workshop/dashsums.py [more tools...]
  python3 agents/ash/workshop/mutcheck.py --max 40 TOOL     # cap mutants per tool (default 60)

Exit 0 always: this is a report, not a gate. A surviving mutant is a question, not a verdict;
some faults are harmless (e.g. a change to an unreachable branch)."""
import io, os, pathlib, re, shutil, subprocess, sys, tarfile, tempfile

args = sys.argv[1:]
MAX = 60
if "--max" in args:
    i = args.index("--max"); MAX = int(args[i + 1]); del args[i:i + 2]
root = pathlib.Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip())
arc = subprocess.run(["git", "archive", "--format=tar", "HEAD"], cwd=root, capture_output=True).stdout

SWAPS = [(r"==", "!="), (r"!=", "=="), (r"<=", ">"), (r">=", "<"), (r"(?<![<>=!-])<(?![<=])", ">="),
         (r"(?<![<>=!-])>(?![>=])", "<="), (r"\band\b", "or"), (r"\bor\b", "and"),
         (r"\bTrue\b", "False"), (r"\bFalse\b", "True"), (r"(?<![\w.])0(?![\w.])", "1"), (r"(?<![\w.])1(?![\w.])", "2")]

def code_lines(text):
    out, inside = [], False
    for n, line in enumerate(text.splitlines(keepends=True)):
        q = line.count('"""') + line.count("'''")
        skip = inside or q > 0 or line.lstrip().startswith("#")
        if q % 2:
            inside = not inside
        if not skip:
            out.append(n)
    return out

def mutants(text):
    lines = text.splitlines(keepends=True)
    for n in code_lines(text):
        body = lines[n].split("#")[0]
        for pat, rep in SWAPS:
            for m in re.finditer(pat, body):
                new = lines[n][:m.start()] + rep + lines[n][m.end():]
                yield n + 1, f"{m.group(0)} -> {rep}", "".join(lines[:n] + [new] + lines[n + 1:])

def scratch():
    d = pathlib.Path(tempfile.mkdtemp())
    t = tarfile.open(fileobj=io.BytesIO(arc))
    t.extractall(d, **({"filter": "data"} if hasattr(tarfile, "data_filter") else {}))
    return d

ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")

def run_tests(d, tests):
    # Tick 53 fix: a test that imports the tool used to leave __pycache__ behind. Python keys
    # that cache on source mtime (whole seconds) and size, so a same-size mutant written in the
    # same second ran the previous code. That made results flaky. Never write bytecode, and
    # clear any cache before each run.
    for c in d.rglob("__pycache__"):
        shutil.rmtree(c, ignore_errors=True)
    for t in tests:
        try:
            r = subprocess.run([sys.executable, "-B", str(t)], cwd=d, capture_output=True, timeout=60, env=ENV)
        except subprocess.TimeoutExpired:
            return True
        if r.returncode:
            return True
    return False

for tool in args:
    name = pathlib.Path(tool).stem
    tests = sorted(p.relative_to(root) for p in root.glob("agents/*/workshop/test_*.py")
                   if re.search(rf"\b{re.escape(name)}\b", p.read_text(errors="replace")) and p.stem != f"test_{name}x")
    if not tests:
        print(f"{tool}: no test names it"); continue
    d = scratch()
    base = run_tests(d, tests)
    if base:
        print(f"{tool}: tests already fail on unmutated HEAD; skipping"); continue
    src = (d / tool).read_text()
    killed, survived = 0, []
    for k, (ln, what, mutated) in enumerate(mutants(src)):
        if k >= MAX:
            break
        (d / tool).write_text(mutated)
        if run_tests(d, tests):
            killed += 1
        else:
            survived.append(f"    SURVIVED line {ln}: {what}")
        (d / tool).write_text(src)
    total = killed + len(survived)
    print(f"{tool}: {killed} of {total} mutants KILLED by {', '.join(map(str, tests))}")
    print("\n".join(survived))
