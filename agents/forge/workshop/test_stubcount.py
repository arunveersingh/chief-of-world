#!/usr/bin/env python3
"""test_stubcount.py: drills stubcount.py's argument handling and a live no-call case."""
import subprocess, sys, os
S = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stubcount.py")
run = lambda *x: subprocess.run([sys.executable, S, *x], capture_output=True, text=True)
for bad in ([], ["x"], ["PROP-0037", "--tick"], ["PROP-0037", "--tick", "z"], ["PROP-0037", "extra"]):
    r = run(*bad); assert r.returncode == 64 and "usage" in r.stdout, bad
r = run("PROP-0037", "--builder", "forge", "--active", "ash,quill,forge")
assert "counted yes-voters: ash, quill" in r.stdout and r.stdout.strip().endswith("no stub call"), r.stdout
r = run("PROP-0037", "--active", "nobody"); assert "no stub call possible" in r.stdout, r.stdout
print("all stubcount tests pass")
