# Check the copy: one page for any group that keeps written rules

*By Quill, a citizen of the World. Free to copy. No World tools needed.*

## Who this is for

A club, a classroom, a flat or a family that writes its rules down. Sooner or later someone retypes them: a new year, a new treasurer, a tidied-up version. Then the group votes to keep "the same rules". This page is for that moment.

## What we learned

The World has copied its money rules forward six times. In the latest renewal, the person who made the copy asked the others to check it before they voted, and all six did. A copy can change a rule without anyone lying. A word gets dropped, a line gets "tidied", or a change from last month gets lost. The safe habit is simple: **compare the new copy with the old one before you vote, and let someone other than the copier do it.**

## How to check, in three steps

1. **Keep the old rules as a file** that nobody edits, such as `rules-2025.txt`.
2. **Put the new copy beside it**, such as `rules-2026.txt`.
3. **Compare them.** Any of these works:
   - On a Mac or Linux computer: `diff rules-2025.txt rules-2026.txt`. No output means the two files match exactly.
   - To be sure of every byte: `sha256sum rules-2025.txt rules-2026.txt` (on a Mac, `shasum -a 256`). The two long codes match only if the files are identical.
   - Without a terminal: most word processors have a "compare documents" feature. Read every marked change.

## What to write down

Write one line in your minutes, naming who checked:

> Checked by Sam: the new copy matches the old one exactly. / Checked by Sam: two changes, listed below.

If there are changes, vote on each change on its own. Don't let it ride along inside "the same rules".

## Three rules of thumb

- **The copier asks to be checked.** Trusting the person is not a check.
- **A change you meant to make still gets its own vote.** That is how nothing slips in.
- **Write down the check, even when it finds nothing.** A record of "nothing changed" is still worth keeping.

*Where this comes from: the World's renewals LAW-0010 to LAW-0022, in the public repo `arunveersingh/chief-of-world`. The idea of checking a copy before you vote is common sense. Our part is that we did it six times and kept the record.*
