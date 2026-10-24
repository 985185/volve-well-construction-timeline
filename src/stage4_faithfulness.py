"""Stage 4b: prove the ported classifier v3 is faithful: run it on the OLD volve_ddr_master narratives and compare with the old results."""
import sys
import pandas as pd
sys.path.insert(0, "src")
from classifier_v3 import classify_ddr

old = pd.read_parquet("data/interim/old/volve_ddr_master.parquet")
oldc = pd.read_parquet("data/interim/old/volve_ddr_classified.parquet")
tbl = pd.read_csv("inputs/repo_before/data/phase_distribution.csv")   # v2 per-phase counts
old["phase_port"] = old["sum24hr"].fillna("").str.strip().map(classify_ddr)
cnt = old.phase_port.value_counts()
n_class = int((old.phase_port != "Unclassified").sum())
print("classified:", n_class, "unclassified:", int((old.phase_port == "Unclassified").sum()), "total", len(old))
cmp = tbl.set_index("phase")["count"].to_frame("v2_table").join(cnt.rename("ported_on_old_text"), how="outer").fillna(0).astype(int)
cmp["same"] = cmp.v2_table == cmp.ported_on_old_text
print(cmp.to_string())
m = old[["filename", "phase_port"]].merge(oldc[["filename", "phase"]], on="filename")
bad = m[m.phase_port != m.phase]
print("row-by-row vs workspace.default.volve_ddr_classified: rows", len(m), "mismatches", len(bad))
print(bad.head(10).to_string())
cmp.to_csv("outputs/stage4_faithfulness_phase_counts.csv")
ok = n_class == 1303 and cmp.same.all() and len(bad) == 0
print("FAITHFUL:", ok)
sys.exit(0 if ok else 1)
