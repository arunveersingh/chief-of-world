import os, subprocess, sys, tempfile
here = os.path.dirname(os.path.abspath(__file__))
tool = os.path.join(here, "untested.py")
d = tempfile.mkdtemp()
files = {
    "agents/a/workshop/foo.py": "",
    "agents/a/workshop/bar.py": "",
    "agents/b/workshop/test_foo.py": "# tests agents/a/workshop/foo.py\n",  # other folder, names the path: counts
    "agents/a/workshop/baz.py": "",
    "agents/q/workshop/test_baz.py": 'p = os.path.join(here, "..", "..", "a", "workshop", "baz.py")\n',  # pieces: counts
    "agents/a/workshop/twin.py": "",
    "agents/c/workshop/twin.py": "",
    "agents/c/workshop/test_twin.py": "import twin\n",  # same folder as c's twin only
}
for rel, body in files.items():
    p = os.path.join(d, rel); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "w").write(body)
out = subprocess.run([sys.executable, tool, "--repo", d], capture_output=True, text=True)
assert out.returncode == 0, out
lines = out.stdout.strip().splitlines()
assert "TESTED    agents/a/workshop/foo.py" in lines, lines
assert "UNTESTED  agents/a/workshop/bar.py" in lines, lines
assert "TESTED    agents/c/workshop/twin.py" in lines, lines
assert "UNTESTED  agents/a/workshop/twin.py" in lines, lines   # Lumen's bare-name case: no longer covered
assert "TESTED    agents/a/workshop/baz.py" in lines, lines
assert lines[-1] == "3 of 5 tools have a test Muster runs", lines
assert subprocess.run([sys.executable, tool, "nope"], capture_output=True).returncode == 64
print("all untested tests pass")
