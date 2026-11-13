import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import clock
root = clock.repo_root(os.path.dirname(__file__))
res, st = clock.main(["clock.py", "--repo", root])
# v3 (tick 15): don't hard-code the sunset. Read LAW-0007's header independently and agree with it.
import glob, re
hdr = [l for l in open(glob.glob(os.path.join(root, "governance/laws/LAW-0007-*.md"))[0], encoding="utf-8") if l.lstrip().startswith("**Sunset")][0]
# v4 (tick 51): Decree 9 / Article 0.6, laws stand until repealed. A header may now say "none";
# then clock must report no sunset for LAW-0007 at all, not a stale one from the old clock.
m = re.match(r"\s*\*\*Sunset:\*\*\s*(?:expires after tick (\d+))?", hdr, re.I)
want = int(m.group(1)) if m and m.group(1) else None
assert res.get("LAW-0007") == want, (res, want)
assert all(s[2] == "LAW-0007" for s in st)
assert not any(s[0] == "LAW-0007" for s in st), "header line must not count as stale"
# v2: annotated lines are not stale
import tempfile
d = tempfile.mkdtemp(); law = os.path.join(d, "LAW-9.md")
open(law, "w").write("**Sunset:** expires after tick 16\n**Effect:** sunset (after tick 12; since LAW-0010: after tick 16)\n**Effect:** this expires after tick 12\n")
got = clock.stale({"LAW-9": law}, {"LAW-9": 16})
assert [g[1] for g in got] == [3], got
assert not any(s[0] in ("LAW-0008", "LAW-0009") for s in st), "Chief's annotations must read clean"
print("all clock tests pass")
