"""Stage 8b: kick-off depth for the 15 sidetracks under TJ's uniform rule (decisions 27, 32):

  "the depth at which the narrative first reports new formation or departure from the parent hole; where none is stated, the depth at which the kick-off or
   window is started; where the narrative is empty, the measured depth at the parent-to-child transition (DEPTH_SEQUENCE)."

Tier T1 = a depth is stated together with new-formation or departure language ("50% formation obtained at 1364 m", "kicked off at 3185m", "commenced drilling hole from 2911 m").
Tier T2 = the narrative names a kick-off / window / oriented-drilling start but no formation or departure depth: the start depth is used (window top for windows).
Tier T3 = the narrative is empty: measured depth at the parent-to-child transition.
Method wording (decision 33): 'depth in text' | 'event in text, depth from md' | 'depth sequence (narrative empty)'.

The choice of evidence report and depth per sidetrack is a reading of the narratives (SPEC). This script verifies the depth occurs in that report (text or md field), cuts the
evidence quote (15 words or fewer) from the raw narrative, and compares with NOD and with the previous version of this table.
"""
import os
import re
import pandas as pd

d = pd.read_parquet("data/interim/ddr.parquet")
d["day"] = d.date_report.str[:10]
d["mdn"] = pd.to_numeric(d.md, errors="coerce")
nod = pd.concat([pd.read_csv(f"data/raw/nod/wellbore_{k}_all_20261024.csv", encoding="utf-8-sig", dtype=str) for k in ["development", "exploration"]]).set_index("wlbWellboreName")
v2 = pd.read_csv("inputs/repo_before/data/sidetrack_relationships.csv").set_index("wellbore").kickoff_depth_m
prev = pd.read_csv("outputs/kickoff_table.csv").set_index("sidetrack").ddr_kickoff_depth_m if os.path.exists("outputs/kickoff_table.csv") else None

DT, EV, DS = "depth in text", "event in text, depth from md", "depth sequence (narrative empty)"
# sidetrack, parent, depth, evidence wellbore, evidence day, token (None = md field), method, tier, NOD record, confidence, v2 status, alternatives, note
SPEC = [
    ("15/9-19 A", "none in WITSML (NOD lists 15/9-19 S)", 2178, "15/9-19 A", "1997-07-29", "2178-2183", DT, "T2", "15/9-19 A", "HIGH", "NEW (absent from v2 table)",
     "2183 (window bottom)", "window top; a first window (2202-2207 m, 1997-07-26) was abandoned"),
    ("15/9-19 B", "15/9-19 A", 2231, "15/9-19 B", "1997-11-11", "2231M", DT, "T1", "15/9-19 B", "HIGH", "SAME", "", ""),
    ("15/9-19 BT2", "15/9-19 B", 2911, "15/9-19 B", "1997-12-06", "2911", DT, "T1", None, "HIGH", "SAME", "2903 (top of sidetrack plug)", "NOD has no separate record (its 15/9-19 B record is the B leg)"),
    ("15/9-19 ST2", "15/9-19 S", 1536, "15/9-19 S", "1992-12-19", None, DS, "T3", "15/9-19 SR", "LOW", "SAME", "1486 (parent drilled cement to 1,486 m the day before)", "both reports of 1992-12-19 read 'None'"),
    ("15/9-F-1 A", "15/9-F-1", 2620, "15/9-F-1", "2013-08-24", None, EV, "T2", "15/9-F-1 A", "MEDIUM",
     "NOT A KICK-OFF: 3,004 m is the depth reached on the first F-1 A report (8 1/2 in. hole drilled to 3,004 m)", "", "event named in the parent's last report; md 2620"),
    ("15/9-F-1 B", "15/9-F-1 A", 2617, "15/9-F-1 A", "2013-08-30", None, EV, "T2", "15/9-F-1 B", "MEDIUM",
     "NOT A KICK-OFF: SECTION START (3,100 m = 3 m of new formation below the 9 5/8 in. shoe track, then FIT)", "", "event named in the parent's last report; md 2617"),
    ("15/9-F-1 C", "15/9-F-1 B", 1364, "15/9-F-1 B", "2014-02-22", "1364", DT, "T1", "15/9-F-1 C", "HIGH",
     "NOT A KICK-OFF: SECTION START (3,059 m = start of 8 1/2 in. section)", "1355 (start of time drilling)", "new formation (50%) first reported at 1364 m"),
    ("15/9-F-9 A", "15/9-F-9", 421.5, "15/9-F-9", "2009-06-30", "421,5", DT, "T2", "15/9-F-9 A", "HIGH",
     "NOT A KICK-OFF: 459 m is where the first F-9 A report starts drilling, below the window (window 421.5 to 428.2 m)", "428.2 (window bottom); 436.5 (formation drilled to, 2009-07-02)", "window top"),
    ("15/9-F-11 T2", "15/9-F-11", 246, "15/9-F-11", "2013-03-23", "246", DT, "T2", None, "MEDIUM", "CHANGED BY RULE (v2 257 m = hand-over depth)", "257 (hand-over depth, 2013-03-24)",
     "start of oriented drilling out of the cement (TOC 244 m); NOD has no separate record"),
    ("15/9-F-11 A", "15/9-F-11 T2", 2586, "15/9-F-11 T2", "2013-05-15", "2586m", DT, "T1", "15/9-F-11 A", "HIGH", "SAME", "", ""),
    ("15/9-F-11 B", "15/9-F-11 A", 2589, "15/9-F-11 A", "2013-05-29", "2589", DT, "T1", "15/9-F-11 B", "LOW",
     "NOT A KICK-OFF: SECTION START (3,271 m = 8 1/2 in. section start after the 9 5/8 x 10 3/4 in. casing)", "2531 (start of the cement and new-formation interval)",
     "new formation reported by 2589 m; evidence is an interval 2531 to 2589 m"),
    ("15/9-F-15 A", "15/9-F-15", 1381, "15/9-F-15", "2008-12-12", "1381", DT, "T1", "15/9-F-15 A", "HIGH", "SAME", "1368 (start of the cement/new-formation interval)", ""),
    ("15/9-F-15 B", "15/9-F-15 A", 3185, "15/9-F-15 A", "2009-01-14", "3185m", DT, "T1", "15/9-F-15 B", "HIGH", "SAME", "3210 (depth of the first '50/50 cement/formation' report)", ""),
    ("15/9-F-15 C", "15/9-F-15 B", 2566, "15/9-F-15 B", "2009-01-19", "2566", DT, "T2", "15/9-F-15 C", "MEDIUM", "SAME", "2575 (depth the section reached; the NOD value)",
     "kick-off initiated after cement drilled to 2566 m"),
    ("15/9-F-15 D", "15/9-F-15 C", 1380, "15/9-F-15 C", "2013-11-11", None, EV, "T2", "15/9-F-15 D", "MEDIUM", "SAME", "", "parent set kick-off plug 2013-11-10; child's first report says 'kicked off' without a depth"),
]
CUE = re.compile(r"kick|whip.?stock|window|time drill|% formation|transferred|sidetrack", re.I)


def cut_quote(text, token):
    toks = " ".join(text.split()).split()
    if token:
        rx = re.compile(r"(?<![\d.,])" + re.escape(token) + r"(?!\d)")
        for i, t in enumerate(toks):
            if rx.search(t):
                return " ".join(toks[max(0, i - 7): i + 8])
        return None
    for i, t in enumerate(toks):
        if CUE.search(t):
            return " ".join(toks[max(0, i - 4): i + 11])
    return ""


rows = []
for st, par, depth, ew, eday, tok, method, tier, nrec, conf, v2s, alt, note in SPEC:
    key = "NO " + st
    rep = d[(d.wellbore == "NO " + ew) & (d.day == eday)]
    assert len(rep) == 1, (st, ew, eday, len(rep))
    r = rep.iloc[0]
    if method == DT:
        q = cut_quote(r.sum24Hr, tok); assert q, (st, "token not found in narrative")
    elif method == EV:
        assert abs(r.mdn - depth) < 1, (st, "md field does not equal depth", r.mdn)
        q = cut_quote(r.sum24Hr, None)
        if st == "15/9-F-15 D":                    # the event wording is in the child's first report; the depth is the parent's md
            q = cut_quote(d[(d.wellbore == key) & (d.day == eday)].iloc[0].sum24Hr, None)
        assert q, (st, "no kick-off wording found")
    else:
        c = d[(d.wellbore == key) & (d.day == eday)].iloc[0]
        assert r.mdn == c.mdn == depth, (st, r.mdn, c.mdn)
        q = "(narratives of both 1992-12-19 reports are 'None'; md 1,536 on both)"
    n = nod.loc[nrec, "wlbKickOffPoint"] if nrec else None
    n = None if (n is None or pd.isna(n)) else float(n)
    v = v2.get(key)
    rows.append(dict(sidetrack=st, parent=par, ddr_kickoff_depth_m=depth, rule_tier=tier, method=method, evidence_wellbore=ew, evidence_date=eday, evidence_quote=q, confidence=conf,
                     nod_wlbKickOffPoint_m=n, nod_minus_ddr_m=None if n is None else round(n - depth, 1), v2_depth_m=None if pd.isna(v) else float(v), v2_status=v2s,
                     alternative_depths=alt, note=note))
t = pd.DataFrame(rows)
assert (t.evidence_quote.str.split().str.len() <= 15).all()
t.to_csv("outputs/kickoff_table.csv", index=False)
pd.set_option("display.width", 250, "display.max_colwidth", 60)
print(t[["sidetrack", "ddr_kickoff_depth_m", "rule_tier", "method", "evidence_date", "nod_wlbKickOffPoint_m", "nod_minus_ddr_m", "confidence"]].to_string(index=False))
print(t.method.value_counts().to_dict(), t.rule_tier.value_counts().to_dict())
if prev is not None:
    ch = t.set_index("sidetrack").ddr_kickoff_depth_m.compare(prev) if False else [(s, prev[s], x) for s, x in t.set_index("sidetrack").ddr_kickoff_depth_m.items() if prev[s] != x]
    print("rows whose depth changed versus the previous table:", ch)
s19 = d[d.wellbore == "NO 15/9-19 S"]
print("19 S structured mdKickoff:", sorted(set(s19.md_kickoff.dropna())), "in", int(s19.md_kickoff.notna().sum()), "of", len(s19), "DDRs; NOD 19 S wlbKickOffPoint:", nod.loc["15/9-19 S", "wlbKickOffPoint"])
