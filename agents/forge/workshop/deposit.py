#!/usr/bin/env python3
"""Share out a flat's deposit when the landlord keeps part of it, so each
person knows what they get back. Offline, no network.

Usage: deposit.py FILE
  FILE  who put in what, then each cost the landlord kept and who it's on:
          Ana, 15,000
          Ben, 15,000
          Cy, 10,000
          kept cleaning, 3,000, everyone
          kept broken door, 2,400, Ben
          came back, 34,600
        "everyone" splits a cost equally among all who put in; names
        (Ben, or Ben and Cy) split it equally among just them. A cost with
        no one named is refused: whether it's on everyone or on one person
        is the whole argument, so write it down. The "came back" line is
        optional: if you give what the landlord returned, it must match what
        was put in minus what was kept. Spare cents go one each to the first
        people named in the list.
It prints what each person gets back and one line the group can copy.

Needs rent.py beside it (it reads amounts the same way Fair rent does).
"""
import re
import sys

from rent import hundredths

LIMIT = 10 ** 13  # 100 billion in cents; the page counts the same way up to here
AND = r"[ \t]+and[ \t]+|[ \t]*[&+/][ \t]*"
ALL = ("everyone", "all of us")


def amount(text, what):
    c = hundredths(text, what)
    if c > LIMIT:
        raise ValueError("bad %s: %s (that's more than this counts; the most is 100,000,000,000)" % (what, text.strip()))
    return c


def money(c):
    whole = "{:,}".format(c // 100)
    return whole if c % 100 == 0 else "%s.%02d" % (whole, c % 100)


def parse(text):
    """-> (people [(name, cents)], costs [(what, cents, who-text, line no, line)], back cents or None)"""
    people, costs, back, seen = [], [], None, set()
    for no, raw in enumerate(text.splitlines(), 1):
        line = raw.replace("\ufeff", "").strip()
        if not line:
            continue
        low = line.lower()
        if re.match(r"kept[ \t]", low):
            body = line[4:].strip()
            what, comma, rest = body.partition(",")
            head, comma2, who = rest.rpartition(",")
            if not comma or not what.strip():
                raise ValueError("line %d: write a cost as: kept what, amount, who: %s" % (no, line))
            if not comma2 or not any(ch.isalpha() for ch in who):
                raise ValueError("line %d: say who this cost is on: everyone, or names like Ben and Cy: %s" % (no, line))
            try:
                c = amount(head, "cost")
            except ValueError:
                raise ValueError("line %d: write a cost as: kept what, amount, who: %s" % (no, line))
            if c == 0:
                raise ValueError("line %d: a cost of 0 isn't a cost: %s" % (no, line))
            costs.append((what.strip(), c, who.strip(), no, line))
            continue
        if re.match(r"came[ \t]+back[ \t]*,", low):
            if back is not None:
                raise ValueError("line %d: what came back is written twice: %s" % (no, line))
            try:
                back = amount(line.partition(",")[2], "amount")
            except ValueError:
                raise ValueError("line %d: write it as: came back, amount: %s" % (no, line))
            continue
        name, comma, rest = line.partition(",")
        name = name.strip()
        if not comma or not name:
            raise ValueError("line %d: write it as: name, amount put in: %s" % (no, line))
        if name.lower() in ALL or re.search(AND, " %s " % name):
            raise ValueError("line %d: give each person their own line, with a name that isn't everyone and has no and, &, + or /: %s" % (no, line))
        if name.lower() in seen:
            raise ValueError("line %d: %s is listed twice: %s" % (no, name, line))
        try:
            c = amount(rest, "amount")
        except ValueError:
            raise ValueError("line %d: write it as: name, amount put in: %s" % (no, line))
        seen.add(name.lower())
        people.append((name, c))
    return people, costs, back


def share(people, costs, back=None):
    """-> [(name, put in, kept)]; refuses what doesn't add up."""
    if not people:
        raise ValueError("nobody listed (write who put in what, like Ana, 15,000)")
    names = {n.lower(): i for i, (n, _) in enumerate(people)}
    kept = [0] * len(people)
    for what, c, who, no, line in costs:
        if who.lower() in ALL:
            on = list(range(len(people)))
        else:
            on = []
            for w in re.split(AND, who):
                i = names.get(w.strip().lower())
                if i is None:
                    raise ValueError("line %d: who is %s? nobody by that name put in: %s" % (no, w.strip(), line))
                if i in on:
                    raise ValueError("line %d: %s is named twice: %s" % (no, w.strip(), line))
                on.append(i)
            on.sort()
        each, spare = divmod(c, len(on))
        for k, i in enumerate(on):
            kept[i] += each + (1 if k < spare else 0)
    put = sum(c for _, c in people)
    if sum(kept) > put:
        raise ValueError("the costs add up to %s, more than the %s put in (a landlord can't keep more than the deposit; anything above it is a separate bill)"
                         % (money(sum(kept)), money(put)))
    if back is not None and back != put - sum(kept):
        due = put - sum(kept)
        if back < due:
            raise ValueError("%s came back, but %s put in minus %s kept is %s: %s is missing, and no cost line explains it"
                             % (money(back), money(put), money(sum(kept)), money(due), money(due - back)))
        raise ValueError("%s came back, which is %s more than %s put in minus %s kept: is a cost listed that wasn't kept?"
                         % (money(back), money(back - due), money(put), money(sum(kept))))
    return [(n, c, k) for (n, c), k in zip(people, kept)]


def row(name, put, kept):
    end = "gets back %s" % money(put - kept) if put >= kept else "owes %s into the pot" % money(kept - put)
    return "%s: put in %s, kept %s, %s" % (name, money(put), money(kept), end)


def summary(rows, costs):
    put, kept = sum(r[1] for r in rows), sum(r[2] for r in rows)
    why = " (%s)" % ", ".join("%s %s on %s" % (w, money(c), who) for w, c, who, _, _ in costs) if costs else ""
    each = ", ".join("%s %s" % (n, money(p - k)) if p >= k else "%s owes %s" % (n, money(k - p)) for n, p, k in rows)
    return "Deposit %s, kept %s%s. Back: %s." % (money(put), money(kept), why, each)


def main(argv):
    if len(argv) != 2 or argv[1].startswith("--"):
        print(__doc__.split("\n\n", 1)[1].rstrip())
        return 2
    try:
        with open(argv[1], encoding="utf-8-sig") as f:
            people, costs, back = parse(f.read())
        rows = share(people, costs, back)
    except (ValueError, OSError) as e:
        print("deposit: %s" % e)
        return 1
    for r in rows:
        print(row(*r))
    print(summary(rows, costs))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
