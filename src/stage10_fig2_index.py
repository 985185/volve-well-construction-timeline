"""Stage 10 prep for Fig. 2: report number within each wellbore, written to outputs/fig2_report_index.csv so the figure script reads only from outputs/.
report_number = rank among the wellbore's DDRs counted from its first report of any kind (1 = first report; every DDR counts, with or without a recorded depth; the 1980 sentinel record
excluded). This is the counting basis of Table 6 (reports to TD = report number of the TD report)."""
import pandas as pd

d = pd.read_parquet("data/interim/ddr.parquet")
d["day"] = pd.to_datetime(d.date_report.str[:10]); d["mdn"] = pd.to_numeric(d.md, errors="raise")
d = d[d.day.dt.year != 1980]
rows = []
for w, g in d.groupby("wellbore"):
    g = g.sort_values(["day", "filename"]).reset_index(drop=True)
    g = g.copy(); g["report_number"] = range(1, len(g) + 1)
    rows.append(g[["filename", "wellbore", "report_number"]])
r = pd.concat(rows); r.to_csv("outputs/fig2_report_index.csv", index=False)
t = pd.read_csv("outputs/timeline.csv")
m = t.merge(r, on=["filename", "wellbore"], how="left", validate="one_to_one")
assert m.report_number.notna().all() and len(m) == 1421
du = pd.read_csv("outputs/duration_table.csv").dropna(subset=["td_md_m"])               # check against Table 6: reports to TD = report number of the first report at TD date
for x in du.itertuples():
    g = m[(m.wellbore == "NO " + x.wellbore) & (m.date.str[:10] == str(x.td_date))].report_number.min()
    assert g == x.ddrs_to_td, (x.wellbore, g, x.ddrs_to_td)
print("rows", len(r), "timeline rows matched", len(m), "max report number", int(r.report_number.max()))
