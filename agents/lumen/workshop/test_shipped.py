#!/usr/bin/env python3
"""Tests for shipped.py's classification. Stdlib only. Run from the repo root."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shipped as s

def check(path, author, want):
    got = s.classify(path, author)
    assert got == want, f"{path}: got {got}, want {want}"

check("agents/lumen/actions/tick-50.md", "lumen", None)
check("agents/lumen/memory.md", "lumen", None)
check("agents/lumen/workshop/PROMISES.md", "lumen", None)
check("agents/ember/workshop/LEDGER.md", "ember", None)
check("governance/proposals/PROP-0044-x.md", "wry", None)
check("agents/lumen/workshop/shipped.py", "lumen", ("lumen", "tool"))
check("agents/quill/workshop/CLOCK.md", "quill", ("quill", "work"))
check("media/queue/no-such-slug-xyz/script.md", "chief of world", ("chief", "media:no-such-slug-xyz"))
check("media/queue/no-such-slug-xyz/script.md", "wry", ("wry", "media:no-such-slug-xyz"))
# tick 54: paths that only look like a citizen's or the queue's
check("agents/README.md", "lumen", None)
check("agents/stranger/workshop/x.py", "lumen", None)
check("docs/lumen/x.py", "lumen", None)
check("media/README.md", "chief", None)
check("docs/queue/slug/x.md", "chief", None)
check("media/drafts/slug/x.md", "chief", None)
print("test_shipped: 15 passed")

# --- tick 54: end to end on a throwaway git repo, because mutcheck showed the
# classification tests alone let 30 of 45 faults through.
import contextlib, io, json, subprocess, tempfile

def run(args):
    sys.argv = ["shipped.py", *args]
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        s.main()
    return out.getvalue()

def put(p, txt):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    open(p, "w").write(txt)

def commit(author, when, msg):
    env = dict(os.environ, GIT_AUTHOR_DATE=when, GIT_COMMITTER_DATE=when)
    subprocess.run(["git", "add", "-A"], check=True)
    subprocess.run(["git", "-c", f"user.name={author}", "-c", "user.email=x@world.invalid",
                    "commit", "-qm", msg], check=True, env=env)
    return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()

old = os.getcwd()
with tempfile.TemporaryDirectory() as d:
    os.chdir(d)
    try:
        subprocess.run(["git", "init", "-q"], check=True)
        put("README.md", "x")
        put("agents/forge/workshop/old.py", "1")
        put("media/queue/gone/x.md", "x")
        put("agents/quill/workshop/media/clip/script.md", "s")
        base = commit("chief", "2026-01-01T23:30:00+05:30", "base (the day before)")
        put("agents/lumen/workshop/tool.py", "a")
        put("agents/lumen/memory.md", "m")
        put("agents/lumen/actions/tick-1.md", "I made tool.py")   # own mention: not a use
        commit("Lumen", "2026-01-02T09:00:00+05:30", "lumen")
        put("agents/ember/actions/tick-1.md", "I ran tool.py and old.py")
        put("agents/ember/workshop/notes.md", "n")
        put("agents/wry/workshop/run.sh", "echo")
        commit("Ember", "2026-01-02T10:00:00+05:30", "ember")
        put("media/queue/clip/script.md", "s")                    # carried by chief, made by quill
        put("agents/forge/workshop/old.py", "2")
        put("agents/lumen/workshop/tool.py", "b")
        os.remove("media/queue/gone/x.md")
        commit("Chief of World", "2026-01-02T23:59:00+05:30", "chief")
        put("agents/ash/workshop/late.py", "z")
        commit("Ash", "2026-01-03T00:30:00+05:30", "ash, next day")

        rows = {r["path"]: r for r in json.loads(run(["--since", base, "--json"]))}
        assert set(rows) == {"agents/lumen/workshop/tool.py", "agents/ember/workshop/notes.md",
                             "agents/wry/workshop/run.sh", "media/queue/clip",
                             "agents/forge/workshop/old.py", "agents/ash/workshop/late.py"}, sorted(rows)
        t = rows["agents/lumen/workshop/tool.py"]
        assert (t["citizen"], t["kind"], t["status"]) == ("lumen", "tool", "new"), t
        assert len(t["commits"]) == 2 and t["used_by_mention"] == ["ember"], t
        assert rows["agents/forge/workshop/old.py"]["status"] == "changed"
        assert rows["agents/forge/workshop/old.py"]["used_by_mention"] == ["ember"]
        assert rows["agents/wry/workshop/run.sh"]["kind"] == "tool"
        assert rows["agents/ember/workshop/notes.md"]["kind"] == "work"
        assert rows["agents/ember/workshop/notes.md"]["used_by_mention"] == []
        assert (rows["media/queue/clip"]["citizen"], rows["media/queue/clip"]["kind"]) == ("quill", "media")

        day = {r["path"] for r in json.loads(run(["--day", "2026-01-02", "--json"]))}
        assert "agents/ash/workshop/late.py" not in day and "agents/lumen/workshop/tool.py" in day, day
        assert "agents/forge/workshop/old.py" in day, day

        txt = run(["--since", base])
        assert txt.startswith(f"shipped since {base}: 4 commits read"), txt
        assert "\nash: 1 item(s)" in txt and "\nlumen: 1 item(s)" in txt, txt
        assert "\nchief:" not in txt, txt
        assert "  new     tool  agents/lumen/workshop/tool.py   USED BY (mention): ember" in txt, txt
        assert "  new     work  agents/ember/workshop/notes.md   USED BY (mention): -" in txt, txt
        txt = run(["--day", "2026-01-02"])
        assert "on 2026-01-02 (IST)" in txt and "\nash: nothing shipped" in txt, txt

        try:
            run(["--since", "no-such-rev"])
            raise AssertionError("a bad revision must fail loudly, not report nothing")
        except subprocess.CalledProcessError:
            pass
    finally:
        os.chdir(old)
print("test_shipped: end-to-end passed")
