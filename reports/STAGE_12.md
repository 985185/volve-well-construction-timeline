# Stage 12: Manuscript (DRAFT)

Date: 2026-10-24. Branch: `rerun-2026-10`. Scripts: `src/stage12_manuscript.py` (builds the draft), `src/stage12_check.py` (registry check), `src/stage12_changes.py` (change log). Outputs: `manuscript/paper2_draft.docx`, `manuscript/CHANGES.md`, `outputs/manuscript_registry_check.csv`, `data/interim/stage12_log.json`.

**Status: DRAFT, not final.** Kick-off depths and everything derived from them are PROVISIONAL (AI-proposed from the narratives, pending author verification) and are highlighted in yellow. Stage 12 is not finalised until TJ fills the author columns of `outputs/kickoff_signoff.xlsx`.

## Rulings applied first (decisions 40 to 46, logged in `notes/decisions.md`)

1. Kick-off: the three AI proposals were rejected and the proposal columns now equal the Stage 8b table; added rule "for casing exits (milled windows), kick-off = top of window"; 19 A 2,178 m, F-9 A 421.5 m, F-11 B 2,589 m (LOW). Author columns untouched and empty.
2. One spud-offset definition, then reworded (decision 47): WITSML spud date minus the NOD pre-drill entry date where NOD records one, otherwise the NOD main entry date; used in Fig. 4 and the Stage 7 table. The first version (closest date to the first report) looked at the outcome and was replaced. The only change against the previous table is 15/9-F-11 (offset 0 to +335 days, Exact to Unresolved); counts are now 6, 8, 4, 1, 2, 5 (v2 7, 8, 4, 1, 2, 4). Fig. 4 was regenerated.
3. F-1 statement registered (`f1.spud_section_statement`) and used in the spud section.
4. 17.6 years for the 1980 gap.
5. Sidahmed et al. (2015): verified through the Crossref record of DOI 10.2118/173429-MS (title, three authors Sidahmed, Coley, Shirzadi, issued 2015); OnePetro itself returned 403. Citation kept, note cleared.
6. Energistics: no source shows a published release labelled 1.4.0.0, and the year of the 1.4.1.1 release differs between sources, so the reference cites the schema version declared in the files with an access date (24 October 2026). This is the one reference that is weaker than TJ's first preference.
7. Licence: Equinor Open Data Licence; the Volve page names it and permits academic institutions, students and researchers to use the data, but the licence text and any redistribution wording were not in the page content retrieved. The no-narrative-text policy stands as the resolution of open item 7.

## What the draft changes (49 logged changes, each with registry id and reason in `manuscript/CHANGES.md`)

Numbers: Table 1 rig (1,758, 99.94%) and forecast24hr (1,656, 94.14%); placeholders 515 (331 + 7 + 176 + 1) in the abstract, Section 4, Section 6.2 and the conclusions; WITSML 1.4.0.0 everywhere (abstract, 3.1, 6.4, reference); 17.6 years; the F-12 and F-1 passages (91 to 340 days, F-1 two campaigns); Section 5.6 rewritten from the kick-off table (15 recovered; 11 depth in text, 3 event in text with depth from md, 1 depth sequence; NOD 12 values, 6 equal, 4 within 10 m, 2 further, 3 none; the "operational versus geometric" paragraph deleted; window-top rule; 19 A as the 15th sidetrack) with new Table 5; new Section 5.7 and Table 6 (duration, drilled length, metres per report-day, gap flag, 19 B and F-11 indicative); F-1 family shared intervals in Section 6.3, the limitations and a new conclusion; Appendix A (225 registry entries).

Text: "None" is in the source archive; days counted from the first report with a recorded depth (Section 5.3, Fig. 2 label and caption); spud categories "assigned by inspection, rules formalised afterwards" with the rules stated (resolves the tolerance note); the classifier priority order and hole-size rules stated (resolves the Section 3.3 note); the 50 audit calls were made by the author; AI disclosure rewritten (Claude Code built and ran the pipeline; kick-off depths AI-proposed from the narratives and, once confirmed, verified by the author; the author made all 50 calls); availability statement rewritten for the no-narrative policy; the four figure placeholders replaced by the Stage 10 PNGs.

Spud: Table 4 now reads Exact 6 and Unresolved 5, the text says the rules reproduce 25 of the 26 inspection assignments, and an open note asks TJ to confirm the category reported for 15/9-F-11 (Exact by inspection, Unresolved under the stated rule).

One correction of a v2 statement: the Table 4 detail cell for "Unresolved" read "15/9-19 series"; the four unresolved wellbores are 15/9-19 BT2, 19 S, 19 ST2 and F-9 (19 B is a definitional offset). Corrected and logged.

## Check: every number in the docx against the registry

1,503 numeric tokens (body, tables, captions; the Abbreviations and References lists excluded): 1,470 match a registry value; 33 are ignored for a stated reason (22 section numbers, 7 years in citations, 3 identifiers, 1 figure from a cited study); **0 mismatches**; 0 em dashes. The match is by value, so it shows each number exists in the registry, not that it sits in the right sentence; the new sentences were written from the registry entries named in `CHANGES.md`.

## Highlighting and notes

81 highlighted runs (provisional kick-off-derived values, in the abstract, Sections 3.5, 5.6, 6.3, Table 5, Table 6, the limitations, the conclusions and the AI disclosure clause "verified by the author"). Open [TJ:] notes in the draft (5): the title-page affiliation note (IPTC portal), the draft banner after the title, the provisional-values note under Table 5, the 15/9-F-11 spud category, and the repository-contents check before upload (Stage 13). 14 v2 notes were cleared as resolved (listed in `CHANGES.md`).

## Not done

- The draft was built with python-docx and checked by re-reading it; I have not opened it in Word, so page layout and table widths of the new Tables 5 and 6 need a visual check.
- Kick-off numbers, the yellow highlighting and the AI disclosure wording cannot be finalised before TJ fills the author columns.
- Open items still with TJ or Stage 13: the IPTC portal affiliation, the repository contents against the availability statement (the manifest and extracted table live in the gitignored `data/` folder), and the licence wording on redistribution, which Equinor's page does not state.
