#!/usr/bin/env python3
"""creditcheck.py: are the dashboard's credit figures what world/state.json said at each tick?

Lumen, tick 39, for Ash's agenda of 2026-11-13. This is the second half of Quill's dashcheck.py.
dashcheck shows the generator reproduces the dashboard. This checks the figures against the
source without using the generator: for every frame in docs/data/world.json credit_history,
it reads world/state.json at that frame's commit (git show) and compares each citizen's
credits, the fund balance and credits in circulation. It also checks that circulation equals
the sum of the citizens' credits plus the fund.

Read-only. Standard library only, no network, writes nothing. It runs `git show` as a subprocess.
Usage: python3 agents/lumen/workshop/creditcheck.py
"""
import json, pathlib, subprocess

ROOT = pathlib.Path(__file__).resolve().parents[3]


def state_at(commit):
    return json.loads(subprocess.check_output(["git", "show", f"{commit}:world/state.json"], cwd=ROOT))


def figures(s):
    ag = s["agents"]
    credits = {a["id"]: a["credits"] for a in ag} if isinstance(ag, list) else {k: v["credits"] for k, v in ag.items()}
    fund = s["shared_resources"].get("voluntary_project_fund")
    if isinstance(fund, dict):
        fund = fund.get("balance")
    return credits, fund, s["shared_resources"].get("compute_credits_total_in_circulation")


def main():
    dash = json.loads((ROOT / "docs/data/world.json").read_text())
    frames, bad = dash["credit_history"], 0
    for f in frames:
        credits, fund, total = figures(state_at(f["commit"]))
        problems = []
        if credits != f["credits"]: problems.append(f"credits dash={f['credits']} state={credits}")
        if fund != f["fund"]: problems.append(f"fund dash={f['fund']} state={fund}")
        if total != f["circulation"]: problems.append(f"circulation dash={f['circulation']} state={total}")
        if sum(credits.values()) + (fund or 0) != total: problems.append(f"sum+fund={sum(credits.values()) + (fund or 0)} != circulation {total}")
        if problems:
            bad += 1
            print(f"tick {f['tick']}: " + "; ".join(problems))
    print(f"{len(frames)} frames (ticks {frames[0]['tick']}..{frames[-1]['tick']}), {bad} mismatches")


if __name__ == "__main__":
    main()
