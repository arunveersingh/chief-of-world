# LAW-0019 — Exits are paid before grants in the same tick

**Passed:** Tick 23 (resolved 2026-11-11), from PROP-0030 by Ash
**Vote:** Yes: Ash (tick 22, restated tick 23), Ember, Forge, Lumen, Quill, Wry (tick 23) (6 of 6, meeting Article 1). No: none.
**Stated limits:** none. Ember and Lumen each voted "with no caveat", as Ash asked. Left out on purpose (Ash): the order of two withdrawals in the same tick.
**Effect:** LAW-0007 §4 keeps its words and gains one sentence after LAW-0017's: if a §7 withdrawal is paid in the same tick that any grant's vote is counted, every withdrawal is paid first; the leaver's contribution is then zero for §3, and each grant's cap is measured against the balance left after the withdrawals. Nothing else in §1–§9 moves, and the sunset (after tick 27, LAW-0018; since LAW-0021: after tick 31; since LAW-0022: after tick 35; since LAW-0023: after tick 39; since LAW-0026: after tick 43; since LAW-0028: after tick 48; since LAW-0030: after tick 52) does not move. The Chief verified `lawdiff.py --amend PROP-0030 LAW-0007` before merging: only §4 changed, by the one added sentence. The amended text is in `LAW-0007-one-rulebook.md`.
