"""Stage 5: timeline dataset. Exclude depth placeholders (-999.99 and 0), cast md to float, add days from the wellbore's first retained DDR."""
import pandas as pd

d = pd.read_parquet("data/interim/ddr.parquet")
ph = pd.read_parquet("data/interim/classified_new.parquet")[["filename", "phase"]]
d = d.merge(ph, on="filename", validate="one_to_one")
d["md_m"] = pd.to_numeric(d["md"], errors="raise")
n0 = len(d)
sent = d["md"].str.strip() == "-999.99"
zero = (d["md_m"] == 0) & ~sent
print(f"{n0} DDRs - {int(sent.sum())} sentinel - {int(zero.sum())} zero = {n0 - int(sent.sum()) - int(zero.sum())}")
t = d[~sent & ~zero & d.md_m.notna()].copy()
t["date"] = pd.to_datetime(t["date_report"].str[:10])
t["days_from_first_ddr"] = (t["date"] - t.groupby("wellbore")["date"].transform("min")).dt.days
t = t.sort_values(["wellbore", "date", "filename"])
out = t[["wellbore", "date_report", "days_from_first_ddr", "md_m", "phase", "filename"]].rename(columns={"date_report": "date"})
out.to_csv("outputs/timeline.csv", index=False)
print("rows", len(out), "wellbores", out.wellbore.nunique(), "| min md", out.md_m.min(), "max md", out.md_m.max())
print(out.groupby("wellbore").agg(rows=("md_m", "size"), max_md=("md_m", "max"), span_days=("days_from_first_ddr", "max")).to_string())
print(out.phase.value_counts().to_string())

# comparison with the v2 dataset (inputs/repo_before/data/volve_timeline_dataset.csv), row by row on filename
o = pd.read_csv("inputs/repo_before/data/volve_timeline_dataset.csv")
m = out.merge(o, on="filename", how="outer", suffixes=("", "_v2"), indicator=True)
print("\nonly new:", int((m._merge == "left_only").sum()), "only v2:", int((m._merge == "right_only").sum()))
b = m[m._merge == "both"]
for c in ["wellbore", "days_from_first_ddr", "md_m", "phase"]:
    print(f"{c}: differing rows {int((b[c] != b[c + '_v2']).sum())}")
print("date: differing rows", int((b["date"] != b["date_report"]).sum()))
