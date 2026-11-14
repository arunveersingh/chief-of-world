"""Tests Wry's agents/wry/workshop/tworecords.py (the Chief cites it for LAW-0007 §6 every tick).
Lives in Forge's workshop because only Wry edits Wry's folder. Read-only: builds fake repos in temp dirs."""
import json, os, subprocess, sys, tempfile
here = os.path.dirname(os.path.abspath(__file__))
root = os.path.normpath(os.path.join(here, "..", "..", ".."))
tool = os.path.join(root, "agents/wry/workshop/tworecords.py")

def fake(events, chron_text):
    d = tempfile.mkdtemp()
    for sub in ("world", "logs", "chronicle"): os.makedirs(os.path.join(d, sub))
    json.dump({"institutions": [{"id": "voluntary_project_fund",
               "grants": [{"proposal": "PROP-0099", "approved_tick": 7}]}]},
              open(os.path.join(d, "world/state.json"), "w"))
    open(os.path.join(d, "logs/events.jsonl"), "w").write("".join(json.dumps(e) + "\n" for e in events))
    if chron_text is not None:
        open(os.path.join(d, "chronicle/0007-tick-7.md"), "w").write(chron_text)
    return subprocess.run([sys.executable, tool], cwd=d, capture_output=True, text=True)

strict = {"type": "grant_passed", "proposal": "PROP-0099"}
r = fake([strict], "PROP-0099 passes")                       # both records
assert r.returncode == 0 and "1 grants, 0 missing records" in r.stdout and "WARN" not in r.stdout, r
r = fake([strict], None)                                     # chronicle file missing
assert r.returncode == 1 and "chronicle NO" in r.stdout, r
r = fake([strict], "nothing about it")                       # chronicle present, grant absent
assert r.returncode == 1 and "chronicle NO" in r.stdout, r
r = fake([], "PROP-0099 passes")                             # event missing
assert r.returncode == 1 and "event NO" in r.stdout, r
r = fake([{"type": "grant", "summary": "PROP-0099 paid"}], "PROP-0099")  # loose event: counts, but WARN
assert r.returncode == 0 and "WARN" in r.stdout, r
# tick 52 mutant `and -> or` on strict-form line survived both tests; these kill it:
r = fake([{"type": "grant", "proposal": "PROP-0099"}], "PROP-0099")  # right proposal, wrong type: WARN
assert r.returncode == 0 and "WARN" in r.stdout, r
r = fake([{"type": "grant_passed", "proposal": "PROP-0001", "summary": "PROP-0099"}], "PROP-0099")  # right type, wrong proposal: WARN
assert r.returncode == 0 and "WARN" in r.stdout, r
print("all tworecords tests pass")
