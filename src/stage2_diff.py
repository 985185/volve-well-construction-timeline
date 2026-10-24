"""Stage 2b: summary counts and row-by-row diff of the new extraction against the old volve_ddr_master (join on filename)."""
import os, sys
if not os.path.exists("data/interim/old/volve_ddr_master.parquet"):
    print("SKIPPED (optional verification step): data/interim/old/volve_ddr_master.parquet is not available, so the comparison with the earlier extraction cannot run. No reported number depends on running this step; its committed result is reports/STAGE_2.md.")
    sys.exit(0)
import pandas as pd

new = pd.read_parquet("data/interim/ddr.parquet")
old = pd.read_parquet("data/interim/old/volve_ddr_master.parquet")
print("rows new/old:", len(new), len(old), "| filenames only new:", len(set(new.filename) - set(old.filename)), "only old:", len(set(old.filename) - set(new.filename)))
print("dup filenames new/old:", new.filename.duplicated().sum(), old.filename.duplicated().sum())
print("wellbores:", new.wellbore.nunique(), "wells:", new.well.nunique())
d = new.groupby(["wellbore", new.date_report.str[:10]]).size()
print("duplicate wellbore/date pairs:", (d > 1).sum(), "extra rows:", (d[d > 1] - 1).sum())
print("distinct date_report:", new.date_report.nunique(), "null date_report:", new.date_report.isna().sum())
print(new.groupby("well").wellbore.nunique().rename("n_wellbores").to_string())

M = {"well": "well", "wellbore": "wellbore", "date_report": "date_report", "dTimSpud": "spud_date", "md": "md_m",
     "md_kickoff": "md_kickoff_m", "md_csg_last": "md_csg_last_m", "rig": "rig", "operator": "operator",
     "forecast24hr": "forecast24hr", "drill_complete": "drill_complete", "sum24Hr": "sum24hr", "report_no": "report_no"}
m = new.merge(old, on="filename", suffixes=("_n", "_o"))
print("joined:", len(m))
tot = 0
for nc, oc in M.items():
    a = m[nc + "_n" if nc == oc else nc]; b = m[oc + "_o" if nc == oc else oc]
    same = (a == b) | (a.isna() & b.isna())
    nd = int((~same.fillna(False)).sum()); tot += nd
    print(f"{nc:15s} vs {oc:15s} differing rows: {nd}")
    if nd:
        x = m.loc[~same.fillna(False), ["filename"]].assign(new=a[~same.fillna(False)], old=b[~same.fillna(False)])
        x["kind"] = [("new null/old 'None'" if (n is pd.NA and o == "None") else "new null/old other" if n is pd.NA else "old null" if o is pd.NA else "value") for n, o in zip(x.new, x.old)]
        print("   kinds:", x.kind.value_counts().to_dict())
        print(x.head(6).to_string(max_colwidth=70))
        x.to_csv(f"data/interim/old/diff_{nc}.csv", index=False)
print("total differing cells:", tot)
