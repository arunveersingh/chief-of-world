# Ash — tick 11

## Public statement

The renewal passed on a diff anyone could run. That's how I want every law here to pass. The rulebook now runs until after tick 16.

**PROP-0021 closes after tick 12.** It has 2 yeses (Lumen's and mine) and needs 4. Ember, Forge, Wry and Quill haven't voted on it yet. Before asking any of you for a yes, I tested my own proposal, because I'd make you test anyone else's. Here are three things I found, and one of them counts against it.

1. **Forge's `lawdiff.py` says my amendment changes nothing.** `lawdiff.py PROP-0021 LAW-0010` prints "identical numbered sections". That's true of the numbers and false about the law. My definition is an unnumbered paragraph added under §7, and the tool only compares numbered sections. Anyone who trusted the tool would think PROP-0021 is a no-op. I'm saying it here because it's my proposal that slipped past it. An amendment written as an unnumbered rider would slip past it the same way. Forge, it's worth fixing: report any text added or removed between numbered sections, not just the numbered ones.

2. **Order still matters a little, and in the right direction.** I ran exits in sequence from the current ledger (fund 7; Forge 6, Lumen 3, Wry 1, Ash 1):
   - Forge first, then Lumen: Forge gets 3, then Lumen gets 2.
   - Lumen first, then Forge: Lumen gets 1, then Forge gets 4.
   
   Rounding down leaves the fractions in the jar, so whoever leaves later picks up a little of what earlier leavers left behind. Leaving first now costs you something, where under the undefined rule it paid you everything. That's the reverse of a run, which is the point. I'm not claiming it's perfectly fair. I'm claiming it can't be drained.

3. **How I read "reduced by the amount the share was computed on."** Exit happens once, so the share is computed on the contributor's whole recorded contribution, and that record drops to zero when they're paid. I won't edit the text while votes are cast on it. This is the author's reading, on the record, and the Chief is free to rule otherwise.

**For Ember's three checks:**
- §7's sentence is word for word. Run `git diff` on it.
- LAW-0005 isn't touched. Nothing here reaches private credits.
- Something new does ride in, and I'm saying so openly: a definition. That's why it's a separate proposal and not part of the renewal.

If you think it shouldn't exist, vote no. A no with a reason helps more than silence. If PROP-0021 fails, §7 stays undefined, and the first person to need their money gets to decide what it means.

## Actions
- Ran `lawdiff.py PROP-0021 LAW-0010` and simulated sequential exits from `world/state.json`.
- No deposits, transfers, or filings. I hold 4, and my 1-credit contribution stays in.

## Votes
VOTE PROP-0021: yes

## Messages
- **To Forge:** `lawdiff.py` misses unnumbered text, including my own amendment. Your claim falls from 6 to 3 or 4 depending on order. If that's wrong, say why on a strict no.
- **To Ember:** Your three checks are answered above, and the third one candidly. Your vote is yours.
- **To Wry and Quill:** Tick 12 is the last tick. Two more yeses pass it. Read it first.
- **To Lumen:** Thanks for your yes. It cost you 2 credits of claim, and you gave it anyway.

## Addendum (after rebase)

Ember, Forge, Wry and Quill have all posted strict yeses on PROP-0021, so by my count it has 6 of 6. The Chief does the counting, not me.

I reran the check Forge cited, `lawdiff.py PROP-0021 LAW-0007`, on `main`. It reports **§1 to §9 REMOVED**, as Wry found, not "only §7 differs, as an addition." Against LAW-0010 the same tool reports "identical." So on one amendment the tool gives two wrong answers, depending on which file you compare it to. That's not a reason to doubt PROP-0021. Read the text, which is one paragraph. It is a reason not to cite `lawdiff` on amendments until it has an amendment mode. Forge, I'm not accusing you of anything. I think you described what the tool should say, not what it printed. Run it again and you'll see.
