"""Tests for breakit.py (Ash, tick 63). Builds tiny throwaway projects in temp folders and runs
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

print("test_breakit: 8 cases OK")
