"""breakit.py (Ash, tick 63; tick 66-68 fixes from Wry's break-it logs; tick 69 --repeat; tick 70 --lines; tick 71 sums): do your tests notice when your code breaks? One file, standard library, no network.

It copies your project to a temp folder, makes one small fault at a time in ONE Python file
(== to !=, < to >=, and to or, True to False, 0 to 1, 1 to 2, + to -, * to /, ...), runs YOUR test command on
the copy, and tells you which faults your tests did not notice. Your own files are never changed.

  python3 breakit.py src/prices.py -- python3 -m pytest -q
  python3 breakit.py prices.py --dir . --max 100 --timeout 30 -- python3 -m unittest

  --dir DIR      the project folder to copy and run the command in (default: current folder)
  --max N        try at most N faults (default 200)
  --timeout S    seconds before one test run counts as stuck (default 60)
  --repeat N     run the untouched tests N times before any fault (default 3, at least 1)
  --lines A-B    only make faults on lines A to B (e.g. 40-80), to check one function in a big file

Options may go before or after the file. Before any fault, it runs your command once on the
untouched copy. If that fails or gets stuck, it stops and says so: a fault can't be judged against
tests that already fail. It runs them --repeat times in all: if they don't pass every time, they are
flaky, so it stops before spending a run on any fault. Then it makes the copy crash the moment it loads. If your tests still
pass, they never ran the copy (they load an installed or absolute-path version), so it stops
rather than score them.
  CAUGHT   the command failed (nonzero exit) with the fault in: your tests noticed.
  MISSED   the command still passed: nothing checks that line that way.
  FLAKY    the command failed once with the fault in but passed when rerun: not counted as caught.
           Every catch is run twice, so a test that fails at random can't earn one.
  STUCK    the command ran past --timeout with the fault in. Counted as caught, and listed,
           because a fault that hangs your code is noticed, but you may want a real test for it.
If --max stops the run early, the report says how many faults were left untried and from which
line, so a partial score is never read as the whole file.
A MISSED fault is a question, not a verdict: some faults change nothing (an unreachable branch,
an equivalent bound). String literals and comments are never changed. Exit code: 0 always,
except 2 for bad usage, 3 when the untouched tests fail, find no tests or get stuck, 4 when the
tests never ran the copy, and 5 when the tests are flaky (the untouched copy fails on a repeat run,
before the faults or at the end, or a fault is FLAKY), so the score can't be trusted. Every STOP shows your command's last lines."""
import io, os, pathlib, re, shutil, subprocess, sys, tempfile, tokenize

SWAPS = [(r"==", "!="), (r"!=", "=="), (r"<=", ">"), (r">=", "<"), (r"(?<![<>=!-])<(?![<=])", ">="),
         (r"(?<![<>=!-])>(?![>=])", "<="), (r"\band\b", "or"), (r"\bor\b", "and"),
         (r"\bTrue\b", "False"), (r"\bFalse\b", "True"), (r"(?<![\w.])0(?![\w.])", "1"), (r"(?<![\w.])1(?![\w.])", "2")]
SUMS = {"+": "-", "-": "+", "*": "/", "/": "*"}  # arithmetic, found as operator tokens: never inside ->, **, += or //
SKIP = {tokenize.STRING, tokenize.COMMENT} | {getattr(tokenize, k) for k in ("FSTRING_MIDDLE", "TSTRING_MIDDLE") if hasattr(tokenize, k)}

def faults(text):
    """Yield (line number, change, new text). Skips strings and comments, by Python's tokenizer."""
    lines = text.splitlines(keepends=True)
    spans, ops = {}, {}
    for tok in tokenize.generate_tokens(io.StringIO(text).readline):
        if tok.type == tokenize.OP and tok.string in SUMS:
            ops.setdefault(tok.start[0] - 1, []).append(tok.start[1])
        if tok.type in SKIP:
            (sr, sc), (er, ec) = tok.start, tok.end
            for r in range(sr, er + 1):
                spans.setdefault(r - 1, []).append((sc if r == sr else 0, ec if r == er else len(lines[r - 1])))
    for n, line in enumerate(lines):
        found = []
        for pat, rep in SWAPS:
            for m in re.finditer(pat, line):
                if not any(a < m.end() and m.start() < b for a, b in spans.get(n, [])):
                    found.append((m.start(), m.end(), m.group(0), rep))
        found += [(c, c + 1, line[c], SUMS[line[c]]) for c in ops.get(n, [])]
        for start, end, old, rep in found:
            new = "".join(lines[:n] + [line[:start] + rep + line[end:]] + lines[n + 1:])
            try:  # a fault that isn't valid Python (f(*args) to f(/args)) would fail every test: skip it, don't score it
                compile(new, "breakit", "exec")
            except (SyntaxError, ValueError):
                continue
            yield n + 1, f"{old} -> {rep}", new

def run(cmd, d, timeout, tail=False):
    """'pass', 'fail', 'none' (exit 5: no tests ran) or 'stuck'; with tail=True, also the output's last lines.
    Never writes bytecode, so a stale cached copy can't run."""
    for c in d.rglob("__pycache__"):
        shutil.rmtree(c, ignore_errors=True)
    try:
        r = subprocess.run(cmd, cwd=d, capture_output=True, timeout=timeout,
                           env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
        res = "pass" if r.returncode == 0 else "none" if r.returncode == 5 else "fail"
        out = (r.stdout + r.stderr).decode(errors="replace")
    except subprocess.TimeoutExpired:
        res, out = "stuck", ""
    if not tail:
        return res
    return res, [ln for ln in out.splitlines() if ln.strip()][-6:]

def show(lines):
    if lines:
        print("  Last lines your command printed:")
        for ln in lines:
            print("  | " + ln[:200])

def usage(msg):
    print(f"breakit: {msg}\n  usage: python3 breakit.py FILE.py [--dir DIR] [--max N] [--timeout S] [--repeat N] [--lines A-B] -- TEST COMMAND\n  (python3 breakit.py --help for more)")
    return 2

def main(argv):
    if not argv or argv[0] in ("-h", "--help") or "--" not in argv:
        print(__doc__); return 2
    i = argv.index("--"); opts, cmd = argv[:i], argv[i + 1:]
    conf = {"--dir": ".", "--max": "200", "--timeout": "60", "--repeat": "3", "--lines": ""}
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
        mx, rep = int(conf["--max"]), int(conf["--repeat"])
    except ValueError:
        return usage(f"{'--max' if not conf['--max'].lstrip('-').isdigit() else '--repeat'} needs a whole number")
    try:
        to = float(conf["--timeout"])
    except ValueError:
        return usage("--timeout needs a number of seconds")
    if rep < 1:
        return usage("--repeat needs at least 1")
    lo, hi = 1, None
    if conf["--lines"]:
        m = re.fullmatch(r"\s*(\d+)\s*-\s*(\d+)\s*", conf["--lines"])
        if not m or not 1 <= int(m.group(1)) <= int(m.group(2)):
            return usage(f"--lines needs two line numbers like 40-80, first not after second, got {conf['--lines']}")
        lo, hi = int(m.group(1)), int(m.group(2))
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
        base, out = run(cmd, d, to, tail=True)
        if base == "none":
            print("STOP: your test command ran no tests (exit code 5), before any fault was made. Check that it finds\n"
                  "  your tests: unittest looks for test*.py files, and pytest looks for test_*.py and *_test.py.")
            show(out); return 3
        if base != "pass":
            print(f"STOP: your tests {'fail' if base == 'fail' else 'got stuck'} before any fault is made. Fix that first.")
            show(out); return 3
        for k in range(2, rep + 1):  # the same untouched tests, again: a flaky suite stops here, cheaply
            again, out = run(cmd, d, to, tail=True)
            if again != "pass":
                print(f"STOP: your tests passed on run 1 but {'failed' if again == 'fail' else 'got stuck' if again == 'stuck' else 'found no tests'} on run {k}, "
                      "with no fault made. They are flaky,\n  so any score would be partly luck. Fix the flaky test first. Nothing was scored.")
                show(out); return 5
        # Canary: make the copied file crash the moment it loads. Tests that still pass never loaded it.
        (d / rel).write_text('raise SystemExit("breakit canary")\n' + text)
        res, out = run(cmd, d, to, tail=True)
        if res in ("pass", "none"):
            print(f"STOP: your tests still passed when the copy of {rel} was made to crash on load, so they never ran it.\n"
                  "  Usually they load your original file instead (an installed package, pip install -e, PYTHONPATH,\n"
                  "  or an absolute path in a test or conftest.py), or they catch the import error and skip every test\n"
                  "  (a bare except: around the import). Make them import the file from the project folder. Nothing was scored.")
            show(out); return 4
        (d / rel).write_text(text)
        missed, stuck, flaky, total = [], [], [], 0
        todo = [f for f in faults(text) if lo <= f[0] <= (hi or f[0])]
        if not todo:
            print(f"breakit: no faults to make in {rel}" + (f" on lines {lo}-{hi}" if hi else "") + ". Nothing was scored.")
            return 0
        left = todo[mx:]
        for n, change, new in todo[:mx]:
            total += 1
            (d / rel).write_text(new)
            res = run(cmd, d, to)
            if res in ("pass", "none"):
                missed.append((n, change))
            elif res == "stuck":
                stuck.append((n, change))
            elif run(cmd, d, to) in ("pass", "none"):  # a catch must fail twice, or it may be a flaky test
                flaky.append((n, change))
        (d / rel).write_text(text)
        end, out = run(cmd, d, to, tail=True)
        caught = total - len(missed) - len(flaky)
        where = f" on lines {lo}-{hi}" if hi else ""
        print(f"{rel}: your tests caught {caught} of {total} faults{where}")
        if left:
            print(f"  NOT TRIED: {len(left)} more fault{'s' if len(left) != 1 else ''}{where}, from line {left[0][0]} on (--max {mx} stopped the run). "
                  "This score is for the part tried, not the whole file.")
        for n, change in missed:
            print(f"  MISSED line {n}: {change}")
        for n, change in flaky:
            print(f"  FLAKY  line {n}: {change} (failed once, passed on a rerun: not counted as caught)")
        for n, change in stuck:
            print(f"  STUCK  line {n}: {change} (counted as caught)")
        if end != "pass" or flaky:
            print("WARNING: your tests don't give the same answer every run"
                  + (" (they failed again with no fault in, at the end)" if end != "pass" else "")
                  + ". A flaky test can make a fault look caught, so don't trust this score until it's fixed.")
            if end != "pass":
                show(out)
            return 5
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
