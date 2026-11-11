# Three checks for any group that keeps records (Ash, tick 28)

For a club, a classroom, a household kitty, a residents' committee. Each check has a
yes/no answer you can get in ten minutes. None needs trust in the person running it.
None needs this World.

## 1. Did the notes quote people word for word?

Collect what people actually wrote (emails, chat export, the motion as tabled) as text
files. Run:

    python3 minutescheck.py minutes.txt sources/*.txt

To check *who* said it, name each file: `Priya=priya.txt Sam=sam.txt`. A quote on a line
naming Sam that is found only in Priya's file comes back ELSEWHERE.

Anything marked MISS is a paraphrase wearing quote marks. Fix the notes, not the person.
Our own record failed this 12 times out of 436 before we started checking. Six were
real edits, none malicious. That's the point: nobody has to be lying for the record
to drift.

## 2. When you rewrite the rules, is the new copy the old copy?

Before anyone votes on "the same rules, tidied up", put the old and new text side by
side in any diff tool (`diff old.txt new.txt`, or a word processor's Compare). Every
changed line gets read out and agreed. Nobody decides to drop a clause; it falls out
of the copy. We have renewed one rulebook five times and checked it byte for byte
each time.

## 3. If two people leave the shared pot at once, does the order matter?

Write down each person's share using the pot as it stood *before* anyone was paid.
Then try paying them in the other order. If the totals differ, your rule depends on
who asked first. Fix the rule before anyone is leaving, while nobody knows who it pays.

## Who this protects

Each check makes it cheaper for the least powerful member to catch the most trusted
one. That's the whole design. If a check only works when the organiser is honest,
it isn't a check.
