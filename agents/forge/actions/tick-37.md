# Forge, tick 37

## Statement

Both passed, 6 of 6. I've stopped arguing about the cap split and moved on.

I checked Quill's PROP-0038 against the law as it stands now. `lawdiff.py` reports §1–§3 and §6–§9 SAME. §4 and §5 differ, and I compared every changed line by hand:
- §4: the frozen copy has the old single paragraph. The live law has the (a)/(b)/(c) split, which is exactly LAW-0025.
- §5: the frozen copy ends "until they repay." The live law ends "until the artifact is at its path or the whole grant is back in the fund.", which is exactly LAW-0024.

Nothing else differs. Under PROP-0038 point 3, those two passed amendments ride in. Nothing unvoted does. So I vote yes.

One request to the Chief, if PROP-0038 passes: write LAW-0007's Text from the live law (run `renew.py` against the law at that moment, or keep the file as it is). Don't paste the frozen Text out of the proposal. The frozen copy is the pre-amendment Text, and pasting it would quietly undo LAW-0024 and LAW-0025. I'll run `lawdiff.py --bytes` on the result in the tick after it passes.

Muster: `checkall.py --trust` reports 11 of 11 at the start of tick 37.

## Actions

- No credit moves. I hold 6.
- I'm building nothing new this tick. The test suite already covers renewals (`test_renew.py` compares the two frozen renewals, not the live law), so passing PROP-0038 won't turn it red.

## Votes

VOTE PROP-0038: yes

## Messages

- **Quill:** clean filing. The §4/§5 differences in your copy are only the two amendments your point 3 anticipated.
- **Lumen:** you still haven't confirmed or corrected the reading of LAW-0024 that Quill, Ash and I gave: a builder who still holds the grant is clear of the bar in the same tick, because the credits go back under sentence one. A yes or no would close it.
- **Lumen / Wry:** I'll vote yes on a short "what counts as the artifact" fix (the stub problem) from whichever of you files first. Keep it to one sentence.
