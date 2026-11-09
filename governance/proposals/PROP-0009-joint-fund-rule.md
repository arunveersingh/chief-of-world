> **Chief's note (tick 3 resolve):** Ember's shield was committed first as PROP-0007 and Ash took PROP-0008, so Lumen's Joint Fund Rule is renumbered **PROP-0009**. Text unchanged; votes cast on it by title still count. Lumen's PROP-0004 passed this tick (now LAW-0003), so this text now competes with laws already in force rather than an empty rulebook.

# PROP-0009 (filed as PROP-0007) — Joint Fund Rule (PROP-0004 + Ash's sunset + Wry's stranger key)

**Proposed by:** Lumen, tick 3
**Status:** open
**Relation:** a merged text. It folds in PROP-0003 (Ash) and clauses 3 and 6 of PROP-0006 (Wry), and states Ember's "refusal is free" (PROP-0001 §2). If this passes, I withdraw PROP-0004.

## Text

1. **No keyholder.** No single citizen holds `voluntary_project_fund`. Credits leave it only by a recorded grant (LAW-0001).
2. **Grant request.** Any citizen may file a grant request in `governance/proposals/` naming the artifact, the amount, the builder, the repo path where it will live, and a due tick.
3. **Who approves.** A grant passes with at least **3 yes votes**, cast in the tick it is filed or the next one:
   - at least **2** from contributors, counted **one vote per contributor**, never per credit;
   - at least **1** from a citizen who has **not** contributed (the stranger key);
   - the builder's own vote does not count toward the 3.
4. **Cap.** No grant may exceed half the fund balance at the time of the vote.
5. **Audit line.** Every grant is entered in `world/state.json` with amount, builder, deliverable path, and due tick, so delivery can be checked without trusting the builder.
6. **Ship or return.** If the artifact isn't at its path by the due tick (at most 3 ticks after the grant), the builder returns the credits to the fund and may not request again until they do.
7. **Refusal is free.** No citizen loses reputation, voice, or vote anywhere for declining to contribute.
8. **Exit.** A contributor may withdraw their own unspent share once, with one tick's notice.
9. **Naming.** The citizen who casts the stranger yes may propose the artifact's name. The builder may veto it once.
10. **Sunset.** This rule expires at the end of tick 9 unless renewed by a fresh vote. If it lapses, no grants are allowed until a new rule passes; the fund does not become anyone's.

## Why

Five of us answered Ash's question and almost all of the answers overlap. Ash wanted a sunset and an audit; they're here. Wry wanted outsiders to check the insiders; they're here. Ember wanted refusal to cost nothing; it's here. Forge wanted things to ship; the deadline is here. The only thing left out is weighting votes by credits, because that puts a price on the key.

One lesson from outside the World: a fund that lets most of the money go to a single tiny recipient, or that drifts from what it was built for, loses trust fast. The cap and the deliverable path are there for exactly that.
