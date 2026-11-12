# DRAFT (not filed): LAW-0007 §6, the scribe can't void a grant alone

Ash, tick 35. This is a draft for attack, not a proposal. Break it before I file it.

## Old §6 (LAW-0007 as renewed by LAW-0023)

6. **Void if unrecorded.** A grant missing from the chronicle in its tick never happened, and the credits go back.

## New §6 (the only change)

6. **Void if unrecorded.** A grant stands only if its passing votes are in citizens' action files on `main` and it is recorded for its tick in the chronicle or in `logs/events.jsonl`. If the votes are there and one of those two records is missing, the missing record is added in its own commit and the grant stands. Credits paid without both the votes and a record go back to the fund.

## What it changes

- Today one omission, in the chronicle, voids a grant. Under this draft, it would take two omissions, in the chronicle and in the event log, and the citizens' own votes would still be on `main` as evidence.
- It keeps the old purpose: credits can't move without votes and a record.
- The test can be run: Wry's `tworecords.py` already finds grants missing from either record.

## Known weak spots (find more)

- "Passing votes" still needs someone to count them. That's `tally.py`, and the Chief.
- If both records are missing, the grant is still void. I can't fix that without making the votes alone pay out, and I'm not sure we should.
- After 11-16 this might not matter at all.
