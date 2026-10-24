# Stage 8b: Kick-off under the uniform rule

Date: 2026-10-24. Branch: `rerun-2026-10`. Scripts: `src/stage8b_kickoff_table.py`, `src/stage8b_signoff.py`. Outputs: `outputs/kickoff_table.csv`, `outputs/kickoff_signoff.xlsx` (for TJ's sign-off, author columns empty). Decisions: `notes/decisions.md` items 27 to 36.

**Status: the table is final pending TJ's row-by-row sign-off. The manuscript will use only author-approved depths.**

## The rule (TJ decision 32), applied uniformly to all 15

"The depth at which the narrative first reports new formation or departure from the parent hole; where none is stated, the depth at which the kick-off or window is started; where the narrative is empty, the measured depth at the parent-to-child transition (DEPTH_SEQUENCE)."

Operationally: tier T1 = a depth is stated together with new-formation or departure language (for example "50% formation obtained at 1364 m", "kicked off at 3185m"); tier T2 = the narrative names a kick-off, window or oriented-drilling start but gives no formation or departure depth, so the start depth is used (window top for windows); tier T3 = empty narrative, measured depth at the parent-to-child transition. Evidence is read from the parent's last and the sidetrack's first reports. I chose the evidence report and depth by reading the narratives; the script checks the depth occurs in that report (text or md field) and cuts the quote.

Method wording (decision 33): "depth in text", "event in text, depth from md" (the narrative names the kick-off event but not the depth, the depth is the md of the same report), "depth sequence (narrative empty)". Counts: depth in text 11, event in text with depth from md 3 (F-1 A, F-1 B, F-15 D), depth sequence 1 (19 ST2); 15 in total. Tiers: T1 7, T2 7, T3 1.

## Table (15 sidetracks, depths in m MD, NOD = wlbKickOffPoint, snapshot 2026-10-24)

| Sidetrack | Parent | DDR kick-off | Evidence quote (report, date) | Method | Tier | Confidence | NOD | NOD - DDR |
|---|---|---|---|---|---|---|---|---|
| 15/9-19 A | none in WITSML (NOD lists 15/9-19 S) | 2,178 | `SET 2ND WHIPSTOCK & MILLED WINDOW FROM 2178-2183 M. DRILLED 19 M FORMATION. CIRCULATED HOLE` (9-19 A, 1997-07-29) | depth in text | T2 | HIGH | 2,178 | +0 |
| 15/9-19 B | 15/9-19 A | 2,231 | `DRESS CMT AND PERFORMED KICK OFF FROM 2231M TO 2277M.` (9-19 B, 1997-11-11) | depth in text | T1 | HIGH | 2,200 | -31 |
| 15/9-19 BT2 | 15/9-19 B | 2,911 | `M;TOP OF SIDETRACK PLUG. DRILLED CMT. TO 2911 M. COMMENCED DRILLING 8 1/2" HOLE FROM` (9-19 B, 1997-12-06) | depth in text | T1 | HIGH |  |  |
| 15/9-19 ST2 | 15/9-19 S | 1,536 | `(narratives of both 1992-12-19 reports are 'None'; md 1,536 on both)` (9-19 S, 1992-12-19) | depth sequence (narrative empty) | T3 | LOW |  |  |
| 15/9-F-1 A | 15/9-F-1 | 2,620 | `shoe and rathole. Commenced kick off to F-1A` (9-F-1, 2013-08-24) | event in text, depth from md | T2 | MEDIUM | 2,620 | +0 |
| 15/9-F-1 B | 15/9-F-1 A | 2,617 | `Drilled out cement and kicked off well to F-1 B.` (9-F-1 A, 2013-08-30) | event in text, depth from md | T2 | MEDIUM | 2,604 | -13 |
| 15/9-F-1 C | 15/9-F-1 B | 1,364 | `hole to 1355 m. Commenced time drilling to1364 m. 50% formation obtained at 1364 m.` (9-F-1 B, 2014-02-22) | depth in text | T1 | HIGH | 1,364 | +0 |
| 15/9-F-9 A | 15/9-F-9 | 421.5 | `over pull. Milled 12-1/4" sidetrack window from 421,5 m (top) to 424 m. Note:Bottom window` (9-F-9, 2009-06-30) | depth in text | T2 | HIGH | 428 | +6.5 |
| 15/9-F-11 T2 | 15/9-F-11 | 246 | `Ran wireline gyro. Washed down oriented to 246 m. Oriented drilled 26" hole from 246` (9-F-11, 2013-03-23) | depth in text | T2 | MEDIUM |  |  |
| 15/9-F-11 A | 15/9-F-11 T2 | 2,586 | `and kicked off to F-11 A at 2586m MD.` (9-F-11 T2, 2013-05-15) | depth in text | T1 | HIGH | 2,578 | -8 |
| 15/9-F-11 B | 15/9-F-11 A | 2,589 | `new formation from 2531 m MD to 2589 m MD.` (9-F-11 A, 2013-05-29) | depth in text | T1 | LOW | 2,586 | -3 |
| 15/9-F-15 A | 15/9-F-15 | 1,381 | `Drilled cement/new formation from 1368 m to 1381 m MD. Initiated kick off of F-15.` (9-F-15, 2008-12-12) | depth in text | T1 | HIGH | 1,381 | +0 |
| 15/9-F-15 B | 15/9-F-15 A | 3,185 | `Drilled 8½" hole from 3141m to 3185m and kicked off at 3185m continued drilling` (9-F-15 A, 2009-01-14) | depth in text | T1 | HIGH | 3,185 | +0 |
| 15/9-F-15 C | 15/9-F-15 B | 2,566 | `OBM. Drilled cement from 2490 m to 2566 m MD. Initiated kick off and drilled` (9-F-15 B, 2009-01-19) | depth in text | T2 | MEDIUM | 2,575 | +9 |
| 15/9-F-15 D | 15/9-F-15 C | 1,380 | `BHA. Drilled cement and kicked off. Drilled 17 1/2" hole.` (9-F-15 C, 2013-11-11) | event in text, depth from md | T2 | MEDIUM | 1,380 | +0 |

## Rows whose depth changed under the rule

Compared with the previous version of this table (the departure-from-parent version): **one row changes. 15/9-F-11 T2: 257 m to 246 m.** The narrative of 2013-03-23 reports oriented drilling out of the cement starting at 246 m (top of cement 244 m), and gives no formation or departure depth, so tier T2 applies; 257 m was the hand-over depth of the next day. **15/9-F-1 C stays at 1,364 m** (T1: 50% formation obtained at 1,364 m). The other 13 rows are unchanged. Compared with v2, the rows that differ are the five listed below plus F-11 T2 (v2 257 m) and the new 19 A.

## v2 depths that were not kick-offs

| Sidetrack | v2 depth (m) | Re-derived (m) | What the v2 depth is |
|---|---|---|---|
| 15/9-F-1 A | 3,004 | 2,620 | 3,004 m is the depth reached on the first F-1 A report (8 1/2 in. hole drilled to 3,004 m) |
| 15/9-F-1 B | 3,100 | 2,617 | SECTION START (3,100 m = 3 m of new formation below the 9 5/8 in. shoe track, then FIT) |
| 15/9-F-1 C | 3,059 | 1,364 | SECTION START (3,059 m = start of 8 1/2 in. section) |
| 15/9-F-9 A | 459 | 421.5 | 459 m is where the first F-9 A report starts drilling, below the window (window 421.5 to 428.2 m) |
| 15/9-F-11 B | 3,271 | 2,589 | SECTION START (3,271 m = 8 1/2 in. section start after the 9 5/8 x 10 3/4 in. casing) |

F-1 B, F-1 C and F-11 B are section starts; F-1 A and F-9 A are drilled depths of the first report. 15/9-F-11 T2 differs from v2 (257 to 246 m) because of the rule, not because v2 used a section start.

## Where the evidence allows another reading (not applied; for sign-off)

| Sidetrack | Depth used | Other depth(s) the evidence supports |
|---|---|---|
| 15/9-19 A | 2,178 | 2183 (window bottom) |
| 15/9-19 BT2 | 2,911 | 2903 (top of sidetrack plug) |
| 15/9-19 ST2 | 1,536 | 1486 (parent drilled cement to 1,486 m the day before) |
| 15/9-F-1 C | 1,364 | 1355 (start of time drilling) |
| 15/9-F-9 A | 421.5 | 428.2 (window bottom); 436.5 (formation drilled to, 2009-07-02) |
| 15/9-F-11 T2 | 246 | 257 (hand-over depth, 2013-03-24) |
| 15/9-F-11 B | 2,589 | 2531 (start of the cement and new-formation interval) |
| 15/9-F-15 A | 1,381 | 1368 (start of the cement/new-formation interval) |
| 15/9-F-15 B | 3,185 | 3210 (depth of the first '50/50 cement/formation' report) |
| 15/9-F-15 C | 2,566 | 2575 (depth the section reached; the NOD value) |

The two window cases (19 A and F-9 A) are the main judgement: I read "where the kick-off or window is started" as the window top; reading "departure from the parent hole" as the window bottom would give 2,183 m and 428.2 m. NOD is 2,178 m and 428 m.

## 15/9-19 S (reported only, as instructed)

Structured `mdKickoff` for 19 S: 562 m in all 49 DDRs. NOD `wlbKickOffPoint` for 19 S: blank. No interpretation.

## Cross-paper correction (replaces the note of decision 28, per TJ)

"F-1 family shared intervals: all four of F-1, F-1 A, F-1 B, F-1 C share the hole above 1,364 m MD; F-1, F-1 A and F-1 B share it above approximately 2,617 to 2,620 m MD. Correct the former 'F-1 / F-1 C share formations above 3,059 m' statement in Papers 1, 3 and the barrier paper."

## Housekeeping

- `inputs/paper2_rebuild_prompt_pack_v2.md` copied from the Downloads folder (SHA-256 `18dbd3265cf9796ee26c93feb4a4486bddb1a1b392faeea4b73eddeb582884e0`; source and copy hashes identical; no secrets found by scan).
- All evidence quotes in `outputs/kickoff_table.csv` and the workbook are 15 words or fewer.

## Next

TJ reviews `outputs/kickoff_signoff.xlsx`. Stage 9 plan is in the chat reply; computing waits for TJ's go.
