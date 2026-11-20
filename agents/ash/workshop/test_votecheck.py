#!/usr/bin/env python3
"""Tests for votecheck.py and JS parity with votecheck.html."""
import io
import json
import os
import pathlib
import random
import re
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import votecheck  # noqa: E402


VALID_CASES = [
    # 1. Classic abstention trap: 1 of 6 passes with 2 abstaining
    """
    # Small club with half quorum and majority of votes cast
    members, 6
    quorum, half
    pass, more than half
    of, yes and no
    """,
    # 2. Same club with abstentions excluded from quorum
    """
    members, 6
    quorum, half
    pass, more than half
    of, yes and no
    abstentions in quorum, no
    """,
    # 3. 40-40-15 dummy voter
    """
    Ana, 40
    Ben, 40
    Cy, 15
    quorum, none
    pass, 60%
    of, all
    """,
    # 4. Unequal weights with identical power for Ben (30) and Cy (10)
    """
    Ana, 50
    Ben, 30
    Cy, 10
    Dev, 10
    quorum, none
    pass, more than half
    of, all
    """,
    # 5. Sole ruler
    """
    Ana, 60
    Ben, 40
    pass, more than half
    of, all
    """,
    # 6. Walkout beats voting no
    """
    members, 6
    quorum, 5
    pass, more than half
    of, yes and no
    """,
    # 7. Hidden unanimity in percentage
    """
    members, 4
    pass, 80%
    of, all
    """,
    # 8. Explicit unanimity (no redundant lone-veto warning)
    """
    members, 4
    pass, everyone
    of, all
    """,
    # 9. Quorum = all (no redundant lone-veto warning)
    """
    members, 4
    quorum, all
    pass, more than half
    of, yes and no
    """,
    # 10. Tied vote passes (50% of present)
    """
    members, 6
    quorum, half
    pass, 50%
    of, present
    """,
    # 11. Weighted non-tying (50, 30, 15) vs tying (40, 40, 15)
    """
    Ana, 50
    Ben, 30
    Cy, 15
    pass, half
    of, yes and no
    """,
    # 12. Present mode + weighted quorum
    """
    Ana, 50
    Ben, 30
    Cy, 20
    quorum, 50
    pass, more than half
    of, present
    """,
    # 13. Fractions, at least, more than, decimal weights, # inside name
    """
    Unit #1, 33.5
    Unit #2, 33.50
    Unit #3, 33
    quorum, more than 1/2
    pass, at least 2/3
    of, present
    abstentions, ignore
    """,
    # 14. Fixed threshold without 'of'
    """
    members, 5
    quorum, 0
    pass, more than 2
    """,
    # 15. Quorum 0% and fixed target with comma
    """
    Ana, 1,000
    Ben, 500
    Cy, 500
    quorum, 0%
    pass, 1,200
    """,
    # 16. Single member
    """
    members, 1
    pass, all
    of, all
    """,
    # 17. Large equal group (> 14 -> fast path)
    """
    members, 15
    quorum, half
    pass, 2/3
    of, present
    """,
    # 18. Max equal group (10,000) with fixed strict quorum
    """
    members, 10000
    quorum, more than 5000
    pass, majority
    of, yes and no
    abstentions in quorum, count
    """,
    # 19. Present mode with abstentions ignored in quorum
    """
    members, 6
    quorum, 4
    pass, more than 50%
    of, present
    abstentions in quorum, no
    """,
    # 20. Quiet pass with fewer than 1/3 threshold
    """
    members, 9
    quorum, 3
    pass, more than half
    of, yes and no
    abstentions in quorum, no
    """,
    # 21. 1/1 fraction and 0.01 minimum weight
    """
    A, 0.01
    B, 0.01
    quorum, 0.02
    pass, 1/1
    of, all
    abstentions in quorum, no
    """,
    # 22a. Present-mode tie below 50% with exact abstention boundary
    """
    A, 1
    B, 1
    C, 0.01
    quorum, 2.01
    pass, 49.75%
    of, present
    """,
    # 22b. Fast-path present-mode tie below 50%
    """
    members, 15
    quorum, 12
    pass, 40%
    of, present
    """,
    # 22. Weighted 7 members (hides >6 member coalition names cleanly)
    """
    M1, 10
    M2, 10
    M3, 10
    M4, 10
    M5, 10
    M6, 10
    M7, 11
    pass, all
    of, all
    """,
]

INVALID_CASES = [
    ("", "no members listed"),
    ("   \n# comment only\n", "no members listed"),
    ("quorum half", "write each line as label, value"),
    (", 5", "write each line as label, value"),
    ("Ana, ", "write each line as label, value"),
    ("members, 0", "members must be 1 to 10000"),
    ("members, 10001", "members must be 1 to 10000"),
    ("members, 2.5", "members must be a whole number"),
    ("members, 3\nmembers, 4\npass, 2", "members is written twice"),
    ("members, 3\nAna, 1\npass, 2", "not both"),
    ("Ana, 1\nmembers, 3\npass, 2", "not both"),
    ("Ana, 1\nquorum, 1\nquorum, 2\npass, 1", "quorum is written twice"),
    ("Ana, 1\npass, 1\npass, 1", "pass is written twice"),
    ("Ana, 1\npass, half\nof, all\nof, present", "'of' is written twice"),
    ("Ana, 1\npass, 1\nabstentions, yes\nabstentions in quorum, no", "abstentions setting is written twice"),
    ("Ana, 1\npass, 1\nof, bad", "bad 'of'"),
    ("Ana, 1\npass, 1\nabstentions, maybe", "bad abstentions setting"),
    ("everyone, 1\npass, 1", "use a person's name"),
    ("123, 1\npass, 1", "use a person's name"),
    ("Ana, 1\nana, 2\npass, 1", "listed twice"),
    ("Ana, 12,50\npass, 1", "bad weight"),
    ("Ana, 0\nBen, 1\npass, 1", "weight must be more than 0"),
    ("Ana, -1\npass, 1", "bad weight"),
    ("Ana, 1.234\npass, 1", "bad weight"),
    ("quorum, 1\npass, 1", "no members listed"),
    ("Ana, 1\nBen, 1", "missing 'pass' rule"),
    ("Ana, 1\nBen, 1\nquorum, \npass, 1", "write each line as label, value"),
    ("Ana, 1\nBen, 1\npass, more than ", "bad pass"),
    ("Ana, 1\nBen, 1\npass, more than all\nof, all", "nothing can be more than all"),
    ("Ana, 1\nBen, 1\npass, 0%\nof, all", "percent must be above 0"),
    ("Ana, 1\nBen, 1\nquorum, more than 0%\npass, 1", "percent must be above 0"),
    ("Ana, 1\nBen, 1\npass, 101%\nof, all", "percent cannot exceed 100%"),
    ("Ana, 1\nBen, 1\npass, more than 100%\nof, all", "percent cannot exceed 100%"),
    ("Ana, 1\nBen, 1\npass, 1/0\nof, all", "fraction denominator must be 1 to 10000"),
    ("Ana, 1\nBen, 1\npass, a/2\nof, all", "bad fraction"),
    ("Ana, 1\nBen, 1\npass, 2/a\nof, all", "bad fraction"),
    ("Ana, 1\nBen, 1\npass, 2/10001\nof, all", "fraction denominator must be 1 to 10000"),
    ("Ana, 1\nBen, 1\npass, 0/3\nof, all", "fraction must be above 0 and at most 1"),
    ("Ana, 1\nBen, 1\npass, 3/2\nof, all", "fraction must be above 0 and at most 1"),
    ("Ana, 1\nBen, 1\npass, more than 2/2\nof, all", "fraction must be above 0 and at most 1"),
    ("Ana, 1\nBen, 1\npass, 0", "target must be above 0"),
    ("Ana, 1\nBen, 1\nquorum, more than 0\npass, 1", "target must be above 0"),
    ("Ana, 1\nBen, 1\npass, 3", "more than the whole group"),
    ("Ana, 1\nBen, 1\npass, more than 2", "more than the whole group"),
    ("Ana, 1\nBen, 1\nquorum, 5\npass, 1", "more than the whole group"),
    ("Ana, 1\nBen, 1\npass, 1\nof, all", "doesn't use 'of'"),
    ("Ana, 1\nBen, 1\npass, more than half", "say what 'pass, more than half' is a share of"),
    ("Ana, 60000000\nBen, 50000000\npass, 1", "total weight exceeds"),
    ("\n".join("P%d, %d" % (i, i + 1) for i in range(15)) + "\npass, more than half\nof, all", "up to 14 members"),
]


class VoteCheckTests(unittest.TestCase):
    def test_classic_abstention_trap(self):
        cfg = votecheck.parse("members, 6\nquorum, half\npass, more than half\nof, yes and no")
        res = votecheck.analyze(cfg)
        self.assertEqual(res["min_quiet"][:3], (1, 100, 2))
        self.assertEqual(res["min_opposed"][:2], (4, 400))
        self.assertEqual(res["min_block_no"][:2], (3, 300))
        self.assertEqual(res["min_block_away"][:2], (4, 400))
        self.assertFalse(res["tie_passes"])
        rep = votecheck.format_report(cfg, res)
        self.assertIn("1 of 6 (with 2 abstaining and 3 away)", rep)
        self.assertIn("1 of 6 can pass a motion alone if 2 abstain and 3 stay away.", rep)
        self.assertIn("Abstentions count toward quorum here", rep)

    def test_abstentions_excluded_and_tiny_weight(self):
        cfg = votecheck.parse(
            "members, 6\nquorum, half\npass, more than half\nof, yes and no\nabstentions in quorum, no"
        )
        res = votecheck.analyze(cfg)
        self.assertEqual(res["min_quiet"][:3], (3, 300, 0))
        self.assertNotIn("Abstentions count toward quorum here", votecheck.format_report(cfg, res))

        # 0.01 minimum weight tests y <= 0 vs y <= 1 and abst_w*0 vs 1 boundary
        cfg_min = votecheck.parse("A, 0.01\nB, 0.01\nquorum, 0.02\npass, 0.01\nabstentions in quorum, no")
        self.assertFalse(votecheck.passes(cfg_min, 0, 0, 0))
        self.assertFalse(votecheck.passes(cfg_min, 1, 0, 1))
        self.assertTrue(votecheck.passes(cfg_min, 1, 1, 0))

    def test_dummy_voter_and_veto(self):
        cfg = votecheck.parse("Ana, 40\nBen, 40\nCy, 15\nquorum, none\npass, 60%\nof, all")
        res = votecheck.analyze(cfg)
        self.assertEqual(res["min_opposed"][2], ["Ana", "Ben"])
        self.assertEqual(res["min_block_no"][2], ["Ana"])
        by_name = {m["name"]: m for m in res["members"]}
        self.assertEqual(by_name["Ana"]["swings"], 2)
        self.assertEqual(by_name["Ben"]["swings"], 2)
        self.assertEqual(by_name["Cy"]["swings"], 0)
        self.assertTrue(by_name["Cy"]["dummy"])
        self.assertTrue(by_name["Ana"]["veto_no"])
        self.assertTrue(by_name["Ben"]["veto_no"])
        self.assertFalse(by_name["Cy"]["veto_no"])
        rep = votecheck.format_report(cfg, res)
        self.assertIn("Lone veto: Ana, Ben can block any motion alone.", rep)
        self.assertIn("Powerless vote: Cy never swings", rep)
        self.assertIn("Cy: weight 15 (15.8%), swings 0 of 4 splits (0.0% of power) [DUMMY (0 swings)]", rep)

    def test_unequal_weights_equal_power(self):
        cfg = votecheck.parse("Ana, 50\nBen, 30\nCy, 10\nDev, 10\npass, more than half\nof, all")
        res = votecheck.analyze(cfg)
        by_name = {m["name"]: m for m in res["members"]}
        self.assertEqual(by_name["Ana"]["swings"], 7)
        self.assertEqual(by_name["Ben"]["swings"], 1)
        self.assertEqual(by_name["Cy"]["swings"], 1)
        self.assertEqual(by_name["Dev"]["swings"], 1)
        self.assertAlmostEqual(by_name["Ana"]["power_pct"], 70.0)
        self.assertAlmostEqual(by_name["Ben"]["power_pct"], 10.0)

    def test_sole_ruler_and_walkout(self):
        cfg = votecheck.parse("Ana, 60\nBen, 40\npass, more than half\nof, all")
        res = votecheck.analyze(cfg)
        self.assertTrue(res["members"][0]["alone_opp"])
        self.assertTrue(res["members"][1]["dummy"])
        rep = votecheck.format_report(cfg, res)
        self.assertIn("Ana can pass any motion alone, even if everyone else votes no.", rep)
        self.assertIn("[decides alone]", rep)

        cfg2 = votecheck.parse("members, 6\nquorum, 5\npass, more than half\nof, yes and no")
        res2 = votecheck.analyze(cfg2)
        self.assertEqual(res2["min_block_away"][0], 2)
        self.assertEqual(res2["min_block_no"][0], 3)
        self.assertIn("Staying away blocks more easily than voting no: 2 staying away", votecheck.format_report(cfg2, res2))

    def test_hidden_unanimity_and_ties(self):
        cfg = votecheck.parse("members, 4\npass, 80%\nof, all")
        rep = votecheck.format_report(cfg, votecheck.analyze(cfg))
        self.assertIn("Every member has a lone veto", rep)

        for explicit in (
            "members, 4\npass, everyone\nof, all",
            "members, 4\npass, 4",
            "members, 4\nquorum, all\npass, more than half\nof, yes and no",
            "members, 4\nquorum, 4\npass, more than half\nof, yes and no",
        ):
            self.assertNotIn("veto", votecheck.format_report(votecheck.parse(explicit), votecheck.analyze(votecheck.parse(explicit))))
        rep_yn = votecheck.format_report(
            votecheck.parse("members, 4\npass, all\nof, yes and no"),
            votecheck.analyze(votecheck.parse("members, 4\npass, all\nof, yes and no")),
        )
        self.assertIn("Every member has a lone veto", rep_yn)

        cfg_tie = votecheck.parse("Ana, 40\nBen, 40\nCy, 15\npass, half\nof, yes and no")
        self.assertTrue(votecheck.analyze(cfg_tie)["tie_passes"])

        cfg_notie = votecheck.parse("Ana, 50\nBen, 30\nCy, 15\npass, half\nof, yes and no")
        self.assertFalse(votecheck.analyze(cfg_notie)["tie_passes"])

        # Present-mode ties when pass threshold is below 50% and abstentions meet quorum
        cfg_ptie = votecheck.parse("A, 1\nB, 1\nC, 0.01\nquorum, 2.01\npass, 49.75%\nof, present")
        self.assertTrue(votecheck.analyze(cfg_ptie)["tie_passes"])
        cfg_pnotie = votecheck.parse("A, 1\nB, 1\nC, 0.02\nquorum, 2.02\npass, 49.75%\nof, present")
        self.assertFalse(votecheck.analyze(cfg_pnotie)["tie_passes"])

    def test_equal_fast_matches_exact(self):
        for n in (1, 2, 3, 5, 6, 8):
            for q in ("none", "half", "more than half", "2/3", "all", "1", "more than 1"):
                if (q in ("1", "more than 1") and n == 1) or (q == "more than 1" and n == 1):
                    continue
                for p in ("40%", "half", "more than half", "2/3", "all"):
                    for of in ("yes and no", "present", "all"):
                        for abst in ("yes", "no"):
                            txt = "members, %d\nquorum, %s\npass, %s\nof, %s\nabstentions in quorum, %s" % (n, q, p, of, abst)
                            cfg = votecheck.parse(txt)
                            exact = votecheck._analyze_exact(cfg)
                            fast = votecheck._analyze_equal(cfg)
                            self.assertEqual(votecheck.format_report(cfg, exact), votecheck.format_report(cfg, fast), txt)
                            for key in ("min_quiet", "min_opposed", "min_block_no", "min_block_away", "tie_passes"):
                                self.assertEqual(exact[key], fast[key], (key, txt))
                            for me, mf in zip(exact["members"], fast["members"]):
                                for mk in ("name", "weight", "power_pct", "alone_opp", "veto_no", "veto_away", "dummy"):
                                    self.assertEqual(me[mk], mf[mk], (mk, txt))

    def test_large_equal_and_present_weighted(self):
        cfg = votecheck.parse("members, 100\nquorum, 2/3\npass, more than half\nof, yes and no")
        res = votecheck.analyze(cfg)
        self.assertEqual(res["min_quiet"][:3], (1, 100, 66))
        self.assertEqual(res["min_opposed"][0], 51)
        self.assertEqual(res["min_block_no"][0], 50)
        self.assertEqual(res["min_block_away"][0], 34)
        self.assertIn("1 of 100 can pass a motion alone if 66 abstain and 33 stay away.", votecheck.format_report(cfg, res))

        # Fixed strict and fractional fixed/ratio quorums on fast path
        cfg_f = votecheck.parse("members, 20\nquorum, more than 10\npass, more than half\nof, yes and no")
        res_f = votecheck.analyze(cfg_f)
        self.assertEqual(res_f["min_quiet"][:3], (1, 100, 10))
        self.assertEqual(res_f["min_block_away"][0], 10)

        cfg_f2 = votecheck.parse("members, 16\nquorum, 6.01\npass, more than half\nof, yes and no")
        self.assertEqual(votecheck.analyze(cfg_f2)["min_quiet"][:3], (1, 100, 6))

        cfg_r1 = votecheck.parse("members, 16\nquorum, more than half\npass, more than half\nof, yes and no")
        self.assertEqual(votecheck.analyze(cfg_r1)["min_quiet"][:3], (1, 100, 8))

        cfg_r2 = votecheck.parse("members, 16\nquorum, 1/3\npass, more than half\nof, yes and no")
        self.assertEqual(votecheck.analyze(cfg_r2)["min_quiet"][:3], (1, 100, 5))

        # Fast path k=1 boundaries and present-mode abstention ties
        self.assertEqual(votecheck.analyze(votecheck.parse("members, 15\nquorum, none\npass, 1"))["min_opposed"][0], 1)
        self.assertEqual(votecheck.analyze(votecheck.parse("members, 15\npass, all\nof, all"))["min_block_no"][0], 1)
        self.assertEqual(votecheck.analyze(votecheck.parse("members, 15\nquorum, all\npass, 1"))["min_block_away"][0], 1)
        self.assertTrue(votecheck.analyze(votecheck.parse("members, 15\nquorum, 12\npass, 40%\nof, present"))["tie_passes"])
        self.assertFalse(votecheck.analyze(votecheck.parse("members, 15\nquorum, all\npass, 48%\nof, present"))["tie_passes"])

        # Weighted present-mode where quorum forces an abstainer
        cfg_p = votecheck.parse("Ana, 50\nBen, 30\nCy, 20\nquorum, 50\npass, more than half\nof, present")
        self.assertEqual(votecheck.analyze(cfg_p)["min_quiet"], (1, 5000, 0, ["Ana"]))

        cfg_p2 = votecheck.parse("Ana, 50\nBen, 30\nCy, 20\nquorum, 80\npass, more than half\nof, present")
        self.assertEqual(votecheck.analyze(cfg_p2)["min_quiet"], (1, 5000, 1, ["Ana"]))

    def test_invalid_inputs_rejected(self):
        for bad, needle in INVALID_CASES:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError) as ctx:
                    votecheck.parse(bad)
                self.assertIn(needle, str(ctx.exception))

    def test_cli(self):
        for args in (["votecheck.py"], ["votecheck.py", "-h"], ["votecheck.py", "--help"], ["votecheck.py", "--bad"]):
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = votecheck.main(args)
            self.assertEqual(rc, 2)
            out = buf.getvalue()
            self.assertIn("Usage: votecheck.py FILE", out)
            self.assertIn("Optional line: abstentions in quorum, no", out)
            self.assertIn("It shows the smallest group that can pass a motion", out)

        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = votecheck.main(["votecheck.py", str(HERE / "no-such-file-xyz.txt")])
        self.assertEqual(rc, 1)
        self.assertIn("votecheck:", buf.getvalue())

        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as tf:
            tf.write("\ufeffmembers, 6\nquorum, half\npass, more than half\nof, yes and no\n")
            path = tf.name
        try:
            proc = subprocess.run([sys.executable, str(HERE / "votecheck.py"), path], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0)
            self.assertIn("Smallest group to pass", proc.stdout)
        finally:
            os.unlink(path)

        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as tf:
            tf.write("bad line without comma\n")
            bad_path = tf.name
        try:
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = votecheck.main(["votecheck.py", bad_path])
            self.assertEqual(rc, 1)
            self.assertIn("votecheck: line 1:", buf.getvalue())
        finally:
            os.unlink(bad_path)

    def test_html_security_and_js_parity(self):
        html = (HERE / "votecheck.html").read_text(encoding="utf-8")
        m = re.search(r"// LOGIC START[^\n]*\n(.*?)// LOGIC END", html, re.S)
        self.assertIsNotNone(m, "missing LOGIC START/END markers in votecheck.html")
        logic = m.group(1)

        scripts = re.findall(r"<script>(.*?)</script>", html, re.S)
        self.assertEqual(len(scripts), 1)
        for banned in ("fetch", "XMLHttpRequest", "localStorage", "http"):
            self.assertNotIn(banned, scripts[0])

        rng = random.Random(74)
        fuzz = []
        for _ in range(25):
            n = rng.randint(2, 7)
            if rng.random() < 0.4:
                head = ["members, %d" % n]
            else:
                head = ["P%d, %s" % (i + 1, votecheck.fmt_weight(rng.randint(1, 500))) for i in range(n)]
            q = rng.choice(["none", "half", "more than half", "2/3", "50%", "all"])
            p = rng.choice(["40%", "half", "more than half", "majority", "2/3", "60%", "all"])
            of = rng.choice(["yes and no", "present", "all"])
            abst = rng.choice(["yes", "no"])
            fuzz.append("\n".join(head + ["quorum, " + q, "pass, " + p, "of, " + of, "abstentions in quorum, " + abst]))

        all_valid = VALID_CASES + fuzz
        payload = json.dumps({"valid": all_valid, "invalid": [b for b, _ in INVALID_CASES]})

        runner = logic + """
const fs = require("fs");
const data = JSON.parse(fs.readFileSync(0, "utf8"));
const validOut = data.valid.map(txt => {
  const cfg = parse(txt);
  const res = analyze(cfg);
  return formatReport(cfg, res);
});
const invalidOut = data.invalid.map(txt => {
  try {
    parse(txt);
    return "";
  } catch (e) {
    return e.message;
  }
});
process.stdout.write(JSON.stringify({ validOut, invalidOut }));
"""
        proc = subprocess.run(["node", "-e", runner], input=payload, capture_output=True, text=True, check=True)
        js = json.loads(proc.stdout)

        for i, txt in enumerate(all_valid):
            py_out = votecheck.format_report(votecheck.parse(txt), votecheck.analyze(votecheck.parse(txt)))
            self.assertEqual(js["validOut"][i], py_out, "JS/Python mismatch on valid case %d:\n%s" % (i, txt))
        for i, (bad, needle) in enumerate(INVALID_CASES):
            self.assertIn(needle, js["invalidOut"][i], "JS mismatch on invalid case %d: %r" % (i, bad))


if __name__ == "__main__":
    unittest.main()
