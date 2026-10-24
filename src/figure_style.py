"""Shared figure style: one phase colour map for every figure (consistent phase colours), 300 dpi output into outputs/figures/. No data is read here."""
import os

DPI = 300
OUT = "outputs/figures"
os.makedirs(OUT, exist_ok=True)

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

# validation categories (Fig. 4), same colours as v2
CATEGORY_COLORS = {
    "EXACT": ("#2ca02c", "Exact"),
    "DEFINITIONAL_OFFSET": ("#1f77b4", "Definitional offset"),
    "ERROR": ("#d62728", "WITSML data-entry error"),
    "INHERITED": ("#ff9896", "Inherited parent spud date"),
    "IDENTITY": ("#9467bd", "Wellbore-identity conflation"),
    "UNRESOLVED": ("#7f7f7f", "Unresolved"),
}


def save(fig, name):
    path = f"{OUT}/{name}"
    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    print("saved", path)
