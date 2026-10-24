# Field-Scale Well Construction Timeline Reconstruction from WITSML Daily Drilling Reports

**Paper:** T. Appalla (independent researcher), "Field-Scale Well Construction Timeline Reconstruction from WITSML Daily Drilling Reports: A Complete Operational History of the Equinor Volve Dataset", IPTC 2027, paper IPTC-25544-MS.

This repository is the reproducible pipeline behind the paper. It parses the 1,759 WITSML Daily Drilling Reports (DDRs) of the Equinor Volve field from the raw XML, classifies each report into one of 13 construction phases with a frozen rule-based classifier (v3), audits what the classifier misses, validates total depth and spud date against the Norwegian Offshore Directorate (NOD) FactPages, recovers sidetrack kick-off depths, and computes durations to total depth. Every number in the manuscript is produced by code in `src/` and traced in `outputs/numbers_registry.json` (one entry per number, with the producing script and function, the SHA-256 of the input files and a timestamp).

The branch `rerun-2026-10` is a clean rerun from the raw data. The state before the rerun is kept under `inputs/` for comparison.

## Licences

- **Code:** Apache License 2.0 (`LICENSE`).
- **Data:** the Volve data are disclosed by Equinor ASA under the Equinor Open Data Licence (https://www.equinor.com/energy/volve-data-sharing). This repository does **not** redistribute DDR narrative text. It holds file names, wellbore names, dates, depths, categories, calls and evidence quotes of 15 words or fewer (an ellipsis is not counted as a word). The raw DDR XML is not in the repository; obtain it as described below.
- **NOD data:** the FactPages wellbore exports are fetched from https://factpages.sodir.no and the export of 24 October 2026 is committed in `data/nod/` (see `data/nod/README.md` for the source, date and attribution). Derived comparison tables are in `outputs/`.

## Obtaining the raw DDR XML (Databricks Marketplace)

1. In a Databricks workspace, install the Equinor Volve listing from the Databricks Marketplace (provider `equinorasa`, share `equinoropendata_volve`). This creates the catalog `equinor_asa_volve_data_village` with schema `public` and the volume `volve`.
2. Authenticate the Databricks CLI with a profile named `volve` (`databricks auth login --host <workspace-host> --profile volve`). Tokens and `~/.databrickscfg` are never committed.
3. Download the DDR folder (about 21 MB). In Git Bash on Windows, prefix with `MSYS_NO_PATHCONV=1`:

```
MSYS_NO_PATHCONV=1 databricks fs cp -r --overwrite --profile volve \
  "dbfs:/Volumes/equinor_asa_volve_data_village/public/volve/Well_technical_data/Daily Drilling Report - XML Version" \
  data/raw/ddr_xml/
```

4. Expected result: 1,759 XML files, 21,315,879 bytes in total. `src/stage1_manifest.py` writes `data/raw/manifest.csv` (path, sha256, bytes) and checks names and sizes against the Marketplace metadata catalog (`workspace.default.volve_metadata_catalog`).

## Setup and inputs

```
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt     # Windows; use .venv/bin/python elsewhere
```

The pipeline needs only two things:

1. **The Volve DDR XML** in `data/raw/ddr_xml/` (1,759 files, see above). It is not in the repository.
2. **The files tracked in this repository**: `src/`, `inputs/`, the NOD wellbore snapshot in `data/nod/` (FactPages Table View exports retrieved 2026-10-24, committed with its metadata and attribution; the register changes over time, so a newer export may give different NOD comparison results and the registry values correspond to this snapshot), and the committed outputs that act as inputs (`outputs/audit_adjudications.csv`, `outputs/kickoff_signoff.xlsx`).

## Reproducing everything

From the repository root:

```
.venv/Scripts/python -X utf8 src/run_pipeline.py
```

This runs every stage in order (extract, data quality, classification, timeline, audit, NOD validation, kick-off, durations, figures, registry, manuscript draft) in about a minute on a laptop and stops at the first failure. It was tested from a fresh clone with only the DDR XML added: all 235 registry values, all tables and figures, and the manuscript text came out identical to the committed ones (only timestamps and the SHA-256 of generated files differ in `outputs/numbers_registry.json`).

| Stage | Script(s) | Writes |
|---|---|---|
| 1 Fetch raw | `stage1_manifest.py`, `stage1_nod.py` | `data/raw/manifest.csv`, `data/nod/nod_snapshot_20261024_metadata.json` |
| 2 Extract | `stage2_extract.py` | `data/interim/ddr.parquet` (raw strings, not tracked) |
| 3 Data quality | `stage3_quality.py` | `outputs/stage3_*.csv` |
| 4 Classify | `stage4_classify.py`, `stage4_rules_table.py` (classifier: `src/classifier_v3.py`, frozen) | `outputs/table2_phase_distribution.csv`, `outputs/stage4_priority_rules.*` |
| 5 Timeline | `stage5_timeline.py` | `outputs/timeline.csv` (1,421 rows) |
| 6 Audit | `stage6_prepare.py` (frame and strata), `stage6_estimates.py` (reads the published `outputs/audit_adjudications.csv`) | audit frame in `data/interim/`, estimates printed and registered |
| 7 NOD validation | `stage7_td.py`, `stage7_spud.py` | `outputs/td_validation.csv`, `outputs/spud_validation.csv` |
| 8 Kick-off | `stage8_f1c.py`, `stage8_kickoff.py`, `stage8b_kickoff_table.py`, `stage8d_apply_signoff.py` | `outputs/kickoff_table.csv`, `outputs/kickoff_proposal.csv` |
| 9 Duration | `stage9_duration.py` | `outputs/duration_table.csv`, `outputs/duration_family_summary.csv` |
| 10 Figures | `stage10_fig2_index.py`, `figure1_depth_vs_time.py` to `figure4_spud_offset.py` | `outputs/figures/*.png` (300 dpi; read `outputs/` only) |
| 11 Registry | `stage11_registry.py` | `outputs/numbers_registry.json` and comparison CSVs |
| 12 Manuscript | `stage12_manuscript.py`, `stage12_changes.py`, `stage12_check.py` | `manuscript/paper2_draft.docx`, `manuscript/CHANGES.md`, `outputs/manuscript_registry_check.csv` |

**Optional verification steps** compare the rerun with the author's earlier Databricks tables or catalog. They print `SKIPPED` and exit normally when those files are absent, and **no reported number depends on running them**:

- `stage1_expected.py` (set `VOLVE_FETCH_CATALOG=1` and a Databricks profile `volve`): checks file names and sizes against the Marketplace metadata catalog.
- `stage2_diff.py`, `stage2_text_diff.py`, `stage4_faithfulness.py` and the comparison blocks inside `stage4_classify.py` and `stage6_prepare.py`: need `data/interim/old/*.parquet` (exported with `stage2_export_old.py` and `stage4_export_old_classified.py` from the earlier tables) or `local_private/old_audit/`, which hold narrative text and are not in the repository.
- The few numbers that state these comparisons in the paper (103 narratives whose encoding was repaired, 1,303 classified on the earlier text, 0 mismatches, 0 phase changes) are read from their committed results (`outputs/stage2_encoding_summary.json`, `outputs/stage4_faithfulness_summary.json`, `outputs/stage4_faithfulness_phase_counts.csv`, `outputs/stage4_phase_changes_mojibake.csv`) and are flagged as such in the registry.

Historical steps that are not part of the pipeline because they were run once and must not be rerun: `stage8b_signoff.py` and `stage8c_proposal.py` (they built the kick-off sign-off workbook that the author has since signed off; both refuse to overwrite it), `stage6_publish_adjudications.py` (author side, builds the published adjudication file), `stage7_spud_evidence.py` (writes narrative snippets to `local_private/` only), and the report builders `stage8_report.py`, `stage8c_report.py`, `stage9_report.py`.

The narrative of each stage (what ran, results, arithmetic, discrepancies) is in `reports/STAGE_<n>.md`; decisions taken by the author are logged in `notes/decisions.md`; suspected classifier gaps (the classifier is frozen) are in `notes/classifier_gaps.md`.

## Where each manuscript table and figure comes from

| Item | Source file | Script |
|---|---|---|
| Table 1, field population | `outputs/stage3_table1_field_population.csv` | `stage3_quality.py` |
| Table 2, phase distribution | `outputs/table2_phase_distribution.csv` | `stage4_classify.py` |
| Priority order and hole-size rules (Section 3.3) | `outputs/stage4_priority_rules.md` | `stage4_rules_table.py` |
| Audit estimates (Section 5.2) | `outputs/audit_adjudications.csv` and registry entries `audit.*` | `stage6_estimates.py`, `stage11_registry.py` |
| Timeline dataset (Section 5.3) | `outputs/timeline.csv` | `stage5_timeline.py` |
| Table 3, total depth | `outputs/td_validation.csv` | `stage7_td.py` |
| Table 4, spud validation | `outputs/spud_validation.csv` | `stage7_spud.py` |
| Table 5, kick-off depths | `outputs/kickoff_table.csv`, `outputs/kickoff_proposal.csv` | `stage8b_kickoff_table.py`, `stage8d_apply_signoff.py` |
| Table 6, durations | `outputs/duration_table.csv` | `stage9_duration.py` |
| Fig. 1 | `outputs/figures/figure1_depth_vs_time.png` | `figure1_depth_vs_time.py` |
| Fig. 2 | `outputs/figures/figure2_days_vs_depth.png` | `stage10_fig2_index.py`, `figure2_days_vs_depth.py` |
| Fig. 3 | `outputs/figures/figure3_td_validation.png` | `figure3_td_validation.py` |
| Fig. 4 | `outputs/figures/figure4_spud_offset.png` | `figure4_spud_offset.py` |
| Every number in the text | `outputs/numbers_registry.json` | `stage11_registry.py`; checked by `stage12_check.py` |

Phase labels: the classifier's internal names "Reservoir drilling" and "Surface casing" appear in the data files; the manuscript and figures display them as "12¼ in. and smaller hole" and "Surface hole and casing" (label-only change, patterns frozen; `notes/decisions.md`, item 49).

## Repository layout

```
inputs/        state before the rerun: v2 manuscript, old registry, old audit adjudications, classifier v3 source, old figures
data/raw/      raw DDR XML and manifest (not tracked)
data/nod/      NOD wellbore snapshot of 2026-10-24 with README and metadata (tracked)
data/interim/  extracted and intermediate tables (not tracked, regenerated by code)
src/           one module per stage
outputs/       timeline, tables, figures, audit and kick-off files, numbers_registry.json
reports/       STAGE_<n>.md, one per stage
notes/         decisions.md (log of author decisions), classifier_gaps.md
manuscript/    updated manuscript draft and the number-by-number change log (CHANGES.md)
```

## How AI was used

The pipeline was built and run with Claude Code (Anthropic). Sidetrack kick-off depths were proposed by the AI tool and reviewed and approved by the author in `outputs/kickoff_signoff.xlsx`; the 50 audit adjudications were made by the author. See the AI disclosure in the manuscript.

## Citation

See `CITATION.cff`.
