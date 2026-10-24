"""Stage 10 prep for Fig. 2: report number within each wellbore, written to outputs/fig2_report_index.csv so the figure script reads only from outputs/.
report_number = rank among the wellbore's DDRs (every DDR counts, with or without a recorded depth; the 1980 sentinel record excluded), where the wellbore's first report with a
recorded depth (md not '-999.99' or '0') is 1. Table 6 counts reports the same way, but starts at the wellbore's first report of any kind (1 higher for the wellbores whose first report has no depth)."""
import pandas as pd

d = pd.read_parquet("data/interim/ddr.parquet")
d["day"] = pd.to_datetime(d.date_report.str[:10]); d["mdn"] = pd.to_numeric(d.md, errors="raise")
d = d[d.day.dt.year != 1980]
rows = []
for w, g in d.groupby("wellbore"):
    g = g.sort_values(["day", "filename"]).reset_index(drop=True)
    first = g.index[g.mdn > 0].min()
    g = g.loc[first:].copy(); g["report_number"] = range(1, len(g) + 1)
    rows.append(g[["filename", "wellbore", "report_number"]])
r = pd.concat(rows); r.to_csv("outputs/fig2_report_index.csv", index=False)
t = pd.read_csv("outputs/timeline.csv")
m = t.merge(r, on=["filename", "wellbore"], how="left", validate="one_to_one")
assert m.report_number.notna().all() and len(m) == 1421
print("rows", len(r), "timeline rows matched", len(m), "max report number", int(r.report_number.max()))
