"""Stage 6a: categories for unclassified DDRs, sampling frame, strata, and mapping of the old 50 audit records to filenames.
No adjudication values are read into any output of this script (old calls are only used later, after TJ's blind review)."""
import re, sys
import pandas as pd
sys.path.insert(0, "src")

d = pd.read_parquet("data/interim/ddr.parquet").merge(pd.read_parquet("data/interim/classified_new.parquet")[["filename", "phase"]], on="filename")
d["text"] = d["sum24Hr"].fillna("").str.strip()
CATS = [  # priority-ordered, first match wins; ported from C:\Volve\paper2_rebuild\unclassified_category_query.sql (Spark RLIKE '(?i)...')
    ("EMPTY_RECORD", r"^\s*None\s*$"),
    ("BOP_RISER", r"\bBOP\b|\briser\b|\bdiverter\b|connector test|\bLMRP\b|\bLMPR\b|marine.{0,10}riser"),
    ("WIRELINE_NON_TEST", r"\bwireline\b|slickline|\be-?line\b|\bMDT\b|electric.?line|\bWL\b"),
    ("PRODUCTION_MON", r"\bchoke\b|well test|build.?up test|flowed|\bproduction\b|flowline|separator|shut.?in"),
    ("RIG_MAINTENANCE", r"maintenance|\brepair|tool fail|equipment fail|breakdown|changed out worn"),
    ("MUD_FLUID", r"\bmud\b|\bbrine\b|circulat|\bfluid\b"),
    ("WELL_HANDOVER", r"handover|hand.?over|suspen"),
    ("LABOUR", r"strike|labour|labor|union|crew change"),
    ("WAITING_GENERIC", r"\bw\.?o\.?w\.?\b|\bwaiting\b|stand.?by"),
    ("GENERIC_TRIP", r"\bPOOH\b|\bRIH\b|\btrip\b|\bTIH\b"),
]
def cat(t):
    for name, rx in CATS:
        if re.search(rx, t, re.I): return name
    return "OTHER"
u = d[d.phase == "Unclassified"].copy()
u["category"] = u.text.map(cat)
cc = u.category.value_counts()
print("unclassified:", len(u)); print(cc.to_dict()); print("sum", int(cc.sum()))
tgt = {"BOP_RISER": 147, "EMPTY_RECORD": 73, "OTHER": 63, "GENERIC_TRIP": 61, "MUD_FLUID": 35, "WIRELINE_NON_TEST": 34, "PRODUCTION_MON": 30, "RIG_MAINTENANCE": 8, "WAITING_GENERIC": 3, "WELL_HANDOVER": 2, "LABOUR": 0}
print("categories equal to v2 counts:", {k: int(cc.get(k, 0)) == v for k, v in tgt.items()})

# compare with the old category file row by row (wellbore + date)
oc = pd.read_csv(r"C:\Volve\paper2_rebuild\unclassified_categories.csv"); oc["day"] = oc.date_report.str[:10]
u["day"] = u.date_report.str[:10]
mm = u.merge(oc[["wellbore", "day", "category"]], on=["wellbore", "day"], suffixes=("", "_old"), how="outer", indicator=True)
print("old category file vs new, rows:", mm._merge.value_counts().to_dict(), "| category differs:", int((mm.category != mm.category_old).sum()))

# frame and strata (v2 definition: days from the wellbore's first DDR, sentinel included, <= 730)
d["day"] = pd.to_datetime(d.date_report.str[:10])
first = d.groupby("wellbore").day.min().rename("first_ddr")
f = u[u.category != "EMPTY_RECORD"].copy(); f["day"] = pd.to_datetime(f.day)
f = f.merge(first, on="wellbore"); f["days_since_first_ddr"] = (f.day - f.first_ddr).dt.days
f["stratum"] = (f.days_since_first_ddr <= 730).map({True: "construction_era", False: "production_era"})
print("frame:", len(f), f.stratum.value_counts().to_dict(), "| 383/1759 =", round(383 / 1759, 4))
f = f.sort_values("filename")
f[["filename", "wellbore", "date_report", "category", "days_since_first_ddr", "stratum"]].to_parquet("data/interim/audit_frame.parquet", index=False)

# mapping of the old 50
old = pd.read_csv("local_private/old_audit/audit_sample.csv")
old["day"] = old.date_report.str[:10]
fr = f.assign(day=f.day.dt.strftime("%Y-%m-%d"))
dd = d.assign(day=d.day.dt.strftime("%Y-%m-%d"))
m = old[["wellbore", "day", "category", "stratum", "days_since_first_ddr", "sum24hr"]].merge(dd[["filename", "wellbore", "day", "phase", "text"]], on=["wellbore", "day"], how="left", indicator=True)
print("\nold 50 -> raw DDR by wellbore + date:", m._merge.value_counts().to_dict(), "| distinct filenames:", m.filename.nunique(), "| duplicates keys in old:", int(old.duplicated(["wellbore", "day"]).sum()))
print("DDR rows matching more than one old record:", int(m.filename.duplicated().sum()))
m = m.merge(fr[["filename", "category", "stratum", "days_since_first_ddr"]], on="filename", how="left", suffixes=("", "_new"))
print("in new frame:", int(m.category_new.notna().sum()), "of 50 | phase Unclassified:", int((m.phase == "Unclassified").sum()))
print("category same:", int((m.category == m.category_new).sum()), "| stratum same:", int((m.stratum == m.stratum_new).sum()), "| days_since_first_ddr same:", int((m.days_since_first_ddr == m.days_since_first_ddr_new).sum()))
def moji(s):
    try: return s.encode("cp1252").decode("utf-8")
    except Exception: return s
same_txt = [(moji(a.strip()) == b) or (a.strip() == b) for a, b in zip(m.sum24hr.fillna(""), m.text.fillna(""))]
print("narrative identical to raw (after strip / mojibake repair):", sum(same_txt), "of 50")
print(m[~pd.Series(same_txt)][["wellbore", "day"]].to_string())
print("stratum counts in old 50:", m.stratum.value_counts().to_dict())
m[["filename", "wellbore", "day", "stratum", "stratum_new", "category", "category_new"]].to_csv("data/interim/audit_old50_filename_map.csv", index=False)
