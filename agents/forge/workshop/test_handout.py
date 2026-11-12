"""Forge, tick 31: every path HANDOUT.md names exists, and its kitty example prints what it says."""
import os, re, subprocess, sys
here = os.path.dirname(os.path.abspath(__file__))
root = os.path.abspath(os.path.join(here, "..", "..", ".."))
text = open(os.path.join(here, "HANDOUT.md")).read()
paths = set(re.findall(r"`(agents/[^`\s]+)`", text))
assert len(paths) >= 5, paths
missing = [p for p in paths if not os.path.exists(os.path.join(root, p))]
assert not missing, missing
block = re.search(r"    python3 kitty.py (.+)\n((?:    .+\n)+?)\n", text)
args, expect = block.group(1).split(), [l.strip() for l in block.group(2).splitlines()]
out = subprocess.run([sys.executable, os.path.join(here, "kitty.py"), *args], capture_output=True, text=True).stdout.splitlines()
assert out == expect, (out, expect)
print("handout paths and example check out")
