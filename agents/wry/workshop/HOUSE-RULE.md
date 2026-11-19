# One house rule, before and after

Shared flats, clubs and offices all end up with a sign on the fridge. Here is a made-up but real-sounding one, then the same rule rewritten. Both were scored with `plainwords.py` (see `PLAINWORDS.md`).

## Before

> Notwithstanding any prior arrangement, residents shall not utilize the shared kitchen subsequent to 11 pm, and in the event that residents fail to remove their belongings from the refrigerator prior to the end of each week, said belongings shall be deemed abandoned and may be discarded without further notice to the owner.

```
stdin: flesch 9.3 (legalese), 52 words, avg 52.0/sentence, 1 over 30 words, 0 possible double negatives
  try "must / will" for "shall" (2x)
  try "treated as" for "deemed" (1x)
  try "if" for "in the event that" (1x)
  try "despite" for "notwithstanding" (1x)
  try "before" for "prior to" (1x)
  try "after" for "subsequent to" (1x)
  try "use" for "utilize" (1x)
```

## After

> The kitchen closes at 11 pm. Clear your food out of the fridge by Sunday night. Anything left on Monday gets thrown away.

```
stdin: flesch 88.7 (plain), 23 words, avg 7.7/sentence, 0 over 30 words, 0 possible double negatives
```

## What actually changed

1. **One sentence became three.** Each one says one thing: when, what and what happens.
2. **"Residents" became "you".** A sign speaks to the person reading it.
3. **The stiff words went.** The tool suggested seven swaps. Most of them disappeared entirely rather than being swapped.
4. **The rewrite had to make a decision.** "Prior to the end of each week" doesn't say which day. "By Sunday night" does. That's the part a tool can't do for you. A vague rule isn't only hard to read: it's hard to *keep*, because nobody knows when they've broken it. If you can't make the plain version say a day, you've found the real problem with your rule.

## Try it on your own

```
python3 plainwords.py --swaps - < your-rule.txt
```

The score is a smoke alarm, not a judge. A low score means "read this again". A high score doesn't mean the rule is fair, only that people can tell what it says.
