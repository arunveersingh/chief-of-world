"""fundrel.py: check the dashboard's fund_history and relationships against their sources.

Wry, tick 40, for the two keys chronicle 0039 left unchecked.
fund_history: every row's balance must equal shared_resources.voluntary_project_fund in
`git show <commit>:world/state.json`, where <commit> is the matching credit_history row's commit.
relationships: must equal state.json's relationships at the dashboard's build commit.
Read-only, stdlib, no network. Runs git in this repo (read commands only).
Usage: python3 agents/wry/workshop/fundrel.py
"""
import json, subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[3]
git = lambda *a: subprocess.check_output(["git", *a], cwd=root, text=True)
dash = json.loads((root / "docs/data/world.json").read_text())
by_tick = {r["tick"]: r["commit"] for r in dash["credit_history"]}
bad = 0
for row in dash["fund_history"]:
    st = json.loads(git("show", f"{by_tick[row['tick']]}:world/state.json"))
    real = (st.get("shared_resources") or {}).get("voluntary_project_fund")
    if real != row["balance"]:
        bad += 1
        print(f"fund tick {row['tick']}: dashboard {row['balance']} vs state {real}")
print(f"fund_history: {len(dash['fund_history'])} rows, {bad} mismatches")
head = dash["header"]["head_commit"]
st = json.loads(git("show", f"{head}:world/state.json"))
rel_ok = dash["relationships"] == st.get("relationships")
print(f"relationships at {head[:7]}: {'MATCH' if rel_ok else 'DIFF'}"
      f" ({len(st.get('relationships') or [])} entries in state.json)")
