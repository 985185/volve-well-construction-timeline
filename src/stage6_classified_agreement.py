"""Stage 6e: phase-label agreement between the author's blind labels and the classifier, from the filled workbook (argument 1, default outputs/classified_audit_filled.xlsx).
Categories: EXACT (my_phase equals the assigned phase), TIE (different label, but my_note names the assigned phase), NONE_FITS, DISAGREE. Prints counts overall and by phase and lists the non-exact rows.
Writes outputs/classified_audit_agreement.csv (record_id, wellbore, date, phase labels and category; no narrative text)."""
import sys, json
import pandas as pd

path = sys.argv[1] if len(sys.argv) > 1 else "outputs/classified_audit_filled.xlsx"
rv = pd.read_excel(path, sheet_name="review", keep_default_na=False); ky = pd.read_excel(path, sheet_name="key")
m = rv.merge(ky, on="record_id", validate="one_to_one"); assert len(m) == 52 and (m.my_phase.astype(str).str.strip() != "").all(), "every row needs a my_phase"
norm = lambda s: " ".join(str(s).strip().lower().replace("\u00bc", "1/4").split())
def cat(r):
    mine, key, note = norm(r.my_phase), norm(r.assigned_phase_display), norm(r.my_note)
    if mine == key: return "EXACT"
    if mine == "none fits": return "NONE_FITS"
    if key in note: return "TIE"
    return "DISAGREE"
m["category"] = m.apply(cat, axis=1)
n = len(m); c = m.category.value_counts().to_dict()
print("overall:", c, f"| exact {c.get('EXACT', 0)}/{n} = {c.get('EXACT', 0) / n:.3f}")
nf = c.get("NONE_FITS", 0); print(f"exact among rows with a label (excluding none fits): {c.get('EXACT', 0)}/{n - nf} = {c.get('EXACT', 0) / (n - nf):.3f}")
tb = pd.crosstab(m.assigned_phase_display, m.category).reindex(columns=["EXACT", "TIE", "NONE_FITS", "DISAGREE"], fill_value=0); print(tb.to_string())
print("rows with a note:", int((m.my_note.astype(str).str.strip() != "").sum()))
print("\nnon-exact rows (assigned | my_phase | note):")
for r in m[m.category != "EXACT"].itertuples(): print(f"  {r.category:9s} {r.record_id} | {r.assigned_phase_display} | {r.my_phase} | {r.my_note}")
# Causes of the 22 disagreements of the single-report blind audit: PROPOSED from reading each narrative (the author's note column was empty); to be confirmed by the author.
CAUSE = {**{k: "incidental keyword" for k in ["15_9_19_S_1992_11_29", "15_9_F_15_D_2016_07_27", "15_9_F_10_2009_05_18", "15_9_F_4_2008_02_08", "15_9_F_14_2008_06_19", "15_9_F_1_C_2014_03_21", "15_9_F_15_D_2013_12_30", "15_9_F_15_A_2008_12_23"]},
         **{k: "whipstock or window milling under Workover" for k in ["15_9_19_A_1997_07_25", "15_9_19_A_1997_07_26", "15_9_19_A_1997_07_29", "15_9_F_9_2009_07_02"]},
         **{k: "campaign context" for k in ["15_9_F_15_C_2013_10_14", "15_9_F_15_C_2013_10_23", "15_9_F_1_C_2016_10_22", "15_9_F_4_2008_03_22", "15_9_F_5_2012_09_16"]},
         **{k: "phase-scheme ambiguity" for k in ["15_9_F_12_2007_08_02", "15_9_F_1_B_2013_09_02"]},
         "15_9_19_ST2_1993_02_23": "mixed day",
         **{k: "unclear from the text (author to say)" for k in ["15_9_F_9_A_2009_07_08", "15_9_19_A_1997_10_21"]}}
m["cause_proposed"] = m.record_id.str.replace(".xml", "", regex=False).map(CAUSE).where(m.category != "EXACT", "")
assert (m.cause_proposed != "").sum() == (m.category != "EXACT").sum()
print("causes (proposed):",m[m.category != "EXACT"].cause_proposed.value_counts().to_dict())
m[["record_id", "wellbore", "date", "assigned_phase_display", "my_phase", "my_note", "category", "cause_proposed"]].rename(columns={"assigned_phase_display": "assigned_phase"}).sort_values("record_id").to_csv("outputs/classified_audit_agreement.csv", index=False, lineterminator="\n")

# Wilson interval and frequency-weighted agreement (phase agreement rates weighted by the phase's share of the 1,303 classified reports)
def wilson(k, n, z=1.96):
    p = k / n; den = 1 + z * z / n; ctr = (p + z * z / (2 * n)) / den; h = z * (p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5 / den
    return ctr - h, ctr + h
k = int((m.category == "EXACT").sum()); lo, hi = wilson(k, n)
print(f"\nsingle-report blind agreement {k}/{n} = {k / n:.4f}; Wilson 95% {lo:.4f} to {hi:.4f}")
pop = pd.read_parquet("data/interim/classified_new.parquet"); pop = pop[pop.phase != "Unclassified"]; assert len(pop) == 1303
DISP = {"Spud / Conductor": "Spud/Conductor", "Surface casing": "Surface hole and casing", "Intermediate drilling": "Intermediate drilling", "Intermediate casing": "Intermediate casing",
        "Reservoir drilling": "12¼ in. and smaller hole", "Liner / Casing run": "Liner/Casing run", "Cementing": "Cementing", "Completion": "Completion", "P&A": "P&A",
        "Logging / Testing": "Logging/Testing", "Workover": "Workover", "Waiting / Downtime": "Waiting/Downtime", "Rig move / Setup": "Rig move/Setup"}
share = pop.phase.map(DISP).value_counts(); rate = m.groupby("assigned_phase_display").category.apply(lambda s: (s == "EXACT").mean())
w = sum(share[ph] * rate[ph] for ph in share.index) / 1303
print("frequency-weighted agreement = sum(phase count x phase agreement rate) / 1,303 = " + " + ".join(f"{share[ph]}x{rate[ph]:.2f}" for ph in share.index) + f" / 1303 = {w:.4f}")
