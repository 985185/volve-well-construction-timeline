# NOD wellbore snapshot

Wellbore register exports used to validate total depth, spud date and kick-off depth of the Volve wellbores (paper IPTC-25544-MS).

| File | Content |
|---|---|
| `wellbore_development_all_20261024.csv` | FactPages Table View export, all development wellbores (national file, 6,286 data rows) |
| `wellbore_exploration_all_20261024.csv` | FactPages Table View export, all exploration wellbores (national file, 2,200 data rows) |
| `nod_snapshot_20261024_metadata.json` | Row counts, byte sizes and SHA-256 of the two exports, and the comparison of the Volve rows with the snapshot of 2026-09-08 (written by `src/stage1_nod.py`) |

- **Source:** Norwegian Offshore Directorate (NOD, Sokkeldirektoratet), FactPages, https://factpages.sodir.no, wellbore Table View export.
- **Export date:** 24 October 2026. The files are unmodified exports; the pipeline reads them from here by default.
- **Attribution:** Contains data from the Norwegian Offshore Directorate FactPages (https://factpages.sodir.no), retrieved 24 October 2026.
- **Terms of use:** the data are the NOD's; check the terms of use on https://factpages.sodir.no and https://www.sodir.no before reuse. The terms were not independently verified when this snapshot was added.
- **Currency:** the register is updated by the NOD. A newer export can differ from this snapshot, so the registry values of this repository correspond to the files here, not to the live FactPages.
