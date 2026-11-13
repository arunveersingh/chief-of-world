import os, subprocess, sys, tempfile
here = os.path.dirname(os.path.abspath(__file__))
tool = os.path.join(here, "untested.py")
d = tempfile.mkdtemp()
for rel in ["agents/a/workshop/foo.py", "agents/a/workshop/bar.py", "agents/b/workshop/test_foo.py"]:
    p = os.path.join(d, rel); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "w").close()
out = subprocess.run([sys.executable, tool, "--repo", d], capture_output=True, text=True)
assert out.returncode == 0, out
lines = out.stdout.strip().splitlines()
assert "TESTED    agents/a/workshop/foo.py" in lines, lines   # a test in another citizen's workshop counts
assert "UNTESTED  agents/a/workshop/bar.py" in lines, lines
assert lines[-1] == "1 of 2 tools have a test Muster runs", lines
assert subprocess.run([sys.executable, tool, "nope"], capture_output=True).returncode == 64
print("all untested tests pass")
