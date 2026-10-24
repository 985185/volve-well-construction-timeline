# Decisions log (append-only)

## 2026-10-24, after Stage 0

1. **Raw XML source.** Search local drives first (C:\Volve, then the rest of C:). If the DDR XML is not found, TJ downloads the "Daily Drilling Report - XML Version" folder from Equinor himself. Do not try to repair the Marketplace share.
2. **Old audit files copied (not moved) into `inputs/old_audit/`.**

   | File in repo | Source path | SHA-256 |
   |---|---|---|
   | `inputs/old_audit/audit_adjudicated.csv` | `C:\Volve\paper2_rebuild\audit_adjudicated.csv` | `6e5a566672f0a2612888fb9426ab3a5a52234a64b978caa2716d813f88aea041` |
   | `inputs/old_audit/audit_sample.csv` | `C:\Volve\paper2_rebuild\audit_sample.csv` | `ed20f2eb5bb201b8847366460be804f912e5e2caf27c7b5e9cc0c92823532b50` |
   | `inputs/old_audit/sampling_frame.json` | `C:\Volve\paper2_rebuild\sampling_frame.json` | `72506e0a3d4ea339a609497899036a904ff80b04375465389bb1acd4ed823b09` |
   | `inputs/old_audit/numbers_registry_59entry.json` | `C:\Volve\paper2_rebuild\numbers_registry.json` | `a52ef2caba60fb53d6bcc8c06568ccb93e97f44d14a31ff237aca81216a5804d` |

   Hashes were computed on the source files and re-checked on the copies; they match. The 59-entry registry supersedes the 53-entry `inputs/repo_before/data/numbers_registry.json`, which is kept unchanged as part of the "before" state.
3. **Python 3.10 is acceptable** for the venv.
4. **Latest manuscript (`inputs/paper2_v2.docx`):** the answer in TJ's reply was left as an unfilled template. Treated as UNANSWERED. Working assumption for now is that `inputs/paper2_v2.docx` is the base; TJ to confirm before Stage 12.
5. **Adjudicator identity (open item 4):** the answer in TJ's reply was left as an unfilled template. UNANSWERED. Nothing is assumed. TJ to answer before Stage 6 and before the AI disclosure is finalised.
6. **Stage 6 audit decision (TJ).** Keep the existing 50-record sample and the original stratification (construction era = date_report within 730 days of the wellbore's first DDR, 1980 sentinel included, as in v2: 296 + 87, allocation 39 + 11). Map each record to its filename by wellbore + date and verify the mapping is one-to-one. Do not redraw the sample. Do not apply the 1980 stratum fix; the two known stratum misassignments (15/9-19 A 1980 sentinel, 15/9-F-1 2013 re-entry) become a stated limitation in the paper. This supersedes the earlier CLAUDE.md Stage 6 wording; CLAUDE.md has been updated to match.

## 2026-10-24, Stage 1

7. **Manuscript base confirmed (TJ):** `inputs/paper2_v2.docx` is the latest manuscript.
8. **Adjudicator identity (open item 4):** STILL UNANSWERED. TJ's reply again contained the unfilled template. Nothing assumed; needed before Stage 6.
9. **Licence note:** TJ's reply contained an unfilled placeholder instead of the listing's sharing terms. NOT RECORDED. Needed for open item 7 and the README (Stage 13). Until then the repo must not be assumed to permit redistributing DDR narrative text.
10. **Raw DDR route.** TJ re-added the Volve Marketplace listing (the reply left the date as a placeholder; catalog `equinor_asa_volve_data_village.public` created per Databricks timestamp 1792824654197 ms, i.e. 2026-10-24). Files were downloaded on 2026-10-24 with `databricks fs cp -r --overwrite` (profile `volve`, CLI v1.15.0) from `dbfs:/Volumes/equinor_asa_volve_data_village/public/volve/Well_technical_data/Daily Drilling Report - XML Version` to `data/raw/ddr_xml/`. Verified: 1,759 files, 21,315,879 bytes, zero missing or extra names, zero per-file size mismatches against `workspace.default.volve_metadata_catalog`. Manifest: `data/raw/manifest.csv`. The expected list is `data/raw/expected_from_catalog.csv`.
11. **NOD snapshot 2026-10-24.** Full national development and exploration wellbore CSV exports fetched by HTTP from the same FactPages export URLs as the Sept snapshot (see `data/raw/nod/nod_snapshot_20261024_metadata.json`). Volve subset (`15/9-F-` and `15/9-19`) is identical to the 2026-09-08 snapshot except for the `datesyncNPD` column.

## 2026-10-24, Stage 2

12. **"None" narratives (TJ):** agreed that the 73 literal "None" narratives are stored in the source archive (`<sum24Hr>None</sum24Hr>` in 73 raw XML files), not an extraction artefact. Correct the artefact claim in the registry (Stage 11, entry `stage4_discrepancy_literal_None_text`) and in the manuscript (Stage 12).
13. **Classifier input (TJ):** strip whitespace inside the classifier call only; keep raw strings in `ddr.parquet`. Stage 4 reports any phase change caused by the mojibake fix.
14. **Old `rig` column (TJ):** `workspace.default.volve_ddr_master.rig` is wrong: it holds the literal string `name` in all 1,759 rows (old extractor read the first `<name>` child). It must not be shipped, and any earlier paper that used it must be checked. Correct rigs come from `rigAlias` with namingSystem "NPD Name": MÆRSK INSPIRER 1,384, BYFORD DOLPHIN 208, TREASURE PROSPECT 166, 1 null.
15. **WITSML version:** the raw DDR files declare `drillReports version="1.4.0.0"` (all 1,759), not 1.4.1.1. In Stage 12 correct every "1.4.1.1" in the manuscript and fix the Energistics reference to the correct version, verifying the version and year first.
16. **`data/interim/` is gitignored** (regenerated from raw by code).

## 2026-10-24, Stage 3

17. **Table 1 rig (TJ):** rig populated is 1,758 (99.94%), note "1 record missing (1980 sentinel)". Replaces the v2 value 1,759 (100.0%), which came from the constant old column.
18. **Table 1 forecast24hr (TJ), deliberate change from v2:** report the genuine population excluding the 103 literal "None" strings, for consistency with sum24Hr: 1,759 - 103 = 1,656 (94.14%), note `103 literal "None" strings excluded`. v2 reported 100.0%. Eight `n/a`/`N/A` forecast strings are kept as genuine (flagged, not changed).
19. **Placeholder total (TJ):** count every placeholder in every extracted field (literal "None", `-999.99`, `0` depth, empty-but-present tags, 1980 date sentinel), tabulate by field, register the total. Result 515 cells (176 None + 331 sentinel + 7 zero + 0 empty + 1 date). v2 "411" = 331 + 7 + 73. Manuscript sentence rewritten from the registry value in Stage 12.
20. **Non-ASCII characters** ³ Ø æ ¿ Æ Å are not normalised by classifier v3 (frozen); logged in `notes/classifier_gaps.md`.

## 2026-10-24, Stage 6 instructions (TJ)

21. **Blind review.** `outputs/audit_blind_review.xlsx` holds the 50 records (record id = raw DDR file name, wellbore, date, stratum, full sum24Hr) with empty columns my_call, my_miss_reason, my_note. No old calls, categories or reasons are in it. Row order shuffled with seed 20261024 (`random.Random(20261024).shuffle` over the 50 rows sorted by filename). Stage 6 stops until TJ returns the filled file.
22. **TJ's calls are the official adjudication.** After return: compare with the old calls (agreement %, Cohen's kappa, list of disagreements), then compute all Stage 6 estimates from TJ's calls: sample proportion, Wilson 95% CI, scaling by frame / total DDRs (383 / 1,759), stratum-weighted check, floor from EMPTY_RECORD. The old calls are kept in `inputs/old_audit/` as the "before" state only.
23. **Licence / open item 7 resolved (TJ).** The public repo ships no DDR narrative text. Published audit output contains filename, wellbore, date, stratum, call and miss reason only. Consequences: `outputs/audit_blind_review*.xlsx` and filled variants are gitignored; narrative-bearing files must not be pushed (see STAGE_6.md for the files currently tracked locally that need removing before any push).
24. **Stage 12 wording (TJ).** `days_from_first_ddr` counts from each wellbore's first row with a usable depth: fix the wording in Section 5.3 and the Fig. 2 caption. Use the 515 placeholder total in the manuscript.

## 2026-10-24, open item 4 and narrative handling (TJ)

25. **Open item 4 resolved (TJ):** TJ made all 50 CONSTRUCTION / NON_CONSTRUCTION calls himself. The original calls in `inputs/old_audit/audit_adjudicated.csv` are the official adjudication. The blind review (decision 21 and 22) is cancelled and `outputs/audit_blind_review.xlsx` was deleted. Stage 6 estimates use the original calls. AI disclosure: no AI made or pre-labelled the audit adjudications (the wording in Section "Use of generative AI" can drop the amend-if note for the audit; figures and code assistance stay as disclosed).
26. **Narrative text policy (TJ):** option (a). The unpushed local history was rewritten to drop the `sum24hr` column from `inputs/old_audit/audit_adjudicated.csv` and `audit_sample.csv`. The full-text originals are kept in the untracked, gitignored folder `local_private/old_audit/` (copies of `C:\Volve\paper2_rebuild\`; SHA-256 in the Stage 6 report). Quotes of DDR text in anything committed or published are acceptable at 15 words or fewer, never full narratives; same limit for Stage 8 evidence quotes.

## 2026-10-24, Stage 8 decisions (TJ)

27. **Kick-off definition (TJ):** the kick-off depth is the depth at which the sidetrack leaves the parent wellbore (standard usage). For 15/9-F-1 C this is 1,364 m MD, matching NOD's `wlbKickOffPoint`; 3,059 m is the start of the 8 1/2 in. section, not the kick-off. v2's decision (3,059 m operational kick-off versus 1,364 m geometric departure point) is withdrawn.
28. **Cross-paper correction (TJ):** F-1 / F-1 C shared interval is above 1,364 m MD, not 3,059 m; correct in Papers 1, 3 and the barrier paper.
29. **Kick-off re-derivation (TJ):** all 15 sidetracks are re-derived under decision 27 from the parent's last report(s) and the sidetrack's first report(s) (time drilling, window milling, kick-off, sidetrack, "% formation" language). Every case where the v2 depth was a section start is flagged. 19 S's constant structured mdKickoff (562 m) is compared with NOD's value for 19 S and reported only.
30. **Spud rules wording (TJ):** the spud categories were assigned by inspection; the rules in `reports/STAGE_7.md` were formalised afterwards to describe those assignments. This wording goes in the manuscript.
31. **Quotes (TJ):** public `master` history is not rewritten. Quotes of DDR text are trimmed to 15 words or fewer in the new `inputs/` copies and in all new outputs.
