"""External review evidence (November 2026): values read from the DDR narratives and checked by pattern search; each value is asserted against the report that states it.
Reads data/interim/ddr.parquet and outputs/td_validation.csv; writes outputs/review_evidence.json (numbers and file names only, no narrative text)."""
import json
import re
import pandas as pd

d = pd.read_parquet("data/interim/ddr.parquet")
d["day"] = d.date_report.str[:10]
d["t"] = d.sum24Hr.fillna("").str.replace("½", " 1/2").str.replace("¼", " 1/4").str.replace("¾", " 3/4").str.replace(r"\s+", " ", regex=True)


def rep(wb, day):
    r = d[(d.wellbore == wb) & (d.day == day)]; assert len(r) == 1, (wb, day); return r.iloc[0]


def has(wb, day, pat):
    r = rep(wb, day); assert re.search(pat, r.t, re.I), (wb, day, pat); return r.filename


E = {}
# --- 15/9-F-15 total depth: the reports state 4,090 m; no F-15 report states 4,105 m
f15 = d[d.wellbore == "NO 15/9-F-15"]
E["f15_td_stated_m"] = 4090; E["f15_td_report"] = has("NO 15/9-F-15", "2008-11-28", r"4090 ?m ?\(TD\)")
has("NO 15/9-F-15", "2008-11-28", r"from 3889m to 4090m"); E["f15_td_report_drilled_from_m"] = 3889
E["f15_reports_mentioning_4105"] = int((f15.t + " " + f15.forecast24hr.fillna("")).str.contains(r"4[ ,.]?105").sum()); assert E["f15_reports_mentioning_4105"] == 0
nod = pd.concat([pd.read_csv(f"data/nod/wellbore_{k}_all_20261024.csv", encoding="utf-8-sig", dtype=str) for k in ("development", "exploration")]).set_index("wlbWellboreName")
E["f15_nod_td_m"] = float(nod.loc["15/9-F-15", "wlbTotalDepth"]); assert E["f15_nod_td_m"] == 4105.0
# --- 15/9-19 S: stuck pipe, cutter, cut, cement plugs, cement drilled out, transition
S = "NO 15/9-19 S"
E["s19_packed_off_m"] = 2732; has(S, "1992-12-10", r"PACKED OFF AT 2732 M, WORKED PIPE DOWN TO 2741 M")
E["s19_pipe_worked_to_m"] = 2741; has(S, "1992-12-11", r"WORK PIPE FREE AT 2741 M")
E["s19_cutter_detonated_m"] = 2658; has(S, "1992-12-12", r"DETONATED AT 2658M")
E["s19_pipe_cut_m"] = 2516; has(S, "1992-12-13", r"CUT PIPE AT 2516M")
E["s19_backoff_mentions"] = int(d[d.wellbore.isin([S, "NO 15/9-19 ST2"])].t.str.contains(r"back(?:ed)?[\s-]?off|backoff", case=False, regex=True).sum()); assert E["s19_backoff_mentions"] == 0
has(S, "1992-12-15", r"CEMENT PLUG FROM 2180 TO 1980 M AND FROM 1850 TO 1550M"); has(S, "1992-12-16", r"3\.RD CMT PLUG FROM 1543M TO 1430M")
E["s19_cement_plugs_m"] = [[2180, 1980], [1850, 1550], [1543, 1430]]
E["st2_lower_bound_report"] = has(S, "1992-12-18", r"DRILLED CEMENT TO 1486M"); E["st2_lower_bound_report_date"] = "1992-12-18"; E["st2_cement_drilled_out_m"] = 1486
for wb in (S, "NO 15/9-19 ST2"):
    r = rep(wb, "1992-12-19"); assert r.sum24Hr.strip() == "None" and float(r.md) == 1536
E["st2_md_at_transition_m"] = 1536
# --- 15/9-19 B: stuck, backoff attempt, cut, sidetrack plug, new hole
B = "NO 15/9-19 B"
has(B, "1997-11-29", r"BACKED OFF DP TOO HIGH"); E["b19_backoff_attempt_too_high"] = True
has(B, "1997-11-30", r"CUT DRILL STRING AT 3164M"); E["b19_string_cut_m"] = 3164
has(B, "1997-12-04", r"SIDETRACK PLUG FROM 2983 - 2835 M"); E["b19_sidetrack_plug_m"] = [2983, 2835]
E["b19_stuck_at_m"] = 3272; has(B, "1997-11-28", r"DRILLED 8 1/2\" HOLE FROM 3212M TO 3272M")
# --- casing sizes: 14 in. and 10 3/4 in. in the narratives (any spelling)
p14 = re.compile(r"(?<![\d./,-])14\s*(?:\"|''|”|-?\s?in\b|-?\s?inch)", re.I)
p1034 = re.compile(r"(?<![\d./,])10[\s\-]*3\s*/\s*4|(?<![\d])10[.,]75", re.I)
for k, p in (("14in", p14), ("10_3_4in", p1034)):
    m = d[d.t.apply(lambda s: bool(p.search(s)))]
    E[f"casing_{k}_ddrs"] = len(m); E[f"casing_{k}_wellbores"] = sorted(m.wellbore.str.replace("NO ", "").unique())
comb = re.compile(r"9[\s-]*5/8\s*(?:\"|in|'')?\s*[xX]\s*10[\s-]*3/4|10[\s-]*3/4\s*(?:\"|in|'')?\s*[xX]\s*9[\s-]*5/8"); tb = re.compile(r"tie[\s-]?back", re.I)
m = d[d.t.apply(lambda s: bool(p1034.search(s)))]
E["casing_10_3_4in_with_tieback_or_9_5_8_combination_ddrs"] = int(m.t.apply(lambda s: bool(comb.search(s)) or bool(tb.search(s))).sum()); assert E["casing_10_3_4in_with_tieback_or_9_5_8_combination_ddrs"] > E["casing_10_3_4in_ddrs"] / 2
# --- Hugin Formation: 15/9-F-4 pressure samples in the 8 1/2 in. section; end of its 12 1/4 in. section
F4 = "NO 15/9-F-4"
has(F4, "2008-02-27", r"Hugin Fm"); has(F4, "2008-02-27", r"station on 3417,5 m MD"); E["f4_hugin_pressure_point_md_m"] = 3417.5
has(F4, "2007-10-29", r"12 1/4\" hole section from 2626 m to TD at 2770 m"); E["f4_12_25in_section_td_m"] = 2770
o = d[(d.wellbore == F4) & d.t.str.contains(r"8 1/2\" hole", case=False)].sort_values("day"); E["f4_first_8_5in_report"] = o.day.iloc[0]
assert E["f4_first_8_5in_report"] > "2007-10-29" and E["f4_first_8_5in_report"] < "2008-02-27"
json.dump(E, open("outputs/review_evidence.json", "w", newline="\n"), indent=1)
print(json.dumps(E, indent=1))
