"""Figure 3: WITSML maximum depth versus NOD total depth for all matched wellbores (24 of 26). Reads only outputs/td_validation.csv."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from figure_style import save

v = pd.read_csv("outputs/td_validation.csv")
m = v[v.outcome != "UNMATCHED"]; un = v[v.outcome == "UNMATCHED"]
assert len(m) == 24 and len(un) == 2
fig, ax = plt.subplots(figsize=(9, 9))
for outcome, color in {"EXACT": "#2ca02c", "CLOSE_NOT_EXACT": "#ff7f0e"}.items():
    s = m[m.outcome == outcome]
    ax.scatter(s.witsml_max_md_m, s.nod_total_depth_m, c=color, s=45, label=f"{'Exact (within 0.5 m)' if outcome == 'EXACT' else 'Close, not exact'} (n={len(s)})", zorder=3, edgecolors="black", linewidths=0.3)
ax.plot([0, 5600], [0, 5600], "k--", linewidth=1, zorder=1, label="1:1 reference")
for r in m.itertuples():
    short = r.witsml_wellbore.replace("NO 15/9-", "")
    if r.outcome == "CLOSE_NOT_EXACT":
        ax.annotate(f"{short}\n(difference {r.diff_m:g} m)", (r.witsml_max_md_m, r.nod_total_depth_m), fontsize=8, xytext=(8, -10), textcoords="offset points", color="#ff7f0e", fontweight="bold")
    if short == "F-7":
        ax.annotate("F-7, F-9", (r.witsml_max_md_m, r.nod_total_depth_m), fontsize=7, xytext=(8, 10), textcoords="offset points")
ax.set_xlim(0, 5600); ax.set_ylim(0, 5600); ax.set_aspect("equal"); ax.grid(alpha=0.2)
ax.set_xlabel("WITSML maximum measured depth (m)"); ax.set_ylabel("NOD total depth (m)")
ax.legend(loc="upper left", fontsize=9)
ax.set_title("TD validation: WITSML maximum depth versus NOD total depth (24 matched wellbores of 26)\n"
             f"Not plotted (unmatched, no NOD counterpart): {', '.join(un.witsml_wellbore.str.replace('NO 15/9-', ''))}", fontsize=10)
fig.tight_layout()
save(fig, "figure3_td_validation.png")
print("plotted", len(m), "unmatched", un.witsml_wellbore.tolist())
