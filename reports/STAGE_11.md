# Stage 11: Numbers registry

Date: 2026-10-24. Branch: `rerun-2026-10`. Script: `src/stage11_registry.py`. Outputs: `outputs/numbers_registry.json` (211 entries), `outputs/registry_comparison_v2.csv`, `outputs/registry_comparison_old.csv`, `outputs/registry_coverage.csv`.

**Status: complete. Kick-off and duration-derived entries are PROVISIONAL (AI-proposed kick-off depths, pending author verification). Stage 12 must not finalise them until TJ fills the author columns of `outputs/kickoff_signoff.xlsx`.**

## The registry

Each entry has: id, value, description, producer (script and function; the scripts are procedural, so the function is the block or helper that computes it), inputs (SHA-256 of every input file), timestamp (UTC), the v2 value, status against v2 (SAME, CHANGED or NEW) and a provisional flag. Values are read from the earlier stages' output files by code, not typed. Many entries are tables (Table 3 total depth, the spud table, the kick-off table, the duration table, the family summary) held as one entry each.

| Count | |
|---|---|
| Entries | 211 |
| SAME as v2 | 155 |
| CHANGED against v2 | 23 |
| NEW (no v2 counterpart) | 33 |
| PROVISIONAL | 41 (all kick-off entries and the drilled-length and rate table) |

The v2 registry had 59 entries; the rerun has 211 because it registers every number in the tables and the kick-off, duration, placeholder and classifier-overlap results separately. The sentence in the manuscript that quotes "59 entries" must be rewritten from the new count.

## Comparison with the v2 targets in CLAUDE.md

Every v2 target in the CLAUDE.md table is reproduced exactly, except where the rows below say otherwise: 1,759 DDRs, 26 wellbores, 11 families; 73 "None" narratives, 331 `-999.99`, 7 zero depths; 1,686 genuine narratives (95.85%); 248 md_kickoff (14.10%); ½ and ¼ (61 DDRs 82 occurrences, 10 DDRs 14 occurrences); 1,303 classified (74.1%) and 456 unclassified; all 13 phase counts; BOP_RISER 147 of 456; audit frame 383, strata 296 + 87, allocation 39 + 11; 26 of 50 (23 of 39 and 3 of 11; misses 9, 10, 7); Wilson 0.385 to 0.652; attainable rate 85.4% (82.5 to 88.3%), stratum-weighted 85.3%; floor 4.2%; 1,421 timeline rows; TD 24 matched, 22 exact, F-15 15 m, 19 S 227 m, unmatched 19 B (3,272 m) and F-11 (347 m); spud 7, 8, 4, 1, 2, 4.

## (a) Every number that differs from v2

| Item | v2 | Rerun | Why |
|---|---|---|---|
| Table 1, rig populated | 1,759 (100.0%) | 1,758 (99.94%) | old column held the constant `name`; one DDR (the 1980 sentinel) has no rig. Decision 17 |
| Table 1, forecast24hr populated | 1,759 (100.0%) | 1,656 (94.14%), 103 literal "None" excluded | consistency with sum24Hr. Decision 18 (deliberate change) |
| Placeholder total | 411 | 515 | 331 + 7 + 73 = 411 in v2; the full register adds 103 forecast "None" and 1 date sentinel (176 + 331 + 7 + 0 + 1 = 515). Decision 19 |
| WITSML version | 1.4.1.1 | 1.4.0.0 | the files declare 1.4.0.0 in all 1,759. Decision 15; the Energistics reference also needs checking in Stage 12 |
| NOD snapshot date | 2026-09-08 | 2026-10-24 | refreshed; the Volve subset is identical except the sync date |
| Years from the 1980 sentinel to 19 A's first genuine DDR | 17.5 | 17.56 (rounds to 17.6) | 6,415 days / 365.25; v2 appears to have truncated |
| Kick-off depth F-1 A | 3,004 m | 2,620 m | v2 depth was the depth reached on the first F-1 A report (PROVISIONAL) |
| Kick-off depth F-1 B | 3,100 m | 2,617 m | v2 depth was a section start (PROVISIONAL) |
| Kick-off depth F-1 C | 3,059 m | 1,364 m | v2 depth was the 8 1/2 in. section start (PROVISIONAL) |
| Kick-off depth F-9 A | 459 m | 421.5 m in the table; 428.2 m proposed | v2 depth was where the first report starts drilling below the window (PROVISIONAL) |
| Kick-off depth F-11 B | 3,271 m | 2,589 m in the table; 2,531 m proposed | v2 depth was the 8 1/2 in. section start (PROVISIONAL) |
| Kick-off depth F-11 T2 | 257 m | 246 m | uniform rule, start of oriented drilling (PROVISIONAL) |
| Kick-off depth 15/9-19 A | not in the v2 table | 2,178 m in the table; 2,183 m proposed | the 15th sidetrack (PROVISIONAL) |
| Kick-off methods | 12 free text, 2 depth sequence, 1 unknown | 11 depth in text, 3 event in text with depth from md, 1 depth sequence (narrative empty); 15 recovered | new method wording and 19 A (PROVISIONAL) |
| F-1 C: NOD minus DDR kick-off | 1,695 m | 0 m | follows from the F-1 C depth (PROVISIONAL) |
| F-1 family shared hole | above 3,059 m ("F-1 / F-1 C") | all four above 1,364 m; F-1, F-1 A and F-1 B above about 2,617 to 2,620 m | decision 34 (PROVISIONAL) |
| Number of registry entries | 59 | 211 | see above |

Also changed in content though not in a number: the statement that the 73 "None" narratives are an extraction artefact (they are in the source XML); the statement that the raw XML was not accessible (it was downloaded and hashed in Stage 1, 1,759 files, 21,315,879 bytes); the `days_from_first_ddr` wording in Section 5.3 and the Fig. 2 caption (counts from each wellbore's first row with a usable depth); the AI disclosure (open item 4 resolved: author made the 50 calls; kick-off depths AI-proposed); Fig. 3 and Fig. 4 captions (24 and 25 wellbores, Fig. 4 offset convention, see Stage 10).

From the old registry rather than v2 (for the record): the old registry's attainable rate 87.6% and its propagated interval 84.1 to 91.0% used 456/1,759; the v2 manuscript and this rerun use 383/1,759 (85.4%, 82.5 to 88.3%).

## (b) Kick-off rows where the AI proposal differs from the Stage 8b table (3)

| Sidetrack | Table (m) | Proposed (m) | Reason in one line |
|---|---|---|---|
| 15/9-19 A | 2,178 | 2,183 | the window is milled 2178-2183 m with formation drilled below it, so the departure is at the window bottom under the strict first tier; 2,178 m is the window-start fallback |
| 15/9-F-9 A | 421.5 | 428.2 | same reading: window 421.5 to 428.2 m, formation drilled below; NOD 428 m |
| 15/9-F-11 B | 2,589 | 2,531 | the 2,531 to 2,589 m cement-and-new-formation interval gives no first-formation depth, so the kick-off-start fallback 2,531 m applies |

The other 12 rows are marked Y. F-1 C stays at 1,364 m, F-11 T2 at 246 m, 19 ST2 at 1,536 m and 19 B at 2,231 m. Full reasons are in `outputs/kickoff_signoff.xlsx`.

## Comparison with the old 59-entry registry (`outputs/registry_comparison_old.csv`)

34 old entries have a counterpart and were compared; 25 are narratives, process notes or stop-and-report records and were not compared. Of the 34: 24 SAME, and 10 differ or need a note: rig 100.0 to 99.94 and forecast24hr 100.0 to 94.14 (changed on purpose); F-1 C kick-off 3,059 to 1,364 (provisional); the free-text, depth-sequence and not-recoverable kick-off counts (changed definitions and the 15th sidetrack); the old 87.6% rate and its interval; and `sum24hr_CORRECTED` 95.9 against 95.85 (rounding). `stage4_partA_leak_check` was not rerun (re-testing the frozen patterns on the unclassified set is true by construction and 456 unclassified is reproduced).

## Coverage of the v2 manuscript (`outputs/registry_coverage.csv`)

Numeric tokens in the v2 manuscript body (before the references) and its four tables: 792. In the registry: 759. Ignored with a reason: 32 (18 section numbers, 8 years, 3 identifiers, 2 quotes of the `-999.99` string, 1 figure from a cited study). Not in the registry: 1 (a section reference inside a Table 2 cell). Caveat: the match is by numeric value only, so it shows that each number is available in the registry, not that the number is attached to the right sentence; Stage 12 will check each sentence. Two figures are carried as external, not reproduced by code: 15/9-19 S suspended at 3,569.0 m (TVD 2,394.0 m), which is NOD web-page text (from the old registry); the 2,741 m stuck-pipe depth was checked and is in the 19 S narratives of 1992-12-10 and 1992-12-11.

## Stop

As instructed, stopping after Stage 11. Stage 12 (manuscript) must not finalise kick-off numbers until TJ has filled the author columns. Open items that remain: 5 (spud tolerances are now stated explicitly but fitted to v2's labels), 6 (Sidahmed et al. 2015 title and authors on OnePetro, needs TJ), 7 (licence: narrative text is not published; TJ's listing note for the repo is still not recorded), and the Energistics version and year.
