"""Stage 8c: build reports/STAGE_8c.md (AI kick-off proposal and the F-1 2007 versus 2013 check) from outputs/kickoff_proposal.csv and the DDR data."""
import pandas as pd

x = pd.read_csv("outputs/kickoff_proposal.csv")
f = lambda v: "" if pd.isna(v) else (f"{v:,.1f}" if float(v) % 1 else f"{v:,.0f}")
rows = [f"| {r.sidetrack} | {f(r.ddr_kickoff_depth_m)} | {r.proposed_approved} | {f(r.proposed_depth)} | {r.proposed_reason} |" for r in x.itertuples()]
diff = x[x.proposed_approved == "N"]

d = pd.read_parquet("data/interim/ddr.parquet")
d["day"] = pd.to_datetime(d.date_report.str[:10]); d["mdn"] = pd.to_numeric(d.md)
g1 = d[(d.wellbore == "NO 15/9-F-1")]
a, b = g1[g1.day.dt.year == 2007], g1[g1.day.dt.year == 2013]
va, vb = a[a.mdn > 0], b[b.mdn > 0]
f1 = (f"| 2007 reports | {len(a)} | {a.day.min().date()} to {a.day.max().date()} | {len(va)} | {va.mdn.max():,.0f} m on {va[va.mdn == va.mdn.max()].day.min().date()} |\n"
      f"| 2013 reports | {len(b)} | {b.day.min().date()} to {b.day.max().date()} | {len(vb)} | {vb.mdn.max():,.0f} m on {vb[vb.mdn == vb.mdn.max()].day.min().date()} |")
gap = (b.day.min() - a.day.max()).days

txt = f"""# Stage 8c: AI proposal for the kick-off sign-off, and the F-1 check

Date: 2026-10-24. Branch: `rerun-2026-10`. Scripts: `src/stage8c_proposal.py`, `src/stage8c_report.py`. Outputs: `outputs/kickoff_signoff.xlsx` (proposal columns added), `outputs/kickoff_proposal.csv`.

**These depths are AI-PROPOSED, pending author verification.** `proposed_by` = AI in every row. The columns `author_approved`, `author_depth` and `author_note` are TJ's and are empty (0 cells filled; the script refuses to run if any is filled). Everything derived from the proposed depths is PROVISIONAL until those columns are filled. If TJ accepts the proposals unchanged, the manuscript's AI disclosure must say that the kick-off depths were proposed by an AI tool and verified by the author (decision 37).

## Rule used (TJ decision 32), applied strictly

"The depth at which the narrative first reports new formation or departure from the parent hole; where none is stated, the depth at which the kick-off or window is started; where the narrative is empty, the measured depth at the parent-to-child transition." For windows I read the hole as leaving the parent casing at the window bottom (with new formation drilled below), so the window bottom is the stated departure depth and the window top is the fallback when no departure depth is stated. This reading is the one judgement that changes two rows (19 A and F-9 A).

## Proposal (15 rows; Y = proposal equals the current table, N = it does not)

| Sidetrack | Current table (m) | Proposed approved | Proposed depth (m) | Reason |
|---|---|---|---|---|
{chr(10).join(rows)}

## Rows where the proposal differs from the current table (3)

{chr(10).join(f"- {r.sidetrack}: {f(r.ddr_kickoff_depth_m)} m to {f(r.proposed_depth)} m." for r in diff.itertuples())}

The five rows you asked about: F-1 C stays at 1,364 m (Y; 1,355 m is the second-tier fallback and is not used because the first tier is met); F-11 T2 stays at 246 m (Y); F-11 B changes to 2,531 m (N; the 2,531 to 2,589 m interval gives no point value under the first tier); 19 ST2 stays at 1,536 m (Y, depth only, third tier); 19 B stays at 2,231 m (Y; NOD's 2,200 m is not an input to the rule, and the only 2200 in the 19 A and 19 B reports is a clock time, "AT 2200 HRS").

## Check and report only: 15/9-F-1 reports of 2007 versus 2013

| Group | DDRs | Date range | DDRs with a valid depth | Maximum valid depth |
|---|---|---|---|---|
{f1}

The two groups are {gap:,} days apart (the largest gap in F-1's record). All of F-1's depth beyond 226 m, including its 3,632 m TD (NOD 3,632 m, completion 21.08.2013), is in the 2013 reports. No interpretation is made here.

## Next

TJ fills the author columns. Stage 12 must not finalise kick-off numbers until then.
"""
open("reports/STAGE_8c.md", "w", encoding="utf-8").write(txt)
print(len(txt), "|", f1.replace(chr(10), " // "), "| gap", gap)
