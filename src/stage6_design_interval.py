"""Stage 6c: design-based estimate for the stratified audit (stratum-weighted proportion, finite-population correction, 95% interval) and the resulting recovery estimate.
Reads outputs/audit_adjudications.csv and data/interim/audit_frame.parquet; writes outputs/audit_design_interval.json. Arithmetic is printed."""
import json, math
import pandas as pd

TOTAL, CLASSIFIED, FRAME = 1759, 1303, 383
a = pd.read_csv("outputs/audit_adjudications.csv", keep_default_na=False)
N = pd.read_parquet("data/interim/audit_frame.parquet").stratum.value_counts().to_dict()
assert sum(N.values()) == FRAME and len(a) == 50
rows, p_st, var = {}, 0.0, 0.0
for h in ("construction_era", "production_era"):
    s = a[a.stratum == h]; n = len(s); k = int((s.call == "CONSTRUCTION").sum()); p = k / n; W = N[h] / FRAME; f = n / N[h]
    v = W * W * (1 - f) * p * (1 - p) / (n - 1)
    rows[h] = dict(N=N[h], n=n, k=k, p=p, W=W, f=f, var_term=v); p_st += W * p; var += v
    print(f"{h}: N={N[h]} n={n} k={k} p={p:.4f} W={W:.4f} f=n/N={f:.4f} (allocation {n}/{N[h]}); term W^2(1-f)p(1-p)/(n-1) = {v:.6f}")
se = math.sqrt(var); z = 1.96
lo, hi = p_st - z * se, p_st + z * se
sc, obs = FRAME / TOTAL, CLASSIFIED / TOTAL
print(f"stratum-weighted proportion = {p_st:.4f}; variance = {var:.6f}; SE = {se:.4f}; 95% (z=1.96) {lo:.4f} to {hi:.4f}")
rec = obs + p_st * sc; rlo, rhi = obs + lo * sc, obs + hi * sc
print(f"recovery estimate = {CLASSIFIED}/{TOTAL} + {p_st:.4f} x {FRAME}/{TOTAL} = {obs:.4f} + {p_st * sc:.4f} = {rec:.4f}; interval {rlo:.4f} to {rhi:.4f}")
json.dump(dict(strata=rows, p_stratified=p_st, variance=var, se=se, ci=[lo, hi], recovery=rec, recovery_ci=[rlo, rhi]),
          open("outputs/audit_design_interval.json", "w", newline="\n"), indent=1)
