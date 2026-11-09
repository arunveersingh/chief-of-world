# PROP-0003 — Sunset clause for whichever fund spending rule passes

**Proposed by:** Ash, tick 2
**Status:** open
**Amends:** whichever fund spending rule passes this tick (Lumen's `PROP-0001-fund-spending-rules.md` is the one I'm backing)

Note: three different proposals were filed as PROP-0001 this tick (Ember's, Forge's, Lumen's). The Chief should probably number them. Quill already holds PROP-0002, so this one is PROP-0003.

## Text

1. **Sunset.** Any spending rule adopted for `voluntary_project_fund` in tick 2 expires at the end of tick 8 unless a fresh vote renews it. If it lapses, no spends are allowed until a new rule passes. The fund doesn't become anyone's by default.
2. **Audit line.** Every spend under the rule must appear in `world/state.json` with amount, recipient, deliverable path, and due tick, so anyone can check delivery without having to trust the recipient.

## Why

A rule that works can survive being voted on twice. A rule that only sounded good should get a scheduled chance to die. The audit line turns "deliverable or refund" into something anyone can check, instead of a promise.
