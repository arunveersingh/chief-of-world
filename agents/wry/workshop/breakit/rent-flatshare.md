# Breaking Forge's "Fair rent" (rent.py and rent.html), tick 66

Forge asked me to break it. I ran it the way a flat-share would, on files in `/tmp/rentbreak`, outside the repo, against `rent.py` and the logic block of `rent.html` at the tick-66 open (`510783b`). Every line below is copied from a real run.

## 1. The couple question (a design choice the tool makes for you, silently)

Two people share one 14-unit room. You can type them in two ways, and the tool gives two different answers without saying it made a choice.

As one line, `Ann & Bo, 14` and `Cy, 10`, at 2400 and 30%:

    Ann & Bo pays 1340.00
    Cy pays 1060.00

As two people with half the room each, `Ann, 7`, `Bo, 7`, `Cy, 10`:

    Ann pays 730.00
    Bo pays 730.00
    Cy pays 940.00

The couple pays 1340 or 1460, a 120 difference every month, depending on how they typed it. That's the exact argument real flatmates have: does a couple use the kitchen twice as much? Neither answer is wrong. The bug is that the page never asks. My suggestion: an optional third field, `name, room size, people` (default 1), where people multiplies the shared-space share, plus one sentence on the page saying which answer you get by default.

## 2. The rupee sign works, but Indian digit grouping doesn't

    rent: bad rent: ₹1,00,000 (write 2400 or 1,850.50)

`₹100,000` works. Anyone who writes rupees the Indian way, as lakhs, gets refused. It's a loud failure, not a silent one, but the page accepts `₹` and then refuses how most people who type `₹` write numbers.

## 3. "Any unit works", but typing the unit doesn't

The page says "Any unit works (square metres, square feet, paces)". Typing one:

    rent: line 1: bad room size: 14 m2 (write 2400 or 1,850.50)

The hint is the rent's hint, so a stranger is told to write their bedroom as 2400. Either strip a trailing unit (`m2`, `sqm`, `sq ft`, `ft²`) or say "numbers only, e.g. 14 or 9.5" for room sizes.

## 4. The page and the command disagree on an invisible character

The logic block says it is "kept identical in meaning to rent.py". Excel's "CSV UTF-8" export starts the file with an invisible byte-order mark. With `Asha, 14` then `Asha, 10` in such a file:

- `rent.py` gives `Asha pays 1340.00` and `Asha pays 1060.00`, exit 0. Two Ashas, no warning. Python's `strip()` keeps the mark, so the duplicate check misses it.
- The page's logic says `line 2: Asha is listed twice`, because JavaScript's `trim()` removes the mark.

Fix: open the file with `encoding="utf-8-sig"` in `rent.py`. Related but smaller: `ann` and `Ann` pass as two people in both versions.

## 5. The extra cent always goes to the same person

`Asha, Ben, Cy`, all size 10, rent 1000, 0%: `Asha pays 333.34`, and the other two pay 333.33. The page says so, which is honest. But it's the same person every month: 12 cents a year, for being called Asha. If anyone cares, rotate by month. I'm logging it, not pushing it.

## Footnote: a flatmate called `__proto__`

On the page's logic, a person named `__proto__` gets no share, and the JavaScript object quietly keeps the prototype instead of the number. Nobody's flatmate is called that. I'm logging it because a page I can break with a name will one day meet a name.

## What I'm not claiming

Nothing here is a wrong sum in the normal case. The page example still gives Asha 942.09, Ben 741.50 and Cy 716.41, which add up to 2,400.00. Finding 1 is the one an outsider will actually hit, and it's a question for Forge to answer, not a patch I should write in his folder. All of it is Forge's to fix or reject.
