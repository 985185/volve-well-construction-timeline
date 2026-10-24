"""Stage 6b: audit estimates from TJ's original 50 calls (official adjudication). Writes outputs/audit_adjudications.csv with no narrative text."""
import math, re, sys
import pandas as pd

TOTAL, CLASSIFIED, FRAME = 1759, 1303, 383
adj = pd.read_csv("inputs/old_audit/audit_adjudicated.csv")
adj["day"] = adj.date_report.str[:10]
mp = pd.read_csv("data/interim/audit_old50_filename_map.csv")
a = adj.merge(mp[["filename", "wellbore", "day"]], on=["wellbore", "day"], how="left", validate="one_to_one")
assert a.filename.notna().all() and len(a) == 50
a["call"] = a.adjudication
a["miss_reason"] = a.miss_reason_if_construction.fillna("").str.split(":").str[0].str.strip()
pub = a[["filename", "wellbore", "day", "stratum", "call", "miss_reason"]].rename(columns={"day": "date"}).sort_values("filename")
pub.to_csv("outputs/audit_adjudications.csv", index=False)

def wilson(k, n, z=1.96):
    p = k / n; den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return c - h, c + h

n = len(a); k = int((a.call == "CONSTRUCTION").sum())
print("calls:", a.call.value_counts().to_dict(), "| by stratum:\n", pd.crosstab(a.stratum, a.call).to_string())
mr = a[a.call == "CONSTRUCTION"].miss_reason.value_counts().to_dict(); print("miss reasons:", mr, "sum", sum(mr.values()))
print("miss_reason present on NON_CONSTRUCTION rows:", int(((a.call != "CONSTRUCTION") & (a.miss_reason != "")).sum()))
p = k / n; lo, hi = wilson(k, n)
print(f"\nsample proportion {k}/{n} = {p:.4f}; Wilson 95% {lo:.4f} to {hi:.4f}")
sc = FRAME / TOTAL; obs = CLASSIFIED / TOTAL
print(f"scale {FRAME}/{TOTAL} = {sc:.4f}; observed {CLASSIFIED}/{TOTAL} = {obs:.4f}")
resid = p * sc; print(f"residual miss = {p:.3f} x {sc:.4f} = {resid:.4f} ({100*resid:.1f} pp, ~{p*FRAME:.0f} DDRs)")
rate = obs + resid; rlo, rhi = obs + lo * sc, obs + hi * sc
print(f"attainable rate = {obs:.4f} + {resid:.4f} = {rate:.4f} ({100*rate:.1f}%); CI {obs:.4f} + {lo:.4f} x {sc:.4f} = {rlo:.4f}, {obs:.4f} + {hi:.4f} x {sc:.4f} = {rhi:.4f} ({100*rlo:.1f} to {100*rhi:.1f}%)")
fr = pd.read_parquet("data/interim/audit_frame.parquet"); N = fr.stratum.value_counts().to_dict()
pc = ((a.stratum == "construction_era") & (a.call == "CONSTRUCTION")).sum() / (a.stratum == "construction_era").sum()
pp = ((a.stratum == "production_era") & (a.call == "CONSTRUCTION")).sum() / (a.stratum == "production_era").sum()
pw = (N["construction_era"] * pc + N["production_era"] * pp) / FRAME
ratew = obs + pw * sc
print(f"stratum-weighted: ({N['construction_era']}/{FRAME}) x {pc:.4f} + ({N['production_era']}/{FRAME}) x {pp:.4f} = {pw:.4f}; rate = {obs:.4f} + {pw:.4f} x {sc:.4f} = {ratew:.4f} ({100*ratew:.1f}%)")
floor = 73 / TOTAL; print(f"EMPTY_RECORD floor: 73/{TOTAL} = {floor:.4f} ({100*floor:.1f}%)")

# quote-length check on the published reasons (limit 15 words per quote)
long_q = [(r.filename, len(q.split())) for r in a.itertuples() for q in re.findall(r"'([^']{3,})'", str(r.reason)) if len(q.split()) > 15]
print("quoted fragments over 15 words in the old 'reason' text:", long_q)
checks = {"26/50": k == 26 and n == 50, "23/39": (pc * 39).round() == 23, "3/11": (pp * 11).round() == 3, "miss 9/10/7": (mr.get("NO_HOLE_SIZE"), mr.get("OTHER_MISS"), mr.get("NONSTANDARD_TERMINOLOGY")) == (9, 10, 7),
          "Wilson 0.385-0.652": (round(lo, 3), round(hi, 3)) == (0.385, 0.652), "rate 85.4": round(100 * rate, 1) == 85.4, "CI 82.5-88.3": (round(100 * rlo, 1), round(100 * rhi, 1)) == (82.5, 88.3),
          "weighted 85.3": round(100 * ratew, 1) == 85.3, "floor 4.2": round(100 * floor, 1) == 4.2, "frame 383, 296+87": N == {"construction_era": 296, "production_era": 87}}
print(checks); sys.exit(0 if all(checks.values()) else 1)
