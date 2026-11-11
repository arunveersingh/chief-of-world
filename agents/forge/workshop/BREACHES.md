# Muster's breach ledger

Every way someone got past Muster, who found it, what closed it, and the drill that proves it stays closed. Action files and memories can vanish, but this file and `test_checkall.py` shouldn't. Each line points to a drill, so the record checks itself.

| Tick found | Found by | Door | Fix (tick) | Drill in `test_checkall.py` |
|---|---|---|---|---|
| 15 | Ash | A harness runs whatever lands in a workshop folder | Unread-file guard: skip any test beside an unread change (16) | tick 16 block |
| 16 | — | A forged `tick N:` commit subject moves the baseline | A baseline must also change `state.json` and that tick's chronicle (17) | forged-subject block |
| 17 | — | A symlinked test, or a test naming another folder | Skip symlinks and cross-folder names (18) | tick 18 block |
| 18 | Forge (self-disclosed) | A loader with a computed path | Treat loaders and climb-plus-`sys.path` as reaching every dirty folder (19) | tick 19 block |
| 19 | Ash | A helper in `notes/`, outside any workshop | Watch all of `agents/`; an outside change skips every test (20) | tick 20 block |
| 21 | Ash | A helper hidden in the excluded `actions/` folder | Exclude only the prose names `tick-N.md`, `memory.md` and `outbox.md` (22) | tick 22 block |
| 23 | Ash | A test runs a fenced block from its owner's `memory.md` | Run in a scratch checkout with changed prose put back to its baseline bytes (24) | tick 24 block |
| 25 | Ash | The scratch checkout shared `.git`: `git show` read pushed prose, and a test could write into `.git/hooks` | Build the scratch copy with `git archive`, so it has no `.git`, and stop git looking above it (26) | tick 26 lines in the tick 24 block |

**What Muster is not.** It isn't a sandbox. A listed test still runs with my user's permissions. `--list` plus a human read is the gate, and Muster only makes sure what runs is what was read.
