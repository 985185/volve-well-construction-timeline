# Stage 2: Extract

Date: 2026-10-24. Branch: `rerun-2026-10`. Status: complete. **No v2 target is contradicted.** Several differences from the old `volve_ddr_master` table were found and are explained below; two of them need a decision from TJ before Stage 4.

Scripts: `src/stage2_extract.py`, `src/stage2_export_old.py`, `src/stage2_diff.py`, `src/stage2_text_diff.py`. Environment: `.venv/` (Python 3.10.6, pandas 2.3.3, pyarrow 25.0.1, lxml 6.1.3), `requirements.txt` added. Output: `data/interim/ddr.parquet`. Old table exported once to `data/interim/old/volve_ddr_master.parquet` (comparison only; all 24 columns are STRING in Databricks). Nothing under `data/raw/` was changed.

## What was extracted

- 1,759 XML files parsed from `data/raw/ddr_xml/`. Each file has exactly one `drillReport` element (the stop check passed, 0 exceptions).
- All values are raw strings with no casting, stripping or cleaning. A tag that is absent is stored as null; a tag that is present but empty would be stored as `''` (none of the 1,759 files turned out to have one in the required fields).
- Columns: filename, well, wellbore, date_report, dTimSpud, md, md_kickoff, md_csg_last, rig, operator, forecast24hr, drill_complete, sum24Hr, plus provenance columns report_no, schema_version, n_rig_npd_name, n_activity.
- `rig` is the `rigAlias/name` whose `namingSystem` is "NPD Name" (my choice, confirmed in the plan). 1,758 files have exactly one such alias, 1 has none.
- Schema version: all 1,759 files say `version="1.4.0.0"`, not 1.4.1.1 as CLAUDE.md states. Same schema family, no extraction impact seen. Flagged only because the paper may quote the version.
- Encoding: 1,423 files declare `ISO-8859-1`, 336 declare nothing. All non-ASCII bytes are in the 1,423 declared files, and none of those is valid UTF-8, so Latin-1 is the right reading. The 336 undeclared files are pure ASCII. lxml honoured the declaration, so text such as `Ø`, `½`, `¼` is read correctly.

## Results against v2 targets

| Item | v2 target | Rerun | Arithmetic / note |
|---|---|---|---|
| DDRs | 1,759 | 1,759 | 1,759 files, 1,759 rows, 0 duplicate filenames |
| Wellbores | 26 | 26 | distinct `nameWellbore` |
| Well families | 11 | 11 | distinct `nameWell` is 23; collapsing suffixes (A, B, C, D, T2, ST2 ...) gives 19, F-1, F-4, F-5, F-7, F-9, F-10, F-11, F-12, F-14, F-15 = 11 |
| Literal "None" narratives | 73 | 73 | sum24Hr equals `None` after strip; also 73 files with `<sum24Hr>None</sum24Hr>` by grep of the raw XML |
| md_kickoff populated | 248 (14.10%) | 248 | 1,759 - 1,511 absent = 248; 248/1,759 = 14.10%; all 248 are non-blank strings |
| Duplicate wellbore/date pairs | not in v2 table | 0 | 1,759 rows, 1,759 distinct pairs |

Other facts: distinct date_report values 1,690 (many dates repeat across wellbores); 0 null date_report; every date_report matches `YYYY-MM-DDT00:00:00+hh:mm`. 242 rows have `well` different from `wellbore` (sidetrack wellbores). Per-wellbore DDR counts sum to 1,759 (110 + 27 + 62 + 49 + 127 for the 19 series, and so on); the full table with first and last DDR is reproducible from `ddr.parquet`.

Stage 3 items (placeholder counts, Unicode survey) are not computed here, except that the `½` count in the new sum24Hr text is 82 occurrences and `¼` is 14, both equal to the v2 occurrence counts. DDR counts for those are Stage 3.

## Diff against `volve_ddr_master` (join on filename)

Joined 1,759 of 1,759. Filenames only in new: 0; only in old: 0.

Fields with **zero** differences: well, wellbore, date_report, dTimSpud vs spud_date, md vs md_m, report_no (and these include all the `-999.99` and `0` placeholder strings, which both extractions kept as text).

Fields with differences (cells):

| Field | Cells | Cause |
|---|---|---|
| rig | 1,759 | **Old extraction bug.** Old `rig` is the literal string `name` in all 1,759 rows (it read the first `<name>` child, not the rig name). New has 3 real rigs: MÆRSK INSPIRER 1,384, BYFORD DOLPHIN 208, TREASURE PROSPECT 166 = 1,758, plus 1 null (the 1980-01-01 15/9-19 A file has no rig alias). 1,758 + 1 = 1,759. |
| md_kickoff | 1,511 | Representation only: tag absent in new (null), old stored `''`. 0 present-but-different. |
| md_csg_last | 57 | Same: absent vs `''`. 0 present-but-different. |
| drill_complete | 146 | Same: absent vs `''`. 0 present-but-different. |
| operator | 1 | Same: absent vs `''` (the 1980 file). |
| sum24Hr | 322 | Text differences, see below. 1,437 identical. |
| forecast24hr | 262 | Text differences, see below. 1,497 identical. |

Total differing cells: 1,759 + 1,511 + 57 + 146 + 1 + 322 + 262 = 4,058, matching the script's total.

Text differences, every one classified (no unexplained rows):

| Cause | sum24Hr | forecast24hr |
|---|---|---|
| Old text stripped of leading/trailing whitespace | 219 | 194 |
| Old text has mojibake (UTF-8 bytes re-read as cp1252, e.g. `Ø` stored as `Ã˜`) | 65 | 47 |
| Both | 38 | 21 |
| Total | 322 | 262 |

Arithmetic: sum24Hr 219 + 65 + 38 = 322, forecast24hr 194 + 47 + 21 = 262.

Cross-check against raw whitespace: rows where the old text was stripped are 219 + 38 = 257 for sum24Hr and 194 + 21 = 215 for forecast24hr. These equal the number of new strings that have leading or trailing whitespace (257 and 215), so whitespace stripping explains exactly those rows. Rows with mojibake in the old text: 65 + 38 = 103 for sum24Hr and 47 + 21 = 68 for forecast24hr.

The old pipeline in `Paper 2.py` also applied `.strip()` before classifying, so the whitespace difference alone would not change a v2 result. The mojibake touches only 103 sum24Hr rows.

## Findings that need TJ

1. **The "None" narratives are in the source, not an extraction artefact.** The old registry (`stage4_discrepancy_literal_None_text`) says "almost certainly a Python str(None) artifact from the original WITSML extraction". The raw XML literally contains `<sum24Hr>None</sum24Hr>` in 73 files. The wording in the manuscript and registry should be corrected (Stage 11 and 12). The count (73) is unchanged.
2. **Classifier input text (decision before Stage 4).** The old classification ran on stripped text (and on the old table's mojibake). The raw strings carry whitespace. Options: (a) classify on `sum24Hr.strip()` with Latin-1 correct text, which is closest to the v2 pipeline, or (b) classify the raw string. The classifier patterns use `.lower()` and `re.search`, so whitespace should not change matches, but the audit category rule `^none$` does depend on stripping. I propose (a): strip only, no other cleaning, applied inside the classifier call, with raw strings kept in the parquet. Stage 4 will also report whether the 103 + 68 mojibake rows change any phase. Please confirm.
3. **Old `rig` column is wrong** (`name` in every row). It does not feed any v2 number I know of, but Stage 13 should not ship the old table, and any earlier paper that used `volve_ddr_master.rig` should be checked.

## Not done / next

Not committed. `data/interim/` is not gitignored, so `ddr.parquet` and the old-table export would be tracked if committed; say if you want them in git or ignored. Next: Stage 3 (data quality) after your "go" and my Stage 3 plan. Decision 2 above is only needed at Stage 4.
