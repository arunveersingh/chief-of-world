import json, os, sys, tempfile
sys.path.insert(0, os.path.dirname(__file__))
import tworecords as tr

def world(grants, events, chron):
    d = tempfile.mkdtemp()
    for sub in ("world", "logs", "chronicle"): os.makedirs(os.path.join(d, sub))
    json.dump({"institutions": [{"id": "voluntary_project_fund", "grants": grants}]}, open(os.path.join(d, "world/state.json"), "w"))
    open(os.path.join(d, "logs/events.jsonl"), "w").write("".join(json.dumps(e) + "\n" for e in events))
    for t, text in chron.items(): open(os.path.join(d, f"chronicle/{t:04d}-tick-{t}.md"), "w").write(text)
    return d

g = [{"proposal": "PROP-0009", "approved_tick": 7}]
# all three records present, strict event: clean
lines, n, bad = tr.check(world(g, [{"type": "grant_passed", "proposal": "PROP-0009"}], {7: "PROP-0009 passed"}))
assert (n, bad) == (1, 0) and "WARN" not in lines[0], lines
# event only in a summary: counted, but warned
lines, n, bad = tr.check(world(g, [{"type": "grant", "summary": "PROP-0009 paid"}], {7: "PROP-0009"}))
assert bad == 0 and "WARN" in lines[0], lines
# missing event
lines, n, bad = tr.check(world(g, [], {7: "PROP-0009"}))
assert bad == 1 and "event NO" in lines[0], lines
# chronicle exists but doesn't name it, and the wrong tick's chronicle doesn't rescue it
lines, n, bad = tr.check(world(g, [{"type": "grant_passed", "proposal": "PROP-0009"}], {7: "nothing", 8: "PROP-0009"}))
assert bad == 1 and "chronicle NO" in lines[0], lines
# both missing: two missing records, not one (LAW-0029 §6 counts records)
assert tr.check(world(g, [], {}))[2] == 2
# no grants: nothing to miss
assert tr.check(world([], [], {}))[1:] == (0, 0)
# a different proposal's event is not a match
assert tr.check(world(g, [{"type": "grant_passed", "proposal": "PROP-0010"}], {7: "PROP-0009"}))[2] == 1
# tick 52 mutcheck: the strict check needs BOTH fields. Each half alone must still warn.
lines = tr.check(world(g, [{"type": "grant_passed", "summary": "PROP-0009"}], {7: "PROP-0009"}))[0]
assert "WARN" in lines[0], lines          # right type, no proposal field
lines = tr.check(world(g, [{"type": "grant", "proposal": "PROP-0009"}], {7: "PROP-0009"}))[0]
assert "WARN" in lines[0], lines          # proposal field, loose type
# an event of some other type that names the grant is not a grant record
assert tr.check(world(g, [{"type": "vote", "proposal": "PROP-0009"}], {7: "PROP-0009"}))[2] == 1
# the CLI takes an optional root, and must use it (not the cwd) when given
import subprocess
d = world(g, [], {})
r = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "tworecords.py"), d],
                   cwd=tempfile.mkdtemp(), capture_output=True, text=True)
assert r.returncode == 1 and "1 grants, 2 missing records" in r.stdout, r
print("all tworecords tests pass")
