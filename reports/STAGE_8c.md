> Status update 2026-10-24: the kick-off depths were signed off by the author (15 of 15 approved, none changed; decision 52). The word PROVISIONAL below is the state at the time of writing and no longer applies.

# Stage 8c: AI proposal for the kick-off sign-off, and the F-1 check

Date: 2026-10-24. Branch: `rerun-2026-10`. Scripts: `src/stage8c_proposal.py`, `src/stage8c_report.py`. Outputs: `outputs/kickoff_signoff.xlsx` (proposal columns added), `outputs/kickoff_proposal.csv`.

**These depths are AI-PROPOSED, pending author verification.** `proposed_by` = AI in every row. The columns `author_approved`, `author_depth` and `author_note` are TJ's and are empty (0 cells filled; the script refuses to run if any is filled). Everything derived from the proposed depths is PROVISIONAL until those columns are filled. If TJ accepts the proposals unchanged, the manuscript's AI disclosure must say that the kick-off depths were proposed by an AI tool and verified by the author (decision 37).

## Rule used (TJ decision 32), applied strictly

"The depth at which the narrative first reports new formation or departure from the parent hole; where none is stated, the depth at which the kick-off or window is started; where the narrative is empty, the measured depth at the parent-to-child transition." Rule added by TJ (decision 40): for casing exits (milled windows), kick-off = top of window. My first proposal read windows at the window bottom; TJ rejected that reading, and the proposal columns now equal the Stage 8b table.

## Proposal (15 rows; Y = proposal equals the current table, N = it does not)

| Sidetrack | Current table (m) | Proposed approved | Proposed depth (m) | Reason |
|---|---|---|---|---|
| 15/9-19 A | 2,178 | Y | 2,178 | Casing exit by a milled window: under the rule as ruled by TJ (decision 40) the kick-off is the top of the window, 2,178 m (window milled 2178-2183 m on 1997-07-29; an earlier window at 2,202-2,207 m was abandoned). NOD and the structured mdKickoff also say 2,178 m. |
| 15/9-19 B | 2,231 | Y | 2,231 | The report states the kick-off depth directly: 'DRESS CMT AND PERFORMED KICK OFF FROM 2231M TO 2277M'. NOD's 2,200 m is not an input to the rule; the only '2200' in the 19 A and 19 B reports is a clock time ('AT 2200 HRS'). |
| 15/9-19 BT2 | 2,911 | Y | 2,911 | The parent's last report states departure with a depth: 'COMMENCED DRILLING 8 1/2" HOLE FROM 2911 M AT 15/9-19BT2' (after cement drilled to 2911 m), and the first BT2 report starts at the same depth. Tier 1. |
| 15/9-19 ST2 | 1,536 | Y | 1,536 | Both 1992-12-19 narratives (parent last, sidetrack first) read 'None', so the third tier applies: measured depth at the transition, 1,536 m on both reports. Depth only, no text support; the parent had drilled cement to 1,486 m the day before, so the true departure could be shallower. |
| 15/9-F-1 A | 2,620 | Y | 2,620 | The parent's last report says 'Commenced kick off to F-1A' without a depth and its md is 2620 m, so tier 2, event in text with depth from md. NOD agrees at 2,620 m. |
| 15/9-F-1 B | 2,617 | Y | 2,617 | The parent's last report says 'Drilled out cement and kicked off well to F-1 B' and its md is 2617 m (2,545 m the day before), so tier 2, event in text with depth from md; the md is the day's deepest point, so the kick-off may be a little shallower (NOD 2,604 m). |
| 15/9-F-1 C | 1,364 | Y | 1,364 | Tier 1: the F-1 B report of 2014-02-22 states '50% formation obtained at 1364 m', the first report of new formation, and F-1 C's first report drills from 1,364 m. 1,355 m is only where time drilling started, the fallback used when no formation depth is stated. NOD agrees at 1,364 m. |
| 15/9-F-9 A | 421.5 | Y | 421.5 | Casing exit by a milled window: kick-off = top of window, 421.5 m ('Milled 12-1/4" sidetrack window from 421,5 m (top) to 424 m'); the window bottom, 428.2 m, is not used (TJ ruling, decision 40). NOD gives 428 m. |
| 15/9-F-11 T2 | 246 | Y | 246 | No formation or departure depth is stated, so tier 2: the 2013-03-23 report says oriented drilling out of the cement started at 246 m (top of cement 244 m). 257 m is where the sidetrack was handed over the next day. NOD has no separate record. |
| 15/9-F-11 A | 2,586 | Y | 2,586 | Tier 1: 'Drilled cement and kicked off to F-11 A at 2586m MD' states the departure depth. NOD 2,578 m. |
| 15/9-F-11 B | 2,589 | Y | 2,589 | LOW confidence. 'Drilled cement and new formation from 2531 m MD to 2589 m MD' reports new formation by the end of the interval, so departure is confirmed at 2,589 m, consistent with F-1 C (formation first reported); the interval start, 2,531 m, is not used (TJ ruling, decision 40). NOD gives 2,586 m, inside the interval. |
| 15/9-F-15 A | 1,381 | Y | 1,381 | 'Drilled cement/new formation from 1368 m to 1381 m MD. Initiated kick off of F-15.' puts the start of the kick-off at the end of the interval, 1,381 m, where the sidetrack's first report also starts. NOD agrees at 1,381 m. |
| 15/9-F-15 B | 3,185 | Y | 3,185 | Tier 1: 'kicked off at 3185m' states the departure depth; the '50/50 cement/formation' remark relates to 3,210 m, drilled afterwards. NOD agrees at 3,185 m. |
| 15/9-F-15 C | 2,566 | Y | 2,566 | Tier 2: cement was drilled from 2,490 to 2,566 m, then 'Initiated kick off', and no formation or departure depth is stated; 2,575 m (the NOD value) is only where the section had reached by the end of the day. |
| 15/9-F-15 D | 1,380 | Y | 1,380 | The sidetrack's first report says 'Drilled cement and kicked off' without a depth, so tier 2 with depth from md: the parent's last report (kick-off plug set the day before) has md 1,380 m. NOD agrees at 1,380 m. |

## TJ's ruling (decision 40): all three AI proposals rejected

My first proposal differed from the Stage 8b table in three rows: 19 A (2,178 to 2,183 m), F-9 A (421.5 to 428.2 m) and F-11 B (2,589 to 2,531 m). TJ rejected all three, keeping the table values and adding the window-top rule. The proposal now agrees with the table in all 15 rows (proposed_approved = Y everywhere); F-11 B stays at LOW confidence (departure confirmed by the end of the cement-and-formation interval, 2,589 m, consistent with F-1 C). F-1 C stays at 1,364 m (1,355 m is the time-drilling start and is not used), F-11 T2 at 246 m, 19 ST2 at 1,536 m (depth only) and 19 B at 2,231 m (NOD's 2,200 m is not an input to the rule; the only 2200 in the 19 A and 19 B reports is a clock time). The values stay PROVISIONAL until TJ fills the author columns.

## Check and report only: 15/9-F-1 reports of 2007 versus 2013

| Group | DDRs | Date range | DDRs with a valid depth | Maximum valid depth |
|---|---|---|---|---|
| 2007 reports | 4 | 2007-12-02 to 2007-12-05 | 4 | 226 m on 2007-12-02 |
| 2013 reports | 34 | 2013-07-22 to 2013-08-24 | 34 | 3,632 m on 2013-08-17 |

The two groups are 2,056 days apart (the largest gap in F-1's record). All of F-1's depth beyond 226 m, including its 3,632 m TD (NOD 3,632 m, completion 21.08.2013), is in the 2013 reports. No interpretation is made here.

## Next

TJ fills the author columns. Stage 12 must not finalise kick-off numbers until then.
