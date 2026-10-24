# Stage 3: Data quality

Date: 2026-10-24. Branch: `rerun-2026-10`. Script: `src/stage3_quality.py`. Outputs: `outputs/stage3_table1_field_population.csv`, `outputs/stage3_unicode_survey.csv`, `outputs/stage3_spud_vs_first_ddr.csv`. Input: `data/interim/ddr.parquet` (raw strings).

**STOPPED at the end of Stage 3 because one value differs from v2 (Table 1, `rig`). Stages 4 and 5 were not run. Waiting for TJ.**

## Discrepancy: rig population

| | v2 (Table 1) | Rerun |
|---|---|---|
| rig populated | 100.0%, 1,759 | **99.94%, 1,758** |

Arithmetic: 1,759 DDRs - 1 DDR with no `rigAlias` named "NPD Name" = 1,758; 1,758 / 1,759 = 99.94%.

Cause (verified): v2 took the count from the old `volve_ddr_master.rig` column, which holds the literal string `name` in all 1,759 rows (Stage 2 finding, decision 14). A column filled with a constant is trivially 100% populated. The one DDR without a rig is `15_9_19_A_1980_01_01.xml`, the 1980-01-01 sentinel record, which also has no `operator` and no `mdCsgLast` and whose narrative is "None". It is the same single record that explains `operator` 1,758 (a v2 value that does match).

Effect: the Table 1 `rig` row changes from 1,759 (100.0%) to 1,758 (99.94%). The rerun value wins only after TJ confirms. Proposed Stage 12 change: update the cell, and say in the notes column "1 record missing", as for `operator`.

## Table 1: population by column (n = 1,759)

Convention (same as v2): a field is populated if the tag is present and non-blank; `md_m` also excludes the `-999.99` sentinel and zero; sum24Hr excludes the literal "None".

| Column | v2 | Rerun % | Rerun count | Match | Note |
|---|---|---|---|---|---|
| date_report | 100.0% / 1,759 | 100.00 | 1,759 | yes | |
| spud_date (dTimSpud) | 100.0% / 1,759 | 100.00 | 1,759 | yes | |
| rig | 100.0% / 1,759 | 99.94 | 1,758 | **NO** | see above |
| forecast24hr | 100.0% / 1,759 | 100.00 | 1,759 | yes | 103 of these are the literal "None" (see below) |
| operator | 99.94% / 1,758 | 99.94 | 1,758 | yes | 1 record missing |
| md_csg_last_m | 96.76% / 1,702 | 96.76 | 1,702 | yes | 1,759 - 57 absent = 1,702 |
| sum24Hr (genuine narrative) | 95.85% / 1,686 | 95.85 | 1,686 | yes | 1,759 - 73 literal None = 1,686; 1,686 / 1,759 = 95.85% |
| drill_complete | 91.70% / 1,613 | 91.70 | 1,613 | yes | 1,759 - 146 absent = 1,613 |
| md_m (excl. sentinel and zero) | 80.78% / 1,421 | 80.78 | 1,421 | yes | 1,759 - 331 - 7 = 1,421; 1,421 / 1,759 = 80.78% |
| md_kickoff_m | 14.10% / 248 | 14.10 | 248 | yes | 1,759 - 1,511 absent = 248 |

## Depth placeholders

| Field | Blank/absent | `-999.99` | exactly `0` | Other non-numeric | Negative (non-sentinel) |
|---|---|---|---|---|---|
| md | 0 | **331** | **7** | 0 | 0 |
| md_kickoff | 1,511 | 0 | 0 | 0 | 0 |
| md_csg_last | 57 | 0 | 0 | 0 | 0 |

v2 targets 331 and 7: both match. 331 + 7 = 338 unusable `md` values (open item 8 mentions a "411 placeholder total"; 331 + 7 + 73 = 411 is the only combination of the counts above that gives it, but I have not confirmed that this is what v2 meant, so it is for Stage 11 to confirm). All 7 zero values are the exact string `0`.

## Literal "None" strings (after strip)

| Field | Count |
|---|---|
| sum24Hr | **73** (v2 target 73: match) |
| forecast24hr | 103 (not a v2 number; v2 counted forecast24hr as 100% populated) |
| well, wellbore, operator, rig, drill_complete | 0 |

56 DDRs have "None" in both sum24Hr and forecast24hr. All "None" values are in the raw XML (Stage 2). The forecast24hr literal "None" count (103) is new and should be mentioned next to the Table 1 forecast24hr row if TJ wants consistent treatment (a "genuine forecast" population would be 1,759 - 103 = 1,656, 94.15%). Not changed unless TJ says so.

## Unicode survey

Counts of DDRs containing the character (and total occurrences):

| Character | sum24Hr DDRs | sum24Hr occ. | v2 target | forecast24hr DDRs | forecast24hr occ. |
|---|---|---|---|---|---|
| ½ | 61 | 82 | 61 DDRs (82 occ.): match | 53 | 70 |
| ¼ | 10 | 14 | 10 DDRs (14 occ.): match | 6 | 9 |
| ¾ | 0 | 0 | | 0 | 0 |
| ⅛ | 0 | 0 | | 0 | 0 |

All non-ASCII characters in the two narrative fields combined: ½ 152, ³ 31, ¼ 23, Ø 13, æ 9, ¿ 3, Æ 2, Å 1. 70 sum24Hr DDRs contain ½ or ¼ (61 + 10 = 71, so 1 DDR contains both). Classifier note: `normalise_text` only handles ½ ¼ ¾ ⅛. The other characters (³ Ø æ ¿ Æ Å) are not handled, which is v3 behaviour and stays frozen. `³` occurs 31 times (e.g. m³); `¿` 3 times (likely a bad character in the source).

## Date sentinels and date checks

- All 1,759 `date_report` and `dTimSpud` values parse as dates.
- **One date sentinel: `15_9_19_A_1980_01_01.xml`** (date_report 1980-01-01, the only date before 1990). It is also the "None"/`-999.99`/no-rig/no-operator record. The next 15/9-19 A DDR is 1997-07-25, a gap of 6,415 days.
- Other DDRs dated Jan 1 (15/9-19 BT2 1998, ST2 1993, F-12 2008, F-15 A 2009, F-15 D 2014) are in the middle of normal campaigns and are not treated as sentinels.
- No `dTimSpud` falls on 1 January. Range of dTimSpud: 1992-09-15 to 2014-02-21. date_report range: 1980-01-01 to 2018-01-25 (excluding the sentinel, 1992-09-09 to 2018-01-25).
- Each wellbore has exactly one distinct `dTimSpud`.
- `dTimSpud` minus first DDR date, in days (negative: spud before first report). Most wellbores are -4 to 0. Large values to check in Stage 7: 15/9-19 A +6,415 (sentinel), 15/9-F-15 +340 (first DDR 2007-11-19, spud 2008-10-24), 15/9-19 S +9, and large negatives for the sidetracks that inherit the parent spud (F-11 A -69, F-11 T2 -17, 19 ST2 -95) and F-12 -91, F-4 -92, F-7 -137. Full table in `outputs/stage3_spud_vs_first_ddr.csv`.
- 46 DDRs are dated before their wellbore's dTimSpud. 909 DDRs are dated after the wellbore's drill_complete date (expected for production-era reports).
- Gaps of more than 365 days between consecutive DDRs in one wellbore: 24 (largest: 15/9-19 A 6,415 days, 15/9-F-15 3,331 days before its 2018-01-25 report, 15/9-F-7 2,673, 15/9-F-1 2,056). Reproduce with `src/stage3_quality.py`. These are the structure behind the construction-era vs production-era strata (Stage 6, kept as in v2).

## Summary against v2 targets

| Item | v2 | Rerun | Match |
|---|---|---|---|
| Genuine narratives | 1,686 (95.85%) | 1,686 (95.85%) | yes |
| "None" narratives | 73 | 73 | yes |
| `-999.99` / `0` depths | 331 / 7 | 331 / 7 | yes |
| md_kickoff populated | 248 (14.10%) | 248 (14.10%) | yes |
| ½ / ¼ | 61 (82) / 10 (14) | 61 (82) / 10 (14) | yes |
| Table 1 rig | 1,759 (100.0%) | 1,758 (99.94%) | **no** |

## Needed from TJ

1. Confirm the `rig` change (1,759 to 1,758, 99.94%, cause: the old column held the constant `name`). The other nine Table 1 rows match.
2. Say whether to add the forecast24hr "None" count (103) to the Table 1 notes.
3. After that I resume with Stage 4 as instructed (frozen classifier, faithfulness check first, then the new extraction, then Stage 5).
