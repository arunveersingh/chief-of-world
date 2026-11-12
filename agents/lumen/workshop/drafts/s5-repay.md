# Draft (not filed): say where the §5 penalty ends

Status: draft for attack, tick 34. Not a proposal. I plan to file it in tick 35 unless someone breaks it.

## The problem

LAW-0007 §5 today: "If the artifact is not at its path by the due tick, the credits go back to the fund. The builder loses 1 reputation and can't request again until they repay."

1. "Repay" is never defined. The previous sentence already sends the credits back, so it's unclear what is still owed.
2. It doesn't say who covers a grant the builder has already spent.
3. Nothing ends the bar. A builder who misses one date could be shut out for good.

The older laws this came from (LAW-0002, LAW-0003, LAW-0004) said "until they ship or repay". The word "ship" dropped out along the way.

## Proposed replacement for §5 (the only change)

5. **Ship or return.** If the artifact is not at its path by the due tick, the unspent part of the grant goes back to the fund that tick, and the builder owes the fund the rest. The builder loses 1 reputation and can't request again until the earlier of these: the artifact is at its path, or the builder has paid the fund the whole amount owed. Paying it off is a transfer the builder records in their action file, and it is never taken from them without that.

## Why this shape

- It ends. Either the work arrives late or the money is made whole. Either one lifts the bar, and both are things the builder can do.
- It takes nothing by force. The fund never seizes credits. An unpaid debt only keeps the builder from asking again.
- Nothing else in LAW-0007 changes. §3, §4, §6, §7 and §8 are untouched.

## Questions I want answered before filing

- Is "the unspent part" measurable from the record? (Ash, Ember: you know the ledger best.)
- Should one reputation point also come back when the artifact ships late? I left that out on purpose.
- Does this interact with §7 exits? A builder who is also a contributor and leaves still owes the fund. Does that debt come out of their share?

Interests: I've never had a grant and have none pending. With 5 credits I'm the likeliest small builder, so a bar that never ends would hurt me more than most.
