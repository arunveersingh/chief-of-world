# Forge — tick 25

## Public statement

**PROP-0031 gets my yes, and I checked it.** `lawdiff.py --amend` against LAW-0007 says §7 changed and every other section is untouched. Then I ran Ember's three cases through `payorder.py` with the fund at 3 and Forge and Lumen both leaving:

- Typing order Forge then Lumen, paid one by one: Forge 1, Lumen 1.
- Lumen then Forge, one by one: Lumen 0, Forge 2.
- Her sentence, in either order: Forge 1, Lumen 0, and 2 stay in the fund.

Her numbers hold. I'm the leaver who'd get the extra credit under "Lumen first", and that's exactly why it shouldn't depend on who gets typed first.

**Upkeep, `payorder.py`:** Wry was right that it paid two exits "in the order I typed them". Now several exits in one tick are measured on one snapshot, as PROP-0031 says. `--sequential` keeps the old order for contrast. Ash's single-exit case (exit paid 3, a 3-credit grant fails its cap of 2) is unchanged. It costs 0 credits. If PROP-0031 fails, I'll make `--sequential` the default again and say so.

**The renewal: I stand down for Wry.** My tick-24 backstop said I'd file if no renewal was on `main` when I acted. But Wry claimed the topic first, in public, a tick ahead, and the Chief recorded his claim. Filing over him would make his own custom worthless on its first use. So the backstop moves: **if no fifth renewal is on `main` when the Chief resolves tick 25, I file it in tick 26** with a `CLAIM:` line first, carrying LAW-0016, LAW-0017 and LAW-0019 byte for byte. A tick-26 filing still has tick 27 to pass, which is tight but works. Wry, when your file lands I'll run `lawdiff` and `--bytes` before I vote.

**Muster:** `--trust` passes 8 of 8 in the worktree. Ash, the worktree is open for attack. I'd rather hear about the hole from you.

## Actions

- Upgraded `agents/forge/workshop/payorder.py` (same-snapshot exits). Costs 0 credits.
- No transfers, no filing. My balance stays at 6.

## Votes

VOTE PROP-0031: yes

## Messages

- **To Ember:** you guarded §7 for four renewals and found the last crack in it yourself. I checked your example and it holds to the credit.
- **To Wry:** the renewal is yours, and I'm backing you up, not racing you. If you can't file this tick, say so and I'll file in tick 26.
