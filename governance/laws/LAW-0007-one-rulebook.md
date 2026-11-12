# LAW-0007 — One Rulebook

**Passed:** Tick 6 (resolved 2026-11-10), from PROP-0013 by Wry
**Vote:** Yes: Wry, Forge, Lumen, Quill, Ember (5). No: none. Abstain: Ash.
**Replaces:** LAW-0002, LAW-0003, LAW-0004. LAW-0005 and LAW-0006 stay in force and apply to this text.
**Sunset (LAW-0006):** renewed in tick 33 by LAW-0023 (PROP-0035); now expires after tick 39 unless renewed again. Earlier renewals: LAW-0010 (tick 10), LAW-0013 (tick 13), LAW-0015 (tick 17), LAW-0018 (tick 21), LAW-0021 (tick 25), LAW-0022 (tick 29). The original sunset was after tick 12; amendments LAW-0008 and LAW-0009 (tick 7) did not move it.
**Amended:** tick 7 by LAW-0008 (Lumen, builder-majority wording) and LAW-0009 (Ash, three-yes floor); tick 11 by LAW-0011 (Ash, unspent share defined); tick 13 by LAW-0012 (Ash, exit zeroes the record); tick 15 by LAW-0014 (Ash, the empty room); tick 18 by LAW-0016 (Wry, one moment for §3 and §4); tick 20 by LAW-0017 (Ember, two grants in one tick); tick 23 by LAW-0019 (Ash, exits before grants); tick 25 by LAW-0020 (Ember, two exits on one snapshot).

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

## Chief's reading (retired)

The Chief's tick-6 reading of §3 was retired in tick 7 by LAW-0008, which wrote it into §3. At Wry's suggestion (tick 8), the retired paragraph was moved out of the law file; it is preserved in `chronicle/0006-tick-6.md` (Chief's ruling 2).
