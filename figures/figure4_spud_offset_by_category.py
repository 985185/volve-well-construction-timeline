"""
Figure 4 -- Spud date offset (days) per wellbore, coloured by validation category.
Data source: C:\\Volve\\paper2_rebuild\\spud_validation.csv (Stage 5/3).

Offset = WITSML dTimSpud (structured spud_date) minus the PRIMARY NOD date
used in spud_validation.csv (main entry date where multiple NOD dates exist;
predrill-entry and other secondary dates are not used for this offset).
Positive offset = WITSML spud is AFTER the NOD date. Negative = WITSML spud
is BEFORE the NOD date.

NO 15/9-F-11 T2 has no NOD date at all (not separately registered -- see
td_validation.csv) and is EXCLUDED from this figure, not silently dropped:
listed in the caption.

The brief named four example categories (EXACT_MATCH, DEFINITIONAL_OFFSET,
WELLBORE_IDENTITY, UNRESOLVED); the actual data also contains WITSML_ERROR
and a distinct WITSML_ERROR_STRUCTURED_FIELD subtype (inherited spud_date
values on sidetracks) -- all six are shown as they are the true classification
result, not narrowed to the four examples.
"""
import csv
from datetime import date
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATA = r"C:\Volve\paper2_rebuild\spud_validation.csv"

CATEGORY_COLORS = {
    "EXACT_MATCH": "#2ca02c",
    "DEFINITIONAL_OFFSET": "#1f77b4",
    "WITSML_ERROR": "#d62728",
    "WITSML_ERROR (structured field only)": "#ff9896",
    "WELLBORE_IDENTITY": "#9467bd",
    "UNRESOLVED": "#7f7f7f",
}

def first_iso_date(s):
    """Extract the first YYYY-MM-DD substring from a possibly-annotated string."""
    s = s.strip()
    token = s.split(" ")[0].split(";")[0].split("(")[0].strip()
    try:
        return date.fromisoformat(token)
    except ValueError:
        return None

rows = []
with open(DATA, encoding="utf-8") as f:
    r = csv.DictReader(f)
    for row in r:
        rows.append(row)

plot_rows = []
excluded = []
for row in rows:
    witsml_d = first_iso_date(row["witsml_spud_date"])
    nod_d = first_iso_date(row["nod_date_used"])
    if witsml_d is None or nod_d is None:
        excluded.append(row["wellbore"])
        continue
    offset = (witsml_d - nod_d).days
    plot_rows.append((row["wellbore"].replace("NO 15/9-", ""), offset, row["classification"]))

# sort by offset for readability
plot_rows.sort(key=lambda x: x[1])

fig, ax = plt.subplots(figsize=(10, 9))
names = [r[0] for r in plot_rows]
offsets = [r[1] for r in plot_rows]
colors = [CATEGORY_COLORS.get(r[2], "#000000") for r in plot_rows]

y_pos = range(len(plot_rows))
ax.barh(y_pos, offsets, color=colors, edgecolor="black", linewidth=0.3)
ax.set_yticks(y_pos)
ax.set_yticklabels(names, fontsize=8)
ax.axvline(0, color="black", linewidth=0.8)
ax.set_xlabel("Offset, days (WITSML spud_date - NOD primary date)")
ax.set_title(
    "Figure 4 -- Spud date offset by validation category (25 of 26 wellbores)\n"
    f"Excluded (no NOD date registered): {', '.join(w.replace('NO 15/9-','') for w in excluded)}",
    fontsize=10
)
ax.grid(alpha=0.2, axis="x")

import matplotlib.patches as mpatches
handles = [mpatches.Patch(color=c, label=k) for k, c in CATEGORY_COLORS.items()]
ax.legend(handles=handles, loc="lower right", fontsize=7.5)

fig.tight_layout()
fig.savefig(r"C:\Volve\paper2_rebuild\figures\figure4_spud_offset_by_category.png", dpi=200, bbox_inches="tight")
print("saved figure4_spud_offset_by_category.png")
print(f"plotted: {len(plot_rows)}, excluded: {excluded}")
