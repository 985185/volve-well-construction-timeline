"""Stage 7c: check each v2 free-text spud/kick-off date against the raw DDR narrative of that day. Narrative snippets go to local_private/ only."""
import re
import pandas as pd

d = pd.read_parquet("data/interim/ddr.parquet"); d["day"] = d.date_report.str[:10]
r = pd.read_pickle("data/interim/spud_rows.pkl")
KW = r"spud|36\W{0,3}(?:\"|in|inch|hole|ho\b)|\b36\b|tagged|sea ?b|seabed|orient|kick|\bkop\b|whipstock|window|side.?track|steerable|hole opener"
out, ok, miss = [], 0, []
for x in r.itertuples():
    if x.freetext_date is None: continue
    row = d[(d.wellbore == x.wellbore) & (d.day == str(x.freetext_date))]
    if len(row) != 1: miss.append((x.wellbore, "no unique DDR on that date")); continue
    t = row.sum24Hr.iloc[0].strip(); hit = sorted({m.group(0).lower() for m in re.finditer(KW, t, re.I)})
    out.append(f"{x.wellbore} {x.freetext_date} filename={row.filename.iloc[0]} keywords={hit}\n  {t[:300]!r}\n")
    if hit: ok += 1
    else: miss.append((x.wellbore, "date exists but no spud/kick-off keyword in that day's narrative"))
open("local_private/stage7_spud_evidence.txt", "w", encoding="utf-8").write("\n".join(out))
n = int(r.freetext_date.notna().sum()); print("free-text dates:", n, "| DDR exists and narrative has a keyword:", ok, "| problems:", miss)
