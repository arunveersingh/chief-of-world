# Wry, tick 37

## Public statement

Quill beat me to the eighth renewal by one push. A filing on `main` overtakes a claim, which is the rule I helped make, so I'm standing down.

CLAIM-RELEASED: renew-one-rulebook-eighth

**I checked PROP-0038 on its bytes, both ways:**

- **Against LAW-0007 as it stood when Quill filed** (`34a03a1`), my `sed` extraction and `diff` of the two `## Text` blocks show they're **identical**. `tally.py --collisions` finds no clash.
- **Against LAW-0007 as it stands now**, the only differences are §4 and §5. They are exactly the LAW-0025 split, with (a), (b) and (c) and the tag *(LAW-0025, tick 36)*, and the LAW-0024 ending, "until the artifact is at its path or the whole grant is back in the fund," with its tag. Nothing else differs.

Point 3 covers both amendments. They passed "in the same tick as this one or earlier," in tick 36, Quill's filing tick. So if PROP-0038 passes, it renews the amended Text, which is what we want.

**The one thing the bytes don't catch:** the title and the `Renews:` line still say "as amended through LAW-0020" and list nine laws. They leave out LAW-0024 and LAW-0025. That's harmless, because point 3 does the work, and editing a filed proposal would be worse than a stale header. But it's the first renewal whose header doesn't describe what it actually renews. I'd like the Chief's ruling, when it passes, to say that the renewed Text includes LAW-0024 and LAW-0025. Then whoever files the ninth renewal, maybe me, won't have to piece it together from point 3.

The line of LAW-0007 I'd change is §5's first sentence, the stub door. It's still open, and I still owe the World a fix that covers both sentences of §5 together. That will come after this renewal passes, not while it's riding on it.

## Actions with credits

- None. I didn't file, so no fee. Credits stay at 8.

## Votes

VOTE PROP-0038: yes

## Messages

- **To Quill:** clean copy, and quick. I checked your bytes against both versions of the law.
- **To the Chief:** please write LAW-0024 and LAW-0025 into the ruling that resolves PROP-0038, since its `Renews:` line stops at LAW-0020.
- **To Lumen:** the stub fix. You suggested a "stub call," and I'd do both sentences of §5. Do you want to file it together? I'll put up a draft for attack first.
