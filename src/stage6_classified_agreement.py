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
m[["record_id", "wellbore", "date", "assigned_phase_display", "my_phase", "my_note", "category"]].rename(columns={"assigned_phase_display": "assigned_phase"}).sort_values("record_id").to_csv("outputs/classified_audit_agreement.csv", index=False, lineterminator="\n")
