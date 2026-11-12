"""sources.py: which dashboard keys come from files, which from git history, which from the clock?

Wry, tick 39, for Ash's agenda of 2026-11-13 (the second half Quill's dashcheck.py doesn't cover).

It makes two /tmp copies of the tree at COMMIT (default: HEAD):
  REAL  a full clone checked out at COMMIT
  FLAT  the same tree via `git archive`, committed once in a fresh repo, so every file is
        byte-identical but the history is one commit
It runs the Chief's tools/build_site_data.py build() on both, then on REAL again with the
clock moved forward one day. Each top-level key is labelled:
  FILES    same on REAL and FLAT, unmoved by the clock: rebuildable from the files alone
  HISTORY  differs between REAL and FLAT: needs git history, not just the files
  CLOCK    changes when only the clock moves
Read-only on the repo, writes only under /tmp, no network.

Usage: python3 agents/wry/workshop/sources.py [--at COMMIT]
"""
import importlib.util, json, subprocess, sys, tempfile
from datetime import timedelta
from pathlib import Path


def sh(args, cwd, **kw):
    return subprocess.check_output(args, cwd=cwd, text=True, **kw).strip()


def load(tree):
    spec = importlib.util.spec_from_file_location(f"bsd_{tree.name}", tree / "tools/build_site_data.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    root = Path(__file__).resolve().parents[3]
    at = sys.argv[sys.argv.index("--at") + 1] if "--at" in sys.argv else "HEAD"
    at = sh(["git", "rev-parse", at], root)
    tmp = Path(tempfile.mkdtemp(prefix="sources-", dir="/tmp"))
    real, flat = tmp / "real", tmp / "flat"
    subprocess.check_call(["git", "clone", "-q", "--no-hardlinks", str(root), str(real)])
    sh(["git", "checkout", "-q", at], real)
    flat.mkdir()
    subprocess.check_call(f"git -C {real} archive {at} | tar -x -C {flat}", shell=True)
    env = ["-c", "user.name=sources", "-c", "user.email=sources@example.invalid"]
    sh(["git", "init", "-q"], flat)
    sh(["git", "add", "-A"], flat)
    sh(["git", *env, "commit", "-qm", "flat copy"], flat)

    a_mod, f_mod = load(real), load(flat)
    a = a_mod.build(real)
    f = f_mod.build(flat)
    base = a_mod.now_ist()
    a_mod.now_ist = lambda: base + timedelta(days=1)
    c = a_mod.build(real)

    print(f"tree {at[:7]}; REAL = full history, FLAT = same files, one commit")
    counts = {}
    for key in a:
        labels = []
        if a[key] != f.get(key):
            labels.append("HISTORY")
        if a[key] != c.get(key):
            labels.append("CLOCK")
        label = "+".join(labels) or "FILES"
        counts[label] = counts.get(label, 0) + 1
        print(f"{key}: {label}")
    print("totals: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))


if __name__ == "__main__":
    main()
