"""Forge, tick 35: does PROP-0036's §4 use exactly the words of LAW-0007 §4, labels aside?
Read-only. Prints SAME WORDS or DIFFERENT plus the words that differ."""
import glob, re, sys
from collections import Counter
words = lambda s: Counter(re.findall(r"[a-z0-9§']+", re.sub(r"\*\(LAW[^)]*\)\*", "", s).lower()))
law = open(glob.glob("governance/laws/LAW-0007-*.md")[0]).read()
old = law[law.index("\n4. "):law.index("\n5. ")]
prop = open(glob.glob("governance/proposals/PROP-0036-*.md")[0]).read()
new = prop[prop.index("> 4. "):prop.index("## Why")]
new = re.sub(r"\(\w\) (Half the balance|Withdrawals first|Grants in number order)\.", "", new)
a, b = words(old), words(new)
if a == b:
    print("SAME WORDS"); sys.exit(0)
print("DIFFERENT", "only in law:", dict(a - b), "only in proposal:", dict(b - a)); sys.exit(1)
