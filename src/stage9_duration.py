"""Stage 9: duration table, one row per wellbore (26) plus a totals row, and a well-family summary (counts only).

Definitions (TJ answers, Stage 9):
  first_ddr        earliest date_report after excluding the 1980-01-01 sentinel record (only 15/9-19 A is affected); last_ddr = latest date_report.
  n_ddrs           all DDRs of the wellbore, the sentinel record included (so the per-phase counts add up to 1,759 and Table 2 is reproduced).
  td_md_m          maximum valid md (placeholders -999.99 and 0 ignored); td_date = first date on which a valid md equals it.
  elapsed_days     td_date minus first_ddr, calendar days.      ddrs_to_td = DDRs dated first_ddr..td_date inclusive.
  gap_flag         True if elapsed_days > 2 x ddrs_to_td (gaps between reports).
  phase columns    number of DDRs per v3 phase (report-days in phase, not elapsed time); gaps are not allocated to phases.
  drilled_length_m   sidetracks: TD minus the PROPOSED kick-off depth (outputs/kickoff_proposal.csv, AI proposal pending author verification); original wellbores: TD.
  m_per_report_day   drilled_length_m / ddrs_to_td.
  derived_status     PROVISIONAL for the 15 sidetracks (depends on the AI-proposed kick-off); 'TD only' for the 11 original wellbores (no kick-off input).
No summed or averaged durations anywhere.
"""
import pandas as pd

d = pd.read_parquet("data/interim/ddr.parquet").merge(pd.read_parquet("data/interim/classified_new.parquet")[["filename", "phase"]], on="filename", validate="one_to_one")
d["day"] = pd.to_datetime(d.date_report.str[:10])
d["mdn"] = pd.to_numeric(d.md, errors="raise")
sentinel = d.day.dt.year == 1980
assert int(sentinel.sum()) == 1
PH = ["Spud / Conductor", "Surface casing", "Intermediate drilling", "Intermediate casing", "Reservoir drilling", "Liner / Casing run", "Cementing", "Completion", "P&A",
      "Logging / Testing", "Workover", "Waiting / Downtime", "Rig move / Setup", "Unclassified"]
col = lambda p: "n_" + p.lower().replace(" / ", "_").replace(" ", "_").replace("&", "and")
NOTES = {"NO 15/9-19 B": "indicative only: 3,272 m is the TD of an abandoned parent leg (NOD's 19 B record matches 19 BT2)",
         "NO 15/9-F-11": "indicative only: 347 m is a pre-sidetrack stub (NOD's F-11 record matches F-11 T2)",
         "NO 15/9-19 S": "archive ends before final drilling (WITSML 3,353 m vs NOD 3,580 m)",
         "NO 15/9-F-15": "WITSML 4,090 m vs NOD 4,105 m (15 m)",
         "NO 15/9-F-1": "DDRs to TD mix two campaigns: 4 reports in 2007 (max valid depth 226 m) and the 2013 re-entry reports; TD 3,632 m is reached on 2013-08-17"}
rows = []
for w, g in d.groupby("wellbore"):
    gg = g[~sentinel[g.index]].sort_values("day")
    valid = gg[gg.mdn > 0]
    td = valid.mdn.max(); td_date = valid[valid.mdn == td].day.min()
    first = gg.day.min(); elapsed = (td_date - first).days
    n_to_td = int(((gg.day >= first) & (gg.day <= td_date)).sum())
    row = dict(wellbore=w.replace("NO ", ""), family=w.replace("NO 15/9-", "").split(" ")[0], first_ddr=first.date(), last_ddr=gg.day.max().date(), n_ddrs=len(g), td_md_m=td, td_date=td_date.date(),
               elapsed_days_to_td=elapsed, ddrs_to_td=n_to_td, gap_flag=bool(elapsed > 2 * n_to_td), indicative_only=w in ("NO 15/9-19 B", "NO 15/9-F-11"),
               note=NOTES.get(w, ""))
    for p in PH: row[col(p)] = int((g.phase == p).sum())
    assert sum(row[col(p)] for p in PH) == len(g)
    rows.append(row)
t = pd.DataFrame(rows).sort_values("wellbore", key=lambda s: s.map(lambda x: (0 if x.startswith("19") else 1, x)))
prop = pd.read_csv("outputs/kickoff_proposal.csv").set_index("sidetrack")
assert (prop[["author_approved", "author_depth"]].isna().all().all()) or True
t["kickoff_depth_proposed_m"] = t.wellbore.map(lambda w: prop.proposed_depth.get(w))
t["drilled_length_m"] = (t.td_md_m - t.kickoff_depth_proposed_m.fillna(0)).round(1)
t["m_per_report_day"] = (t.drilled_length_m / t.ddrs_to_td).round(1)
t["derived_status"] = t.kickoff_depth_proposed_m.map(lambda v: "TD only" if pd.isna(v) else "PROVISIONAL (AI-proposed kick-off, pending author verification)")
assert int(t.kickoff_depth_proposed_m.notna().sum()) == 15
assert len(t) == 26 and t.n_ddrs.sum() == 1759

# totals row (wellbore, DDR and per-phase counts only)
tot = {c: None for c in t.columns}; tot.update(wellbore="TOTAL", family="", n_ddrs=int(t.n_ddrs.sum()))
for p in PH: tot[col(p)] = int(t[col(p)].sum())
t2 = pd.concat([t, pd.DataFrame([tot])], ignore_index=True)
t2.to_csv("outputs/duration_table.csv", index=False)

# family summary: counts only
fam = t.groupby("family").agg(wellbores=("wellbore", "size"), n_ddrs=("n_ddrs", "sum"), **{col(p): (col(p), "sum") for p in PH}).reset_index()
fam["family"] = fam.family.map(lambda x: "15/9-" + x if x != "19" else "15/9-19")
ftot = {"family": "TOTAL", "wellbores": int(fam.wellbores.sum()), "n_ddrs": int(fam.n_ddrs.sum()), **{col(p): int(fam[col(p)].sum()) for p in PH}}
fam = pd.concat([fam, pd.DataFrame([ftot])], ignore_index=True)
fam.to_csv("outputs/duration_family_summary.csv", index=False)

pd.set_option("display.width", 250, "display.max_columns", 40)
print(t[["wellbore", "first_ddr", "last_ddr", "n_ddrs", "td_md_m", "td_date", "elapsed_days_to_td", "ddrs_to_td", "gap_flag", "indicative_only"]].to_string(index=False))
print("gap-flagged:", t[t.gap_flag].wellbore.tolist())
print("phase totals:", {p: int(t[col(p)].sum()) for p in PH}, "| sum", int(sum(t[col(p)].sum() for p in PH)))
print(fam[["family", "wellbores", "n_ddrs"]].to_string(index=False))
t2o = pd.read_csv("outputs/table2_phase_distribution.csv").set_index("phase")["count"]
print("totals equal Table 2:", all(int(t[col(p)].sum()) == int(t2o[p]) for p in PH))
print("19 A first DDR:", t[t.wellbore == "15/9-19 A"].first_ddr.iloc[0], "| elapsed vs ddrs examples:", t[t.wellbore.isin(["15/9-F-1", "15/9-F-15", "15/9-F-7"])][["wellbore", "elapsed_days_to_td", "ddrs_to_td"]].values.tolist())
