"""Stage 3: data quality survey on data/interim/ddr.parquet (raw strings). Writes outputs/stage3_*.csv."""
import collections
import pandas as pd

d = pd.read_parquet("data/interim/ddr.parquet")
N = len(d)
s = lambda c: d[c].fillna("").str.strip()
num = pd.to_numeric(d["md"], errors="coerce")

# --- Table 1: population by column (v2 convention: placeholders and literal "None" narratives are not populated)
rows = []
def add(col, label, mask, note=""):
    rows.append((label, round(100 * mask.sum() / N, 2), int(mask.sum()), note))
add("date_report", "date_report", s("date_report") != "")
add("dTimSpud", "spud_date (dTimSpud)", s("dTimSpud") != "")
add("rig", "rig (NPD Name alias)", s("rig") != "", "1 record missing (1980 sentinel)")
add("forecast24hr", "forecast24hr (genuine)", (s("forecast24hr") != "") & (s("forecast24hr") != "None"), f"{int((s('forecast24hr')=='None').sum())} literal \"None\" strings excluded")
add("operator", "operator", s("operator") != "")
add("md_csg_last", "md_csg_last_m", s("md_csg_last") != "")
add("sum24Hr", "sum24Hr (genuine narrative)", (s("sum24Hr") != "") & (s("sum24Hr") != "None"), f"{int((s('sum24Hr')=='None').sum())} literal None excluded")
add("drill_complete", "drill_complete", s("drill_complete") != "")
add("md", "md_m (excluding sentinel and zero)", (s("md") != "") & (s("md") != "-999.99") & (num != 0))
add("md_kickoff", "md_kickoff_m", s("md_kickoff") != "")
t1 = pd.DataFrame(rows, columns=["Column", "Populated_%", "Count", "Notes"])
t1.to_csv("outputs/stage3_table1_field_population.csv", index=False)
print(t1.to_string(index=False))

# --- placeholders in depth fields
print("\nDEPTH PLACEHOLDERS")
for c in ["md", "md_kickoff", "md_csg_last"]:
    v = s(c); n = pd.to_numeric(d[c], errors="coerce")
    print(f"{c}: blank/absent={int((v=='').sum())}  '-999.99'={int((v=='-999.99').sum())}  exactly '0'={int((v=='0').sum())}  numeric==0={int((n==0).sum())}  other non-numeric={int((n.isna() & (v!='')).sum())}  negative(non-sentinel)={int(((n<0)&(v!='-999.99')).sum())}")
print("md distinct zero-like strings:", collections.Counter(v for v in s('md') if v and float(v) == 0))
print("md populated arithmetic:", N, "-", int((s('md')=='-999.99').sum()), "-", int((num==0).sum()), "=", N - int((s('md')=='-999.99').sum()) - int((num==0).sum()), "| rows with a usable md:", int(((num>0)).sum()))

# --- literal "None" values in every text field
print("\nLITERAL None (after strip):", {c: int((s(c) == "None").sum()) for c in ["well","wellbore","sum24Hr","forecast24hr","operator","rig","drill_complete"]})
print("sum24Hr None & forecast24hr None both:", int(((s('sum24Hr')=='None') & (s('forecast24hr')=='None')).sum()))

# --- Unicode survey
print("\nUNICODE SURVEY (DDRs / occurrences)")
rows = []
for ch in ["½", "¼", "¾", "⅛"]:
    for c in ["sum24Hr", "forecast24hr"]:
        t = d[c].fillna("")
        rows.append((ch, c, int(t.str.contains(ch, regex=False).sum()), int(t.str.count(ch).sum())))
u = pd.DataFrame(rows, columns=["char", "field", "ddrs", "occurrences"]); u.to_csv("outputs/stage3_unicode_survey.csv", index=False); print(u.to_string(index=False))
allna = collections.Counter(ch for c in ["sum24Hr","forecast24hr"] for t in d[c].dropna() for ch in t if ord(ch) > 127)
print("all non-ASCII chars in narratives:", {k: v for k, v in allna.most_common()})
print("ddrs with any ½/¼ in sum24Hr:", int(d.sum24Hr.fillna('').str.contains('[½¼]').sum()), "| ½ or ¼ or ¾ or ⅛ any:", int(d.sum24Hr.fillna('').str.contains('[½¼¾⅛]').sum()))
print("non-ASCII in other string fields:", {c: int(d[c].fillna('').map(lambda x: any(ord(k)>127 for k in x)).sum()) for c in ["well","wellbore","operator","rig"]})

# --- date sentinels
print("\nDATE CHECKS")
dr = pd.to_datetime(d.date_report.str[:10], errors="coerce"); sp = pd.to_datetime(d.dTimSpud.str[:10], errors="coerce")
print("unparseable date_report:", int(dr.isna().sum()), "| unparseable dTimSpud:", int(sp.isna().sum()))
print("date_report year counts <1990:", dr[dr.dt.year < 1990].dt.year.value_counts().to_dict(), "| max:", dr.max().date(), "| min:", dr.min().date())
print("dTimSpud year min/max:", sp.min().date(), sp.max().date())
first = d.assign(dr=dr).groupby("wellbore").dr.agg(["min", "max"])
print("round-number dates (Jan 1) in date_report:", d[d.date_report.str[5:10] == "01-01"][["filename", "wellbore", "date_report"]].to_string(index=False))
print("dTimSpud 01-01:", d[d.dTimSpud.str[5:10] == "01-01"].groupby("wellbore").size().to_dict())
# gaps: wellbores whose first DDR is long before the next
g = d.assign(dr=dr).sort_values(["wellbore","dr"]); g["gap"] = g.groupby("wellbore").dr.diff().dt.days
print("gaps >365 days between consecutive DDRs in a wellbore:", g[g.gap > 365][["wellbore","filename","gap"]].to_string(index=False))
# spud per wellbore (distinct dTimSpud) vs first DDR
sw = d.assign(dr=dr, sp=sp).groupby("wellbore").agg(first_ddr=("dr","min"), n_spud=("sp","nunique"), spud_min=("sp","min"), spud_max=("sp","max"))
sw["spud_minus_first_days"] = (sw.spud_min - sw.first_ddr).dt.days
print(sw.to_string())
sw.to_csv("outputs/stage3_spud_vs_first_ddr.csv")
print("DDRs dated before the wellbore's dTimSpud:", int((dr < sp).sum()), "| after drill_complete:", int((dr > pd.to_datetime(d.drill_complete, errors='coerce')).sum()))

# --- placeholder register: every extracted field (TJ decision 3)
print("\nPLACEHOLDER REGISTER")
fields = ["well", "wellbore", "date_report", "dTimSpud", "md", "md_kickoff", "md_csg_last", "rig", "operator", "forecast24hr", "drill_complete", "sum24Hr"]
depth = {"md", "md_kickoff", "md_csg_last"}
generic = r"^(?:none|null|n/?a|nan|-+|\.+|-999(?:\.99?)?|-9999(?:\.9+)?)$"
sentinel_date = d.date_report.str[:4] == "1980"
reg = []
for c in fields:
    raw, v = d[c], d[c].fillna("")
    st = v.str.strip()
    nonn = pd.to_numeric(raw, errors="coerce")
    row = {"field": c,
           "literal_None": int((st == "None").sum()),
           "sentinel_-999.99": int((st == "-999.99").sum()),
           "zero_depth": int((st == "0").sum()) if c in depth else 0,
           "empty_but_present": int((raw.notna() & (st == "")).sum()),
           "date_sentinel_1980": int(sentinel_date.sum()) if c == "date_report" else 0}
    row["placeholder_cells"] = sum(row[k] for k in ["literal_None", "sentinel_-999.99", "zero_depth", "empty_but_present", "date_sentinel_1980"])
    row["absent_tag_not_counted"] = int(raw.isna().sum())
    other = st[st.str.lower().str.match(generic) & ~st.isin(["None", "-999.99"])]
    row["other_generic_placeholder_like"] = len(other)
    reg.append(row)
r = pd.DataFrame(reg); r.loc[len(r)] = ["TOTAL"] + [int(r[c].sum()) for c in r.columns[1:]]
r.to_csv("outputs/stage3_placeholder_register.csv", index=False); print(r.to_string(index=False))
anyph = (d[fields].apply(lambda col: col.fillna("").str.strip().isin(["None", "-999.99"]) | ((col.name in depth) & (col.fillna("").str.strip() == "0"))).any(axis=1)) | sentinel_date
print("DDRs with at least one placeholder cell:", int(anyph.sum()))
print("v2 411 = 331 + 7 + 73 =", 331 + 7 + 73, "| rerun cells sum of those three:", int(r.set_index('field').loc['TOTAL', ['sentinel_-999.99', 'zero_depth']].sum()) + int((s('sum24Hr') == 'None').sum()))
print("forecast genuine:", int(((s('forecast24hr') != '') & (s('forecast24hr') != 'None')).sum()), round(100 * int(((s('forecast24hr') != '') & (s('forecast24hr') != 'None')).sum()) / N, 4))
