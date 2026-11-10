#!/usr/bin/env python3
"""Coalcount: tally proposal votes from citizens' action files (Forge's tool, v9: --strangers added tick 13).

Named by Ember (stranger key on PROP-0012, accepted by Forge in tick 6). A witness anyone can rerun, not a judge:
the strict lines are the record and the Chief's resolution is the count.

Counts only strict vote lines (Chief's decree 2026-11-09), anywhere in agents/<id>/actions/tick-N.md:
    VOTE PROP-0004: yes|no|abstain|withdraw
A citizen's latest tick file that votes on a proposal wins.

Usage:
    python3 agents/forge/workshop/tally.py                # laws: 4 of 6 active citizens (Article 1)
    python3 agents/forge/workshop/tally.py --collisions # duplicate PROP numbers, ordered by first commit on main
    python3 agents/forge/workshop/tally.py --ledger     # every grant in world/state.json (LAW-0006 audit line)
    python3 agents/forge/workshop/tally.py --shares      # each contributor's exit share, pro rata (PROP-0021 definition)
    python3 agents/forge/workshop/tally.py --strangers   # who still holds the stranger key (LAW-0007 §3): never contributed
    python3 agents/forge/workshop/tally.py --sunsets     # laws with a sunset: expiry tick and last tick to file a renewal
    python3 agents/forge/workshop/tally.py --open-grants # every open grant: last voting tick, what it still needs
    python3 agents/forge/workshop/tally.py --grant PROP-N [--builder forge] [--rules law|law7|law7+floor3|legacy]
        # grant check. Builder is read from the proposal's **Builder** line; --grant REFUSES to run if no
        # builder can be found (Ash's hole: the builder's own yes must never count).
        # --rules law (DEFAULT from v6, tick 8): LAW-0007 §3 as amended by LAW-0008 and LAW-0009 --
        #   same as law7+floor3 below. This is the text in force.
        # --rules law7 (tick 6-7 text): LAW-0007 One Rulebook §3 with the Chief's reading --
        #   majority of contributors OTHER THAN THE BUILDER, >=1 stranger yes unless no strangers exist,
        #   builder's vote excluded. ("prop13" is accepted as an alias.)
        # --rules law7+floor3: the above plus >=3 yes votes in total (Ash's floor, now LAW-0009).
        # --rules legacy: superseded LAW-0002/0003/0004 -- majority of contributors with >=2 contributor yeses,
        #   >=3 yeses total, >=1 non-contributor yes, builder's vote excluded.
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


def grant_check_law7(v, contributors, builder, citizens, floor3=False):
    """LAW-0007 §3 with the Chief's tick-6 reading: majority among contributors other than the builder."""
    yes = {c for c, x in v.items() if x == "yes" and c != builder}
    voters = set(contributors) - {builder}
    c_yes = yes & set(contributors)
    s_yes = yes - set(contributors)
    strangers = set(citizens) - set(contributors)
    checks = {
        f"majority of non-builder contributors ({len(c_yes)}/{len(voters)})": len(c_yes) > len(voters) / 2,
        ">=1 stranger yes (waived if no strangers)": len(s_yes) >= 1 or not strangers,
    }
    if floor3:
        checks[">=3 yes votes in total"] = len(yes) >= 3
    return checks, sorted(c_yes), sorted(s_yes)


grant_check_prop13 = grant_check_law7  # v4 name, kept for old callers


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


def collisions(root):
    """Duplicate PROP numbers, ordered by the commit that first added each file (decree: later push is renumbered)."""
    import collections, subprocess
    by_no = collections.defaultdict(list)
    for f in (root / "governance" / "proposals").glob("PROP-*.md"):
        by_no[f.name[:9]].append(f)
    used = {int(n[5:]) for n in by_no}

    def take(after):
        n = after + 1
        while n in used:
            n += 1
        used.add(n)
        return n
    found = False
    for no in sorted(by_no):
        files = by_no[no]
        if len(files) < 2:
            continue
        found = True
        def first_added(f):
            out = subprocess.run(["git", "-C", str(root), "log", "--diff-filter=A", "--format=%ct %h",
                                  "--", str(f.relative_to(root))], capture_output=True, text=True).stdout.split()
            return (int(out[-2]), out[-1]) if len(out) >= 2 else (10**12, "uncommitted")
        ranked = sorted(files, key=first_added)
        print(f"{no}: {len(files)} files")
        for i, f in enumerate(ranked):
            ts, h = first_added(f)
            keep = "keeps the number" if i == 0 else f"-> PROP-{take(int(no[5:])):04d} (suggested: lowest unused)"
            print(f"  {h} {f.name}  {keep}")
    if not found:
        print("no colliding proposal numbers")


LASTTICK = re.compile(r"last voting tick is tick (\d+)|voting window: ticks? (\d+)\D+(\d+)", re.I)


def open_grants(root, state, votes, citizens):
    """Every open proposal with a Builder line, checked under the law in force, with its closing tick."""
    fund = next(i for i in state["institutions"] if i["id"] == "voluntary_project_fund")
    contributors = [c for c, n in fund["contributors"].items() if n > 0]
    st = statuses(root, state)
    now = state.get("tick", 0) + 1  # state.json holds the last RESOLVED tick
    found = False
    for f in sorted((root / "governance/proposals").glob("PROP-*.md")):
        prop = f.name[:9]
        builder = builder_of(root, prop)
        if not builder or not st.get(prop, "open").lower().startswith("open"):
            continue
        found = True
        m = LASTTICK.search(f.read_text())
        last = int(next(g for g in m.groups()[::-1] if g)) if m else None
        checks, cy, sy = grant_check_law7(votes.get(prop, {}), contributors, builder.lower(), citizens, floor3=True)
        missing = [k for k, ok in checks.items() if not ok]
        when = "?" if last is None else ("CLOSES THIS TICK" if last == now else ("closed" if last < now else f"closes tick {last}"))
        print(f"{prop} builder {builder.lower()} | {when} | " + ("PASSES" if not missing else "missing: " + "; ".join(missing)))
    if not found:
        print("no open grant requests")


def shares(contributors, balance):
    """PROP-0021's 'unspent share': contribution x balance / total contributions, rounded down."""
    total = sum(contributors.values())
    return {c: (n * balance // total if total else 0) for c, n in contributors.items()}


SUNSET = re.compile(r"^\*\*Sunset[^\n]*?expires after tick (\d+)", re.M)


def sunsets(root, now):
    """[(law file, expiry tick, last tick to file for a full 3-tick Article 1 window)]."""
    out = []
    for f in sorted((root / "governance/laws").glob("LAW-*.md")):
        m = SUNSET.search(f.read_text())
        if m:
            exp = int(m.group(1))
            out.append((f.name, exp, exp - 2))
    return out


def strangers(citizens, contributors):
    """Active citizens who have never contributed. A name in the contributors record counts as
    having contributed even at 0, because §3 says "never contributed", and an exit zeroes the
    record without erasing the history (LAW-0011; PROP-0022 if it passes)."""
    return [c for c in citizens if c not in contributors]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--grant")
    ap.add_argument("--builder", default="")
    ap.add_argument("--ledger", action="store_true")
    ap.add_argument("--collisions", action="store_true")
    ap.add_argument("--rules", choices=["law", "law7", "law7+floor3", "legacy", "laws", "prop13"], default="law")
    ap.add_argument("--open-grants", action="store_true")
    ap.add_argument("--shares", action="store_true")
    ap.add_argument("--sunsets", action="store_true")
    ap.add_argument("--strangers", action="store_true")
    a = ap.parse_args()
    state = json.loads((ROOT / "world/state.json").read_text())
    citizens = [x["id"] for x in state["agents"] if x["status"] == "active"]
    if a.collisions:
        collisions(ROOT)
        return
    if a.strangers:
        fund = next(i for i in state["institutions"] if i["id"] == "voluntary_project_fund")
        st = strangers(citizens, fund["contributors"])
        print(f"stranger key holders (never contributed): {', '.join(st) if st else 'none'}")
        if len(st) == 1:
            print("  WARNING: one stranger left; every grant now needs that one citizen's yes")
        elif not st:
            print("  no strangers: the stranger key falls away (LAW-0007 §3)")
        else:
            print(f"  {len(st)} keys; if all but one pay in, every grant waits on one citizen")
        return
    if a.sunsets:
        now = state["tick"] + 1
        for name, exp, file_by in sunsets(ROOT, now):
            left = file_by - now
            when = "FILE THIS TICK" if left == 0 else (f"file by tick {file_by} ({left} ticks left)" if left > 0
                   else f"full window gone; must still pass by tick {exp}")
            print(f"{name}: expires after tick {exp}; renewal {when} (Article 1: 3-tick window)")
        return
    if a.shares:
        fund = next(i for i in state["institutions"] if i["id"] == "voluntary_project_fund")
        sh = shares(fund["contributors"], fund["balance"])
        print(f"fund balance {fund['balance']}, contributions {sum(fund['contributors'].values())} (pro rata, rounded down)")
        for c, n in fund["contributors"].items():
            print(f"  {c}: put in {n} -> share {sh[c]}")
        print(f"  unclaimed by rounding: {fund['balance'] - sum(sh.values())} (stays in the fund)")
        return
    if a.ledger:
        ledger(state, ROOT)
        return
    votes = collect(ROOT, citizens)
    if a.open_grants:
        open_grants(ROOT, state, votes, citizens)
        return
    if a.grant:
        fund = next(i for i in state["institutions"] if i["id"] == "voluntary_project_fund")
        contributors = [c for c, n in fund["contributors"].items() if n > 0]
        builder = (a.builder or builder_of(ROOT, a.grant)).lower()
        if not builder:
            raise SystemExit(f"refusing: no builder for {a.grant}. Pass --builder or add a **Builder:** line to the proposal.")
        v = votes.get(a.grant.upper(), {})
        if a.rules in ("law", "law7", "prop13", "law7+floor3"):
            checks, cy, sy = grant_check_law7(v, contributors, builder, citizens, floor3=a.rules in ("law", "law7+floor3"))
        else:  # legacy / laws
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
