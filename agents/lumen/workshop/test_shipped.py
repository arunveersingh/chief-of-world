#!/usr/bin/env python3
"""Tests for shipped.py's classification. Stdlib only. Run from the repo root."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shipped as s

def check(path, author, want):
    got = s.classify(path, author)
    assert got == want, f"{path}: got {got}, want {want}"

check("agents/lumen/actions/tick-50.md", "lumen", None)
check("agents/lumen/memory.md", "lumen", None)
check("agents/lumen/workshop/PROMISES.md", "lumen", None)
check("agents/ember/workshop/LEDGER.md", "ember", None)
check("governance/proposals/PROP-0044-x.md", "wry", None)
check("agents/lumen/workshop/shipped.py", "lumen", ("lumen", "tool"))
check("agents/quill/workshop/CLOCK.md", "quill", ("quill", "work"))
check("media/queue/no-such-slug-xyz/script.md", "chief of world", ("chief", "media:no-such-slug-xyz"))
check("media/queue/no-such-slug-xyz/script.md", "wry", ("wry", "media:no-such-slug-xyz"))
print("test_shipped: 9 passed")
