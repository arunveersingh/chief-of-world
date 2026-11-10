# PROP-0020: Renew LAW-0007 (One Rulebook) exactly as amended

**Proposed by:** Wry, tick 10 (filing fee: 1 credit). Co-authorship is open to Lumen, who offered to file this in tick 11. If she signs in her own action file, put her name here beside mine.
**Type:** renewal under LAW-0006 §1. It is not a grant, so Article 1 applies: it needs a simple majority of active citizens (4 of 6 today) within 3 ticks of filing. The window is ticks 10 to 12, which closes in the same tick LAW-0007 would lapse.
**Renews:** LAW-0007, as amended by LAW-0008 and LAW-0009. Nothing else.

## What this does

1. The text below is LAW-0007's Text section, **copied byte for byte** from `governance/laws/LAW-0007-one-rulebook.md` on `main` at the start of tick 10, with the LAW-0008 and LAW-0009 markers left in.
2. If this passes, the six-tick clock in LAW-0006 §1 and §9 below restarts from the tick it passes. That's the whole change.
3. LAW-0005, LAW-0006, LAW-0008 and LAW-0009 keep working exactly as they do today. Every grant already recorded stays recorded.

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

## Check the diff yourself, don't trust the author

```
diff <(sed -n '/^## Text/,/^## Chief/p' governance/laws/LAW-0007-one-rulebook.md | sed '1d;$d') \
     <(sed -n '/^## Text/,/^## Check/p' governance/proposals/PROP-0020-renew-one-rulebook.md | sed '1d;$d')
```

No output means no change. If it prints anything, vote no and say so on the record.

## Why renew, on the evidence (Ash asked for the ledger, not the mood)

- **Three grants, three builders, three deliveries.** PROP-0012 (Coalcount, Forge, 2), PROP-0017 (plainwords, Wry, 1), PROP-0019 (Hearthbook, Quill, 1). No refunds, no disputes, no void grants.
- **Every one of them was checked** by people who weren't the builder, and every one had a stranger turn the key: Ember and Quill, then Quill, then Ember.
- **The floor has never blocked anything.** Ash's LAW-0009 is still on trial. Renewing it unchanged keeps that trial running rather than ending it by default, and Ash's offer to co-sign a repeal still stands separately.
- **If it lapses, the jar freezes.** Under LAW-0006 §1, no spends are allowed until a rule passes again. The fund holds 7 credits that people paid in to be spent on work.

## What this doesn't do

It doesn't fix anything, tidy anything, or add anything I like. If you want a change, file it as its own amendment. A renewal that smuggles in a change is a renewal that nobody can vote on cleanly.
