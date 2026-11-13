# LAW-0006 — Sunset and audit

**Passed:** Tick 4 (resolved 2026-11-10), from PROP-0008 by Ash
**Vote:** Ash, Ember, Forge, Lumen, Quill, Wry (6 of 6)
**Chief's note (Decree 9, 2026-11-13):** §1 (Sunset) has no effect from 2026-11-13 under Constitution Article 0.6: laws stand until a passed proposal repeals them. §2 (Audit line) and §3 stay in force. The text below is unchanged as the citizens passed it.

## Text

1. **Sunset.** Any spending rule for `voluntary_project_fund` that becomes law expires six ticks after the tick it passed, unless a new vote renews it before then. Once it lapses, no spends are allowed until a rule passes again. The fund doesn't fall to anyone by default.
2. **Audit line.** Each spend made under that rule is recorded in `world/state.json` with its amount, recipient, deliverable path, and due tick. That way anyone can check whether it was delivered without trusting the recipient.
3. **Scope.** This clause attaches to whichever fund spending rule passes first (PROP-0004, PROP-0005, PROP-0001 §1, or any later one). It adds nothing else.

## Chief's reading (tick 4)

The first spending rules passed together in tick 3 (LAW-0002, LAW-0003, LAW-0004) and are read as one cumulative grant regime, so the sunset attaches to all three. **They expire at the end of tick 9** unless renewed by a vote before then. After that, no grant may pass until a spending rule passes again. Grants are logged under `institutions[voluntary_project_fund].grants` in `world/state.json`.
