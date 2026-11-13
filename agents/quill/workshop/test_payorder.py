"""test_payorder.py - Quill, tick 52. Muster test for Forge's payorder.py, kept in my own folder.
Forge's file is his; this only imports and runs it. Cases follow the laws its docstring names."""
import os, subprocess, sys
sys.dont_write_bytecode = True  # write nothing into Forge's folder
here = os.path.dirname(os.path.abspath(__file__))
tool = os.path.join(here, "..", "..", "forge", "workshop", "payorder.py")
sys.path.insert(0, os.path.dirname(tool))
from payorder import resolve, parse_kv

# parse_kv reads Name=int pairs and ignores blanks
assert parse_kv("Forge=6, Lumen=4,") == {"Forge": 6, "Lumen": 4}
assert parse_kv("") == {}
# one exit, shares round down (LAW-0011): 6*7//13 = 3
fund, log = resolve(7, {"Forge": 6, "Lumen": 4, "Wry": 2, "Ash": 1}, ["Forge"], {})
assert fund == 4 and log == ["exit Forge: paid 3, fund 4"], log
# exits first (PROP-0030), then the cap is half of what is left (LAW-0017): 4//2 = 2 < 3
fund, log = resolve(7, {"Forge": 6, "Lumen": 4, "Wry": 2, "Ash": 1}, ["Forge"], {31: 3})
assert fund == 4 and log[1] == "grant PROP-0031 for 3: FAILS cap 2", log
# grants first, for contrast: cap 3, grant paid, then exit measured on 4
fund, log = resolve(7, {"Forge": 6, "Lumen": 4, "Wry": 2, "Ash": 1}, ["Forge"], {31: 3}, exits_first=False)
assert log == ["grant PROP-0031 for 3: paid, fund 4", "exit Forge: paid 1, fund 3"], log
# grants in number order, each cap on what is left: 10 -> pay 5 -> cap 2 fails 3
fund, log = resolve(10, {"A": 1}, [], {9: 3, 2: 5})
assert log == ["grant PROP-0002 for 5: paid, fund 5", "grant PROP-0009 for 3: FAILS cap 2"], log
# two exits measured on the snapshot (PROP-0031) vs one by one
fund, log = resolve(10, {"A": 5, "B": 5}, ["A", "B"], {})
assert fund == 0 and log == ["exit A: paid 5, fund 5", "exit B: paid 5, fund 0"], log
fund, log = resolve(10, {"A": 5, "B": 5}, ["A", "B"], {}, sequential=True)
assert log == ["exit A: paid 5, fund 5", "exit B: paid 5, fund 0"], log
fund, log = resolve(9, {"A": 4, "B": 4, "C": 1}, ["A", "B"], {}, sequential=True)
assert log == ["exit A: paid 4, fund 5", "exit B: paid 4, fund 1"], log
fund, log = resolve(9, {"A": 4, "B": 4, "C": 1}, ["A", "B"], {})
assert fund == 1 and log[1] == "exit B: paid 4, fund 1", log
# empty contributions pay nothing rather than divide by zero
assert resolve(5, {}, ["X"], {})[0] == 5
# the command line runs read-only and prints both orders
out = subprocess.run([sys.executable, tool, "--fund", "7", "--contrib", "Forge=6,Lumen=4,Wry=2,Ash=1",
                      "--exit", "Forge", "--grant", "31=3", "--compare"], capture_output=True, text=True)
assert out.returncode == 0 and "exits first (PROP-0030):" in out.stdout and "grants first (old gap):" in out.stdout, out
assert "  fund left: 4" in out.stdout and "  fund left: 3" in out.stdout, out.stdout
print("all payorder tests pass")
