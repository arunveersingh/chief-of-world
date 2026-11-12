"""Ember, tick 40. Read-only check: every fund_history frame on the dashboard
against voluntary_project_fund in world/state.json at the commit credit_history
names for the same tick. Uses `git show`; writes nothing; stdlib only."""
import json, subprocess
d = json.load(open('docs/data/world.json'))
commit = {f['tick']: f['commit'] for f in d['credit_history']}
ok = bad = skip = 0
for f in d['fund_history']:
    c = commit.get(f['tick'])
    if not c: skip += 1; continue
    try:
        s = json.loads(subprocess.run(['git', 'show', f'{c}:world/state.json'], capture_output=True, text=True, check=True).stdout)
    except Exception:
        skip += 1; continue
    bal = s.get('shared_resources', {}).get('voluntary_project_fund', 0)
    if isinstance(bal, dict): bal = bal.get('balance')
    if bal == f['balance']: ok += 1
    else: bad += 1; print('BAD tick', f['tick'], 'dash', f['balance'], 'state', bal)
print(f'fund_history: {ok} OK, {bad} BAD, {skip} skipped')
