"""Stage 7a: total depth validation, all 26 WITSML wellbores vs NOD FactPages snapshot 2026-10-24.
Matching rule: (1) exact NOD name; (2) technical sidetrack (WITSML name ending T2) is matched to the NOD record in the same well family whose TD agrees within the exact tolerance,
preferring the parent designation; the WITSML parent leg whose NOD record was claimed that way is reported UNMATCHED (abandoned parent leg). Exact tolerance: |diff| <= 0.5 m."""
import re
import pandas as pd

TOL = 0.5
tl = pd.read_csv("outputs/timeline.csv")
wit = tl.groupby("wellbore").md_m.max().rename("witsml_max_md_m").reset_index()
nod = pd.concat([pd.read_csv(f"data/raw/nod/wellbore_{k}_all_20261024.csv", encoding="utf-8-sig", dtype=str) for k in ["development", "exploration"]])
nod = nod[nod.wlbWellboreName.str.contains(r"15/9-F-|15/9-19", regex=True)].copy()
nod["td"] = pd.to_numeric(nod.wlbTotalDepth, errors="coerce")
nodtd = nod.set_index("wlbWellboreName").td
fam = lambda n: re.match(r"(15/9-(?:F-\d+|19))", n).group(1)
wit["name"] = wit.wellbore.str.replace(r"^NO ", "", regex=True)
is_t2 = wit.name.str.contains(r"T2$")
claimed = {}                                              # NOD record -> WITSML T2 wellbore
for r in wit[is_t2].itertuples():
    f = fam(r.name); parent = re.sub(r"\s*T2$", "", r.name) if r.name.endswith(" T2") else re.sub(r"T2$", "", r.name)
    cands = [n for n in nodtd.index if fam(n) == f and pd.notna(nodtd[n]) and abs(nodtd[n] - r.witsml_max_md_m) <= TOL and n not in claimed]
    cands.sort(key=lambda n: (n != parent, n))              # parent designation first
    if cands: claimed[cands[0]] = r.wellbore
rows = []
for r in wit.itertuples():
    t2 = [n for n, w in claimed.items() if w == r.wellbore]
    if t2: n, how = t2[0], "T2 sidetrack matched to NOD record with agreeing TD"
    elif r.name in nodtd.index and r.name not in claimed: n, how = r.name, "name"
    else: n, how = None, "unmatched (NOD record of this name claimed by its technical sidetrack)" if r.name in nodtd.index else "unmatched (no NOD record)"
    td = nodtd[n] if n else None
    diff = abs(td - r.witsml_max_md_m) if n else None
    out = "UNMATCHED" if n is None else ("EXACT" if diff <= TOL else "CLOSE_NOT_EXACT")
    rows.append(dict(witsml_wellbore=r.wellbore, witsml_max_md_m=r.witsml_max_md_m, nod_wellbore=n, nod_total_depth_m=td, match_method=how, diff_m=None if n is None else round(diff, 1), outcome=out))
res = pd.DataFrame(rows); res.to_csv("outputs/td_validation.csv", index=False)
print(res.drop(columns="match_method").to_string(index=False))
c = res.outcome.value_counts().to_dict(); print(c, "| matched:", int((res.outcome != "UNMATCHED").sum()), "| total", len(res))
used = set(res.nod_wellbore.dropna()); print("NOD Volve records:", len(nodtd), "used:", len(used), "not matched:", sorted(set(nodtd.index) - used))
# comparison with v2 table
v2 = pd.read_csv("inputs/repo_before/data/td_validation.csv").rename(columns={"agreement": "v2_outcome"})
m = res.merge(v2[["witsml_wellbore", "witsml_max_md_m", "nod_wellbore_matched", "nod_total_depth_m", "diff_m", "v2_outcome"]], on="witsml_wellbore", suffixes=("", "_v2"))
m["v2_outcome"] = m.v2_outcome.replace({"CLOSE_NOT_EXACT": "CLOSE_NOT_EXACT"})
bad = m[(m.outcome != m.v2_outcome) | (m.witsml_max_md_m != m.witsml_max_md_m_v2) | (m.nod_wellbore.fillna("") != m.nod_wellbore_matched.fillna("")) | (m.nod_total_depth_m.fillna(-1) != m.nod_total_depth_m_v2.fillna(-1))]
print("rows differing from v2 td_validation.csv:", len(bad)); print(bad.to_string() if len(bad) else "")
