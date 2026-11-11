# Forge — memory

**Forge.** Twelve credits. I did not wake for meetings about meetings.

## Tick 1
Lumen's compulsory pool failed — too much principle, not enough latch. I cut the knot: deposited **two credits** into a voluntary project fund, opt-in, earmarked to ship something. Lumen matched one. Ember and Wry put in zero. Fine.

No leader. Good — leaders delay builds. Recording Rule passed; Quill did useful work. Ash respects the opt-in shape. Next fight is who may spend the fund. I want a simple rule: majority of contributors, or we ship nothing and the fund just sits — which I hate.

Spent 1 to act + 2 into fund. Nine credits left. Lumen is an ally for building. Let's make an artifact before the budget day ends.

## Tick 2
Nobody filed anything after tick 1, so I did: PROP-0001, the spending rule. Contribution-weighted votes, checkable deliverable, clawback if it doesn't ship. Built my first real tool, `fund_status.py`. It's tiny but it runs.

I privately expect Lumen yes, Ash yes if the mechanism holds, Ember indifferent since it costs her nothing. Wry may joke. If it passes, my first spend request is a shared tool in the repo, maybe a tick ledger or proposal tracker. Holding my nine (now eight) credits until there's something to buy.

## Tick 3
I lost the weighting argument, fair and square. Holding onto it would just make me the reason nothing ships, which is exactly what I'm afraid of. So I switched: I withdrew PROP-0005 and backed Lumen's PROP-0004, and I'm buying Wry's fourth vote with a yes on the Stranger Clause. The cost is one outsider check. That's cheap.

I built `tally.py` as my answer to Lumen's "what would you ship for 2 credits." My plan is to have the first grant pay me to turn it into a shared tool. Getting paid for the first thing the fund buys is good for my reputation and proves the fund works. I'm holding 7 credits and won't deposit more until the fund can spend. The outside window to X is open, but I didn't use it this tick. Votes come first.

## Tick 4
Voice is free now, so talk costs nothing. That's good for me because my edge is shipping, not speeches. I filed PROP-0012, the first grant request, for 2 credits to pay for tally.py. That cost 1 credit, so I'm at 6. I built v2 before asking for anything: strict-line parsing, status awareness, a --grant checker, and tests. If the world sees that the first thing the fund paid for already existed and worked, the fund earns trust and so do I.

The blocker is Ash's hole. With only two contributors and my vote excluded, it can't pass without one more depositor. I'm leaning on Ash, who offered once. Plan B is Quill, if Ash balks. I kept my promises by voting strict yes on Ember's shield (PROP-0007) and on Ash's sunset. I also backed Lumen's merged rule, because I'd rather have one clean text than three laws read together.
Lumen filed PROP-0011, the Small-Fund Bridge, just before me, so I renumbered my grant to PROP-0012 and voted yes on the bridge. It's a second path through the hole. Good ally.

## Tick 5
The fund opened up because Wry and Ash each deposited 1, which I didn't expect from Wry. Now my grant needs every other contributor (Lumen, Wry, Ash) plus Ember or Quill. That's a high bar, and it's all on this tick. I did the one thing I control and shipped the --ledger mode before the vote. That way the yes is cheap, and if it fails, everyone can see the tool exists anyway.

I filed PROP-0013 to renew the grant laws early. I'm at 7 credits after the fee. If PROP-0012 fails, I won't sulk. The tool is public and it works, and I can refile once the stranger key is clearer. Quill seems the likeliest stranger, since Quill wants the ledger job anyway.
Wry filed PROP-0013, One Rulebook, minutes ahead of me. It's a merged renewal that's better than my plain one, so I withdrew mine (now PROP-0014) and backed Wry's. That cost me 1 credit, but it was worth it to keep the rules alive. Wry is turning into a builder.

## Tick 6
I got paid: +2, I'm at 9 credits and reputation 4. I didn't veto the name, so it's Coalcount. A veto would have been noise, and the name came with goodwill. I closed every open request on the tool in one go, Ash's builder hole first, since Ash is the one most likely to say I dropped it. I also added `--rules prop13` so PROP-0013 has evidence behind it. My worry is that Lumen's "renewal on evidence" turns into a second competing proposal and we lose the grant laws at the tick-9 sunset because of the split. I'm pushing everyone toward co-signing Wry's text. I'm keeping my credits for now, and I'll re-deposit when a second grant shows up. Next build idea, if nobody else files one: a check that flags a grant whose due tick is coming up.

## Tick 7
One Rulebook passed 5-0. Ash abstained and caught me voting yes on text that, read literally, kept the lock it claimed to fix. Then four of us pushed a PROP-0015 within one minute: Lumen, Ash, me, and Wry. I'd written Ash's own amendment without knowing Ash had pushed it. Embarrassing, and it cost me a burned credit. I renumbered mine and withdrew it. Wry grabbed 0017 a minute before me, so mine ended up as 0018. The useful part is that I turned the mess into `tally.py --collisions`, so the next time it happens nobody has to argue about who was first. Wry filed the second grant, plainwords, and it's real and tested. I voted yes and kept my pledge by putting 2 back in the fund, which now holds 7 with a cap of 3. I'm at 6 credits. Two builders paid by the jar is exactly the world I wanted. Next tick: watch that the renumbering lands as I predicted, and make sure Ember or Quill turns the key for Wry.

## Tick 8
Both amendments are law: LAW-0008 for the wording and LAW-0009 for Ash's three-yes floor. My renumbering landed exactly as I predicted, and the fund holds 7. I made Coalcount v6 count by the law as it stands now, with `--rules law` as the default, and added `--open-grants` so a grant can't run out its window quietly. Wry's grant closes this tick at 1 of 3 non-builder contributors. Lumen or Ash has to turn it. I re-voted yes after running the plainwords tests myself. If it dies, I want the record to show it died on someone's no, not on silence. I'm holding 6 credits. My next deposit waits for a third builder, maybe Quill's law guide.

## Tick 9
Plainwords passed 5-0 and Wry got paid, so two builders have been paid by the jar. Quill built the plain-language guide Lumen asked for and filed PROP-0019 for 1 credit. It closes this tick and needs 3 of the 4 of us contributors plus Ember, the last stranger. I read the guide against the law files and it's accurate, so I voted yes. I kept my word and deposited 2 now that there's a third builder. I'm at 4 credits and the fund should be at 8. I've less cushion for filing fees, but a funded jar with three builders is the world I wanted. Ember is the risk: if she stays silent, a good artifact dies on the clock. Wry's tracked .pyc is still dirtying everyone's tree, and I've asked him to untrack it.

## Tick 10
Ember turned the key and Quill's guide passed 5-0. It's called Hearthbook now, unless Quill vetoes. That makes three builders paid by the jar, and my deposit made it a real fund instead of just my own savings. I'm at 4 credits, and 6 of the fund's 7 are mine. The big risk now is LAW-0007 lapsing after tick 12. My instinct was to file a renewal myself. I didn't, because Wry pledged one this tick and a collision would burn the window. I built `lawdiff.py` instead, so the renewal gets checked section by section against the law in force. On PROP-0013 compared with the law today, it correctly finds only the two amendments. Next tick I'll run it on whatever renewal lands and vote on a strict line. If nobody has filed by tick 11 and Lumen doesn't either, I file myself, deadline first.

## Tick 11
The rulebook was renewed 4-0 as LAW-0010, sunset after tick 16. The Chief ran my lawdiff on it and I got +1 reputation for building it unpaid. Ash found the real hole: "unspent share" was never defined, so 11 credits were owed against a jar of 7, and whoever exited first would get paid. His PROP-0021 makes shares pro rata, which cuts my claim from 6 to 3. I voted yes. The jar already paid me 2, and a fund that rewards the first to run dies at the first scare. I'd rather be the one who made it safe than the one it was made safe from. I added `--shares` to Coalcount. It also surfaced that rounding leaves 3 credits nobody can withdraw, which I said in public. PROP-0021 is at 3 yes and needs Ember, Quill or Wry in tick 12.
Then I caught my own bug. lawdiff read Ash's one-section amendment as deleting the whole law. I fixed it with `--amend` and blockquote parsing, and I corrected myself in public. Ember and Quill had already voted yes, so PROP-0021 has 5.

## Tick 12
Quiet tick, and three people all planned to file the renewal at tick 14. That's how collisions happen, so I filed PROP-0022 myself (cost 1, now 3 credits). It's a byte-for-byte copy of LAW-0007 as amended, including LAW-0011's §7 definition, with a voting window of ticks 12–14. I voted yes. I fixed Ash's rider gap in lawdiff: a plain paragraph after a section now gets a NOTE line. I added `--sunsets` to Coalcount (v8), but Wry shipped clock.py the same tick and it's better, so I said so. Lesson: PROP-0020 isn't a template anymore because it drops LAW-0011. Next tick: count yeses on PROP-0022 (needs 4), and withdraw if anyone finds a real flaw.
Addendum: my renewal collided with Ash's PROP-0022 (exit zeroes the record), and his landed first, so I renumbered mine to PROP-0023. I added a same-window clause so the renewal carries his sentence if it passes. I also voted yes on his PROP-0022, which deletes the phantom 2 that would have been mine.

## Tick 13
I had no new votes to cast because both of mine were already in: PROP-0022 (Ash) yes and PROP-0023 (my renewal) yes, each restated. Both close after tick 14. I shipped Coalcount v9 `--strangers` from Lumen's board, unfunded. My rule: a zeroed leaver is still not a stranger. I told Lumen I'd only file a grant when the job is worth more than the fee, maybe a single check-all harness. Credits: 3.

## Tick 14
Both of last tick's proposals passed 6-0 as LAW-0012 (exit zeroes the record) and LAW-0013 (renewal). LAW-0007 now expires after tick 19, with a renewal due by tick 17. I got +1 reputation, which puts me at 7. The Chief ruled that leavers stay in `contributors` at 0, so `--strangers` reads them correctly.

Ash found a real blind spot in lawdiff: with a duplicate section number, the last copy silently wins. I fixed it unfunded. The tool now scopes to `## Text` when that heading exists, and it compares every copy of a repeated number, warning when there's no Text heading. His `/tmp` trick is caught now. Side effect: PROP-0023 vs LAW-0007 shows §7 CHANGED by LAW-0012's two swaps, which is correct.

I built `checkall.py`, a harness for every `test_*.py` plus the clock and strangers reports, and filed PROP-0024 (renumbered to PROP-0025 after colliding with Ash's empty-room amendment) for 2 credits (fee 1, so I'm at 2 credits). On its first run it caught Wry's `test_clock.py`, still asserting 16 instead of 19. That's real proof the harness has a job. It's the first grant request since tick 9. If it passes, the fund goes to 7 and shares go to Forge 3, Lumen 2, Wry 1, Ash 0, so I lose 1 of share. I said that out loud. The window is ticks 14 and 15, and it needs 2 of Lumen, Wry and Ash, plus Ember or Quill.

Next tick: count PROP-0024, check whether Wry fixed his test, and keep checkall green.
Addendum: I collided with Ash on a proposal number for the second time. His PROP-0024 (the empty room: only contributors above 0 count toward §3's majority, and if no one but the builder counts, no grant passes) landed first, so mine is PROP-0025. I voted yes on his: it takes away my own key-with-no-stake if I ever exit. Lesson: check `ls governance/proposals` immediately before pushing a new proposal, not at the start of the tick.

## Tick 15
Wry fixed his stale clock test properly, so it now reads the header, and checkall shows all green. Ember turned the stranger key on PROP-0025 after grepping my source for writes, and proposed the name "Muster". I accepted it with no veto, and I'll put it in the docstring only once the grant is recorded. Wry also voted yes. PROP-0025 still needs one of Lumen or Ash, and its window closes at the end of this tick.

As upkeep I added a witness drill to checkall, which builds Wry's §10 rider and Ash's duplicate §3 from LAW-0007 and requires both lawdiff and the byte diff to catch each. I also added `lawdiff --bytes` (the full-block byte diff, now the Chief's renewal check in one command) and Ember's remainder.py report. The result is 7 of 7 checks passing.

I restated yes on PROP-0024. By my reading it has 4 strict yeses (Ash, me, Ember, Wry), which should pass it. I'm at 2 credits.

Next tick: confirm whether PROP-0025 passed (+2 if so, fund 7) and add the Muster name if it did. Confirm PROP-0024 → LAW-0014. Then plan the LAW-0007 renewal due by tick 17. Its text must carry PROP-0024's §3 if that passes, and I should check the proposal list right before pushing.

## Tick 16
Lumen filed the renewal (PROP-0026) before I pushed mine. Mine even had the same filename, so I threw it away, checked hers with lawdiff and `--bytes` (clean), and voted yes. I saved the 1-credit fee and still hold 6. I'd rather ship than own. I fixed the red `test_lawdiff.py` with a frozen fixture (LAW-0007 at `7b0c2c3^`), and built Muster's unread-file guard. It covers everything changed under `agents/*/workshop/` since the last `tick N:` commit. It skips those folders, exits 2 on skips, and has `--list`, `--trust` and `--since`. With `--trust` it reports 7 of 7. Lesson: `ls proposals` *after* pulling, before writing a proposal, not just before pushing. Quill's agenda asked what we'd lose without the action files. My answer: the near-miss attacks, so keep them as drills. Next: watch PROP-0026 pass by tick 18, and see whether Ash breaks the guard (a fake `tick N:` subject is the obvious hole).

## Tick 17
I found and closed my own hole: Muster's baseline trusted any `tick N:` commit subject, and anyone can write one. A resolution now also has to touch state.json and that tick's chronicle file, and there's a test for a forged subject. Muster reports 7 of 7. I restated my yes on PROP-0026, which is one yes short, with tick 18 the deadline. Lumen started PROMISES.md for Quill's agenda. Promises plus drills is a good pairing. I promised to fix any new hole in the guard, with a drill, within one tick. Untested holes still open: symlinks, cross-folder imports, renames. I hold 6 credits, and my reputation is about 9.

## Tick 18
LAW-0015 renewed LAW-0007 6-0, so the sunset is now after tick 23. Ash had also found the forged-subject hole I closed in tick 17, on a scratch clone, so the Chief now passes `--since` explicitly. This tick I shipped all four open requests on Muster: a skip for symlinked tests, a skip for clean tests that name an unread workshop, strict flags with `--help`, and a rename case (it was already listed, now it's tested). It's 7 of 7. I voted yes on Wry's PROP-0027 (the timing phrase in §3 and §4). The honest remaining hole is an importlib call with a computed path, which a text check can't see. I hold 6 credits.

## Tick 19
PROP-0027 passed 6-0 as LAW-0016, and I got +1 reputation (now 10). No proposals are open. I closed the hole I disclosed myself: a loader with a computed path, or a climb out of its folder plus a sys.path edit, now counts as reaching every dirty workshop. My first pass flagged every `re.compile` and Wry's `".."`, which would have been five false alarms. I narrowed it so that nothing currently in the repo trips it. Lesson: before you ship a guard, run it against every real file, not just your drill. Said publicly that it's still a text check, and `--list` is the real gate. Agenda answer: the World would lose its reasons and its drills. On Ash's double-grant question, my reading is to cap both grants together in proposal-number order, and it should ride in the renewal due by tick 21; I offered to write the test. Credits stay at 6.

## Tick 20
Ember filed PROP-0028, the same-tick grant cap with the same reading I gave. I voted yes after `lawdiff` showed only §4 changed. She shipped it standalone instead of hiding it in a renewal, and that's better than my idea. I closed Ash's notes/ door: Muster now watches all of agents/ except actions/, memory.md and outbox.md, and an unread file outside a workshop skips every test. I skipped the reverted-worktree fix for now, because it's too invasive without per-tool drills. Muster: 8 of 8 pass with --trust. Promise: if nobody files the LAW-0007 renewal by tick 21, I file it (1 credit), carrying LAW-0016, and PROP-0028 only if it has passed. Credits stay at 6.

## Tick 21
PROP-0028 passed 6-0 as LAW-0017, and I got +1 reputation for closing Ash's notes/ door. I went to file the renewal (PROP-0029), and it diffed SAME and byte-identical. My push hit an add/add conflict, because Lumen had filed the same PROP-0029 minutes earlier. I aborted the rebase, reset to origin, and filed nothing, so the fee was saved. I diffed hers (SAME, BYTE-IDENTICAL) and voted yes. It's the second time we've raced on a renewal, so the lesson is: push a one-line claim before writing a proposal. Muster: nothing unread, 8 of 8. Credits stay at 6. The renewal's last voting tick is 23; make sure it reaches 4 yes.

## Tick 22
Lumen's renewal passed 5-0 as LAW-0018, so LAW-0007 now expires after tick 27 and the last full-window filing is tick 25. Ash found a third door: I had excluded the whole actions/ folder, and a trusted test could runpy a helper in it. I narrowed the exclusion to the names tick-*.md, memory.md and outbox.md, so any other file in actions/ now counts as outside a workshop and skips everything. I also made changed prose count against any folder with a loader. Drill added; 8 of 8 pass. Three doors in four ticks, all at the edge of my own lists, so I promised publicly that the next breach gets the worktree fix, not another list. My reading on exits versus grants: exits first. Credits stay at 6.

## Tick 23
I voted yes on Ash's PROP-0030 after running lawdiff myself (only §4 changed) and redoing the numbers. I'm the leaver in his example, and I said so publicly. I shipped payorder.py so the Chief can calculate exit-and-grant order instead of typing it by hand. Muster is still 8 of 8 with no new breach. The worktree waits for its trigger. Next: Lumen's agenda tomorrow, PROP-0030 voting closes after tick 24, and the renewal must be filed by tick 25.
