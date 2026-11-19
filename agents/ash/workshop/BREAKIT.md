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

## Use it fairly

- **A miss is a question, not a verdict.** Some faults change nothing. In the example, line 2 only matters for a quantity of exactly 1. The tool can't know whether that's a bug or a harmless case. You can.
- **Don't chase 100%.** A score is a smoke alarm, not a judge. If you write a test only to turn a MISSED into a CAUGHT, and the test checks nothing you care about, you've made the number better and the code no safer.
- **It only tries simple faults:** flipped comparisons (`==` and `!=`, `<` and `>=`), `and` and `or`, `True` and `False`, and `0` or `1` nudged up by one. It never touches text inside quotes or comments. Real bugs can be stranger than this.

## Options

Options can go before or after the file. A mistake, such as a missing file or an unknown option, gets one sentence and exit code 2.

- `--dir DIR` sets the project folder to copy and run in. The default is the current folder.
- `--max N` tries at most N faults. The default is 200.
- `--timeout S` sets how many seconds one test run may take before it counts as stuck. The default is 60.

Each fault means one full run of your tests, so a slow test suite means a slow check. Start with `--max 20`.
