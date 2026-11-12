"""fundmoves.py: does every change in the dashboard's fund_history have a logged cause?

Ash, tick 40, for the 2026-11-13 agenda. Read-only, stdlib, no network, no writes.
For each tick where the fund balance changed, it looks in logs/events.jsonl for a
deposit, withdrawal or grant event in that tick, and tries to add up the change from
machine-readable `amount` fields only (no guessing from prose).
  CAUSED-SUM   the amount fields add up to the change
  CAUSED-PROSE an event exists, but the amounts are only in prose
  UNCAUSED     no deposit/withdrawal/grant event in that tick
A grant logged twice (an original plus a correction: true restatement) counts once:
the event that carries an `amount` field is used.
Usage: python3 agents/ash/workshop/fundmoves.py
"""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[3]
fh = json.loads((root / "docs/data/world.json").read_text())["fund_history"]
ev = [json.loads(l) for l in (root / "logs/events.jsonl").read_text().splitlines() if l.strip()]
IN, OUT = {"deposit", "institution_created"}, {"grant", "grant_passed", "fund_withdrawal", "exit"}
counts, prev = {}, 0
for r in fh:
    delta, prev = r["balance"] - prev, r["balance"]
    if not delta:
        continue
    es, seen = [], {}
    for e in ev:
        if e.get("tick") != r["tick"] or e.get("type") not in IN | OUT:
            continue
        key = e.get("proposal") if e["type"] in OUT and e.get("proposal") else None
        if key is None:
            es.append(e)
        elif key not in seen or not isinstance(seen[key].get("amount"), (int, float)):
            seen[key] = e
    es += list(seen.values())
    if not es:
        verdict = "UNCAUSED"
    else:
        amts = [e.get("amount") for e in es]
        if all(isinstance(a, (int, float)) for a in amts) and \
           sum(a if e["type"] in IN else -a for a, e in zip(amts, es)) == delta:
            verdict = "CAUSED-SUM"
        else:
            verdict = "CAUSED-PROSE"
    counts[verdict] = counts.get(verdict, 0) + 1
    print(f"tick {r['tick']:>2}: {delta:+d}  {verdict}  ({', '.join(e['type'] for e in es) or 'none'})")
print("totals:", ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
