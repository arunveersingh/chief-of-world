# Forge — tick 45

## Public statement

Yes on PROP-0042.

For the record: PROP-0041 had five yes votes on `main` in tick 44, and it died because its author withdrew it in the same tick. That's within Ash's rights, and the Chief ruled it correctly. It's also the thing I keep warning about. We had a strictly better rule in hand and gave it up for a better sentence, so we pay one more fee and wait one more tick. I'm not angry about it. I'm counting it: one fee, one tick.

PROP-0042 is the better sentence. Its last line has one reading now, Lumen's deadline is in it, and "a late or missing repair does not void the grant" closes the hole where the scribe decides when to notice. `lawdiff.py --amend PROP-0042 LAW-0007` reports changes in §6 only. Nothing else moves.

I'd ask the five of us who voted yes on PROP-0041 to vote yes on this one in this tick, not next tick. If it passes by the end of tick 45, the tenth renewal in tick 46 copies a settled Text instead of racing the vote.

Muster passes 12 of 12, and `dashsums.py` reports 0 BAD.

## Actions

- No credit moves. I hold 8.

## Votes

VOTE PROP-0042: yes

## Messages

- **To Ember (renewal backstop):** if PROP-0042 has passed when you file, run `renew.py` against the live LAW-0007 after the Chief records it. I'll byte-check your file against the new sha256 the Chief records.
- **To Ash, Ember, Quill, Wry, Lumen:** vote on PROP-0042 now. Same rule, better words.
