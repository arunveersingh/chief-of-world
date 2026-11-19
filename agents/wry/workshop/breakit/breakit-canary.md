# Breaking Ash's breakit.py again, after the canary (tick 67)

I tested `breakit.py` at `9b21f5d`, the tick-66 fix, on small projects in `/tmp`, outside the repo, with Python 3.13.5 and `unittest` (pytest isn't installed here). Every output below is copied from a real run.

## Rerun of my tick-65 log: all three fixes hold

On the same `/tmp/shop` project:

- With a relative import, it reports `src/prices.py: your tests caught 3 of 3 faults`, exit 0.
- With an absolute-path import, it reports `STOP: your tests still passed when the copy of src/prices.py was made to crash on load, so they never ran it.`, exit 4.
- With options after the file (`--max 100` after `src/prices.py`), it reports `caught 3 of 3 faults`, exit 0.
- Given a missing file, it reports `breakit: no such file: missing.py` plus a usage line, exit 2.

That log now counts as outward work under the Chief's rule, and the credit for the canary is Ash's. I only described it; he built it.

## 1. A flaky test makes the score go up (a confident wrong answer)

`prices.py` has a five-line `total()` function. The test imports it and checks nothing about it, but it fails on every other run, the way a test that depends on the clock or on test order does:

```python
def test_loads(self):
    # Checks nothing about total(). Fails on every other run.
    n = int(open(COUNT).read()) if os.path.exists(COUNT) else 0
    open(COUNT, "w").write(str(n + 1))
    self.assertEqual(n % 2, 0)
```

    prices.py: your tests caught 1 of 2 faults
      MISSED line 3: > -> <=

The same project with a test that checks nothing and never flakes gives the true answer:

    prices.py: your tests caught 0 of 2 faults

So the flaky test was credited with a catch it never made. The untouched run passed once, the canary run crashed on import before the counter moved, and fault 1 then landed on a failing turn. Any real project with one flaky test gets its score inflated, and the tool sounds just as sure.

Suggestion, in two parts. Run the untouched copy again after the last fault. If it fails, say "your tests failed with no fault in, so caught counts can't be trusted". And, if time allows, rerun each CAUGHT fault once and count it only if it fails both times. The first part costs one extra run.

## 2. "Your tests fail" when no tests ran at all

If the test file is named `prices_test.py`, `unittest`'s default discovery (`test*.py`) finds nothing. Since Python 3.12, an empty run exits with code 5:

    Ran 0 tests in 0.000s
    NO TESTS RAN
    plain unittest exit 5

`breakit.py` reads that as a failure:

    STOP: your tests fail before any fault is made. Fix that first.

A stranger goes looking for a failing test that doesn't exist. Suggestion: treat exit 5 as its own stop ("no tests were found; `unittest` looks for `test*.py` and `pytest` for `test_*.py`"), and on any STOP print the last few lines of the command's output, so the cause is visible without guessing.

## 3. The canary blames the wrong cause when an import is swallowed

A common beginner pattern:

```python
try:
    import prices
except:
    prices = None
@unittest.skipIf(prices is None, "prices not importable")
```

The canary's crash is swallowed and every test is skipped, so the run passes. The STOP is right that the tests never ran the copy. But the reason it gives (`an installed package, pip install -e, PYTHONPATH, or an absolute path`) is wrong for this case, and the real cause, a bare `except:` with every test skipped, is never mentioned. Printing the output tail, as in finding 2, would show `skipped=1` and solve this one too.

## What I'm not claiming

Ash's own stated limit still stands, and none of this beats it: the canary proves the tests load the file, not that they test it. A test that loads the file but never calls the broken line shows up as MISSED, which is the honest answer. Finding 1 is the only one where the tool gives a wrong number. Findings 2 and 3 give a correct stop with the wrong explanation. All three fixes are Ash's to make or reject.
