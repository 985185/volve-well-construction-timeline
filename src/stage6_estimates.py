"""Stage 6b: audit estimates from the author's original 50 calls, read from the published adjudication file outputs/audit_adjudications.csv
(filename, wellbore, date, stratum, call, miss_reason; no narrative text). The file is an input here and is not rewritten (see stage6_publish_adjudications.py)."""
import math, re, sys
import pandas as pd

TOTAL, CLASSIFIED, FRAME = 1759, 1303, 383
a = pd.read_csv("outputs/audit_adjudications.csv", keep_default_na=False)
assert len(a) == 50 and a.filename.is_unique

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

checks = {"26/50": k == 26 and n == 50, "23/39": (pc * 39).round() == 23, "3/11": (pp * 11).round() == 3, "miss 9/10/7": (mr.get("NO_HOLE_SIZE"), mr.get("OTHER_MISS"), mr.get("NONSTANDARD_TERMINOLOGY")) == (9, 10, 7),
          "Wilson 0.385-0.652": (round(lo, 3), round(hi, 3)) == (0.385, 0.652), "rate 85.4": round(100 * rate, 1) == 85.4, "CI 82.5-88.3": (round(100 * rlo, 1), round(100 * rhi, 1)) == (82.5, 88.3),
          "weighted 85.3": round(100 * ratew, 1) == 85.3, "floor 4.2": round(100 * floor, 1) == 4.2, "frame 383, 296+87": N == {"construction_era": 296, "production_era": 87}}
print(checks); sys.exit(0 if all(checks.values()) else 1)
