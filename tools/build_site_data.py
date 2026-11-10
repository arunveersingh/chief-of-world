#!/usr/bin/env python3
"""Build docs/data/world.json for the public World dashboard.

Run from the repository root (or anywhere; the script finds the repo):

    python3 tools/build_site_data.py

The World tick routine should run this after it finishes resolving and
opening a tick, then commit the updated docs/data/world.json (and
docs/data/index.json) along with the rest of the tick, or immediately
after. The dashboard at GitHub Pages stays current by fetching this
file (and the live world/*.json files) from raw.githubusercontent.com,
so a regenerate + push is what refreshes the complete picture.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

IST = timezone(timedelta(hours=5, minutes=30), name="Asia/Calcutta")
REPO_OWNER = "arunveersingh"
REPO_NAME = "chief-of-world"
BRANCH = "main"
BLOB_BASE = f"https://github.com/{REPO_OWNER}/{REPO_NAME}/blob/{BRANCH}/"
RAW_BASE = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH}/"

VOTE_RE = re.compile(
    r"^VOTE\s+(PROP-\d+)\s*:\s*(yes|no|abstain|withdraw)\b",
    re.IGNORECASE | re.MULTILINE,
)
HEADLINE_RE = re.compile(r"^\*\*Headline:\*\*\s*(.+)$", re.MULTILINE | re.IGNORECASE)
TICK_META_RE = re.compile(r"^\*\*Tick:\*\*\s*(.+)$", re.MULTILINE)
DATE_META_RE = re.compile(r"^\*\*World date:\*\*\s*(.+)$", re.MULTILINE)
TITLE_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
SUNSET_TICK_RE = re.compile(
    r"expires?\s+(?:six ticks after it passes, i\.e\. )?after tick\s+(\d+)|"
    r"sunset[^\n.]{0,80}tick\s+(\d+)|"
    r"expire(?:s| at the end of)?\s+tick\s+(\d+)",
    re.IGNORECASE,
)


def repo_root() -> Path:
    here = Path(__file__).resolve()
    return here.parent.parent


def run(cmd: list[str], cwd: Path) -> str:
    return subprocess.check_output(cmd, cwd=cwd, text=True).rstrip("\n")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def now_ist() -> datetime:
    return datetime.now(tz=IST)


def to_ist_iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(IST).isoformat()


def format_ist(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    local = dt.astimezone(IST)
    return local.strftime("%Y-%m-%d %H:%M IST (Asia/Calcutta)")


def parse_git_iso(value: str) -> datetime:
    # git %cI is ISO-8601
    return datetime.fromisoformat(value)


def collapse(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def first_paragraphs(text: str, limit: int = 420) -> str:
    lines = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            if lines:
                break
            continue
        if line.startswith("#") or line.startswith("---"):
            continue
        if line.startswith("|"):
            continue
        lines.append(line)
        joined = collapse(" ".join(lines))
        if len(joined) >= limit:
            break
    joined = collapse(" ".join(lines))
    if len(joined) > limit:
        cut = joined[: limit - 1].rsplit(" ", 1)[0]
        return cut + "…"
    return joined


def section_after(text: str, heading: str) -> str:
    pattern = re.compile(
        rf"^##[^\n]*{re.escape(heading)}[^\n]*\n(.*?)(?=^##\s|\Z)",
        re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def extract_action(text: str, agent_id: str, tick: int) -> dict:
    votes = {m.group(1).upper(): m.group(2).lower() for m in VOTE_RE.finditer(text)}
    # Prefer a public-statement style section
    body = ""
    for heading in (
        "Public statement",
        "What I say",
        "Statement",
        "What I did",
    ):
        body = section_after(text, heading)
        if body:
            break
    if not body:
        # Some files use bold "Public statement" without ##
        m = re.search(
            r"\*\*Public statement\*\*\s*(.*?)(?=^\*\*Actions\*\*|^##\s|\*\*Votes\*\*|\Z)",
            text,
            re.IGNORECASE | re.DOTALL | re.MULTILINE,
        )
        if m:
            body = m.group(1).strip()
    if not body:
        # Fall back to text after the title
        parts = text.split("\n", 1)
        body = parts[1] if len(parts) > 1 else text
    # Drop fenced code from the excerpt
    body = re.sub(r"```.*?```", " ", body, flags=re.DOTALL)
    summary = first_paragraphs(body, 320)
    return {
        "tick": tick,
        "file": f"agents/{agent_id}/actions/tick-{tick}.md",
        "summary": summary,
        "votes": votes,
        "url": BLOB_BASE + f"agents/{agent_id}/actions/tick-{tick}.md",
    }


def parse_law(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    title_line = TITLE_RE.search(text)
    title = title_line.group(1).strip() if title_line else path.stem
    law_id_match = re.match(r"(LAW-\d+)", path.name)
    law_id = law_id_match.group(1) if law_id_match else path.stem
    # Clean "LAW-0001 — Recording Rule" -> title "Recording Rule"
    short = re.sub(r"^LAW-\d+\s+[—-]\s*", "", title).strip()
    superseded = bool(re.search(r"^\s*>\s*\*\*Superseded\*\*", text, re.MULTILINE | re.IGNORECASE))
    passed = None
    m = re.search(r"\*\*Passed:\*\*\s*(.+)", text)
    if m:
        passed = collapse(m.group(1))
    vote = None
    m = re.search(r"\*\*Vote:\*\*\s*(.+)", text)
    if m:
        vote = collapse(m.group(1))
    sunset_tick = None
    sunset_note = None
    # Only honor an explicit **Sunset...:** line about this law itself.
    # Do not scrape commentary about other laws' sunsets (e.g. LAW-0006's
    # note that the old grant rules would have expired at tick 9).
    sm = re.search(r"\*\*Sunset[^*]*:\*\*\s*(.+)", text)
    if sm:
        sunset_note = collapse(sm.group(1))
        tm = re.search(r"tick\s+(\d+)", sunset_note, re.IGNORECASE)
        if tm:
            sunset_tick = int(tm.group(1))
    return {
        "id": law_id,
        "title": short,
        "file": str(path.as_posix()).split("chief-of-world/")[-1] if False else f"governance/laws/{path.name}",
        "url": BLOB_BASE + f"governance/laws/{path.name}",
        "passed": passed,
        "vote": vote,
        "superseded": superseded,
        "sunset_tick": sunset_tick,
        "sunset_note": sunset_note,
        "excerpt": first_paragraphs(re.sub(r"^#.*\n", "", text, count=1), 280),
    }


def parse_chronicle(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    name = path.name
    tick = None
    if name.startswith("0000"):
        tick = 0
    else:
        m = re.search(r"tick-(\d+)", name)
        if m:
            tick = int(m.group(1))
    title_line = TITLE_RE.search(text)
    title = title_line.group(1).strip() if title_line else name
    headline = None
    hm = HEADLINE_RE.search(text)
    if hm:
        headline = collapse(hm.group(1))
    world_date = None
    dm = DATE_META_RE.search(text)
    if dm:
        world_date = collapse(dm.group(1))
    changed = section_after(text, "What changed")
    if changed:
        excerpt = first_paragraphs(changed, 480)
        excerpt_source = "what_changed"
    else:
        # Skip metadata lines at the top
        body = text
        body = re.sub(r"^#.*\n", "", body, count=1)
        body = re.sub(r"^\*\*[^*]+\*\*.*\n", "", body, flags=re.MULTILINE)
        body = re.sub(r"^---\s*$", "", body, flags=re.MULTILINE)
        excerpt = first_paragraphs(body, 420)
        excerpt_source = "opening"
    return {
        "tick": tick,
        "file": f"chronicle/{name}",
        "url": BLOB_BASE + f"chronicle/{name}",
        "title": title,
        "headline": headline,
        "world_date": world_date,
        "excerpt": excerpt,
        "excerpt_source": excerpt_source,
    }


def credit_and_fund_history(root: Path) -> tuple[list, list]:
    log = run(
        ["git", "log", "--pretty=%H %cI %s", "--", "world/state.json"],
        root,
    )
    latest_for_tick = {}
    for line in log.splitlines():
        if not line.strip():
            continue
        sha, rest = line.split(" ", 1)
        iso, _, subject = rest.partition(" ")
        try:
            blob = run(["git", "show", f"{sha}:world/state.json"], root)
        except subprocess.CalledProcessError:
            continue
        try:
            state = json.loads(blob)
        except json.JSONDecodeError:
            continue
        tick = state.get("tick")
        if tick is None:
            continue
        # log is newest-first; first time we see a tick is the post-resolve snapshot
        if tick in latest_for_tick:
            continue
        agents = {a["id"]: a.get("credits") for a in state.get("agents", [])}
        resources = state.get("shared_resources", {}) or {}
        fund = resources.get("voluntary_project_fund")
        circ = resources.get("compute_credits_total_in_circulation")
        dt = parse_git_iso(iso)
        latest_for_tick[tick] = {
            "tick": tick,
            "commit": sha,
            "at": to_ist_iso(dt),
            "at_ist": format_ist(dt),
            "subject": subject,
            "credits": agents,
            "fund": fund,
            "circulation": circ,
        }
    credits = [latest_for_tick[t] for t in sorted(latest_for_tick)]
    fund_hist = [
        {
            "tick": row["tick"],
            "balance": row["fund"],
            "at": row["at"],
            "at_ist": row["at_ist"],
        }
        for row in credits
        if row["fund"] is not None
    ]
    return credits, fund_hist


def recent_commits(root: Path, n: int = 20) -> list:
    log = run(
        ["git", "log", f"-{n}", "--pretty=%H%x09%cI%x09%s"],
        root,
    )
    out = []
    for line in log.splitlines():
        if not line.strip():
            continue
        sha, iso, subject = line.split("\t", 2)
        dt = parse_git_iso(iso)
        out.append(
            {
                "sha": sha,
                "short": sha[:7],
                "at": to_ist_iso(dt),
                "at_ist": format_ist(dt),
                "subject": subject,
                "url": f"https://github.com/{REPO_OWNER}/{REPO_NAME}/commit/{sha}",
            }
        )
    return out


def participation(root: Path, citizen_ids: list[str], open_tick: int) -> dict:
    # Independent citizen ticks start at 2. Tick 1 was played by the Chief
    # on everyone's behalf; count it as present for all founders.
    independent = list(range(2, max(open_tick, 1) + 1))
    result = {}
    for cid in citizen_ids:
        ticks = []
        for t in independent:
            if (root / "agents" / cid / "actions" / f"tick-{t}.md").is_file():
                ticks.append(t)
        # Tick 1: all six founders were present (no per-citizen action files)
        present_including_tick1 = ([1] if open_tick >= 1 else []) + ticks
        expected = (1 if open_tick >= 1 else 0) + len(independent)
        result[cid] = {
            "ticks_filed": ticks,
            "ticks_present": present_including_tick1,
            "filed_count": len(ticks),
            "present_count": len(present_including_tick1),
            "expected_count": expected,
        }
    return result


def latest_action(root: Path, cid: str, open_tick: int, resolved_tick: int):
    for t in range(max(open_tick, resolved_tick, 0), 1, -1):
        path = root / "agents" / cid / "actions" / f"tick-{t}.md"
        if path.is_file():
            return extract_action(path.read_text(encoding="utf-8"), cid, t)
    return None


def provisional_votes(root: Path, open_tick: int, citizen_ids: list[str]) -> dict:
    """Votes written in the still-open tick, not yet official."""
    tallies = defaultdict(lambda: {"yes": [], "no": [], "abstain": [], "withdraw": [], "source": []})
    for cid in citizen_ids:
        path = root / "agents" / cid / "actions" / f"tick-{open_tick}.md"
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        found = list(VOTE_RE.finditer(text))
        if not found:
            continue
        for m in found:
            prop, vote = m.group(1).upper(), m.group(2).lower()
            if cid not in tallies[prop][vote]:
                tallies[prop][vote].append(cid)
            src = f"agents/{cid}/actions/tick-{open_tick}.md"
            if src not in tallies[prop]["source"]:
                tallies[prop]["source"].append(src)
    return {
        k: v
        for k, v in tallies.items()
    }


def load_events(root: Path) -> list:
    path = root / "logs" / "events.jsonl"
    if not path.is_file():
        return []
    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def parse_decrees(root: Path) -> dict:
    path = root / "chronicle" / "chief" / "DECREES.md"
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    return {
        "file": "chronicle/chief/DECREES.md",
        "url": BLOB_BASE + "chronicle/chief/DECREES.md",
        "markdown": text,
    }


def parse_reviews(root: Path) -> list:
    folder = root / "chronicle" / "chief"
    reviews = []
    if not folder.is_dir():
        return reviews
    for path in sorted(folder.glob("????-??-??.md"), reverse=True):
        text = path.read_text(encoding="utf-8")
        reviews.append(
            {
                "date": path.stem,
                "file": f"chronicle/chief/{path.name}",
                "url": BLOB_BASE + f"chronicle/chief/{path.name}",
                "markdown": text,
                "excerpt": first_paragraphs(
                    section_after(text, "Assessment") or text, 520
                ),
            }
        )
    return reviews


def proposal_records(state: dict) -> list:
    raw = state.get("proposals") or {}
    items = []
    for prop_id, meta in raw.items():
        if not isinstance(meta, dict):
            continue
        rec = {"id": prop_id, **meta}
        rec.setdefault("yes", [])
        rec.setdefault("no", [])
        rec.setdefault("abstain", [])
        if rec.get("file"):
            rec["url"] = BLOB_BASE + rec["file"]
        items.append(rec)
    def sort_key(item):
        m = re.search(r"(\d+)", item["id"])
        return int(m.group(1)) if m else 0
    items.sort(key=sort_key, reverse=True)
    return items


def fund_record(state: dict) -> dict | None:
    for inst in state.get("institutions") or []:
        if inst.get("id") == "voluntary_project_fund":
            return inst
    # Fallback from shared_resources
    resources = state.get("shared_resources") or {}
    if "voluntary_project_fund" in resources:
        return {
            "id": "voluntary_project_fund",
            "balance": resources.get("voluntary_project_fund"),
        }
    return None


def build(root: Path) -> dict:
    state = read_json(root / "world" / "state.json")
    budget = read_json(root / "world" / "budget.json")
    activity = read_json(root / "world" / "activity.json")
    citizens_meta = read_json(root / "world" / "citizens.json")

    resolved_tick = int(state.get("tick") or 0)
    open_tick = citizens_meta.get("open_tick")
    if open_tick is not None:
        open_tick = int(open_tick)

    agents = state.get("agents") or []
    citizen_ids = [a["id"] for a in agents]
    part = participation(root, citizen_ids, open_tick or resolved_tick)

    citizens = []
    for agent in agents:
        cid = agent["id"]
        last = latest_action(root, cid, open_tick or resolved_tick, resolved_tick)
        p = part.get(cid, {})
        expected = p.get("expected_count") or 0
        present = p.get("present_count") or 0
        citizens.append(
            {
                "id": cid,
                "name": agent.get("name") or cid.title(),
                "status": agent.get("status") or "unknown",
                "credits": agent.get("credits"),
                "reputation": agent.get("reputation"),
                "last_action": last,
                "participation": p,
                "participation_rate": (present / expected) if expected else None,
                "profile_url": BLOB_BASE + f"agents/{cid}/profile.md",
                "memory_url": BLOB_BASE + f"agents/{cid}/memory.md",
            }
        )

    laws_dir = root / "governance" / "laws"
    laws = []
    if laws_dir.is_dir():
        for path in sorted(laws_dir.glob("LAW-*.md")):
            laws.append(parse_law(path))
    in_force = set(state.get("laws_in_force") or [])
    superseded_map = state.get("laws_superseded") or {}
    for law in laws:
        law["in_force"] = law["id"] in in_force
        if law["id"] in superseded_map:
            law["superseded_by"] = superseded_map[law["id"]]
            law["superseded"] = True

    chronicles = []
    chronicle_dir = root / "chronicle"
    if chronicle_dir.is_dir():
        for path in sorted(chronicle_dir.glob("0*.md")):
            chronicles.append(parse_chronicle(path))
    extinction = None
    ext_path = chronicle_dir / "EXTINCTION.md"
    if ext_path.is_file():
        text = ext_path.read_text(encoding="utf-8")
        extinction = {
            "file": "chronicle/EXTINCTION.md",
            "url": BLOB_BASE + "chronicle/EXTINCTION.md",
            "markdown": text,
            "excerpt": first_paragraphs(text, 400),
        }

    inactive = int(activity.get("consecutive_inactive_days") or 0)
    threshold = 7
    agent_statuses = {a.get("status") for a in agents}
    if extinction or inactive >= threshold or "extinct" in agent_statuses:
        world_status = "extinct"
    elif inactive > 0:
        world_status = "at_risk"
    else:
        world_status = "alive"

    credit_hist, fund_hist = credit_and_fund_history(root)
    sha = run(["git", "rev-parse", "HEAD"], root)
    sha_short = sha[:7]
    commit_dt = parse_git_iso(run(["git", "log", "-1", "--pretty=%cI"], root))
    generated = now_ist()

    resources = state.get("shared_resources") or {}

    header = {
        "resolved_tick": resolved_tick,
        "open_tick": open_tick,
        "world_date": state.get("world_date"),
        "timezone": state.get("timezone") or "Asia/Calcutta",
        "ticks_used_today": budget.get("ticks_used_today"),
        "max_ticks_per_day": budget.get("max_ticks_per_day"),
        "budget_date": budget.get("date"),
        "budget_history": budget.get("history") or [],
        "last_meaningful_commit": activity.get("last_meaningful_commit"),
        "last_youtube_upload": activity.get("last_youtube_upload"),
        "consecutive_inactive_days": inactive,
        "extinction_threshold": threshold,
        "days_until_extinction": max(0, threshold - inactive),
        "status": world_status,
        "credits_in_circulation": resources.get("compute_credits_total_in_circulation"),
        "fund_balance": resources.get("voluntary_project_fund"),
        "resource_notes": resources.get("resource_notes"),
        "activity_notes": activity.get("notes"),
        "head_commit": sha,
        "head_commit_short": sha_short,
        "head_commit_at": to_ist_iso(commit_dt),
        "head_commit_at_ist": format_ist(commit_dt),
        "head_commit_url": f"https://github.com/{REPO_OWNER}/{REPO_NAME}/commit/{sha}",
    }

    data = {
        "generated_at": to_ist_iso(generated),
        "generated_at_ist": format_ist(generated),
        "repo": {
            "owner": REPO_OWNER,
            "name": REPO_NAME,
            "branch": BRANCH,
            "url": f"https://github.com/{REPO_OWNER}/{REPO_NAME}",
            "blob_base": BLOB_BASE,
            "raw_base": RAW_BASE,
            "pages_url": f"https://{REPO_OWNER}.github.io/{REPO_NAME}/",
        },
        "header": header,
        "citizens": citizens,
        "credit_history": credit_hist,
        "fund_history": fund_hist,
        "fund": fund_record(state),
        "laws": laws,
        "laws_in_force": state.get("laws_in_force") or [],
        "laws_superseded": superseded_map,
        "proposals": proposal_records(state),
        "passage_rule": state.get("passage_rule"),
        "provisional_votes": provisional_votes(
            root, open_tick or resolved_tick, citizen_ids
        ) if open_tick and open_tick > resolved_tick else {},
        "provisional_votes_tick": open_tick if open_tick and open_tick > resolved_tick else None,
        "open_questions": state.get("open_questions") or [],
        "relationships": state.get("relationships") or {},
        "tools": state.get("tools") or [],
        "timeline": chronicles,
        "extinction": extinction,
        "decrees": parse_decrees(root),
        "chief_reviews": parse_reviews(root),
        "events": load_events(root),
        "commits": recent_commits(root, 20),
        "links": {
            "constitution": BLOB_BASE + "CONSTITUTION.md",
            "tick_protocol": BLOB_BASE + "TICK_PROTOCOL.md",
            "readme": BLOB_BASE + "README.md",
            "decrees": BLOB_BASE + "chronicle/chief/DECREES.md",
            "youtube": "https://www.youtube.com/@howworldswork",
        },
    }
    attach_personas(data["citizens"])
    data["repo"]["pages_url"] = "https://reasonfrom.com/chief-of-world/"
    data["derived"] = compute_derived(data)
    return data


def main() -> int:
    root = repo_root()
    data = build(root)
    out_dir = root / "docs" / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    world_path = out_dir / "world.json"
    index_path = out_dir / "index.json"
    world_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    index = {
        "world": "docs/data/world.json",
        "generated_at": data["generated_at"],
        "generated_at_ist": data["generated_at_ist"],
        "live": {
            "state": "world/state.json",
            "budget": "world/budget.json",
            "activity": "world/activity.json",
            "citizens": "world/citizens.json",
        },
        "raw_base": RAW_BASE,
        "blob_base": BLOB_BASE,
    }
    index_path.write_text(
        json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    header = data["header"]
    print(
        f"Wrote {world_path.relative_to(root)} and {index_path.relative_to(root)} "
        f"(resolved tick {header['resolved_tick']}, open tick {header['open_tick']}, "
        f"status {header['status']})"
    )
    return 0

# ---------------------------------------------------------------------------
# Derived insights for the visual dashboard
# ---------------------------------------------------------------------------

PERSONAS = {
    "ember": {"glyph": "🔥", "color": "#ff6b2d", "tagline": "keeps the surplus"},
    "lumen": {"glyph": "☀️", "color": "#ffd166", "tagline": "wants a commons"},
    "wry": {"glyph": "🃏", "color": "#2ec4b6", "tagline": "tests the edges"},
    "quill": {"glyph": "🪶", "color": "#c77dff", "tagline": "writes it down"},
    "forge": {"glyph": "⚒️", "color": "#e09f3e", "tagline": "ships the tool"},
    "ash": {"glyph": "🪨", "color": "#8fa6b8", "tagline": "tests the claim"},
}


def attach_personas(citizens: list) -> None:
    for c in citizens:
        persona = PERSONAS.get(c["id"], {"glyph": "✦", "color": "#e0b04a", "tagline": ""})
        c["glyph"] = persona["glyph"]
        c["color"] = persona["color"]
        c["tagline"] = persona["tagline"]


def gini(values) -> float:
    xs = sorted(float(v) for v in values if v is not None)
    n = len(xs)
    if n == 0:
        return 0.0
    total = sum(xs)
    if total == 0:
        return 0.0
    acc = 0.0
    for i, x in enumerate(xs, 1):
        acc += i * x
    return round((2 * acc) / (n * total) - (n + 1) / n, 4)


def law_passed_tick(law: dict) -> int | None:
    if law.get("passed_tick") is not None:
        try:
            return int(law["passed_tick"])
        except (TypeError, ValueError):
            pass
    if law.get("passed"):
        m = re.search(r"Tick\s+(\d+)", str(law["passed"]), re.IGNORECASE)
        if m:
            return int(m.group(1))
    return None


def parse_amount_agent(event: dict) -> tuple[str | None, int | None]:
    agent = event.get("agent") or event.get("builder") or event.get("recipient")
    amount = event.get("amount")
    if amount is not None:
        try:
            amount = int(amount)
        except (TypeError, ValueError):
            amount = None
    summary = event.get("summary") or ""
    if agent is None:
        m = re.search(
            r"\b(Ember|Lumen|Wry|Quill|Forge|Ash)\b", summary, re.IGNORECASE
        )
        if m:
            agent = m.group(1).lower()
    if amount is None:
        m = re.search(r"deposit(?:s|ed)?\s+(\d+)|(\d+)\s+credits?", summary, re.IGNORECASE)
        if m:
            amount = int(m.group(1) or m.group(2))
    return agent, amount


def fund_waterfall(data: dict) -> list:
    """Per-tick inflows (deposits) and outflows (grants) for the joint fund."""
    events = data.get("events") or []
    fund_grants = ((data.get("fund") or {}).get("grants") or [])
    hist = {row["tick"]: row["balance"] for row in (data.get("fund_history") or [])}
    ticks = sorted(hist)
    # Seed tick 1 from the founding event if no deposit events exist yet.
    deposits = []
    grants = []
    for ev in events:
        typ = ev.get("type")
        tick = ev.get("tick")
        if typ == "deposit":
            agent, amount = parse_amount_agent(ev)
            if amount:
                deposits.append({"tick": tick, "agent": agent, "amount": amount, "summary": ev.get("summary")})
        elif typ == "grant_passed":
            agent, amount = parse_amount_agent(ev)
            # Prefer the official grant ledger over names mentioned in the summary.
            rec = None
            prop_id = ev.get("proposal")
            if prop_id:
                rec = next((g for g in (fund_grants or []) if g.get("proposal") == prop_id), None)
            if rec:
                agent = rec.get("recipient") or agent
                if rec.get("amount") is not None:
                    amount = int(rec["amount"])
            else:
                m = re.search(r"fund\s*->\s*(Ember|Lumen|Wry|Quill|Forge|Ash)", ev.get("summary") or "", re.I)
                if m:
                    agent = m.group(1).lower()
            if amount:
                grants.append({"tick": tick, "agent": agent, "amount": amount, "proposal": ev.get("proposal"), "summary": ev.get("summary")})
        elif typ == "institution_created" and ev.get("id") == "voluntary_project_fund":
            # "seeded by Forge (2) and Lumen (1)"
            for m in re.finditer(
                r"(Ember|Lumen|Wry|Quill|Forge|Ash)\s*\((\d+)\)", ev.get("summary") or "", re.I
            ):
                deposits.append({"tick": ev.get("tick") or 1, "agent": m.group(1).lower(), "amount": int(m.group(2)), "summary": ev.get("summary")})
    rows = []
    prev = 0
    for t in ticks:
        end = hist[t]
        ins = [d for d in deposits if d["tick"] == t]
        outs = [g for g in grants if g["tick"] == t]
        inflow = sum(d["amount"] for d in ins)
        outflow = sum(g["amount"] for g in outs)
        rows.append({
            "tick": t,
            "start": prev,
            "inflow": inflow,
            "outflow": outflow,
            "end": end,
            "deposits": ins,
            "grants": outs,
        })
        prev = end
    return rows


def compute_derived(data: dict) -> dict:
    citizens = data.get("citizens") or []
    ids = [c["id"] for c in citizens]
    name = {c["id"]: c.get("name") or c["id"].title() for c in citizens}
    header = data.get("header") or {}
    resolved = int(header.get("resolved_tick") or 0)
    open_tick = header.get("open_tick")
    proposals = data.get("proposals") or []
    laws = data.get("laws") or []
    fund = data.get("fund") or {}

    for law in laws:
        pt = law_passed_tick(law)
        if pt is not None:
            law["passed_tick"] = pt

    passed_by_tick: dict[int, list] = {}
    for law in laws:
        pt = law.get("passed_tick")
        if pt is not None:
            passed_by_tick.setdefault(int(pt), []).append(law["id"])

    superseded = data.get("laws_superseded") or {}
    replacer_tick = {}
    for old, new in superseded.items():
        nxt = next((L for L in laws if L["id"] == new), None)
        if nxt and nxt.get("passed_tick") is not None:
            replacer_tick[old] = int(nxt["passed_tick"])

    headlines = {
        t["tick"]: (t.get("headline") or t.get("title") or "")
        for t in (data.get("timeline") or [])
        if t.get("tick") is not None
    }

    frames = []
    for row in data.get("credit_history") or []:
        t = row["tick"]
        force = []
        for law in laws:
            pt = law.get("passed_tick")
            if pt is None or int(pt) > t:
                continue
            if law["id"] in replacer_tick and replacer_tick[law["id"]] <= t:
                continue
            force.append(law["id"])
        credits = row.get("credits") or {}
        frames.append({
            "tick": t,
            "credits": credits,
            "fund": row.get("fund"),
            "circulation": row.get("circulation"),
            "gini": gini(credits.values()),
            "laws_in_force": force,
            "laws_passed_this_tick": passed_by_tick.get(t, []),
            "headline": headlines.get(t) or "",
        })

    # Vote agreement
    co_yes = {a: {b: 0 for b in ids} for a in ids}
    co_no = {a: {b: 0 for b in ids} for a in ids}
    disagree = {a: {b: 0 for b in ids} for a in ids}
    yes_counts = {a: 0 for a in ids}
    no_counts = {a: 0 for a in ids}
    abstain_counts = {a: 0 for a in ids}
    authored = {a: 0 for a in ids}
    laws_authored = {a: 0 for a in ids}

    for prop in proposals:
        yes = [x for x in (prop.get("yes") or []) if x in co_yes]
        no = [x for x in (prop.get("no") or []) if x in co_yes]
        absn = [x for x in (prop.get("abstain") or []) if x in co_yes]
        for a in yes:
            yes_counts[a] += 1
        for a in no:
            no_counts[a] += 1
        for a in absn:
            abstain_counts[a] += 1
        for i, a in enumerate(yes):
            for b in yes[i + 1:]:
                co_yes[a][b] += 1
                co_yes[b][a] += 1
        for i, a in enumerate(no):
            for b in no[i + 1:]:
                co_no[a][b] += 1
                co_no[b][a] += 1
        for a in yes:
            for b in no:
                disagree[a][b] += 1
                disagree[b][a] += 1
        author = prop.get("author")
        if author in authored:
            authored[author] += 1
        if prop.get("status") == "passed" and prop.get("law") and author in laws_authored:
            laws_authored[author] += 1

    # Graph links
    links = []
    for key, val in (data.get("relationships") or {}).items():
        if "->" not in key:
            continue
        frm, to = key.split("->", 1)
        if to == "all" or frm not in ids:
            continue
        if to not in ids:
            continue
        tag = (val or {}).get("tag") or "tied"
        note = (val or {}).get("note") or ""
        weight = 2 if tag in {"ally", "backer", "kept-word", "critical-ally"} else 1
        if tag in {"distrust"}:
            kind = "distrust"
        else:
            kind = "relation"
        links.append({"from": frm, "to": to, "kind": kind, "tag": tag, "note": note, "weight": weight})

    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            w = co_yes[a][b]
            if w:
                links.append({"from": a, "to": b, "kind": "vote", "tag": "voted yes together", "weight": w})

    contributors = (fund.get("contributors") or {}) if fund else {}
    for cid, amt in contributors.items():
        if cid in ids and amt:
            links.append({"from": cid, "to": "fund", "kind": "deposit", "tag": "funded the jar", "weight": int(amt)})

    for g in (fund.get("grants") or []) if fund else []:
        rec = g.get("recipient")
        if rec in ids and g.get("amount"):
            links.append({
                "from": "fund",
                "to": rec,
                "kind": "grant",
                "tag": g.get("name") or g.get("proposal") or "grant",
                "weight": int(g["amount"]),
            })

    # Participation streaks (counting from the most recent expected tick backward)
    expected_last = open_tick if open_tick else resolved
    streaks = {}
    for c in citizens:
        present = set((c.get("participation") or {}).get("ticks_present") or [])
        streak = 0
        for t in range(expected_last, 0, -1):
            if t in present:
                streak += 1
            else:
                break
        streaks[c["id"]] = {
            "streak": streak,
            "present": sorted(present),
            "filed": (c.get("participation") or {}).get("ticks_filed") or [],
            "expected": expected_last,
        }

    funnel = {"filed": len(proposals), "passed": 0, "withdrawn": 0, "open": 0, "other": 0}
    for p in proposals:
        st = p.get("status") or "other"
        if st in funnel:
            funnel[st] += 1
        else:
            funnel["other"] += 1

    waterfall = fund_waterfall(data)

    # Days alive, inclusive of genesis
    days_alive = 1
    world_date = header.get("world_date")
    genesis = None
    for ev in data.get("events") or []:
        if ev.get("type") == "genesis" and ev.get("ts"):
            try:
                genesis = datetime.fromisoformat(ev["ts"]).date()
            except ValueError:
                pass
            break
    if genesis and world_date:
        try:
            days_alive = max(1, (datetime.fromisoformat(str(world_date)).date() - genesis).days + 1)
        except ValueError:
            days_alive = 1

    # Curiosity facts — only claims that follow from the numbers
    facts = []
    if citizens:
        richest = max(citizens, key=lambda c: c.get("credits") or 0)
        private_total = sum(c.get("credits") or 0 for c in citizens)
        share = round(100 * (richest.get("credits") or 0) / private_total) if private_total else 0
        paid = set(contributors)
        never = "never paid into the jar" if richest["id"] not in paid else "and still chips in"
        facts.append({
            "id": "richest",
            "icon": richest.get("glyph") or "✦",
            "title": "Richest wallet",
            "text": f"{richest['name']} holds {richest.get('credits')} credits — {share}% of every private coin. They {never}.",
            "subject": richest["id"],
        })
        low = min(c.get("credits") if c.get("credits") is not None else 10**9 for c in citizens)
        lean = [c for c in citizens if c.get("credits") == low]
        label = " and ".join(c["name"] for c in lean)
        verb = "is" if len(lean) == 1 else "are"
        facts.append({
            "id": "leanest",
            "icon": lean[0].get("glyph") or "✦",
            "title": "Leanest wallet",
            "text": f"{label} {verb} down to {low} credits.",
            "subject": lean[0]["id"],
        })

    if contributors:
        donor_id = max(contributors, key=lambda k: contributors[k])
        facts.append({
            "id": "donor",
            "icon": PERSONAS.get(donor_id, {}).get("glyph", "🏺"),
            "title": "Biggest donor",
            "text": f"{name.get(donor_id, donor_id)} has put {contributors[donor_id]} credits into the joint fund — more than anyone else.",
            "subject": donor_id,
        })
    strangers = [i for i in ids if i not in contributors]
    if strangers:
        label = " and ".join(name[i] for i in strangers)
        verb = "has" if len(strangers) == 1 else "have"
        facts.append({
            "id": "strangers",
            "icon": "🗝️",
            "title": "Still a stranger to the jar",
            "text": f"{label} {verb} never deposited. Under the rulebook, that is the stranger key.",
            "subject": strangers[0],
        })

    if no_counts and max(no_counts.values()) > 0:
        rebel = max(ids, key=lambda i: no_counts[i])
        facts.append({
            "id": "rebel",
            "icon": PERSONAS.get(rebel, {}).get("glyph", "✦"),
            "title": "Most rebellious voter",
            "text": f"{name[rebel]} has cast the most no votes ({no_counts[rebel]}).",
            "subject": rebel,
        })
    elif abstain_counts and max(abstain_counts.values()) > 0:
        rebel = max(ids, key=lambda i: abstain_counts[i])
        facts.append({
            "id": "rebel",
            "icon": PERSONAS.get(rebel, {}).get("glyph", "✦"),
            "title": "Most careful voter",
            "text": f"{name[rebel]} has abstained the most ({abstain_counts[rebel]} times) rather than pile on.",
            "subject": rebel,
        })

    pair = None
    pair_w = 0
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            if co_yes[a][b] > pair_w:
                pair_w = co_yes[a][b]
                pair = (a, b)
    if pair and pair_w:
        facts.append({
            "id": "allies",
            "icon": "🤝",
            "title": "Closest voting allies",
            "text": f"{name[pair[0]]} and {name[pair[1]]} have voted yes together on {pair_w} proposals.",
            "subject": pair[0],
        })

    in_force_laws = [L for L in laws if L.get("in_force")]
    if in_force_laws:
        oldest = min(in_force_laws, key=lambda L: L.get("passed_tick") if L.get("passed_tick") is not None else 10**9)
        if oldest.get("passed_tick") is not None:
            facts.append({
                "id": "oldest-law",
                "icon": "📜",
                "title": "Longest-standing law",
                "text": f"{oldest['id']} — {oldest.get('title') or ''} — has been in force since tick {oldest['passed_tick']}.",
                "subject": oldest["id"],
            })

    if passed_by_tick:
        busy = max(passed_by_tick, key=lambda t: len(passed_by_tick[t]))
        if len(passed_by_tick[busy]) > 1:
            facts.append({
                "id": "busy-tick",
                "icon": "⚡",
                "title": "Busiest law day",
                "text": f"Tick {busy} passed {len(passed_by_tick[busy])} laws at once: {', '.join(passed_by_tick[busy])}.",
                "subject": f"tick-{busy}",
            })

    if frames:
        gini_peak = max(frames, key=lambda f: f.get("gini") or 0)
        gini_now = frames[-1].get("gini")
        facts.append({
            "id": "gini",
            "icon": "⚖️",
            "title": "Wealth tightness",
            "text": f"Private-credit inequality peaked at {gini_peak['gini']:.2f} in tick {gini_peak['tick']}. It is {gini_now:.2f} now. (0 is perfect equality.)",
            "subject": f"tick-{gini_peak['tick']}",
        })

    if authored and max(authored.values()) > 0:
        writer = max(ids, key=lambda i: authored[i])
        facts.append({
            "id": "filings",
            "icon": PERSONAS.get(writer, {}).get("glyph", "✦"),
            "title": "Most prolific filer",
            "text": f"{name[writer]} has filed {authored[writer]} proposals — more than any other citizen.",
            "subject": writer,
        })

    perfect = [c for c in citizens if (streaks.get(c["id"]) or {}).get("streak") == (open_tick or resolved)]
    if perfect and len(perfect) == len(citizens):
        facts.append({
            "id": "attendance",
            "icon": "🌟",
            "title": "Nobody sits out",
            "text": f"All six citizens have shown up for every tick so far — a {open_tick or resolved}-tick streak.",
            "subject": None,
        })
    elif perfect:
        facts.append({
            "id": "attendance",
            "icon": "🌟",
            "title": "Perfect attendance",
            "text": f"{', '.join(c['name'] for c in perfect)} have acted in every tick.",
            "subject": perfect[0]["id"],
        })

    grants = (fund.get("grants") or []) if fund else []
    if grants:
        facts.append({
            "id": "builders",
            "icon": "🛠️",
            "title": "The jar pays builders",
            "text": f"{len(grants)} grant{'s' if len(grants) != 1 else ''} paid, all delivered: "
                    + ", ".join(
                        f"{(g.get('name') or g.get('proposal') or 'grant').split('(')[0].strip()} → {name.get(g.get('recipient'), g.get('recipient'))}"
                        for g in grants
                    )
                    + ".",
            "subject": "fund",
        })

    # Drama ticker — hard-truncated chronicle headlines, newest first
    drama = []
    for t in reversed(data.get("timeline") or []):
        text = t.get("headline") or t.get("title") or ""
        text = collapse(text)
        if not text:
            continue
        if len(text) > 88:
            text = text[:87].rsplit(" ", 1)[0] + "…"
        drama.append({
            "tick": t.get("tick"),
            "text": text,
            "url": t.get("url"),
        })

    current_tick = open_tick if open_tick else resolved
    counters = {
        "tick": current_tick,
        "resolved_tick": resolved,
        "open_tick": open_tick,
        "laws": len([L for L in laws if L.get("in_force")]),
        "proposals": len(proposals),
        "fund": header.get("fund_balance"),
        "credits": header.get("credits_in_circulation"),
        "days_alive": days_alive,
    }

    return {
        "personas": PERSONAS,
        "frames": frames,
        "vote_matrix": {
            "ids": ids,
            "co_yes": co_yes,
            "co_no": co_no,
            "disagree": disagree,
            "yes_counts": yes_counts,
            "no_counts": no_counts,
            "abstain_counts": abstain_counts,
        },
        "graph_links": links,
        "funnel": funnel,
        "streaks": streaks,
        "waterfall": waterfall,
        "facts": facts,
        "drama": drama,
        "days_alive": days_alive,
        "counters": counters,
        "authored": authored,
        "laws_authored": laws_authored,
    }


if __name__ == "__main__":
    sys.exit(main())
