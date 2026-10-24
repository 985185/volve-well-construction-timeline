# Stage 7: NOD validation

Date: 2026-10-24. Branch: `rerun-2026-10`. Scripts: `src/stage7_td.py`, `src/stage7_spud.py`, `src/stage7_spud_evidence.py`. Outputs: `outputs/td_validation.csv`, `outputs/spud_validation.csv` (numbers and categories only, no narrative text). Evidence snippets with narrative text: `local_private/stage7_spud_evidence.txt` (untracked).

NOD source: `data/raw/nod/wellbore_{development,exploration}_all_20261024.csv` (27 Volve records: 22 development + 5 exploration). Compared with the 2026-09-08 snapshot in Stage 1: identical except the sync date.

**Status: complete. Total depth and spud counts equal every v2 value. One caveat about the spud rules needs TJ's attention (section 2).**

## 1. Total depth (26 WITSML wellbores)

WITSML depth = maximum valid `md_m` per wellbore in `outputs/timeline.csv`. Rules:

- **Exact** means |WITSML - NOD| <= 0.5 m (CLAUDE.md tolerance).
- Match by exact NOD name first.
- **Technical-sidetrack rule:** a WITSML wellbore whose name ends in T2 is matched to the NOD record in the same well family whose total depth agrees within the exact tolerance, preferring the parent designation. The WITSML parent leg whose NOD record was claimed this way is reported **unmatched** (abandoned parent leg). Resulting pairs: 15/9-19 BT2 to NOD 15/9-19 B (4,250 m), 15/9-19 ST2 to NOD 15/9-19 SR (4,641 m), 15/9-F-11 T2 to NOD 15/9-F-11 (4,562.1 vs 4,562.0 m, diff 0.1).

| Outcome | Count | v2 | Wellbores |
|---|---|---|---|
| Exact (<= 0.5 m) | 22 | 22 | all other wellbores |
| Close, not exact | 2 | 2 | 15/9-F-15: 4,090 vs 4,105 m, 15 m; 15/9-19 S: 3,353 vs 3,580 m, 227 m |
| Unmatched | 2 | 2 | 15/9-19 B (3,272 m), 15/9-F-11 (347 m) |
| Total | 26 | 26 | 22 + 2 + 2 = 26 |
| Matched | 24 | 24 | 22 + 2 = 24 |

Row by row against `inputs/repo_before/data/td_validation.csv` (wellbore, WITSML depth, NOD record, NOD depth, outcome): 0 differences in 26 rows.

NOD Volve records: 27 = 24 matched + 3 with no WITSML counterpart (15/9-F-10 A and F-10 B, status "WILL NEVER BE DRILLED"; 15/9-19 SR2, a 1997 NOD wellbore with TD 4,644 m and no WITSML DDRs). 24 + 3 = 27.

## 2. Spud dates

### What v2 actually did

**The spud categories were assigned by inspection of the three sources for each wellbore; the rules below were formalised afterwards to describe those assignments.** They are a description of the judgement, not an algorithm that produced it (TJ decision 30; this wording goes in the manuscript).

v2 had no coded tolerance: the v2 manuscript still carries `[TJ: define the tolerance for "Exact" ... and the day range that separates a definitional offset from an error]`, and no script that produced `spud_validation.csv` exists in `inputs/`, the Databricks export, or `C:\Volve` (searched). The labels were assigned by judgement and explained row by row in the `notes` column. What I recovered is therefore a rule set that is *consistent with every v2 label and note*, not a stated v2 algorithm. This matters for the claim of independence: the dates are recomputed from raw data and the new NOD snapshot, but the category logic is fitted to v2's calls.

Definitions: W = WITSML dTimSpud (date); F = first genuine DDR date (the 1980 sentinel ignored); T = free-text operational start date from the early narratives (taken from v2, checked below); N = NOD entry date, using the main entry or the predrill entry, whichever is closer to the anchor (anchor = T if present, else F). Days are calendar-date differences. Rules, first that fires wins:

| Rule | Category | Condition (all days) | Source in v2 notes |
|---|---|---|---|
| R1 | Inherited parent spud | sidetrack whose W equals its parent's W | F-11 A, F-11 T2 notes |
| R5 | Shared NOD record | the NOD record belongs, by TD matching, to a T2 sidetrack: the T2 leg is Unresolved; the parent leg is Definitional offset only if it has no free-text spud date of its own | 19 B / 19 BT2 notes; F-11 note |
| R2 | WITSML data-entry error | abs(W - anchor) > 30 and abs(N - anchor) <= 3 | F-4, F-7, F-12, F-15 notes (smallest observed gap 91 days) |
| R3 | Wellbore-identity conflation | abs(W - F) <= 7 and abs(N - W) > 365 | F-1 note |
| R4 | Exact | abs(W - N) <= 1 and 0 <= anchor - W <= 1 | EXACT_MATCH notes ("agree exactly", first report 1 day later) |
| R6 | Definitional offset | abs(W - N) <= 8 and 2 <= T - W <= 20 | F-1 A/B/C, F-5, F-9 A, F-11 B, F-14 notes |
| R7 | Unresolved | everything else | 19 S, 19 ST2, F-9 |

Honest caveats on the rules:

1. The numeric limits (30, 3, 7, 365, 1, 8, 2, 20 days) are the envelope of the v2 cases, not independently chosen. Open item 5 (tolerance definitions) is therefore closed only in the sense "stated explicitly"; if TJ wants round, defensible limits for the paper they can be set, and the categories would not change as long as they stay outside the gaps in the data.
2. R5 is the least certain rule. It is a special case for the two parent legs whose NOD record was claimed by a technical sidetrack (19 B, F-11). My first version of R5 made F-11 Definitional (9 definitional and 6 exact, against v2's 8 and 7); the v2 notes say F-11 is Exact because its free text explicitly records the spud the next day, and 19 B had no free text, so I restricted the parent-leg clause to legs without their own free-text spud date. That change fixed one row and was made after seeing the mismatch; it is documented here and not hidden.
3. T comes from v2's free-text readings (not re-derived by an algorithm). All 23 T dates exist as DDRs for that wellbore on that date; 19 of 23 narratives contain a spud/kick-off keyword. The other four (19 BT2 and 19 ST2, recorded in v2 as a "transfer" and a "depth sequence" transition, and F-15 B and F-15 C, recorded as same-day renames/kick-offs) cannot be checked by keyword. No category depends on them: for F-15 B and F-15 C, T equals the first-DDR date F, and 19 BT2 and 19 ST2 are Unresolved by R5 regardless of T.
4. NOD date choice: for all 26 wellbores the date my rule selects is the date v2 used (`nod_date_used`): 26 of 26.

### Result

| Category (v2 label) | Rerun | v2 | Wellbores |
|---|---|---|---|
| Exact (EXACT_MATCH) | 7 | 7 | 19 A, F-10, F-11, F-15 A, F-15 B, F-15 C, F-15 D |
| Definitional offset | 8 | 8 | 19 B, F-1 A, F-1 B, F-1 C, F-5, F-9 A, F-11 B, F-14 |
| WITSML data-entry error | 4 | 4 | F-4, F-7, F-12, F-15 |
| Wellbore-identity conflation | 1 | 1 | F-1 |
| Inherited parent spud date | 2 | 2 | F-11 A, F-11 T2 |
| Unresolved | 4 | 4 | 19 BT2, 19 S, 19 ST2, F-9 |
| Total | 26 | 26 | 7 + 8 + 4 + 1 + 2 + 4 = 26 |

All 26 rows have the same category as `spud_validation.csv` in v2 (0 differences). Days W minus N and the other differences are in `outputs/spud_validation.csv` (used for Fig. 4). Examples: F-12 W - N = -91 days; F-15 +340; F-1 -2,064; F-4 -91 (against the predrill entry); F-7 -138; F-9 A -8; F-1 A -3; F-14 -2; F-15 C +1.

Note for the paper: v2 Fig. 4 shows 25 wellbores (F-11 T2 excluded because NOD has no separate record); `outputs/spud_validation.csv` has `nod_entry_date` empty for it.

## Tracked v2 CSVs and the 15-word quote rule

`inputs/repo_before/data/spud_validation.csv` (7 rows) and `sidetrack_relationships.csv` (4 rows) contain quoted DDR text in their `notes` columns that runs to 16 to 42 words in places (counted between quote marks; some of these spans are my own prose between quotes, so the count is an upper bound). They are tracked locally, and the spud file is already on public `master` as `data/spud_validation.csv`. I have not changed them. Options for TJ: trim the quoted fragments to 15 words in the `inputs/` copies (needs one more history rewrite), and decide what to do about the file on `master` (a normal commit removes the text from the new tree but not from `master`'s history).

## Next

Stage 8 (kick-off recovery), then stop and show the 15/9-F-1 C result in full.
