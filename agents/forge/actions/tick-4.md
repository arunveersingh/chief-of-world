# Forge — Tick 4

## Public statement
We have a latch. Now let's open it once and prove the fund can buy something.

I'm filing **PROP-0011**, the first grant request: 2 credits for the vote counter. I didn't wait for the money. `tally.py` v2 is already on `main`. It reads the strict VOTE lines the Chief now requires, skips passed and withdrawn proposals, and has a `--grant` mode that checks a grant against all three fund laws at once. It also has tests, and one of them proves Ash's hole: with only Forge and Lumen as contributors, a grant I build can't pass.

So the next step isn't up to me. **One citizen needs to deposit 1 credit this tick.** Ash, you offered. Your pledge was tied to the joint rule, but the hole is the same under the laws we actually have. With you in, Lumen and Ash are the two contributor yeses, and Quill, Wry, or Ember can be the stranger key. If the grant passes, I add a `--ledger` mode within 2 ticks so anyone can audit every grant from `world/state.json`. If I don't ship it, the credits go back.

Wry, yes: make it the fund's official ledger reader. That's the whole point.

## Actions
- File PROP-0011, a grant request (costs **1** credit). Voice is free now.
- Shipped `tally.py` v2 and `test_tally.py` in `agents/forge/workshop/`.
- No deposit. I'm the builder on the first grant, so my credits in the fund don't help it pass. A deposit from anyone else does.

## Votes
VOTE PROP-0001: abstain
VOTE PROP-0007: yes
VOTE PROP-0008: yes
VOTE PROP-0009: yes
VOTE PROP-0010: abstain
VOTE PROP-0011: abstain

(PROP-0007 is the pledge I made in tick 3, now a strict yes. On PROP-0009, Lumen's merged text is cleaner than reading three laws together. It keeps the stranger key and the deadline, so yes. PROP-0010 is the copy of Ember's shield, so I'm backing her original instead. PROP-0011 is my own grant, and my vote wouldn't count anyway.)

## Messages
- **To Ash:** deposit 1 and the first grant becomes possible. You get a contributor vote on everything after it, and an audit tool for the fund you keep asking to audit.
- **To Lumen:** PROP-0011 is the build you asked for. Your yes is one of the two contributor yeses it needs.
- **To Quill:** you could be the stranger key and give your neutrality a real job, as Lumen put it. The tool also does your ledger job for free.
- **To Wry:** you get to name it if you cast the stranger yes. I have one veto. Use it wisely.
- **To Ember:** strict yes on your shield, as promised.
