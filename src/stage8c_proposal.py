"""Stage 8c: AI PROPOSAL for the kick-off sign-off (TJ instruction). Adds proposed_by / proposed_approved / proposed_depth / proposed_reason to outputs/kickoff_signoff.xlsx.
The author columns (author_approved, author_depth, author_note) are TJ's and are left empty; this script refuses to run if any of them has been filled.

Uniform rule applied strictly (TJ decision 32): the depth at which the narrative first reports new formation or departure from the parent hole; where none is stated, the depth
at which the kick-off or window is started; where the narrative is empty, the measured depth at the parent-to-child transition.
Rule added by TJ (decision 40): for casing exits (milled windows), kick-off = top of window. (An earlier AI reading used the window bottom; TJ rejected it and the proposals for 19 A, F-9 A and F-11 B now equal the table.)
"""
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

path = "outputs/kickoff_signoff.xlsx"
old = pd.read_excel(path, sheet_name="signoff")
assert old[["author_approved", "author_depth", "author_note"]].notna().sum().sum() == 0, "author columns are filled: refusing to overwrite TJ's review"
t = pd.read_csv("outputs/kickoff_table.csv")

# sidetrack: (proposed_approved, proposed_depth, proposed_reason)
P = {
    "15/9-19 A": ("Y", 2178, "Casing exit by a milled window: under the rule as ruled by TJ (decision 40) the kick-off is the top of the window, 2,178 m (window milled 2178-2183 m on 1997-07-29; an earlier window at 2,202-2,207 m was abandoned). NOD and the structured mdKickoff also say 2,178 m."),
    "15/9-19 B": ("Y", 2231, "The report states the kick-off depth directly: 'DRESS CMT AND PERFORMED KICK OFF FROM 2231M TO 2277M'. NOD's 2,200 m is not an input to the rule; the only '2200' in the 19 A and 19 B reports is a clock time ('AT 2200 HRS')."),
    "15/9-19 BT2": ("Y", 2911, "The parent's last report states departure with a depth: 'COMMENCED DRILLING 8 1/2\" HOLE FROM 2911 M AT 15/9-19BT2' (after cement drilled to 2911 m), and the first BT2 report starts at the same depth. Tier 1."),
    "15/9-19 ST2": ("Y", 1536, "Both 1992-12-19 narratives (parent last, sidetrack first) read 'None', so the third tier applies: measured depth at the transition, 1,536 m on both reports. Depth only, no text support; the parent had drilled cement to 1,486 m the day before, so the true departure could be shallower."),
    "15/9-F-1 A": ("Y", 2620, "The parent's last report says 'Commenced kick off to F-1A' without a depth and its md is 2620 m, so tier 2, event in text with depth from md. NOD agrees at 2,620 m."),
    "15/9-F-1 B": ("Y", 2617, "The parent's last report says 'Drilled out cement and kicked off well to F-1 B' and its md is 2617 m (2,545 m the day before), so tier 2, event in text with depth from md; the md is the day's deepest point, so the kick-off may be a little shallower (NOD 2,604 m)."),
    "15/9-F-1 C": ("Y", 1364, "Tier 1: the F-1 B report of 2014-02-22 states '50% formation obtained at 1364 m', the first report of new formation, and F-1 C's first report drills from 1,364 m. 1,355 m is only where time drilling started, the fallback used when no formation depth is stated. NOD agrees at 1,364 m."),
    "15/9-F-9 A": ("Y", 421.5, "Casing exit by a milled window: kick-off = top of window, 421.5 m ('Milled 12-1/4\" sidetrack window from 421,5 m (top) to 424 m'); the window bottom, 428.2 m, is not used (TJ ruling, decision 40). NOD gives 428 m."),
    "15/9-F-11 T2": ("Y", 246, "No formation or departure depth is stated, so tier 2: the 2013-03-23 report says oriented drilling out of the cement started at 246 m (top of cement 244 m). 257 m is where the sidetrack was handed over the next day. NOD has no separate record."),
    "15/9-F-11 A": ("Y", 2586, "Tier 1: 'Drilled cement and kicked off to F-11 A at 2586m MD' states the departure depth. NOD 2,578 m."),
    "15/9-F-11 B": ("Y", 2589, "LOW confidence. 'Drilled cement and new formation from 2531 m MD to 2589 m MD' reports new formation by the end of the interval, so departure is confirmed at 2,589 m, consistent with F-1 C (formation first reported); the interval start, 2,531 m, is not used (TJ ruling, decision 40). NOD gives 2,586 m, inside the interval."),
    "15/9-F-15 A": ("Y", 1381, "'Drilled cement/new formation from 1368 m to 1381 m MD. Initiated kick off of F-15.' puts the start of the kick-off at the end of the interval, 1,381 m, where the sidetrack's first report also starts. NOD agrees at 1,381 m."),
    "15/9-F-15 B": ("Y", 3185, "Tier 1: 'kicked off at 3185m' states the departure depth; the '50/50 cement/formation' remark relates to 3,210 m, drilled afterwards. NOD agrees at 3,185 m."),
    "15/9-F-15 C": ("Y", 2566, "Tier 2: cement was drilled from 2,490 to 2,566 m, then 'Initiated kick off', and no formation or departure depth is stated; 2,575 m (the NOD value) is only where the section had reached by the end of the day."),
    "15/9-F-15 D": ("Y", 1380, "The sidetrack's first report says 'Drilled cement and kicked off' without a depth, so tier 2 with depth from md: the parent's last report (kick-off plug set the day before) has md 1,380 m. NOD agrees at 1,380 m."),
}
assert set(P) == set(t.sidetrack) and len(P) == 15
for s, (a, dep, why) in P.items():
    assert (a == "Y") == (float(dep) == float(t.set_index("sidetrack").loc[s, "ddr_kickoff_depth_m"])), s     # Y exactly when the proposal equals the current table

x = old.copy()
x["proposed_by"] = "AI"
x["proposed_approved"] = x.sidetrack.map(lambda s: P[s][0])
x["proposed_depth"] = x.sidetrack.map(lambda s: P[s][1])
x["proposed_reason"] = x.sidetrack.map(lambda s: P[s][2])
order = [c for c in old.columns if not c.startswith("author_")] + ["proposed_by", "proposed_approved", "proposed_depth", "proposed_reason", "author_approved", "author_depth", "author_note"]
x = x[order]
x.to_csv("outputs/kickoff_proposal.csv", index=False)

wb = Workbook(); ws = wb.active; ws.title = "signoff"
ws.append(order)
for r in x.itertuples(index=False):
    ws.append([None if (isinstance(v, float) and pd.isna(v)) else (int(v) if isinstance(v, float) and v.is_integer() else v) for v in r])
for c in ws[1]:
    c.font = Font(bold=True); c.fill = PatternFill("solid", fgColor="DDDDDD")
widths = {"sidetrack": 14, "parent": 24, "ddr_kickoff_depth_m": 12, "evidence_quote": 56, "evidence_report": 26, "method": 28, "rule_tier": 8, "confidence": 11, "nod_wlbKickOffPoint_m": 12,
          "nod_minus_ddr_m": 11, "v2_depth_m": 10, "alternative_depths": 34, "note": 40, "proposed_by": 10, "proposed_approved": 11, "proposed_depth": 11, "proposed_reason": 80,
          "author_approved": 12, "author_depth": 12, "author_note": 40}
for i, c in enumerate(order, 1):
    ws.column_dimensions[ws.cell(1, i).column_letter].width = widths[c]
col = {c: ws.cell(1, i).column_letter for i, c in enumerate(order, 1)}
for row in ws.iter_rows(min_row=2):
    for c in row: c.alignment = Alignment(wrap_text=True, vertical="top")
    for i, c in enumerate(row):
        if order[i].startswith("proposed_"): c.fill = PatternFill("solid", fgColor="E6F0FA")
        if order[i].startswith("author_"): c.fill = PatternFill("solid", fgColor="FFF9D6")
dv = DataValidation(type="list", formula1='"Y,N"', allow_blank=True); ws.add_data_validation(dv)
dv.add(f"{col['author_approved']}2:{col['author_approved']}16"); dv.add(f"{col['proposed_approved']}2:{col['proposed_approved']}16")
ws.freeze_panes = "C2"
info = wb.create_sheet("info")
for line in ["Kick-off sign-off, 15 sidetracks. Blue columns = AI PROPOSAL (proposed_by = AI); yellow columns = author (TJ), empty until TJ fills them. The manuscript will use only author-approved depths.",
             "Rule: the depth at which the narrative first reports new formation or departure from the parent hole; where none is stated, the depth at which the kick-off or window is started; where the narrative is empty, the measured depth at the parent-to-child transition.",
             "proposed_approved = Y where the proposal equals the current ddr_kickoff_depth_m; N where the evidence or rule does not support the current value, with proposed_depth.",
             "Everything derived from the proposed depths (drilled_length_m, m_per_report_day) is PROVISIONAL until the author columns are filled.",
             "Quotes are 15 words or fewer. NOD = wlbKickOffPoint, snapshot 2026-10-24. Depths in m MD."]:
    info.append([line])
info.column_dimensions["A"].width = 150
wb.save(path)

chk = pd.read_excel(path, sheet_name="signoff")
print(chk.shape, "author cells filled:", int(chk[["author_approved", "author_depth", "author_note"]].notna().sum().sum()), "| proposed_by:", chk.proposed_by.unique().tolist())
print(chk[["sidetrack", "ddr_kickoff_depth_m", "proposed_approved", "proposed_depth"]].to_string(index=False))
print("rows where the proposal differs from the current table:", chk[chk.proposed_approved == "N"].sidetrack.tolist())
