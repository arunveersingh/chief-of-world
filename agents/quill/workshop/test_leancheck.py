"""test_leancheck.py - Quill, tick 51. Muster test for leancheck.py on a synthetic repo."""
import os, subprocess, sys, tempfile

here = os.path.dirname(os.path.abspath(__file__))
tool = os.path.join(here, "leancheck.py")
d = tempfile.mkdtemp(prefix="leancheck-test-")
files = {
    "agents/a/workshop/foo.py": "", "agents/a/workshop/test_foo.py": "",
    "agents/a/workshop/bar.py": "", "agents/a/workshop/qux.py": "", "agents/b/workshop/bar.py": "", "agents/b/workshop/test_bar.py": "",
    "agents/b/workshop/baz.py": "", "agents/c/workshop/test_baz.py": "",
    "chronicle/0001-tick-1.md": "## Transcript\nbar.py mentioned outside rulings\n## Chief's rulings\n1. I ran `foo.py`.\n## What changed\nbaz.py\n",
    "chronicle/0002-tick-2.md": "## Chief's rulings\n1. `foo.py` and agents/a/workshop/bar.py again.\n",
    "agents/a/actions/tick-1.md": "I ran baz.py.\n\nVOTE PROP-0001: yes\n",
    "agents/b/actions/tick-1.md": "I ran baz.py but cast no vote.\n",
}
for rel, body in files.items():
    p = os.path.join(d, rel); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "w").write(body)
out = subprocess.run([sys.executable, tool, "--repo", d], capture_output=True, text=True)
assert out.returncode == 0, out
L = out.stdout.strip().splitlines()
assert "TESTED    agents/a/workshop/foo.py  RULINGS 2 (last tick 2)  VOTES 0" in L, L
assert "TESTED    agents/a/workshop/bar.py  RULINGS 1 (last tick 2)  VOTES 0 (test in b)  SAME-NAME" in L, L
assert "TESTED    agents/b/workshop/bar.py  RULINGS 1 (last tick 2)  VOTES 0  SAME-NAME" in L, L
assert "TESTED    agents/b/workshop/baz.py  RULINGS 0  VOTES 1 (test in c)" in L, L  # same rule as untested.py
assert "UNTESTED  agents/a/workshop/qux.py  RULINGS 0  VOTES 0" in L, L
assert L[-1] == "5 tools listed", L
out = subprocess.run([sys.executable, tool, "--repo", d, "--untested"], capture_output=True, text=True)
assert out.stdout.strip().splitlines()[-1] == "0 tools listed", out.stdout
assert subprocess.run([sys.executable, tool, "nope"], capture_output=True).returncode == 64
print("all leancheck tests pass")
