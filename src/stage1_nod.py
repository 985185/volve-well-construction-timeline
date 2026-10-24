"""Stage 1c: record NOD snapshot metadata, compare the Volve subset with the 2026-09-08 snapshot, append hashes to manifest."""
import csv, hashlib, io, json, re, sys

DATE = "20261024"
FILES = {"development": f"data/raw/nod/wellbore_development_all_{DATE}.csv",
         "exploration": f"data/raw/nod/wellbore_exploration_all_{DATE}.csv"}
OLD = {"development": "inputs/repo_before/data/nod_volve_reference_development.csv",
       "exploration": "inputs/repo_before/data/nod_volve_reference_exploration.csv"}
pat = re.compile(r"15/9-F-|15/9-19")
meta = {"retrieval_date": "2026-10-24", "files": {}}
for k, p in FILES.items():
    raw = open(p, "rb").read()
    rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline="")))
    sub = [r for r in rows if pat.search(r["wlbWellboreName"])]
    old = list(csv.DictReader(open(OLD[k], encoding="utf-8-sig", newline="")))
    key = lambda r: tuple(sorted(r.items()))
    oldset, newset = {r["wlbWellboreName"]: r for r in old}, {r["wlbWellboreName"]: r for r in sub}
    changed = [n for n in oldset if n in newset and oldset[n] != newset[n]]
    meta["files"][k] = {"path": p, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "total_rows": len(rows),
                        "volve_subset_rows": len(sub), "sept_subset_rows": len(old),
                        "only_in_new": sorted(set(newset) - set(oldset)), "only_in_sept": sorted(set(oldset) - set(newset)),
                        "rows_changed_vs_sept": changed}
    print(k, len(rows), "subset", len(sub), "sept", len(old), "new-only", meta["files"][k]["only_in_new"], "sept-only", meta["files"][k]["only_in_sept"], "changed", len(changed))
    for n in changed:
        print("  CHANGED", n, {c: (oldset[n][c], newset[n][c]) for c in oldset[n] if oldset[n][c] != newset[n].get(c)})
json.dump(meta, open("data/raw/nod/nod_snapshot_20261024_metadata.json", "w"), indent=1)
with open("data/raw/manifest.csv", "a", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    for k, v in meta["files"].items(): w.writerow([v["path"], v["sha256"], v["bytes"]])
