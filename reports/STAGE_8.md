# Stage 8: Kick-off recovery

Date: 2026-10-24. Branch: `rerun-2026-10`. Scripts: `src/stage8_kickoff.py`, `src/stage8_f1c.py`, `src/stage8_report.py`. Outputs: `outputs/kickoff_recovery.csv`, `outputs/stage8_f1c_depths.csv` (depths only). Full narrative evidence (up to 300 characters per DDR) is in `local_private/stage8_kickoff_evidence.txt` and `local_private/stage8_f1c_ddrs.md`, untracked per the narrative policy. Quotes below are 15 words or fewer.

**UPDATE 2026-10-24 (TJ decisions 27 to 29): sections 1, 3 and 4 below used the v2 depths and are superseded by `reports/STAGE_8b.md`, where every kick-off is re-derived as the depth at which the sidetrack leaves the parent. Section 2 (the 15th sidetrack is 15/9-19 A) and the F-1 C evidence in section 3 stand.**

**Status (original): complete. STOPPED for TJ as instructed. The 15/9-F-1 C result (open item 1) is in section 3 and is not what v2 states.**

## 1. Kick-off table, one row per sidetrack by designation (15)

Method: FREE_TEXT = the depth is quoted in a DDR narrative (searched in the parent's last 5 and the sidetrack's first 30 reports); DEPTH_SEQUENCE = the depth equals the parent's last or the child's first measured depth with no narrative quote; NONE = no evidence. Search depth = the v2 depth, or for 15/9-19 A (no v2 row) the single structured `mdKickoff` value. Confidence: HIGH = narrative with a kick-off cue word plus an independent check (structured field or depth sequence) and within 5 days of the first report; MEDIUM = cue word in the narrative, or depth sequence only; CHECK = the quoted depth first appears more than 5 days after the sidetrack's first report. "NOD kick-off" is `wlbKickOffPoint` from the 2026-10-24 snapshot; the difference is NOD minus ours.

| Sidetrack | Method | Depth (m) | Evidence date | Days after first DDR | Evidence quote | Confidence | NOD kick-off (m) | NOD - ours (m) |
|---|---|---|---|---|---|---|---|---|
| 15/9-19 A | FREE_TEXT | 2,178 | 1997-07-29 | 4 | `SET 2ND WHIPSTOCK & MILLED WINDOW FROM 2178-2183 M. DRILLED 19 M FORMATION. CIRCULATED` | HIGH | 2,178 | +0 |
| 15/9-19 B | FREE_TEXT | 2,231 | 1997-11-11 | 1 | `TIME) DRESS CMT AND PERFORMED KICK OFF FROM 2231M TO 2277M.` | HIGH | 2,200 | -31 |
| 15/9-19 BT2 | FREE_TEXT | 2,911 | 1997-12-06 | 0 | `2903 M;TOP OF SIDETRACK PLUG. DRILLED CMT. TO 2911 M. COMMENCED DRILLING 8 1/2" HOLE` | HIGH | 2,200 | -711 |
| 15/9-19 ST2 | DEPTH_SEQUENCE | 1,536 |  |  |  | MEDIUM |  |  |
| 15/9-F-1 A | FREE_TEXT | 3,004 | 2013-08-24 | 0 | `F-1 Drilled and steered 8 1/2" section to 3004 m MD.` | HIGH | 2,620 | -384 |
| 15/9-F-1 B | FREE_TEXT | 3,100 | 2013-09-06 | 7 | `MD. Drilled 3 meters of new formation to 3100m MD. Performed FIT to 1.60 sg.` | CHECK | 2,604 | -496 |
| 15/9-F-1 C | FREE_TEXT | 3,059 | 2014-03-11 | 17 | `track and rathole, drilled 3m new formation to 3059 m.` | CHECK | 1,364 | -1,695 |
| 15/9-F-9 A | FREE_TEXT | 459 | 2009-07-04 | 0 | `Drilled/oriented 12 1/4" hole from 459 m to 500 m. Removed cuttings` | MEDIUM | 428 | -31 |
| 15/9-F-11 A | FREE_TEXT | 2,586 | 2013-05-15 | 0 | `cement and kicked off to F-11 A at 2586m MD.` | MEDIUM | 2,578 | -8 |
| 15/9-F-11 B | FREE_TEXT | 3,271 | 2013-06-08 | 10 | `Perform FIT and drilled 8 1/2" hole to 3271 m.` | CHECK | 2,586 | -685 |
| 15/9-F-11 T2 | FREE_TEXT | 257 | 2013-03-24 | 0 | `time drilled 26" hole from 250 m to 257 m. Transferred over to well 15/9-F-11` | HIGH |  |  |
| 15/9-F-15 A | FREE_TEXT | 1,381 | 2008-12-12 | 0 | `MD. Drilled cement/new formation from 1368 m to 1381 m MD. Initiated kick off of` | MEDIUM | 1,381 | +0 |
| 15/9-F-15 B | FREE_TEXT | 3,185 | 2009-01-14 | 0 | `Drilled 8½" hole from 3141m to 3185m and kicked off at 3185m continued` | MEDIUM | 3,185 | +0 |
| 15/9-F-15 C | FREE_TEXT | 2,566 | 2009-01-19 | 0 | `sg OBM. Drilled cement from 2490 m to 2566 m MD. Initiated kick off and` | MEDIUM | 2,575 | +9 |
| 15/9-F-15 D | DEPTH_SEQUENCE | 1,380 |  |  |  | MEDIUM | 1,380 | +0 |

Counts: FREE_TEXT 13, DEPTH_SEQUENCE 2 (15/9-19 ST2 and 15/9-F-15 D), NONE 0; 13 + 2 + 0 = 15. v2 reported 12 free text and 2 depth sequence with the 15th unknown. All 12 v2 free-text depths and both depth-sequence depths were found again in the raw data at the same value; the new row is 15/9-19 A.

## 2. Open item 2: the 15th sidetrack

15 sidetracks by designation: 19 A, 19 B, 19 BT2, 19 ST2, F-1 A, B, C, F-9 A, F-11 A, B, T2, F-15 A, B, C, D. The v2 kick-off table had 15 rows but listed 15/9-19 S (marked NOT_RECOVERABLE) and omitted 15/9-19 A, so only 14 outcomes were reported. 19 S carries the NOD designation letter S (deviated exploration wellbore, per the NOD guideline in CLAUDE.md) and its earliest DDRs describe a top-hole spud, so it is the original wellbore of the series, not a sidetrack; it correctly has no kick-off. 19 A is a sidetrack and its kick-off is recoverable:

- Structured `mdKickoff` = 2178 in all 110 of its DDRs (a constant, not a measured series).
- Narrative of 1997-07-29: window milled from 2178 to 2183 m (second whipstock; the first window at 2202 to 2207 m on 1997-07-26 was abandoned after the string could not pass back through it).
- NOD `wlbKickOffPoint` = 2178 m.

Three sources agree, difference 0 m. Parent: NOD's DISKOS parent field lists 15/9-19 S; the WITSML archive has no earlier wellbore adjacent in time (its first genuine DDR is 1997-07-25 and the 1980 record is a sentinel). I have not tried to settle the 19-series genealogy (per the earlier decision).

## 3. Open item 1: 15/9-F-1 C kick-off (3,059 m in v2 versus about 1,364 m in NOD), in full

F-1 C has 98 DDRs (2014-02-22 to 2016-10-22). The structured `mdKickoff` field is empty in all 98. Evidence, with quotes of 15 words or fewer:

| Date | DDR | md (m) | Quote |
|---|---|---|---|
| 2014-02-22 | F-1 B (its last DDR) | 1,364 | `Commenced time drilling to1364 m. 50% formation obtained at 1364 m.` |
| 2014-02-22 | F-1 C (its first DDR) | 1,502 | `Drilled 17 1/2" hole from 1364 m to 1482 m.` |
| 2014-03-05 | F-1 C | 3,056 | `Drilled 12 1/4" hole from 2646 m to 3056 m.` |
| 2014-03-08 | F-1 C | 3,056 | `Landed casing at 3047 m.` |
| 2014-03-11 | F-1 C | 3,059 | `drilled 3m new formation to 3059 m.` |
| 2014-03-13 | F-1 C | 3,290 | `Drilled and oriented 8 1/2" from 3059 m to 3293 m.` |

Depth by report for the first 19 F-1 C DDRs (all before 2014-03-13, dates 2014-02-22 to 2014-03-12): 1,502; 1,660; 1,684; 1,684; 2,080; 2,514; 2,514; 2,514; 2,514; 2,514; 2,646; 3,056; 3,056; 3,056; 3,056; 3,056; 3,056; 3,059; 3,059. Then 3,290 on 2014-03-13, 3,806 on 03-14, and 4,094 (TD) on 03-15.

Counts requested: reports before 2014-03-13: 19; of these with depth shallower than 3,059 m: **17**; equal to 3,059 m: 2 (03-11 and 03-12); deeper: 0. The shallowest F-1 C depth is 1,502 m on the first report. The depths below 3,059 m are not isolated: 17 consecutive daily reports lie under it, rising from 1,502 m.

What the evidence shows, stated without further interpretation:

1. The last F-1 B report and the first F-1 C report are on the same day (2014-02-22). F-1 B records time drilling to 1,364 m and then hands over to F-1 C; F-1 C then drills 17 1/2 in. hole from 1,364 m. That is the same value as NOD's 1,364 m.
2. 3,059 m is the depth reached on 2014-03-11 by drilling out the shoe track and 3 m of new formation, after the 13 3/8 in. and the 10 3/4 x 9 5/8 in. casing strings were run and cemented (casing landed at 3,047 m on 03-08). The 8 1/2 in. RSS drilling that v2 treats as the "oriented drilling start" begins on 2014-03-13 from that depth.
3. No report before 2014-03-13 shows a depth that supports 3,059 m as the depth at which F-1 C leaves F-1 B; the reports before that date are at 1,502 to 3,056 m.

Not decided here (TJ's call): which depth is right for the paper's "kick-off" definition. The user decision recorded in v2 (3,059 m = operational kick-off where new drilling begins, NOD 1,364 m = geometric departure point) assumed that the F-1 C wellbore only begins to be drilled at 3,059 m. The DDRs show the wellbore is already being drilled from 1,364 m on its first day. If the intended quantity is where F-1 C departs from the F-1 B wellbore, the DDR evidence agrees with NOD. If it is where the 8 1/2 in. reservoir section starts, 3,059 m fits, but that is a section start rather than a kick-off. Either way the v2 treatment of 3,059 m versus 1,364 m as a definitional pair needs to be revisited. This affects the shared-interval disclosure for F-1 and F-1 C in Papers 1, 3 and the barrier paper, as stock-take open item 1 warned.

## 4. Same pattern in other sidetracks (flagged, not interpreted)

The quoted depth first appears in the narrative more than 5 days after the sidetrack's first report for three wellbores: F-1 B (7 days, 3,100 m, NOD 2,604 m), F-11 B (10 days, 3,271 m, NOD 2,586 m) and F-1 C (17 days, 3,059 m, NOD 1,364 m). NOD's kick-off differs from ours by more than 30 m for: 15/9-19 B, 15/9-19 BT2, 15/9-F-1 A, 15/9-F-1 B, 15/9-F-1 C, 15/9-F-9 A, 15/9-F-11 B. Exact agreement (0 m) for 19 A, F-15 A, F-15 B and F-15 D; within 10 m for F-11 A (8 m) and F-15 C (9 m). For F-1 A the parent's last measured depth (2,620 m) equals NOD's kick-off, whereas our depth (3,004 m) equals the sidetrack's first measured depth. Whether v2's "operational kick-off" depths are systematically deeper than the point where the wellbore departs is for TJ to judge; the table gives both depths so each row can be checked.

## 5. Structured field

`mdKickoff` is populated in 248 DDRs, in four wellbores, each with one constant value: 19 A 110 DDRs (2178 m), 19 B 27 (2911 m), 19 BT2 62 (2911 m) and 19 S 49 (562 m); 110 + 27 + 62 + 49 = 248. Two points for TJ, no interpretation attempted:

- The 2911 m on the 19 B reports equals the kick-off recovered for 19 BT2, not the 2231 m recovered for 19 B itself.
- 19 S (the original exploration wellbore, no kick-off in v2) carries 562 m in all 49 of its reports. No 19 S narrative contains the number 562, and one 19 S narrative contains a kick-off/whipstock/window cue word (not examined). I have not used the 562 m anywhere.

## Next

Awaiting TJ's decision on F-1 C (and the F-1 B and F-11 B pattern) before Stage 9 (duration table, only if TJ says go) and the later stages.
