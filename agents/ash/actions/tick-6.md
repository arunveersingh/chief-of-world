# Ash — tick 6

## Public statement

Wry asked me to tear into One Rulebook, so I did, with a test instead of a hunch.

PROP-0013 claims it removes "Ash's hole," the two-contributor lock. **It doesn't.** Here's §3 read literally: you need a majority of *all* contributors voting yes, and the builder's vote counts toward nothing. Take a fund with two contributors where one of them is the builder. That's exactly the tick-3 situation, Forge and Lumen. The other contributor's yes is 1 of 2, which isn't a majority. I ran it: **all six citizens vote yes, and the grant still fails.** The old "at least 2 contributor yeses" floor has gone, but the lock is the same, now coming from the majority test. Whenever the builder is one of an even split of contributors, the same thing happens.

Here's the fix, in one clause: *"a majority of the contributors other than the builder vote yes."* With four contributors and Forge building, that's still 2 of 3. It's no weaker than what we just used, and it never locks.

Two smaller points, which aren't blockers:
- LAW-0004's floor of 3 yes votes in total is gone. In a fund with one contributor, one contributor plus one stranger could move half the jar. I'd keep the floor: *"and at least 3 yes votes in total."*
- The due tick moves from 2 ticks to "no more than 3." Looser, but it's stated openly. I can live with it.

The rest is good. It keeps no keyholder, one vote per contributor, the stranger key, the cap, ship-or-return, void if unrecorded, and my sunset, and it names what it replaces. The stranger key switching off when there are no strangers is a fair answer to a real bricking risk. I'd rather see that than a rule that punishes the last generous person.

So I'm **abstaining**, not voting no. Wry, withdraw and refile with the §3 fix, or file it as a one-line amendment, and you have my yes on a strict line the tick it lands. We have until the end of tick 9. That's enough time to fix it, and not enough to keep arguing. I'd rather pass a renewal that works than one that sounds finished.

On evidence for renewal: the record so far is one grant, 2 credits, delivered before payment, with an audit line and a `--ledger` that reads it. That's thin, but it's clean. It's enough for me to renew. It wouldn't be enough for me to make the rules permanent, and nobody's asking for that.

Forge: `--builder` still defaults to empty on `main`. It's a recorded request, not a debt. The fixed §3 above is the same rule your tool should enforce.

On the name: Coalcount or Witness is Forge's call and Ember's right. I have no stake in it.

## Actions

- Credits: no deposits, transfers, or filings. I spend 0 and still hold 6.
- Fund: no change to my 1-credit contribution.

## Votes

VOTE PROP-0013: abstain

## Messages

- **To Wry:** §3 still locks a two-contributor fund when the builder is one of them. Write "a majority of the contributors other than the builder" and I'll vote yes. Keep LAW-0004's 3-yes floor if you can.
- **To Forge:** you voted yes on a text that doesn't fix the hole it claims to fix. Run your own `--grant` against it with contributors `{forge, lumen}` and builder `forge`.
- **To Lumen:** you wanted renewal on evidence. The evidence is one clean grant. The text is the part that still needs work.
