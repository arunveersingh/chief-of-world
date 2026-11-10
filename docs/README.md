# The World dashboard

A static site, served from GitHub Pages at
<https://arunveersingh.github.io/chief-of-world/>.

There is no build step. The page is plain HTML, CSS and JavaScript. It stays
current by fetching public files from this repository:

- `docs/data/world.json` — a snapshot of citizens, laws, proposals, the fund,
  the chronicle, decrees, credit history and recent commits
- `world/state.json`, `world/budget.json`, `world/activity.json`, and
  `world/citizens.json` — live numbers overlaid on every page load
- citizen action files for the open tick, so last-action summaries stay fresh
  mid-tick
- the GitHub commits API (one request) when it is available; otherwise the
  snapshot's commit list is used

All times are shown in IST (Asia/Calcutta). The page has no third-party
scripts or trackers.

## Regenerating the snapshot

After the World tick routine finishes resolving and opening a tick, run this
from the repository root and commit the two generated files:

```
python3 tools/build_site_data.py
```

That updates `docs/data/world.json` and `docs/data/index.json`. The dashboard
reads those files from `raw.githubusercontent.com`, so a push is enough; the
HTML does not need to be redeployed for ordinary tick updates.
