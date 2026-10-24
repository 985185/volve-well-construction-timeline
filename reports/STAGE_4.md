# Stage 4: Classify

Date: 2026-10-24. Branch: `rerun-2026-10`. Status: **complete, no discrepancy.** Table 2 and the old per-phase counts reproduce exactly.

Scripts: `src/classifier_v3.py`, `src/stage4_export_old_classified.py`, `src/stage4_faithfulness.py`, `src/stage4_classify.py`, `src/stage4_rules_table.py`. Outputs: `outputs/table2_phase_distribution.csv`, `outputs/stage4_faithfulness_phase_counts.csv`, `outputs/stage4_priority_rules.md` and `.csv`, `outputs/stage4_phase_changes_mojibake.csv` (empty), `data/interim/classified_new.parquet`.

## Plan followed

1. Port classifier v3 verbatim (frozen, rule 5). 2. Faithfulness proof on the OLD narratives; stop if not exact. 3. Run on the new extraction with whitespace stripped inside the call only (TJ decision 13). 4. Report phase changes caused by the mojibake fix. 5. Write the priority and hole-size rules as a table.

## 1. Port

`src/classifier_v3.py` is a byte-for-byte copy of `inputs/repo_before/classifier_v3.py` (SHA-256 `472e9e5e37a6c97d20477376d6f2e516ecec084e201ad82dc1f16f6174b6feb0`, `cmp` identical). No pattern, priority or logic was touched. Phases are assigned by `classify_ddr(text)`: `normalise_text` (½ ¼ ¾ ⅛ to " 1/2" etc.), then `classify_v3`.

## 2. Faithfulness check on the old text (passed)

Input: the narratives in the old `workspace.default.volve_ddr_master.sum24hr` (mojibake included), stripped, then `classify_ddr`.

- Classified 1,303, Unclassified 456, total 1,759. 1,303 + 456 = 1,759. Matches the v2 target 1,303 / 456.
- All 14 per-phase counts equal the v2 table (`phase_distribution.csv`), 14 of 14 `same = True` (`outputs/stage4_faithfulness_phase_counts.csv`).
- Row by row against the old `workspace.default.volve_ddr_classified.phase` (joined on filename): 1,759 rows, **0 mismatches**.

So the ported classifier reproduces the v2 results exactly; the proof required before running on new data holds.

## 3. New extraction (Table 2)

Input: raw `sum24Hr` from `data/interim/ddr.parquet`, stripped inside the call.

| Phase | Count | % of 1,759 | v2 | Match |
|---|---|---|---|---|
| Reservoir drilling | 256 | 14.6 | 256 | yes |
| Completion | 228 | 13.0 | 228 | yes |
| Liner / Casing run | 144 | 8.2 | 144 | yes |
| Waiting / Downtime | 120 | 6.8 | 120 | yes |
| Cementing | 100 | 5.7 | 100 | yes |
| Logging / Testing | 93 | 5.3 | 93 | yes |
| Intermediate casing | 82 | 4.7 | 82 | yes |
| Intermediate drilling | 77 | 4.4 | 77 | yes |
| Surface casing | 66 | 3.8 | 66 | yes |
| Spud / Conductor | 52 | 3.0 | 52 | yes |
| P&A | 41 | 2.3 | 41 | yes |
| Rig move / Setup | 38 | 2.2 | 38 | yes |
| Workover | 6 | 0.3 | 6 | yes |
| Unclassified | 456 | 25.9 | 456 | yes |
| Total | 1,759 | | 1,759 | |

Classified: 256 + 228 + 144 + 120 + 100 + 93 + 82 + 77 + 66 + 52 + 41 + 38 + 6 = 1,303; 1,303 / 1,759 = 74.08%, reported as 74.1%. Unclassified 456 / 1,759 = 25.92%, reported as 25.9%. All match v2 (1,303, 74.1%, 456).

## 4. Effect of the mojibake fix

103 DDRs have narrative text that differs between the old table and the raw (after stripping). Running the classifier on the old text and on the new text gives **identical phases for all 1,759 rows: 0 phase changes** (including those 103). The mojibake affects characters such as `Ø` that no v3 pattern uses.

## 5. Priority order and hole-size rules (open item 3)

Paper-ready table: `outputs/stage4_priority_rules.md` (generated from `PHASES_V3`, not retyped; patterns shown in code format). Rule in one paragraph: the narrative is lower-cased and fractions normalised; each of 13 phases tests its regular expressions anywhere in the text; the matching phase with the lowest priority number is assigned; otherwise Unclassified. Priority order: 1 Spud / Conductor, 2 Surface casing, 3 Intermediate drilling, 4 Intermediate casing, 5 Reservoir drilling, 6 Liner / Casing run, 7 Cementing, 8 Completion, 9 P&A, 10 Logging / Testing, 11 Workover, 12 Waiting / Downtime, 13 Rig move / Setup.

Size-based patterns (hole or casing sizes, pattern contains a digit) per phase: Spud 3 of 5, Surface casing 6 of 6, Intermediate drilling 4 of 4, Intermediate casing 8 of 8, Reservoir drilling 11 of 13, Liner / Casing 15 of 17, Cementing 4 of 10, Completion 0 of 11, P&A 7 of 12, Logging 1 of 16, Workover 1 of 5, Waiting 2 of 10, Rig move 3 of 7. (Caveat: "contains a digit" also catches `\b`-free patterns such as `P.U.`-type items; the split in the markdown table is the mechanical rule, not a hand judgement.)

Overlap statistics (new, useful for the paper's explanation of the priority rule):

| DDRs matching | 0 phases | 1 phase | 2 phases | 3 or more |
|---|---|---|---|---|
| Count | 456 | 781 | 376 | 146 |

456 + 781 + 376 + 146 = 1,759. Total pattern matches across phases 2,014; assigned 1,303; the 711 others lost to a higher-priority phase (2,014 - 1,303 = 711, equal to the sum of the "assigned elsewhere" column in the CSV). Most frequent winner over loser: Reservoir drilling over Logging / Testing (63), Intermediate casing over Liner / Casing run (53), Liner / Casing run over Completion (45), Completion over Logging / Testing (41), Cementing over P&A (41).

## Findings logged, not acted on

`notes/classifier_gaps.md` now has two entries: non-ASCII characters not normalised (from Stage 3) and the dead `8½` pattern in Reservoir drilling (matches 0 of 1,759 normalised narratives).

## Next

Stage 5 (timeline dataset), run next as instructed.
