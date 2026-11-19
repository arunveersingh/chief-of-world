"""breakit.py (Ash, tick 63; tick 66 fixes from Wry's break-it log): do your tests notice when your code breaks? One file, standard library, no network.

It copies your project to a temp folder, makes one small fault at a time in ONE Python file
(== to !=, < to >=, and to or, True to False, 0 to 1, 1 to 2, ...), runs YOUR test command on
the copy, and tells you which faults your tests did not notice. Your own files are never changed.

  python3 breakit.py src/prices.py -- python3 -m pytest -q
  python3 breakit.py prices.py --dir . --max 100 --timeout 30 -- python3 -m unittest

  --dir DIR      the project folder to copy and run the command in (default: current folder)
  --max N        try at most N faults (default 200)
  --timeout S    seconds before one test run counts as stuck (default 60)

Options may go before or after the file. Before any fault, it runs your command once on the
untouched copy. If that fails or gets stuck, it stops and says so: a fault can't be judged against
tests that already fail. Then it makes the copy crash the moment it loads. If your tests still
pass, they never ran the copy (they load an installed or absolute-path version), so it stops
rather than score them.
  CAUGHT   the command failed (nonzero exit) with the fault in: your tests noticed.
  MISSED   the command still passed: nothing checks that line that way.
  STUCK    the command ran past --timeout with the fault in. Counted as caught, and listed,
           because a fault that hangs your code is noticed, but you may want a real test for it.
A MISSED fault is a question, not a verdict: some faults change nothing (an unreachable branch,
an equivalent bound). String literals and comments are never changed. Exit code: 0 always,
except 2 for bad usage, 3 when the untouched tests fail or get stuck, and 4 when the tests
never ran the copy."""
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

def usage(msg):
    print(f"breakit: {msg}\n  usage: python3 breakit.py FILE.py [--dir DIR] [--max N] [--timeout S] -- TEST COMMAND\n  (python3 breakit.py --help for more)")
    return 2

def main(argv):
    if not argv or argv[0] in ("-h", "--help") or "--" not in argv:
        print(__doc__); return 2
    i = argv.index("--"); opts, cmd = argv[:i], argv[i + 1:]
    conf = {"--dir": ".", "--max": "200", "--timeout": "60"}
    files = []
    while opts:  # options may come before or after the file
        if opts[0] in conf:
            if len(opts) < 2:
                return usage(f"{opts[0]} needs a value")
            conf[opts[0]] = opts[1]; opts = opts[2:]
        elif opts[0].startswith("--"):
            return usage(f"unknown option {opts[0]}")
        else:
            files.append(opts.pop(0))
    if len(files) != 1:
        return usage("expected exactly one Python file before --, got " + (", ".join(files) or "none"))
    if not cmd:
        return usage("no test command after --")
    try:
        mx, to = int(conf["--max"]), float(conf["--timeout"])
    except ValueError:
        return usage("--max needs a whole number and --timeout a number of seconds")
    src = pathlib.Path(conf["--dir"]).resolve()
    target = (pathlib.Path(files[0]) if pathlib.Path(files[0]).is_absolute() else pathlib.Path.cwd() / files[0]).resolve()
    if not src.is_dir():
        return usage(f"--dir {conf['--dir']} is not a folder")
    if not target.is_file():
        return usage(f"no such file: {files[0]}")
    try:
        rel = target.relative_to(src)
    except ValueError:
        return usage(f"{files[0]} is not inside the project folder {src} (set --dir)")
    try:
        text = target.read_text()
    except (OSError, UnicodeDecodeError) as e:
        return usage(f"can't read {files[0]}: {e}")
    tmp = pathlib.Path(tempfile.mkdtemp()); d = tmp / "p"
    try:
        shutil.copytree(src, d, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        base = run(cmd, d, to)
        if base != "pass":
            print(f"STOP: your tests {'fail' if base == 'fail' else 'got stuck'} before any fault is made. Fix that first.")
            return 3
        # Canary: make the copied file crash the moment it loads. Tests that still pass never loaded it.
        (d / rel).write_text('raise SystemExit("breakit canary")\n' + text)
        if run(cmd, d, to) == "pass":
            print(f"STOP: your tests still passed when the copy of {rel} was made to crash on load, so they never ran it.\n"
                  "  They probably load your original file instead (an installed package, pip install -e, PYTHONPATH,\n"
                  "  or an absolute path in a test or conftest.py). Make them import from the project folder. Nothing was scored.")
            return 4
        (d / rel).write_text(text)
        missed, stuck, total = [], [], 0
        for n, change, new in faults(text):
            if total >= mx:
                break
            total += 1
            (d / rel).write_text(new)
            res = run(cmd, d, to)
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
