"""Stage 4c: run frozen classifier v3 on the new extraction (strip inside the call only), compare with v2 Table 2 and with the old text."""
import re, sys
import pandas as pd
sys.path.insert(0, "src")
import classifier_v3 as C

new = pd.read_parquet("data/interim/ddr.parquet")
old = pd.read_parquet("data/interim/old/volve_ddr_master.parquet")
new["phase"] = new["sum24Hr"].fillna("").map(lambda t: C.classify_ddr(t.strip()))
new[["filename", "wellbore", "date_report", "phase"]].to_parquet("data/interim/classified_new.parquet", index=False)

order = ["Reservoir drilling", "Completion", "Liner / Casing run", "Waiting / Downtime", "Cementing", "Logging / Testing",
         "Intermediate casing", "Intermediate drilling", "Surface casing", "Spud / Conductor", "P&A", "Rig move / Setup", "Workover", "Unclassified"]
v2 = pd.read_csv("inputs/repo_before/data/phase_distribution.csv").set_index("phase")["count"]
t2 = pd.DataFrame({"phase": order, "count": [int((new.phase == p).sum()) for p in order]})
t2["pct_of_1759"] = (100 * t2["count"] / len(new)).round(1); t2["v2_count"] = [int(v2[p]) for p in order]; t2["same"] = t2["count"] == t2["v2_count"]
t2.to_csv("outputs/table2_phase_distribution.csv", index=False); print(t2.to_string(index=False))
print("classified:", int((new.phase != "Unclassified").sum()), "unclassified:", int((new.phase == "Unclassified").sum()), "sum:", int(t2["count"].sum()))

# row-by-row against phase assigned on OLD text (v2 result)
m = new[["filename", "phase", "sum24Hr"]].merge(old[["filename", "sum24hr"]], on="filename")
m["phase_oldtext"] = m["sum24hr"].fillna("").str.strip().map(C.classify_ddr)
ch = m[m.phase != m.phase_oldtext]
print("phase differs between old text and new text:", len(ch))
moji = m["sum24hr"].fillna("").str.contains("[ÃÂ]", regex=True) | (m["sum24hr"].fillna("").str.strip() != m["sum24Hr"].fillna("").str.strip())
print("rows whose stripped narrative text differs old vs new:", int(moji.sum()), "| of which phase changes:", int((moji & (m.phase != m.phase_oldtext)).sum()))
print(ch[["filename", "phase_oldtext", "phase"]].to_string())
ch.rename(columns={"sum24Hr": "text_new", "sum24hr": "text_old"}).to_csv("outputs/stage4_phase_changes_mojibake.csv", index=False)   # columns named text_*: the file is empty (0 phase changes) and must never carry narrative text

# is any DDR classified only through the 8½ pattern (suspected dead pattern)?
pat = re.compile(r"8½.{0,5}(?:hole|section)", re.I)
print("narratives containing literal '8½' + hole/section (pre-normalisation):", int(new.sum24Hr.fillna("").str.contains(r"8½.{0,5}(?:hole|section)", regex=True, case=False).sum()))
