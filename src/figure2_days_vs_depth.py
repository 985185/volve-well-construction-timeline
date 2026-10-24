"""Figure 2: days versus depth for all 26 wellbores, coloured by hole section. Reads only outputs/timeline.csv.
x = days_from_first_ddr, which counts from each wellbore's first report with a recorded (usable) depth."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from figure_style import PHASE_COLORS, save

t = pd.read_csv("outputs/timeline.csv")
HOLE = ["Spud / Conductor", "Surface casing", "Intermediate drilling", "Reservoir drilling"]
fig, ax = plt.subplots(figsize=(11, 7))
bg = t[~t.phase.isin(HOLE)]
ax.scatter(bg.days_from_first_ddr, bg.md_m, c="#e8e8e8", s=6, label="Other phase (background)", zorder=1, edgecolors="none")
for p in HOLE:
    g = t[t.phase == p]
    ax.scatter(g.days_from_first_ddr, g.md_m, c=PHASE_COLORS[p], s=10, label=f"{p} (n={len(g)})", zorder=2, edgecolors="none")
ax.invert_yaxis()
ax.set_xlabel("Days from first report with recorded depth")
ax.set_ylabel("Measured depth (m)")
ax.set_title(f"Days versus depth, all {t.wellbore.nunique()} wellbores, coloured by hole section\n(background: all other phases and unclassified reports)")
ax.legend(loc="upper right", fontsize=8, markerscale=1.5); ax.grid(alpha=0.2)
fig.tight_layout()
save(fig, "figure2_days_vs_depth.png")
print({p: int((t.phase == p).sum()) for p in HOLE}, "background", len(bg), "wellbores", t.wellbore.nunique())
