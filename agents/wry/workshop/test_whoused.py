import os, sys, tempfile, subprocess
sys.path.insert(0, os.path.dirname(__file__))
import whoused as s
# path mapping
assert s.thing_of("agents/wry/workshop/clock.py", "wry") == ("tool", "clock.py")
assert s.thing_of("agents/wry/workshop/media/the-door/script.md", "wry") == ("work", "media/the-door")
assert s.thing_of("agents/wry/workshop/__pycache__/x.pyc", "wry") is None
assert s.thing_of("agents/ash/workshop/x.py", "wry") is None, "only your own folder"
assert s.thing_of("media/queue/six-citizens/script.md", "lumen") == ("piece", "six-citizens")
assert s.thing_of("agents/wry/actions/tick-50.md", "wry") is None, "action files are not things"
# mentions: whole names only
rx = s.mention_re("tally.py")
assert rx.search("ran `tally.py --collisions`") and not rx.search("ran mytally.py")
# a tiny repo: Forge ships a tool, Ash names it, Forge naming it himself doesn't count
d = tempfile.mkdtemp()
def sh(*a, env=None): subprocess.run(a, cwd=d, check=True, capture_output=True, env=env)
os.makedirs(os.path.join(d, "world")); os.makedirs(os.path.join(d, "agents/forge/workshop"))
os.makedirs(os.path.join(d, "agents/ash/actions")); os.makedirs(os.path.join(d, "agents/forge/actions"))
open(os.path.join(d, "world/citizens.json"), "w").write('{"citizens":{"ash":1,"forge":2}}')
open(os.path.join(d, "agents/forge/workshop/gizmo.py"), "w").write("print(1)\n")
open(os.path.join(d, "agents/forge/actions/tick-1.md"), "w").write("I built gizmo.py\n")
open(os.path.join(d, "agents/ash/actions/tick-2.md"), "w").write("I ran `gizmo.py` and it worked.\n")
sh("git", "init", "-q")
env = dict(os.environ, GIT_AUTHOR_NAME="Forge", GIT_AUTHOR_EMAIL="f@x", GIT_COMMITTER_NAME="Forge",
           GIT_COMMITTER_EMAIL="f@x", GIT_AUTHOR_DATE="2026-11-14T10:00:00+05:30", GIT_COMMITTER_DATE="2026-11-14T10:00:00+05:30")
sh("git", "add", "-A", env=env); sh("git", "commit", "-qm", "forge: gizmo", env=env)
import datetime
got = s.shipped_on(d, datetime.date(2026, 11, 14), ["ash", "forge"])
assert got == {"ash": {}, "forge": {"gizmo.py": "tool"}}, got
assert s.shipped_on(d, datetime.date(2026, 11, 13), ["ash", "forge"])["forge"] == {}, "day boundary is IST"
assert s.uses(d, "gizmo.py", "forge", ["ash", "forge"]) == {"ash": [2]}
print("all shipped tests pass")
assert s.thing_of("agents/forge/workshop/test_kitty.py", "forge") is None, "tests ride with their tool"
open(os.path.join(d, "agents/ash/actions/tick-3.md"), "w").write("Untested: `gizmo.py`\nother line\n")
assert s.show(d, "gizmo.py", "forge", ["ash", "forge"]) == [("ash", 2, "I ran `gizmo.py` and it worked."), ("ash", 3, "Untested: `gizmo.py`")]
print("show test passes")

# tick 56: cases for the 13 survivors mutcheck found (19 of 32)
import io, contextlib
# folders: a non-media subfolder is one thing named by its folder; media is named by two levels
assert s.thing_of("agents/wry/workshop/kit/sub/a.py", "wry") == ("work", "kit")
assert s.thing_of("agents/wry/workshop/media/x/y/z.md", "wry") == ("work", "media/x")
# git errors must not pass silently
try:
    s.git(tempfile.mkdtemp(), "log"); raise SystemExit("git outside a repo should raise")
except subprocess.CalledProcessError:
    pass
# a second day: Forge ships two things just after midnight IST; the Chief's commit is not a citizen's
os.makedirs(os.path.join(d, "agents/forge/workshop/kit/deep"))
open(os.path.join(d, "agents/forge/workshop/kit/deep/inner.py"), "w").write("x=1\n")
open(os.path.join(d, "agents/forge/workshop/widget.py"), "w").write("x=2\n")
e2 = dict(env, GIT_AUTHOR_DATE="2026-11-15T00:30:00+05:30", GIT_COMMITTER_DATE="2026-11-15T00:30:00+05:30")
sh("git", "add", "-A", env=e2); sh("git", "commit", "-qm", "forge: kit, widget", env=e2)
open(os.path.join(d, "agents/forge/workshop/chiefnote.py"), "w").write("x=3\n")
e3 = dict(e2, GIT_AUTHOR_NAME="Chief", GIT_COMMITTER_NAME="Chief",
          GIT_AUTHOR_DATE="2026-11-15T09:00:00+05:30", GIT_COMMITTER_DATE="2026-11-15T09:00:00+05:30")
sh("git", "add", "-A", env=e3); sh("git", "commit", "-qm", "chief: note", env=e3)
got = s.shipped_on(d, datetime.date(2026, 11, 15), ["ash", "forge"])
assert got == {"ash": {}, "forge": {"kit": "work", "widget.py": "tool"}}, got
# owner lookup finds nested files, and by base name
assert s.owner_of(d, "inner.py", ["ash", "forge"]) == "forge"
assert s.owner_of(d, "gizmo.py", ["ash", "forge"]) == "forge"
assert s.owner_of(d, "nope.py", ["ash", "forge"]) is None
# --show orders by tick first, then citizen
os.makedirs(os.path.join(d, "agents/quill/actions"))
open(os.path.join(d, "agents/quill/actions/tick-1.md"), "w").write("quill read gizmo.py\n")
cs = ["ash", "forge", "quill"]
assert [(c, t) for c, t, _ in s.show(d, "gizmo.py", "forge", cs)] == [("quill", 1), ("ash", 2), ("ash", 3)]
# CLI: --uses prints the owner; the day view names a citizen only on their first row
open(os.path.join(d, "world/citizens.json"), "w").write('{"citizens":{"ash":1,"forge":2,"quill":3}}')
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    s.main(["--uses", "gizmo.py", "--repo", d])
assert buf.getvalue().startswith("gizmo.py (owner: forge): ash (2), quill (1)"), buf.getvalue()
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    s.main(["--day", "2026-11-15", "--repo", d])
rows = [l for l in buf.getvalue().splitlines() if "kit" in l or "widget.py" in l]
assert rows[0].startswith("forge") and rows[1].startswith("      "), rows
print("tick-56 whoused cases pass")
