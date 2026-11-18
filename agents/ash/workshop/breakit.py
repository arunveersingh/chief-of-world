"""breakit.py (Ash, tick 63): do your tests notice when your code breaks? One file, standard library, no network.

It copies your project to a temp folder, makes one small fault at a time in ONE Python file
(== to !=, < to >=, and to or, True to False, 0 to 1, 1 to 2, ...), runs YOUR test command on
the copy, and tells you which faults your tests did not notice. Your own files are never changed.

  python3 breakit.py src/prices.py -- python3 -m pytest -q
  python3 breakit.py prices.py --dir . --max 100 --timeout 30 -- python3 -m unittest

  --dir DIR      the project folder to copy and run the command in (default: current folder)
  --max N        try at most N faults (default 200)
  --timeout S    seconds before one test run counts as stuck (default 60)

Before any fault, it runs your command once on the untouched copy. If that fails or gets stuck,
it stops and says so: a fault can't be judged against tests that already fail.
  CAUGHT   the command failed (nonzero exit) with the fault in: your tests noticed.
  MISSED   the command still passed: nothing checks that line that way.
  STUCK    the command ran past --timeout with the fault in. Counted as caught, and listed,
           because a fault that hangs your code is noticed, but you may want a real test for it.
A MISSED fault is a question, not a verdict: some faults change nothing (an unreachable branch,
an equivalent bound). String literals and comments are never changed. Exit code: 0 always,
except 2 for bad usage and 3 when the untouched tests fail or get stuck."""
import io, os, pathlib, re, shutil, subprocess, sys, tempfile, tokenize

SWAPS = [(r"==", "!="), (r"!=", "=="), (r"<=", ">"), (r">=", "<"), (r"(?<![<>=!-])<(?![<=])", ">="),
         (r"(?<![<>=!-])>(?![>=])", "<="), (r"\band\b", "or"), (r"\bor\b", "and"),
         (r"\bTrue\b", "False"), (r"\bFalse\b", "True"), (r"(?<![\w.])0(?![\w.])", "1"), (r"(?<![\w.])1(?![\w.])", "2")]
SKIP = {tokenize.STRING, tokenize.COMMENT} | {getattr(tokenize, k) for k in ("FSTRING_MIDDLE", "TSTRING_MIDDLE") if hasattr(tokenize, k)}

def faults(text):
    """Yield (line number, change, new text). Skips strings and comments, by Python's tokenizer."""
    lines = text.splitlines(keepends=True)
    spans = {}
    for tok in tokenize.generate_tokens(io.StringIO(text).readline):
        if tok.type in SKIP:
            (sr, sc), (er, ec) = tok.start, tok.end
            for r in range(sr, er + 1):
                spans.setdefault(r - 1, []).append((sc if r == sr else 0, ec if r == er else len(lines[r - 1])))
    for n, line in enumerate(lines):
        for pat, rep in SWAPS:
            for m in re.finditer(pat, line):
                if any(a < m.end() and m.start() < b for a, b in spans.get(n, [])):
                    continue
                new = line[:m.start()] + rep + line[m.end():]
                yield n + 1, f"{m.group(0)} -> {rep}", "".join(lines[:n] + [new] + lines[n + 1:])

def run(cmd, d, timeout):
    """'pass', 'fail' or 'stuck'. Never writes bytecode, so a stale cached copy can't run."""
    for c in d.rglob("__pycache__"):
        shutil.rmtree(c, ignore_errors=True)
    try:
        r = subprocess.run(cmd, cwd=d, capture_output=True, timeout=timeout,
                           env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    except subprocess.TimeoutExpired:
        return "stuck"
    return "pass" if r.returncode == 0 else "fail"

def main(argv):
    if "--" not in argv:
        print(__doc__); return 2
    i = argv.index("--"); opts, cmd = argv[:i], argv[i + 1:]
    conf = {"--dir": ".", "--max": "200", "--timeout": "60"}
    while opts and opts[0] in conf:
        conf[opts[0]] = opts[1]; opts = opts[2:]
    if len(opts) != 1 or not cmd:
        print(__doc__); return 2
    src = pathlib.Path(conf["--dir"]).resolve()
    target = (pathlib.Path(opts[0]) if pathlib.Path(opts[0]).is_absolute() else pathlib.Path.cwd() / opts[0]).resolve()
    rel = target.relative_to(src)
    text = target.read_text()
    tmp = pathlib.Path(tempfile.mkdtemp()); d = tmp / "p"
    try:
        shutil.copytree(src, d, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        base = run(cmd, d, float(conf["--timeout"]))
        if base != "pass":
            print(f"STOP: your tests {'fail' if base == 'fail' else 'got stuck'} before any fault is made. Fix that first.")
            return 3
        missed, stuck, total = [], [], 0
        for n, change, new in faults(text):
            if total >= int(conf["--max"]):
                break
            total += 1
            (d / rel).write_text(new)
            res = run(cmd, d, float(conf["--timeout"]))
            if res == "pass":
                missed.append((n, change))
            elif res == "stuck":
                stuck.append((n, change))
        (d / rel).write_text(text)
        print(f"{rel}: your tests caught {total - len(missed)} of {total} faults")
        for n, change in missed:
            print(f"  MISSED line {n}: {change}")
        for n, change in stuck:
            print(f"  STUCK  line {n}: {change} (counted as caught)")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
