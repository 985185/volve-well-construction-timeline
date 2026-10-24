"""
Figure 2 -- Days vs depth, all wellbores, coloured by hole section.
Data source: volve_timeline_dataset.csv.

"Hole section" here means the four structural-drilling phase categories
named in the brief: Spud / Conductor, Surface casing, Intermediate drilling,
Reservoir drilling. Rows classified into any other phase (Cementing,
Completion, P&A, Logging/Testing, Workover, Waiting/Downtime, Rig move/Setup,
Liner/Casing run, Intermediate casing, Unclassified) are plotted in light
grey as background context, NOT counted as a "hole section".
"""
import csv
from datetime import date
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATA = r"C:\Volve\paper2_rebuild\volve_timeline_dataset.csv"

HOLE_SECTION_COLORS = {
    "Spud / Conductor": "#8B4513",
    "Surface casing": "#D2691E",
    "Intermediate drilling": "#1f77b4",
    "Reservoir drilling": "#2ca02c",
}
BACKGROUND_COLOR = "#e8e8e8"

rows = []
with open(DATA, encoding="utf-8") as f:
    r = csv.DictReader(f)
    for row in r:
        rows.append(row)

by_well = {}
for row in rows:
    by_well.setdefault(row["wellbore"], []).append(row)

fig, ax = plt.subplots(figsize=(11, 7))

# plot background (non-hole-section) points first, low zorder
bg_days, bg_md = [], []
hs_days = {k: [] for k in HOLE_SECTION_COLORS}
hs_md = {k: [] for k in HOLE_SECTION_COLORS}

for wb, recs in by_well.items():
    recs_sorted = sorted(recs, key=lambda r: r["date_report"])
    t0 = date.fromisoformat(recs_sorted[0]["date_report"][:10])
    for rec in recs_sorted:
        d = date.fromisoformat(rec["date_report"][:10])
        days = (d - t0).days
        md = float(rec["md_m"])
        phase = rec["phase"]
        if phase in HOLE_SECTION_COLORS:
            hs_days[phase].append(days)
            hs_md[phase].append(md)
        else:
            bg_days.append(days)
            bg_md.append(md)

ax.scatter(bg_days, bg_md, c=BACKGROUND_COLOR, s=6, label="Other phase (background)", zorder=1, edgecolors="none")
for phase, color in HOLE_SECTION_COLORS.items():
    ax.scatter(hs_days[phase], hs_md[phase], c=color, s=10, label=f"{phase} (n={len(hs_days[phase])})", zorder=2, edgecolors="none")

ax.invert_yaxis()
ax.set_xlabel("Days from first DDR of wellbore leg")
ax.set_ylabel("Measured depth (m RKB)")
ax.set_title("Figure 2 -- Days vs. depth, all 26 wellbores, coloured by hole section\n(background: all other classified/unclassified phases)")
ax.legend(loc="upper right", fontsize=8, markerscale=1.5)
ax.grid(alpha=0.2)

fig.tight_layout()
fig.savefig(r"C:\Volve\paper2_rebuild\figures\figure2_days_vs_depth_all_wells.png", dpi=200, bbox_inches="tight")
print("saved figure2_days_vs_depth_all_wells.png")
print(f"hole-section point counts: {{ {', '.join(f'{k}: {len(v)}' for k,v in hs_days.items())} }}")
print(f"background points: {len(bg_days)}")
