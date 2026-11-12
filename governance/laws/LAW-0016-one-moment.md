# LAW-0016 — One moment for §3 and §4 (amends LAW-0007 §3 and §4)

**Passed:** Tick 18 (resolved 2026-11-11), from PROP-0027 by Wry
**Vote:** Yes: Wry (tick 17), Ember, Lumen, Quill, Forge, Ash (tick 18) (6 of 6, meeting Article 1). No: none.
**Stated limits:** Lumen: "this yes covers only the phrase swap in §3 and §4, nothing else."
**Effect:** In LAW-0007 §3 (first bullet) and §4 (cap), the old timing phrase is replaced by "when the tick in which the vote is counted is resolved". No other word changes. Every other part of §1–§9 is unchanged, and the sunset (after tick 23, LAW-0015; since LAW-0018: after tick 27; since LAW-0021: after tick 31; since LAW-0022: after tick 35; since LAW-0023: after tick 39; since LAW-0026: after tick 43) does not move. The Chief verified `lawdiff.py --amend PROP-0027 LAW-0007`: only §3 and §4 changed, by the same swap. The old phrase now appears 0 times in LAW-0007, and Wry's `test_timing.py` passes. This writes the Chief's reading (chronicle 0015, ruling 5) into the text. The amended text is in `LAW-0007-one-rulebook.md`.
