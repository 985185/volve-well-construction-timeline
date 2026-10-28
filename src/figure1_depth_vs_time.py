"""Figure 1: depth versus calendar date for four representative wellbores, points coloured by phase. Reads only outputs/timeline.csv."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd
from figure_style import PHASE_COLORS, label, save

t = pd.read_csv("outputs/timeline.csv")
t["day"] = pd.to_datetime(t.date.str[:10])
GAP_DAYS = 14   # the line is not drawn across gaps longer than this


def panel(ax, wells, title):
    for w in wells:
        g = t[t.wellbore == w].sort_values("day")
        seg = [0]
        for i in range(1, len(g)):
            if (g.day.iloc[i] - g.day.iloc[i - 1]).days > GAP_DAYS:
                ax.plot(g.day.iloc[seg], g.md_m.iloc[seg], color="#999999", linewidth=0.8, zorder=1); seg = []
            seg.append(i)
        ax.plot(g.day.iloc[seg], g.md_m.iloc[seg], color="#999999", linewidth=0.8, zorder=1)
        ax.scatter(g.day, g.md_m, c=g.phase.map(PHASE_COLORS), s=10, zorder=2, edgecolors="none")
        if len(wells) > 1:
            ax.annotate(w.replace("NO 15/9-", ""), (g.day.iloc[0], g.md_m.iloc[0]), fontsize=6, xytext=(3, 3), textcoords="offset points")
    ax.invert_yaxis(); ax.set_title(title, fontsize=9); ax.set_xlabel("Date")
    loc = mdates.AutoDateLocator(minticks=3, maxticks=6); ax.xaxis.set_major_locator(loc); ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(loc))
    ax.grid(alpha=0.2)


fig, axes = plt.subplots(1, 4, figsize=(16, 4.2))
panel(axes[0], ["NO 15/9-19 S"], "15/9-19 S\n(1990s exploration)")
panel(axes[1], ["NO 15/9-F-14"], "15/9-F-14\n(development well)")
panel(axes[2], ["NO 15/9-F-1", "NO 15/9-F-1 B", "NO 15/9-F-1 C"], "15/9-F-1, F-1 B, F-1 C\n(sidetrack family)")
panel(axes[3], ["NO 15/9-F-7"], "15/9-F-7\n(shallow, TD 1,085 m)")
axes[0].set_ylabel("Measured depth (m)")
fig.legend(handles=[mpatches.Patch(color=c, label=label(p)) for p, c in PHASE_COLORS.items()], loc="lower center", ncol=7, fontsize=6.5, bbox_to_anchor=(0.5, -0.08))
fig.tight_layout(rect=[0, 0.06, 1, 1])
save(fig, "figure1_depth_vs_time.png")
