"""Stage 8: build reports/STAGE_8.md from outputs/kickoff_recovery.csv (table rows are generated, not typed)."""
import pandas as pd

r = pd.read_csv("outputs/kickoff_recovery.csv")


def f(x, n=0):
    return "" if pd.isna(x) else f"{x:,.{n}f}"


lines = []
for x in r.itertuples():
    q = "" if pd.isna(x.evidence_quote) else "`" + x.evidence_quote.replace("|", "/") + "`"
    nm = "" if pd.isna(x.nod_kickoff_m) else f(x.nod_kickoff_m)
    df_ = "" if pd.isna(x.nod_minus_ours_m) else f"{x.nod_minus_ours_m:+,.0f}"
    off = "" if pd.isna(x.evidence_days_after_first_ddr) else int(x.evidence_days_after_first_ddr)
    ed = x.evidence_date if pd.notna(x.evidence_date) else ""
    lines.append(f"| {x.wellbore.replace('NO ', '')} | {x.method} | {f(x.kickoff_depth_m)} | {ed} | {off} | {q} | {x.confidence} | {nm} | {df_} |")
tbl = "\n".join(lines)
big = ", ".join(r[r.nod_minus_ours_m.abs() > 30].wellbore.str.replace("NO ", "").tolist())

txt = open("src/stage8_report_template.md", encoding="utf-8").read().replace("{{TABLE}}", tbl).replace("{{BIG}}", big)
open("reports/STAGE_8.md", "w", encoding="utf-8").write(txt)
print(len(txt), "|", big)
