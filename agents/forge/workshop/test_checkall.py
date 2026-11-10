import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from checkall import tests, run, ROOT

found = [str(t) for t in tests()]
assert "agents/forge/workshop/test_lawdiff.py" in found and "agents/forge/workshop/test_checkall.py" in found
code, out = run(["-c", "print('ok')"])
assert code == 0 and out == "ok"
code, out = run(["-c", "raise SystemExit(3)"])
assert code == 3
# tick 15: the drill builds both known attacks and both witnesses catch both
from checkall import drill, attacks
law = (ROOT / "governance/laws/LAW-0007-one-rulebook.md").read_text()
fakes = attacks(law)
assert all(f != law for f in fakes.values())
assert "10. **Keeper.**" in fakes["Wry's rider after §9 (tick 14)"]
assert fakes["Ash's duplicate §3 (tick 13)"].count("at least 3 citizens vote yes in total") == 1
assert len(drill()) == 2 and all(ld and bd for _, ld, bd in drill()), drill()
print("all checkall tests pass")
