"""Figure 4 (file figure3_td_validation.png): WITSML maximum depth versus NOD total depth for all matched wellbores (24 of 26; 21 matched by name, circles; 3 technical sidetracks matched by depth, diamonds). Reads only outputs/td_validation.csv."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from figure_style import save

v = pd.read_csv("outputs/td_validation.csv")
m = v[v.outcome != "UNMATCHED"]; un = v[v.outcome == "UNMATCHED"]
assert len(m) == 24 and len(un) == 2
fig, ax = plt.subplots(figsize=(9, 9))
dm = m.match_method.str.startswith("T2")                # technical sidetracks matched by depth, not by name
LAB = {"EXACT": "Within 0.5 m", "CLOSE_NOT_EXACT": "Differs by more than 0.5 m"}
for outcome, color in {"EXACT": "#2ca02c", "CLOSE_NOT_EXACT": "#ff7f0e"}.items():
    s_ = m[(m.outcome == outcome) & ~dm]
    ax.scatter(s_.witsml_max_md_m, s_.nod_total_depth_m, c=color, s=45, marker="o", label=f"{LAB[outcome]}, matched by name (n={len(s_)})", zorder=3, edgecolors="black", linewidths=0.3)
s_ = m[dm]
ax.scatter(s_.witsml_max_md_m, s_.nod_total_depth_m, c="#2ca02c", s=90, marker="D", label=f"Technical sidetrack matched by depth, within 0.5 m (n={len(s_)})", zorder=4, edgecolors="black", linewidths=0.6)
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
fig.tight_layout()
save(fig, "figure3_td_validation.png")
print("plotted", len(m), "unmatched", un.witsml_wellbore.tolist())
