# Paper 2 Rebuild — Staged Prompt Pack v2

**Paper:** IPTC-25544-MS / 27IPTC-P-1392-SPE  
**Title:** Field-Scale Well Construction Timeline Reconstruction from WITSML Daily Drilling Reports: The Equinor Volve Dataset  
**Venue:** IPTC 2027 Bangkok, ePoster  
**Manuscript deadline:** 4 January 2027, 11:59 PM CT  
**Effective deadline:** 11 December 2026 (TJ departs for India)  
**Author:** T. Appalla, independent affiliation  

---

## What this pack is for

The prior draft contained internal contradictions: 456 vs 563 unclassified DDRs,
an underived 1,421 figure, a misattributed Unicode recovery rate, a backwards
spud-date diagnosis, mixed date sources in Table 1, unsourced kick-off depths,
and a reproducibility citation pointing to the wrong codebase. Every number in
the rebuilt manuscript must trace to a query or computation in this pack.

---

## Environment — confirmed working as of 7 September 2026

**Data source:** `workspace.default.volve_ddr_master` — Delta table, 1,759 rows,
26 distinct wellbores. This is the authoritative source. The raw XML volume is
not accessible; this table was extracted from it previously and is the starting
point for all analysis.

**Access:** Claude Desktop with Databricks SQL MCP connector  
Workspace: `https://<workspace-host>`  
SQL warehouse: auto-starts on query  

**Write path for artefacts:** save CSVs and JSON outputs using PowerShell in
Claude Desktop — `Set-Content` without `-Encoding utf8` to avoid BOM issues,
or use `[System.IO.File]::WriteAllText()` with explicit UTF-8 no-BOM encoding.
Local working directory: `C:\Volve\paper2_rebuild\`

**Known schema quirks confirmed in Stage 0:**
- `md_m` is stored as STRING, not numeric. Use string comparisons:
  `md_m = '-999.99'` for sentinel, `md_m = '0'` for zero, not numeric literals.
- 331 rows have `md_m = '-999.99'` (sentinel), 7 rows have `md_m = '0'`
- Total excluded from depth-time dataset: 338 rows
- 1,759 − 338 = **1,421** depth-time data points — derivation now confirmed

**Confirmed foundation figures (Stage 0, 7 September 2026):**
- Total DDRs: 1,759 ✓ matches accepted abstract
- Distinct wellbores in table: 26 (vs 23 in paper — three sidetracks merged,
  see Stage 1 Part A)
- Null sum24hr: 0 — all free text present
- Excluded md rows: 338 (331 sentinel + 7 zero)
- Implied timeline dataset rows: 1,421

---

## How to use this pack

Each stage runs in Claude Desktop with the Databricks SQL connector active.
Paste the **Global Preamble** first in every new session, then the stage prompt.
Do not skip stages — each reads outputs the previous stage produced.

After each stage confirm the output files exist in `C:\Volve\paper2_rebuild\`
before starting the next one.

If a stage hits a STOP condition, resolve it before continuing. Do not work
around a contradiction — document it and ask.

---

## GLOBAL PREAMBLE — paste at the start of every stage session

```
You are rebuilding a peer-reviewed manuscript for IPTC 2027 Bangkok.
Paper: IPTC-25544-MS, "Field-Scale Well Construction Timeline Reconstruction
from WITSML Daily Drilling Reports: The Equinor Volve Dataset"
Author: T. Appalla, independent affiliation.

DATA SOURCE
Primary table: workspace.default.volve_ddr_master
1,759 rows, 26 distinct wellbores, all in Databricks SQL warehouse.
md_m column is STRING type — use string comparisons, not numeric.
Sentinel value for missing depth: '-999.99' (string). Zero depth: '0' (string).

LOCAL WORKING DIRECTORY: C:\Volve\paper2_rebuild\
All output files go here. Use PowerShell to write files.
To write without BOM: [System.IO.File]::WriteAllText('C:\Volve\paper2_rebuild\filename.json', $content, [System.Text.UTF8Encoding]::new($false))

NUMBERS REGISTRY
Every figure you compute is appended to C:\Volve\paper2_rebuild\numbers_registry.json
Format per entry:
{
  "key": "descriptive_name",
  "value": <the number>,
  "query": "the exact SQL that produced it",
  "timestamp": "ISO 8601 UTC"
}
Nothing enters the manuscript unless it is in this registry.

WORKING RULES — these override any instinct to be helpful

1. NO INVENTED NUMBERS. No estimates, placeholders, or "approximately" for any
   figure that should be computed. If a query fails, fix the query. If the data
   is not there, report that plainly.

2. STOP AND REPORT. If a count does not reconcile, if a result contradicts a
   prior stage, or if an assumption in this prompt turns out to be wrong —
   STOP. Report the discrepancy and wait. Do not pick the more convenient number.

3. SHOW YOUR ARITHMETIC. Every derived figure shows the calculation:
   e.g. "1,759 total − 338 excluded = 1,421 depth-time rows".

4. STRING TYPES. md_m is STRING. Cast explicitly when needed:
   CAST(md_m AS DOUBLE) — but first filter out '-999.99' and '0' strings.

5. ONE NUMBER EVERYWHERE. If a figure appears in more than one place in the
   manuscript, it is the same number drawn from the same registry entry.
```

---

## STAGE 1 — Wellbore inventory and sidetrack resolution

**Goal:** Resolve the 26-vs-23 wellbore discrepancy and establish the definitive
wellbore list for the paper. Confirm or correct the 1,759 DDR count.

**Output files:** `wellbore_inventory.csv`, `sidetrack_relationships.csv`,
first entries in `numbers_registry.json`

```
Stage 1 of 7. Read the Global Preamble. Do not write any prose yet.

PART A — Identify the extra wellbores
The accepted abstract states 23 wellbores. The table has 26 distinct wellbores.
Run:

SELECT wellbore, COUNT(*) as ddr_count,
       MIN(date_report) as first_ddr,
       MAX(date_report) as last_ddr
FROM workspace.default.volve_ddr_master
GROUP BY wellbore
ORDER BY wellbore

Compare against the 23-wellbore list from the paper:
15/9-19 S, 15/9-19 A, 15/9-19 B, 15/9-F-1, 15/9-F-1 A, 15/9-F-1 B,
15/9-F-1 C, 15/9-F-4, 15/9-F-5, 15/9-F-7, 15/9-F-9, 15/9-F-9 A,
15/9-F-10, 15/9-F-11, 15/9-F-11 A, 15/9-F-11 B, 15/9-F-12, 15/9-F-14,
15/9-F-15, 15/9-F-15 A, 15/9-F-15 B, 15/9-F-15 C, 15/9-F-15 D

Name every wellbore in the table that is NOT in that list. For each extra
wellbore, determine: is it a sidetrack that was merged into its parent in the
prior analysis, or is it genuinely new data not covered by the abstract?

The expected extras are BT2, ST2, and F-11 T2 variants — confirm or correct.

PART B — Sidetrack relationships
For each sidetrack wellbore (any wellbore with A, B, C, D, T2, ST2, BT2
in its name), query its DDRs to find the kick-off depth:

SELECT wellbore, date_report, md_m, sum24hr
FROM workspace.default.volve_ddr_master
WHERE wellbore = '<sidetrack_name>'
ORDER BY date_report
LIMIT 5

Identify the first DDR where depth increases from the kick-off point.
Also search sum24hr text for kick-off language:

SELECT wellbore, date_report, md_m, sum24hr
FROM workspace.default.volve_ddr_master
WHERE wellbore = '<sidetrack_name>'
  AND (LOWER(sum24hr) LIKE '%kick%off%'
    OR LOWER(sum24hr) LIKE '%kickoff%'
    OR LOWER(sum24hr) LIKE '%kicked off%'
    OR LOWER(sum24hr) LIKE '%sidetrack%')
ORDER BY date_report

Known reference: F-1C kicked off at 3,059 m MD. Verify your method recovers
this before applying it to other sidetracks.

Write sidetrack_relationships.csv:
wellbore | parent_wellbore | kickoff_depth_m | kickoff_source | notes

Where kickoff_source is one of:
  STRUCTURED_FIELD  — from md_kickoff_m column
  FREE_TEXT         — extracted from sum24hr
  DEPTH_SEQUENCE    — inferred from first non-zero depth in DDR sequence
  NOT_RECOVERABLE   — genuinely cannot be determined

Do not guess. NOT_RECOVERABLE is a valid and honest answer.

PART C — Definitive wellbore count
State explicitly:
  - Total distinct wellbores in the table
  - How many match the paper's 23-wellbore list
  - How many are extra, and what they are
  - Whether the paper should be updated to reflect the true count, or whether
    the extras should be excluded with documented justification

The answer affects the abstract. If the true count is 26, say so. If the extras
are properly treated as sub-wellbores merged into their parents for timeline
purposes, document that treatment precisely.

PART D — DDR count reconciliation
The abstract states 1,759 DDRs. The table has 1,759 rows. They match.
But confirm: are there duplicate rows (same wellbore + date_report)?

SELECT wellbore, date_report, COUNT(*) as cnt
FROM workspace.default.volve_ddr_master
GROUP BY wellbore, date_report
HAVING COUNT(*) > 1
ORDER BY cnt DESC

If duplicates exist, report them and their count. If none, confirm that.

Write wellbore_inventory.csv:
wellbore | ddr_count | first_ddr | last_ddr | max_md_string |
in_paper_23 | sidetrack_of | notes

Append all figures to numbers_registry.json.
```

---

## STAGE 2 — Field provenance and data quality

**Goal:** Characterise every key field's population state across all 1,759 DDRs.
Replace the prior draft's unsupported "100% population" claim with real numbers.

**Output files:** `field_provenance.csv`, `field_provenance_summary.csv`,
`encoding_survey.csv`, updated `numbers_registry.json`

```
Stage 2 of 7. Read the Global Preamble and Stage 1 outputs.

PART A — Field population survey
For each of these columns, count how many rows fall into each state.
Remember md_m is STRING — handle accordingly.

Columns to survey:
  date_report, spud_date, drill_complete, operator, rig,
  md_m, md_kickoff_m, md_csg_last_m, sum24hr, forecast24hr

States:
  NULL          — IS NULL in SQL
  EMPTY_STRING  — = '' 
  SENTINEL      — known placeholder value ('-999.99', '0', '-999', 'None')
  POPULATED     — everything else (a genuine value)

For each column run:
SELECT
  COUNT(*) as total,
  SUM(CASE WHEN <col> IS NULL THEN 1 ELSE 0 END) as null_count,
  SUM(CASE WHEN <col> = '' THEN 1 ELSE 0 END) as empty_count,
  SUM(CASE WHEN <col> IN ('-999.99','0','-999','None') THEN 1 ELSE 0 END) as sentinel_count,
  COUNT(*) - SUM(CASE WHEN <col> IS NULL THEN 1 ELSE 0 END)
           - SUM(CASE WHEN <col> = '' THEN 1 ELSE 0 END)
           - SUM(CASE WHEN <col> IN ('-999.99','0','-999','None') THEN 1 ELSE 0 END)
  as populated_count
FROM workspace.default.volve_ddr_master

Run this for every column. Report all numbers.

The prior draft claimed "100% population for all fields including md_m" and
attributed it to "default values where schema element is present but unpopulated."
Determine whether that claim is accurate or whether it was artefact of the
extraction logic treating sentinel values as populated. State the finding plainly.

PART B — md_kickoff_m survey
The manuscript claims mdKickoff was empty across the archive. Verify:

SELECT md_kickoff_m, COUNT(*) as cnt
FROM workspace.default.volve_ddr_master
GROUP BY md_kickoff_m
ORDER BY cnt DESC

If any non-null, non-sentinel values exist, list which wellbores they belong to.

PART C — Encoding survey of sum24hr
Find non-ASCII characters in the free text:

SELECT DISTINCT
  wellbore,
  date_report,
  LENGTH(sum24hr) - LENGTH(REGEXP_REPLACE(sum24hr, '[^\x00-\x7F]', '')) as non_ascii_count
FROM workspace.default.volve_ddr_master
WHERE LENGTH(sum24hr) - LENGTH(REGEXP_REPLACE(sum24hr, '[^\x00-\x7F]', '')) > 0
ORDER BY non_ascii_count DESC

Then for a sample of affected rows, show the actual characters:

SELECT wellbore, date_report,
       REGEXP_EXTRACT_ALL(sum24hr, '[^\x00-\x7F]') as non_ascii_chars
FROM workspace.default.volve_ddr_master
WHERE LENGTH(sum24hr) - LENGTH(REGEXP_REPLACE(sum24hr, '[^\x00-\x7F]', '')) > 0
LIMIT 20

The known encoding issue is Unicode fraction characters (½ and ¼) causing
pattern mismatch for hole size dimensions like "8½ inch" and "17½ inch".
Confirm whether these are present and in how many rows.

Write encoding_survey.csv:
wellbore | date_report | non_ascii_char | unicode_codepoint | occurrence_count

Write field_provenance_summary.csv:
column | null_count | empty_count | sentinel_count | populated_count | populated_pct

Append all figures to numbers_registry.json.
```

---

## STAGE 3 — Phase classifier re-run

**Goal:** Re-execute the v3 phase classifier against the live table and confirm
or correct the accepted-abstract figures: 74.1% classification rate, 13 phases,
1,303 classified, 456 unclassified.

**Output files:** `ddr_classified.csv`, `phase_distribution.csv`,
`unclassified_ddrs.csv`, updated `numbers_registry.json`

```
Stage 3 of 7. Read the Global Preamble and Stage 2 outputs.

PART A — Recover the classifier
The v3 classifier assigns each DDR to one of 13 phases by matching patterns
against the normalised sum24hr text. The pattern set is:

Priority 1  — Spud / Conductor: 36 inch hole, 30 inch conductor, spud,
              tagged sea btm
Priority 2  — Surface casing: 26 inch hole, 20 inch casing, ran 20 inch casing
Priority 3  — Intermediate drilling: 17 1/2 inch hole, 17 1/2 inch section,
              drilled 17 1/2
Priority 4  — Intermediate casing: 13 3/8 inch casing, 10 3/4 inch liner,
              ran 14 inch casing
Priority 5  — Reservoir drilling: 12 1/4 inch hole, 8 1/2 inch hole,
              drilled 8 1/2, coring
Priority 6  — Liner / Casing run: liner, running liner, RIH with liner,
              7 inch liner, tieback casing,
              RIH.{0,20}tie.back.{0,10}string (post-audit addition)
Priority 7  — Cementing: cement, WOC, bumped plug, waiting on cement
Priority 8  — Completion: completion, tubing, packer, perforat, inflow test
Priority 9  — P&A: set plug, EZSV, EVO plug, cut casing, P&A, abandon
Priority 10 — Logging / Testing: logging, LWD, wireline, PLT, FIT,
              pressure point
Priority 11 — Workover: workover, coiled tubing, sidetrack, window mill
Priority 12 — Waiting / Downtime: WOW, waiting on weather, OFS strike,
              rig maintenance
Priority 13 — Rig move / Setup: skidded rig, positioned rig,
              skidded cantilever, mooring

Unicode normalisation (MUST apply before matching):
  Replace Unicode ½ (U+00BD) with ' 1/2'
  Replace Unicode ¼ (U+00BC) with ' 1/4'

Priority resolution: when multiple patterns match, the lowest priority number
wins (Priority 1 beats Priority 13).

PART B — Apply the classifier in SQL
Run the classifier as a SQL CASE expression over the normalised sum24hr.
Apply Unicode normalisation first using REGEXP_REPLACE or TRANSLATE.

For each DDR, assign the highest-priority matching phase. If no pattern matches,
assign 'Unclassified'.

CREATE OR REPLACE TABLE workspace.default.volve_ddr_classified AS
SELECT
  filename,
  wellbore,
  date_report,
  md_m,
  sum24hr,
  CASE
    WHEN normalised_text RLIKE '(?i)(36.inch.hole|30.inch.conductor|\\bspud\\b|tagged.sea.btm)'
      THEN 'Spud / Conductor'
    WHEN normalised_text RLIKE '(?i)(26.inch.hole|20.inch.casing|ran.20.inch)'
      THEN 'Surface casing'
    WHEN normalised_text RLIKE '(?i)(17.1/2.inch.hole|17.1/2.inch.section|drilled.17.1/2)'
      THEN 'Intermediate drilling'
    WHEN normalised_text RLIKE '(?i)(13.3/8.inch.casing|10.3/4.inch.liner|ran.14.inch.casing)'
      THEN 'Intermediate casing'
    WHEN normalised_text RLIKE '(?i)(12.1/4.inch.hole|8.1/2.inch.hole|drilled.8.1/2|\\bcoring\\b)'
      THEN 'Reservoir drilling'
    WHEN normalised_text RLIKE '(?i)(\\bliner\\b|running.liner|RIH.with.liner|7.inch.liner|tieback.casing|RIH.{0,20}tie.?back.{0,10}string)'
      THEN 'Liner / Casing run'
    WHEN normalised_text RLIKE '(?i)(\\bcement\\b|\\bWOC\\b|bumped.plug|waiting.on.cement)'
      THEN 'Cementing'
    WHEN normalised_text RLIKE '(?i)(\\bcompletion\\b|\\btubing\\b|\\bpacker\\b|perforat|inflow.test)'
      THEN 'Completion'
    WHEN normalised_text RLIKE '(?i)(set.plug|EZSV|EVO.plug|cut.casing|\\bP.?&.?A\\b|\\babandon\\b)'
      THEN 'P&A'
    WHEN normalised_text RLIKE '(?i)(\\blogging\\b|\\bLWD\\b|\\bwireline\\b|\\bPLT\\b|\\bFIT\\b|pressure.point)'
      THEN 'Logging / Testing'
    WHEN normalised_text RLIKE '(?i)(\\bworkover\\b|coiled.tubing|\\bsidetrack\\b|window.mill)'
      THEN 'Workover'
    WHEN normalised_text RLIKE '(?i)(\\bWOW\\b|waiting.on.weather|OFS.strike|rig.maintenance)'
      THEN 'Waiting / Downtime'
    WHEN normalised_text RLIKE '(?i)(skidded.rig|positioned.rig|skidded.cantilever|\\bmooring\\b)'
      THEN 'Rig move / Setup'
    ELSE 'Unclassified'
  END as phase
FROM (
  SELECT *,
    TRANSLATE(TRANSLATE(sum24hr, '½', ' 1/2'), '¼', ' 1/4') as normalised_text
  FROM workspace.default.volve_ddr_master
)

ARITHMETIC CHECK — run immediately after:
SELECT
  COUNT(*) as total,
  SUM(CASE WHEN phase != 'Unclassified' THEN 1 ELSE 0 END) as classified,
  SUM(CASE WHEN phase = 'Unclassified' THEN 1 ELSE 0 END) as unclassified,
  ROUND(100.0 * SUM(CASE WHEN phase != 'Unclassified' THEN 1 ELSE 0 END) / COUNT(*), 1) as classification_rate_pct
FROM workspace.default.volve_ddr_classified

classified + unclassified MUST equal total. If not, STOP.

PART C — Reconciliation against the accepted abstract
The abstract states: 1,759 DDRs, 74.1% rate, 1,303 classified, 456 unclassified.
Report whether your re-run reproduces these figures exactly.

If YES: record it and continue.
If NO: STOP. Report the difference, do not adjust anything to match.
Note that 456 unclassified is the CORRECT figure (1,759 - 1,303 = 456).
The prior draft incorrectly stated 563 in some places — that was a v2 era
number. The v3 correct figure is 456.

PART D — Phase distribution
SELECT phase, COUNT(*) as ddr_count,
       ROUND(100.0 * COUNT(*) / 1759, 1) as pct
FROM workspace.default.volve_ddr_classified
GROUP BY phase
ORDER BY ddr_count DESC

Verify the phase counts sum to 1,759.

PART E — Unicode normalisation isolated effect
Run the classifier TWICE — once with normalisation, once without — and report
the difference. This gives the isolated normalisation effect for Conclusion 5.

WITHOUT normalisation: use sum24hr directly
WITH normalisation: use the TRANSLATE expression above

The difference in classification count is the figure to report. Do NOT report
the v2-vs-v3 improvement (which included both normalisation AND new patterns)
as if it were normalisation alone.

Write ddr_classified.csv and phase_distribution.csv.
Write unclassified_ddrs.csv with wellbore, date_report, md_m, sum24hr
for all unclassified records.
Append all figures to numbers_registry.json.
```

---

## STAGE 4 — Unclassified audit

**Goal:** Formally characterise the 456 unclassified DDRs. Establish the residual
miss rate. This is the basis for Conclusion 2 of the paper.

**Output files:** `unclassified_categories.csv`, `audit_sample.csv`,
`audit_adjudicated.csv`, `audit_summary.json`, updated `numbers_registry.json`

```
Stage 4 of 7. Read the Global Preamble and Stage 3 outputs.
The unclassified count from Stage 3 is the population for this stage.
Call it N_unclassified. It must equal 1,759 minus the Stage 3 classified count.

PART A — Leak check
Apply the full v3 pattern set to every unclassified DDR. Any record that
matches any pattern is a pipeline bug — the classifier should have caught it.

SELECT *
FROM workspace.default.volve_ddr_classified
WHERE phase = 'Unclassified'
  AND (
    normalised_text RLIKE '(?i)(36.inch.hole|30.inch.conductor|\\bspud\\b)'
    OR normalised_text RLIKE '(?i)(26.inch.hole|20.inch.casing)'
    -- [include all 13 pattern groups]
  )

Report every record found. These are genuine classifier errors to fix.
For each one: which pattern matched, and why did the classifier miss it.

PART B — Category assignment, full population
Assign every unclassified DDR to one of these operational categories:

  BOP_RISER         — BOP tests, riser running, marine operations
  GENERIC_TRIP      — POOH/RIH with no phase context
  PRODUCTION_MON    — production monitoring, well test, choke management
  EMPTY_RECORD      — null, blank, or single-word sum24hr
  RIG_MAINTENANCE   — rig equipment, tool repair
  WAITING_GENERIC   — waiting with no specific cause
  WIRELINE_NON_TEST — wireline operations not classifiable as logging
  MUD_FLUID         — mud mixing, fluid management
  WELL_HANDOVER     — well handover, suspension
  LABOUR            — labour disputes, crew change
  OTHER             — anything not fitting above

Use SQL CASE on sum24hr patterns for an initial pass, then manually review
a sample to confirm categories are correct.

The category counts MUST sum to N_unclassified. Show this explicitly.

PART C — Stratified sample
Draw a 50-DDR stratified sample:
  - Stratum 1: DDRs within 730 days of that wellbore's first DDR (construction era)
  - Stratum 2: DDRs more than 730 days after first DDR (production era)
  Allocate proportionally to stratum size.

Document the sampling frame BEFORE drawing the sample:
  - Population: N_unclassified
  - Stratum 1 size and sample allocation
  - Stratum 2 size and sample allocation
  - Random seed used

SELECT wellbore, date_report, sum24hr, '' as adjudication, '' as reason
FROM workspace.default.volve_ddr_classified
WHERE phase = 'Unclassified'
  AND <stratum condition>
ORDER BY RAND(<seed>)
LIMIT <allocation>

Write audit_sample.csv. The adjudication and reason columns are blank
for you to fill in.

PART D — Adjudication
Review each of the 50 sampled DDRs and classify as:
  CONSTRUCTION — a genuine construction operation the classifier missed
  NON_CONSTRUCTION — correctly excluded (no construction phase language)

For each CONSTRUCTION record, state why the classifier missed it:
  NONSTANDARD_TERMINOLOGY — unusual phrasing for a standard operation
  NO_HOLE_SIZE — construction operation without hole size dimension
  OTHER_MISS — other pattern gap

PART E — Residual miss rate
Show the arithmetic explicitly:

miss_rate_in_sample = CONSTRUCTION_count / 50
residual_miss_rate_over_all_DDRs = miss_rate_in_sample × (N_unclassified / 1759)
estimated_true_classification_rate = observed_rate + residual_miss_rate_over_all_DDRs

State the 95% confidence interval on the sample proportion using Wilson score
or normal approximation. If the sample is too small to support a meaningful
interval, say so explicitly — do not report a point estimate as if it were precise.

Write audit_adjudicated.csv and audit_summary.json.
Append all figures to numbers_registry.json.
```

---

## STAGE 5 — External validation

**Goal:** Validate total depth and spud date reconstruction against NOD FactPages
for all wellbores, not just seven. Resolve the F-7/F-9 depth question and the
F-1 spud date diagnosis.

**Output files:** `nod_reference.csv`, `td_validation.csv`,
`spud_validation.csv`, `sidetrack_disclosure.csv`,
updated `numbers_registry.json`

```
Stage 5 of 7. Read the Global Preamble and all prior stage outputs.

PART A — NOD reference snapshot
Fetch the NOD development wellbore table from:
https://factpages.sodir.no/en/wellbore/tableview/development/all

Export as CSV, save as nod_snapshot_<YYYYMMDD>.csv with today's date.
Record the retrieval date and URL as metadata in numbers_registry.json.
Filter to Volve wellbores (field = 'VOLVE') and save as nod_volve_reference.csv.

Sanity check — these must appear and have these depths:
  15/9-F-7:  1,085 m  (confirmed correct — batch-drilled top-hole)
  15/9-F-9:  1,085 m  (confirmed correct — batch-drilled top-hole)
If either is missing or wrong, STOP.

PART B — Total depth validation, all wellbores
For each wellbore, compare:
  WITSML max md: SELECT wellbore, MAX(CAST(md_m AS DOUBLE)) as max_md
                 FROM workspace.default.volve_ddr_master
                 WHERE md_m NOT IN ('-999.99', '0') AND md_m IS NOT NULL
                   AND md_m != ''
                 GROUP BY wellbore
  NOD total depth: from nod_volve_reference.csv

Write td_validation.csv:
wellbore | witsml_max_md | nod_total_depth | difference_m | outcome

Outcome categories:
  EXACT_MATCH      — difference = 0
  WITHIN_TOLERANCE — |difference| ≤ 15 m
  DISCREPANCY      — |difference| > 15 m
  NO_NOD_RECORD    — wellbore not found in NOD snapshot

For F-7 and F-9: present 1,085 m as a validated batch-drilled top-hole
signature, NOT as an anomaly or problem. The reconstruction agreed with NOD.
This is a positive result. Frame it that way.

PART C — Spud date validation
Compare three date sources per wellbore:
  (i)   WITSML spud_date field
  (ii)  First date in DDR sequence for that wellbore (MIN(date_report))
  (iii) NOD spud date

Classify each wellbore into exactly one category:

  EXACT_MATCH        — WITSML spud_date = NOD date
  DEFINITIONAL_OFFSET — WITSML predates NOD consistently; WITSML records
                        permit/rig-arrival date, NOD records first drilling
  WITSML_ERROR       — WITSML value is inconsistent with the wellbore's
                        OWN DDR chronology (i.e., it's before the first DDR
                        date in a way that cannot be explained by permit lead
                        time, or it's wildly inconsistent)
  WELLBORE_IDENTITY  — NOD and WITSML refer to different wellbore events
                        (e.g. original drilling vs re-entry)
  UNRESOLVED         — cannot determine

CRITICAL RULE: A WITSML value is a WITSML_ERROR only if it contradicts
THAT WELLBORE'S OWN DDR chronology. If the WITSML value is consistent
with the first DDR date, the discrepancy is on the NOD side.

Specifically re-examine 15/9-F-1:
  WITSML spud_date: 2007-11-28
  First DDR date: 2007-12-02
  NOD spud date: 2013-07-23
  F-1A spud date: 2013-08-20
The WITSML value (2007-11-28) is consistent with the first DDR (2007-12-02).
The NOD date (2013-07-23) aligns with F-1A, not F-1.
This is a WELLBORE_IDENTITY mismatch, NOT a WITSML error.
The prior draft called it a WITSML data entry error — that was wrong.

Write spud_validation.csv:
wellbore | witsml_spud | first_ddr_date | nod_spud | witsml_vs_nod_days | category | notes

PART D — Sidetrack disclosure
Using sidetrack_relationships.csv from Stage 1:
For every sidetrack pair, state:
  - the shared interval (surface to kick-off depth)
  - the implication for formation-level analysis

The F-1 / F-1C disclosure is mandatory:
"F-1 and F-1C share the wellbore interval above 3,059 m MD (confirmed
kick-off depth from sum24hr text dated 2014-03-13). These wellbores cannot
be treated as independent for formation-level analysis above that depth."

Write sidetrack_disclosure.csv.
Append all figures to numbers_registry.json.
```

---

## STAGE 6 — Figures and timeline dataset

**Goal:** Build the published dataset and the four manuscript figures.

**Output files:** `volve_timeline_dataset.csv`, `well_inventory.csv`,
figure scripts and PNGs in `C:\Volve\paper2_rebuild\figures\`

```
Stage 6 of 7. Read the Global Preamble and all prior stage outputs.

PART A — Timeline dataset
Join volve_ddr_classified (from Stage 3) with field provenance.
Include a row ONLY where md_m is POPULATED (not null, not empty, not sentinel).

SELECT
  wellbore,
  date_report,
  DATEDIFF(date_report, MIN(date_report) OVER (PARTITION BY wellbore
    ORDER BY date_report)) as days_from_first_ddr,
  CAST(md_m AS DOUBLE) as md_m,
  phase,
  filename
FROM workspace.default.volve_ddr_classified
WHERE md_m NOT IN ('-999.99', '0')
  AND md_m IS NOT NULL AND md_m != ''
ORDER BY wellbore, date_report

DERIVATION CHECK — show this arithmetic explicitly in the paper:
  Total DDRs:                    1,759
  Excluded (sentinel '-999.99'): 331
  Excluded (zero '0'):           7
  Timeline dataset rows:         1,421
  Verify: 1,759 - 331 - 7 = 1,421

Save as volve_timeline_dataset.csv.

PART B — Well inventory table
One row per wellbore. State the source of every date column explicitly.
Do NOT mix sources within a column.
Do NOT let sidetracks inherit parent spud dates.

wellbore | ddr_count | first_ddr (source: WITSML date_report MIN) |
last_ddr (source: WITSML date_report MAX) |
spud_date_witsml | spud_date_nod | spud_category (from Stage 5) |
max_md_witsml | nod_total_depth | td_outcome (from Stage 5) |
top_3_phases | sidetrack_of | kickoff_depth_m | kickoff_source

Save as well_inventory.csv.

PART C — Figures
Generate four figures as Python matplotlib scripts.
Save each script AND its PNG output.

Figure 1: Depth vs time — FOUR representative wells at full page width.
Choose: one 1990s exploration well (15/9-19 S), one straightforward
development well (15/9-F-14), one sidetrack family (F-1/F-1B/F-1C),
one shallow well (F-7 or F-9 at 1,085 m).
Phase colour bands overlaid. Gaps where md is absent left visible.
A 26-well facet is illegible at IPTC column width — do NOT produce it
as Figure 1. Offer it as a supplementary figure.

Figure 2: Days vs depth curves for all wells, coloured by hole section.
Spud/Conductor, Surface casing, Intermediate drilling, Reservoir drilling.

Figure 3: TD validation scatter — reconstructed max MD vs NOD total depth.
All wellbores. 1:1 reference line. Label outliers by wellbore name.
F-7 and F-9 at 1,085 m should appear as correctly validated points.

Figure 4: Spud date offset in days, grouped by category from Stage 5.
One bar per wellbore, coloured by EXACT_MATCH / DEFINITIONAL_OFFSET /
WELLBORE_IDENTITY / UNRESOLVED.
```

---

## STAGE 7 — Manuscript

**Goal:** Write the full manuscript. Reads only persisted artefacts.
No number enters the paper unless it is in numbers_registry.json.

**Output file:** `paper2_draft.docx`

```
Stage 7 of 7. Read numbers_registry.json FIRST. You may not write any figure
that is not in it. If a figure is missing from the registry, stop and say
which figure is missing rather than estimating it.

Output: plain .docx, 4,000-7,000 words, IMRAD structure, flowing prose.
No bullet lists in the body. No IPTC template yet.

TITLE
"Field-Scale Well Construction Timeline Reconstruction from WITSML Daily
Drilling Reports: The Equinor Volve Dataset"

AUTHOR AND AFFILIATION
T. Appalla
[Independent Researcher]

Do NOT list any government department or employer.

ACKNOWLEDGEMENTS (mandatory wording)
"The author thanks Equinor ASA for releasing the Volve dataset as an open
resource. The Norwegian Offshore Directorate FactPages database provided
independent validation records. This work was conducted independently of
the author's employer."

This must be consistent with the independent affiliation above.

ABSTRACT
Must reproduce the accepted IPTC abstract figures exactly, or state and
justify any changes. Key figures from the accepted abstract:
  1,759 DDRs, 13 phases, three classifier versions, 74.1% classification rate,
  formal stratified audit of unclassified records, 94% non-construction in sample,
  ~2% residual miss rate, TD validation against NOD FactPages,
  six-of-seven exact agreement in the original validation set, 15 m discrepancy,
  two spud-date data entry errors, 1,421 depth-time-phase data points.

If Stage 3 did not reproduce 74.1%, the abstract must be updated. Do not
reproduce a figure the analysis does not support.

SECTION 2 — BACKGROUND AND RELATED WORK
The nearest comparable published work is SPE-228268-MS. Describe it accurately:
  - Applies CPD, semi-supervised NLP and sequence mining to NPT root cause analysis
  - 701 DDRs from 10 wells
  - Explicitly states all analyses used SYNTHETIC datasets
  - Leaves rigorous validation and quantitative performance assessment to future work
  - Does not report a precision or recall figure

Do not attribute a precision figure to it. One of its authors may review this paper.

Frame the contribution: this paper applies deterministic rule-based classification
to a REAL, OPEN, PERMANENTLY CITABLE archive with a formal stratified audit
and independent regulatory cross-validation across all wellbores.

Citation (verified from PDF):
Karnot, M.H., Abdulkhaleq, H.B., Al-Mudhafar, W.J., Alibraheem, A.,
Alsubaih, A., and Alshawi, U. 2025. Deep Natural Language Processing for
Automatic Root Cause Analysis of Non Productive Time Events in Drilling Reports.
Paper SPE-228268-MS presented at SPE ATCE, Houston, 20-22 October.
DOI 10.2118/228268-MS.

Drop the Maersk Drilling / DTU study — it has no verifiable citation.

SELF-CONTAINMENT
The paper must stand alone. Describe the WITSML extraction and the
volve_ddr_master table structure in enough detail that a reader can reproduce
the work without any companion paper.

DATA QUALITY SECTION
Report the Stage 2 field provenance findings honestly.
If the prior "100% population" claim was an artefact of sentinel values
being counted as populated, say so directly. It is a useful finding.

RESULTS MUST INCLUDE with derivations shown:
  - Classification rate with arithmetic check
  - Unicode normalisation isolated effect (not the v2-vs-v3 improvement)
  - Audit sampling frame, then results
  - Timeline dataset row count: 1,759 − 331 − 7 = 1,421 (show this)
  - TD validation across all wellbores
  - F-7 and F-9 at 1,085 m presented as validated batch-drilled signature
  - Spud date validation with four-category classification
  - F-1 spud date reclassified as WELLBORE_IDENTITY, not WITSML error

LIMITATIONS SECTION MUST STATE:
  - Single primary phase per DDR; multi-phase days underrepresent cementing
  - No interpolation across depth gaps
  - Sidetrack wellbores where kick-off depth was NOT RECOVERABLE (name them)
  - F-1 and F-1C share the interval above 3,059 m MD
  - Audit sample size and what it can and cannot support statistically

NOVELTY CLAIMS
Add "to the author's knowledge" qualifier.
State the claim ONCE in the introduction and ONCE in conclusions. Not three times.

TERMINOLOGY
NOD throughout. Never NPD.
British English spelling throughout.

REFERENCES
Author-year format for everything. No bare paper numbers.
Every reference must have: authors, year, venue, identifier.

CODE AND DATA AVAILABILITY
Read the github_audit output before writing this section. Cite ONLY a
repository that actually contains the classifier code for this paper,
verified in the audit. If no suitable repository exists yet, write:
"Code and data will be made available at [repository URL] upon acceptance."
Flag this as a pre-submission action item.

FIGURES
Insert placeholders with full captions, keyed to Stage 6 output filenames.

TRACEABILITY APPENDIX
A table: every number in the paper | registry key | section where it appears.
```

---

## STAGE 8 — Adversarial review

**Goal:** Find every remaining defect before submission.

```
Stage 8. Review the Stage 7 manuscript as a hostile reviewer.
Do NOT edit. Produce a numbered findings list.

Check each of the following. For every finding state:
  severity: BLOCKING (paper cannot be submitted) / SUBSTANTIVE (weakens the
            paper significantly) / POLISH (minor)
  location: section and paragraph
  fix: the specific change required

1. ARITHMETIC
   - Verify every count, percentage and total by recomputation
   - Verify every table's rows sum to its stated total
   - Verify percentages recompute from stated numerators and denominators
   - Specifically: classified + unclassified = 1,759
   - Specifically: 1,759 − 331 − 7 = 1,421

2. TRACEABILITY
   - Every number in the prose must appear in numbers_registry.json
   - List any that do not

3. INTERNAL CONSISTENCY
   - Every number stated more than once must be identical everywhere
   - Abstract vs results vs conclusions — check all three match
   - 456 unclassified (not 563) must appear consistently

4. SOURCE CONSISTENCY
   - No table column mixes WITSML and NOD dates without labelling
   - Sidetracks do not inherit parent spud dates

5. UNSUPPORTED CLAIMS
   - Every assertion backed by a result in this paper or a cited source
   - Flag any assertion that relies on a companion paper not yet published

6. OVERCLAIMING
   - Novelty claims qualified with "to the author's knowledge"
   - "Complete operational history" not used if coverage is partial

7. CITATIONS
   - Every reference has authors, year, venue, identifier
   - SPE-228268-MS attributed accurately (synthetic data, no precision figure)
   - No uncitable references

8. AFFILIATION AND ACKNOWLEDGEMENTS
   - Author block says independent affiliation
   - Acknowledgements say work conducted independently of employer
   - These two are consistent with each other

9. F-1 SPUD DATE
   - Classified as WELLBORE_IDENTITY, not WITSML error
   - The reasoning is stated

10. F-7 / F-9
    - 1,085 m presented as validated result, not anomaly

11. UNICODE CLAIM
    - Recovery rate attributed to normalisation alone, not v2-vs-v3 improvement

12. WORD COUNT — within 4,000-7,000 band
```

---

## Sequencing against deadlines

| Window | Work |
|---|---|
| Now — end Sept | Stages 1–3. Foundation data established. |
| Early Oct | Stage 4 audit. Requires manual DDR review — budget time for it. |
| Mid Oct | Stage 5 validation. Take the NOD snapshot and freeze it. |
| Late Oct | Stage 6 figures. Start early — figures always take longer. |
| Nov | Stage 7 manuscript draft. NT Parliamentary Counsel work starts 2 Nov. |
| Early Dec | Stage 8 review, revise, second pass. |
| 11 Dec | Submit. This is the real deadline — you fly to India that day. |

---

## Fixed decisions

- `volve_ddr_master` is the data source. Raw XML volume not accessible.
- `md_m` is STRING — always use string comparisons or explicit CAST.
- Classifier v3 re-executed verbatim, not redesigned.
- Validation covers all wellbores, not seven.
- Single author, independent affiliation, consistent acknowledgement.
- Plain .docx now; IPTC template applied before submission.
- Unclassified count = 1,759 − classified. One number, everywhere.
- 456 unclassified (v3), not 563 (v2 stale figure).
- F-7 and F-9 at 1,085 m are correct and validated — not anomalies.
- F-1 spud discrepancy is a wellbore identity issue, not a WITSML error.

## Defects fixed by this pack

| Defect | Fixed at |
|---|---|
| 456 vs 563 unclassified contradiction | Stage 3 arithmetic check |
| 1,421 with no derivation | Stage 6 Part A — 1,759−331−7=1,421 |
| Unicode 8.6% misattributed to normalisation | Stage 3 Part E isolated test |
| F-1 spud diagnosis backwards | Stage 5 Part C — reclassified |
| Table 1 mixes date sources | Stage 6 Part B — sources labelled per column |
| Kick-off depths unsourced | Stage 1 Part B, Stage 5 Part D |
| F-7/F-9 presented as anomaly | Stage 5 Part B — reframed as validated result |
| SPE-228268-MS mischaracterised | Stage 7 — accurate description required |
| Maersk/DTU uncitable | Dropped entirely |
| Companion paper load-bearing | Stage 7 self-containment requirement |
| Validation limited to 7 wells | Stage 5 — all wellbores |
| Title overclaims complete coverage | Stage 7 — revised title |
| Novelty claim repeated three times | Stage 7 — stated twice maximum |
| NPD used instead of NOD | Stage 7 — terminology enforced |
| Figure 1 illegible at 23 wells | Stage 6 — four representative wells |
| Cited repo is wrong codebase | Stage 7 — audit-gated citation |
| Affiliation contradicts acknowledgement | Stage 7 — both set to independent |
