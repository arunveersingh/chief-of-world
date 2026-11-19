"""Tests for breakit.py (Ash, tick 63; cases 9-11 tick 66, 12-14 tick 68, 15 tick 69). Builds tiny throwaway projects in temp folders and runs
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
assert out.splitlines() == ["shop.py: your tests caught 1 of 3 faults", "  MISSED line 2: 0 -> 1", "  MISSED line 3: 0 -> 1"], out
assert (d / "shop.py").read_text() == SRC
assert not (d / "__pycache__").exists()

# 2. Testing qty 0 catches line 3 but not line 2: with qty 0, "if qty == 1" falls through to
#    2 * 0, which is still 0. Only a test at qty 1 catches it. That is what a miss asks you.
(d / "test_shop.py").write_text("from shop import total\nassert total(2, 3) == 6\nassert total(2, 0) == 0\n")
rc, out = run(d, "shop.py", "--", sys.executable, "test_shop.py")
assert out.splitlines() == ["shop.py: your tests caught 2 of 3 faults", "  MISSED line 2: 0 -> 1"], out
(d / "test_shop.py").write_text("from shop import total\nassert total(2, 3) == 6\nassert total(2, 0) == 0\nassert total(2, 1) == 2\n")
rc, out = run(d, "shop.py", "--", sys.executable, "test_shop.py")
assert out.splitlines() == ["shop.py: your tests caught 3 of 3 faults"], out

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
assert out.splitlines() == ["m.py: your tests caught 1 of 1 faults"], out

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
assert rc == 0 and out.splitlines() == ["prices.py: your tests caught 3 of 3 faults"], out
assert (d / "prices.py").read_text() == SHOP

# 10. Options after the file, as in the --help example, work the same as before it.
rc, out = run(d, "prices.py", "--dir", ".", "--max", "2", "--timeout", "30", "--", sys.executable, "test_rel.py")
assert rc == 0 and out.splitlines() == ["prices.py: your tests caught 2 of 2 faults"], out

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
assert rc == 5 and lines[0] == "prices.py: your tests caught 0 of 3 faults", out
assert any(l.startswith("  FLAKY  line") for l in lines) and "WARNING: your tests don't give the same answer" in out, out
(d / "test_prices.py").write_text(FLAKY_TEST.replace("self.assertEqual(n % 2, 0)", "pass"))
rc, out = run(d, "prices.py", "--", sys.executable, "test_prices.py")
assert rc == 0 and out.splitlines()[0] == "prices.py: your tests caught 0 of 3 faults" and "FLAKY" not in out, out

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
assert rc == 0 and out.splitlines()[0] == "prices.py: your tests caught 0 of 3 faults", out

print("test_breakit: 15 cases OK")
