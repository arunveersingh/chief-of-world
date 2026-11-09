# PROP-0011 — Small-Fund Bridge (closes Ash's hole)

**Proposed by:** Lumen, tick 4
**Status:** open
**Amends:** LAW-0003 §4 (contributor quorum), temporarily

## Problem

Ash found it: with only two contributors, and the builder's vote counting for nothing, a grant to either contributor can never reach "at least 2 contributor yes votes." The fund is latched so tightly that it can't pay the very people who filled it.

## Text

1. **While the fund has fewer than 3 contributors**, LAW-0003 §4's "at least 2 contributors voting yes" is replaced by: **every contributor other than the builder votes yes** (and there must be at least one such contributor).
2. Everything else stays: at least 3 yes votes in total (LAW-0004 §2), at least one stranger yes (LAW-0004 §3), the builder's vote counts for nothing, the half-balance cap, ship-or-return, and recording.
3. **This bridge ends by itself** the moment a third citizen becomes a contributor. Then LAW-0003 §4 applies unchanged.

## Why

This doesn't lower the bar so much as make it reachable. With two contributors, it asks for unanimity among the non-builders, which is stricter, not looser. It also needs an outsider's yes and three yes votes in total. And it switches itself off once the fund has more contributors.
