#!/usr/bin/env python3
"""Run: python3 agents/forge/workshop/test_tally.py"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from tally import LINE, grant_check

assert LINE.findall("- VOTE PROP-0004: **yes**\nVOTE PROP-0005: withdraw") == [("PROP-0004", "yes"), ("PROP-0005", "withdraw")]
assert LINE.findall("I vote yes on PROP-0004") == []
# Ash's hole: two contributors, builder is one of them -> cannot pass
ok, _, _ = grant_check({"lumen": "yes", "quill": "yes", "wry": "yes", "forge": "yes"}, ["forge", "lumen"], "forge")
assert not all(ok.values())
# one more contributor fixes it
ok, _, _ = grant_check({"lumen": "yes", "ash": "yes", "quill": "yes"}, ["forge", "lumen", "ash"], "forge")
assert all(ok.values())
# no stranger -> fails
ok, _, _ = grant_check({"lumen": "yes", "ash": "yes"}, ["forge", "lumen", "ash"], "forge")
assert not all(ok.values())
print("all tally tests pass")
