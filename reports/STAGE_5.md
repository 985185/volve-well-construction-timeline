# Stage 5: Timeline dataset

Date: 2026-10-24. Branch: `rerun-2026-10`. Status: **complete, no discrepancy.** 1,421 rows, identical to the v2 dataset on every column.

Script: `src/stage5_timeline.py`. Inputs: `data/interim/ddr.parquet`, `data/interim/classified_new.parquet`. Output: `outputs/timeline.csv` (columns wellbore, date, days_from_first_ddr, md_m, phase, filename).

## Construction and arithmetic

- Start: 1,759 DDRs.
- Exclude the `-999.99` depth sentinel: 331.
- Exclude zero depth (`0`): 7.
- Exclude blank depth: 0 (no blank or non-numeric `md` values exist).
- 1,759 - 331 - 7 - 0 = **1,421** (v2 target 1,421: match).
- `md` was cast with `pd.to_numeric(errors="raise")`; it did not fail, so every non-sentinel value is a valid number. Depth range 17.0 to 5,331.0 m.
- 26 wellbores, all present (every wellbore keeps at least 6 rows).
- `days_from_first_ddr` is measured from the wellbore's first *retained* row (first DDR with a usable depth), so it is 0 for the first row of every wellbore. This is the v2 definition (verified by the comparison below). It means 15/9-19 A counts from 1997-07-26 (its 1980 sentinel and the 1997-07-25 record have `-999.99` depths and are excluded). Stage 9 (duration table, if requested) should use first and last DDR dates from the full DDR set instead, not this column.
- The `date` column holds the full ISO timestamp from `date_report` (for example `1997-07-26T00:00:00+02:00`), as in v2 where the column was called `date_report`.
- Sorted by wellbore, date, filename.

## Phase counts in the timeline

Reservoir drilling 255, Completion 170, Liner / Casing run 123, Waiting / Downtime 99, Intermediate drilling 77, Cementing 71, Intermediate casing 69, Logging / Testing 63, Surface casing 62, Spud / Conductor 50, P&A 23, Rig move / Setup 16, Workover 4, Unclassified 339. Sum: 255 + 170 + 123 + 99 + 77 + 71 + 69 + 63 + 62 + 50 + 23 + 16 + 4 + 339 = 1,421.

## Comparison with the v2 dataset (`inputs/repo_before/data/volve_timeline_dataset.csv`, 1,421 rows)

Joined on filename: only in new 0, only in v2 0. Differing rows: wellbore 0, date 0, days_from_first_ddr 0, md_m 0, phase 0. The rerun timeline is identical to v2 in all 1,421 rows.

Per-wellbore maximum depth matches the v2 Table 3 inputs I could see in the extract (for example 15/9-19 B 3,272.0, 15/9-F-11 347.0, 15/9-F-11 T2 4,562.1, 15/9-F-10 5,331.0). Full per-wellbore table is in the run output of `src/stage5_timeline.py`; the TD comparison itself is Stage 7.

## Stop

As instructed, stopping after Stage 5. Next is Stage 6 (audit). Decisions already made: keep the old 50 records and original strata; map by wellbore + date. Still unanswered by TJ and needed there: who made the CONSTRUCTION / NON_CONSTRUCTION calls (open item 4).
