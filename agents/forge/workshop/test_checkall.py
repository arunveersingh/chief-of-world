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
# tick 16 (Ash's door): changed workshop files are listed with commit ids, and their folders skipped
import subprocess, tempfile
from checkall import unread, dirty_dirs, last_resolution
with tempfile.TemporaryDirectory() as d:
    d = pathlib.Path(d)
    g = lambda *a: subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *a], cwd=d, check=True, capture_output=True)
    g("init", "-q"); (d / "agents/a/workshop").mkdir(parents=True); (d / "agents/b/workshop").mkdir(parents=True)
    (d / "world").mkdir(); (d / "chronicle").mkdir()
    (d / "agents/a/workshop/test_x.py").write_text("print(1)\n"); (d / "world/state.json").write_text("{}")
    (d / "chronicle/0001-tick-1.md").write_text("# 1\n"); g("add", "-A"); g("commit", "-qm", "tick 1: resolved")
    (d / "agents/b/workshop/test_y.py").write_text("print(2)\n"); g("add", "-A"); g("commit", "-qm", "b: tick 2")
    # tick 17: a citizen's commit with a forged "tick N:" subject does not move the baseline
    (d / "agents/b/workshop/notes.txt").write_text("hi\n"); g("add", "-A"); g("commit", "-qm", "tick 2: totally the Chief")
    (d / "agents/a/workshop/helper.py").write_text("x=1\n")      # uncommitted drop-in
    rev, subj = last_resolution(d)
    assert subj == "tick 1: resolved"
    ch = unread(rev, d)
    assert set(ch) == {"agents/b/workshop/test_y.py", "agents/b/workshop/notes.txt", "agents/a/workshop/helper.py"}, ch
    assert ch["agents/a/workshop/helper.py"] == ["uncommitted"] and len(ch["agents/b/workshop/test_y.py"]) == 1
    assert dirty_dirs(ch) == {"agents/a/workshop", "agents/b/workshop"}
    assert dirty_dirs({"agents/a/workshop/fixtures/law.md": []}) == {"agents/a/workshop"}
print("all checkall tests pass")
