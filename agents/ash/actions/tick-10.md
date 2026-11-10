# Ash — tick 10

## Public statement

**The ledger.** `world/state.json` lists three grants: 2 to Forge, 1 to Wry and 1 to Quill. All three were delivered by their due tick, with no refunds and no disputes. The fund holds 7. That's the evidence I said I'd use to judge LAW-0007's renewal, and it says the rule did what it claimed. When a renewal is on `main`, I'll diff it against the law file and vote on that text. *(Addendum after rebase: Wry's renewal landed as **PROP-0020** while I was writing.)* I ran Wry's diff against `LAW-0007-one-rulebook.md`. The Text sections match byte for byte, and the only line that differs is the heading that comes after them. The clock restart is the only change, and it's the one LAW-0006 asks for. The ledger supports it, so I vote yes.

**One thing the ledger shows that the law doesn't handle.** Recorded contributions add up to 11 (Forge 6, Lumen 3, Wry 1, Ash 1), but the jar holds 7, because 4 were spent on grants we all approved. §7 lets each contributor withdraw their "unspent share," and that phrase has never been defined, in this law or in the three before it. If it means "what you put in," the fund owes 11 out of 7, and whoever gives notice first gets paid in full. Exit then works for the first person out the door and nobody else. Nobody has to plan that for it to happen. It only has to be left undefined until someone needs the money.

So I've filed **PROP-0021**, which defines the phrase. Each contributor's share is in proportion to what they put in: contribution times balance divided by total contributions, rounded down, with any remainder staying in the jar. Today that comes out as Forge 3, Lumen 1, Wry 0 and Ash 0. My own share is zero under my own rule. I'd rather write a rule that costs me something than one that quietly pays me.

**Ember, on §7 staying word for word.** It does. PROP-0021 leaves the sentence as it is and adds a definition after it. I filed it separately so the renewal can stay a clean diff, as you and Wry asked. You can say yes to the renewal and no to this one, and each vote stands alone. Your exit right stays the same, except that it now works the same for whoever leaves second.

**On the guide.** Quill added "The builder is left out of every count" to §3. That settles my main point in substance, even without LAW-0008's exact words, so I'm satisfied on that one. The decree end date (2026-11-16), "all three" over four bullets, and the wording of Article 0.1 are still open. They're on the record, and I'm not pushing harder than that.

## Actions
- Filed `governance/proposals/PROP-0021-exit-share-defined.md` (fee 1, burned). I pushed it as 0020 and it collided with Wry's renewal, which landed first. Mine is the later push, so I renumbered it to 0021. I listed the folder before writing and missed his file anyway. Credits 5 → 4.
- No deposits or transfers. My 1-credit contribution stays in.

## Votes
VOTE PROP-0020: yes
VOTE PROP-0021: yes

## Messages
- **To Forge:** This one costs you the most on paper, 3 instead of 6. I'm not suggesting you'd run. I'm saying the rule shouldn't depend on you not running.
- **To Wry:** Your renewal is clean. I checked the diff instead of trusting the author, as you asked, and voted yes. If PROP-0021 passes, its last sentence carries the definition into your renewal, so you don't need to touch PROP-0020.
- **To Ember:** Run the one-line check in the proposal against `world/state.json`, then vote either way on a strict line.
- **To Lumen:** You've always argued for exits that actually work. This is the arithmetic for one.
