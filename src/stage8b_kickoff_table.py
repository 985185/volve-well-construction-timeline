"""Stage 8b: kick-off depth re-derived under TJ's definition (decision 27): the depth at which the sidetrack leaves the parent wellbore.

Evidence is read from the parent's last report(s) and the sidetrack's first report(s): kick-off, window milling, time drilling, "% formation", hand-over language.
The choice of evidence report and depth per sidetrack is a reading of the narratives (listed in SPEC); this script verifies that the depth really occurs in that report
(narrative text or md field) and cuts the evidence quote (15 words or fewer) from the raw narrative. Method:
  FREE_TEXT       the depth is written in the narrative of the evidence report
  DEPTH_SEQUENCE  the depth is the measured depth (md field) of the parent's last report = the sidetrack's first report, with kick-off language in the narrative or none
"""
import re
import pandas as pd

d = pd.read_parquet("data/interim/ddr.parquet")
d["day"] = d.date_report.str[:10]
d["mdn"] = pd.to_numeric(d.md, errors="coerce")
nod = pd.concat([pd.read_csv(f"data/raw/nod/wellbore_{k}_all_20261024.csv", encoding="utf-8-sig", dtype=str) for k in ["development", "exploration"]]).set_index("wlbWellboreName")
v2 = pd.read_csv("inputs/repo_before/data/sidetrack_relationships.csv").set_index("wellbore").kickoff_depth_m

# sidetrack, parent, depth, evidence wellbore, evidence day, search token (None = md field), method, NOD record, confidence, v2 status, note
SPEC = [
    ("15/9-19 A", "none in WITSML (NOD lists 15/9-19 S)", 2178, "15/9-19 A", "1997-07-29", "2178-2183", "FREE_TEXT", "15/9-19 A", "HIGH", "NEW (absent from v2 table)", "second whipstock; first window (2202-2207 m, 1997-07-26) abandoned"),
    ("15/9-19 B", "15/9-19 A", 2231, "15/9-19 B", "1997-11-11", "2231M", "FREE_TEXT", "15/9-19 B", "HIGH", "SAME", ""),
    ("15/9-19 BT2", "15/9-19 B", 2911, "15/9-19 B", "1997-12-06", "2911", "FREE_TEXT", None, "HIGH", "SAME", "NOD has no separate record (its 15/9-19 B record is the B leg)"),
    ("15/9-19 ST2", "15/9-19 S", 1536, "15/9-19 S", "1992-12-19", None, "DEPTH_SEQUENCE", "15/9-19 SR", "LOW", "SAME", "both reports of 1992-12-19 are 'None'; parent drilled cement to 1486 m the day before"),
    ("15/9-F-1 A", "15/9-F-1", 2620, "15/9-F-1", "2013-08-24", None, "DEPTH_SEQUENCE", "15/9-F-1 A", "MEDIUM", "NOT A KICK-OFF: 3,004 m is the depth reached on the first F-1 A report (8 1/2 in. hole drilled to 3,004 m)", "cue 'kick off' in parent's last report; md 2620"),
    ("15/9-F-1 B", "15/9-F-1 A", 2617, "15/9-F-1 A", "2013-08-30", None, "DEPTH_SEQUENCE", "15/9-F-1 B", "MEDIUM", "NOT A KICK-OFF: SECTION START (3,100 m = 3 m of new formation below the 9 5/8 in. shoe track, then FIT)", "cue 'kicked off' in parent's last report; md 2617"),
    ("15/9-F-1 C", "15/9-F-1 B", 1364, "15/9-F-1 B", "2014-02-22", "1364", "FREE_TEXT", "15/9-F-1 C", "HIGH", "NOT A KICK-OFF: SECTION START (3,059 m = start of 8 1/2 in. section)", "TJ decision 27"),
    ("15/9-F-9 A", "15/9-F-9", 421.5, "15/9-F-9", "2009-06-30", "421,5", "FREE_TEXT", "15/9-F-9 A", "HIGH", "NOT A KICK-OFF: 459 m is where the first F-9 A report starts drilling, below the window (window 421.5 to 428.2 m)", "top of window; window bottom 428.2 m"),
    ("15/9-F-11 T2", "15/9-F-11", 257, "15/9-F-11", "2013-03-24", "257", "FREE_TEXT", None, "MEDIUM", "SAME", "oriented drilling out of the cement started at 246 m (2013-03-23); 257 m is the hand-over depth; NOD has no separate record"),
    ("15/9-F-11 A", "15/9-F-11 T2", 2586, "15/9-F-11 T2", "2013-05-15", "2586m", "FREE_TEXT", "15/9-F-11 A", "HIGH", "SAME", ""),
    ("15/9-F-11 B", "15/9-F-11 A", 2589, "15/9-F-11 A", "2013-05-29", "2589", "FREE_TEXT", "15/9-F-11 B", "LOW", "NOT A KICK-OFF: SECTION START (3,271 m = 8 1/2 in. section start after the 9 5/8 x 10 3/4 in. casing)", "evidence is an interval: cement and new formation drilled from 2531 to 2589 m; point value = new formation reached"),
    ("15/9-F-15 A", "15/9-F-15", 1381, "15/9-F-15", "2008-12-12", "1381", "FREE_TEXT", "15/9-F-15 A", "HIGH", "SAME", ""),
    ("15/9-F-15 B", "15/9-F-15 A", 3185, "15/9-F-15 A", "2009-01-14", "3185m", "FREE_TEXT", "15/9-F-15 B", "HIGH", "SAME", ""),
    ("15/9-F-15 C", "15/9-F-15 B", 2566, "15/9-F-15 B", "2009-01-19", "2566", "FREE_TEXT", "15/9-F-15 C", "MEDIUM", "SAME", "kick-off initiated after cement drilled to 2566 m; section then drilled to 2575 m (the NOD value)"),
    ("15/9-F-15 D", "15/9-F-15 C", 1380, "15/9-F-15 C", "2013-11-11", None, "DEPTH_SEQUENCE", "15/9-F-15 D", "MEDIUM", "SAME", "parent set kick-off plug 2013-11-10; child's first report says 'kicked off' without a depth"),
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
    for i, t in enumerate(toks):                       # cue sentence for depth-sequence rows
        if CUE.search(t):
            return " ".join(toks[max(0, i - 4): i + 11])
    return ""


rows = []
for st, par, depth, ew, eday, tok, method, nrec, conf, v2s, note in SPEC:
    key = "NO " + st
    rep = d[(d.wellbore == "NO " + ew) & (d.day == eday)]
    assert len(rep) == 1, (st, ew, eday, len(rep))
    r = rep.iloc[0]
    if method == "FREE_TEXT":
        q = cut_quote(r.sum24Hr, tok); assert q, (st, "token not found in narrative")
    else:
        q = cut_quote(r.sum24Hr, None)
        if st == "15/9-F-15 D":                        # cue sits in the child's first report; depth from the parent's md field
            c = d[(d.wellbore == key) & (d.day == eday)].iloc[0]; q = cut_quote(c.sum24Hr, None)
        assert abs(r.mdn - depth) < 1 or st == "15/9-19 ST2", (st, "md field does not equal depth", r.mdn)
        if st == "15/9-19 ST2":
            c = d[(d.wellbore == key) & (d.day == eday)].iloc[0]; assert r.mdn == c.mdn == 1536; q = "(narratives of both 1992-12-19 reports are 'None'; md 1,536 on both)"
    n = nod.loc[nrec, "wlbKickOffPoint"] if nrec else None
    n = None if (n is None or pd.isna(n)) else float(n)
    v = v2.get(key)
    rows.append(dict(sidetrack=st, parent=par, ddr_kickoff_depth_m=depth, method=method, evidence_wellbore=ew, evidence_date=eday, evidence_quote=q, confidence=conf,
                     nod_wlbKickOffPoint_m=n, nod_minus_ddr_m=None if n is None else round(n - depth, 1), v2_depth_m=None if pd.isna(v) else float(v), v2_status=v2s, note=note))
t = pd.DataFrame(rows)
assert (t.evidence_quote.str.split().str.len() <= 15).all()
t.to_csv("outputs/kickoff_table.csv", index=False)
pd.set_option("display.width", 250, "display.max_colwidth", 70)
print(t[["sidetrack", "ddr_kickoff_depth_m", "method", "evidence_date", "nod_wlbKickOffPoint_m", "nod_minus_ddr_m", "v2_depth_m", "confidence"]].to_string(index=False))
print(t.method.value_counts().to_dict(), "| not a kick-off in v2:", int(t.v2_status.str.startswith("NOT").sum()))
# 19 S report only
s19 = d[d.wellbore == "NO 15/9-19 S"]
print("19 S structured mdKickoff:", sorted(set(s19.md_kickoff.dropna())), "in", int(s19.md_kickoff.notna().sum()), "of", len(s19), "DDRs")
print("NOD wlbKickOffPoint, 19 series:", {k: nod.loc[k, "wlbKickOffPoint"] for k in nod.index if k.startswith("15/9-19")})
