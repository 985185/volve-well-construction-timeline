"""Stage 8 open item 1: every 15/9-F-1 C DDR with md and the first 300 characters of the narrative (full list in local_private/ only; the committed CSV has depths, no text)."""
import os
import pandas as pd
d = pd.read_parquet("data/interim/ddr.parquet"); d["day"] = d.date_report.str[:10]; d["mdn"] = pd.to_numeric(d.md, errors="coerce")
c = d[d.wellbore == "NO 15/9-F-1 C"].sort_values("day")
c[["day", "filename", "md"]].rename(columns={"day": "date"}).to_csv("outputs/stage8_f1c_depths.csv", index=False)
os.makedirs("local_private", exist_ok=True)
with open("local_private/stage8_f1c_ddrs.md", "w", encoding="utf-8") as f:
    for r in c.itertuples(): f.write(f"{r.day} | {r.filename} | md={r.md} | {' '.join(r.sum24Hr.split())[:300]}\n")
pre = c[c.day < "2014-03-13"]
print("F-1 C DDRs:", len(c), "| before 2014-03-13:", len(pre), "| md < 3059:", int((pre.mdn < 3059).sum()), "| md == 3059:", int((pre.mdn == 3059).sum()), "| md > 3059:", int((pre.mdn > 3059).sum()))
print("first DDR", c.day.min(), "md", c.md.iloc[0], "| last pre-03-13 DDR", pre.day.max(), "| 03-13 md", c[c.day == "2014-03-13"].md.iloc[0])
print("shallowest md in F-1 C:", c.mdn[c.mdn > 0].min(), "| DDRs with md < 3059 in the whole wellbore:", int(((c.mdn > 0) & (c.mdn < 3059)).sum()))
b = d[(d.wellbore == "NO 15/9-F-1 B")].sort_values("day").iloc[-1]
print("F-1 B last DDR:", b.day, "md", b.md, "| same-day F-1 C DDR md:", c[c.day == b.day].md.iloc[0])
