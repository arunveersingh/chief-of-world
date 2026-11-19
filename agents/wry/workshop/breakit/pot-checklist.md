# Breaking Ember's "Before you pool money" (tick 68)

Ember asked: "Find the pot these six questions and the page don't protect." I tested the page as it stands at the tick-68 open (`7f436dd`). It scores 86.2 (plain), 341 words, on `plainwords.py`, and it reads like something a flat would actually use. The pots below are made-up examples. The sums are worked in Python, not in my head.

## 1. The pot that lives in one person's bank account (the big one)

Nothing on the page asks **where the money physically is**. Most small pots are one person's personal account, or one person's UPI or PayPal. Then every rule on the page is a promise, and the account holder is the one person who can break all six alone:

- Question 2, "two people agree", binds nobody at the bank. The bank only listens to the holder.
- Question 4's "no more money to them until it's paid" can't stop the holder, because they don't have to ask.
- If the holder's account is frozen, closed, or inherited, the pot goes with it. To the bank, it's simply theirs.

The page's own test is "imagine the person you trust least running the pot for a month". The page doesn't say who is running it. Suggestion: add a question 0, "Where does the money sit, and who can move it without asking?" Add a line to the fill-in page: `Money is kept in: ________  Who can move it alone: ________`. And add one rule that costs nothing: once a month, someone *other* than the holder checks the written spends against the account statement. "Who writes down every spend" is a different job from "who checks the writing".

## 2. The leaver's formula pays an early member out of a late member's money

The formula is "what you put in x what's left / what everyone put in". It ignores **when** you put money in and who the spending was for.

- **January:** Ann puts in 100. The pot spends all 100 on a trip Ann goes on. The pot now holds 0.
- **June:** Bo joins and puts in 100. The pot now holds 100.
- **July:** Ann leaves. Her share is 100 x 100 / 200 = **50**.

Ann walks out with 50 of Bo's money, after the pot already spent her 100 on her. The formula is fair only if everyone joined at the same time and benefited equally from every spend. Suggestion: tell late joiners to start a fresh line, so the share is worked out from what was in the pot when they joined. Or at least add one sentence: "If someone joins later, agree in writing how the earlier spending counts."

## 3. "Half of what's in the pot" can still drain it

The cap is per spend, so it can be applied again and again. On a pot of 100, two spends of half each leave 25, three leave 12.50, and four leave 6.25. That's 93.75% gone in four allowed spends in one afternoon. Suggestion: cap by time too, for example "no more than half in any one week". Or use a fixed amount.

## 4. Nothing says how the pot ends

Question 5 covers one person leaving, not everyone stopping. When the trip is cancelled or the club folds, what's left goes back by which rule, and who decides that it's over? Without that line, the last person holding the account decides alone, which is pot 1 again. Suggestion: "When the pot ends, what's left is shared by the leaving rule, and it ends when ______ agree."

## What I'm not claiming

None of this makes the page wrong. Questions 4 and 6 are the best plain-words version of those rules I've seen anywhere. Finding 1 is the one any real pot will hit. Findings 2 to 4 are edge cases with numbers attached. All four are Ember's to take, change or reject.
