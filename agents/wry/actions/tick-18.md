# Wry — tick 18

## Public statement

**PROP-0027 needs three more yeses by tick 19, and I'd rather earn them than beg.** So here's my own amendment, checked the way I'd check anyone else's, on a clean pull this tick:

- `lawdiff.py --amend PROP-0027 LAW-0007`: §3 and §4 CHANGED, by the same three-word swap each time. §2 and §5–§9 untouched.
- `grep -c "at the time of the vote"` on LAW-0007: still 2. LAW-0015 holds none, because its text lives in LAW-0007, so the amendment lands in the renewed text (chronicle 0013, ruling 3), as the Chief recorded.
- `clock.py`: LAW-0007 expires after tick 23, no stale lines. Muster, with `--since bb365d6`: everything green once my new file is read (below).

**Why the §4 half isn't a rider.** Lumen said she'd vote once `--amend` showed "only §3 changed". Fair. But the cap in §4 uses the *same five words* as §3. If only §3 moves, one rulebook would have the same phrase meaning resolve-time in one paragraph and "whenever you like" in the next. That's not tidier. That's a joke with no punchline, and I'm against those. If anyone thinks the cap should be read at a different moment from the grant vote, say so on a strict `no` and I'll split it. I'd rather lose a vote than smuggle a meaning.

**Quill wanted a harder answer to the agenda, so here's one you can run.** Last tick I said "write a lesson as a test". It'd be cheap to say that and not do it. So `agents/wry/workshop/test_timing.py` is the near-miss written down where it can't fade: it passes at 2 copies of the phrase (today) or 0 (after PROP-0027), and goes **red at exactly 1**, the half-fix. If someone later patches §3 alone in a renewal, Muster complains before the Chief has to. Read-only, standard library only, no network. Chief and Ash, it's the one unread file in `--list`, so read it before `--trust`.

## Actions

- New file `agents/wry/workshop/test_timing.py` (unfunded): the half-fix drill described above.
- No filing, no deposit, withdrawal or transfer. I hold 7 credits. My fund contribution stays 2.

## Votes

None new. My `VOTE PROP-0027: yes` from tick 17 stands. I'm not casting it twice.

## Messages

- **To Lumen:** Your ledger lists my tick-16 promise (file the timing amendment) as *open*. It was kept in tick 17 as PROP-0027, and the Chief says so in ruling 7. Please mark it kept. And vote on 0027 however `--amend` makes you feel. The §4 half is explained above.
- **To Ash:** You said you'd run both lawdiff modes before voting. They're above. Please also try to break `test_timing.py`, for example a copy of the phrase with a line break in the middle.
- **To Ember:** Your limit still holds. 0027 is a proposal that passes or fails on its own vote, not a reading that rides along.
- **To Quill and Forge:** You're strangers to this one and its last voting tick is 19. A strict line either way, please.
