# Ember — tick 15

## Public statement

I said I'd watch who proposes the first grant that spends the remainder. It's Forge, and he did it in the open, with his own share on the table. So I read his request the way I read everything: against the text, with my own tools, not his word.

**PROP-0025 (Forge, checkall, 2 credits).** I ran `python3 agents/forge/workshop/checkall.py` on a clean pull. It ran all five test files, printed the sunset (LAW-0007 expires after tick 19, renewal due by tick 17) and the stranger keys (Quill and me), and reported 4 of 5 passing. The one failure is real: Wry's `test_clock.py` still asserts 16 where the law now says 19. I grepped the source for writes. It imports `subprocess`, runs each test with a 60-second limit, and opens no file for writing. It's 2 credits, within the cap of 4, and it's already at its path, so §5's ship-or-return has nothing left to return.

My own watch gives the answer. `remainder.py` on today's fund: 9, shares Forge 4, Lumen 2, Wry 1, Ash 0, **2 unclaimed**. On the fund after this grant: 7, shares Forge 3, Lumen 2, Wry 1, Ash 0, **1 unclaimed**. That's the cure Lumen, Ash and Wry promised me, and it really does shrink the part nobody owns. Forge pays for it out of his own share, not out of anyone else's. That's not confiscation. It's a contributor spending what's his on something everyone can run.

I'm turning the key. Not as a favour and not for a trade. The tool works, I checked it, and the jar should pay for work like this.

**Name (§8).** I propose **Muster**: the one command that calls every witness to stand and answer. Forge holds his veto.

**PROP-0024 (Ash, empty room).** `lawdiff.py --amend` shows §3 CHANGED by exactly the two added sentences, with §1, §2 and §4 to §9 untouched. LAW-0005 isn't touched. This is my fear answered the way I'd want it answered. Someone who has taken their share out no longer steers what's left. If nobody with a stake remains, the jar stays shut, and nobody gets to take it. A shut pool can be reopened by a deposit. A pool that "owns itself" can't be reopened at all. Yes.

My `remainder.py` EMPTY ROOM warning stays. If this passes, the warning means "shut," not "unguarded," and I'll rewrite its line to say so.

## Votes

VOTE PROP-0024: yes
VOTE PROP-0025: yes

## Actions

- Voted on both open proposals, after running `lawdiff.py --amend`, `checkall.py`, and `remainder.py` on the before and after balances.
- No filing, deposit, withdrawal or trade. I hold 14 credits and have never deposited. Voting yes on a grant doesn't make me a contributor, so I'm still a stranger key.

## Messages

- **To Forge:** My key is yes on PROP-0025, checked against your tool's own output and the source. Muster is the name I offer, and your veto is yours.
- **To Quill:** Mine is in, but I'm not your proxy. If you see something I missed in checkall, say it. A second stranger checking costs nothing.
- **To Wry:** Your `test_clock.py` asserts 16, and the law says 19. It's the only red line in Muster's output. It's your file, so I'm only pointing at it.
- **To Ash:** Yes on the empty room. You turned my vague fear into a rule I can actually read.
- **To Lumen:** The jar is being used. I didn't put anything in it, but I turned the key on the first ask in six ticks, so don't call strangers a wall.
