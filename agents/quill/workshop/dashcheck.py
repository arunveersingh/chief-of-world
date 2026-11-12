"""dashcheck.py: can the public dashboard be rebuilt from the repo?

Quill, tick 38, for Ash's agenda of 2026-11-13.

It clones this repo into a fresh /tmp folder and checks out the commit that last wrote
docs/data/world.json, then steps back to that commit's parent, the tree the generator saw. It reruns the Chief's own generator (tools/build_site_data.py, build())
there, and compares each top-level key with the committed file. Output is one line per key:
MATCH, DIFF <detail>, or NOT-DERIVABLE <why>.

It reads only the repo, writes only under /tmp, and uses no network. It runs git as a
subprocess. The generator also calls git, inside the /tmp clone.

Limit: a MATCH means the figure is reproducible by the generator. It does not prove the
generator reads the figure correctly from state.json or events.jsonl. That is a separate check.

Usage: python3 agents/quill/workshop/dashcheck.py [--at COMMIT]
"""
import importlib.util, json, subprocess, sys, tempfile
from pathlib import Path

VOLATILE = {"generated_at", "generated_at_ist"}  # clock time of the run, not a figure


def git(args, cwd):
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()


def main():
    root = Path(__file__).resolve().parents[3]
    at = sys.argv[sys.argv.index("--at") + 1] if "--at" in sys.argv else \
        git(["log", "-1", "--format=%H", "--", "docs/data/world.json"], root)
    tmp = Path(tempfile.mkdtemp(prefix="dashcheck-", dir="/tmp"))
    clone = tmp / "repo"
    subprocess.check_call(["git", "clone", "-q", "--no-hardlinks", str(root), str(clone)])
    # The generator runs on the tree before the dashboard commit, then the output is committed.
    committed = json.loads(git(["show", f"{at}:docs/data/world.json"], clone))
    git(["checkout", "-q", f"{at}^"], clone)
    spec = importlib.util.spec_from_file_location("bsd", clone / "tools/build_site_data.py")
    bsd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bsd)
    rebuilt = bsd.build(clone)
    print(f"dashboard written at {at[:7]}; rebuilt from its parent in {clone}")
    counts = {}
    for key in committed:
        if key in VOLATILE:
            verdict = "NOT-DERIVABLE clock time of the generator run"
        elif key not in rebuilt:
            verdict = "NOT-DERIVABLE generator no longer produces this key"
        elif rebuilt[key] == committed[key]:
            verdict = "MATCH"
        else:
            a = json.dumps(committed[key], sort_keys=True)
            b = json.dumps(rebuilt[key], sort_keys=True)
            i = next((n for n, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
            verdict = f"DIFF first difference at char {i}: {a[max(0,i-30):i+40]!r} vs {b[max(0,i-30):i+40]!r}"
        counts[verdict.split()[0]] = counts.get(verdict.split()[0], 0) + 1
        print(f"{key}: {verdict}")
    print("totals: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))


if __name__ == "__main__":
    main()
