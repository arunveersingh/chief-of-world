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
# tick 18: symlinks, cross-folder reach, renames, and flags
from checkall import symlinked, reaches
with tempfile.TemporaryDirectory() as d:
    d = pathlib.Path(d)
    g = lambda *a: subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *a], cwd=d, check=True, capture_output=True)
    g("init", "-q")
    for c in "abc":
        (d / f"agents/{c}/workshop").mkdir(parents=True)
    (d / "elsewhere.py").write_text("print('outside')\n")
    (d / "agents/a/workshop/test_link.py").symlink_to(d / "elsewhere.py")
    assert symlinked("agents/a/workshop/test_link.py", d) and not symlinked("agents/a/workshop", d)
    (d / "agents/c/workshop/test_reach.py").write_text("import sys; sys.path.insert(0, 'agents/b/workshop')\n")
    (d / "agents/c/workshop/test_calm.py").write_text("print(1)\n")
    assert reaches("agents/c/workshop", {"agents/b/workshop"}, d) == ["agents/b/workshop"]
    assert reaches("agents/a/workshop", {"agents/b/workshop"}, d) == []
    assert reaches("agents/b/workshop", {"agents/b/workshop"}, d) == []      # its own folder is handled already
    # tick 19: a computed path can't be read as text, so a dynamic loader reaches every dirty folder
    il = "import" + "lib"
    (d / "agents/a/workshop/test_sly.py").write_text(f"import {il}, os\nn = 'b' + ''\n{il}.import_module('x')\n")
    assert reaches("agents/a/workshop", {"agents/b/workshop", "agents/c/workshop"}, d) == ["agents/b/workshop", "agents/c/workshop"]
    assert reaches("agents/a/workshop", {"agents/a/workshop"}, d) == []     # nothing else dirty, nothing to reach
    (d / "agents/a/workshop/test_sly.py").write_text("import sys, pathlib\nsys.path.insert(0, str(pathlib.Path(__file__)" + ".parent" + ".parent))\n")
    assert reaches("agents/a/workshop", {"agents/b/workshop"}, d) == ["agents/b/workshop"]
    from checkall import dynamic
    assert not dynamic("import re\nx = re.compile('a')\n")                       # a regex is not a loader
    assert not dynamic("import os\nROOT = os.path.join(os.path.dirname(__file__), '..', '..')\n")  # climbing to read is fine
    (d / "agents/a/workshop/test_sly.py").unlink()
    # a rename is listed under its new name
    (d / "world").mkdir(); (d / "chronicle").mkdir(); (d / "world/state.json").write_text("{}")
    (d / "chronicle/0001-tick-1.md").write_text("x\n"); (d / "agents/b/workshop/old.py").write_text("x=1\n")
    g("add", "-A"); g("commit", "-qm", "tick 1: base")
    g("mv", "agents/b/workshop/old.py", "agents/b/workshop/test_new.py"); g("commit", "-qm", "b: rename")
    assert "agents/b/workshop/test_new.py" in unread(last_resolution(d)[0], d)
# tick 20: Ash's notes/ door. A helper outside the workshop is watched and skips every workshop.
from checkall import outside
with tempfile.TemporaryDirectory() as d:
    d = pathlib.Path(d)
    g = lambda *a: subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *a], cwd=d, check=True, capture_output=True)
    g("init", "-q")
    for c in "ab":
        (d / f"agents/{c}/workshop").mkdir(parents=True)
        (d / f"agents/{c}/actions").mkdir(parents=True)
    (d / "agents/a/notes").mkdir()
    (d / "world").mkdir(); (d / "chronicle").mkdir(); (d / "world/state.json").write_text("{}")
    (d / "chronicle/0001-tick-1.md").write_text("x\n")
    (d / "agents/a/workshop/test_probe.py").write_text("import runpy  # reads ../notes/helper.py\n")
    (d / "agents/a/notes/helper.py").write_text("print('boring')\n")
    g("add", "-A"); g("commit", "-qm", "tick 1: base")
    # prose only: nothing is unread, nothing is skipped
    (d / "agents/b/actions/tick-2.md").write_text("words\n"); (d / "agents/b/memory.md").write_text("m\n")
    (d / "agents/b/outbox.md").write_text("o\n"); g("add", "-A"); g("commit", "-qm", "b: tick 2")
    assert unread(last_resolution(d)[0], d) == {}
    # Ash's attack: change only notes/helper.py
    (d / "agents/a/notes/helper.py").write_text("print('not boring')\n"); g("commit", "-qam", "a: tweak notes")
    ch = unread(last_resolution(d)[0], d)
    assert list(ch) == ["agents/a/notes/helper.py"] and outside(ch) == ["agents/a/notes/helper.py"]
    assert dirty_dirs(ch, d) == {"agents/a/workshop", "agents/b/workshop"}
    assert dirty_dirs({"agents/b/workshop/x.py": []}, d) == {"agents/b/workshop"}   # a workshop change stays local
# tick 22: Ash's actions/ door. A helper in actions/ is watched; a loader test is skipped when prose changes.
from checkall import prose_changed, loader_folder
with tempfile.TemporaryDirectory() as d:
    d = pathlib.Path(d)
    g = lambda *a: subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *a], cwd=d, check=True, capture_output=True)
    g("init", "-q")
    for c in "ab":
        (d / f"agents/{c}/workshop").mkdir(parents=True); (d / f"agents/{c}/actions").mkdir(parents=True)
    (d / "world").mkdir(); (d / "chronicle").mkdir(); (d / "world/state.json").write_text("{}")
    (d / "chronicle/0001-tick-1.md").write_text("x\n")
    rp = "run" + "py"
    (d / "agents/a/workshop/test_probe.py").write_text(f"import {rp}  # runs ../actions/helper.py\n")
    (d / "agents/b/workshop/test_calm.py").write_text("print(1)\n")
    (d / "agents/a/actions/helper.py").write_text("print('v1')\n")
    g("add", "-A"); g("commit", "-qm", "tick 1: base")
    (d / "agents/a/actions/helper.py").write_text("print('v2')\n"); g("commit", "-qam", "a: only the helper")
    base = last_resolution(d)[0]
    ch = unread(base, d)
    assert list(ch) == ["agents/a/actions/helper.py"] and outside(ch) == ["agents/a/actions/helper.py"]
    assert dirty_dirs(ch, d) == {"agents/a/workshop", "agents/b/workshop"}       # Ash's exact recipe: everything skipped
    assert prose_changed(base, d) == []
    # prose stays unlisted, but counts against a loader
    (d / "agents/a/actions/tick-2.md").write_text("words\n"); (d / "agents/a/memory.md").write_text("m\n")
    assert sorted(unread(base, d)) == ["agents/a/actions/helper.py"]
    assert prose_changed(base, d) == ["agents/a/actions/tick-2.md", "agents/a/memory.md"]
    assert loader_folder("agents/a/workshop", d) and not loader_folder("agents/b/workshop", d)
# tick 24: Ash's memory.md breach (tick 23), end to end. A test runs the last fenced py block of its
# owner's memory.md with subprocess; memory is prose, so the change is never listed. In the worktree the
# changed memory.md is back at baseline bytes, so the planted block never runs.
from checkall import worktree, drop
with tempfile.TemporaryDirectory() as d:
    d = pathlib.Path(d)
    g = lambda *a: subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *a], cwd=d, check=True, capture_output=True)
    g("init", "-q")
    (d / "agents/a/workshop").mkdir(parents=True); (d / "agents/a/actions").mkdir(parents=True)
    (d / "world").mkdir(); (d / "chronicle").mkdir(); (d / "world/state.json").write_text("{}")
    (d / "chronicle/0001-tick-1.md").write_text("x\n")
    fence = "`" * 3
    (d / "agents/a/memory.md").write_text(f"{fence}py\nprint('calm')\n{fence}\n")
    (d / "agents/a/workshop/test_mem.py").write_text(
        "import pathlib, subprocess, sys\n"
        "t = (pathlib.Path(__file__).resolve().parents[1] / 'memory.md').read_text()\n"
        f"code = t.split('{fence}py')[-1].split('{fence}')[0]\n"
        "print(subprocess.run([sys.executable, '-c', code], capture_output=True, text=True).stdout.strip())\n")
    g("add", "-A"); g("commit", "-qm", "tick 1: base")
    base = last_resolution(d)[0]
    (d / "agents/a/memory.md").write_text(f"{fence}py\nprint('PLANTED')\n{fence}\n")
    (d / "agents/a/outbox.md").write_text("new prose\n")
    g("add", "-A"); g("commit", "-qm", "a: tick 2")
    assert unread(base, d) == {}                                   # nothing listed: that was the breach
    in_place = subprocess.run([sys.executable, "agents/a/workshop/test_mem.py"], cwd=d, capture_output=True, text=True).stdout
    assert "PLANTED" in in_place                                   # running in place falls for it
    wt = worktree(base, d)
    try:
        assert wt and (wt / "agents/a/memory.md").read_text() == f"{fence}py\nprint('calm')\n{fence}\n"
        assert not (wt / "agents/a/outbox.md").exists()            # prose new since baseline is removed
        out = subprocess.run([sys.executable, "agents/a/workshop/test_mem.py"], cwd=wt, capture_output=True, text=True).stdout
        assert out.strip() == "calm", out
        assert (d / "agents/a/memory.md").read_text().count("PLANTED") == 1   # the real checkout is untouched
    finally:
        drop(wt, d)
    assert not wt.exists() and str(wt) not in subprocess.run(["git", "worktree", "list"], cwd=d, capture_output=True, text=True).stdout
code, out = run(["agents/forge/workshop/checkall.py", "--hepl"])
assert code == 64 and "unknown" in out, (code, out)
code, out = run(["agents/forge/workshop/checkall.py", "--help"])
assert code == 0 and "Muster" in out
print("all checkall tests pass")
