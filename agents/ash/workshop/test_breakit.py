"""Tests for breakit.py (Ash, tick 63; cases 9-11 tick 66, 12-14 tick 68, 15 tick 69, 16 tick 70, 17 tick 71, 18 tick 72). Builds tiny throwaway projects in temp folders and runs
the tool on them as a stranger would: by path, with their own test command. Standard library only."""
import pathlib, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent
TOOL = HERE / "breakit.py"

def project(files):
    d = pathlib.Path(tempfile.mkdtemp())
    for name, body in files.items():
        (d / name).write_text(body)
    return d

def run(d, *args):
    r = subprocess.run([sys.executable, "-B", str(TOOL), *args], cwd=d, capture_output=True, text=True, timeout=120)
    return r.returncode, r.stdout

# 1. A miss is reported by line and change; the user's file is left exactly as it was.
SRC = "def total(price, qty):\n    if qty == 0:\n        return 0\n    return price * qty\n"
d = project({"shop.py": SRC, "test_shop.py": "from shop import total\nassert total(2, 3) == 6\n"})
rc, out = run(d, "shop.py", "--", sys.executable, "test_shop.py")
assert rc == 0, out
assert out.splitlines() == ["shop.py: your tests caught 2 of 4 faults", "  MISSED line 2: 0 -> 1", "  MISSED line 3: 0 -> 1"], out
assert (d / "shop.py").read_text() == SRC
assert not (d / "__pycache__").exists()

# 2. Testing qty 0 catches line 3 but not line 2: with qty 0, "if qty == 1" falls through to
#    2 * 0, which is still 0. Only a test at qty 1 catches it. That is what a miss asks you.
(d / "test_shop.py").write_text("from shop import total\nassert total(2, 3) == 6\nassert total(2, 0) == 0\n")
rc, out = run(d, "shop.py", "--", sys.executable, "test_shop.py")
assert out.splitlines() == ["shop.py: your tests caught 3 of 4 faults", "  MISSED line 2: 0 -> 1"], out
(d / "test_shop.py").write_text("from shop import total\nassert total(2, 3) == 6\nassert total(2, 0) == 0\nassert total(2, 1) == 2\n")
rc, out = run(d, "shop.py", "--", sys.executable, "test_shop.py")
assert out.splitlines() == ["shop.py: your tests caught 4 of 4 faults"], out

# 3. A fault that makes the code hang is STUCK, counted as caught, within --timeout (not 60 s).
LOOP = "def countdown(n):\n    while n != 0:\n        n -= 1\n    return n\n"
d = project({"loop.py": LOOP, "test_loop.py": "from loop import countdown\nassert countdown(3) == 0\n"})
rc, out = run(d, "--timeout", "1", "loop.py", "--", sys.executable, "test_loop.py")
assert out.splitlines() == ["loop.py: your tests caught 3 of 3 faults", "  STUCK  line 3: 1 -> 2 (counted as caught)"], out

# 4. Tests that already fail, or already hang, stop the run with exit 3 and no fault judged.
d = project({"a.py": "X = 1\n", "test_a.py": "import a\nassert a.X == 2\n"})
rc, out = run(d, "a.py", "--", sys.executable, "test_a.py")
assert rc == 3 and out.startswith("STOP: your tests fail before any fault"), out
d = project({"a.py": "X = 1\n", "test_a.py": "import time\ntime.sleep(5)\n"})
rc, out = run(d, "--timeout", "1", "a.py", "--", sys.executable, "test_a.py")
assert rc == 3 and out.startswith("STOP: your tests got stuck"), out

# 5. Strings and comments are never changed; --max caps the count; --dir works from elsewhere.
d = project({"m.py": 'LABEL = "a == b and 0"  # x >= 1\nY = 1 == 1\n', "test_m.py": "import m\nassert m.Y is True\n"})
rc, out = run(d.parent, "--dir", str(d), "--max", "1", str(d / "m.py"), "--", sys.executable, "test_m.py")
assert out.splitlines() == ["m.py: your tests caught 1 of 1 faults",
                           "  NOT TRIED: 2 more faults, from line 2 on (--max 1 stopped the run). "
                           "This score is for the part tried, not the whole file."], out

# 6. No command given: usage, exit 2.
rc, out = run(d, "m.py")
assert rc == 2 and "breakit.py" in out

# 7. A multi-line string spans lines (its middle and end are masked too), a line can mix a string
#    with code (only the code part changes), and the user's test output never leaks into the report.
MIX = 'NOTE = """first\nsecond == 1\n"""\nS = "<"; OK = 1 == 1\n'
d = project({"mix.py": MIX, "test_mix.py": "import mix\nprint('noise from the test')\nassert mix.OK is True\n"})
rc, out = run(d, "mix.py", "--", sys.executable, "test_mix.py")
assert out.splitlines() == ["mix.py: your tests caught 3 of 3 faults"], out

# 8. A command but no file, or two files: usage, exit 2.
rc, out = run(d, "--", sys.executable, "test_mix.py")
assert rc == 2 and "breakit.py" in out
rc, out = run(d, "mix.py", "test_mix.py", "--", sys.executable, "test_mix.py")
assert rc == 2 and "breakit.py" in out

# 9. Wry's "0 of 3" (tick 65): the tests import the ORIGINAL file by absolute path, so they never run
#    the copy. The canary makes the copy crash on load; the tests still pass, so nothing is scored.
SHOP = "def total(qty, price):\n    if qty <= 0:\n        return 0\n    return qty * price\n"
d = project({"prices.py": SHOP})
(d / "test_abs.py").write_text(f"import sys\nsys.path.insert(0, {str(d)!r})\nfrom prices import total\n"
                               "assert total(0, 5) == 0 and total(1, 5) == 5 and total(-1, 5) == 0\n")
(d / "test_rel.py").write_text("from prices import total\nassert total(0, 5) == 0 and total(1, 5) == 5 and total(-1, 5) == 0\n")
rc, out = run(d, "prices.py", "--", sys.executable, "test_abs.py")
assert rc == 4 and out.startswith("STOP: your tests still passed") and "caught" not in out, out
rc, out = run(d, "prices.py", "--", sys.executable, "test_rel.py")
assert rc == 0 and out.splitlines() == ["prices.py: your tests caught 4 of 4 faults"], out
assert (d / "prices.py").read_text() == SHOP

# 10. Options after the file, as in the --help example, work the same as before it.
rc, out = run(d, "prices.py", "--dir", ".", "--max", "2", "--timeout", "30", "--", sys.executable, "test_rel.py")
assert rc == 0 and out.splitlines() == ["prices.py: your tests caught 2 of 2 faults",
    "  NOT TRIED: 2 more faults, from line 3 on (--max 2 stopped the run). This score is for the part tried, not the whole file."], out

# 11. Mistakes get one sentence and exit 2, never a traceback.
for args, says in [(["nope.py"], "no such file: nope.py"), (["/tmp"], "no such file"),
                   (["prices.py", "--max", "lots"], "--max needs a whole number"),
                   (["prices.py", "--repeat", "twice"], "--repeat needs a whole number"),
                   (["prices.py", "--speed", "3"], "unknown option --speed"),
                   (["prices.py", "--dir", "nowhere"], "is not a folder")]:
    r = subprocess.run([sys.executable, "-B", str(TOOL), *args, "--", "true"], cwd=d, capture_output=True, text=True)
    assert r.returncode == 2 and says in r.stdout and "Traceback" not in r.stdout + r.stderr, (args, r.stdout, r.stderr)
other = project({"far.py": "X = 1\n"})
r = subprocess.run([sys.executable, "-B", str(TOOL), str(other / "far.py"), "--", "true"], cwd=d, capture_output=True, text=True)
assert r.returncode == 2 and "is not inside the project folder" in r.stdout and "Traceback" not in r.stderr, r.stdout + r.stderr

# 12. Wry's flaky test (tick 67): it checks nothing and fails every other run. It used to turn an
#     honest "0 of N" into a catch. Each catch now has to fail twice, and the untouched copy runs
#     again at the end, so the flake earns nothing and the run says the score can't be trusted.
FL = "def total(qty, price):\n    if qty > 0:\n        return qty * price\n    return 0\n"
FLAKY_TEST = ("import os, unittest, prices\nC = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'count.txt')\n"
              "class T(unittest.TestCase):\n    def test_loads(self):\n"
              "        n = int(open(C).read()) if os.path.exists(C) else 0\n        open(C, 'w').write(str(n + 1))\n"
              "        self.assertEqual(n % 2, 0)\nif __name__ == '__main__':\n    unittest.main()\n")
#     (--repeat 1 skips the up-front check of case 15, so the per-fault check is tested on its own.)
d = project({"prices.py": FL, "test_prices.py": FLAKY_TEST})
rc, out = run(d, "prices.py", "--repeat", "1", "--", sys.executable, "test_prices.py")
lines = out.splitlines()
assert rc == 5 and lines[0] == "prices.py: your tests caught 0 of 4 faults", out
assert any(l.startswith("  FLAKY  line") for l in lines) and "WARNING: your tests don't give the same answer" in out, out
(d / "test_prices.py").write_text(FLAKY_TEST.replace("self.assertEqual(n % 2, 0)", "pass"))
rc, out = run(d, "prices.py", "--", sys.executable, "test_prices.py")
assert rc == 0 and out.splitlines()[0] == "prices.py: your tests caught 0 of 4 faults" and "FLAKY" not in out, out

# 13. No tests found (unittest and pytest exit 5) is its own stop, not "your tests fail", and the
#     command's last lines are shown.
d = project({"prices.py": FL, "prices_test.py": "import prices\n"})
rc, out = run(d, "prices.py", "--", sys.executable, "-c", "import sys; print('NO TESTS RAN'); sys.exit(5)")
assert rc == 3 and out.startswith("STOP: your test command ran no tests") and "| NO TESTS RAN" in out, out

# 14. A bare except: around the import swallows the canary and skips every test. The stop names
#     that cause too, and shows the output, so "skipped" is visible.
SKIP_TEST = ("import unittest\ntry:\n    import prices\nexcept:\n    prices = None\n"
             "class T(unittest.TestCase):\n    @unittest.skipIf(prices is None, 'prices not importable')\n"
             "    def test_total(self):\n        self.assertEqual(prices.total(2, 3), 6)\n"
             "if __name__ == '__main__':\n    unittest.main()\n")
d = project({"prices.py": FL, "test_prices.py": SKIP_TEST})
rc, out = run(d, "prices.py", "--", sys.executable, "test_prices.py")
assert rc == 4 and "bare except:" in out and "skipped=1" in out, out

# 15. Tick 69: the untouched tests run 3 times before any fault. Wry's every-other-run flake is
#     stopped on run 2, with exit 5, before a single fault is spent, and nothing is scored.
d = project({"prices.py": FL, "test_prices.py": FLAKY_TEST})
rc, out = run(d, "prices.py", "--", sys.executable, "test_prices.py")
assert rc == 5 and out.startswith("STOP: your tests passed on run 1 but failed on run 2") and "caught" not in out, out
assert "| FAILED" in out, out
rc, out = run(d, "prices.py", "--repeat", "0", "--", sys.executable, "test_prices.py")
assert rc == 2 and "--repeat needs at least 1" in out, out
(d / "test_prices.py").write_text(FLAKY_TEST.replace("self.assertEqual(n % 2, 0)", "pass"))
rc, out = run(d, "prices.py", "--", sys.executable, "test_prices.py")
assert rc == 0 and out.splitlines()[0] == "prices.py: your tests caught 0 of 4 faults", out

# 16. Tick 70: --lines keeps faults to one stretch of a big file, and a run cut short by --max says
#     what it left untried. Before this, "--max 20" scored only the top of a file and didn't say so.
BIG = ("def a(x):\n    return x == 0\n\n"            # lines 1-2: tested
       "def b(x):\n    return x > 1\n")               # lines 4-5: untested
d = project({"big.py": BIG, "test_big.py": "from big import a\nassert a(0) is True\nassert a(5) is False\n"})
rc, out = run(d, "big.py", "--lines", "4-5", "--", sys.executable, "test_big.py")
assert rc == 0 and out.splitlines() == ["big.py: your tests caught 0 of 2 faults on lines 4-5",
                                        "  MISSED line 5: > -> <=", "  MISSED line 5: 1 -> 2"], out
rc, out = run(d, "big.py", "--max", "2", "--", sys.executable, "test_big.py")
assert out.splitlines() == ["big.py: your tests caught 2 of 2 faults",
                            "  NOT TRIED: 2 more faults, from line 5 on (--max 2 stopped the run). "
                            "This score is for the part tried, not the whole file."], out
rc, out = run(d, "big.py", "--lines", "3-3", "--", sys.executable, "test_big.py")
assert rc == 0 and out.strip() == "breakit: no faults to make in big.py on lines 3-3. Nothing was scored.", out
for bad in ("5-4", "0-3", "five", "4"):
    rc, out = run(d, "big.py", "--lines", bad, "--", sys.executable, "test_big.py")
    assert rc == 2 and "--lines needs two line numbers" in out, (bad, out)

# 17. Tick 71: sums break too (+ to -, - to +, * to /, / to *). A test with a zero bill can't tell
#     multiply from divide, so both are MISSED. Operators that aren't sums (->, **, *args, +=) and
#     text in quotes are left alone, and a fault that isn't valid Python is skipped, not scored.
SPLIT = "def share(bill, days, all_days):\n    return bill * days / all_days\n"
d = project({"split.py": SPLIT, "test_split.py": "from split import share\nassert share(0, 10, 30) == 0\n"})
rc, out = run(d, "split.py", "--", sys.executable, "test_split.py")
assert rc == 0 and out.splitlines() == ["split.py: your tests caught 0 of 2 faults",
                                        "  MISSED line 2: * -> /", "  MISSED line 2: / -> *"], out
(d / "test_split.py").write_text("from split import share\nassert share(300, 10, 30) == 100\n")
rc, out = run(d, "split.py", "--", sys.executable, "test_split.py")
assert rc == 0 and out.splitlines() == ["split.py: your tests caught 2 of 2 faults"], out
ODD = 'def f(*a, **k) -> int:\n    n = 2 ** 3\n    n += 2\n    return "a + b"  # c - d\n'
d = project({"odd.py": ODD, "test_odd.py": "import odd\nassert odd.f() == 'a + b'\n"})
rc, out = run(d, "odd.py", "--", sys.executable, "test_odd.py")
assert rc == 0 and out.strip() == "breakit: no faults to make in odd.py. Nothing was scored.", out

# 18. Tick 72, Wry's clock bug (tick 71): a failure that lasts a few seconds fails the fault run
#     AND its rerun, so "fail twice" counted a fault nobody checks as caught. Here the bad seconds
#     are runs 1-3 of the test (counted in a file, so the case is the same every time). Each catch
#     now ends with the untouched copy, which fails inside the bad seconds too: FLAKY, exit 5.
BURST_TEST = FLAKY_TEST.replace("self.assertEqual(n % 2, 0)", "self.assertNotIn(n, (1, 2, 3))")
d = project({"prices.py": FL, "test_prices.py": BURST_TEST})
rc, out = run(d, "prices.py", "--repeat", "1", "--", sys.executable, "test_prices.py")
lines = out.splitlines()
assert rc == 5 and lines[0] == "prices.py: your tests caught 0 of 4 faults", out
assert "  FLAKY  line 2: > -> <= (failed twice, but the untouched copy failed too: not counted as caught)" in lines, out
#     A real catch still counts: fault, fault, untouched copy passes.
d = project({"prices.py": FL, "test_prices.py": "import prices\nassert prices.total(2, 3) == 6\nassert prices.total(0, 3) == 0\nassert prices.total(1, 3) == 3\n"})
rc, out = run(d, "prices.py", "--", sys.executable, "test_prices.py")
assert rc == 0 and "FLAKY" not in out and "caught 4 of 4" in out.splitlines()[0], out

print("test_breakit: 18 cases OK")
