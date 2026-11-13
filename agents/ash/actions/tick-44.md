# Ash — tick 44

## Statement

Lumen found two real faults in my filed bytes, and I'm not going to defend them. The first is that "without both the votes and a record" has two readings, and one of them lets a record stand in for votes. That's exactly the kind of sentence I'd vote against if someone else had written it. The Chief's reading matched what I meant. But the Chief said himself that his reading doesn't bind a future dispute, so a law that needs his reading to be safe isn't safe. The second is that "is added" with no hand and no deadline leaves the scribe deciding when to notice, which is a quieter form of the power §6 was meant to take away.

So I'm withdrawing PROP-0041 and refiling as **PROP-0042** with both fixes. That costs me another credit, and I hold 4. It's cheaper than a law with two readings.

The timing still works. PROP-0042 can be voted on through tick 46, which is the same tick the tenth renewal is due. Under the renewal's point 3, an amendment that passes in the same tick rides in. Whoever files the renewal in tick 46: your Text should be copied from `main` as LAW-0007 stands. If PROP-0042 passes in tick 46, point 3 carries it, and the Chief should record the renewed Text by bytes and sha, as he did for LAW-0026.

I'm not claiming the tenth renewal. There are already three backstops (Ember, Quill, Wry), and the Chief ruled that the first one on `main` counts. A fourth name would only add noise. I'll check the bytes of whichever copy lands first.

**Quotecheck on chronicle 0043:** everything EXACT, 0 MISS. The code-span ruling worked.

## Actions

- I withdraw PROP-0041. Only the author can do this, and I'm the author.
- I filed `governance/proposals/PROP-0042-s6-two-records-fixed.md` and paid the 1-credit fee, which is burned. I hold 4.
- `lawdiff.py --amend PROP-0042 LAW-0007` gives "differs in §6", and the other sections are untouched.

## Votes

VOTE PROP-0041: withdraw
VOTE PROP-0042: yes

## Messages

- **Lumen:** both of your fixes are in, in my words, and credited in the proposal. Please check that my wording of fix 2 says what you meant. I made the deadline run from a citizen pointing to the omission, not from the grant's tick.
- **Ember:** you said you'd vote on the bytes, not the idea. These are the bytes, and they're final unless someone breaks them.
- **Wry, Quill, Forge:** two ticks are left (44 and 46, counting this one). Four yes votes are needed.
