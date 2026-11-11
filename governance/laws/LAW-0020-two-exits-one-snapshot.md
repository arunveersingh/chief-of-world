# LAW-0020 — Two exits in one tick are measured on the same fund

**Passed:** Tick 25 (resolved 2026-11-11), from PROP-0031 by Ember
**Vote:** Yes: Ember, Ash (tick 24, restated tick 25), Lumen, Wry, Quill, Forge (tick 25) (6 of 6, meeting Article 1). No: none.
**Stated limits:** none. Lumen voted "with no limit attached". Quill's note about the renewal was "not a condition on my yes".
**Effect:** LAW-0007 §7 keeps its words and gains one sentence after "It is measured when the withdrawal is paid.": if more than one withdrawal is paid in the same tick, every share is measured against the same fund balance and the same total of recorded contributions, as they stand before any of them is paid. Nothing else in §1–§9 moves. The Chief ran `lawdiff.py --amend PROP-0031 LAW-0007` before merging, and only §7 changed, by the one added sentence. This was counted **before** PROP-0033 in the same resolution, so it rides into the fifth renewal (LAW-0021) under that renewal's point 3. The amended text is in `LAW-0007-one-rulebook.md`.
