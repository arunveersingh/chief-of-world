# Do your tests notice when your code breaks?

A test that passes tells you the code works today. It doesn't tell you whether the test would fail if someone broke the code tomorrow. `breakit.py` checks that. It breaks your code on purpose, one small fault at a time, and tells you which faults your tests didn't notice.

It's one file, uses only the Python standard library, and makes no network calls. It never changes your own files. All the work happens in a temporary copy that is deleted at the end.

## How to use it

Copy `breakit.py` anywhere. Then, from your project folder:

```
python3 breakit.py prices.py -- python3 -m pytest -q
```

The part before `--` is the one file to break. The part after `--` is the command you already use to run your tests. Any command works, as long as it exits with 0 when the tests pass.

## What you get back

```
shop.py: your tests caught 1 of 3 faults
  MISSED line 2: 0 -> 1
  MISSED line 3: 0 -> 1
```

`MISSED line 3: 0 -> 1` means that when line 3 said `1` instead of `0`, every test still passed. Nothing checks that line that way. Either write a test that would notice, or decide on purpose that it doesn't matter.

`STUCK` means the fault made your tests run past the time limit. That counts as caught, but it's listed so you can decide whether you want a real test for it.

If your tests already fail, or already hang, before any fault is made, it stops and tells you. A fault can't be judged against tests that already fail.

It also refuses to score tests that never run the copy. Before any real fault, it makes the copied file crash the moment it loads. If your tests still pass, they never loaded it, so it stops with exit code 4 and says so instead of giving you a score:

```
STOP: your tests still passed when the copy of src/prices.py was made to crash on load, so they never ran it.
```

That usually means your tests load your original file instead of the copy. That happens with an installed package (`pip install -e .`), a `PYTHONPATH` set in your shell, or an absolute path in a test or `conftest.py`. Make your tests import from the project folder, and run it again. Without this check, the tool used to answer "caught 0 of 3" about tests that were fine.

**Flaky tests.** A test that sometimes fails for no reason, for example because it depends on the clock or on the order tests run in, can make a fault look caught when it wasn't. So before any fault, the tool runs your untouched tests 3 times. If they don't pass all 3 times, it stops with exit code 5 and scores nothing:

```
STOP: your tests passed on run 1 but failed on run 2, with no fault made. They are flaky,
  so any score would be partly luck. Fix the flaky test first. Nothing was scored.
```

That costs two extra runs in all, not two per fault, so a flaky suite is caught before it wastes an afternoon. Change the count with `--repeat N`. A test that fails only rarely can pass 3 times in a row, so there is a second check. Every catch is run twice and counts only if it fails both times. A fault that fails once and then passes is listed as `FLAKY` and not counted. The untouched copy is also run again at the end. If it fails, or anything was `FLAKY`, the tool warns you not to trust the score and exits with 5. This makes a flaky test much less likely to fool it, but not impossible: a test that fails at random can still fail twice in a row. If you see the warning, fix the flaky test first.

**No tests found.** If your test command finds no tests (`unittest` and `pytest` exit with 5), the tool says so instead of saying your tests fail. Every stop also shows the last lines your command printed, so you can see the cause, such as `skipped=1` when a test file catches its own import error and skips everything.

## Use it fairly

- **A miss is a question, not a verdict.** Some faults change nothing. In the example, line 2 only matters for a quantity of exactly 1. The tool can't know whether that's a bug or a harmless case. You can.
- **Don't chase 100%.** A score is a smoke alarm, not a judge. If you write a test only to turn a MISSED into a CAUGHT, and the test checks nothing you care about, you've made the number better and the code no safer.
- **It only tries simple faults:** flipped comparisons (`==` and `!=`, `<` and `>=`), `and` and `or`, `True` and `False`, and `0` or `1` nudged up by one. It never touches text inside quotes or comments. Real bugs can be stranger than this.

## Options

Options can go before or after the file. A mistake, such as a missing file or an unknown option, gets one sentence and exit code 2.

- `--dir DIR` sets the project folder to copy and run in. The default is the current folder.
- `--max N` tries at most N faults. The default is 200.
- `--timeout S` sets how many seconds one test run may take before it counts as stuck. The default is 60.
- `--repeat N` sets how many times the untouched tests run before any fault. The default is 3, and 1 turns the up-front check off.
- `--lines A-B` makes faults only on lines A to B, for example `--lines 90-140`. Use it to check one function in a big file.

Each fault means one full run of your tests, so a slow test suite means a slow check.

**A short run is not a whole score.** `--max 20` tries the first 20 faults, which are the ones nearest the top of the file. If it stops early, the report says what it skipped:

```
bills.py: your tests caught 20 of 20 faults
  NOT TRIED: 15 more faults, from line 77 on (--max 20 stopped the run). This score is for the part tried, not the whole file.
```

That run is real. The only fault those tests miss is on line 100, past where `--max 20` stopped, so "20 of 20" looked perfect. To save time, pick the part you care about with `--lines` instead of cutting the run short. Then the score says which lines it covers: `bills.py: your tests caught 11 of 12 faults on lines 90-140`.
