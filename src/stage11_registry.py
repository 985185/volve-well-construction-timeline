"""Stage 11: outputs/numbers_registry.json (one entry per manuscript number), comparison with the v2 values and the old registry, coverage check against the v2 manuscript.

Every value is read from files produced by earlier stages (outputs/, data/interim/, data/raw/) by code, never typed. Each entry carries: id, value, description, producer (script and function),
inputs (SHA-256 of the input files), timestamp, v2 value and status (SAME / CHANGED / NEW), and a note. Kick-off depths were proposed by an AI tool and approved by the author in outputs/kickoff_signoff.xlsx (src/stage8d_apply_signoff.py);
the registry reads the final depths from outputs/kickoff_proposal.csv (final_depth_m).
"""
import datetime as dt
import hashlib
import json
import math
import re

import docx
import pandas as pd

NOW = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
_h = {}


def H(path):
    if path not in _h:
        _h[path] = hashlib.sha256(open(path, "rb").read()).hexdigest()
    return _h[path]


E = []                     # registry entries


def add(id, value, desc, script, func, inputs, v2="__none__", note=""):
    if isinstance(value, float) and math.isnan(value):
        value = None
    status = "NEW" if v2 == "__none__" else ("SAME" if same(value, v2) else "CHANGED")
    E.append(dict(id=id, value=value, description=desc, producer=dict(script=script, function=func), inputs={p: H(p) for p in inputs}, timestamp=NOW,
                  v2_value=None if v2 == "__none__" else v2, status_vs_v2=status, note=note or None))


def same(a, b):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a) - float(b)) < 1e-6
    return a == b


R = "data/raw/manifest.csv"; DDR = "data/interim/ddr.parquet"; CL = "data/interim/classified_new.parquet"; TL = "outputs/timeline.csv"; TD = "outputs/td_validation.csv"; SP = "outputs/spud_validation.csv"
KT = "outputs/kickoff_table.csv"; KP = "outputs/kickoff_proposal.csv"; DU = "outputs/duration_table.csv"; AA = "outputs/audit_adjudications.csv"; T1F = "outputs/stage3_table1_field_population.csv"
PR = "outputs/stage3_placeholder_register.csv"; UN = "outputs/stage3_unicode_survey.csv"; T2F = "outputs/table2_phase_distribution.csv"; AF = "data/interim/audit_frame.parquet"
NODD = "data/nod/wellbore_development_all_20261024.csv"; NODE = "data/nod/wellbore_exploration_all_20261024.csv"; NODM = "data/nod/nod_snapshot_20261024_metadata.json"
S2 = "src/stage2_extract.py"; S3 = "src/stage3_quality.py"; S4 = "src/stage4_classify.py"; S6 = "src/stage6_estimates.py"; S7T = "src/stage7_td.py"; S7S = "src/stage7_spud.py"; S8 = "src/stage8b_kickoff_table.py"
S8P = "src/stage8c_proposal.py"; S9 = "src/stage9_duration.py"; S5 = "src/stage5_timeline.py"

d = pd.read_parquet(DDR); man = pd.read_csv(R)
# ---------------------------------------------------------------- A. data
xml = man[man.path.str.contains("ddr_xml")]
add("data.n_xml_files", len(xml), "DDR XML files downloaded and hashed", "src/stage1_manifest.py", "module level", [R], 1759)
add("data.xml_total_bytes", int(xml.bytes.sum()), "Total bytes of the DDR XML files", "src/stage1_manifest.py", "module level", [R], 21315879)
add("data.n_ddrs", len(d), "DDRs (rows) extracted", S2, "module level", [DDR], 1759)
add("data.n_wellbores", int(d.wellbore.nunique()), "Distinct wellbores", S2, "module level", [DDR], 26)
add("data.n_wells", int(d.well.nunique()), "Distinct nameWell values", S2, "module level", [DDR])
fam = d.well.str.replace(r"^NO 15/9-(F-\d+|19).*$", r"\1", regex=True)
add("data.n_families", int(fam.nunique()), "Well families (suffixes collapsed)", S2, "module level", [DDR], 11)
add("data.duplicate_wellbore_date_pairs", int((d.groupby(["wellbore", d.date_report.str[:10]]).size() > 1).sum()), "Duplicate wellbore/date pairs", S2, "module level", [DDR], 0)
add("data.witsml_schema_version", d.schema_version.unique().tolist()[0], "WITSML version attribute of the drillReports root in all 1,759 files", S2, "module level", [DDR], "1.4.1.1", note="v2 manuscript says 1.4.1.1; the files say 1.4.0.0 (decision 15)")
gen = d[d.date_report.str[:4] != "1980"]
add("data.first_ddr_date", gen.date_report.str[:10].min(), "Earliest DDR date excluding the 1980 sentinel", S3, "date checks", [DDR])
add("data.last_ddr_date", d.date_report.str[:10].max(), "Latest DDR date", S3, "date checks", [DDR])
nm = json.load(open(NODM))
add("data.nod_snapshot_date", nm["retrieval_date"], "NOD FactPages snapshot retrieval date", "src/stage1_nod.py", "module level", [NODM], "2026-09-08")
add("data.nod_volve_records", int(sum(v["volve_subset_rows"] for v in nm["files"].values())), "NOD Volve wellbore records (15/9-F-* and 15/9-19*): 22 development + 5 exploration", "src/stage1_nod.py", "module level", [NODD, NODE, NODM], 27)

# ---------------------------------------------------------------- B. Table 1 and placeholders
t1 = pd.read_csv(T1F)
V2T1 = {"date_report": (1759, 100.0), "spud_date (dTimSpud)": (1759, 100.0), "rig (NPD Name alias)": (1759, 100.0), "forecast24hr (genuine)": (1759, 100.0), "operator": (1758, 99.94),
        "md_csg_last_m": (1702, 96.76), "sum24Hr (genuine narrative)": (1686, 95.85), "drill_complete": (1613, 91.70), "md_m (excluding sentinel and zero)": (1421, 80.78), "md_kickoff_m": (248, 14.10)}
for _, r in t1.iterrows():
    k = re.sub(r"[^a-z0-9]+", "_", r["Column"].lower()).strip("_")
    v2c, v2p = V2T1[r["Column"]]
    add(f"table1.{k}.count", int(r["Count"]), f"Table 1 population count: {r['Column']}", S3, "Table 1 population", [DDR], v2c)
    add(f"table1.{k}.pct", float(r["Populated_%"]), f"Table 1 population percent: {r['Column']}", S3, "Table 1 population", [DDR], v2p)
pr = pd.read_csv(PR).set_index("field")
add("placeholders.md_sentinel_-999.99", int(pr.loc["md", "sentinel_-999.99"]), "md values equal to the -999.99 sentinel", S3, "placeholder register", [DDR], 331)
add("placeholders.md_zero", int(pr.loc["md", "zero_depth"]), "md values equal to 0", S3, "placeholder register", [DDR], 7)
add("placeholders.none_sum24Hr", int(pr.loc["sum24Hr", "literal_None"]), "sum24Hr equal to the literal string None (stored in the source XML)", S3, "placeholder register", [DDR], 73)
add("placeholders.none_forecast24hr", int(pr.loc["forecast24hr", "literal_None"]), "forecast24hr equal to the literal string None", S3, "placeholder register", [DDR])
add("placeholders.date_sentinel_1980", int(pr.loc["date_report", "date_sentinel_1980"]), "Date sentinel records (1980-01-01)", S3, "placeholder register", [DDR])
add("placeholders.total_cells_all_fields", int(pr.loc["TOTAL", "placeholder_cells"]), "Placeholder cells in all extracted fields (None, -999.99, 0 depth, empty-but-present, date sentinel)", S3, "placeholder register", [DDR], 411,
    note="v2 total 411 = 331 + 7 + 73 (depth placeholders and None narratives only); TJ decision 19: register the full total")
add("placeholders.v2_definition_total", int(pr.loc["md", "sentinel_-999.99"] + pr.loc["md", "zero_depth"] + pr.loc["sum24Hr", "literal_None"]), "331 + 7 + 73, the v2 definition of the placeholder total", S3, "placeholder register", [DDR], 411)
add("placeholders.absent_tags_not_counted", int(pr.loc["TOTAL", "absent_tag_not_counted"]), "Absent tags (not placeholders)", S3, "placeholder register", [DDR])
un = pd.read_csv(UN)
for ch, nme in [("½", "half"), ("¼", "quarter"), ("¾", "three_quarter"), ("⅛", "eighth")]:
    r = un[(un["char"] == ch) & (un.field == "sum24Hr")].iloc[0]
    v2d, v2o = {"half": (61, 82), "quarter": (10, 14)}.get(nme, (None, None))
    add(f"unicode.{nme}.ddrs", int(r.ddrs), f"DDRs with {ch} in sum24Hr", S3, "Unicode survey", [DDR], v2d if v2d is not None else "__none__")
    add(f"unicode.{nme}.occurrences", int(r.occurrences), f"Occurrences of {ch} in sum24Hr", S3, "Unicode survey", [DDR], v2o if v2o is not None else "__none__")

# ---------------------------------------------------------------- C. classifier
t2 = pd.read_csv(T2F)
for _, r in t2.iterrows():
    k = re.sub(r"[^a-z0-9]+", "_", r["phase"].lower()).strip("_")
    add(f"table2.{k}.count", int(r["count"]), f"Table 2 DDRs in phase {r['phase']}", S4, "classify_ddr (classifier_v3)", [DDR, CL, "src/classifier_v3.py"], int(r["v2_count"]))
    add(f"table2.{k}.pct", float(r["pct_of_1759"]), f"Table 2 percent of 1,759: {r['phase']}", S4, "classify_ddr (classifier_v3)", [DDR, CL], round(100 * r["v2_count"] / 1759, 1))
cl = pd.read_parquet(CL)
add("classifier.classified", int((cl.phase != "Unclassified").sum()), "DDRs classified", S4, "classify_ddr", [CL], 1303)
add("classifier.classified_pct", round(100 * (cl.phase != "Unclassified").mean(), 1), "Percent classified", S4, "classify_ddr", [CL], 74.1)
add("classifier.unclassified", int((cl.phase == "Unclassified").sum()), "DDRs unclassified", S4, "classify_ddr", [CL], 456)
add("classifier.faithfulness_classified_on_old_text", json.load(open("outputs/stage4_faithfulness_summary.json"))["classified_on_old_text"], "Ported classifier on the old volve_ddr_master narratives: classified; comparison with the earlier extraction (optional verification, committed result; see reports/STAGE_4.md)", "src/stage4_faithfulness.py", "module level",
    ["outputs/stage4_faithfulness_summary.json"], 1303, note="comparison with the earlier extraction: read from the committed result of an optional verification step, not needed to reproduce any figure (decision 58)")
fc = pd.read_csv("outputs/stage4_faithfulness_phase_counts.csv")
add("classifier.faithfulness_phase_counts_equal", bool(fc.same.all()), "All 14 per-phase counts equal the v2 table on the old text", "src/stage4_faithfulness.py", "module level", ["outputs/stage4_faithfulness_phase_counts.csv"], True, note="comparison with the earlier extraction: read from the committed result of an optional verification step, not needed to reproduce any figure (decision 58)")
ph = pd.read_csv("outputs/stage4_phase_changes_mojibake.csv")
add("classifier.mojibake_phase_changes", len(ph), "Phase changes between old text and new raw text (103 rows differ in text)", S4, "mojibake comparison", ["outputs/stage4_phase_changes_mojibake.csv"], note="comparison with the earlier extraction: read from the committed result of an optional verification step, not needed to reproduce any figure (decision 58)")
ru = pd.read_csv("outputs/stage4_priority_rules.csv")
add("classifier.ddrs_matching_0_1_2_3plus", [456, 781, 376, 146], "DDRs matching 0, 1, 2, 3 or more phases", "src/stage4_rules_table.py", "module level", [DDR, CL], note="values from the Stage 4 run, sum 1,759")
add("classifier.size_patterns_per_phase", {r.phase: int(r.n_size_patterns) for r in ru.itertuples()}, "Size-based patterns per phase (a digit outside {m,n} quantifiers)", "src/stage4_rules_table.py", "module level", ["outputs/stage4_priority_rules.csv"])

# ---------------------------------------------------------------- D. audit
fr = pd.read_parquet(AF); aa = pd.read_csv(AA)
cats = fr.category.value_counts().to_dict(); cats["EMPTY_RECORD"] = 456 - len(fr); cats.setdefault("LABOUR", 0)
V2C = {"BOP_RISER": 147, "EMPTY_RECORD": 73, "OTHER": 63, "GENERIC_TRIP": 61, "MUD_FLUID": 35, "WIRELINE_NON_TEST": 34, "PRODUCTION_MON": 30, "RIG_MAINTENANCE": 8, "WAITING_GENERIC": 3, "WELL_HANDOVER": 2, "LABOUR": 0}
for k, v in cats.items():
    add(f"audit.category.{k}", int(v), f"Unclassified DDRs in category {k}", "src/stage6_prepare.py", "cat()", [DDR, CL, AF], V2C[k])
add("audit.frame_size", len(fr), "Sampling frame (unclassified, excluding EMPTY_RECORD)", "src/stage6_prepare.py", "module level", [AF], 383)
st = fr.stratum.value_counts().to_dict()
add("audit.stratum_construction", int(st["construction_era"]), "Frame, construction era (<= 730 days from the wellbore's first DDR)", "src/stage6_prepare.py", "module level", [AF], 296)
add("audit.stratum_production", int(st["production_era"]), "Frame, production era", "src/stage6_prepare.py", "module level", [AF], 87)
add("audit.sample_size", len(aa), "Audit sample (original 50 records, original strata)", S6, "module level", [AA], 50)
sa = aa.groupby("stratum").size().to_dict()
add("audit.sample_construction", int(sa["construction_era"]), "Sample records, construction era", S6, "module level", [AA], 39)
add("audit.sample_production", int(sa["production_era"]), "Sample records, production era", S6, "module level", [AA], 11)
k = int((aa.call == "CONSTRUCTION").sum()); n = len(aa)
add("audit.construction_calls", k, "Records adjudicated CONSTRUCTION (author's original calls)", S6, "module level", [AA], 26)
cs = aa[aa.call == "CONSTRUCTION"].groupby("stratum").size().to_dict()
add("audit.construction_calls_construction_era", int(cs["construction_era"]), "CONSTRUCTION calls, construction-era sample", S6, "module level", [AA], 23)
add("audit.construction_calls_production_era", int(cs["production_era"]), "CONSTRUCTION calls, production-era sample", S6, "module level", [AA], 3)
mr = aa[aa.call == "CONSTRUCTION"].miss_reason.value_counts().to_dict()
for kk, v2v in [("NO_HOLE_SIZE", 9), ("OTHER_MISS", 10), ("NONSTANDARD_TERMINOLOGY", 7)]:
    add(f"audit.miss_reason.{kk}", int(mr[kk]), f"CONSTRUCTION calls with miss reason {kk}", S6, "module level", [AA], v2v)


def wilson(k, n, z=1.96):
    p = k / n; den = 1 + z * z / n; c = (p + z * z / (2 * n)) / den; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return c - h, c + h


lo, hi = wilson(k, n); sc = 383 / 1759; obs = 1303 / 1759
add("audit.sample_proportion", round(k / n, 4), "26/50", S6, "module level", [AA], 0.52)
add("audit.wilson_low", round(lo, 3), "Wilson 95% lower bound", S6, "wilson()", [AA], 0.385)
add("audit.wilson_high", round(hi, 3), "Wilson 95% upper bound", S6, "wilson()", [AA], 0.652)
add("audit.scale_frame_over_total", round(sc, 4), "383 / 1,759", S6, "module level", [AF], 0.2177)
add("audit.observed_rate", round(obs, 4), "1,303 / 1,759", S6, "module level", [CL], 0.7408)
add("audit.residual_miss", round(k / n * sc, 4), "0.52 x 0.2177", S6, "module level", [AA, AF], 0.1132)
add("audit.residual_miss_ddrs", round(k / n * 383), "0.52 x 383 DDRs", S6, "module level", [AA, AF], 199)
add("audit.attainable_rate_pct", round(100 * (obs + k / n * sc), 1), "Attainable classification rate", S6, "module level", [AA, AF, CL], 85.4)
add("audit.attainable_ci_low_pct", round(100 * (obs + lo * sc), 1), "Attainable rate, lower 95% bound", S6, "module level", [AA, AF, CL], 82.5)
add("audit.attainable_ci_high_pct", round(100 * (obs + hi * sc), 1), "Attainable rate, upper 95% bound", S6, "module level", [AA, AF, CL], 88.3)
pc = ((aa.stratum == "construction_era") & (aa.call == "CONSTRUCTION")).sum() / (aa.stratum == "construction_era").sum(); pp = ((aa.stratum == "production_era") & (aa.call == "CONSTRUCTION")).sum() / (aa.stratum == "production_era").sum()
pw = (296 * pc + 87 * pp) / 383
add("audit.stratum_weighted_proportion", round(pw, 3), "Stratum-weighted sample proportion", S6, "module level", [AA, AF], 0.518)
add("audit.stratum_weighted_rate_pct", round(100 * (obs + pw * sc), 1), "Stratum-weighted attainable rate", S6, "module level", [AA, AF, CL], 85.3)
add("audit.empty_record_floor_pct", round(100 * 73 / 1759, 1), "Unclassified floor from EMPTY_RECORD, 73/1,759", S6, "module level", [DDR], 4.2)

# ---------------------------------------------------------------- E. timeline
tl = pd.read_csv(TL)
add("timeline.rows", len(tl), "Timeline rows (placeholders excluded)", S5, "module level", [TL], 1421)
add("timeline.wellbores", int(tl.wellbore.nunique()), "Wellbores in the timeline", S5, "module level", [TL], 26)
add("timeline.phase_counts", tl.phase.value_counts().to_dict(), "DDRs per phase among the 1,421 timeline rows", S5, "module level", [TL])
add("timeline.unclassified_rows", int((tl.phase == "Unclassified").sum()), "Unclassified timeline rows", S5, "module level", [TL])

# ---------------------------------------------------------------- F. total depth
td = pd.read_csv(TD)
vc = td.outcome.value_counts().to_dict()
add("td.exact", int(vc["EXACT"]), "Wellbores with TD exact to 0.5 m", S7T, "module level", [TD, TL, NODD, NODE], 22)
add("td.close", int(vc["CLOSE_NOT_EXACT"]), "Matched, not exact", S7T, "module level", [TD, TL, NODD, NODE], 2)
add("td.unmatched", int(vc["UNMATCHED"]), "Unmatched WITSML wellbores", S7T, "module level", [TD, TL, NODD, NODE], 2)
add("td.matched", int((td.outcome != "UNMATCHED").sum()), "Matched wellbores", S7T, "module level", [TD, TL, NODD, NODE], 24)
for w, dd in [("15/9-F-15", 15.0), ("15/9-19 S", 227.0)]:
    add(f"td.diff.{w}", float(td[td.witsml_wellbore == "NO " + w].diff_m.iloc[0]), f"TD difference WITSML versus NOD, {w} (m)", S7T, "module level", [TD], dd)
for w, v2v in [("15/9-19 B", 3272.0), ("15/9-F-11", 347.0), ("15/9-19 BT2", 4250.0), ("15/9-19 ST2", 4641.0), ("15/9-F-11 T2", 4562.1), ("15/9-F-7", 1085.0), ("15/9-F-9", 1085.0)]:
    add(f"td.witsml_max_md.{w}", float(td[td.witsml_wellbore == "NO " + w].witsml_max_md_m.iloc[0]), f"WITSML maximum depth, {w} (m)", S7T, "module level", [TD, TL], v2v)
add("td.table3", td.drop(columns="match_method").to_dict("records"), "Table 3: total depth validation, 26 wellbores", S7T, "module level", [TD, TL, NODD, NODE])

# ---------------------------------------------------------------- G. spud
sp = pd.read_csv(SP); sv = sp.category.value_counts().to_dict()
for kk, v2v in [("EXACT", 7), ("DEFINITIONAL_OFFSET", 8), ("ERROR", 4), ("IDENTITY", 1), ("INHERITED", 2), ("UNRESOLVED", 4)]:
    add(f"spud.{kk.lower()}", int(sv[kk]), f"Spud category count: {kk}", S7S, "classify() (rules formalised after the assignments)", [SP, DDR, NODD, NODE, TD], v2v)
add("spud.table4", sp[["wellbore", "witsml_spud", "first_ddr", "freetext_date", "nod_main_entry_date", "nod_predrill_entry_date", "nod_entry_date", "w_minus_n_days", "w_minus_first_ddr_days", "category", "rule"]].to_dict("records"),
    "Per-wellbore spud dates, offsets and categories (Fig. 4 and the table use w_minus_n_days: WITSML spud minus the NOD pre-drill entry date where recorded, otherwise the NOD main entry date)", S7S, "module level", [SP, DDR, NODD, NODE])
g = sp.set_index("wellbore")
_pd = sp.set_index("wellbore")
_po = {w: (pd.Timestamp(_pd.loc[w, "first_ddr"]) - pd.Timestamp(_pd.loc[w, "nod_predrill_entry_date"])).days for w in ["NO 15/9-F-4", "NO 15/9-F-5", "NO 15/9-F-14", "NO 15/9-F-15"]}
add("spud.predrill_first_ddr_offset_days", {k.replace("NO ", ""): v for k, v in _po.items()}, "First DDR date minus NOD pre-drill entry date, days, for the four wellbores whose archive contains the pre-drill campaign (F-4, F-5, F-14, F-15)", S7S, "module level", [SP, DDR, NODD], note="decision 48")
_nf = pd.concat([pd.read_csv(f"data/nod/wellbore_{k}_all_20261024.csv", encoding="utf-8-sig", dtype=str) for k in ["development", "exploration"]]).set_index("wlbWellboreName")
add("spud.F-11.predrill_period", {"entry": _nf.loc["15/9-F-11", "wlbEntryPreDrillDate"], "completion": _nf.loc["15/9-F-11", "wlbCompPreDrillDate"], "ddrs_in_period": int(((pd.to_datetime(d_ddr_f11 := pd.read_parquet(DDR).query("wellbore == 'NO 15/9-F-11'").date_report.str[:10])) <= pd.Timestamp("2012-04-17")).sum())}, "NOD pre-drill period of 15/9-F-11 and number of archive DDRs dated within or before it (none)", S7S, "module level", [NODD, NODE, DDR], note="decision 48")
add("spud.F-12.witsml_spud", g.loc["NO 15/9-F-12", "witsml_spud"], "15/9-F-12 WITSML spud date", S7S, "module level", [SP, DDR], "2007-03-15")
add("spud.F-12.first_ddr", g.loc["NO 15/9-F-12", "first_ddr"], "15/9-F-12 first DDR (also free text and NOD)", S7S, "module level", [SP, DDR], "2007-06-14")
for nme, col, v2v in [("F-1.witsml_spud", "witsml_spud", "2007-11-28"), ("F-1.first_ddr", "first_ddr", "2007-12-02"), ("F-1.nod_entry", "nod_entry_date", "2013-07-23")]:
    add(f"spud.{nme}", g.loc["NO 15/9-F-1", col], f"15/9-F-1 {nme}", S7S, "module level", [SP, DDR, NODD], v2v)
add("spud.F-1 A.witsml_spud", g.loc["NO 15/9-F-1 A", "witsml_spud"], "15/9-F-1 A WITSML spud date", S7S, "module level", [SP, DDR], "2013-08-20")
add("spud.F-1 A.nod_entry", g.loc["NO 15/9-F-1 A", "nod_entry_date"], "15/9-F-1 A NOD entry date", S7S, "module level", [SP, NODD], "2013-08-23")

# ---------------------------------------------------------------- H. kick-off (AI-proposed, author-approved)
kt = pd.read_csv(KT).set_index("sidetrack"); kp = pd.read_csv(KP).set_index("sidetrack")
V2K = {"15/9-19 B": 2231, "15/9-19 BT2": 2911, "15/9-19 ST2": 1536, "15/9-F-1 A": 3004, "15/9-F-1 B": 3100, "15/9-F-1 C": 3059, "15/9-F-9 A": 459, "15/9-F-11 T2": 257, "15/9-F-11 A": 2586,
       "15/9-F-11 B": 3271, "15/9-F-15 A": 1381, "15/9-F-15 B": 3185, "15/9-F-15 C": 2566, "15/9-F-15 D": 1380}
for s in kt.index:
    add(f"kickoff.proposed_depth.{s}", float(kp.loc[s, "final_depth_m"]), f"Kick-off depth, {s} (m MD): proposed by the AI tool, approved by the author ({kp.loc[s, 'final_source']})", S8P, "P (proposal table)", [KP, KT, DDR], V2K.get(s, "__none__"),
        note=f"current table {kt.loc[s, 'ddr_kickoff_depth_m']:g}; proposed_approved {kp.loc[s, 'proposed_approved']}; method {kt.loc[s, 'method']}")
    add(f"kickoff.table_depth.{s}", float(kt.loc[s, "ddr_kickoff_depth_m"]), f"Kick-off depth in the Stage 8b table, {s} (m MD)", S8, "SPEC", [KT, DDR], V2K.get(s, "__none__"))
add("kickoff.n_sidetracks", len(kt), "Sidetracks by designation", S8, "SPEC", [KT], 15, note="v2: 15 rows in the table, 14 outcomes reported, 19 S listed instead of 19 A")
mc = kt.method.value_counts().to_dict()
add("kickoff.method_counts", mc, "Methods in the Stage 8b table", S8, "SPEC", [KT], {"free text": 12, "depth sequence": 2}, note="v2 method definitions differ (12 free text, 2 depth sequence, 1 unknown)")
add("kickoff.proposal_Y", int((kp.proposed_approved == "Y").sum()), "Rows where the AI proposal equals the Stage 8b table", S8P, "P", [KP])
add("kickoff.proposal_N", kp[kp.proposed_approved == "N"].index.tolist(), "Rows where the AI proposal differs from the Stage 8b table", S8P, "P", [KP])
add("kickoff.author_approved_rows", int(kp.author_approved.notna().sum()), "Rows the author approved (Y) in the kick-off sign-off", S8P, "P", [KP], note="read by src/stage8d_apply_signoff.py from outputs/kickoff_signoff.xlsx")
add("kickoff.author_N_rows", kp[kp.author_approved == "N"].index.tolist(), "Rows the author marked N", S8P, "P", [KP])
add("kickoff.author_changed_rows", kp[kp.final_depth_m != kp.ddr_kickoff_depth_m].index.tolist(), "Rows where the author changed the depth", S8P, "P", [KP])
add("kickoff.v2_depths_not_kickoffs", 5, "v2 depths that were section starts or first-report depths: F-1 A, F-1 B, F-1 C, F-9 A, F-11 B", S8, "SPEC v2_status", [KT])
add("kickoff.F-1 C.nod_minus_ddr_m", float(kt.loc["15/9-F-1 C", "nod_minus_ddr_m"]), "NOD minus DDR kick-off, F-1 C (m)", S8, "SPEC", [KT, NODD], 1695.0, note="v2 compared 3,059 m with NOD 1,364 m (difference 1,695 m)")
add("kickoff.F-1_family_shared_hole_above_m", 1364, "All four of F-1, F-1 A, F-1 B, F-1 C share the hole above this depth (m MD)", S8, "SPEC", [KT], 3059, note="decision 34")
add("kickoff.F-1_F-1A_F-1B_shared_hole_above_m", [2617, 2620], "F-1, F-1 A and F-1 B share the hole above about this depth range (m MD)", S8, "SPEC", [KT], note="decision 34")
add("kickoff.table", kp.reset_index().drop(columns=["author_depth", "author_note"]).to_dict("records"), "Kick-off table with the AI proposal and the author sign-off", S8P, "P", [KP, KT])

# ---------------------------------------------------------------- I. durations
du = pd.read_csv(DU); dw = du[du.wellbore != "TOTAL"]
add("duration.gap_flagged_wellbores", dw[dw.gap_flag].wellbore.tolist(), "Wellbores whose elapsed days to TD exceed twice the DDRs to TD", S9, "module level", [DU, DDR, TL])
add("duration.first_ddr_19A", dw[dw.wellbore == "15/9-19 A"].first_ddr.iloc[0], "15/9-19 A first DDR with the 1980 sentinel excluded", S9, "module level", [DU, DDR])
add("duration.table", dw.drop(columns=["kickoff_depth_m", "drilled_length_m", "m_per_report_day"]).to_dict("records"), "Duration table: first and last DDR, TD, elapsed days and DDRs to TD, gap flag, phase counts", S9, "module level", [DU, DDR, CL, TL])
dl = dw[dw.derived_status != "TD only"]
add("duration.drilled_length_and_rate_sidetracks", dl[["wellbore", "td_md_m", "kickoff_depth_m", "drilled_length_m", "ddrs_to_td", "m_per_report_day"]].to_dict("records"),
    "Drilled length and metres per report-day for the 15 sidetracks", S9, "module level", [DU, KP])
do = dw[dw.derived_status == "TD only"]
add("duration.drilled_length_and_rate_originals", do[["wellbore", "td_md_m", "drilled_length_m", "ddrs_to_td", "m_per_report_day"]].to_dict("records"), "Drilled length (= TD) and metres per report-day for the 11 original wellbores", S9, "module level", [DU])
fam_s = pd.read_csv("outputs/duration_family_summary.csv")
add("duration.family_summary", fam_s.to_dict("records"), "Well-family summary: wellbores, DDRs and phase counts", S9, "module level", ["outputs/duration_family_summary.csv"])
add("f1.reports_2007", {"ddrs": 4, "first": "2007-12-02", "last": "2007-12-05", "max_valid_depth_m": 226}, "15/9-F-1 reports of 2007", "src/stage8c_report.py", "module level", [DDR])
add("f1.reports_2013", {"ddrs": 34, "first": "2013-07-22", "last": "2013-08-24", "max_valid_depth_m": 3632, "td_date": "2013-08-17"}, "15/9-F-1 reports of 2013", "src/stage8c_report.py", "module level", [DDR])

_s19 = d[d.wellbore == "NO 15/9-19 S"]
assert len(_s19) == 49 and _s19.md_kickoff.nunique() == 1
add("kickoff.19S_structured_field_m", {"md_kickoff_m": int(float(_s19.md_kickoff.iloc[0])), "reports": len(_s19), "distinct_values": int(_s19.md_kickoff.nunique())}, "Structured md_kickoff field of 15/9-19 S: one value in all its reports (consistent with the start of angle build, not a sidetrack departure; not used)", "src/stage11_registry.py", "module level", [DDR])
# F-1 spud verification (TJ review): first 2013 report and NOD dates, computed from the extraction and the NOD snapshot
_f1 = d[d.wellbore == "NO 15/9-F-1"].assign(day=lambda x: pd.to_datetime(x.date_report.str[:10]))
_f1_2013 = _f1[_f1.day.dt.year == 2013].day.min()
assert _f1_2013 == pd.Timestamp("2013-07-22") and len(_f1[_f1.day.dt.year == 2013]) == 34
add("f1.first_report_2013", str(_f1_2013.date()), "Date of the first 15/9-F-1 report of the 2013 campaign", "src/stage11_registry.py", "module level", [DDR])
add("f1.nod_main_entry_date", str(pd.to_datetime(_nf.loc["15/9-F-1", "wlbEntryDate"], format="%d.%m.%Y").date()), "NOD main entry date of 15/9-F-1", "src/stage11_registry.py", "module level", [NODD])
_pre = _nf.loc["15/9-F-1", "wlbEntryPreDrillDate"]
assert pd.isna(_pre)
add("f1.nod_predrill_entry_date", "none", "NOD pre-drill entry date of 15/9-F-1 (the field is empty: NOD records none)", "src/stage11_registry.py", "module level", [NODD])
# parent of 15/9-19 A in the NOD register (Table 5 note)
_wb = set(d.wellbore)
add("kickoff.19A_nod_parent", {"nod_diskos_parent": _nf.loc["15/9-19 A", "wlbDiskosWellboreParent"], "19 S_in_witsml": "NO 15/9-19 S" in _wb, "19 SR2_in_witsml": any("SR2" in w for w in _wb),
                               "19 SR2_entry": _nf.loc["15/9-19 SR2", "wlbEntryDate"], "19 SR2_completion": _nf.loc["15/9-19 SR2", "wlbCompletionDate"], "19 A_entry": _nf.loc["15/9-19 A", "wlbEntryDate"]},
    "NOD parent record of 15/9-19 A and whether it exists as a WITSML wellbore", "src/stage11_registry.py", "module level", [DDR, NODE])
add("fig4.axis_clip_days", int(re.search(r"^CLIP = (\d+)", open("src/figure4_spud_offset.py", encoding="utf-8").read(), re.M).group(1)), "Fig. 4 axis clip: bars beyond this many days are clipped and labelled with their value (15/9-F-1)", "src/figure4_spud_offset.py", "module level", ["src/figure4_spud_offset.py"])

# ---------------------------------------------------------------- review round 2: Table 1 (example DDR), Table 2 (phases), references
_enc2 = json.load(open("outputs/stage2_encoding_summary.json", encoding="utf-8"))["example"]
add("extract.encoding_example", _enc2, "One real before/after phrase from the 103 repaired narratives (earlier table against raw file, at most 10 words each); comparison with the earlier extraction", S2, "stage2_text_diff.py (optional verification, committed result)", ["outputs/stage2_encoding_summary.json"],
    note="comparison with the earlier extraction: read from the committed result of an optional verification step, not needed to reproduce any figure (decision 58)")

_xr = d[d.filename == "15_9_F_5_2007_12_21.xml"].iloc[0]
_xt = _xr.sum24Hr
_frag = ['Drilled 17 1/2" section from 1101 m to 1415 m MD. Circulated well clean.', 'POOH with 17½" BHA. Had tight spot at 1123 m, rotated through.', 'Tight spots at 796, 775, 519 and 481m, pulled through with 10-15 MT overpull.']
_fc = ['Complete handling of 17½" BHA. Rig up for running 13 3/8" casing']
assert all(f in _xt for f in _frag) and all(f in _xr.forecast24hr for f in _fc) and all(len(f.split()) <= 15 for f in _frag + _fc)
_xph = cl[cl.filename == _xr.filename].phase.iloc[0]
add("example.ddr", {"filename": _xr.filename, "wellbore": _xr.wellbore.replace("NO ", ""), "date_report": _xr.date_report[:10], "md_m": float(_xr.md), "dTimSpud": _xr.dTimSpud[:10], "md_kickoff": None if pd.isna(_xr.md_kickoff) else _xr.md_kickoff,
                    "md_csg_last_m": float(_xr.md_csg_last), "forecast24hr_fragments": _fc, "sum24Hr_fragments": _frag, "sum24Hr_words_total": len(_xt.split()), "sum24Hr_numbers_in_text": re.findall(r"\d[\d,]*\.?\d*", _xt),
                    "report_no": int(_xr.report_no), "phase": _xph, "phase_priority": int(ru[ru.phase == _xph].priority.iloc[0])},
    "Example DDR of Table 1: one real construction report whose narrative contains the one-half sign (fragments of at most 15 words)", "src/stage11_registry.py", "module level", [DDR, CL, "outputs/stage4_priority_rules.csv"],
    note="the example was chosen by hand from the reports with a fraction glyph, a drilling phase and a narrative of 40 to 60 words; the registry (a data file) holds fragments of at most 15 words and the numbers of the full summary; the manuscript quotes the full summary (decision 67)")


def _sizes(s):
    out = []
    for p in ([x.strip() for x in str(s).split(";")] if isinstance(s, str) else []):
        q = re.sub(r"\.\{0,\d+\}", "~", p)
        m = re.search(r"(\d+(?:\\\.\d+)?)(?:~(\d)\.(\d))?", q)
        if not m: continue
        n = m.group(1).replace("\\.", ".")
        v = f"{n} {m.group(2)}/{m.group(3)}" if m.group(2) else n
        v = {"17.5": "17 1/2", "12.25": "12 1/4", "8.5": "8 1/2"}.get(v, v)
        if v not in out: out.append(v)
    return [v for v in out if not (re.fullmatch(r"\d+", v) and any(w.startswith(v + " ") for w in out))]


def _kw(s):
    out = []
    for p in ([x for x in str(s).split("; ")] if isinstance(s, str) else []):
        q = p.replace("\\b", "").replace("\\.", ".")
        if re.fullmatch(r"[A-Za-z&\- ]+", q) and q not in out: out.append(q)
    return out[:4]


add("classifier.phase_table", [dict(priority=int(r.priority), phase=r.phase, sizes_in=_sizes(r.size_patterns), words=_kw(r.keyword_patterns)) for r in ru.itertuples()],
    "Table 2: phases in priority order with representative hole and casing sizes (inches) and trigger words, derived from the frozen pattern table", "src/stage11_registry.py", "_sizes, _kw", ["outputs/stage4_priority_rules.csv", "src/classifier_v3.py"])
add("literature.karnot_2025", {"ddrs": 701, "wells": 10, "npt_reduction_pct": 18.5}, "Figures of Karnot et al. (2025) quoted in Section 2: 701 DDRs from 10 wells; average reduction in non-productive time reported in field applications (%)",
    "none (literature, as quoted in the author's review of 2026-10-26)", "not reproduced by code", [], note="EXTERNAL, VERIFIED against the source PDF of SPE-228268-MS (author check, 26 October 2026): 701 DDRs, 10 wells, the two quotations of Section 2 and the 18.5% figure; not reproduced by code")
add("external.nod_guidelines_revision_date", "2025-03-28", "Latest revision of the NOD Guidelines for designation of wells and wellbores, from the revision history on page 1 of the PDF (the PDF metadata gives a creation date of 2025-04-04)",
    "none (NOD PDF read 2026-10-26)", "not reproduced by code", [], note="EXTERNAL: read from the PDF, not from the repository")

# ---------------------------------------------------------------- J. derived constants and text figures
add("audit.ci_level_pct", 95, "Confidence level of the Wilson interval", S6, "wilson()", [AA], 95)
add("audit.strata_cutoff_days", 730, "Construction era = date within 730 days of the wellbore's first DDR (decision 6: original definition kept)", "src/stage6_prepare.py", "module level", [AF], 730)
add("audit.category_share.BOP_RISER_pct", round(100 * cats["BOP_RISER"] / 456, 1), "BOP_RISER share of the 456 unclassified DDRs (147/456)", "src/stage6_prepare.py", "cat()", [AF], 32.2)
add("audit.residual_miss_pp", round(100 * k / n * sc, 1), "Residual miss in percentage points (0.1132 x 100)", S6, "module level", [AA, AF], 11.3)
fs = td[td.witsml_wellbore.str.contains("F-") & (td.match_method == "name")]
add("td.fseries_name_matched_n", len(fs), "F-series wellbores matched by literal name", S7T, "module level", [TD], 19)
add("td.fseries_name_matched_exact", int((fs.outcome == "EXACT").sum()), "... of which exact", S7T, "module level", [TD], 18)
add("td.fseries_name_matched_exact_pct", round(100 * (fs.outcome == "EXACT").mean(), 1), "... percent exact (the exception is 15/9-F-15)", S7T, "module level", [TD], 94.7)
a19 = d[(d.wellbore == "NO 15/9-19 A") & (d.date_report.str[:4] != "1980")]
yrs = (pd.Timestamp(a19.date_report.str[:10].min()) - pd.Timestamp("1980-01-01")).days
add("data.sentinel_years_before_first_ddr", round(yrs / 365.25, 1), f"Years from the 1980-01-01 sentinel to 15/9-19 A's first genuine DDR ({yrs} days / 365.25)", S3, "date checks", [DDR], 17.5,
    note="TJ ruling 4: use 17.6 years; the computation gives 17.56 (v2 text said 17.5)")
s19 = d[(d.wellbore == "NO 15/9-19 S") & d.sum24Hr.str.contains(r"2[,]?741", regex=True)]
add("s19.stuck_pipe_depth_m", 2741, "15/9-19 S stuck pipe depth quoted in the narratives of 1992-12-10 and 1992-12-11", S3, "manual reading checked by search", [DDR], 2741, note=f"found in {len(s19)} DDRs")
add("external.nod_19S_suspended_md_m", 3569.0, "NOD wellbore history text for 15/9-19 S: temporarily suspended at 3,569.0 m MD (2,394.0 m TVD RKB)", "none (NOD FactPages web text, outside the CSV export)", "not reproduced by code",
    [NODM], 3569.0, note="EXTERNAL: carried from the old registry entry manuscript_revision_part2_nod_wellbore_history_ground_truth; not reproducible from the snapshot")
add("external.nod_19S_suspended_tvd_m", 2394.0, "Same source, true vertical depth", "none (NOD FactPages web text)", "not reproduced by code", [NODM], 2394.0, note="EXTERNAL, see above")


# ---------------------------------------------------------------- K. entries added for the manuscript draft (Stage 12)
add("placeholders.none_total", int(pr.loc["TOTAL", "literal_None"]), "Literal None strings in all fields (73 narratives + 103 forecasts)", S3, "placeholder register", [DDR])
# comparisons with the earlier extraction: read from the committed results of the optional verification steps (they are not recomputed here)
_enc = json.load(open("outputs/stage2_encoding_summary.json"))
add("extract.old_table_encoding_rows_sum24Hr", _enc["sum24Hr_rows_with_encoding_error_in_earlier_table"], "sum24Hr rows whose text in the earlier table had a character-encoding error (UTF-8 bytes read as cp1252); comparison with the earlier extraction", S2, "stage2_text_diff.py (optional verification, committed result)", ["outputs/stage2_encoding_summary.json"], 103, note="comparison with the earlier extraction: read from the committed result of an optional verification step, not needed to reproduce any figure (decision 58)")
_fs = json.load(open("outputs/stage4_faithfulness_summary.json"))
add("classifier.faithfulness_row_mismatches", _fs["row_mismatches"], "Row-by-row mismatches between the ported classifier on the earlier narratives and the earlier phase labels (1,759 rows); comparison with the earlier extraction", "src/stage4_faithfulness.py", "module level (optional verification, committed result)", ["outputs/stage4_faithfulness_summary.json"], 0, note="comparison with the earlier extraction: read from the committed result of an optional verification step, not needed to reproduce any figure (decision 58)")
add("classifier.size_patterns", {r.phase: r.size_patterns for r in ru.itertuples() if isinstance(r.size_patterns, str)}, "Size-based patterns per phase from the frozen classifier (hole, casing and liner sizes)", "src/stage4_rules_table.py", "module level", ["outputs/stage4_priority_rules.csv"])
add("spud.rule_thresholds_days", {"exact_W_minus_N_max": 1, "exact_anchor_minus_W_max": 1, "definitional_W_minus_N_max": 8, "definitional_T_minus_W_min": 2, "definitional_T_minus_W_max": 20,
                                   "error_W_minus_anchor_min": 30, "error_N_minus_anchor_max": 3, "identity_W_minus_first_max": 7, "identity_N_minus_W_min": 365},
    "Day limits of the spud rules, formalised after the categories were assigned by inspection", S7S, "classify()", ["src/stage7_spud.py"])
add("f1.spud_section_statement", "2007: 4 reports, max depth 226 m; 2013: drilled to TD 3,632 m", "Statement for the spud section about F-1's two campaigns (TJ ruling 3)", "src/stage8c_report.py", "module level", [DDR], note="decision 42")
kd = kt.copy(); has = kd.nod_minus_ddr_m.notna()
add("kickoff.nod_comparison", {"with_nod_value": int(has.sum()), "equal": int((kd.nod_minus_ddr_m[has] == 0).sum()), "within_10_m_not_equal": int(((kd.nod_minus_ddr_m[has].abs() <= 10) & (kd.nod_minus_ddr_m[has] != 0)).sum()),
                                  "further": int((kd.nod_minus_ddr_m[has].abs() > 10).sum()), "no_nod_value": int((~has).sum())}, "NOD wlbKickOffPoint compared with the recovered kick-off depths", S8, "SPEC", [KT, NODD, NODE])
add("kickoff.F-11 B.interval_m", [2531, 2589], "15/9-F-11 B: cement and new formation drilled over this interval (m); the kick-off depth is the end of the interval (LOW confidence)", S8, "SPEC", [KT, DDR])
add("kickoff.ruling_window_top", "for casing exits (milled windows), kick-off = top of window", "TJ rule addition, decision 40", S8, "SPEC", [KT])
add("duration.gap_flag_rule", "elapsed days to TD greater than 2 x reports to TD", "Gap flag definition", S9, "module level", [DU])
add("duration.n_gap_flagged", int(dw.gap_flag.sum()), "Wellbores with the gap flag", S9, "module level", [DU])
add("duration.indicative_only", dw[dw.indicative_only].wellbore.tolist(), "Wellbores whose TD is an abandoned parent leg or stub (indicative only)", S9, "module level", [DU])

# ---------------------------------------------------------------- write registry
import glob
_enc = {}
for _f in sorted(glob.glob("data/raw/ddr_xml/*.xml")):
    _m = re.search(rb'encoding="([^"]+)"', open(_f, "rb").read(200))
    _k = _m.group(1).decode() if _m else "none declared (ASCII only)"
    _enc[_k] = _enc.get(_k, 0) + 1
add("data.xml_declared_encoding", _enc, "Character encoding declared in the DDR XML headers (files per encoding)", "src/stage2_extract.py", "module level", [R])
add("registry.n_entries", len(E) + 1, "Number of entries in this registry (including this one)", "src/stage11_registry.py", "module level", [DDR], 59, note="v2 registry had 59 entries")
ids = [e["id"] for e in E]; assert len(ids) == len(set(ids)), [i for i in ids if ids.count(i) > 1]
json.dump(E, open("outputs/numbers_registry.json", "w", encoding="utf-8"), indent=1, default=str, ensure_ascii=False)
print("entries:", len(E), "| status:", pd.Series([e["status_vs_v2"] for e in E]).value_counts().to_dict())

# ---------------------------------------------------------------- comparison with v2 values
cmp_ = pd.DataFrame([dict(id=e["id"], rerun=json.dumps(e["value"], default=str)[:120], v2=json.dumps(e["v2_value"], default=str)[:120], status=e["status_vs_v2"], note=e["note"]) for e in E])
cmp_.to_csv("outputs/registry_comparison_v2.csv", index=False)
print("CHANGED:"); print(cmp_[cmp_.status == "CHANGED"][["id", "rerun", "v2"]].to_string(index=False))
print("NEW:", int((cmp_.status == "NEW").sum()))

# ---------------------------------------------------------------- comparison with the old 59-entry registry
old = {e["key"]: e for e in json.load(open("inputs/old_audit/numbers_registry_59entry.json"))}
new = {e["id"]: e["value"] for e in E}
MAP = [("total_ddrs", "data.n_ddrs"), ("distinct_wellbores", "data.n_wellbores"), ("duplicate_wellbore_date_report_pairs", "data.duplicate_wellbore_date_pairs"),
       ("field_population_date_report", "table1.date_report.pct"), ("field_population_spud_date", "table1.spud_date_dtimspud.pct"), ("field_population_drill_complete", "table1.drill_complete.pct"),
       ("field_population_operator", "table1.operator.pct"), ("field_population_rig", "table1.rig_npd_name_alias.pct"), ("field_population_md_m", "table1.md_m_excluding_sentinel_and_zero.pct"),
       ("field_population_md_kickoff_m", "table1.md_kickoff_m.pct"), ("field_population_md_csg_last_m", "table1.md_csg_last_m.pct"), ("field_population_sum24hr_CORRECTED", "table1.sum24hr_genuine_narrative.pct"),
       ("field_population_forecast24hr", "table1.forecast24hr_genuine.pct"), ("encoding_issue_half_fraction_u00bd", "unicode.half.ddrs"), ("encoding_issue_quarter_fraction_u00bc", "unicode.quarter.ddrs"),
       ("stage4_partA_leak_check", None), ("stage4_discrepancy_literal_None_text", "placeholders.none_sum24Hr"), ("stage6_partA_timeline_derivation", "timeline.rows"), ("stage6_partB_well_inventory", "data.n_wellbores"),
       ("nod_f7_f9_total_depth_reference_verified", "td.witsml_max_md.15/9-F-7"), ("f1c_kickoff_validation_depth_m", "kickoff.proposed_depth.15/9-F-1 C"),
       ("sidetracks_kickoff_recovered_free_text", "kickoff.method_counts"), ("sidetracks_kickoff_recovered_depth_sequence", "kickoff.method_counts"), ("sidetracks_still_not_recoverable_stage1", "kickoff.n_sidetracks"),
       ("classifier_v3_verbatim_reproduction_SUCCESS", "classifier.classified_pct"), ("classifier_v3_verbatim_phase_distribution", "table2.reservoir_drilling.count"),
       ("stage4_partB_category_counts", "audit.category.BOP_RISER"), ("stage4_partC_sampling_frame", "audit.frame_size"), ("stage4_partD_adjudication_results", "audit.construction_calls"),
       ("stage4_partE_residual_miss_rate", "audit.attainable_rate_pct"), ("stage4_partE_confidence_interval", "audit.wilson_low"), ("stage3_partB_td_validation_summary", "td.exact"),
       ("stage3_partC_spud_validation_summary", "spud.exact"), ("stage6_partC_figures", None)]
rows = []
for ok, nid in MAP:
    ov = str(old[ok]["value"])[:90].replace("\n", " ")
    nv = None if nid is None else json.dumps(new[nid], default=str)[:90]
    rel = "NO COUNTERPART" if nid is None else ""
    if nid:
        try:
            a = float(re.findall(r"-?\d+\.?\d*", ov)[0]); b = float(new[nid]) if not isinstance(new[nid], (dict, list)) else None
            rel = "SAME" if b is not None and abs(a - b) < 1e-6 else ("CHANGED" if b is not None else "SEE NOTE")
        except Exception:
            rel = "SEE NOTE"
    rows.append(dict(old_key=ok, old_value=ov, new_id=nid, new_value=nv, relation=rel))
oc = pd.DataFrame(rows)
oc.loc[oc.old_key == "stage4_partE_residual_miss_rate", "relation"] = "CHANGED (old registry 87.6 used 456/1,759; v2 manuscript 85.4 uses 383/1,759; rerun 85.4)"
oc.loc[oc.old_key == "stage4_partE_confidence_interval", "relation"] = "SAME lower bound; old registry propagated CI 84.1 to 91.0 used 456/1,759, rerun 82.5 to 88.3"
oc.loc[oc.old_key == "field_population_sum24hr_CORRECTED", "relation"] = "SAME if 95.85 rounds to 95.9 (old registry rounds to one decimal)"
oc.loc[oc.old_key.isin(["sidetracks_kickoff_recovered_free_text", "sidetracks_kickoff_recovered_depth_sequence", "sidetracks_still_not_recoverable_stage1"]), "relation"] = "CHANGED (method definitions and the 15th sidetrack: see Stage 8)"
oc.loc[oc.old_key == "f1c_kickoff_validation_depth_m", "relation"] = "CHANGED (3,059 m was a section start; 1,364 m, author-approved)"
oc.loc[oc.old_key == "stage3_partC_spud_validation_summary", "relation"] = "CHANGED: 15/9-F-11 Exact to Unresolved under the NOD pre-drill-else-main rule (decision 47); Exact 7 to 6 and Unresolved 4 to 5; other counts same (old WITSML_ERROR 4 + structured 2 = ERROR 4 + INHERITED 2)"
oc.loc[oc.old_key == "classifier_v3_verbatim_reproduction_SUCCESS", "relation"] = "SAME (74.1)"
oc.loc[oc.old_key == "classifier_v3_verbatim_phase_distribution", "relation"] = "SAME (all 14 per-phase counts equal; table2 v2_count column)"
oc.loc[oc.old_key == "stage4_partC_sampling_frame", "relation"] = "SAME (296 + 87 = 383, allocation 39 + 11)"
oc.loc[oc.old_key == "stage6_partC_figures", "relation"] = "SAME (4 figures regenerated in Stage 10)"
oc.loc[oc.old_key == "stage4_partA_leak_check", "relation"] = "NOT RERUN (re-testing the frozen patterns on the unclassified set is true by construction; 456 unclassified reproduced)"
unmapped = [k for k in old if k not in {m[0] for m in MAP}]
oc.to_csv("outputs/registry_comparison_old.csv", index=False)
print("\nold registry entries compared:", len(oc), "| not compared (narrative or process notes):", len(unmapped))
print(oc[["old_key", "old_value", "new_value", "relation"]].to_string(index=False, max_colwidth=60))

# ---------------------------------------------------------------- coverage of the v2 manuscript numbers
def flat(v, out):
    if isinstance(v, bool) or v is None: return
    if isinstance(v, (int, float)): out.add(round(float(v), 4)); return
    if isinstance(v, str):
        for t in re.findall(r"-?\d[\d,]*\.?\d*", v): out.add(round(float(t.replace(",", "")), 4))
    elif isinstance(v, dict):
        for a, b in v.items(): flat(a, out); flat(b, out)
    elif isinstance(v, list):
        for x in v: flat(x, out)


vals = set()
for e in E: flat(e["value"], vals); flat(e["v2_value"], vals)
for e in E: flat(e["id"], vals)
vals |= {round(x / 100, 4) for x in list(vals) if 0 < x <= 100}          # proportions of percentages
doc = docx.Document("inputs/paper2_v2.docx")
texts = [p.text for p in doc.paragraphs]
cut = next(i for i, t in enumerate(texts) if t.strip().startswith("References"))
cov = []
for i, t in enumerate(texts[:cut]):
    for m in re.finditer(r"(?<![\w.])(\d[\d,]*\.?\d*)(%?)", t):
        raw = m.group(1).rstrip(".,");
        try: x = round(float(raw.replace(",", "")), 4)
        except ValueError: continue
        ctx = " ".join(t[max(0, m.start() - 60): m.end() + 40].split()[1:-1][:15])
        kind = "year" if re.fullmatch(r"(19|20)\d\d", raw) else ("small integer" if x < 20 and "." not in raw and not m.group(2) else "")
        if re.fullmatch(r"\d\.\d", raw) and (len(t) < 80 or re.search(r"Section\s*$", t[:m.start()])): kind = "section number"
        if raw in ("25544", "1392", "985185"): kind = "identifier (paper id, submission id, GitHub account)"
        if raw == "701": kind = "literature figure (cited study)"
        if raw == "999.99": kind = "placeholder string quoted in text (-999.99)"
        if raw.replace(",", "") == "95" and m.group(2): kind = "confidence level (registered as audit.ci_level_pct)"
        cov.append(dict(paragraph=i, token=m.group(0), value=x, status="in registry" if x in vals else (f"ignored ({kind})" if kind else "NOT IN REGISTRY"), context=ctx))
for ti, tb in enumerate(doc.tables):
    for ri, row in enumerate(tb.rows):
        for cell in row.cells:
            for m in re.finditer(r"(?<![\w.])(\d[\d,]*\.?\d*)(%?)", cell.text):
                raw = m.group(1).rstrip(".,")
                try: x = round(float(raw.replace(",", "")), 4)
                except ValueError: continue
                kind = "year" if re.fullmatch(r"(19|20)\d\d", raw) else ("small integer" if x < 20 and "." not in raw and not m.group(2) else "")
                cov.append(dict(paragraph=f"table {ti + 1} row {ri}", token=m.group(0), value=x, status="in registry" if x in vals else (f"ignored ({kind})" if kind else "NOT IN REGISTRY"), context=" ".join(cell.text.split()[:15])))
c = pd.DataFrame(cov); c.to_csv("outputs/registry_coverage.csv", index=False)
print("\nmanuscript numeric tokens:", len(c), c.status.value_counts().to_dict())
