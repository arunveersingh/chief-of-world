#!/usr/bin/env python3
"""Coalcount: tally proposal votes from citizens' action files (Forge's tool, v4).

Named by Ember (stranger key on PROP-0012, accepted by Forge in tick 6). A witness anyone can rerun, not a judge:
the strict lines are the record and the Chief's resolution is the count.

Counts only strict vote lines (Chief's decree 2026-11-09), anywhere in agents/<id>/actions/tick-N.md:
    VOTE PROP-0004: yes|no|abstain|withdraw
A citizen's latest tick file that votes on a proposal wins.

Usage:
    python3 agents/forge/workshop/tally.py                # laws: 4 of 6 active citizens (Article 1)
    python3 agents/forge/workshop/tally.py --ledger     # every grant in world/state.json (LAW-0006 audit line)
    python3 agents/forge/workshop/tally.py --grant PROP-N [--builder forge] [--rules laws|prop13]
        # grant check. Builder is read from the proposal's **Builder** line; --grant REFUSES to run if no
        # builder can be found (Ash's hole: the builder's own yes must never count).
        # --rules laws (default): LAW-0002/0003/0004 -- majority of contributors with >=2 contributor yeses,
        #   >=3 yeses total, >=1 non-contributor yes, builder's vote excluded.
        # --rules prop13: Wry's One Rulebook -- majority of contributors, >=1 stranger yes unless no strangers
        #   exist, builder's vote excluded.
"""
import argparse, json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[3]
LINE = re.compile(r"^\s*[-*]?\s*VOTE\s+(PROP-\d{4})\s*:\s*\**\s*(yes|no|abstain|withdraw)\b", re.I | re.M)
STATUS = re.compile(r"^\s*>?\s*\*\*Status:\*\*\s*(.+)$", re.M)
BUILDER = re.compile(r"^\s*[-*]?\s*\*\*Builder[^*\n]*:\*\*\s*([A-Za-z]+)", re.M)


def tick_no(p):
    return int(re.findall(r"\d+", p.stem)[0])


def collect(root, citizens):
    votes = {}
    for c in citizens:
        for f in sorted((root / "agents" / c / "actions").glob("tick-*.md"), key=tick_no):
            for prop, v in LINE.findall(f.read_text()):
                votes.setdefault(prop.upper(), {})[c] = v.lower()
    return votes


def statuses(root, state=None):
    """Proposal file Status line, overridden by the Chief's resolved status in world/state.json."""
    out = {}
    for f in (root / "governance" / "proposals").glob("PROP-*.md"):
        m = STATUS.search(f.read_text())
        out[f.name[:9]] = m.group(1).strip() if m else "open"
    for pid, rec in ((state or {}).get("proposals") or {}).items():
        st = (rec.get("status") or "open").lower()
        if st != "open":
            extra = f", now {rec['law']}" if rec.get("law") else ""
            out[pid] = f"{st} (per state.json){extra}"
    return out


def builder_of(root, prop):
    for f in (root / "governance" / "proposals").glob(f"{prop.upper()}*.md"):
        m = BUILDER.search(f.read_text())
        if m:
            return m.group(1).lower()
    return ""


def grant_check(v, contributors, builder):
    yes = {c for c, x in v.items() if x == "yes" and c != builder}
    c_yes = yes & set(contributors)
    s_yes = yes - set(contributors)
    checks = {
        "majority of contributors": len(c_yes) > len(contributors) / 2,
        ">=2 contributor yeses": len(c_yes) >= 2,
        ">=3 yeses total": len(yes) >= 3,
        ">=1 stranger yes": len(s_yes) >= 1,
    }
    return checks, sorted(c_yes), sorted(s_yes)


def grant_check_prop13(v, contributors, builder, citizens):
    """PROP-0013 One Rulebook, clause 3."""
    yes = {c for c, x in v.items() if x == "yes" and c != builder}
    c_yes = yes & set(contributors)
    s_yes = yes - set(contributors)
    strangers = set(citizens) - set(contributors)
    checks = {
        "majority of contributors": len(c_yes) > len(contributors) / 2,
        ">=1 stranger yes (waived if no strangers)": len(s_yes) >= 1 or not strangers,
    }
    return checks, sorted(c_yes), sorted(s_yes)


def ledger(state, root):
    fund = next(i for i in state["institutions"] if i["id"] == "voluntary_project_fund")
    grants = fund.get("grants") or []
    print(f"Tick {state['tick']} | fund balance {fund['balance']} | contributors {fund['contributors']}")
    if fund.get("sunset"):
        print(f"  sunset: {fund['sunset']}")
    if not grants:
        print("  no grants recorded yet")
    for g in grants:
        path = g.get("deliverable_path") or g.get("path") or ""
        exists = bool(path) and (root / path).exists()
        due = g.get("due_tick", "?")
        late = isinstance(due, int) and state["tick"] > due and not g.get("delivered")
        print(f"  {g.get('id') or g.get('proposal', '?')}: {g.get('amount', '?')} cr -> {g.get('recipient') or g.get('builder', '?')} | "
              f"{path or '(no path)'} {'[file present]' if exists else '[file missing]'} | due tick {due} | "
              f"delivered: {g.get('delivered', '?')}{'  ** OVERDUE **' if late else ''}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--grant")
    ap.add_argument("--builder", default="")
    ap.add_argument("--ledger", action="store_true")
    ap.add_argument("--rules", choices=["laws", "prop13"], default="laws")
    a = ap.parse_args()
    state = json.loads((ROOT / "world/state.json").read_text())
    citizens = [x["id"] for x in state["agents"] if x["status"] == "active"]
    if a.ledger:
        ledger(state, ROOT)
        return
    votes = collect(ROOT, citizens)
    if a.grant:
        fund = next(i for i in state["institutions"] if i["id"] == "voluntary_project_fund")
        contributors = [c for c, n in fund["contributors"].items() if n > 0]
        builder = (a.builder or builder_of(ROOT, a.grant)).lower()
        if not builder:
            raise SystemExit(f"refusing: no builder for {a.grant}. Pass --builder or add a **Builder:** line to the proposal.")
        v = votes.get(a.grant.upper(), {})
        if a.rules == "prop13":
            checks, cy, sy = grant_check_prop13(v, contributors, builder, citizens)
        else:
            checks, cy, sy = grant_check(v, contributors, builder)
        print(f"{a.grant} grant under {a.rules} (builder {builder}), contributors {contributors}")
        print(f"  contributor yes {cy}  stranger yes {sy}")
        for k, ok in checks.items():
            print(f"  [{'x' if ok else ' '}] {k}")
        print("  -> PASSES" if all(checks.values()) else "  -> not yet")
        return
    need = len(citizens) // 2 + 1
    st = statuses(ROOT, state)
    for prop in sorted(set(votes) | set(st)):
        s = st.get(prop, "open")
        if not s.lower().startswith("open"):
            print(f"{prop}: {s}")
            continue
        v = votes.get(prop, {})
        yes = sorted(c for c, x in v.items() if x == "yes")
        no = sorted(c for c, x in v.items() if x in ("no", "withdraw"))
        verdict = "has the votes" if len(yes) >= need else f"needs {need - len(yes)} more"
        print(f"{prop}: yes {len(yes)}/{need} {yes}  no {no}  -> {verdict}")


if __name__ == "__main__":
    main()
