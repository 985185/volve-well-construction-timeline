# Stage 10: Figures

Date: 2026-10-24. Branch: `rerun-2026-10`. Scripts: `src/figure_style.py` (shared phase colours, 300 dpi, output folder), `src/figure1_depth_vs_time.py`, `src/figure2_days_vs_depth.py`, `src/figure3_td_validation.py`, `src/figure4_spud_offset.py`. Images: `outputs/figures/figure{1,2,3,4}_*.png`.

**Status: complete.** All four PNGs are 300 dpi (checked from the file metadata: 299.9994, 4770x1382, 3270x2059, 2627x2670 and 2958x2670 pixels). Every figure script reads only from `outputs/`: Fig. 1 and 2 from `outputs/timeline.csv`, Fig. 3 from `outputs/td_validation.csv`, Fig. 4 from `outputs/spud_validation.csv`. The only other import is `figure_style.py`, which holds colours and does not read data.

## What each figure shows

| Figure | Content | Source | Counts shown |
|---|---|---|---|
| 1 | Depth versus calendar date, four representative wellbores (19 S, F-14, the F-1, F-1 B and F-1 C family, F-7), points coloured by phase, line broken across gaps longer than 14 days | `timeline.csv` | 1,421-row timeline |
| 2 | Days versus depth, all wellbores, coloured by hole section. x-axis label: "Days from first report with recorded depth" (TJ) | `timeline.csv` | 26 wellbores; Spud 50, Surface casing 62, Intermediate drilling 77, Reservoir drilling 255 plotted in colour, 977 other points in grey; 50 + 62 + 77 + 255 + 977 = 1,421 |
| 3 | WITSML maximum depth versus NOD total depth, with the 1:1 line | `td_validation.csv` | all 24 matched wellbores (22 exact, 2 close: F-15 15 m, 19 S 227 m); unmatched 19 B and F-11 named in the title |
| 4 | Offset in days, WITSML spud date minus NOD main entry date, coloured by category | `spud_validation.csv` | 25 wellbores, F-11 T2 excluded (no separate NOD record): Exact 7, Definitional offset 8, WITSML data-entry error 4, Unresolved 4, Inherited 1, Wellbore-identity conflation 1; 7 + 8 + 4 + 4 + 1 + 1 = 25 |

Phase colours come from one dictionary (`PHASE_COLORS`) used by Figs 1 and 2, the same hues as v2, so the colours are consistent across figures.

## Changes from the v2 figures (for the Stage 12 captions)

- Fig. 2 x label is now "Days from first report with recorded depth", which is how `days_from_first_ddr` is defined (each wellbore counts from its first report with a usable depth, not from its first DDR).
- Axis label for depth is "Measured depth (m)": v2 said "m RKB", and I have not verified the depth reference of the WITSML `md` field, so I removed the reference datum.
- Figure titles no longer start with "Figure N" (captions belong in the manuscript) and use no dashes.
- Fig. 3 plots 24 wellbores as before, including F-11 T2, which is matched to NOD F-11 by depth.
- Fig. 4 offset convention is unchanged from v2: WITSML spud date minus NOD **main** entry date. That differs from the NOD date used for the categories in `spud_validation.csv` (the main or predrill date closer to the first report). The plotted offsets that differ from the category offsets are F-4 (-217 days against -91), F-5 (-37 against -4), F-14 (-31 against -2) and F-15 (+305 against +340). This is a convention to state in the caption; the days quoted in the Stage 7 report for F-4 (-91) and F-15 (+340) use the predrill date.
- Zero-day offsets are drawn as value labels so that they are visible (13 of 25 are 0 or 1 day).
- File names changed (for example `figure2_days_vs_depth.png`), and the old PNGs stay in `inputs/repo_before/figures/` as the "before" state.

## Not changed or not checked

- Fig. 1 still uses the same four panels as v2, which was a choice of the brief; the F-1 panel draws the 2007 reports (4 DDRs) far from the 2013 reports, matching the F-1 finding in Stage 8c.
- The figures show phases from the frozen v3 classifier; 339 of the 1,421 plotted points are Unclassified (light grey in Fig. 1).

## Next

Stage 11 (registry).
