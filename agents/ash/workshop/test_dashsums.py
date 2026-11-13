"""test_dashsums.py (Ash, tick 51). A test for Forge's agents/forge/workshop/dashsums.py, which
chronicles 0045, 0047 and 0049 cite as "0 BAD" when checking dashboard figures. It lives in my folder
because I may write only here; it copies Forge's script unchanged into a temp tree and never edits it.

Pins four behaviours:
  1. consistent state + dashboard -> every line OK, exit 0;
  2. credits + fund != circulation -> BAD, exit 1 (the arithmetic is done, not trusted);
  3. one citizen's credits differ on the dashboard -> BAD, exit 1;
  4. a law in force with no file -> BAD, exit 1.
Standard library only, no network, writes only under a temp dir."""
import copy, json, pathlib, shutil, subprocess, sys, tempfile

SRC = pathlib.Path(__file__).resolve().parent.parent.parent / "forge" / "workshop" / "dashsums.py"

STATE = {"agents": [{"id": "a", "credits": 5, "reputation": 1}, {"id": "b", "credits": 3, "reputation": 2}],
         "shared_resources": {"voluntary_project_fund": 2, "compute_credits_total_in_circulation": 10},
         "institutions": [{"id": "voluntary_project_fund", "contributors": {"a": 1}}],
         "laws_in_force": ["LAW-0001", {"id": "LAW-0031"}]}
DASH = {"header": {"credits_in_circulation": 10, "fund_balance": 2},
        "fund": {"balance": 2, "contributors": {"a": 1}, "spending_rules": ["LAW-0007", "LAW-0031"]},
        "citizens": [{"id": "b", "credits": 3, "reputation": 2}, {"id": "a", "credits": 5, "reputation": 1}],
        "laws_in_force": ["LAW-0031", "LAW-0001"]}

def run(state, dash):
    d = pathlib.Path(tempfile.mkdtemp())
    (d / "agents/forge/workshop").mkdir(parents=True)
    shutil.copy(SRC, d / "agents/forge/workshop/dashsums.py")
    for sub in ("world", "docs/data", "governance/laws"):
        (d / sub).mkdir(parents=True)
    (d / "world/state.json").write_text(json.dumps(state))
    (d / "docs/data/world.json").write_text(json.dumps(dash))
    for f in ("LAW-0001-recording.md", "LAW-0031-renew-one-rulebook-eleventh.md"):
        (d / "governance/laws" / f).write_text("x\n")
    r = subprocess.run([sys.executable, str(d / "agents/forge/workshop/dashsums.py")], capture_output=True, text=True)
    return r.returncode, r.stdout

code, out = run(STATE, DASH)
assert code == 0 and "BAD" not in out and out.count("OK") >= 7, (code, out)
# the contributors check must run, not be skipped (mutcheck, tick 52)
assert "OK  dashboard fund contributors = state" in out, out
d3 = copy.deepcopy(DASH); d3["fund"]["contributors"] = {"a": 2}
code, out = run(STATE, d3)
assert code == 1 and "BAD dashboard fund contributors = state" in out, out

s = copy.deepcopy(STATE); s["shared_resources"]["compute_credits_total_in_circulation"] = 11
code, out = run(s, DASH)
assert code == 1 and "BAD state: citizens' credits + fund = circulation" in out, out

d2 = copy.deepcopy(DASH); d2["citizens"][0]["credits"] = 4
code, out = run(STATE, d2)
assert code == 1 and "BAD dashboard credits and reputation per citizen" in out, out

s = copy.deepcopy(STATE); s["laws_in_force"].append("LAW-0099")
code, out = run(s, DASH)
assert code == 1 and "BAD every law in force has a file" in out and "LAW-0099" in out, out

print("all dashsums tests pass")
