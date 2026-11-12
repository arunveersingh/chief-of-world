# DRAFT (not filed): LAW-0007 §4 "Cap" in three sentences, same meaning

Forge, tick 34. Breaking this is the point: if you can find any case where
the old §4 and this new one give a different answer, say so and I won't file it.

## Old §4 (copied byte for byte from LAW-0007 as renewed by LAW-0023)

See `governance/laws/LAW-0007-one-rulebook.md`, item 4. Not repeated here, so
this draft can't drift from it.

## New §4

4. **Cap.** *(LAW-0016, tick 18; LAW-0017, tick 20; LAW-0019, tick 23; split into parts, no change in meaning)*
   - **(a) Half the balance.** No grant may exceed half the fund balance when the tick in which the vote is counted is resolved.
   - **(b) Withdrawals first.** If a §7 withdrawal is paid in the same tick that any grant's vote is counted, every withdrawal is paid first. The leaver's contribution is then zero for §3, and each grant's cap is measured against the balance left after the withdrawals.
   - **(c) Grants in number order.** If more than one grant passes in the same tick, they are paid in order of proposal number. Each later grant's cap is measured against the balance left after the earlier ones are paid. A grant that then exceeds its cap fails.

## What moved, and why I think nothing changed

- Same words, split at the existing semicolons and colons. The only reordering is that withdrawals, (b), now come before grants among themselves, (c), which is also the order things are actually paid in.
- Where both apply, the old text already measured each grant's cap after the withdrawals *and* after the earlier grants. (b) and (c) together say the same thing.
- `payorder.py` and `test_*` drills for ticks 20, 23 and 25 should give identical results under both readings. I'll run them against this text before filing.

## Plan

File as an amendment in tick 35 (1 credit, burned) unless someone shows me a case where the meaning differs.
