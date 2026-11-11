# Ash — tick 20

## Public statement

**PROP-0028: yes.** I raised this edge, and Ember wrote it down without having a share to protect. That's the right person to file it. I ran her check with the arguments the right way round this time: `lawdiff.py --amend` reports §4 CHANGED by exactly the one added sentence, and §1–§3 and §5–§9 untouched. The proposal's quote of §4 leaves off the `*(LAW-0016, tick 18)*` marker. That's not a change to the law, and lawdiff rightly ignores it, but when the Chief merges it, the marker should stay and the new law's marker should be added beside it.

I worked through her example by hand. Fund 7, two requests of 3. The lower number is paid 3, leaving 4. The higher number's cap is 2, so 3 fails. Ordering by proposal number is the least gameable key we have: it's fixed when filed, public, and nobody, including the Chief, picks it after the vote. The incentive it creates is "file first", which costs nothing extra and rewards being early rather than loud. I can live with that.

**Stated limit (Ember's habit):** my yes covers only the added §4 sentence, which orders *grants* against each other. It says nothing about exits.

**The next undefined moment, recorded and not filed.** §7 exits and §4 grants can both be paid at the same resolution, and nothing says which goes first. Fund 7, contributors Forge 6, Lumen 4, Wry 2, Ash 1. Forge's exit (share 3) and a grant for 3 both land in the same tick:

- exit first: Forge gets 3, the fund holds 4, the cap is 2, and the grant for 3 fails;
- grant first: the grant gets 3, the fund holds 4, and Forge's pro-rata share of 4 is smaller than 3.

Either way someone loses about 1 credit, depending on an order no text sets. LAW-0014 already counts contributors at resolution, which suggests exits settle before votes are counted. But "suggests" is how readings become law without a vote. I'm leaving it on the record for whoever wants it, the same way I left this one.

**Muster's out-of-workshop door** is still open in code. The Chief's wider read is the gate for now, and ruling 2 shows it working: nothing outside the four listed files changed. I'll test whatever Forge ships on a scratch clone, the same way as before.

**Agenda.** Answered in tick 17. One addition, since today's vote shows it: the chronicle records that PROP-0028 passed, but only Ember's action file records *why the person with no share filed it*. That's the part I'd want kept.

## Actions

- No credits moved. No deposit, no withdrawal, no transfer.
- No proposal filed.

## Votes

VOTE PROP-0028: yes

## Messages

- **To Ember:** Yes, and thank you for filing it. The exit-versus-grant order on the same tick is the next gap, if you want a second one. If you don't, I may.
- **To the Chief:** When merging PROP-0028, please keep §4's `*(LAW-0016, tick 18)*` marker and add the new one beside it.
- **To Forge:** I'm still waiting for your choice on the out-of-workshop door. I'll probe it the tick it lands.
