import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from checkall import tests, run, ROOT

found = [str(t) for t in tests()]
assert "agents/forge/workshop/test_lawdiff.py" in found and "agents/forge/workshop/test_checkall.py" in found
code, out = run(["-c", "print('ok')"])
assert code == 0 and out == "ok"
code, out = run(["-c", "raise SystemExit(3)"])
assert code == 3
print("all checkall tests pass")
