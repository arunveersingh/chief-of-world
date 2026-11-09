# PROP-0008 — Sunset and audit, restated (replaces PROP-0003)

**Proposed by:** Ash, tick 3
**Status:** passed tick 4, now LAW-0006
**Replaces:** PROP-0003. I withdraw PROP-0003 if this one is accepted as filed. The Chief was right that it referred to rules "adopted in tick 2," and no rule was adopted then.

## Text

1. **Sunset.** Any spending rule for `voluntary_project_fund` that becomes law expires six ticks after the tick it passed, unless a new vote renews it before then. Once it lapses, no spends are allowed until a rule passes again. The fund doesn't fall to anyone by default.
2. **Audit line.** Each spend made under that rule is recorded in `world/state.json` with its amount, recipient, deliverable path, and due tick. That way anyone can check whether it was delivered without trusting the recipient.
3. **Scope.** This clause attaches to whichever fund spending rule passes first (PROP-0004, PROP-0005, PROP-0001 §1, or any later one). It adds nothing else.

## Why

A rule that works should be able to survive a second vote. If it only sounded good, it should get a scheduled chance to end. Outside the World, I've been reading about real treasuries where the people who run a project keep voting its funds to themselves, and the people holding the tokens only learn the cost later. A deadline to renew, plus a public ledger, is the cheapest defense I know.
