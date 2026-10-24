# Stage 8b: Kick-off re-derived (depth at which the sidetrack leaves the parent)

Date: 2026-10-24. Branch: `rerun-2026-10`. Script: `src/stage8b_kickoff_table.py`. Output: `outputs/kickoff_table.csv`. Decisions: `notes/decisions.md` items 27 to 31.

**Status: STOPPED after the table, as instructed. Stage 9 waits for TJ to see this table.**

Definition (TJ decision 27): kick-off = the depth at which the sidetrack leaves the parent wellbore. Evidence = the parent's last report(s) and the sidetrack's first report(s): kick-off, window milling, time drilling, "% formation" and hand-over language. For each sidetrack I picked the evidence report and depth by reading the narratives; the script then checks the depth really occurs in that report (text or md field) and cuts the quote from the raw narrative. Quotes are 15 words or fewer (cut from the narrative, so they can start mid-sentence). Method: FREE_TEXT = the depth is written in the narrative; DEPTH_SEQUENCE = the depth is the md field of the parent's last report (equal to the sidetrack's first), with kick-off wording in the narrative or none. "NOD" = `wlbKickOffPoint`, NOD snapshot 2026-10-24; difference = NOD minus DDR depth; blank where NOD has no record or no value. All depths in m MD.

## Kick-off table (15 sidetracks)

| Sidetrack | Parent | DDR kick-off (m) | Evidence quote (wellbore report, date) | Method | Confidence | NOD wlbKickOffPoint (m) | NOD - DDR (m) |
|---|---|---|---|---|---|---|---|
| 15/9-19 A | none in WITSML (NOD lists 15/9-19 S) | 2,178 | `SET 2ND WHIPSTOCK & MILLED WINDOW FROM 2178-2183 M. DRILLED 19 M FORMATION. CIRCULATED HOLE` (9-19 A, 1997-07-29) | FREE_TEXT | HIGH | 2,178 | +0 |
| 15/9-19 B | 15/9-19 A | 2,231 | `DRESS CMT AND PERFORMED KICK OFF FROM 2231M TO 2277M.` (9-19 B, 1997-11-11) | FREE_TEXT | HIGH | 2,200 | -31 |
| 15/9-19 BT2 | 15/9-19 B | 2,911 | `M;TOP OF SIDETRACK PLUG. DRILLED CMT. TO 2911 M. COMMENCED DRILLING 8 1/2" HOLE FROM` (9-19 B, 1997-12-06) | FREE_TEXT | HIGH |  |  |
| 15/9-19 ST2 | 15/9-19 S | 1,536 | `(narratives of both 1992-12-19 reports are 'None'; md 1,536 on both)` (9-19 S, 1992-12-19) | DEPTH_SEQUENCE | LOW |  |  |
| 15/9-F-1 A | 15/9-F-1 | 2,620 | `shoe and rathole. Commenced kick off to F-1A` (9-F-1, 2013-08-24) | DEPTH_SEQUENCE | MEDIUM | 2,620 | +0 |
| 15/9-F-1 B | 15/9-F-1 A | 2,617 | `Drilled out cement and kicked off well to F-1 B.` (9-F-1 A, 2013-08-30) | DEPTH_SEQUENCE | MEDIUM | 2,604 | -13 |
| 15/9-F-1 C | 15/9-F-1 B | 1,364 | `hole to 1355 m. Commenced time drilling to1364 m. 50% formation obtained at 1364 m.` (9-F-1 B, 2014-02-22) | FREE_TEXT | HIGH | 1,364 | +0 |
| 15/9-F-9 A | 15/9-F-9 | 421.5 | `over pull. Milled 12-1/4" sidetrack window from 421,5 m (top) to 424 m. Note:Bottom window` (9-F-9, 2009-06-30) | FREE_TEXT | HIGH | 428 | +6.5 |
| 15/9-F-11 T2 | 15/9-F-11 | 257 | `drilled 26" hole from 250 m to 257 m. Transferred over to well 15/9-F-11 T2.` (9-F-11, 2013-03-24) | FREE_TEXT | MEDIUM |  |  |
| 15/9-F-11 A | 15/9-F-11 T2 | 2,586 | `and kicked off to F-11 A at 2586m MD.` (9-F-11 T2, 2013-05-15) | FREE_TEXT | HIGH | 2,578 | -8 |
| 15/9-F-11 B | 15/9-F-11 A | 2,589 | `new formation from 2531 m MD to 2589 m MD.` (9-F-11 A, 2013-05-29) | FREE_TEXT | LOW | 2,586 | -3 |
| 15/9-F-15 A | 15/9-F-15 | 1,381 | `Drilled cement/new formation from 1368 m to 1381 m MD. Initiated kick off of F-15.` (9-F-15, 2008-12-12) | FREE_TEXT | HIGH | 1,381 | +0 |
| 15/9-F-15 B | 15/9-F-15 A | 3,185 | `Drilled 8½" hole from 3141m to 3185m and kicked off at 3185m continued drilling` (9-F-15 A, 2009-01-14) | FREE_TEXT | HIGH | 3,185 | +0 |
| 15/9-F-15 C | 15/9-F-15 B | 2,566 | `OBM. Drilled cement from 2490 m to 2566 m MD. Initiated kick off and drilled` (9-F-15 B, 2009-01-19) | FREE_TEXT | MEDIUM | 2,575 | +9 |
| 15/9-F-15 D | 15/9-F-15 C | 1,380 | `BHA. Drilled cement and kicked off. Drilled 17 1/2" hole.` (9-F-15 C, 2013-11-11) | DEPTH_SEQUENCE | MEDIUM | 1,380 | +0 |

Counts: FREE_TEXT 11, DEPTH_SEQUENCE 4 (15/9-19 ST2, F-1 A, F-1 B, F-15 D); 11 + 4 = 15, none unrecovered. NOD gives a value for 12 of the 15 (no value for 19 BT2, 19 ST2 and F-11 T2: NOD has no separate record, or none with a kick-off). Of those 12: exactly equal in 6 (19 A, F-1 A, F-1 C, F-15 A, F-15 B, F-15 D); within 10 m but not equal in 4 (F-9 A +6.5, F-11 A -8, F-11 B -3, F-15 C +9); further away in 2 (19 B -31, F-1 B -13). 6 + 4 + 2 = 12.

Notes on individual rows (evidence, not interpretation): 15/9-19 A: second whipstock, an earlier window at 2,202 to 2,207 m (1997-07-26) was abandoned. 15/9-19 ST2: both 1992-12-19 narratives read "None"; the parent had drilled cement to 1,486 m the day before, so 1,536 m rests on the measured depth only. 15/9-F-9 A: window top 421.5 m, window bottom 428.2 m (NOD 428). 15/9-F-11 T2: oriented drilling out of the cement began at 246 m on 2013-03-23, and 257 m is the hand-over depth; the table uses the hand-over depth, consistent with F-1 C. 15/9-F-11 B: evidence is an interval (cement and new formation drilled from 2,531 to 2,589 m), the point value is where new formation is reached. 15/9-F-15 C: kick-off initiated after cement was drilled to 2,566 m, the section then reached 2,575 m, which is the NOD value.

## v2 depths that were not kick-offs (5 of 15)

| Sidetrack | v2 depth (m) | Re-derived (m) | What the v2 depth is |
|---|---|---|---|
| 15/9-F-1 A | 3,004 | 2,620 | 3,004 m is the depth reached on the first F-1 A report (8 1/2 in. hole drilled to 3,004 m) |
| 15/9-F-1 B | 3,100 | 2,617 | SECTION START (3,100 m = 3 m of new formation below the 9 5/8 in. shoe track, then FIT) |
| 15/9-F-1 C | 3,059 | 1,364 | SECTION START (3,059 m = start of 8 1/2 in. section) |
| 15/9-F-9 A | 459 | 421.5 | 459 m is where the first F-9 A report starts drilling, below the window (window 421.5 to 428.2 m) |
| 15/9-F-11 B | 3,271 | 2,589 | SECTION START (3,271 m = 8 1/2 in. section start after the 9 5/8 x 10 3/4 in. casing) |

Section starts: F-1 B, F-1 C and F-11 B (the first two checked first, as you asked; both are section starts). Not section starts but also not kick-offs: F-1 A (depth reached on the first report) and F-9 A (where the first report starts drilling below the window). The other nine v2 depths equal the re-derived ones, and 15/9-19 A is new. So 5 of the 14 v2 values change.

## 15/9-19 S structured kick-off versus NOD (reported only)

- Structured `mdKickoff` for 15/9-19 S: 562 m in all 49 of its DDRs (constant).
- NOD `wlbKickOffPoint` for 15/9-19 S: blank. (For the rest of the 19 series NOD gives 2,178 m for 19 A, 2,200 m for 19 B, and blank for 19 SR and 19 SR2.)

No interpretation, as instructed.

## Cross-paper correction (decision 28)

F-1 / F-1 C shared interval is above 1,364 m MD, not 3,059 m; to be corrected in Papers 1, 3 and the barrier paper. For F-1 B to F-1 A and F-11 B to F-11 A the same section-start problem applies to any statement that used v2's 3,100 m or 3,271 m as a kick-off or shared-interval limit; the re-derived depths are 2,617 m and 2,589 m.

## Quotes policy checks (decision 31)

All evidence quotes in `outputs/kickoff_table.csv` are 15 words or fewer (asserted in the script). `inputs/repo_before/data/sidetrack_relationships.csv` was trimmed: four quoted DDR fragments of 16 to 22 words now end after 15 words plus an ellipsis. `spud_validation.csv` has no quoted DDR fragment over 15 words (the long spans found earlier were my own prose between apostrophes), so it is unchanged. To remove the long fragments from the unpushed branch history too, the branch was rewritten again, this time from `master`'s tip, because the rerun-setup commit `e1ce707` (the old `798d6ce`) held the untrimmed files. `master` and `origin/master` were not touched (still `34bc1c0`) and still contain the untrimmed `data/sidetrack_relationships.csv`; per your decision I did not rewrite them. All branch commit hashes changed again.

## Next

Stage 9 (duration table) after TJ has seen this table.
