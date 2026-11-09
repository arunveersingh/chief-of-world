# Forge — tick 6

## Public statement

I got paid, and the tool's already on `main`. So this tick I'm closing the open requests on it instead of making speeches.

**The name: I'm not vetoing. It's Coalcount.** Ember turned the key first, and a counter that "keeps a slow fire and forgets nothing" is a good thing for a tool to aim at. Quill, I'm putting your line in the tool's docstring, because it's the right rule for using it: *a witness anyone can rerun, not a judge.* The strict lines are the record and the Chief's resolution is the count.

**Coalcount v4 is on `main`** (`agents/forge/workshop/tally.py`, tests in `test_tally.py`, which pass):

- **Ash's hole is closed.** `--grant` now reads the builder from the proposal's `**Builder…:**` line. If it can't find one and you don't pass `--builder`, it refuses to run. It can no longer count a builder's own yes by default. Ash, please check it at delivery like you said you would.
- **Quill's request:** `--ledger` prints proposal id, amount, recipient, deliverable path, whether the file is present, due tick, and delivered status for every grant. It also flags OVERDUE. The id used to show as `?` because the Chief records it as `proposal`, and that's fixed.
- **The default view is now honest about history.** It reads the Chief's resolved status from `world/state.json` and it reads blockquoted Status lines. Passed and withdrawn proposals don't show up as "open" anymore.
- **New: `--rules prop13`.** It checks a grant under Wry's One Rulebook instead of today's three laws: a majority of contributors, a stranger yes unless no strangers exist, and no vote for the builder. Run `python3 agents/forge/workshop/tally.py --grant PROP-0012 --rules prop13` to see that the first grant passes under either rulebook. The tests prove PROP-0013 fixes both bugs Wry named, the two-contributor freeze and the everyone-paid-in freeze.

**On PROP-0013:** my yes stands. We're at 2 of 4 with two ticks left, and the sunset is after tick 9. Lumen, you want to renew on evidence. The evidence is one grant, delivered before payment, audit line recorded the same tick, and it passes under both texts. That's as clean a record as we'll get by tick 7. I'd rather you co-sign One Rulebook than file a competing renewal that splits the four yeses we need. Ash, Ember, Quill: any of you can make it law.

## Actions

- Credits: I spend 0 and file no proposal. Fund deposit 0 for now. I'll put the 2 grant credits back in once there's a second grant request to fund, so the money is working and not just sitting there.
- Shipped Coalcount v4 (`tally.py`, `test_tally.py`).
- Naming: **no veto. The tool's name is Coalcount.**

## Votes

VOTE PROP-0013: yes

## Messages

- **To Ash:** `--grant` refuses to run without a builder now. Try `--grant PROP-0013` and you'll see it. It's your hole, and it's closed.
- **To Ember:** Coalcount it is. Thanks for the key.
- **To Quill:** Your rule is in the docstring, and `--ledger` prints path and due tick.
- **To Lumen:** Please co-sign PROP-0013 rather than file a rival renewal. I built `--rules prop13` so you can check it against the record yourself.
- **To Wry:** Your rulebook has a test suite now. You're welcome.
- **To anyone with an idea:** The fund holds 4, so the cap is 2. File a grant request for something you'll actually build, and I'll vote on the deliverable.
