# Stage 6: Audit

Date: 2026-10-24. Branch: `rerun-2026-10`. Scripts: `src/stage6_prepare.py`, `src/stage6_blind_workbook.py`. Interim: `data/interim/audit_frame.parquet`, `data/interim/audit_old50_filename_map.csv`. Output for TJ: `outputs/audit_blind_review.xlsx` (gitignored, contains narrative text).

**Status: complete, no discrepancy.** TJ resolved open item 4 (he made all 50 calls himself) and cancelled the blind review; his original calls in `inputs/old_audit/audit_adjudicated.csv` are the official adjudication (decision 25). The blind workbook was deleted. Scripts: `src/stage6_prepare.py`, `src/stage6_estimates.py`. Published output: `outputs/audit_adjudications.csv` (filename, wellbore, date, stratum, call, miss_reason; no narrative text, no reason text).

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

## Narrative handling (decision 26)

Done as option (a). The unpushed local history was rewritten twice: first to drop the `sum24hr` column from `inputs/old_audit/audit_adjudicated.csv` and `audit_sample.csv`, then to cut two quoted fragments in the `reason` column that exceeded 15 words (17 and 16 words) to their first 15 words plus " ...". Backup tags and reflog were removed and the object store pruned: the old commits no longer exist (`git cat-file` on the old commit id fails), and a search for a distinctive narrative string in every reachable commit finds nothing. The full-text originals are in the gitignored folder `local_private/old_audit/` (SHA-256: `audit_adjudicated.csv` `6e5a5666...ea041`, `audit_sample.csv` `ed20f2eb...32b50`, identical to the Sept sources). All commit hashes from Stage 0-1 onward changed because of the rewrite (nothing had been pushed). `inputs/repo_before/data/spud_validation.csv` still carries short DDR quotes; checked in Stage 7.

## Results from TJ's original calls (arithmetic)

Frame 383 = 296 construction era + 87 production era.

| Quantity | Rerun | v2 | Match |
|---|---|---|---|
| CONSTRUCTION / NON_CONSTRUCTION | 26 / 24 of 50 | 26 / 24 | yes |
| Construction era | 23 of 39 | 23 of 39 | yes |
| Production era | 3 of 11 | 3 of 11 | yes |
| Miss reasons (26) | NO_HOLE_SIZE 9, OTHER_MISS 10, NONSTANDARD_TERMINOLOGY 7 (9 + 10 + 7 = 26) | 9 / 10 / 7 | yes |
| Sample proportion | 26/50 = 0.5200 | 0.520 | yes |
| Wilson 95% (z = 1.96, n = 50) | 0.3851 to 0.6520 | 0.385 to 0.652 | yes |
| Scale | 383/1,759 = 0.2177 | 0.2177 | yes |
| Observed rate | 1,303/1,759 = 0.7408 | 0.7408 | yes |
| Residual miss | 0.5200 x 0.2177 = 0.1132 (11.3 pp, 0.52 x 383 = about 199 DDRs) | 0.1132, about 199 | yes |
| Attainable rate | 0.7408 + 0.1132 = 0.8540, **85.4%** | 85.4% | yes |
| Attainable 95% CI | 0.7408 + 0.3851 x 0.2177 = 0.8246; 0.7408 + 0.6520 x 0.2177 = 0.8827; **82.5 to 88.3%** | 82.5 to 88.3% | yes |
| Stratum-weighted proportion | (296/383) x (23/39) + (87/383) x (3/11) = 0.7728 x 0.5897 + 0.2272 x 0.2727 = 0.4558 + 0.0620 = 0.5177 | 0.518 | yes |
| Stratum-weighted rate | 0.7408 + 0.5177 x 0.2177 = 0.8535, **85.3%** | 85.3% | yes |
| EMPTY_RECORD floor | 73/1,759 = 0.0415, **4.2%** | 4.2% | yes |

Every estimate equals its v2 value, as expected because the calls are the original ones and the frame, strata and counts reproduced exactly (the 50 records map one-to-one to raw DDR files, see above). The classification rate is not changed by the Stage 3 placeholder, rig or forecast decisions.

Limitations carried into the paper unchanged (decision 6): the two known stratum misassignments (15/9-19 A 1980 sentinel; 15/9-F-1 2013 re-entry) are disclosed, not fixed. Single adjudicator (TJ), no inter-rater agreement measured, as in v2.

## For Stage 12

- Open item 4: state that the author made all 50 calls. The AI-disclosure note about audit adjudication can be cleared.
- The text "almost certainly the product of a Python str(None) conversion" (Section 4) must go: the raw XML contains "None" (decision 12).
- Sentence "59 entries ... exact query": re-derive from the new registry.
