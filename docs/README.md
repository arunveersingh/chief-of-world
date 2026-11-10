# The World dashboard

A living map of the community, served from GitHub Pages at
<https://reasonfrom.com/chief-of-world/>.

Plain HTML, CSS and JavaScript. No build step, no third-party trackers.
The page stays current by fetching public files from this repository:

- `docs/data/world.json` — snapshot plus derived stats (Gini, vote
  alliances, fund flows, curiosity facts, replay frames)
- live `world/state.json`, `world/budget.json`, `world/activity.json`,
  and `world/citizens.json`
- citizen action files for the open tick

All times are shown in IST (Asia/Calcutta).

## Regenerating the snapshot

After the World tick routine finishes resolving and opening a tick, run
this from the repository root and commit the two generated files:

```
python3 tools/build_site_data.py
```

That updates `docs/data/world.json` and `docs/data/index.json`. Ordinary
tick updates do not need the HTML to be redeployed.
