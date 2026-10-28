"""Figure 2: report number versus depth for all 26 wellbores, coloured by hole section. Reads only outputs/timeline.csv and outputs/fig2_report_index.csv.
x = report number counted from the wellbore's first report of any kind (1 = first report; every DDR counts, the 1980 sentinel excluded), the same count as Table 6. Only reports with a valid depth are plotted. No title inside the image (the caption carries it)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from figure_style import PHASE_COLORS, label, save

t = pd.read_csv("outputs/timeline.csv").merge(pd.read_csv("outputs/fig2_report_index.csv"), on=["filename", "wellbore"], validate="one_to_one")
HOLE = ["Spud / Conductor", "Surface casing", "Intermediate drilling", "Reservoir drilling"]
fig, ax = plt.subplots(figsize=(11, 7))
bg = t[~t.phase.isin(HOLE)]
ax.scatter(bg.report_number, bg.md_m, c="#e8e8e8", s=6, label="Other phase (background)", zorder=1, edgecolors="none")
for p in HOLE:
    g = t[t.phase == p]
    ax.scatter(g.report_number, g.md_m, c=PHASE_COLORS[p], s=10, label=f"{label(p)} (n={len(g)})", zorder=2, edgecolors="none")
ax.invert_yaxis()
ax.set_xlabel("Report number (1 = wellbore's first report)")
ax.set_ylabel("Measured depth (m)")
ax.legend(loc="upper right", fontsize=8, markerscale=1.5); ax.grid(alpha=0.2)
fig.tight_layout()
save(fig, "figure2_days_vs_depth.png")
print({p: int((t.phase == p).sum()) for p in HOLE}, "background", len(bg), "wellbores", t.wellbore.nunique(), "max report number", int(t.report_number.max()))
