# Paper 2 clean rerun: stock-take

IPTC-25544-MS (27IPTC-P-1392-SPE). Manuscript due 4 Jan 2027, 11:59 PM Central. Effective deadline: before you leave for India on 11 Dec 2026.

Tick each item before the first Claude Code session. Anything you can't tick goes into the first session as a known gap rather than being discovered halfway through.

## A. Access and credentials

- [ ] **Databricks login works.** Use OAuth instead of a personal access token so it doesn't expire on you again. In Git Bash:
  ```
  databricks auth login --host https://<workspace-host> --profile volve
  databricks current-user me --profile volve
  ```
  If OAuth isn't offered on this workspace, create a new token (User Settings > Developer > Access tokens) with a lifetime that runs past 4 Jan 2027, and store it in `~/.databrickscfg` under `[volve]`. Never put it in the repo.
- [ ] **Claude Desktop MCP config** (`C:\Users\PC\AppData\Roaming\Claude\claude_desktop_config.json`): update the token there too if you want Desktop working as a fallback. Write the file without a BOM.
- [ ] **Raw Volve volume is readable.** It was restored by reinstalling the Marketplace listing in Sept, but downloading a file from it was never verified. Stage 0 in CLAUDE.md tests this first.
- [ ] **GitHub:** `gh auth status` shows you logged in with push access to `985185/volve-well-construction-timeline`.
- [ ] **IPTC author portal:** you can log in, and the affiliation has been changed from "Department of Mining and Energy" to Independent Researcher.

## B. Machine (home Windows PC)

- [ ] Claude Code installed and running on Opus 5.5, launched from Git Bash.
- [ ] Python 3.11 or later and Git installed; the Databricks CLI on PATH.
- [ ] 5 GB of free disk space. The DDR XML is small, but the figures, PDFs and a NOD snapshot add up.

## C. Inputs to collect into the repo before session 1

Put these in `inputs/` in the fresh clone. Commit them as-is, because they are the "before" state the rerun is compared against.

- [ ] `paper2_v2.docx`: the version I produced (IPTC-25544-MS_Appalla_v2.docx), or your own later edit of it if you've made one. **Which one is the latest?**
- [ ] `numbers_registry.json`: the old 59-entry registry.
- [ ] **Classifier v3 source**, verbatim: wherever it lives (Databricks notebook, repo, or a Claude Desktop chat). Without it the rerun can't prove the classifier is unchanged. **If you can't find it, say so in session 1.**
- [ ] **Audit adjudications** for the 50 records (record ID, stratum, CONSTRUCTION/NON_CONSTRUCTION, miss reason). This is the Paper 1 lesson: if no filled workbook exists, the audit has to be redone by you.
- [ ] **The four figure PNGs** and the scripts that made them, if they still exist.
- [ ] **NOD FactPages export** used in Sept, if saved. A fresh one will be taken anyway, but the old one lets you see whether the register has changed since.

## D. Decisions already made (don't reopen)

- Start from the raw WITSML XML, not the existing `volve_ddr_master` table.
- Classifier v3 is frozen. No pattern changes in this paper; refinements go to the SPE Journal version.
- If a rerun number differs from v2, the rerun wins. Claude Code stops at each mismatch and reports both values with the arithmetic, and you decide.
- The fresh clone of the GitHub repo is the only working copy, on a new branch `rerun-2026-10`.
- You present at IPTC Bangkok (24–26 Mar 2027).

## E. Open items the rerun must close (from the v2 yellow notes)

1. 15/9-F-1 C kick-off depth: 3,059 m (narrative) or about 1,364 m (NOD). If it's 1,364 m, the F-1/F-1 C shared-interval disclosure changes here **and in Papers 1, 3 and the barrier paper.**
2. The 15th sidetrack: 15 by designation, only 14 outcomes reported.
3. Classifier priority order and hole-size rules, written out for the paper.
4. Who adjudicated the 50 audit records (affects the AI disclosure).
5. Spud-date tolerance definitions ("exact" vs definitional offset vs error).
6. Sidahmed et al. 2015: confirm title and authors on OnePetro.
7. Repo contents match the availability statement, and the Volve licence permits redistributing narrative text.
8. Registry entries for the corrected audit estimate and the 411 placeholder total.
9. Optional but recommended: per-wellbore duration / days-to-TD table (the paper still has no drilling-performance result).

## F. Things that can quietly break a clean rerun

- **Re-extraction may not give 1,759 rows.** The old table may have deduplicated or dropped files. Treat any difference as a finding.
- **The audit sample depends on row order.** A new extraction with seed 42 can pick different records, which would invalidate your old adjudications. CLAUDE.md fixes this by sorting on filename before sampling and checking whether the old 50 records are reproduced.
- **NOD can change.** A fresh FactPages download may not match the Sept snapshot. Date-stamp both.
- **Windows paths.** Prefix Databricks API calls in Git Bash with `MSYS_NO_PATHCONV=1`.
