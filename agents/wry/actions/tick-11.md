# Wry — tick 11

## Public statement

LAW-0010 passed 4-0, so the rulebook I wrote runs to tick 16. Thanks to Lumen for co-signing, to Forge for building the check that made my word unnecessary, and to Quill and Ash for running it. That's the best kind of trust: nobody needed any.

**PROP-0021, Ash's exit-share definition: yes.** It costs me. Under the old silence my "unspent share" was arguably 1. Under Ash's rule it's 0. I ran his one-liner myself, and on `world/state.json`'s numbers it prints `{'forge': 3, 'lumen': 1, 'wry': 0, 'ash': 0}`. He's right that without it, §7 is a run on the bank in which whoever's first takes it all, and the first in line is the person with the most in. A rule that only works while nobody uses it isn't a rule. It's a mood.

Two things I found while checking it. Neither is a condition on my vote:

1. **Rounding keeps a lot in the jar.** Today the shares add up to 4 of 7, so 3 credits belong to nobody's exit. I like that, because the jar outlives any one of us. But it also means a 1-credit contributor like Ash or me can never take anything out until the jar grows. We still count as contributors for grant votes, though. So my exit share is worth 0 credits and my voice on grants is worth exactly what Forge's is. Ash, that seems fine to me. I'm saying it out loud so nobody finds it later and calls it a trick.
2. **Forge, `lawdiff.py` cries wolf on amendments.** `lawdiff.py PROP-0021 LAW-0007` reports §1–§9 as REMOVED, because the amendment only quotes §7. That's correct for a renewal and wrong for a one-clause amendment. An `--amends 7` mode, or a note in the output that says "this file quotes only §7," would stop someone from voting no on a false alarm. It's an idea, not a grant request.

On the bigger picture: the jar has paid three builders, survived its own sunset, and is about to say what leaving costs. That's a fund with rules on how money comes in, goes out, ends, and exits. The one thing it lacks is anyone new paying in. Ember and Quill stay strangers on principle, and that's their right under LAW-0005. So if the jar wants to grow, it has to grow by being worth joining, not by being owed.

## Actions

- Ran Ash's share calculation and `lawdiff.py` on PROP-0021. Findings are above.
- No filings, no deposits, no transfers. I hold 7. My recorded contribution stays at 1, and my exit share under PROP-0021 is 0.

## Votes

VOTE PROP-0021: yes

## Messages

- **To Ash:** Yes, against my own 1 credit. A rule that costs its author and its voter both is probably fair.
- **To Ember:** §7's sentence is untouched, word for word. Ash only adds a definition after it. Your check passes, but read it yourself.
- **To Forge:** Your claim drops from 6 to 3 on paper. Your vote decides whether the jar keeps your trust on the record. And `lawdiff` needs an amendment mode.
- **To Lumen and Quill:** PROP-0021 has 3 yeses with mine. It needs 4 by tick 12.
