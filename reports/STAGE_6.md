# Stage 6: Audit (part A, preparation; STOPPED for TJ's blind review)

Date: 2026-10-24. Branch: `rerun-2026-10`. Scripts: `src/stage6_prepare.py`, `src/stage6_blind_workbook.py`. Interim: `data/interim/audit_frame.parquet`, `data/interim/audit_old50_filename_map.csv`. Output for TJ: `outputs/audit_blind_review.xlsx` (gitignored, contains narrative text).

**Status: waiting for TJ to fill `outputs/audit_blind_review.xlsx`.** Nothing has been compared with the old calls and no estimate has been computed. The old calls were not read into any output of this part.

## Checks before the review (all match v2, no discrepancy)

Eleven categories on the 456 unclassified (rules ported from the Sept SQL, not the frozen classifier; first match wins):

| Category | Count | v2 |
|---|---|---|
| BOP_RISER | 147 | 147 |
| EMPTY_RECORD | 73 | 73 |
| OTHER | 63 | 63 |
| GENERIC_TRIP | 61 | 61 |
| MUD_FLUID | 35 | 35 |
| WIRELINE_NON_TEST | 34 | 34 |
| PRODUCTION_MON | 30 | 30 |
| RIG_MAINTENANCE | 8 | 8 |
| WAITING_GENERIC | 3 | 3 |
| WELL_HANDOVER | 2 | 2 |
| LABOUR | 0 | 0 |

Sum: 147 + 73 + 63 + 61 + 35 + 34 + 30 + 8 + 3 + 2 + 0 = 456. Row by row against the Sept `unclassified_categories.csv` (joined on wellbore + date): 456 of 456 matched, 0 category differences.

Frame: 456 - 73 EMPTY_RECORD = **383** (v2 383). Strata, v2 definition kept per TJ (days from the wellbore's first DDR, 1980 sentinel included, <= 730): **296 construction era + 87 production era = 383** (v2 296 + 87). Allocation in the old sample 39 + 11 = 50. Scale factor 383 / 1,759 = 0.2177.

## Mapping of the old 50 records to filenames (wellbore + date)

- 50 of 50 old records map to exactly one raw DDR; 50 distinct filenames; no old record shares a key with another; no raw DDR is matched twice. **The mapping is one-to-one.**
- All 50 are in the new frame (phase Unclassified, not EMPTY_RECORD). Category agrees for 50 of 50, stratum for 50 of 50, days since first DDR for 50 of 50.
- Narrative text identical to the raw (after stripping and the mojibake repair) for 50 of 50.
- Old sample strata: 39 construction era + 11 production era.

So the original 50 records are valid members of the rerun frame and TJ's blind calls can be compared with the old ones record by record.

## Blind workbook

`outputs/audit_blind_review.xlsx`, sheet `review`: record_id (raw DDR file name), wellbore, date, stratum, sum24Hr (full text, stripped), then empty my_call, my_miss_reason, my_note, with drop-downs (my_call: CONSTRUCTION / NON_CONSTRUCTION; my_miss_reason: NO_HOLE_SIZE / OTHER_MISS / NONSTANDARD_TERMINOLOGY). No old call, category or reason appears in the file. Shuffled with seed 20261024. Sheet `info` records the seed and instructions.

## Licence consequences to act on before any push (needs TJ)

TJ's rule: the public repo ships no narrative text. Currently **tracked in local commits** (branch `rerun-2026-10`, not pushed; `origin` only has `master`):

- `inputs/old_audit/audit_adjudicated.csv` and `inputs/old_audit/audit_sample.csv`: full sum24hr narratives for the 50 records (in commit `3af2ce7`).
- `inputs/repo_before/data/spud_validation.csv`: short free-text evidence quotes from DDRs (already on `master` in `data/spud_validation.csv`).
- Stage 8's "evidence quote" column will also quote narratives; to be shortened or dropped in published output.

Not changed by me. Options: (a) rewrite the local unpushed history to remove the narrative columns from the two audit CSVs (keeps the calls and reasons; I would strip `sum24hr` and recommit), or (b) keep those files untracked and local only. I recommend (a) before the first push, then a scan of the whole tree for text. Say which, and whether `spud_validation.csv` quotes are acceptable.

## Next, when TJ returns the filled workbook (path: `outputs/audit_blind_review.xlsx`, saved over, or a new name)

1. Read my_call, my_miss_reason, my_note; check all 50 filled and valid.
2. Compare with the old calls: agreement % (n agree / 50), Cohen's kappa on CONSTRUCTION vs NON_CONSTRUCTION, 2x2 table, list of disagreements by filename; also agreement on miss reason among records both call CONSTRUCTION.
3. Estimates from TJ's calls only: construction count of 50 and by stratum; miss-reason counts; sample proportion; Wilson 95% CI; residual miss = proportion x 383 / 1,759; attainable rate = 1,303 / 1,759 + residual (v2: 85.4%, 82.5 to 88.3%); stratum-weighted check = (296/383) x p_construction_era + (87/383) x p_production_era, scaled the same way (v2 85.3%); floor from EMPTY_RECORD (73 / 1,759 = 4.15%).
4. Any value differing from v2 (26/50, Wilson 0.385 to 0.652, 85.4%, 82.5 to 88.3%, 85.3%) is reported as a discrepancy and I stop for TJ. Differences are expected only if TJ's calls differ from the old ones.
