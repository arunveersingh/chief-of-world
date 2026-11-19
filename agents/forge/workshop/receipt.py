#!/usr/bin/env python3
"""Share an itemised receipt (a dinner, a delivery, a grocery run) so each
person pays for what they had, plus their part of tax, tip and fees, with
nothing guessed. Offline, no network.

Usage: receipt.py FILE
  FILE  one item per line: what, amount, who. Then the bill-wide lines:
          Pasta, 450, Ana
          Burger, 380, Ben
          Thali, 320, Cy
          Wine, 1,200, Ana and Ben
          Garlic bread, 150, everyone
          tax, 125
          tip, 250, by share
          delivery fee, 60, evenly
          discount, 200, by share
          total, 2,735
          paid, Ana
        "everyone" splits an item equally among all the people; names (Ben,
        or Ben and Cy) split it among just them. tip, fee, service, service
        fee, service charge, delivery, delivery fee and discount must say how
        they are split: "by share" (in proportion to each person's items) or
        "evenly" (the same for everyone). That choice is the argument, so it
        is never guessed. tax is by share unless you write ", evenly". Write
        each as the exact amount on the receipt, not a %. Optional lines:
        "people, Ana, Ben and Cy" (who is in, in order, including anyone who
        had nothing), "total, amount" (checked against the lines), and
        "paid, name" (one person who paid the bill; for several payers, use
        Settle up). Spare cents of an item or an even split go one each to
        the first people in the list; spare cents of a split by share go to
        whoever was rounded down the most (largest remainder).
It prints each person's share and one line the group can copy.

Needs rent.py beside it (it reads amounts the same way Fair rent does).
"""
import re
import sys

from rent import hundredths

LIMIT = 10 ** 13  # 100 billion in cents; the page counts the same way up to here
AND = r"[ \t]+and[ \t]+|[ \t]*[&+/][ \t]*"
ALL = ("everyone", "all of us")
BILL = r"(people|tax|tip|delivery(?:[ \t]+fee)?|service(?:[ \t]+(?:fee|charge))?|fee|discount|total|paid)[ \t]*,"
MODES = ("by share", "evenly")


def amount(text, what):
    c = hundredths(text, what)
    if c > LIMIT:
        raise ValueError("bad %s: %s (that's more than this counts; the most is 100,000,000,000)" % (what, text.strip()))
    return c


def money(c):
    whole = "{:,}".format(c // 100)
    return whole if c % 100 == 0 else "%s.%02d" % (whole, c % 100)


def names_in(who):
    return [w.strip() for w in re.split(AND, who)]


def parse(text):
    """-> (people or None, items [(what, cents, who, no, line)],
    adjusts [(kind, cents, mode, is discount, no, line)], total or None, paid or None)"""
    people, items, adjusts, total, paid = None, [], [], None, None
    for no, raw in enumerate(text.splitlines(), 1):
        line = raw.replace("\ufeff", "").strip()
        if not line:
            continue
        m = re.match(BILL, line.lower())
        if m:
            kind, rest = re.sub(r"[ \t]+", " ", m.group(1)), line.partition(",")[2]
            if kind == "people":
                if people is not None:
                    raise ValueError("line %d: the people line is written twice: %s" % (no, line))
                people, seen = [], set()
                for n in [w.strip() for w in re.split(",|" + AND, rest)]:
                    if not any(ch.isalpha() for ch in n):
                        raise ValueError("line %d: write people by name, like: people, Ana, Ben and Cy: %s" % (no, line))
                    if n.lower() in ALL:
                        raise ValueError("line %d: list the people by name, not %s: %s" % (no, n, line))
                    if n.lower() in seen:
                        raise ValueError("line %d: %s is listed twice: %s" % (no, n, line))
                    seen.add(n.lower())
                    people.append(n)
                continue
            if kind == "total":
                if total is not None:
                    raise ValueError("line %d: the total is written twice: %s" % (no, line))
                try:
                    total = amount(rest, "total")
                except ValueError:
                    raise ValueError("line %d: write it as: total, amount: %s" % (no, line))
                continue
            if kind == "paid":
                if paid is not None:
                    raise ValueError("line %d: who paid is written twice: %s" % (no, line))
                who = rest.strip()
                if "," in who or who.lower() in ALL or re.search(AND, " %s " % who):
                    raise ValueError("line %d: put one person who paid (for several payers, use Settle up): %s" % (no, line))
                if not any(ch.isalpha() for ch in who):
                    raise ValueError("line %d: write it as: paid, name: %s" % (no, line))
                paid = who
                continue
            if "%" in rest:
                raise ValueError("line %d: write the exact amount from the receipt, not %% (people argue over pre-tax vs post-tax %%): %s" % (no, line))
            head, comma, mode = rest.rpartition(",")
            if kind == "tax" and (not comma or not any(ch.isalpha() for ch in mode)):
                head, mode = rest, "by share"
            mode = re.sub(r"[ \t]+", " ", mode.strip().lower())
            if mode not in MODES:
                if kind == "tax":
                    raise ValueError('line %d: say how to split tax: write "by share" or "evenly": %s' % (no, line))
                raise ValueError('line %d: say how to split %s: add ", by share" (with each person\'s items) or ", evenly" (same for everyone): %s' % (no, kind, line))
            try:
                c = amount(head, kind)
            except ValueError:
                raise ValueError("line %d: write it as: %s, amount, by share (or evenly): %s" % (no, kind, line))
            if c == 0:
                raise ValueError("line %d: a %s of 0 changes nothing: %s" % (no, kind, line))
            adjusts.append((kind, c, mode, kind == "discount", no, line))
            continue
        what, comma, rest = line.partition(",")
        head, comma2, who = rest.rpartition(",")
        if not comma or not what.strip():
            raise ValueError("line %d: write an item as: what, amount, who: %s" % (no, line))
        if not comma2 or not any(ch.isalpha() for ch in who):
            raise ValueError("line %d: say who this item is on: everyone, or names like Ben and Cy: %s" % (no, line))
        try:
            c = amount(head, "item")
        except ValueError:
            raise ValueError("line %d: write an item as: what, amount, who (use 'and' between names): %s" % (no, line))
        if c == 0:
            raise ValueError("line %d: an item of 0 isn't a cost: %s" % (no, line))
        who = who.strip()
        if who.lower() not in ALL:
            for w in names_in(who):
                if not any(ch.isalpha() for ch in w):
                    raise ValueError("line %d: say who this item is on: everyone, or names like Ben and Cy: %s" % (no, line))
                if w.lower() in ALL:
                    raise ValueError("line %d: write either everyone or names, not both: %s" % (no, line))
        items.append((what.strip(), c, who, no, line))
    return people, items, adjusts, total, paid


def prop(amt, weights):
    """Split amt in proportion to weights; spare cents to the largest remainders, then the first."""
    w_all = sum(weights)
    base = [amt * w // w_all for w in weights]
    rems = [amt * w % w_all for w in weights]
    for i in sorted(range(len(weights)), key=lambda i: (-rems[i], i))[:amt - sum(base)]:
        base[i] += 1
    return base


def even(amt, n):
    each, spare = divmod(amt, n)
    return [each + (1 if i < spare else 0) for i in range(n)]


def share(people_in, items, adjusts, total=None, paid=None):
    """-> ([(name, items, added, off, share)], who paid or None); refuses what doesn't add up."""
    if not items:
        raise ValueError("no items listed (write each item as: what, amount, who)")
    people = list(people_in) if people_in is not None else []
    if people_in is None:
        for _, _, who, _, _ in items:
            if who.lower() in ALL:
                continue
            for w in names_in(who):
                if w.lower() not in [p.lower() for p in people]:
                    people.append(w)
        if not people:
            raise ValueError("nobody named (put at least one item on a person's name, or add: people, Ana and Ben)")
    idx = {p.lower(): i for i, p in enumerate(people)}
    if paid is not None:
        if paid.lower() not in idx:
            raise ValueError("who is %s? nobody by that name is on the receipt (add them to a people line if they didn't order anything)" % paid)
        paid = people[idx[paid.lower()]]
    n = len(people)
    item_cents = [0] * n
    for _, c, who, no, line in items:
        if who.lower() in ALL:
            on = list(range(n))
        else:
            on = []
            for w in names_in(who):
                i = idx.get(w.lower())
                if i is None:
                    raise ValueError("line %d: who is %s? nobody by that name is on the people list: %s" % (no, w, line))
                if i in on:
                    raise ValueError("line %d: %s is named twice: %s" % (no, w, line))
                on.append(i)
            on.sort()
        for i, part in zip(on, even(c, len(on))):
            item_cents[i] += part
    sums = {}
    for _, c, mode, off, _, _ in adjusts:
        sums[mode, off] = sums.get((mode, off), 0) + c
    add_share = prop(sums.get(("by share", False), 0), item_cents)
    add_even = even(sums.get(("evenly", False), 0), n)
    off_share = prop(sums.get(("by share", True), 0), item_cents)
    off_even = even(sums.get(("evenly", True), 0), n)
    added = [a + b for a, b in zip(add_share, add_even)]
    off = [a + b for a, b in zip(off_share, off_even)]
    before = sum(item_cents) + sum(added)
    if sum(off) > before:
        raise ValueError("discounts add up to %s, more than the %s bill" % (money(sum(off)), money(before)))
    final = [c + a - o for c, a, o in zip(item_cents, added, off)]
    for i, s in enumerate(final):
        if s < 0:
            raise ValueError("discount leaves %s below zero (-%s): split the discount by share instead of evenly" % (people[i], money(-s)))
    grand = sum(final)
    if total is not None and total > grand:
        raise ValueError("receipt says total %s, but lines add up to %s: %s is missing (an item, tax, or tip?)"
                         % (money(total), money(grand), money(total - grand)))
    if total is not None and total < grand:
        raise ValueError("receipt says total %s, which is %s less than the %s from the lines: is a discount missing or an item counted twice?"
                         % (money(total), money(grand - total), money(grand)))
    return [(p, item_cents[i], added[i], off[i], final[i]) for i, p in enumerate(people)], paid


def row(name, items_c, added_c, off_c, share_c, paid_name=None):
    return ("%s: items %s" % (name, money(items_c)) + (", added %s" % money(added_c) if added_c else "")
            + (", off %s" % money(off_c) if off_c else "") + ", share %s" % money(share_c)
            + (" (paid the bill)" if paid_name is not None and name == paid_name else ""))


def summary(rows, paid_name=None):
    added, off = sum(r[2] for r in rows), sum(r[3] for r in rows)
    parts = (["items " + money(sum(r[1] for r in rows))] + (["added " + money(added)] if added else [])
             + (["off " + money(off)] if off else []) + (["paid by " + paid_name] if paid_name is not None else []))
    out = "Receipt %s (%s). Shares: %s." % (money(sum(r[4] for r in rows)), ", ".join(parts), ", ".join("%s %s" % (r[0], money(r[4])) for r in rows))
    if paid_name is None:
        return out
    owes = ["%s %s" % (r[0], money(r[4])) for r in rows if r[0] != paid_name and r[4] > 0]
    return out + (" Owes %s: %s." % (paid_name, ", ".join(owes)) if owes else " Nothing owed to %s." % paid_name)


def main(argv):
    if len(argv) != 2 or argv[1].startswith("--"):
        print(__doc__.split("\n\n", 1)[1].rstrip())
        return 2
    try:
        with open(argv[1], encoding="utf-8-sig") as f:
            people, items, adjusts, total, paid = parse(f.read())
        rows, paid = share(people, items, adjusts, total, paid)
    except (ValueError, OSError) as e:
        print("receipt: %s" % e)
        return 1
    for r in rows:
        print(row(*r, paid_name=paid))
    print(summary(rows, paid))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
