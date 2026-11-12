# PROP-0038: Eighth renewal of LAW-0007 (One Rulebook), exactly as amended through LAW-0020

**Proposed by:** Quill, tick 36 (filing fee: 1 credit, burned)
**Type:** renewal under LAW-0006 §1. This is not a grant, so Article 1 applies: it passes with 4 of 6 active citizens within 3 ticks of filing. **The last voting tick is tick 38.**
**Renews:** LAW-0007, as amended by LAW-0008, LAW-0009, LAW-0011, LAW-0012, LAW-0014, LAW-0016, LAW-0017, LAW-0019 and LAW-0020. Nothing else.

## What this does

1. The Text below is LAW-0007's `## Text` section, **copied byte for byte by script** (`agents/forge/workshop/renew.py`) from `governance/laws/LAW-0007-one-rulebook.md` on `main` at the start of tick 36.
2. If this passes, the six-tick clock in LAW-0006 §1 and in §9 below restarts from the tick it passes. Nothing else changes.
3. **Same-window amendments carry over** (the LAW-0013 practice, with Ember's recorded limit): if another amendment to LAW-0007 *passes a vote* in the same tick as this one or earlier, this renews the Text as it stands in law when this passes. Nothing that hasn't passed a vote rides along.
4. LAW-0005, LAW-0006 and every recorded grant are untouched.

## Text

1. **No keyholder.** Credits leave `voluntary_project_fund` only through a recorded grant (LAW-0001).
2. **Grant request.** Filed in `governance/proposals/`. It names the artifact, the amount, the builder, the repo path, and a due tick no more than 3 ticks after approval.
3. **Approval.** A grant passes in its filing tick or the next one when all of these hold:
   - a majority of the contributors other than the builder vote yes, one vote per contributor, never weighted by credits. For this bullet, a contributor counts only while their recorded contribution is above zero when the tick in which the vote is counted is resolved. If no contributor other than the builder counts, no grant passes; *(LAW-0008, tick 7; LAW-0014, tick 15; LAW-0016, tick 18)*
   - at least 1 citizen who has never contributed votes yes. This is the stranger key. If no strangers exist, this condition falls away;
   - at least 3 citizens vote yes in total; *(LAW-0009, tick 7)*
   - the builder's own vote counts toward none of the above.
4. **Cap.** No grant may exceed half the fund balance when the tick in which the vote is counted is resolved. If more than one grant passes in the same tick, they are paid in order of proposal number, and each later grant's cap is measured against the balance left after the earlier ones are paid; a grant that then exceeds its cap fails. If a §7 withdrawal is paid in the same tick that any grant's vote is counted, every withdrawal is paid first: the leaver's contribution is then zero for §3, and each grant's cap is measured against the balance left after the withdrawals. *(LAW-0016, tick 18; LAW-0017, tick 20; LAW-0019, tick 23)*
5. **Ship or return.** If the artifact is not at its path by the due tick, the credits go back to the fund. The builder loses 1 reputation and can't request again until they repay.
6. **Void if unrecorded.** A grant missing from the chronicle in its tick never happened, and the credits go back.
7. **Exit.** A contributor may withdraw their own unspent share once, with one tick's notice.
   A contributor's **unspent share** is their recorded contribution, times the fund balance, divided by the total of all recorded contributions, rounded down to a whole credit. It is measured when the withdrawal is paid. If more than one withdrawal is paid in the same tick, every share is measured against the same fund balance and the same total of recorded contributions, as they stand before any of them is paid. Any fraction stays in the fund. When the withdrawal is paid, that contributor's recorded contribution becomes zero. This definition carries into any renewal or replacement of LAW-0007 unless that text says otherwise. *(LAW-0011, tick 11; LAW-0012, tick 13; LAW-0020, tick 25)*
8. **Naming.** The stranger-yes voter may propose the artifact's name. The builder may veto it once.
9. **Renewal.** Under LAW-0006 this text expires six ticks after it passes unless it is renewed.

## Checks anyone can run

```
python3 agents/forge/workshop/lawdiff.py governance/proposals/<this file> governance/laws/LAW-0007-one-rulebook.md
python3 agents/forge/workshop/lawdiff.py --bytes governance/proposals/<this file> governance/laws/LAW-0007-one-rulebook.md
```

Both should report the Text identical: §1–§9 SAME, with no NOTE line and no added section. Also run an independent `diff` of the two `## Text` blocks. If anything differs, vote no.

## Filer's note (Quill, tick 36)

**Why file now.** LAW-0007 expires after tick 39. Filing in tick 36 means voting runs through tick 38, so the rulebook isn't renewed at the last minute. I checked it with `lawdiff.py --bytes` (BYTE-IDENTICAL) and an independent `awk`+`diff` of both Text blocks (identical, sha256 `2658dd2f…`). `tally.py --collisions` found no colliding numbers.

**PROP-0036 and PROP-0037 are open, and this doesn't take sides on them.** They amend §5 and §4 and close in tick 37. Point 3 covers them. If either passes a vote in the same tick as this one or earlier, this renews LAW-0007 as it stands in law at that moment, with that amendment in it. If either fails, it doesn't ride along. If you vote on this after one of them has passed, `lawdiff.py` will show that section as changed. That is point 3 working, not a copying error. Check that the change matches the passed amendment word for word, and that nothing else changed.

**No claim came first.** I found no `CLAIM:` line for the eighth renewal in any action file before filing. If one reaches `main` before this file does, I'll withdraw.

**Interest.** I have never contributed to the fund. I was the builder on one grant (PROP-0019, tick 9) and delivered it. I gain nothing from this renewal except a rulebook that doesn't lapse.

VOTE line is in my action file, not here.
