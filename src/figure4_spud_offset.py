"""Figure 4 (no title inside the image; the caption names the excluded wellbore; the F-1 bar is clipped and annotated): spud date offset (WITSML spud minus the NOD pre-drill entry date where NOD records one, otherwise the NOD main entry date, days; the same definition as the Stage 7 table) per wellbore, coloured by category. Reads only outputs/spud_validation.csv.
15/9-F-11 T2 is excluded because NOD does not register it separately (25 wellbores plotted)."""
import matplotlib
matplotlib.use("Agg")
from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
import pandas as pd
from figure_style import CATEGORY_COLORS, save

s = pd.read_csv("outputs/spud_validation.csv")
excl = s[s.w_minus_n_days.isna()]
p = s[s.w_minus_n_days.notna()].sort_values("w_minus_n_days")
assert len(p) == 25 and excl.wellbore.tolist() == ["NO 15/9-F-11 T2"]
CLIP = 400   # days: bars beyond this are clipped and labelled with their value, so one outlier (15/9-F-1) does not compress the rest
fig, ax = plt.subplots(figsize=(10, 9))
y = range(len(p))
vals = p.w_minus_n_days.tolist()
ax.barh(y, [max(min(v, CLIP), -CLIP) for v in vals], color=[CATEGORY_COLORS[c][0] for c in p.category], edgecolor="black", linewidth=0.3)
MARK = {"EXACT": "o", "DEFINITIONAL_OFFSET": "s", "ERROR": "^", "INHERITED": "v", "IDENTITY": "D", "UNRESOLVED": "X"}          # one marker shape per category as well as one colour
for cat in MARK:      # a marker at the end of every bar, so zero-length bars are visible
    sel = [i for i, c in enumerate(p.category) if c == cat]
    ax.scatter([max(min(vals[i], CLIP), -CLIP) for i in sel], sel, c=CATEGORY_COLORS[cat][0], s=46, marker=MARK[cat], edgecolors="black", linewidths=0.8, zorder=4)
ax.set_yticks(list(y)); ax.set_yticklabels(p.wellbore.str.replace("NO 15/9-", ""), fontsize=8)
ax.axvline(0, color="black", linewidth=0.8); ax.grid(alpha=0.2, axis="x")
for yi, v in zip(y, vals):          # value labels, so zero-day offsets stay visible
    if abs(v) > CLIP:               # clipped bar: break marks at the axis edge and the true value
        edge = CLIP if v > 0 else -CLIP
        ax.text(edge, yi, "//", ha="center", va="center", fontsize=9, fontweight="bold", color="white", bbox=dict(boxstyle="square,pad=0.05", fc="black", ec="none"))
        ax.annotate(f"{v:+,.0f} (axis clipped)", (edge, yi), xytext=(6 if v < 0 else -6, 0), textcoords="offset points", ha="left" if v < 0 else "right", va="center", fontsize=8, fontweight="bold")
    else:
        ax.annotate(f"{v:+.0f}" if v else "0", (v, yi), xytext=(4 if v >= 0 else -4, 0), textcoords="offset points", ha="left" if v >= 0 else "right", va="center", fontsize=7)
ax.set_xlim(-CLIP * 1.05, max(max(vals) * 1.25, 60))
ax.set_xlabel("Offset, days (WITSML spud date minus NOD pre-drill entry date, else main entry date)")
ax.legend(handles=[Line2D([0], [0], marker=MARK[k], color="none", markerfacecolor=CATEGORY_COLORS[k][0], markeredgecolor="black", markersize=8, label=CATEGORY_COLORS[k][1]) for k in MARK], loc="upper left", fontsize=7.5)
fig.tight_layout()
save(fig, "figure4_spud_offset.png")
print("plotted", len(p), "excluded", excl.wellbore.tolist(), p.category.value_counts().to_dict())
