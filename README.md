# Field-Scale Well Construction Timeline Reconstruction from WITSML Daily Drilling Reports: The Equinor Volve Dataset

**Author:** Tejaswy Appalla (independent researcher)
**Venue:** International Petroleum Technology Conference (IPTC) 2027, Bangkok, Thailand
**Paper identifier:** IPTC-25544-MS

This repository contains the companion code and derived datasets for the paper above. The work reconstructs field-scale well construction timelines for 26 wellbores on the Equinor Volve field by deterministically classifying the free-text 24-hour summary field of 1,759 WITSML Daily Drilling Reports (DDRs) into 13 operational phase categories, audits the unclassified residual by stratified sampling, and validates the reconstruction against the Norwegian Offshore Directorate (NOD) FactPages.

## What this repository contains

| Path | Contents |
|---|---|
| [`classifier_v3.py`](classifier_v3.py) | Standalone Python module: the verbatim v3 phase-classification pattern set (13 categories, priority-ordered regex), the Unicode fraction normaliser, and a `classify_ddr(text)` convenience wrapper. |
| [`classifier_v3_sql.sql`](classifier_v3_sql.sql) | The equivalent SQL `CASE` expression, run against `workspace.default.volve_ddr_master` to produce the classified table reported in the paper. |
| [`data/volve_timeline_dataset.csv`](data/volve_timeline_dataset.csv) | Per-DDR reconstructed timeline: wellbore, date, measured depth, and classified phase (1,421 rows with valid depth). |
| [`data/well_inventory.csv`](data/well_inventory.csv) | Per-wellbore summary: DDR counts, spud/TD validation outcomes, dominant phases, sidetrack relationships, kick-off depths. |
| [`data/phase_distribution.csv`](data/phase_distribution.csv) | Field-wide phase counts and percentages from the classifier output (n=1,759). |
| [`data/td_validation.csv`](data/td_validation.csv) | Per-wellbore comparison of WITSML-reconstructed maximum measured depth against NOD official total depth. |
| [`data/spud_validation.csv`](data/spud_validation.csv) | Per-wellbore comparison of WITSML spud date against NOD entry date, with discrepancy classification. |
| [`data/sidetrack_relationships.csv`](data/sidetrack_relationships.csv) | Parent/child wellbore relationships and recovered kick-off depths. |
| [`data/nod_volve_reference_development.csv`](data/nod_volve_reference_development.csv), [`data/nod_volve_reference_exploration.csv`](data/nod_volve_reference_exploration.csv) | Raw NOD FactPages Table View export rows for the Volve field wellbores, retrieved 2026-09-08 (see `nod_snapshot_20260908_metadata.json` for the exact export URLs and retrieval method). |
| [`data/numbers_registry.json`](data/numbers_registry.json) | Every quantitative figure reported in the paper, with the query or derivation that produced it. This is the paper's single source of truth for all numbers. |
| [`figures/`](figures/) | The four figure-generation scripts and their rendered PNG outputs. |

## Data source

All DDR-derived data in this repository is extracted from the [Equinor Volve open dataset](https://www.equinor.com/energy/volve-data-sharing), disclosed by Equinor ASA under its Open Data Licence. The extraction pipeline that parses the original WITSML 1.4.x XML into a flat table (`workspace.default.volve_ddr_master`, 1,759 DDRs across 26 wellbores) was not built by the author of this paper; this repository picks up from that already-extracted table, which is the paper's stated data source throughout. The raw WITSML XML volume itself was not directly accessible during this work.

The NOD (Norwegian Offshore Directorate, formerly NPD) reference data in `data/nod_volve_reference_*.csv` is a public-domain snapshot from the [NOD FactPages](https://factpages.sodir.no/), used only to independently validate total-depth and spud-date figures derived from the WITSML data.

## Requirements

- Python 3.10+
- No third-party packages are required to run `classifier_v3.py` (standard library `re` only)
- To reproduce `classifier_v3_sql.sql` against the source table, any Spark SQL environment (Databricks SQL warehouse or a standalone Spark session) with access to a table matching the `workspace.default.volve_ddr_master` schema (`filename`, `wellbore`, `date_report`, `md_m` [string, sentinel `'-999.99'` and `'0'` excluded before casting], `sum24hr`)

## Quick start

Classify a single DDR summary string in Python:

```python
from classifier_v3 import classify_ddr

classify_ddr('DRLD 17 1/2" HOLE FROM 500M TO 620M.')
# -> 'Intermediate drilling'
```

Reproduce the full classified table in a Spark SQL environment:

```sql
-- classifier_v3_sql.sql expects a source table with columns:
-- filename, wellbore, date_report, md_m, sum24hr
-- Edit the FROM clause at the bottom of the script to point at your table,
-- then run it directly.
```

Load the pre-computed derived datasets directly (no classifier run required):

```python
import pandas as pd
timeline = pd.read_csv("data/volve_timeline_dataset.csv")
wells = pd.read_csv("data/well_inventory.csv")
```

## Known limitations

Stated here as in the paper's own Limitations section:

- **Single primary phase per DDR.** Each DDR is assigned exactly one phase label (its highest-priority pattern match). A report describing multiple activities in one day is not split; cementing in particular is likely underrepresented where it occurs as a secondary activity within a report classified under a higher-priority category.
- **No depth interpolation.** Gaps in measured-depth coverage (excluded sentinel or missing `md_m` values) are left as gaps in the timeline dataset rather than interpolated.
- **Kick-off depth not recoverable for all sidetracks.** Kick-off depth for NO 15/9-19 S could not be recovered from either free-text narrative or depth-sequence continuity; two further sidetracks rely on the weaker depth-sequence method rather than explicit free-text confirmation.
- **F-1 / F-1C shared-interval ambiguity.** The F-1 family's kick-off depth is reported using the operational (DDR-derived) definition, which differs from a geometric definition NOD uses internally; both are correct for their own purposes but are not interchangeable.
- **Audit sample size.** The stratified audit of the unclassified residual uses a fixed sample of n=50 records with seed 42; the resulting residual miss-rate estimate carries a Wilson 95% confidence interval, not a point guarantee.
- **Two stratification-scheme artefacts.** Two wellbores' earliest recorded DDR dates do not reflect their true drilling-campaign start (an anomalous isolated first record for one wellbore, and a later re-entry/mobilization record for another), which can misassign a small number of genuinely construction-era records into the production-era stratum used for audit sampling.
- **19-series naming discrepancy not fully reconciled.** WITSML "BT2" and "ST2" sidetrack suffixes for the 15/9-19 well series do not map one-to-one onto NOD's "B" and "SR" designations; this repository validates the mapping by total-depth agreement only and does not attempt full drilling-genealogy reconciliation.
- **NOD reference data is a dated snapshot.** The NOD FactPages extract in `data/` reflects the state of that public register as of 2026-09-08 and may not match the live FactPages if NOD has since revised any record.
- **No isolated Unicode-normalisation ablation.** The Unicode fraction normalisation step is applied unconditionally before classification; its standalone contribution to the classification rate (independent of the pattern-set changes between classifier versions) was not separately measured.

## Citation

```bibtex
@inproceedings{appalla2027volve,
  author    = {Appalla, Tejaswy},
  title     = {Field-Scale Well Construction Timeline Reconstruction from WITSML Daily Drilling Reports: The Equinor Volve Dataset},
  booktitle = {International Petroleum Technology Conference},
  year      = {2027},
  address   = {Bangkok, Thailand},
  note      = {IPTC-25544-MS}
}
```

See also [`CITATION.cff`](CITATION.cff).

## Licence

Apache License 2.0 -- see [`LICENSE`](LICENSE).
