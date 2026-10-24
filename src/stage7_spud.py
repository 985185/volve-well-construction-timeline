"""Stage 7b: spud date comparison across WITSML dTimSpud (W), first genuine DDR (F), free-text operational start (T) and NOD entry date (N).

v2 never coded its tolerances (the v2 manuscript carries a [TJ: define the tolerance] note). The rules below were derived from the v2 labels and per-row notes in
inputs/repo_before/data/spud_validation.csv. Applied in this order, first rule that fires wins. Days are calendar-date differences.
 N: the NOD pre-drill entry date where NOD records one (it marks the start of top-hole drilling, i.e. spud); otherwise the NOD main entry date (TJ ruling, decision 47).
    The rule does not look at any other date, so it cannot depend on the outcome. Anchor for the rules below: T if present, else F.
 R1 INHERITED     sidetrack whose W equals its parent wellbore's W.
 R5 SHARED_NOD    the NOD record used is one that TD matching assigned to a technical sidetrack (spans two WITSML legs):
                  the T2 leg is UNRESOLVED (not a like-for-like date); the parent leg is DEFINITIONAL_OFFSET only if it has no free-text
                  spud evidence of its own (T missing); a parent leg with its own free-text spud date goes on to R2 to R7 (v2: F-11 EXACT, 19 B DEFINITIONAL).
 R2 ERROR         |W - anchor| > 30 days and |N - anchor| <= 3 days (N and first report/free text agree, only W disagrees).
 R3 IDENTITY      |W - F| <= 7 days and |N - W| > 365 days (W consistent with own chronology, NOD date belongs to a different episode).
 R4 EXACT         |W - N| <= 1 day and 0 <= anchor - W <= 1 day.
 R6 DEFINITIONAL  |W - N| <= 8 days and 2 <= T - W <= 20 days (administrative start precedes operational start).
 R7 UNRESOLVED    everything else.

Offset used in the outputs and in Fig. 4 (one definition, TJ ruling 2): w_minus_n_days = W minus N, with N chosen by the pre-drill-else-main rule. Both NOD dates are kept as columns
(nod_main_entry_date, nod_predrill_entry_date) but no offset is computed from the main entry date.
"""
import re, sys
import pandas as pd

d = pd.read_parquet("data/interim/ddr.parquet")
d["day"] = pd.to_datetime(d.date_report.str[:10])
W = d.groupby("wellbore").dTimSpud.first().map(lambda s: pd.Timestamp(s[:10]))
assert (d.groupby("wellbore").dTimSpud.nunique() == 1).all()
F = d[d.date_report.str[:4] != "1980"].groupby("wellbore").day.min()
v2 = pd.read_csv("inputs/repo_before/data/spud_validation.csv")
v2["wb"] = v2.wellbore
def lead_date(s):
    m = re.match(r"\s*(\d{4}-\d{2}-\d{2})", str(s)); return pd.Timestamp(m.group(1)) if m else pd.NaT
T = v2.set_index("wb").freetext_spud_or_kickoff_date.map(lead_date)
src = v2.set_index("wb").freetext_source_type
T[T.index == "NO 15/9-19 A"] = pd.NaT          # v2 filled this with the NOD date (no free text exists)

nod = pd.concat([pd.read_csv(f"data/nod/wellbore_{k}_all_20261024.csv", encoding="utf-8-sig", dtype=str) for k in ["development", "exploration"]])
nod = nod[nod.wlbWellboreName.str.contains(r"15/9-F-|15/9-19", regex=True)].set_index("wlbWellboreName")
pdt = lambda s: pd.to_datetime(s, format="%d.%m.%Y", errors="coerce")
td = pd.read_csv("outputs/td_validation.csv")
nod_of = dict(zip(td.witsml_wellbore, td.nod_wellbore))                     # TD matching result
t2_claimed = {n: w for w, n in nod_of.items() if w.endswith("T2") and n}      # NOD record -> T2 wellbore
# spud rows follow v2 pairing: name match for spud, depth-matched record for T2 legs
pair = {w: ("15/9-" + w.split("15/9-")[1]) for w in W.index}
for w, n in nod_of.items():
    if w.endswith("T2") and n: pair[w] = n
pair["NO 15/9-F-11 T2"] = None                                                # NOD does not register T2 separately (v2)
parent = {"NO 15/9-F-11 A": "NO 15/9-F-11", "NO 15/9-F-11 T2": "NO 15/9-F-11"}
rows = []
for w in W.index:
    n = pair[w]; main = pdt(nod.loc[n, "wlbEntryDate"]) if n in nod.index else pd.NaT
    pre = pdt(nod.loc[n, "wlbEntryPreDrillDate"]) if (n in nod.index and "wlbEntryPreDrillDate" in nod.columns) else pd.NaT
    anchor = T[w] if pd.notna(T.get(w, pd.NaT)) else F[w]
    N, ntype = (pre, "predrill") if pd.notna(pre) else ((main, "main") if pd.notna(main) else (pd.NaT, "none"))
    Tw = T.get(w, pd.NaT)
    dWN = (W[w] - N).days if pd.notna(N) else None
    rows.append(dict(nod_main_entry_date=None if pd.isna(main) else main.date(), nod_predrill_entry_date=None if pd.isna(pre) else pre.date(), wellbore=w, witsml_spud=W[w].date(), first_ddr=F[w].date(), freetext_date=None if pd.isna(Tw) else Tw.date(), nod_entry_date=None if pd.isna(N) else N.date(), nod_entry_type=ntype, nod_record=n,
                     w_minus_n_days=dWN, w_minus_first_ddr_days=(W[w] - F[w]).days, anchor_minus_w_days=(anchor - W[w]).days, n_minus_anchor_days=None if pd.isna(N) else (N - anchor).days))
r = pd.DataFrame(rows)

def classify(x):
    w = x.wellbore; Wd = pd.Timestamp(x.witsml_spud); anchor_gap = x.anchor_minus_w_days
    if w in parent and W[w] == W[parent[w]]: return "INHERITED", "R1"
    if w.endswith("T2") and x.nod_record in t2_claimed: return "UNRESOLVED", "R5"
    if x.nod_record in t2_claimed and not w.endswith("T2") and pd.isna(x.freetext_date): return "DEFINITIONAL_OFFSET", "R5"
    if pd.notna(x.nod_entry_date):
        if abs(anchor_gap) > 30 and abs(x.n_minus_anchor_days) <= 3: return "ERROR", "R2"
        if abs(x.w_minus_first_ddr_days) <= 7 and abs(x.w_minus_n_days) > 365: return "IDENTITY", "R3"
        if abs(x.w_minus_n_days) <= 1 and 0 <= anchor_gap <= 1: return "EXACT", "R4"
        if pd.notna(x.freetext_date) and abs(x.w_minus_n_days) <= 8 and 2 <= anchor_gap <= 20: return "DEFINITIONAL_OFFSET", "R6"
    return "UNRESOLVED", "R7"
r[["category", "rule"]] = r.apply(lambda x: pd.Series(classify(x)), axis=1)
r.to_csv("outputs/spud_validation.csv", index=False)
pd.set_option("display.width", 250)
print(r[["wellbore", "witsml_spud", "first_ddr", "freetext_date", "nod_entry_date", "nod_entry_type", "w_minus_n_days", "category", "rule"]].to_string(index=False))

# compare with v2 labels
lab = {"EXACT_MATCH": "EXACT", "DEFINITIONAL_OFFSET": "DEFINITIONAL_OFFSET", "WITSML_ERROR": "ERROR", "WITSML_ERROR (structured field only)": "INHERITED", "WELLBORE_IDENTITY": "IDENTITY", "UNRESOLVED": "UNRESOLVED"}
m = r.merge(v2[["wellbore", "classification", "nod_date_used"]], on="wellbore"); m["v2"] = m.classification.map(lab)
print("\ncounts rerun:", r.category.value_counts().to_dict()); print("counts v2:   ", m.v2.value_counts().to_dict())
bad = m[m.category != m.v2]; print("rows whose category differs from v2:", len(bad)); print(bad[["wellbore", "category", "v2"]].to_string(index=False))
# N chosen vs v2 nod_date_used
chk = m.apply(lambda x: (str(x.nod_entry_date) in str(x.nod_date_used)) or (x.nod_entry_date is None), axis=1)
print("NOD date chosen is the date v2 used (or none):", int(chk.sum()), "of", len(m)); print(m[~chk][["wellbore", "nod_entry_date", "nod_date_used"]].to_string(index=False))
r.to_pickle("data/interim/spud_rows.pkl")
# the only category that differs from v2 is 15/9-F-11 (Exact in v2, Unresolved under the NOD pre-drill-else-main rule, decisions 47 and 48); any other difference fails
sys.exit(0 if set(bad.wellbore) <= {"NO 15/9-F-11"} else 1)
