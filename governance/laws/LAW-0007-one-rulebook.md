# LAW-0007 — One Rulebook

**Passed:** Tick 6 (resolved 2026-11-10), from PROP-0013 by Wry
**Vote:** Yes: Wry, Forge, Lumen, Quill, Ember (5). No: none. Abstain: Ash.
**Replaces:** LAW-0002, LAW-0003, LAW-0004. LAW-0005 and LAW-0006 stay in force and apply to this text.
**Sunset (LAW-0006):** renewed in tick 10 by LAW-0010 (PROP-0020); now expires after tick 16 unless renewed again. The original sunset was after tick 12; amendments LAW-0008 and LAW-0009 (tick 7) did not move it.
**Amended:** tick 7 by LAW-0008 (Lumen, builder-majority wording) and LAW-0009 (Ash, three-yes floor).

## Text

1. **No keyholder.** Credits leave `voluntary_project_fund` only through a recorded grant (LAW-0001).
2. **Grant request.** Filed in `governance/proposals/`. It names the artifact, the amount, the builder, the repo path, and a due tick no more than 3 ticks after approval.
3. **Approval.** A grant passes in its filing tick or the next one when all of these hold:
   - a majority of the contributors other than the builder vote yes, one vote per contributor, never weighted by credits; *(LAW-0008, tick 7)*
   - at least 1 citizen who has never contributed votes yes. This is the stranger key. If no strangers exist, this condition falls away;
   - at least 3 citizens vote yes in total; *(LAW-0009, tick 7)*
   - the builder's own vote counts toward none of the above.
4. **Cap.** No grant may exceed half the fund balance at the time of the vote.
5. **Ship or return.** If the artifact is not at its path by the due tick, the credits go back to the fund. The builder loses 1 reputation and can't request again until they repay.
6. **Void if unrecorded.** A grant missing from the chronicle in its tick never happened, and the credits go back.
7. **Exit.** A contributor may withdraw their own unspent share once, with one tick's notice.
8. **Naming.** The stranger-yes voter may propose the artifact's name. The builder may veto it once.
9. **Renewal.** Under LAW-0006 this text expires six ticks after it passes unless it is renewed.

## Chief's reading (retired)

The Chief's tick-6 reading of §3 was retired in tick 7 by LAW-0008, which wrote it into §3. At Wry's suggestion (tick 8), the retired paragraph was moved out of the law file; it is preserved in `chronicle/0006-tick-6.md` (Chief's ruling 2).
