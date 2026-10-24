"""Stage 2c: classify every sum24hr / forecast24hr difference between new raw strings and the old master table."""
import collections
import pandas as pd

new = pd.read_parquet("data/interim/ddr.parquet"); old = pd.read_parquet("data/interim/old/volve_ddr_master.parquet")
m = new.merge(old, on="filename", suffixes=("_n", "_o"))

def moji(s):  # old table text seen as UTF-8 bytes re-read as cp1252
    try: return s.encode("cp1252").decode("utf-8")
    except Exception: return s

out = []
for c, o in [("sum24Hr", "sum24hr"), ("forecast24hr", "forecast24hr")]:
    a = m[c if c != o else c + "_n"]; b = m[o if c != o else o + "_o"]
    cats = collections.Counter(); rows = []
    for fn, x, y in zip(m.filename, a, b):
        if pd.isna(x) and pd.isna(y): cat = "both null"
        elif pd.isna(x) or pd.isna(y): cat = "null vs value"
        elif x == y: cat = "identical"
        elif y == x.strip(): cat = "old stripped whitespace"
        elif moji(y) == x: cat = "old mojibake"
        elif moji(y) == x.strip(): cat = "old mojibake + stripped"
        else: cat = "UNEXPLAINED"
        cats[cat] += 1
        if cat not in ("identical", "both null"): rows.append((fn, c, cat))
    print(c, dict(cats)); out += rows
pd.DataFrame(out, columns=["filename", "field", "cause"]).to_csv("data/interim/old/diff_text_causes.csv", index=False)
# whitespace detail
for c in ["sum24Hr", "forecast24hr"]:
    s = m[c if c != c.lower() else c + "_n"].dropna()
    print(c, "new strings with leading/trailing whitespace:", int((s != s.str.strip()).sum()), "| 'None' literal:", int((s.str.strip() == "None").sum()), "| empty:", int((s.str.strip() == "").sum()))
