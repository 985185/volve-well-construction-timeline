"""Stage 8: kick-off recovery, one row per sidetrack by designation (15). Method: FREE_TEXT (depth quoted in a DDR narrative near the hand-over), DEPTH_SEQUENCE
(depth taken from the parent's last / child's first measured depth), or NONE. Evidence quotes are <= 15 words; full narratives go to local_private/ only."""
import re, sys
import pandas as pd

d = pd.read_parquet("data/interim/ddr.parquet"); d["day"] = d.date_report.str[:10]; d["mdn"] = pd.to_numeric(d.md, errors="coerce")
v2 = pd.read_csv("inputs/repo_before/data/sidetrack_relationships.csv").set_index("wellbore")
nod = pd.concat([pd.read_csv(f"data/raw/nod/wellbore_{k}_all_20261024.csv", encoding="utf-8-sig", dtype=str) for k in ["development", "exploration"]]).set_index("wlbWellboreName")
td = pd.read_csv("outputs/td_validation.csv").set_index("witsml_wellbore")

SIDETRACKS = ["NO 15/9-19 A", "NO 15/9-19 B", "NO 15/9-19 BT2", "NO 15/9-19 ST2", "NO 15/9-F-1 A", "NO 15/9-F-1 B", "NO 15/9-F-1 C", "NO 15/9-F-9 A", "NO 15/9-F-11 A",
              "NO 15/9-F-11 B", "NO 15/9-F-11 T2", "NO 15/9-F-15 A", "NO 15/9-F-15 B", "NO 15/9-F-15 C", "NO 15/9-F-15 D"]
PARENT = {w: (v2.loc[w, "parent_wellbore"] if w in v2.index else None) for w in SIDETRACKS}
PARENT["NO 15/9-19 A"] = None
CUE = re.compile(r"kick|\bKOP\b|whip.?stock|window|side.?track|orient|steer|new hole|time drilling|commenc\w* drilling|drill\w* (?:new )?formation", re.I)
def forms(n): n = int(n); return rf"(?<![\d.,]){n}(?:[.,]\d)?(?!\d)|(?<![\d.,]){n // 1000},{n % 1000:03d}(?!\d)"
def snippet(text, depth):
    toks = text.split(); rx = re.compile(forms(depth))
    for i, t in enumerate(toks):
        if rx.search(t) or (i + 1 < len(toks) and rx.search(t + toks[i + 1])):
            return " ".join(toks[max(0, i - 7): i + 8])
    return None

rows, full = [], []
for w in SIDETRACKS:
    child = d[d.wellbore == w].sort_values("day"); par = d[d.wellbore == PARENT[w]].sort_values("day") if PARENT[w] else d.iloc[0:0]
    first_day = child[child.day > '1990'].day.iloc[0]; v2d = v2.loc[w, "kickoff_depth_m"] if w in v2.index else None
    v2d = None if pd.isna(v2d) else int(float(v2d))
    sv = sorted({float(x) for x in child.md_kickoff.dropna() if float(x) > 0})
    search_depth = v2d if v2d else (int(sv[0]) if len(sv) == 1 else None)    # 19 A: no v2 row, so the unique structured md_kickoff is the search depth
    scan = pd.concat([par.tail(5), child.head(30)])
    found = None
    if search_depth:
        for r in scan.itertuples():
            s = snippet(" ".join(r.sum24Hr.split()), search_depth)
            if s: found = (r, s, bool(CUE.search(r.sum24Hr))); break
    p_last = par.mdn[par.mdn > 0].iloc[-1] if len(par) and (par.mdn > 0).any() else None
    c_first = child.mdn[child.mdn > 0].iloc[0] if (child.mdn > 0).any() else None
    seq_match = bool(search_depth) and ((p_last is not None and abs(p_last - search_depth) < 1) or (c_first is not None and abs(c_first - search_depth) < 1))
    struct = sorted(set(child.md_kickoff.dropna())) if child.md_kickoff.notna().any() else []
    nk = nod.loc[w.replace("NO ", ""), "wlbKickOffPoint"] if w.replace("NO ", "") in nod.index else None
    nk = nod.loc[td.loc[w, "nod_wellbore"], "wlbKickOffPoint"] if (nk is None and isinstance(td.loc[w, "nod_wellbore"], str)) else nk
    offs = (pd.Timestamp(found[0].day) - pd.Timestamp(first_day)).days if found else None
    if found: method, ev = "FREE_TEXT", found
    elif seq_match: method, ev = "DEPTH_SEQUENCE", None
    else: method, ev = "NONE", None
    if found and offs > 5: conf = "CHECK"
    elif found and found[2] and (seq_match or struct): conf = "HIGH"
    elif found and found[2]: conf = "MEDIUM"
    elif found: conf = "LOW"
    elif seq_match: conf = "MEDIUM"
    else: conf = "NONE"
    rows.append(dict(wellbore=w, parent_in_v2=PARENT[w], v2_method=v2.loc[w, "kickoff_source"] if w in v2.index else "(row absent in v2)", v2_depth_m=v2d, method=method, kickoff_depth_m=search_depth if method != "NONE" else None, evidence_days_after_first_ddr=offs, nod_parent=nod.loc[td.loc[w, "nod_wellbore"], "wlbDiskosWellboreParent"] if isinstance(td.loc[w, "nod_wellbore"], str) else None,
                     evidence_date=ev[0].day if ev else None, evidence_file=ev[0].filename if ev else None, evidence_quote=ev[1] if ev else None, cue_in_narrative=ev[2] if ev else None,
                     parent_last_md=p_last, child_first_md=c_first, depth_sequence_match=seq_match, structured_md_kickoff="; ".join(struct), nod_kickoff_m=nk, confidence=conf))
    if ev: full.append(f"{w} {ev[0].day} {ev[0].filename}\n  {' '.join(ev[0].sum24Hr.split())[:300]}\n")
r = pd.DataFrame(rows)
r["nod_minus_ours_m"] = pd.to_numeric(r.nod_kickoff_m) - pd.to_numeric(r.kickoff_depth_m)
r.to_csv("outputs/kickoff_recovery.csv", index=False)
open("local_private/stage8_kickoff_evidence.txt", "w", encoding="utf-8").write("\n".join(full))
pd.set_option("display.width", 260, "display.max_colwidth", 80)
print(r[["wellbore", "v2_method", "v2_depth_m", "method", "kickoff_depth_m", "evidence_date", "evidence_days_after_first_ddr", "parent_last_md", "child_first_md", "structured_md_kickoff", "nod_kickoff_m", "nod_minus_ours_m", "nod_parent", "confidence"]].to_string(index=False))
print(r.method.value_counts().to_dict(), "| quotes over 15 words:", int((r.evidence_quote.dropna().str.split().str.len() > 15).sum()))
