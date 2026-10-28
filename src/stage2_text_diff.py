"""Stage 2c: classify every sum24hr / forecast24hr difference between new raw strings and the old master table."""
import os, sys
if not os.path.exists("data/interim/old/volve_ddr_master.parquet"):
    print("SKIPPED (optional verification step): data/interim/old/volve_ddr_master.parquet is not available, so the comparison with the earlier extraction cannot run. No reported number depends on running this step; its committed result is outputs/stage2_encoding_summary.json and reports/STAGE_2.md.")
    sys.exit(0)
import collections
import json
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

# committed result read by the registry (a comparison with the earlier table, so it is stored rather than recomputed from the earlier table)
_mm = new[["filename", "sum24Hr"]].merge(old[["filename", "sum24hr"]], on="filename")
n_enc = int(sum(1 for a, b in zip(_mm.sum24Hr.fillna(""), _mm.sum24hr.fillna("")) if (moji(b.strip()) == a.strip()) and moji(b) != b))
# one real before/after phrase (at most 10 words each side): the first file, in file-name order, whose earlier text holds the garbled one-half sign
_ex = None
for _r in _mm.sort_values("filename").itertuples():
    _o, _n = (_r.sum24hr or "").strip(), (_r.sum24Hr or "").strip()
    if "\u00c2\u00bd" in _o and moji(_o) == _n:
        _ow, _nw = _o.split(), _n.split(); _k = [i for i, w in enumerate(_ow) if "\u00c2\u00bd" in w][0]
        _ex = {"filename": _r.filename, "earlier_table": " ".join(_ow[max(0, _k - 4):_k + 2]), "raw_file": " ".join(_nw[max(0, _k - 4):_k + 2])}
        assert len(_ex["earlier_table"].split()) <= 10 and len(_ex["raw_file"].split()) <= 10
        break
json.dump({"sum24Hr_rows_with_encoding_error_in_earlier_table": n_enc, "rows_compared": len(_mm), "example": _ex}, open("outputs/stage2_encoding_summary.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("encoding-error rows in the earlier table (sum24Hr):", n_enc)
