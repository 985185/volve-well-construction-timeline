"""Stage 6a2 (optional, author side): build the published adjudication file outputs/audit_adjudications.csv from the original adjudications
(inputs/old_audit/audit_adjudicated.csv) and the wellbore + date to filename map of the original 50 (data/interim/audit_old50_filename_map.csv, written by stage6_prepare.py
when the original sample is available). Not needed to reproduce any number: stage6_estimates.py reads the committed output."""
import os
import sys
if not os.path.exists("data/interim/audit_old50_filename_map.csv"):
    print("SKIPPED (optional step): the filename map of the original 50 is not available; outputs/audit_adjudications.csv is committed and is the input of stage6_estimates.py.")
    sys.exit(0)
import pandas as pd

adj = pd.read_csv("inputs/old_audit/audit_adjudicated.csv")
adj["day"] = adj.date_report.str[:10]
mp = pd.read_csv("data/interim/audit_old50_filename_map.csv")
a = adj.merge(mp[["filename", "wellbore", "day"]], on=["wellbore", "day"], how="left", validate="one_to_one")
assert a.filename.notna().all() and len(a) == 50
a["call"] = a.adjudication
a["miss_reason"] = a.miss_reason_if_construction.fillna("").str.split(":").str[0].str.strip()
pub = a[["filename", "wellbore", "day", "stratum", "call", "miss_reason"]].rename(columns={"day": "date"}).sort_values("filename")
pub.to_csv("outputs/audit_adjudications.csv", index=False)
print("wrote outputs/audit_adjudications.csv", len(pub))
