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
