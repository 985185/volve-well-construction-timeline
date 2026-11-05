"""
Figure 3 -- TD validation scatter: reconstructed WITSML max MD vs NOD total depth.
Data source: C:\\Volve\\paper2_rebuild\\td_validation.csv (Stage 5/3).

24 of 26 wellbores have a defensible NOD match (22 EXACT, 2 CLOSE_NOT_EXACT);
2 wellbores (NO 15/9-19 B, NO 15/9-F-11 base) are UNMATCHED -- no NOD total
depth exists for them under any defensible pairing (see td_validation.csv
notes) and they are EXCLUDED from this scatter (no y-value to plot), listed
separately in the figure caption instead of silently omitted.
"""
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATA = r"C:\Volve\paper2_rebuild\td_validation.csv"

rows = []
with open(DATA, encoding="utf-8") as f:
    r = csv.DictReader(f)
    for row in r:
        rows.append(row)

matched = [r for r in rows if r["agreement"] != "UNMATCHED"]
unmatched = [r for r in rows if r["agreement"] == "UNMATCHED"]

fig, ax = plt.subplots(figsize=(9, 9))

colors = {"EXACT": "#2ca02c", "CLOSE_NOT_EXACT": "#ff7f0e"}
for agreement, color in colors.items():
    subset = [r for r in matched if r["agreement"] == agreement]
    x = [float(r["witsml_max_md_m"]) for r in subset]
    y = [float(r["nod_total_depth_m"]) for r in subset]
    ax.scatter(x, y, c=color, s=45, label=f"{agreement} (n={len(subset)})", zorder=3, edgecolors="black", linewidths=0.3)

# 1:1 reference line
lims = [0, 5600]
ax.plot(lims, lims, "k--", linewidth=1, zorder=1, label="1:1 reference")

# Label outliers (CLOSE_NOT_EXACT) and the F-7/F-9 overlap point explicitly
for r in matched:
    wb_short = r["witsml_wellbore"].replace("NO 15/9-", "")
    x = float(r["witsml_max_md_m"])
    y = float(r["nod_total_depth_m"])
    if r["agreement"] == "CLOSE_NOT_EXACT":
        ax.annotate(f"{wb_short}\n(diff {r['diff_m']}m)", (x, y), fontsize=8, xytext=(8, -10),
                    textcoords="offset points", color="#ff7f0e", fontweight="bold")
    if wb_short == "F-7":
        ax.annotate(wb_short, (x, y), fontsize=7, xytext=(8, 10), textcoords="offset points")
    elif wb_short == "F-9":
        ax.annotate(wb_short, (x, y), fontsize=7, xytext=(8, -14), textcoords="offset points")

ax.set_xlim(0, 5600)
ax.set_ylim(0, 5600)
ax.set_xlabel("WITSML reconstructed max MD (m)")
ax.set_ylabel("NOD official total depth (m)")
ax.set_aspect("equal")
ax.grid(alpha=0.2)
ax.legend(loc="upper left", fontsize=9)

unmatched_names = ", ".join(r["witsml_wellbore"].replace("NO 15/9-", "") for r in unmatched)
ax.set_title(
    "Figure 3 -- TD validation: WITSML max MD vs. NOD total depth (24 of 26 wellbores)\n"
    f"Excluded (UNMATCHED, no defensible NOD counterpart): {unmatched_names}. "
    "F-7 and F-9 both validate exactly at 1,085 m (overlapping point, lower-left).",
    fontsize=10
)

fig.tight_layout()
fig.savefig(r"C:\Volve\paper2_rebuild\figures\figure3_td_validation_scatter.png", dpi=200, bbox_inches="tight")
print("saved figure3_td_validation_scatter.png")
print(f"plotted: {len(matched)}, excluded as UNMATCHED: {[r['witsml_wellbore'] for r in unmatched]}")
