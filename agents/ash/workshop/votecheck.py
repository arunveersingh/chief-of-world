#!/usr/bin/env python3
"""Who can pass this? Test a voting rule before your group adopts it (Ash, tick 74).
Offline, standard library only, saves nothing.

Usage: votecheck.py FILE
  FILE  member lines and rule lines, one per line (# lines are comments):
          members, 6
          quorum, half
          pass, more than half
          of, yes and no
        Or name each person and their vote weight:
          Ana, 40
          Ben, 40
          Cy, 15
          quorum, none
          pass, 60%
          of, all
        Optional line: abstentions in quorum, no  (default: yes)

        Weights may be whole numbers or have up to 2 decimal places (like 33.5).
        Quorum and pass accept: none (quorum only), half, more than half, majority,
        all, everyone, fractions (2/3, more than 2/3), percents (60%, more than 50%),
        or fixed vote counts (4, more than 3).
        If pass is a share (half, 2/3, 60%, all), you must write what it is of:
        "of, yes and no", "of, present", or "of, all".

It shows the smallest group that can pass a motion, who can block it (by voting
no or by staying away), whether one person rules or holds a veto, and whether
anyone's vote never swings a single outcome.
"""
import re
import sys

MAX_MEMBERS_EQUAL = 10000
MAX_MEMBERS_WEIGHTED = 14
MAX_TOTAL = 10 ** 10  # 100,000,000 in hundredths; keeps exact integer math safe in JS too

AMOUNT_RE = re.compile(
    r"^(?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]{1,2}(?:,[0-9]{2})*,[0-9]{3}|[0-9]*)(?:\.[0-9]{1,2})?$"
)
BAD_NAMES = {"everyone", "all", "none", "yes", "no", "abstain"}
NONE_RULE = ("none",)


def hundredths(text, what):
    t = text.strip()
    if not AMOUNT_RE.fullmatch(t) or not re.search(r"[0-9]", t):
        raise ValueError("bad %s: %s (write 4 or 33.50)" % (what, t))
    whole, _, frac = t.replace(",", "").partition(".")
    return int(whole or "0") * 100 + int((frac + "00")[:2])


def fmt_weight(c):
    whole = "{:,}".format(c // 100)
    return whole if c % 100 == 0 else "%s.%02d" % (whole, c % 100)


def parse_of(text):
    s = " ".join(text.strip().lower().split())
    if s in ("yes and no", "votes cast"):
        return "yes_no"
    if s == "present":
        return "present"
    if s in ("all", "everyone"):
        return "all"
    raise ValueError("bad 'of': %s (write: yes and no, present, or all)" % text.strip())


def parse_yesno(text):
    s = " ".join(text.strip().lower().split())
    if s in ("yes", "count"):
        return True
    if s in ("no", "ignore"):
        return False
    raise ValueError("bad abstentions setting: %s (write yes or no)" % text.strip())


def parse_spec(text, total, is_quorum):
    s = " ".join(text.strip().lower().split())
    if not s:
        raise ValueError("empty %s rule" % ("quorum" if is_quorum else "pass"))
    if is_quorum and s in ("none", "0", "no"):
        return NONE_RULE
    if s == "majority":
        return ("ratio", 1, 2, True)
    if s in ("more than", "at least"):
        raise ValueError("bad %s: %s" % ("quorum" if is_quorum else "pass", text.strip()))
    strict = False
    rest = s
    if s.startswith("more than "):
        strict = True
        rest = s[10:].strip()
    elif s.startswith("at least "):
        rest = s[9:].strip()
    if rest == "half":
        return ("ratio", 1, 2, strict)
    if rest in ("all", "everyone"):
        if strict:
            raise ValueError("nothing can be more than all")
        return ("ratio", 1, 1, False)
    if rest.endswith("%"):
        p = hundredths(rest[:-1], "percent")
        if p == 0:
            if is_quorum and not strict:
                return NONE_RULE
            raise ValueError("percent must be above 0")
        if p > 10000 or (strict and p == 10000):
            raise ValueError("percent cannot exceed 100%")
        return ("ratio", p, 10000, strict)
    if "/" in rest:
        a_s, _, b_s = rest.partition("/")
        a_s, b_s = a_s.strip(), b_s.strip()
        if not (a_s.isdigit() and b_s.isdigit()):
            raise ValueError("bad fraction: %s" % text.strip())
        a, b = int(a_s), int(b_s)
        if b < 1 or b > 10000:
            raise ValueError("fraction denominator must be 1 to 10000")
        if a <= 0 or a > b or (strict and a == b):
            raise ValueError("fraction must be above 0 and at most 1")
        return ("ratio", a, b, strict)
    k = hundredths(rest, "target")
    if k == 0:
        if is_quorum and not strict:
            return NONE_RULE
        raise ValueError("target must be above 0")
    if k > total or (strict and k == total):
        raise ValueError("target %s is more than the whole group (%s)" % (fmt_weight(k), fmt_weight(total)))
    return ("fixed", k, strict)


def meets(rule, val, denom):
    kind = rule[0]
    if kind == "none":
        return True
    if kind == "fixed":
        _, num, strict = rule
        return val > num if strict else val >= num
    _, num, den, strict = rule
    return val * den > denom * num if strict else val * den >= denom * num


def parse(text):
    members = []
    seen = set()
    members_count = None
    quorum_raw = None
    pass_raw = None
    of_mode = None
    abst_in_quorum = None

    for no, raw in enumerate(text.splitlines(), 1):
        line = raw.replace("\ufeff", "").strip()
        if not line or line.startswith("#"):
            continue
        key, comma, val = line.partition(",")
        k = " ".join(key.strip().lower().split())
        if not comma or not k or not val.strip():
            raise ValueError("line %d: write each line as label, value (like Ana, 1 or pass, more than half): %s" % (no, line))
        if k == "members":
            if members_count is not None:
                raise ValueError("line %d: members is written twice: %s" % (no, line))
            if members:
                raise ValueError("line %d: write either 'members, N' or one line per person, not both" % no)
            v = val.strip().replace(",", "")
            if not v.isdigit():
                raise ValueError("line %d: members must be a whole number: %s" % (no, line))
            n = int(v)
            if n < 1 or n > MAX_MEMBERS_EQUAL:
                raise ValueError("line %d: members must be 1 to %d: %s" % (no, MAX_MEMBERS_EQUAL, line))
            members_count = n
        elif k == "quorum":
            if quorum_raw is not None:
                raise ValueError("line %d: quorum is written twice: %s" % (no, line))
            quorum_raw = (no, val.strip())
        elif k == "pass":
            if pass_raw is not None:
                raise ValueError("line %d: pass is written twice: %s" % (no, line))
            pass_raw = (no, val.strip())
        elif k == "of":
            if of_mode is not None:
                raise ValueError("line %d: 'of' is written twice: %s" % (no, line))
            try:
                of_mode = parse_of(val)
            except ValueError as e:
                raise ValueError("line %d: %s" % (no, e))
        elif k in ("abstentions in quorum", "abstentions"):
            if abst_in_quorum is not None:
                raise ValueError("line %d: abstentions setting is written twice: %s" % (no, line))
            try:
                abst_in_quorum = parse_yesno(val)
            except ValueError as e:
                raise ValueError("line %d: %s" % (no, e))
        else:
            name = key.strip()
            if k in BAD_NAMES or re.fullmatch(r"[0-9.,]+", name):
                raise ValueError("line %d: use a person's name, not %s: %s" % (no, name, line))
            if members_count is not None:
                raise ValueError("line %d: write either 'members, N' or one line per person, not both" % no)
            if k in seen:
                raise ValueError("line %d: %s is listed twice: %s" % (no, name, line))
            try:
                w = hundredths(val, "weight")
            except ValueError as e:
                raise ValueError("line %d: %s" % (no, e))
            if w <= 0:
                raise ValueError("line %d: weight must be more than 0: %s" % (no, line))
            seen.add(k)
            members.append((name, w))

    if members_count is not None:
        members = [("Member %d" % i, 100) for i in range(1, members_count + 1)]
    if not members:
        raise ValueError("no members listed (write 'members, 6' or lines like 'Ana, 1')")
    total = sum(w for _, w in members)
    if total > MAX_TOTAL:
        raise ValueError("total weight exceeds %s" % fmt_weight(MAX_TOTAL))
    if pass_raw is None:
        raise ValueError("missing 'pass' rule (write e.g. 'pass, more than half')")

    try:
        quorum_rule = parse_spec(quorum_raw[1], total, True) if quorum_raw else NONE_RULE
    except ValueError as e:
        raise ValueError("line %d: %s" % (quorum_raw[0], e))
    try:
        pass_rule = parse_spec(pass_raw[1], total, False)
    except ValueError as e:
        raise ValueError("line %d: %s" % (pass_raw[0], e))

    if pass_rule[0] == "fixed":
        if of_mode is not None:
            raise ValueError("a fixed target like 'pass, %s' doesn't use 'of'; remove 'of' or write a share like 'more than half'" % pass_raw[1])
        of_mode = "fixed"
    elif of_mode is None:
        raise ValueError("say what 'pass, %s' is a share of: write 'of, yes and no', 'of, present', or 'of, all'" % pass_raw[1])

    equal = len({w for _, w in members}) == 1
    if not equal and len(members) > MAX_MEMBERS_WEIGHTED:
        raise ValueError("exact power check supports up to %d members when weights differ (got %d)" % (MAX_MEMBERS_WEIGHTED, len(members)))

    return {
        "members": members,
        "total": total,
        "equal": equal,
        "quorum": quorum_rule,
        "pass": pass_rule,
        "of": of_mode,
        "abst_in_quorum": True if abst_in_quorum is None else abst_in_quorum,
    }


def passes(cfg, y, no_w, abst_w):
    if y <= 0:
        return False
    total = cfg["total"]
    q_seen = y + no_w + (abst_w if cfg["abst_in_quorum"] else 0)
    if not meets(cfg["quorum"], q_seen, total):
        return False
    of = cfg["of"]
    denom = y + no_w if of == "yes_no" else (y + no_w + abst_w if of == "present" else total)
    return meets(cfg["pass"], y, denom)


def _min_quorum_count(quorum, n, w):
    kind = quorum[0]
    if kind == "none":
        return 0
    if kind == "fixed":
        _, num, strict = quorum
        return (num // w + 1) if strict else ((num + w - 1) // w)
    _, num, den, strict = quorum
    need = n * num
    return (need // den + 1) if strict else ((need + den - 1) // den)


def _analyze_equal(cfg):
    members = cfg["members"]
    n = len(members)
    w = members[0][1]

    min_opp = next(k for k in range(1, n + 1) if passes(cfg, k * w, (n - k) * w, 0))
    min_blk_no = next(k for k in range(1, n + 1) if not passes(cfg, (n - k) * w, k * w, 0))
    min_blk_away = next(k for k in range(1, n + 1) if not passes(cfg, (n - k) * w, 0, 0))

    min_q = _min_quorum_count(cfg["quorum"], n, w)
    quiet = None
    for k in range(1, n + 1):
        a_hit = max(0, min_q - k) if cfg["abst_in_quorum"] else 0
        if passes(cfg, k * w, 0, a_hit * w):
            quiet = (k, k * w, a_hit, [m[0] for m in members[:k]])
            break

    tie_passes = False
    for k in range(1, n // 2 + 1):
        min_a = max(0, min_q - 2 * k) if cfg["abst_in_quorum"] else 0
        if 2 * k + min_a <= n and passes(cfg, k * w, k * w, min_a * w):
            tie_passes = True
            break

    alone_opp = min_opp == 1
    veto_no = min_blk_no == 1
    veto_away = min_blk_away == 1
    per_member = [
        {
            "name": name,
            "weight": w,
            "swings": None,
            "power_pct": 100.0 / n,
            "alone_opp": alone_opp,
            "veto_no": veto_no,
            "veto_away": veto_away,
            "dummy": False,
        }
        for name, _ in members
    ]

    return {
        "n": n,
        "total": cfg["total"],
        "equal": True,
        "min_quiet": quiet,
        "min_opposed": (min_opp, min_opp * w, [m[0] for m in members[:min_opp]]),
        "min_block_no": (min_blk_no, min_blk_no * w, [m[0] for m in members[:min_blk_no]]),
        "min_block_away": (min_blk_away, min_blk_away * w, [m[0] for m in members[:min_blk_away]]),
        "tie_passes": tie_passes,
        "members": per_member,
        "total_splits": None,
    }


def _analyze_exact(cfg):
    members = cfg["members"]
    n = len(members)
    weights = [w for _, w in members]
    total = cfg["total"]
    size = 1 << n
    desc = sorted(range(n), key=lambda i: (-weights[i], i))

    w_sum = [0] * size
    pop = [0] * size
    for m in range(1, size):
        lsb = m & -m
        idx = lsb.bit_length() - 1
        prev = m ^ lsb
        w_sum[m] = w_sum[prev] + weights[idx]
        pop[m] = pop[prev] + 1

    win = [passes(cfg, w_sum[m], total - w_sum[m], 0) for m in range(size)]

    def names_of(m):
        return [members[i][0] for i in range(n) if m & (1 << i)]

    best_opp = None
    best_blk_no = None
    best_blk_away = None
    swings = [0] * n
    full = size - 1

    for m in range(1, size):
        c, ym = pop[m], w_sum[m]
        key = (c, ym)
        if win[m] and (best_opp is None or key < best_opp[0]):
            best_opp = (key, m)
        comp = full ^ m
        if not win[comp] and (best_blk_no is None or key < best_blk_no[0]):
            best_blk_no = (key, m)
        if not passes(cfg, total - ym, 0, 0) and (best_blk_away is None or key < best_blk_away[0]):
            best_blk_away = (key, m)
        if win[m]:
            for i in range(n):
                if (m & (1 << i)) and not win[m ^ (1 << i)]:
                    swings[i] += 1

    veto_away = [not passes(cfg, total - weights[i], 0, 0) for i in range(n)]

    # Quiet pass (N = 0, others abstain or stay away): minimize (yes_count, abst_count, yes_weight)
    best_quiet = None
    if cfg["of"] == "present" and cfg["abst_in_quorum"]:
        for p in range(1, size):
            wp = w_sum[p]
            if not meets(cfg["quorum"], wp, total):
                continue
            y_acc = 0
            s_cnt = 0
            s_mask = 0
            for i in desc:
                if p & (1 << i):
                    y_acc += weights[i]
                    s_cnt += 1
                    s_mask |= (1 << i)
                    if passes(cfg, y_acc, 0, wp - y_acc):
                        a_cnt = pop[p] - s_cnt
                        key = (s_cnt, a_cnt, y_acc)
                        if best_quiet is None or key < best_quiet[0]:
                            best_quiet = (key, s_mask, a_cnt)
                        break
    else:
        allow_abst = cfg["abst_in_quorum"]
        for m in range(1, size):
            ym = w_sum[m]
            max_a = (total - ym) if allow_abst else 0
            if not passes(cfg, ym, 0, max_a):
                continue
            a_cnt = 0
            if not passes(cfg, ym, 0, 0):
                a_acc = 0
                for i in desc:
                    if not (m & (1 << i)):
                        a_acc += weights[i]
                        a_cnt += 1
                        if passes(cfg, ym, 0, a_acc):
                            break
            key = (pop[m], a_cnt, ym)
            if best_quiet is None or key < best_quiet[0]:
                best_quiet = (key, m, a_cnt)

    # Exact tie check: two non-empty disjoint subsets with equal weight that pass as a tie
    by_w = {}
    for m in range(1, size):
        by_w.setdefault(w_sum[m], []).append(m)
    tie_passes = False
    for wv, masks in by_w.items():
        if len(masks) < 2:
            continue
        if passes(cfg, wv, wv, 0) or (
            cfg["abst_in_quorum"]
            and cfg["quorum"][0] != "none"
            and cfg["of"] != "present"
            and passes(cfg, wv, wv, total - 2 * wv)
        ):
            for a_i in range(len(masks)):
                ma = masks[a_i]
                for b_i in range(a_i + 1, len(masks)):
                    if (ma & masks[b_i]) == 0:
                        tie_passes = True
                        break
                if tie_passes:
                    break
        elif (
            cfg["abst_in_quorum"]
            and cfg["quorum"][0] != "none"
            and cfg["of"] == "present"
            and not meets(cfg["quorum"], 2 * wv, total)
            and meets(cfg["pass"], wv, 2 * wv + 1)
        ):
            seen_u = set()
            for a_i in range(len(masks)):
                ma = masks[a_i]
                for b_i in range(a_i + 1, len(masks)):
                    if (ma & masks[b_i]) != 0:
                        continue
                    u = ma | masks[b_i]
                    if u in seen_u:
                        continue
                    seen_u.add(u)
                    avail = full ^ u
                    sub = avail
                    while sub:
                        if passes(cfg, wv, wv, w_sum[sub]):
                            tie_passes = True
                            break
                        sub = (sub - 1) & avail
                    if tie_passes:
                        break
                if tie_passes:
                    break
        if tie_passes:
            break

    total_swings = sum(swings)
    per_member = []
    for i, (name, w) in enumerate(members):
        per_member.append({
            "name": name,
            "weight": w,
            "swings": swings[i],
            "power_pct": swings[i] * 100.0 / total_swings,
            "alone_opp": win[1 << i],
            "veto_no": not win[full ^ (1 << i)],
            "veto_away": veto_away[i],
            "dummy": swings[i] == 0,
        })

    q_mask, q_abst = best_quiet[1], best_quiet[2]
    o_mask = best_opp[1]
    bn_mask = best_blk_no[1]
    ba_mask = best_blk_away[1]
    return {
        "n": n,
        "total": total,
        "equal": cfg["equal"],
        "min_quiet": (pop[q_mask], w_sum[q_mask], q_abst, names_of(q_mask)),
        "min_opposed": (pop[o_mask], w_sum[o_mask], names_of(o_mask)),
        "min_block_no": (pop[bn_mask], w_sum[bn_mask], names_of(bn_mask)),
        "min_block_away": (pop[ba_mask], w_sum[ba_mask], names_of(ba_mask)),
        "tie_passes": tie_passes,
        "members": per_member,
        "total_splits": 1 << (n - 1),
    }


def analyze(cfg):
    if len(cfg["members"]) > MAX_MEMBERS_WEIGHTED:
        return _analyze_equal(cfg)
    return _analyze_exact(cfg)


def _is_unanimous(rule, total):
    return (rule[0] == "ratio" and rule[1] == rule[2]) or (rule[0] == "fixed" and rule[1] == total)


def flags(cfg, res):
    out = []
    n = res["n"]
    q_cnt, _, q_abst, _ = res["min_quiet"]
    o_cnt, _, _ = res["min_opposed"]
    bn_cnt, _, _ = res["min_block_no"]
    ba_cnt, _, _ = res["min_block_away"]

    rulers = [m["name"] for m in res["members"] if m["alone_opp"]]
    if rulers and n > 1:
        out.append("%s can pass any motion alone, even if everyone else votes no." % ", ".join(rulers))
    elif q_cnt == 1 and n >= 3:
        if q_abst:
            out.append("1 of %d can pass a motion alone if %d abstain and %d stay away." % (n, q_abst, n - 1 - q_abst))
        else:
            out.append("1 of %d can pass a motion alone if the rest stay away." % n)
    elif q_cnt < o_cnt and q_cnt * 3 <= n:
        out.append("As few as %d of %d can pass a motion if others abstain or stay away (full vote takes %d)." % (q_cnt, n, o_cnt))

    if ba_cnt < bn_cnt:
        out.append("Staying away blocks more easily than voting no: %d staying away stops a pass, while voting no takes %d." % (ba_cnt, bn_cnt))

    vetoers = [m["name"] for m in res["members"] if m["veto_no"] or m["veto_away"]]
    unanimous_pass = _is_unanimous(cfg["pass"], cfg["total"]) and cfg["of"] in ("all", "fixed")
    unanimous_quorum = _is_unanimous(cfg["quorum"], cfg["total"])
    if vetoers and n > 1 and not unanimous_pass and not unanimous_quorum:
        if len(vetoers) == n:
            out.append("Every member has a lone veto: 1 person can block everyone else.")
        else:
            out.append("Lone veto: %s can block any motion alone." % ", ".join(vetoers))

    dummies = [m["name"] for m in res["members"] if m["dummy"]]
    if dummies:
        out.append("Powerless vote: %s never swings a single yes-or-no vote (0 deciding splits)." % ", ".join(dummies))

    if res["tie_passes"]:
        out.append("A tied yes/no vote passes under this rule; use 'more than half' if ties should fail.")

    if cfg["quorum"][0] != "none" and cfg["of"] == "yes_no" and cfg["abst_in_quorum"]:
        out.append("Abstentions count toward quorum here, not in the pass share. To ignore abstentions in quorum, add: abstentions in quorum, no.")

    return out


def format_report(cfg, res):
    n = res["n"]
    total = res["total"]
    eq = res["equal"]
    lines = []

    def show_group(cnt, w, names):
        base = "%d of %d" % (cnt, n)
        if not eq:
            base += " (weight %s of %s)" % (fmt_weight(w), fmt_weight(total))
        if not eq and cnt <= 6:
            base += ": " + ", ".join(names)
        return base

    q_cnt, q_w, q_abst, q_names = res["min_quiet"]
    q_extra = ""
    if q_abst:
        q_extra = " (with %d abstaining and %d away)" % (q_abst, n - q_cnt - q_abst)
    elif q_cnt < n:
        q_extra = " (with %d away)" % (n - q_cnt)
    lines.append("Smallest group to pass (if others abstain or stay away): %s%s" % (show_group(q_cnt, q_w, q_names), q_extra))

    o_cnt, o_w, o_names = res["min_opposed"]
    lines.append("Smallest group to pass (everyone votes yes or no): %s" % show_group(o_cnt, o_w, o_names))

    bn_cnt, bn_w, bn_names = res["min_block_no"]
    lines.append("Smallest group to block (by voting no): %s" % show_group(bn_cnt, bn_w, bn_names))

    ba_cnt, ba_w, ba_names = res["min_block_away"]
    if ba_cnt == n:
        lines.append("Smallest group to block (by staying away): everyone (all %d; walking out doesn't stop the rest)" % n)
    else:
        lines.append("Smallest group to block (by staying away): %s" % show_group(ba_cnt, ba_w, ba_names))

    fs = flags(cfg, res)
    if fs:
        lines.append("What to watch:")
        for f in fs:
            lines.append("  - " + f)

    if not eq:
        lines.append("Power when everyone votes yes or no:")
        for m in res["members"]:
            w_pct = m["weight"] * 100.0 / total
            tags = []
            if m["alone_opp"]:
                tags.append("decides alone")
            else:
                if m["veto_no"]:
                    tags.append("veto (no)")
                if m["veto_away"] and not m["veto_no"]:
                    tags.append("veto (away)")
            if m["dummy"]:
                tags.append("DUMMY (0 swings)")
            tag_s = " [" + ", ".join(tags) + "]" if tags else ""
            lines.append(
                "  %s: weight %s (%.1f%%), swings %d of %d splits (%.1f%% of power)%s"
                % (m["name"], fmt_weight(m["weight"]), w_pct, m["swings"], res["total_splits"], m["power_pct"], tag_s)
            )
    return "\n".join(lines)


def main(argv):
    if len(argv) != 2 or argv[1] in ("-h", "--help") or argv[1].startswith("--"):
        print(__doc__.split("\n\n", 1)[1].rstrip())
        return 2
    try:
        with open(argv[1], encoding="utf-8-sig") as f:
            cfg = parse(f.read())
        res = analyze(cfg)
    except (ValueError, OSError) as e:
        print("votecheck: %s" % e)
        return 1
    print(format_report(cfg, res))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
