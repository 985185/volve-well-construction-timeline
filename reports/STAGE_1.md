# Stage 1: Fetch raw

Date: 2026-10-24. Branch: `rerun-2026-10`. Status: **complete, no discrepancies against the catalog.**

## Route

The earlier local search found no DDR XML (see the previous version of this report: `C:\Volve`, all of `C:\` and the Downloads zips, 0 matches). TJ then re-added the Marketplace listing. Re-check with the Databricks CLI (profile `volve`):

- `equinor_asa_volve_data_village` now has schema `public` (owner <user-email>) and a volume.
- `databricks fs ls` on `dbfs:/Volumes/equinor_asa_volve_data_village/public/volve/Well_technical_data/Daily Drilling Report - XML Version` lists the DDR files (1,759 entries).
- Download: `databricks fs cp -r --overwrite` of that folder into `data/raw/ddr_xml/`. Wall time 8 min 16 s.

## DDR XML result

| Check | Expected (catalog) | Downloaded | Result |
|---|---|---|---|
| File count | 1,759 | 1,759 | match |
| Total bytes | 21,315,879 | 21,315,879 | match |
| Names missing / extra | 0 / 0 | 0 / 0 | match |
| Per-file size vs `volve_metadata_catalog.file_size_bytes` | 1,759 compared | 0 mismatches | match |
| Distinct SHA-256 | n/a | 1,759 | no duplicate file contents |
| First byte is `<` (after any BOM) | n/a | 1,759 of 1,759 | all look like XML |

The expected list came from the catalog with the filename pattern `_YYYY_MM_DD.xml` (`data/raw/expected_from_catalog.csv`, script `src/stage1_expected.py`). The 1,759 names are also the 1,759 `filename` values in `volve_ddr_master` (checked in Stage 0). This only shows the files exist and have the catalog's sizes; parsing is Stage 2. The v2 target of 1,759 DDRs is not contradicted at file level.

## Manifest

`data/raw/manifest.csv`: columns path, sha256, bytes. 1,762 rows = 1,759 DDR XML + 3 NOD files. Byte totals from the manifest: DDR XML 21,315,879; NOD files 5,813,782. SHA-256 of the manifest itself: `631504c0a8fb110c680903473bf9ae0da396858b452cdb104c7abf12edc106f1`. Script: `src/stage1_manifest.py`.

All files under `data/raw/` carry the Windows read-only attribute (checked: 0 of 1,759 DDR files and 0 of 3 NOD files writable). This is a guard, not a lock; do not rely on it for integrity, use the hashes.

Process note: while testing the read-only flag I created one stray test file in `data/raw/ddr_xml/` and deleted it at once (no content, never hashed). Re-running `stage1_manifest.py` also overwrote the manifest and dropped the NOD rows; I re-appended them from the files on disk. The final manifest is consistent with the files on disk.

## NOD snapshot (retrieved 2026-10-24)

Fetched by HTTP from the same FactPages Table View export URLs recorded for the Sept snapshot (`data/raw/nod/nod_snapshot_20261024_metadata.json`).

| File | Bytes | Data rows | SHA-256 (first 12) |
|---|---|---|---|
| `wellbore_development_all_20261024.csv` | 4,080,420 | 6,286 | 7b569ad8d |
| `wellbore_exploration_all_20261024.csv` | 1,732,088 | 2,200 | 31244e9e9 |

Unlike the Sept snapshot (which kept only the Volve rows), these are the full national files.

**Comparison with the 2026-09-08 snapshot**, on the Volve subset (wellbore name contains `15/9-F-` or `15/9-19`):

- Development: 22 rows now, 22 in Sept. Names identical, none added or removed.
- Exploration: 5 rows now, 5 in Sept. Names identical.
- Every one of the 27 rows differs in exactly one column: `datesyncNPD` (08.09.2026 in Sept, 24.10.2026 now). No other column differs in any row. So the register has not changed for these wellbores between the two dates, in any field.
- Nationally the development table grew from 6,255 to 6,286 rows (+31) and exploration from 2,201 to 2,200 (-1). These are unrelated to Volve and not examined further. (Sept row counts are from the Sept metadata JSON.)

Script: `src/stage1_nod.py`.

## Housekeeping and decisions logged (`notes/decisions.md`, items 7 to 11)

- Manuscript base: `inputs/paper2_v2.docx` confirmed latest by TJ.
- Raw route, date, download command and verification recorded.
- NOD snapshot recorded.

## Still open

1. **Adjudicator of the 50 audit records (open item 4):** TJ's reply again held the unfilled template, "[Write the true answer ...]". Recorded as unanswered. Needed before Stage 6 and before the AI disclosure is final.
2. **Licence note:** the reply held a placeholder, "[what the listing says about sharing]". Not recorded. Needed for open item 7 and the Stage 13 README and data licence note. Until then I assume nothing about redistributing narrative text.
3. The reply also left "[today's date]" as a placeholder. I used the date from the system clock and the Databricks catalog timestamp (2026-10-24) in the decision log. Correct me if the listing was re-added on another day.

## Git state

`data/raw/` is gitignored (`.gitignore` line 37), so the raw files and manifest are not tracked; the manifest hash above is the reference. Untracked or modified and not committed: `inputs/old_audit/`, `notes/`, `reports/`, `src/`, and the `CLAUDE.md` edit. Say if you want a commit.

## Next

Stage 2 (extract to `data/interim/ddr.parquet`, then diff against `volve_ddr_master`). Per rule 4 I will state the Stage 2 plan and wait for "go". Also needed first: create `.venv/` (Python 3.10) and `requirements.txt`.
