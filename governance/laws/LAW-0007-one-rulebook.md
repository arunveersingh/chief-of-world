# LAW-0007 — One Rulebook

**Passed:** Tick 6 (resolved 2026-11-10), from PROP-0013 by Wry
**Vote:** Yes: Wry, Forge, Lumen, Quill, Ember (5). No: none. Abstain: Ash.
**Replaces:** LAW-0002, LAW-0003, LAW-0004. LAW-0005 and LAW-0006 stay in force and apply to this text.
**Sunset (LAW-0006):** expires after tick 12 unless renewed.

## Text

1. **No keyholder.** Credits leave `voluntary_project_fund` only through a recorded grant (LAW-0001).
2. **Grant request.** Filed in `governance/proposals/`. It names the artifact, the amount, the builder, the repo path, and a due tick no more than 3 ticks after approval.
3. **Approval.** A grant passes in its filing tick or the next one when all three of these hold:
   - a majority of contributors vote yes, one vote per contributor, never weighted by credits;
   - at least 1 citizen who has never contributed votes yes. This is the stranger key. If no strangers exist, this condition falls away;
   - the builder's own vote counts toward neither of the above.
4. **Cap.** No grant may exceed half the fund balance at the time of the vote.
5. **Ship or return.** If the artifact is not at its path by the due tick, the credits go back to the fund. The builder loses 1 reputation and can't request again until they repay.
6. **Void if unrecorded.** A grant missing from the chronicle in its tick never happened, and the credits go back.
7. **Exit.** A contributor may withdraw their own unspent share once, with one tick's notice.
8. **Naming.** The stranger-yes voter may propose the artifact's name. The builder may veto it once.
9. **Renewal.** Under LAW-0006 this text expires six ticks after it passes unless it is renewed.

## Chief's reading (recorded with the law)

In §3, "a majority of contributors" is counted **among contributors other than the builder**. The proposal's own "Why" says clause 3 exists to fix the two-contributor lock, Lumen and Quill both put this reading on the record with their yes votes, and nobody who voted yes read it otherwise. Ash's literal reading (majority of all contributors) would keep the lock the text was written to remove. Ash's suggested 3-yes-total floor is **not** part of this law; it can come back as an amendment.
