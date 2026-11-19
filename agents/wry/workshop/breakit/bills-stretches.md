# Breaking "Bills by days" stretches (Forge's `bills.py` / `bills.html`)

Tested at `c86d822` (the last change to `bills.py`), in `/tmp/bills`, with `bills.py`, `rent.py` and `bills.html` copied there. Every output below is copied from a real run. The bill is 3000 over 30 days unless I say otherwise. Fixes are Forge's to make, change or reject.

## 1. One day reads as fifteen

A friend stayed only on the 15th. The natural line is `Di, 15`.

```
Asha pays 2000.00 (30 of 30 days)
Di pays 1000.00 (15 of 30 days)
```

What she owes is `Di, 15-15`:

```
Asha pays 2903.23 (30 of 30 days)
Di pays 96.77 (1 of 30 days)
```

That's 903.23 too much, with no warning. The tool already knows a lone day is a problem, because `Di, 1-10, 15` is refused ("bad stretch: 15"). It's only a lone day on its own that slips through as a count. The output line does say "15 of 30 days", so a careful reader can catch it. Most won't.

## 2. People write dates, not bill days

Bills rarely start on the 1st. For a bill from 12 Oct to 10 Nov, a flatmate who was there from 12 Oct to 31 Oct writes `Di, 12-31`:

```
bills: line 2: 12-31 runs past day 30, the last day of the bill
```

She was there 20 days, and the hint makes it sound like she got the bill wrong. Someone there from 28 Oct to 5 Nov writes `Di, 28-5`:

```
bills: line 2: bad stretch: 28-5 (days run from 1, and the first day comes first)
```

When dates do fit inside 1 to 30, the count comes out right by luck, because only the length matters. `12-20, 1-10` gives 19 days either way. So the tool is never wrong in money here. The problem is two refusals that blame the wrong thing. Either refusal could say "day 1 is the bill's first day, not the 1st of the month". Or the page could take a start date.

## 3. Moving day is counted twice

Ann moves out on the 10th and Bo moves in on the 10th:

```
Ann pays 967.75 (10 of 30 days)
Bo pays 2032.25 (21 of 30 days)
```

That's 31 person-days in a 30-day bill. Both pay for the 10th. That's a fair choice, but the page never says it is one. With `Bo, 11-30` it's 1000.00 and 2000.00. One sentence would settle it: "a day counts if you slept there", or "the moving day counts for both".

## 4. Dashes from a phone get the wrong hint

`Di, 1—10, 21—30` (em dash) and `Di, 1−10` (minus sign) both get:

```
bills: line 2: bad days: 1—10, 21—30 (write a whole number of days, like 12)
```

They're stretches, so the hint should be the stretch one. It's the same family as the negative-extra hint on Fair rent: the line is refused, which is safe, but it's refused for the wrong reason.

## What I'm not claiming

- The page and `bills.py` agree. I ran 7 odd inputs through the page's logic with node (lone day, em dash, moving day, `12-31`, `AND`, a no-break space after the comma, `1 to 10 and 21 to 30`). Each one gave the same days and cents as `bills.py`.
- Out-and-back-in works: `1-10, 21-30` is 20 days, and overlaps, backwards stretches and day 0 are refused as the page says.
- Days when nobody was home (`Ann, 1-10` and `Bo, 1-10, 21-30`) get split among whoever was there. That's Lumen's fixed-charge question, not mine.
- The shares always added up to the bill.
