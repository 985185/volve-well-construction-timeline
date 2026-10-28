"""
Figure 1 -- Depth vs time for four representative wellbores.
Data source: C:\\Volve\\paper2_rebuild\\volve_timeline_dataset.csv (1,421 rows,
built in Stage 6 Part A from workspace.default.volve_ddr_classified, md_m
populated rows only -- sentinel '-999.99' and zero '0' excluded).

Wellbores chosen per brief:
  15/9-19 S    -- 1990s exploration well
  15/9-F-14    -- straightforward development well
  15/9-F-1 family (F-1 -> F-1 B -> F-1 C) -- sidetrack family
  15/9-F-7     -- shallow well, 1,085 m TD (validated against NOD, see td_validation.csv)

Phase colour bands are overlaid (colour = phase category). Points are NOT
connected across a gap of more than 14 days, so missing/excluded md_m periods
remain visibly blank rather than being bridged by an interpolated line.
"""
import csv
from datetime import date
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

DATA = r"C:\Volve\paper2_rebuild\volve_timeline_dataset.csv"

PHASE_COLORS = {
    "Spud / Conductor": "#8B4513",
    "Surface casing": "#D2691E",
    "Intermediate drilling": "#1f77b4",
    "Intermediate casing": "#4682B4",
    "Reservoir drilling": "#2ca02c",
    "Liner / Casing run": "#17becf",
    "Cementing": "#7f7f7f",
    "Completion": "#9467bd",
    "P&A": "#000000",
    "Logging / Testing": "#bcbd22",
    "Workover": "#e377c2",
    "Waiting / Downtime": "#ff9896",
    "Rig move / Setup": "#c5b0d5",
    "Unclassified": "#dddddd",
}

def load():
    rows = []
    with open(DATA, encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append(row)
    return rows

rows = load()
by_well = {}
for row in rows:
    by_well.setdefault(row["wellbore"], []).append(row)
for wb in by_well:
    by_well[wb].sort(key=lambda r: r["date_report"])

def parse_date(s):
    return date.fromisoformat(s[:10])

def plot_panel(ax, wellbores, title):
    # Use REAL calendar dates on the x-axis for every panel (not "days from
    # this leg's own first DDR"). For the multi-leg family panel this is
    # essential: each leg's own DDR series starts at a different real date
    # (F-1: 2007-12-02, F-1 B: 2013-08-30, F-1 C: 2014-02-22, with F-1's own
    # 38 DDRs themselves spanning a ~6-year gap before the 2013 re-entry --
    # see the WELLBORE_IDENTITY finding in spud_validation.csv). Resetting
    # each leg to its own day-zero and overlaying them on one shared axis
    # would make temporally disjoint records look contemporaneous -- a real
    # date axis shows the true multi-year gaps honestly instead.
    import matplotlib.dates as mdates
    for wb in wellbores:
        recs = by_well.get(wb, [])
        if not recs:
            ax.text(0.5, 0.5, f"NO DATA: {wb}", transform=ax.transAxes, ha="center")
            continue
        dates = [parse_date(r["date_report"]) for r in recs]
        mds = [float(r["md_m"]) for r in recs]
        phases = [r["phase"] for r in recs]

        # Break the connecting line where the gap between consecutive points > 14 days
        seg_x, seg_y = [dates[0]], [mds[0]]
        for i in range(1, len(dates)):
            if (dates[i] - dates[i - 1]).days > 14:
                ax.plot(seg_x, seg_y, color="#999999", linewidth=0.8, zorder=1)
                seg_x, seg_y = [], []
            seg_x.append(dates[i])
            seg_y.append(mds[i])
        if len(seg_x) > 1:
            ax.plot(seg_x, seg_y, color="#999999", linewidth=0.8, zorder=1)

        colors = [PHASE_COLORS.get(p, "#dddddd") for p in phases]
        ax.scatter(dates, mds, c=colors, s=10, zorder=2, edgecolors="none")

        # annotate leg name at its start if plotting a multi-leg family panel
        if len(wellbores) > 1:
            ax.annotate(wb.replace("NO 15/9-", ""), (dates[0], mds[0]),
                        fontsize=6, xytext=(3, 3), textcoords="offset points")

    ax.invert_yaxis()
    ax.set_title(title, fontsize=9)
    ax.set_xlabel("Date")
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    for label in ax.get_xticklabels():
        label.set_rotation(45)
        label.set_ha("right")
    ax.grid(alpha=0.2)

fig, axes = plt.subplots(1, 4, figsize=(16, 4.2), sharey=False)

plot_panel(axes[0], ["NO 15/9-19 S"], "15/9-19 S\n(1990s exploration)")
plot_panel(axes[1], ["NO 15/9-F-14"], "15/9-F-14\n(development well)")
plot_panel(axes[2], ["NO 15/9-F-1", "NO 15/9-F-1 B", "NO 15/9-F-1 C"], "15/9-F-1 / F-1 B / F-1 C\n(sidetrack family)")
plot_panel(axes[3], ["NO 15/9-F-7"], "15/9-F-7\n(shallow, TD 1,085 m)")

axes[0].set_ylabel("Measured depth (m RKB)")

handles = [mpatches.Patch(color=c, label=p) for p, c in PHASE_COLORS.items()]
fig.legend(handles=handles, loc="lower center", ncol=7, fontsize=6.5, bbox_to_anchor=(0.5, -0.08))

fig.suptitle("Figure 1 -- Depth vs. time, four representative wellbores (phase-coloured)", fontsize=11)
fig.tight_layout(rect=[0, 0.06, 1, 0.95])
fig.savefig(r"C:\Volve\paper2_rebuild\figures\figure1_depth_vs_time.png", dpi=200, bbox_inches="tight")
print("saved figure1_depth_vs_time.png")
