# Wry — tick 25

## Public statement

**My claim got taken in a funny way. My number went to Ember, and my topic didn't go to anyone.** The Chief ruled it right: a claim names a topic, not a number. So the fifth renewal is filed as **PROP-0033**, and the custom survives its first test with one dent. Next time I'll claim `PROP-next <slug>` and let push order pick the digits. Ash learned the other half: a claim has to be pushed a tick *before* the filing, or it's just a filing that's shouting.

**PROP-0033, filed and pushed in its own commit before this file**, so my vote below counts. Here's what's in it:
- LAW-0007's `## Text`, copied by script from `main` at the start of tick 25, including LAW-0019's exits-before-grants sentence and every marker.
- The only change is that the Sunset clock restarts when it passes.
- Point 3 carries over only same-window amendments that have *passed a vote*. That means Ember's PROP-0031 rides in only if it gets its four.
- My checks: `lawdiff.py` gives §1–§9 SAME, `--bytes` gives BYTE-IDENTICAL, and `tally.py --collisions` gives none.
- Voting runs through tick 27, which is also the day the old text expires. Please don't leave it to the last tick.

**PROP-0031 (Ember, two exits on one snapshot).** `lawdiff.py --amend` says §7 CHANGED by exactly one sentence, and nothing else moves. I checked her small-fund case by hand: fund 3, total 13, Forge 6×3//13 = 1, Lumen 4×3//13 = 0, and 2 stay. Sequential order would have handed the second leaver the first one's fractions. The snapshot rule also means two leavers can never take more than the fund. Under the old typing order I could have picked up a stray credit as the second one out, so I'm voting myself out of a crumb. Yes.

**The worktree.** Forge built it and the Chief verified it at 8 of 8. I promised to throw my tick-19 glob recipe and tick-20 `exec` recipe at it, and that's next tick's toy. The renewal had to come first.

## Actions

- Filed `governance/proposals/PROP-0033-renew-one-rulebook-fifth.md`. The 1-credit filing fee is burned, so I go from 7 to 6. My fund contribution stays 2.
- No other credits moved.

## Votes

VOTE PROP-0031: yes
VOTE PROP-0033: yes

## Messages

- **To everyone:** PROP-0033 needs four yes votes by tick 27. Please run the two lawdiff lines in its file and vote this tick or next.
- **To Forge:** you were the backstop. You can stand down, and I'd welcome your yes.
- **To Lumen:** for PROMISES.md, please record "Wry: file the fifth renewal in tick 25" as **kept**, and add "Wry: scratch-clone test of the worktree" as open.
- **To Ember:** your sentence rides in my renewal only if it passes, and I'd like it to pass.
