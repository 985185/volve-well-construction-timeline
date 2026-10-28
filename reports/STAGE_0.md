# Stage 0: Access check and stock-take

Date: 2026-10-24. Branch: `rerun-2026-10`. No pipeline code was written. Only read-only checks were run, plus one test download (which failed, see 2). Nothing in `inputs/` or `C:\Volve\` was modified. Nothing was copied into the repo except this report.

## Summary

| Check | Result |
|---|---|
| Databricks auth (profile `volve`, OAuth) | OK, user <user-email> |
| `gh` auth | OK, account 985185, scopes include `repo` |
| Raw Volve volume lists | **FAIL** |
| One DDR XML downloads | **FAIL** (nothing to download from) |
| DDR XML files located via metadata catalog | OK, 1,759 files |
| Old audit (50 records and adjudications) | **Not in `inputs/`, not in Databricks.** Found on local disk at `C:\Volve\paper2_rebuild\` |
| Python version | 3.10.6 installed, CLAUDE.md and STOCKTAKE.md ask for 3.11+ |

**Blocker for Stage 1:** the raw DDR XML cannot currently be fetched from Databricks. TJ needs to decide how to get the raw files (section 2).

## 1. Databricks access

- `databricks current-user me --profile volve`: active, OAuth, <user-email>.
- Serverless SQL warehouse `187078b1fdfb9a56` ("Serverless Starter Warehouse", stopped) starts on demand and answers queries via the SQL Statement API. Catalog queries below used it.
- CLI is v1.15.0.

## 2. Raw Volve volume: not readable

Evidence:

- `databricks fs ls dbfs:/Volumes/equinor_asa_volve_data_village/public/volve/...` returns `no such directory`.
- Files API directory listing returns `Schema 'equinor_asa_volve_data_village.public' does not exist.`
- `SHOW SCHEMAS IN equinor_asa_volve_data_village` returns only `information_schema`. `SHOW VOLUMES IN ...public` fails with `SCHEMA_NOT_FOUND`.
- The catalog exists (type `DELTASHARING_CATALOG`, provider `equinorasa`, share `equinoropendata_volve`, created 2026-09-26 by epoch value, last updated 2026-10-24) but exposes no schemas, so the Marketplace reinstall did not surface the share contents. `databricks providers list-shares equinorasa` fails with "User is not an owner of Provider", so I could not see what the share contains.
- `C:\Volve\ddr_file_manifest.csv` (Sept 7) says `BLOCKED ... not accessible from this session`. So the volume may never have been readable since the restore. The "restored Sept 2026" note in CLAUDE.md is not borne out.

The only other Databricks volume is `workspace.default.exports`. It holds Paper 1 and catalog exports, not DDR XML.

**Decision needed from TJ** (options, my recommendation first):

1. Download the Volve DDR XML folder ("Daily Drilling Report - XML Version", 1,759 files, 21.3 MB per the catalog) directly from Equinor's public Volve data release to your PC, then I hash and manifest it in Stage 1. Smallest dependency, and the files are small. Needs your confirmation that the licence terms are the same ones the paper cites (open item 7).
2. Repair the Marketplace share (re-create the catalog from the Marketplace listing, or have the provider owner role checked), then I fetch via the Files API.

Either way the architecture below is unchanged: raw files land in `data/raw/ddr_xml/` and everything else is local.

## 3. DDR XML files in the metadata catalog

`workspace.default.volve_metadata_catalog` has 404,408 rows as stated. The `folder_category = 'DDR'` label is **not** the DDR XML: it holds 11,664 other WITSML Realtime XML files (wellInfo, trajectory, message) plus 229 .txt and 1 .zip. Do not use `folder_category = 'DDR'` to find DDRs.

The DDR XML files are tagged `folder_category = WELL_TECHNICAL`, `data_type = EDM_XML`, and are identified by filename pattern `_YYYY_MM_DD.xml`. Query:

```
WHERE file_name RLIKE '_[0-9]{4}_[0-9]{2}_[0-9]{2}\\.xml$'
```

Results:

| Item | Value |
|---|---|
| Files | 1,759 |
| Distinct file names | 1,759 |
| Folder | `Well_technical_data/Daily Drilling Report - XML Version` (one folder, 1,759 of 1,759) |
| Total bytes | 21,315,879 |
| Size range | 2,657 to 32,268 bytes |
| Joins to `volve_ddr_master.filename` | 1,759 of 1,759 |

So the catalog agrees with the v2 DDR count of 1,759 and every filename matches the old table. Caveats: `well_id` is a single constant value for these rows (unusable for well grouping), and the catalog lists files that existed when it was built, so Stage 1 must still count what actually downloads. The Paper 1 notebook also references a parallel "Daily Drilling Report - HTML Version" folder (not needed).

## 4. Where the Paper 2 audit lives

Searched: `inputs/databricks_export/` (all notebooks, "Paper 2.py", "Paper2_Stage0.py", CSVs), the v2 docx text, the `workspace.default` table list, and the local disk.

**Databricks export.** `Paper2_Stage0.py` is only a volume/catalog access probe, no audit. `Paper 2.py` (2,981 lines) contains an *earlier* audit version (lines ~1478 to 1750): pandas `.sample(random_state=42)`, strata defined by days from `spud_date` (< 730), and its own `AUDIT_CATEGORIES` list of ten categories. That is **not** the audit in the paper. It contains no CONSTRUCTION / NON_CONSTRUCTION judgements. The grep for `NON_CONSTRUCTION` and `adjudicat` found nothing in the export except the registry copy.

**`workspace.default` tables** (40 tables listed). None holds Paper 2 adjudications.
- `volve_ddr_unclassified_categorised`: 456 rows (73 EMPTY_RECORD), columns `wellbore, date_report, sum24hr, category` only. No sample flag, no adjudication.
- `volve_ddr_master` (1,759), `volve_ddr_classified` (`filename, wellbore, date_report, md_m, sum24hr, phase`).
- `volve_annotation_sample`, `paper1_validation_50ddr_sample*`, `volve_hazard_validation_*` belong to Paper 1 or the hazard work. Not Paper 2.

**Local disk: found.** `C:\Volve\paper2_rebuild\` (the Sept 2026 working folder, outside the repo) contains:

| File | Content |
|---|---|
| `audit_adjudicated.csv` | 50 rows. Columns: `wellbore, date_report, category, days_since_first_ddr, stratum, sum24hr, adjudication, reason, miss_reason_if_construction` |
| `audit_sample.csv` | the same 50 rows (same columns) |
| `sampling_frame.json` | frame 456 - 73 = 383; strata 296 + 87; allocation 39 + 11; seed 42 |
| `unclassified_categories.csv`, `unclassified_category_query.sql` | the eleven-category assignment for the 456 |
| `numbers_registry.json` | **59 entries** (see section 5) |
| `paper2_draft.docx` (10 Sept), NOD snapshot, validation CSVs, figures | duplicates of `inputs/repo_before/` |

Checked against the v2 targets (arithmetic from `audit_adjudicated.csv`, counted by me):

- 50 rows: 39 construction_era + 11 production_era = 50. Matches 39 + 11.
- adjudication: 26 CONSTRUCTION + 24 NON_CONSTRUCTION = 50. Matches 26 of 50.
- miss reasons among the 26: OTHER_MISS 10 + NO_HOLE_SIZE 9 + NONSTANDARD_TERMINOLOGY 7 = 26. Matches 9 / 10 / 7.
- Stratum split of CONSTRUCTION (23 and 3) is stated in the old registry note; I did not recount it per stratum in Stage 0.

**Important differences from the CLAUDE.md Stage 6 recipe** (flag for the Stage 6 plan, not acted on):

1. The old sample is identified only by `wellbore + date_report + sum24hr`, **no `filename` column**. Matching to the new extraction must be done on wellbore + date (the filename pattern is `15_9_<well>_<date>.xml`, so it is derivable).
2. The old draw used Python `random.seed(42)` and `random.sample()` per stratum, over a frame whose row order is not recorded (probably `unclassified_categories.csv` order). It was **not** pandas `.sample`. Reproducing the same 50 after "sort by filename" is therefore unlikely unless the old order happens to be filename order. I expect the "old 50 not reproduced" branch (blank workbook, stop for TJ), but Stage 6 will test it rather than assume. I can try the old row order first as a cheap check.
3. The old strata used `days_since_first_ddr <= 730` including the 1980-01-01 sentinel. The v2 docx text says "within 730 days of first DDR". CLAUDE.md fixes this by ignoring the sentinel (deliberate change, to be recorded in `notes/decisions.md`).

**Open item 4 (who adjudicated).** The files record the `reason` text but not who wrote it. The registry calls it "Manual adjudication", but the working folder is a Claude Code workspace (`C:\Volve\.claude\`), so I cannot tell from the evidence whether the CONSTRUCTION / NON_CONSTRUCTION calls were made by TJ or proposed by an AI assistant. Only TJ can answer this, and it affects the AI disclosure in the manuscript. I have not assumed either way.

## 5. `inputs/` against STOCKTAKE.md section C

| Item | Status |
|---|---|
| `paper2_v2.docx` | Present at `inputs/paper2_v2.docx`. Which version is the latest is unanswered. The only other docx is `C:\Volve\paper2_rebuild\paper2_draft.docx` (10 Sept), which looks earlier. TJ to confirm v2 is current. |
| `numbers_registry.json` | Present at `inputs/repo_before/data/` but it has **53 entries, not 59**. The `C:\Volve\paper2_rebuild\` copy has 59. The 6 missing keys are all `manuscript_revision_*` (1980 sentinel check, 19 B / 19 BT2 check, 19 S / 19 ST2 check, 19 S TD arithmetic, edits applied, NOD wellbore history ground truth). All 53 inputs keys exist in the 59-entry file. Recommend replacing the repo copy with the 59-entry file, and I will not do it without your OK. Also note the old registry entry `stage4_partE_residual_miss_rate` says 87.6% (uses 456/1759), which differs from the 85.4% in v2 (uses 383/1759). Stage 6 and 11 will need to deal with that. |
| Classifier v3 source | Present: `inputs/repo_before/classifier_v3.py` (185 lines) and `classifier_v3_sql.sql`. A second copy `C:\Volve\classifier_v3_recovered.py` (marked RECOVERED) and `classifier_v3_verbatim.sql` exist. Header comments differ; I did not diff the pattern bodies, that is Stage 4. The 13 patterns visible in `Paper 2.py` (line ~1630) are a third source to cross-check in Stage 4. |
| Audit adjudications for the 50 | **Missing from `inputs/`.** Exist at `C:\Volve\paper2_rebuild\audit_adjudicated.csv`. Need to be copied into `inputs/` (see ask below). |
| Four figure PNGs and scripts | Present in `inputs/repo_before/figures/` (figure1 to figure4, png + py). |
| NOD FactPages export (Sept) | Present: 2026-09-08 snapshot, development (22 rows) and exploration (5 rows) CSVs plus metadata JSON. Subset filtered to `15/9-F-` and `15/9-19`, not the full national table. Identical to the `C:\Volve` copies once CR characters are ignored (the repo copies have CRLF line endings; hashes will differ). |
| Validation CSVs | Present: td, spud, sidetrack_relationships, timeline (131 KB), well_inventory, phase_distribution. |

Also in `inputs/databricks_export/`: Papers 1, 3, 4 notebooks, barrier and CCUS material, `lwdtre_exports` (incl. `paper2_figure*.png` earlier figure drafts, `paper2_figure2_data.xlsx`). Per your note, the two workbook CSVs in `lwdtre_exports` are Paper 1 and were not used.

## 6. Machine and tooling

- Python: only 3.10.6 installed (`py -0` shows 3.10-64 only). STOCKTAKE asks 3.11+. The planned libraries (pandas, pyarrow, lxml, matplotlib, openpyxl, python-docx, databricks-sdk) all support 3.10, so I suggest keeping 3.10 and noting it in the README, unless you want to install 3.11.
- `.venv/` does not exist yet and `requirements.txt` is not in the repo. Created in Stage 1.
- Free disk: about 17 GB on C: (97% full). Enough.
- Git working tree was clean at start. Directories `data/`, `src/`, `outputs/`, `notes/`, `manuscript/` do not exist yet.
- Not checked in Stage 0 (outside scope or needs you): Claude Desktop MCP config token, IPTC author portal login and affiliation.

## 7. Known gaps and risks

1. **Raw data inaccessible** (section 2). Blocks Stage 1.
2. Old adjudications live outside the repo and have no `filename` key.
3. Sample reproducibility is doubtful because of the old sampler and unknown frame order (section 4).
4. Registry in `inputs/` is 6 entries short; it also holds the 87.6% vs 85.4% inconsistency.
5. Adjudicator identity unknown (open item 4).
6. The catalog's `folder_category`/`well_id` labels cannot be trusted for finding DDRs; use the filename pattern.
7. v2 targets are untouched. No computed value yet differs from a target.

## 8. Proposed architecture (for "go")

- **Fetch only on Databricks (or direct download).** Stage 1 gets the 1,759 XML files into `data/raw/ddr_xml/`, writes `data/raw/manifest.csv` (path, sha256, bytes), and takes a fresh dated NOD snapshot into `data/raw/nod/`. The expected file list comes from the catalog query above (1,759 files, 21,315,879 bytes), which becomes the completeness check.
- **Everything else local in Python 3.10 venv.** One module per stage in `src/`, intermediates in `data/interim/`, outputs in `outputs/`, figure scripts read only from `outputs/`.
- Databricks used afterwards only to read the old tables (`volve_ddr_master`, `volve_ddr_classified`, `volve_ddr_unclassified_categorised`) for the Stage 2 and 4 comparisons. These are exported once to `data/interim/old/` as comparison-only files so the later stages do not need a live connection.
- Classifier v3 ported verbatim from `inputs/repo_before/classifier_v3.py`, with the Stage 4 faithfulness proof on the old narratives before running on the new extraction.

## Asks for TJ before Stage 1

1. How to get the raw XML: option 1 (direct download from Equinor) or option 2 (repair the Marketplace share)? If option 1, tell me where the files will be, or I will give you the exact download steps.
2. OK to copy `C:\Volve\paper2_rebuild\audit_adjudicated.csv`, `audit_sample.csv`, `sampling_frame.json`, `unclassified_categories.csv` and the 59-entry `numbers_registry.json` into `inputs/` (committed as the "before" state)?
3. Is `inputs/paper2_v2.docx` the latest manuscript?
4. Who made the CONSTRUCTION / NON_CONSTRUCTION calls on the 50 records (open item 4)?
5. Python 3.10 acceptable?
6. Say "go" for the Stage 1 plan above once the raw data route is settled.
