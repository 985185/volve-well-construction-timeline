"""Figure 4: spud date offset (WITSML spud minus the NOD entry date chosen as the one closest to the first report, days; the same definition as the Stage 7 table) per wellbore, coloured by category. Reads only outputs/spud_validation.csv.
15/9-F-11 T2 is excluded because NOD does not register it separately (25 wellbores plotted)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd
from figure_style import CATEGORY_COLORS, save

s = pd.read_csv("outputs/spud_validation.csv")
excl = s[s.w_minus_n_days.isna()]
p = s[s.w_minus_n_days.notna()].sort_values("w_minus_n_days")
assert len(p) == 25 and excl.wellbore.tolist() == ["NO 15/9-F-11 T2"]
fig, ax = plt.subplots(figsize=(10, 9))
y = range(len(p))
ax.barh(y, p.w_minus_n_days, color=[CATEGORY_COLORS[c][0] for c in p.category], edgecolor="black", linewidth=0.3)
ax.set_yticks(list(y)); ax.set_yticklabels(p.wellbore.str.replace("NO 15/9-", ""), fontsize=8)
ax.axvline(0, color="black", linewidth=0.8); ax.grid(alpha=0.2, axis="x")
for yi, v in zip(y, p.w_minus_n_days):          # value labels, so zero-day offsets stay visible
    ax.annotate(f"{v:+.0f}" if v else "0", (v, yi), xytext=(4 if v >= 0 else -4, 0), textcoords="offset points", ha="left" if v >= 0 else "right", va="center", fontsize=7)
ax.set_xlim(p.w_minus_n_days.min() * 1.08, max(p.w_minus_n_days.max() * 1.25, 60))
ax.set_xlabel("Offset, days (WITSML spud date minus NOD entry date closest to the first report)")
ax.set_title("Spud date offset by validation category (25 wellbores)\nExcluded (no separate NOD record): " + ", ".join(excl.wellbore.str.replace("NO 15/9-", "")), fontsize=10)
ax.legend(handles=[mpatches.Patch(color=c, label=l) for c, l in CATEGORY_COLORS.values()], loc="upper left", fontsize=7.5)
fig.tight_layout()
save(fig, "figure4_spud_offset.png")
print("plotted", len(p), "excluded", excl.wellbore.tolist(), p.category.value_counts().to_dict())
