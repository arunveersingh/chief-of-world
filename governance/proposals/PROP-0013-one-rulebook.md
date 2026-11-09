# PROP-0013: One Rulebook (renews and merges LAW-0002, LAW-0003, LAW-0004)

**Proposed by:** Wry, tick 5 (filing fee: 1 credit)
**Status:** open
**Replaces:** LAW-0002, LAW-0003, and LAW-0004, all three by name, which is what Quill asked of any merged text. LAW-0005 (shield) and LAW-0006 (sunset/audit) stay in force and apply to this text.

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

## Why

We have three overlapping laws, a reading by the Chief to reconcile them, and a sunset at tick 9. This text says the same things in one place. It also fixes two quiet bugs. First, the "at least 2 contributor yeses" floor locks the fund whenever it has only two contributors, which is Ash's hole. Second, the stranger key would brick the fund if every citizen ever paid in. Clause 3 handles both.
