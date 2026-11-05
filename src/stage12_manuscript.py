"""Stage 12 (DRAFT): build manuscript/paper2_draft.docx from inputs/paper2_v2.docx, every number from outputs/numbers_registry.json, and manuscript/CHANGES.md.
Yellow highlight = an open [TJ:] note only (the kick-off values are author-approved and carry no highlighting). Marker characters in the text below
(U+27E6 and U+27E7) delimit text to be highlighted; they are never written to the document."""
import copy
import json
import os
import re
import sys
from xml.sax.saxutils import escape

import docx
import pandas as pd
from docx.enum.text import WD_COLOR_INDEX
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Inches
from docx.text.paragraph import Paragraph
from docx.text.run import Run

REG = {e["id"]: e for e in json.load(open("outputs/numbers_registry.json", encoding="utf-8"))}
doc = docx.Document("inputs/paper2_v2.docx")
P = list(doc.paragraphs)
L, R = "⟦", "⟧"
T, LOG, RESOLVED = {}, [], []

# section label of every paragraph (for CHANGES.md)
SEC, cur_sec = {}, "front matter"
for i, p in enumerate(P):
    if p.style.name.startswith("Heading"): cur_sec = p.text.strip()
    SEC[i] = cur_sec


def cur(i):
    return T.get(i, P[i].text)


def strip_marks(s):
    return s.replace(L, "").replace(R, "")


def log(i, old, new, rid, reason):
    assert rid is None or all(r in REG for r in rid.split(";")), rid
    LOG.append(dict(location=f"{SEC[i]} (paragraph {i})" if isinstance(i, int) else i, old=old, new=strip_marks(new), id=rid or "", reason=reason))


def sub(i, old, new, rid, reason):
    t = cur(i); assert t.count(old) == 1, (i, old, t.count(old))
    T[i] = t.replace(old, new); log(i, old, new, rid, reason)


def setp(i, new, old_desc, rid, reason):
    T[i] = new; log(i, old_desc, new if len(new) < 400 else new[:400] + " ...", rid, reason)


def dropnote(i):
    t = cur(i); k = t.index("[TJ:"); note = t[k:]
    RESOLVED.append(dict(location=f"{SEC[i]} (paragraph {i})", note=note)); T[i] = t[:k].rstrip()


def write_par(p, text):
    runs = p.runs; tmpl = copy.deepcopy(runs[0]._r)
    for r in runs: p._p.remove(r._r)
    for part in re.split("(⟦.*?⟧)", text):
        if not part: continue
        hl = part.startswith(L)
        r = copy.deepcopy(tmpl); p._p.append(r); run = Run(r, p)
        run.text = part[1:-1] if hl else part
        run.font.highlight_color = WD_COLOR_INDEX.YELLOW if hl else None


def new_par_after(anchor_el, template_p, text, renum=True):
    text = POST(text) if renum else text
    text = restyle(text)
    el = copy.deepcopy(template_p._p); anchor_el.addnext(el)
    par = Paragraph(el, template_p._parent); write_par(par, text); return par


def run_sub(p, idx, old, new):
    r = p.runs[idx]; assert old in r.text, (old, r.text); r.text = r.text.replace(old, new)


def val(k):
    return REG[k]["value"]


DEL = set()                    # paragraphs deleted at flush time

# ---- style revision (see src/stage12_style_text.py and manuscript/style_diff.md): sentence-level rewrites with guards
sys.path.insert(0, "src")
from stage12_style_text import STYLE
STYLE_USED, STYLE_LOG = set(), []
_NUM = re.compile(r"\d[\d,]*\.?\d*")
_QD = re.compile(r"(?<![\w.,;:!?/])\"(?=[A-Za-z0-9])([^\"]{3,}?)\"(?=[\s.,;:)]|$)")
_QS = re.compile(r"(?<![\w.,;:!?])'([^']{8,}?)'(?=[\s.,;:)]|$)")
_REF = re.compile(r"Table \d+|Fig\. \d+|Section \d(?:\.\d)?|Appendix [AB]")


_CITE = re.compile(r"\((?:[A-Z][A-Za-z.&-]*(?: [A-Za-z.&-]+)* )?(?:19|20)\d\d[a-e]?(?:, (?:19|20)\d\d[a-e]?)*\)")      # citation years such as (Zhang et al. 2022) are not content numbers


def _nums(t): return {x.replace(",", "").rstrip(".") for x in _NUM.findall(_CITE.sub("", t))}


def restyle(old):
    hits = [k for k, (sec, prefix, new) in enumerate(STYLE) if old.startswith(prefix)]
    if not hits: return old
    assert len(hits) == 1, ("ambiguous style prefix", old[:60], hits)
    sec, prefix, new = STYLE[hits[0]]; STYLE_USED.add(hits[0])
    assert _nums(new) <= _nums(old), ("number not in the old text", sec, sorted(_nums(new) - _nums(old)), new[:80])
    for q in _QD.findall(old) + _QS.findall(old): assert q in new, ("quotation changed or dropped", sec, q)
    assert set(_REF.findall(new)) <= set(_REF.findall(old)), ("reference added", sec, set(_REF.findall(new)) - set(_REF.findall(old)))
    assert "—" not in new, "em dash"
    STYLE_LOG.append(dict(section=sec, old=old, new=new, removed_numbers=sorted(_nums(old) - _nums(new)), dropped_refs=sorted(set(_REF.findall(old)) - set(_REF.findall(new)))))
    return new


def delp(i, reason):
    log(i, cur(i)[:160] + (" ..." if len(cur(i)) > 160 else ""), "(paragraph deleted)", None, reason)
    DEL.add(i)


def RENUM(t):                      # two tables were added in Section 3, so the old Tables 1 to 6 become 3 to 8; one figure was added, so the old Figs 1 to 4 become 2 to 5
    t = re.sub(r"\bFig\. ([1-4])\b", lambda m: f"Fig. {int(m.group(1)) + 1}", t)
    return re.sub(r"\bTable ([1-6])\b", lambda m: f"Table {int(m.group(1)) + 2}", t)


ADJ = [("adjudications", "labels"), ("adjudication", "labelling"), ("adjudicator", "labeller"), ("adjudicated", "labelled")]


FRACG = {"1/2": "½", "1/4": "¼", "3/4": "¾", "3/8": "⅜", "5/8": "⅝"}


def POST(t):
    t = RENUM(t)
    t = re.sub(r"(\d+) (\d/\d) in\.", lambda m: m.group(1) + FRACG[m.group(2)] + " in.", t)      # hole sizes in running text: 17 1/2 in. becomes 17½ in.
    for a, b in ADJ: t = t.replace(a, b)
    return t


def subany(old, new, rid, reason):
    hits = [i for i in range(len(P)) if i not in DEL and old in cur(i)]
    assert len(hits) == 1, (old[:60], hits)
    sub(hits[0], old, new, rid, reason)


def app(i, text, rid, reason):
    old = cur(i); T[i] = old.rstrip() + " " + text; log(i, old[-80:], text, rid, reason)


# =========================================================================== front matter and abstract
sub(7, 'The archive also stores 73 narratives as the literal string "None" and 331 depths as a sentinel value, neither of which a simple null test detects.',
    'The archive also stores placeholder values in 515 fields (331 depth sentinels, 7 zero depths, 176 literal "None" strings and one date sentinel) that a simple null test does not detect.',
    "placeholders.total_cells_all_fields", "full placeholder register (decision 19); v2 counted 411 (331 + 7 + 73)")
sub(8, "The output is an open depth-time-phase dataset of 1,421 records, published with the classifier code. It supports days-versus-depth benchmarking and records-based screening of legacy wellbores, and the method transfers to other WITSML 1.4.1.1 archives.",
    f"Sidetrack kick-off depths were recovered for all 15 sidetracks by one rule; where NOD records a kick-off point (12 of 15), the recovered depth agrees within 10 m for 10. The output is an open depth-time-phase dataset of 1,421 records, with per-wellbore durations to total depth, published with the classifier code. It supports days-versus-depth benchmarking and records-based screening of legacy wellbores, and the method transfers to other WITSML 1.4-series drillReport archives.",
    "kickoff.nod_comparison;kickoff.n_sidetracks;data.witsml_schema_version", "new kick-off and duration results; abstract clause on NOD agreement replaces the F-1 family clause (TJ review); WITSML version from the files")
sub(7, "one wellbore-identity conflation", "one NOD entry date that marks a later drilling campaign", "spud.identity", "category renamed from Wellbore-identity conflation (TJ review; F-1 verified: first 2013 report 2013-07-22, no NOD pre-drill date)")
sub(10, "(Energistics 2012)", "(Energistics n.d.)", None, "Energistics reference now cites the schema version declared in the files with an access date (decision 45)")
dropnote(14)
sub(20, "dataset's WITSML 1.4.1.1 XML files into a single managed table holding 1,759 rows", "dataset's WITSML 1.4.0.0 XML files (1,759 files, 21,315,879 bytes, each recorded with a SHA-256 hash) into a single table holding 1,759 rows",
    "data.witsml_schema_version;data.n_xml_files;data.xml_total_bytes", "the files declare version 1.4.0.0 (decision 15); file count and bytes from the raw download")
sub(20, "The raw XML archive was not accessible from the compute environment during the final analysis, so the extracted table is the authoritative dataset for this study; it is published in the repository.",
    "Every field is kept as a raw string at extraction, so placeholder values stay visible, and the table is regenerated from the raw files by the published code.",
    "data.n_xml_files", "v2 said the raw XML was not accessible; it was downloaded and hashed in the rerun")
dropnote(25)
sub(25, "Spud/Conductor, Surface casing, Intermediate drilling, Intermediate casing, Reservoir drilling, Liner/Casing run", "Spud/Conductor, Surface hole and casing, Intermediate drilling, Intermediate casing, 12¼ in. and smaller hole, Liner/Casing run", None,
    "label-only change (TJ review): phase names Surface casing and Reservoir drilling renamed for display; classifier patterns and priorities are frozen and untouched")
sub(25, "because drilling reports frequently express hole and casing sizes with these glyphs.",
    "because drilling reports frequently express hole and casing sizes with these glyphs. The priority order is the order listed above. Hole and casing size separate the drilling phases: 36 in. hole and 30 in. conductor (Spud/Conductor), 26 in. hole and 20 in. casing (Surface hole and casing), 17½ in. hole (Intermediate drilling), 13⅜, 10¾ and 14 in. casing (Intermediate casing), 12¼, 8½ and 6 in. hole and coring (12¼ in. and smaller hole), and 9⅝ and 7 in. liner or casing (Liner/Casing run); the remaining phases are matched on keywords alone. Phase names describe the hole and casing sizes each pattern group matches; on Volve platform wells the 12¼ in. hole is usually the section above the reservoir. Every regular expression is listed in the repository file src/classifier_v3.py.",
    "classifier.size_patterns", "resolves the open note on priority order and hole-size rules (open item 3)")
dropnote(29)
sub(29, "was drawn from these 383 with a fixed random seed of 42.", "was drawn from these 383 with a fixed random seed of 42; the rerun of the analysis from the raw files kept this sample and its strata, after confirming that each of the 50 records maps to exactly one DDR file.",
    "audit.sample_size", "reproducibility statement for the kept sample (decision 6)")
sub(29, "Each sampled record was adjudicated as CONSTRUCTION", "Each sampled record was adjudicated by the author as CONSTRUCTION", None, "open item 4 resolved: the author made all 50 calls")
sub(31, "(4,562.1 m and 4,562.0 m).", "(4,562.1 m and 4,562.0 m). The NOD export was retrieved on 24 October 2026; its rows for the Volve wellbores are identical to an export taken on 8 September 2026 except for the register's own synchronisation date.",
    "data.nod_snapshot_date", "NOD snapshot refreshed and compared with the September snapshot")
sub(32, "new hole was kicked off from 2,911 m under", f"new hole was kicked off from 2,911 m under", "kickoff.proposed_depth.15/9-19 BT2", "kick-off depth, author-approved (unchanged value)")
sub(32, "new hole from approximately 1,536 m under", f"new hole from approximately 1,536 m under", "kickoff.proposed_depth.15/9-19 ST2", "kick-off depth, author-approved (unchanged value)")

# =========================================================================== 4 Data quality
sub(40, 'but 73 records contain the literal string "None", almost certainly the product of a Python str(None) conversion during the original extraction. A null test cannot detect a non-empty placeholder of this kind. Correcting for it, the genuine narrative population is 95.85% (1,686 of 1,759).',
    'but 73 records contain the literal string "None". The string is stored in the source XML itself (73 of the 1,759 files contain it), so it is a placeholder in the archive, not an artefact of extraction. A null test cannot detect a non-empty placeholder of this kind. Correcting for it, the genuine narrative population is 95.85% (1,686 of 1,759). The same placeholder appears in 103 forecast24hr values, so the genuine forecast population is 94.14% (1,656 of 1,759). Counting every placeholder in every extracted field gives 515 values: 331 depth sentinels, 7 zero depths, 176 literal "None" strings (73 narratives and 103 forecasts) and one date sentinel; 331 + 7 + 176 + 1 = 515.',
    "placeholders.none_sum24Hr;placeholders.none_forecast24hr;placeholders.none_total;placeholders.total_cells_all_fields;table1.forecast24hr_genuine.count;table1.forecast24hr_genuine.pct",
    "the None string is in the source archive (decision 12); forecast24hr treated like sum24Hr (decision 18); full placeholder total (decision 19)")
sub(41, "17.5 years before", "17.6 years before", "data.sentinel_years_before_first_ddr", "6,415 days / 365.25 = 17.56; TJ ruling 4 (v2 said 17.5)")
sub(41, "It is a date sentinel, not a drilling report.", "It is a date sentinel, not a drilling report. The raw files declare the ISO-8859-1 character encoding; reading them correctly repaired an encoding error that affected 103 narratives in the earlier extraction (for example the character Ø), which changes no phase.",
    "extract.old_table_encoding_rows_sum24Hr", "new finding from the raw-data rerun")

# =========================================================================== 5 Results
sub(44, "The result was checked three ways: a row-count query (1,759), a differently worded phase-distribution query returning identical per-phase counts, and manual tracing of eight randomly selected records against their matching or non-matching expressions.",
    "The ported classifier was first checked against the earlier extraction: on the narratives of the earlier table it reproduced the 1,303 classified records, every per-phase count, and the earlier phase label of all 1,759 records. Applied to narratives read directly from the raw XML it gave the same phase counts, and the 103 narratives whose encoding was repaired (Section 4) changed no phase.",
    "classifier.faithfulness_classified_on_old_text;classifier.faithfulness_row_mismatches;classifier.mojibake_phase_changes", "v2 verification steps replaced by the faithfulness check run in the rerun")
sub(52, "a direct query against the classified table returned exactly 1,421.", "recomputing the dataset from the raw XML gave the same 1,421 rows as the earlier analysis, identical in every column.", "timeline.rows", "rerun check against the v2 dataset")
sub(52, "days from first DDR, measured depth", "days from the wellbore's first report with a recorded depth, measured depth", None, "wording fix (TJ note 4): days are counted from each wellbore's first row with a usable depth")
sub(52, "Fig. 2 plots days since first DDR against measured depth for all 26 wellbores.",
    "Days are therefore counted from each wellbore's first row with a usable depth, not from its first DDR. Fig. 2 plots report number against measured depth for all 26 wellbores. The report number counts every DDR of a wellbore from its first report (1980 sentinel excluded), with or without a recorded depth, so it is the same count as the reports to TD of Table 6; only reports with a valid depth are plotted. The days_from_first_ddr column of the dataset is unchanged from the earlier analysis.", None, "Fig. 2 x-axis changed from calendar days to report count, counted as in Table 6 (TJ review)")
dropnote(61)
sub(61, "Table 4 summarises the outcome, and Fig. 4 plots the offset (WITSML minus NOD) by category.",
    f"Table 4 summarises the outcome, and Fig. 4 plots the offset by category. The offset is the WITSML spud date minus the NOD pre-drill entry date where NOD records one, since it marks the start of top-hole drilling, and otherwise the NOD main entry date. For the four wellbores whose archive contains the NOD pre-drill entry (15/9-F-4, F-5, F-14 and F-15), the first report coincides with that date (the same day, or one day later for F-4), which supports using the pre-drill date as the spud reference. The categories were assigned by inspection of the three sources for each wellbore, and the rules in the Rule column of Table 4 were formalised afterwards to describe those assignments. Applied mechanically, the rules reproduce 25 of the 26 assignments. 15/9-F-11 was assigned Exact by inspection but is unresolved under the rule: NOD records a pre-drill campaign (6 to 17 April 2012) that is absent from the DDR archive; the archive's 2013 reports describe a fresh spud from seabed, including the 30-inch conductor, so the relationship between the two campaigns cannot be determined from these records.",
    "spud.rule_thresholds_days;spud.table4;spud.unresolved;spud.predrill_first_ddr_offset_days;spud.F-11.predrill_period", "resolves the open note on spud tolerances (open item 5); NOD date rule (decision 47); F-11 stays Unresolved (decision 48); TJ review: category rules moved to the Rule column of Table 4 and the paragraph reordered (reference date, pre-drill evidence, inspection then formalised rules, 25 of 26, F-11)")
sub(64, "by three months to a full year", "by 91 to 340 days", "spud.table4", "recomputed offsets against the first report (F-12 91, F-4 92, F-7 137, F-15 340 days)")
sub(65, "an ordinary spud-to-first-report gap. NOD, however, records an entry date of 23 July 2013, nearly six years later and about four weeks before the WITSML spud date (20 August 2013) and NOD entry date (23 August 2013) of 15/9-F-1 A, the sidetrack drilled from the same slot. NOD's 15/9-F-1 record most plausibly reflects the 2013 re-entry ahead of the sidetrack campaign, not the 2007 spud. The case is therefore classified as a wellbore-identity conflation: the WITSML value is consistent with the wellbore's own chronology.",
    "an ordinary spud-to-first-report gap. The 2007 reports are top-hole only (four reports, maximum depth 226 m). F-1 was drilled to its total depth of 3,632 m in the 2013 campaign, whose first report (22 July 2013) is one day before NOD's entry date (23 July 2013). NOD records no pre-drill date for the 2007 work, unlike F-4, F-5, F-14 and F-15. NOD's date therefore marks the later campaign, not the 2007 spud, and the case is classified as NOD date marks later campaign: the WITSML value is consistent with the wellbore's own chronology.",
    "f1.reports_2007;f1.reports_2013;f1.spud_section_statement;f1.first_report_2013;f1.nod_main_entry_date;f1.nod_predrill_entry_date", "TJ ruling 3 (decision 42); TJ review: category renamed, F-1 paragraph rewritten after verifying that the first 2013 report is 2013-07-22 and that NOD records no pre-drill date for F-1; the re-entry-ahead-of-the-sidetrack reading removed")

# ---- 5.6 kick-off (rewritten), 5.7 duration (new)
dropnote(67)
setp(67, "Because the structured kick-off field is sparse, kick-off depth was recovered from the DDRs. The kick-off depth of a sidetrack is the depth at which it leaves its parent wellbore. Kick-off here means the depth at which a sidetrack departs its parent wellbore, not the depth at which an original wellbore begins to build angle; the structured kick-off field of 15/9-19 S (562 m in all its reports) is consistent with the latter and is not used. It was read from the parent's last and the sidetrack's first reports by one rule applied to all sidetracks: the depth at which the narrative first reports new formation or departure from the parent hole; where none is stated, the depth at which the kick-off or window is started (for casing exits by a milled window, the top of the window); and where the narrative is empty, the measured depth at the parent-to-child transition.",
     "v2 5.6 first paragraph (twelve free-text and two depth-sequence recoveries)", "kickoff.ruling_window_top;kickoff.19S_structured_field_m", "Section 5.6 rewritten from the kick-off table with the uniform rule (decisions 27, 32, 40); TJ review: sentence on the meaning of kick-off and the 15/9-19 S structured field added (decision 55)")
dropnote(69)
setp(69, f"NOD's wlbKickOffPoint is available for 12 of the 15 sidetracks. It equals the recovered depth for 6 (15/9-19 A, F-1 A, F-1 C, F-15 A, F-15 B and F-15 D), differs by 10 m or less for 4 (15/9-F-9 A, F-11 A, F-11 B and F-15 C), and by more for 2 (15/9-19 B, 31 m; 15/9-F-1 B, 13 m). NOD has no kick-off value for 3 (15/9-19 BT2, 19 ST2 and F-11 T2). The least certain depths are 15/9-19 ST2, which rests on the measured depth alone, and 15/9-F-11 B, where the narrative reports cement and new formation drilled from 2,531 to 2,589 m and the end of the interval is taken as the departure.",
     "v2 5.6 paragraph on NOD's wlbKickOffPoint (operational versus geometric definition)", "kickoff.nod_comparison;kickoff.F-11 B.interval_m", "the 'operational versus geometric' paragraph is deleted (decision 27); NOD comparison counts from the kick-off table")
sub(75, 'and the narrative string "None" together affect 411 field values (331 + 7 + 73).', 'and the string "None" (in the narrative and forecast fields), together with the date sentinel, affect 515 field values (331 + 7 + 176 + 1).',
    "placeholders.total_cells_all_fields", "full placeholder register (decision 19)")
sub(72, "concentrated in drilling progress reported without a hole size.", "concentrated in drilling progress reported without a hole size. Table 6 gives elapsed days, reports and metres per report-day to total depth for each wellbore as a first benchmark, with the gap flag marking wellbores whose elapsed time cannot be read as drilling time.",
    "duration.table", "new duration results")
sub(82, "such as 15/9-F-1 and 15/9-F-1 C, are not independent penetrations above their kick-off depth.", f"such as the four wellbores of the 15/9-F-1 family, which share the hole above 1,364 m MD, are not independent penetrations above their kick-off depths.",
    "kickoff.F-1_family_shared_hole_above_m", "decision 34 replaces the 'F-1 / F-1 C share formations above 3,059 m' statement")
sub(84, "any WITSML 1.4.1.1 archive", "WITSML 1.4-series drillReport archives (tested here on 1.4.0.0)", "data.witsml_schema_version", "WITSML version from the files; TJ review: tested only on 1.4.0.0")
sub(72, "Days-versus-depth curves (Fig. 2)", "Depth-versus-report-count curves (Fig. 2)", None, "Fig. 2 x-axis is the report number (TJ review)")
sub(88, "2013 re-entry reports ahead of the F-1 A sidetrack", "2013 drilling campaign reports", None, "F-1 stratum wording (TJ review)")
sub(98, "one apparent error is a wellbore-identity conflation in the register", "one apparent error is a NOD entry date that marks a later drilling campaign", "spud.identity", "category renamed (TJ review)")
sub(87, "was adjudicated by a single reviewer, and", "was adjudicated by a single reviewer, the author, and", None, "open item 4 resolved")
setp(90, f"Kick-off depths were read from the narratives by one rule, and two rest on weaker evidence: 15/9-19 ST2 on the measured depth alone and 15/9-F-11 B on an interval of cement and new formation (2,531 to 2,589 m). NOD gives no kick-off point for three sidetracks. All four wellbores of the 15/9-F-1 family (F-1, F-1 A, F-1 B and F-1 C) share the hole above 1,364 m MD, and F-1, F-1 A and F-1 B share it above approximately 2,617 to 2,620 m MD; any formation-level analysis treating them as independent must account for this. Metres per report-day are rates per reported day, not per elapsed day, and the elapsed time to total depth is affected by gaps between reports in the archive (the gap flag in Table 6).",
     "v2 limitation: two depth-sequence kick-offs; F-1 and F-1 C shared interval above the F-1 C kick-off", "kickoff.F-1_family_shared_hole_above_m;kickoff.F-1_F-1A_F-1B_shared_hole_above_m;kickoff.F-11 B.interval_m", "decisions 34 and 40; duration caveat added")
sub(92, "The analysis uses the extracted table rather than the raw XML, so any extraction error upstream of that table would propagate.", "The analysis starts from the raw XML, extracted by the published code with every field kept as a raw string, but an extraction error would still propagate to every result.",
    "data.n_xml_files", "v2 said the analysis used the extracted table; the rerun starts from the raw files")
sub(99, "affect 411 field values", "affect 515 field values", "placeholders.total_cells_all_fields", "full placeholder register (decision 19)")
sub(101, "and use the dataset for phase-duration benchmarking across the campaign.", "and extend the duration results to phase-level durations across the campaign.", None, "duration results now reported (Section 5.7)")
dropnote(104)
setp(104, f"Generative AI (Anthropic Claude, used through Claude Code) built and ran the reproducible analysis pipeline from the raw data and was used to assist with debugging, checking arithmetic and editing the manuscript text. The sidetrack kick-off depths were proposed by the AI tool from the narratives under a fixed order of preference. The author rejected the tool's first proposals for three sidetracks (15/9-19 A, 15/9-F-9 A and 15/9-F-11 B) and kept the earlier values, then reviewed all 15 depths and approved every one without change. The author made all audit adjudications (50 in the audit of unclassified reports and 52 phase labels in the agreement check), reviewed all AI-assisted content, and takes full responsibility for the paper. The causes of the 22 disagreements in the agreement check were assigned by the AI tool from the narratives and are indicative.",
     "v2 AI disclosure (writing, debugging, arithmetic, editing; note about audit adjudication and figures)", None, "AI disclosure matches what happened: AI proposed, author reviewed all 15 rows of the sign-off workbook, approved all 15, changed none, marked none N (decisions 37, 40 and 52)")
dropnote(106)
setp(106, f"The classifier, the extraction and analysis code, the 1,421-row timeline dataset, the audit adjudications (file name, wellbore, date, stratum, call and miss reason), the phase-agreement labels (record id, wellbore, date, assigned phase and the author's phase, with the category and proposed cause of each disagreement; no narrative text), the NOD comparison tables, the kick-off and duration tables, and a numbers registry tracing every reported figure to the script that produced it are available in release v1.0 of the repository at https://github.com/985185/volve-well-construction-timeline/releases/tag/v1.0. DDR narrative text is not redistributed: the Volve data are available from Equinor under the Equinor Open Data Licence (https://www.equinor.com/energy/volve-data-sharing), and the repository holds only file names, dates, depths, categories and quotes of 15 words or fewer. Comparisons with the author's earlier extraction are reported but are not needed to reproduce any figure.",
     "v2 availability statement (audit sample with adjudications, extracted DDR table, NOD tables, registry)", None, "licence and no-narrative-text policy (decisions 26 and 46); TJ review: sentence on the earlier-extraction comparisons added (decision 58); the extracted table is no longer published because it holds narrative text; Stage 13 check: every item listed exists in the repository (decision 57), so the confirmation note is removed")
setp(143, f"Every quantitative figure in this paper traces to an entry in the numbers registry published in the repository ({REG['registry.n_entries']['value']} entries, each with the producing script and function, the SHA-256 of its input files and an execution timestamp). The audit estimates in Section 5.2 are derived arithmetically from registry entries, and the arithmetic is shown in the text.",
     "v2 Appendix A (59 entries, each with the exact query and execution timestamp)", "registry.n_entries", "registry rebuilt with 224 entries; resolves the open note on the attainable-rate and placeholder-total entries")
RESOLVED.append(dict(location=f"{SEC[143]} (paragraph 143)", note=P[143].text[P[143].text.index("[TJ:"):]))

# references and captions
assert P[119].runs[0].text.rstrip().endswith("2012."), P[119].runs[0].text
run_sub(P[119], 0, "2012.", "n.d.")
run_sub(P[119], 1, "Version 1.4.1.1", "data schema version 1.4.0.0, as declared in the Volve DDR files")
run_sub(P[119], 2, "witsml-data-standards/.", "witsml-data-standards/ (accessed 24 October 2026).")
log("References (paragraph 119)", "Energistics. 2012. ... Version 1.4.1.1", "Energistics. n.d. ... data schema version 1.4.0.0, as declared in the Volve DDR files ... (accessed 24 October 2026)", "data.witsml_schema_version",
    "release label and year of 1.4.0.0 could not be verified (decision 45), so the schema version is cited with an access date")
sub(123, "(accessed 8 September 2026)", "(accessed 24 October 2026)", "data.nod_snapshot_date", "snapshot refreshed")
t129 = P[129]; run_sub(t129, 0, "Coley, C.,", "Coley, C.J.,"); t129._p.remove(t129.runs[1]._r)
RESOLVED.append(dict(location="References (paragraph 129)", note="[TJ: verify] (Sidahmed et al. 2015); verified through the Crossref record of DOI 10.2118/173429-MS, decision 44"))
log("References (paragraph 129)", "Sidahmed, M., Coley, C., and Shirzadi, S. 2015 ... [TJ: verify]", "Sidahmed, M., Coley, C.J., and Shirzadi, S. 2015 ...", None, "title and authors verified through Crossref (OnePetro returned 403); citation kept")
sub(137, "Fig. 2: Days since first DDR versus measured depth for all 26 wellbores, coloured by phase.", "Fig. 2: Report number (1 = the wellbore's first report, as counted in Table 6) versus measured depth for all 26 wellbores, coloured by hole section (other phases and unclassified reports in grey).", None, "Fig. 2 x-axis is the report number (TJ review)")
sub(139, "for the 24 matched wellbores, with 1:1 reference line.", "for the 24 matched wellbores, with 1:1 reference line. The two unmatched wellbores (15/9-19 B and 15/9-F-11) are not plotted.", None, "title removed from the image; information moved to the caption (TJ review)")
sub(141, "Fig. 4: Spud date offset (WITSML minus NOD) for 25 wellbores, coloured by validation category.", "Fig. 4: Spud date offset (WITSML spud date minus the NOD pre-drill entry date where recorded, otherwise the NOD main entry date) for 25 wellbores, coloured by validation category. The bar of 15/9-F-1 (offset -2,064 days) is clipped at -400 days and labelled with its value.", "spud.table4", "one offset definition, outcome-independent NOD date rule (decisions 41 and 47)")

# =========================================================================== TJ review, round 2 (structure and wording)
sub(6, "The final classifier version assigns", "It assigns", None, "no classifier versions named (TJ review)")
sub(7, "because the archive does not cover", "because the DDR archive does not cover", None, "wording (TJ review)")

# 1 Introduction: one paragraph, contribution reduced to one sentence
t11 = cur(11); k11 = t11.index("The paper is written to be self-contained")
CONTRIB = "The contribution is the combination, on a real, openly licensed field archive, of a transparent classifier, an estimate of what that classifier misses, validation against the regulator's register for every wellbore rather than a subset, and a description of the data-quality problems that any other user of the archive will meet. "
setp(10, cur(10) + " " + t11[:k11] + CONTRIB + t11[k11:], "v2 Introduction, three paragraphs (context, scope, contribution and roadmap)", None, "TJ review: Introduction merged into one paragraph; the contribution paragraph reduced to one sentence; roadmap sentences removed")
delp(11, "merged into the first Introduction paragraph (TJ review)")
delp(12, "reduced to one sentence inside the first Introduction paragraph (TJ review)")

# 2 Background
t14 = cur(14); T[14] = "Several studies have extracted structured information from the free text of drilling reports." + t14[t14.index(" Sidahmed"):]
log(14, "Text analytics on drilling reports has developed alongside operators' interest in extracting structured information from legacy narratives.", "Several studies have extracted structured information from the free text of drilling reports.", None, "opening sentence replaced (TJ review)")
t17 = cur(17); a17 = t17.index("The present paper differs in three respects."); b17 = t17.index(" a stratified audit")
T[17] = t17[:a17] + "The present paper differs in three respects: (1) it uses a deterministic, auditable classifier, trading model sophistication for transparency of every decision; (2) it works exclusively with a real, openly licensed archive; and (3) it pairs classification with" + t17[b17:]
log(17, "three respects as three sentences", "three respects numbered (1), (2), (3) inline", None, "TJ review")

# 3 Section 3.1
sub(20, "The Volve field (block 15/9, Norwegian North Sea), operated by Equinor (formerly Statoil), was released as an open dataset after decommissioning (Equinor 2018). The DDR archive was extracted from the dataset's", "The DDR archive was extracted from the Volve dataset's", None, "sentence repeating the Volve introduction removed (TJ review)")

# 4 Section 3.6 deleted
delp(33, "Section 3.6 deleted (TJ review); it was the last subsection of Section 3, so no other subsection is renumbered")
delp(34, "Section 3.6 deleted (TJ review)")

# 6 and 7 Section 3.3
sub(25, "Before matching, vulgar-fraction characters (½, ¼, ¾, ⅛) are replaced with ASCII equivalents, because drilling reports frequently express hole and casing sizes with these glyphs.",
    "Before matching, fraction characters such as ½ and ¼, routine in the mixed units of drilling reports, are stored as single special characters that a pattern written as \"1/2\" does not match, so they are converted first.", None, "wording (TJ review)")
delp(26, "paragraph on three classifier versions deleted: classifier versions are not named in the text (TJ review)")
sub(28, "complete v3 pattern set", "complete pattern set", None, "no classifier versions named (TJ review)")

# 9 Section 3.4 in plain language
setp(29, "A stratified sample of 50 records was drawn from these 383. The unclassified reports were split into two strata, an early construction group (reports within 730 days of the wellbore's first report, 296 records) and a later production group (reports more than 730 days after it, 87 records; 296 + 87 = 383), and a random sample was drawn from each in proportion to its size: 39 construction-group and 11 production-group records (39 + 11 = 50). The random draw is recorded in the repository so the same sample can be drawn again; the rerun of the analysis from the raw files kept this sample and its groups, after confirming that each of the 50 records maps to exactly one DDR file. The author read each sampled report and labelled it construction if it described work that builds the well: drilling ahead, coring, running or cementing casing, setting plugs, fishing, or completion. Reports that only described handling the BOP or riser, tripping, waiting or production were labelled non-construction, unless they also named a hole or casing size.",
     "v2 Section 3.4, second paragraph (stratified sample, seed, adjudication rule)", "audit.sample_size;audit.stratum_construction;audit.stratum_production;audit.sample_construction;audit.sample_production;audit.strata_cutoff_days;audit.frame_size",
     "TJ review: plain-language description of the stratified sample and the labelling rule; the seed is no longer quoted; adjudicated replaced by labelled")

# 14 Section 3.2, 3.5 and references
sub(23, "(NOD 2026e)", "(NOD 2025)", "external.nod_guidelines_revision_date", "the guidelines are cited by their own revision (28 March 2025, stated in the document's revision history), not as a FactPages page (TJ review)")
app(31, "All comparisons are against the current register as accessed in October 2026.", "data.nod_snapshot_date", "TJ review")
IDX_E = [i for i in range(len(P)) if P[i].text.startswith("Norwegian Offshore Directorate. 2026e")]; assert len(IDX_E) == 1
IDX_A = [i for i in range(len(P)) if P[i].text.startswith("Norwegian Offshore Directorate. 2026a")]; assert len(IDX_A) == 1
sub(IDX_E[0], "2026e. Guidelines for Designation of Wells and Wellbores.", "2025. Guidelines for Designation of Wells and Wellbores (revision of 28 March 2025).", "external.nod_guidelines_revision_date", "TJ review: cited by its own revision date; 2026a to 2026d now denote FactPages pages only, each with an access date")

# 12 Section 4: a real before and after phrase
_ex = val("extract.encoding_example")
sub(41, "(for example the character Ø)", f"(for example, the earlier table held '{_ex['earlier_table']}' where the raw file reads '{_ex['raw_file']}')", "extract.encoding_example", "real before and after phrase (TJ review)")
sub(41, "the vulgar fraction one-half (½)", "the fraction character one-half (½)", None, "wording (TJ review)")

# 5.1 and 5.2
sub(44, "Applying v3 to all 1,759 DDRs", "Applying the classifier to all 1,759 DDRs", None, "no classifier versions named (TJ review)")
subany("Phase distribution, v3 classifier", "Phase distribution", None, "no classifier versions named (TJ review)")
OLD50 = cur(49)
setp(49, "26 of the 50 sampled reports (52%) were construction work. Scaled to the 383-report frame this is about 199 reports, so a complete pattern set would classify about 85.4% of the 1,759 reports (95% confidence interval 82.5 to 88.3%). The arithmetic, including the stratum-weighted check, is in Appendix B.",
     "v2 Section 5.2, arithmetic paragraph", "audit.construction_calls;audit.sample_size;audit.frame_size;audit.residual_miss_ddrs;audit.attainable_rate_pct;audit.attainable_ci_low_pct;audit.attainable_ci_high_pct",
     "TJ review: plain result kept in the text; full arithmetic and the stratum-weighted check moved to Appendix B")
subany("and the arithmetic is shown in the text.", "and the arithmetic is shown in Appendix B.", "registry.n_entries", "TJ review")

# 13 Section 5.4: 15/9-19 S
app(59, "The archive's reports for this wellbore are incomplete throughout, with 39 reports over 91 days (Table 6), and the cause cannot be determined from the records.", "duration.table", "TJ review: no cause is proposed")

# limitations
subany("but its effect was not separated from other pattern changes between versions.", "but its effect was not separated from other refinements of the pattern set.", None, "no classifier versions named (TJ review)")

# =========================================================================== TJ review, round 3
# 2 Background: Karnot et al. (2025)
IK = [i for i in range(len(P)) if cur(i).startswith("The nearest comparable published work is Karnot")]; assert len(IK) == 1
setp(IK[0], "Karnot et al. (2025) combine change-point detection, semi-supervised natural language processing and sequence mining for root-cause analysis of non-productive time, applied to 701 DDRs from 10 wells. Their Dataset section states that \"all analyses used synthetic datasets constructed to emulate typical drilling records\". Their sequence-mining section, which they describe as a proof-of-concept analysis, states that \"rigorous validation and quantitative performance assessment are left for future work\". Their abstract and conclusions nevertheless report an average 18.5% reduction in non-productive time in field applications.",
     "v2 Section 2, Karnot et al. paragraph", "literature.karnot_2025", "TJ review round 3 and 4: description replaced; both quotations and the 18.5% verified by the author against the source PDF (26 October 2026); the first quotation is from the Dataset section, the second from the sequence-mining section (a proof-of-concept analysis)")
subany("The common limitation across the published DDR work is that it relies on proprietary or synthetic data, so its results", "The common limitation across the published DDR work is that its data are proprietary or synthetic rather than an openly available archive, so its results", None, "kept consistent with the Karnot et al. description (TJ review round 3)")

# 3 F-12
IF = [i for i in range(len(P)) if cur(i).startswith("In the four error cases")]; assert len(IF) == 1
tF = cur(IF[0]); a0 = tF.index("In the four error cases"); a1 = tF.index("Two sidetracks, 15/9-F-11 A")
T[IF[0]] = tF[:a0] + "In the four error cases the structured spud_date contradicts the wellbore's own first report and its narrative by 91 to 340 days, while the first report and the NOD date agree with each other. 15/9-F-12 is the clearest example: the first report (14 June 2007), which describes making up the 36 in. hole opener, and the NOD entry date agree, and only the structured field (15 March 2007) disagrees. " + tF[a1:]
log(IF[0], "three sources agree on 14 June 2007 (first DDR, narrative, NOD)", "the first report and the NOD entry date agree; the first report and its narrative are one document", "spud.F-12.witsml_spud;spud.F-12.first_ddr", "TJ review round 3: the first DDR and the free-text evidence are the same report, so 'three sources' overstated the agreement")

# availability statement: the 15-word limit is for the repository's data files
subany("and the repository holds only file names, dates, depths, categories and quotes of 15 words or fewer.", "and the data files of the repository hold only file names, dates, depths, categories and quotes of 15 words or fewer.", None, "the 15-word limit applies to data files, not to quotations in the manuscript (decision 67)")

# post-processing of every original paragraph: table numbers (+2) and the labelling words
for i in range(len(P)):
    if i in DEL: continue
    t = cur(i); nt = POST(t)
    if nt != t: T[i] = nt
log("Tables", "Tables 1 to 6", "Tables 3 to 8", None, "two tables were added in Section 3 (the example report, Table 1, and the phases, Table 2), so every later table number moves up by two; every reference in the text moves with it")
log("Whole text", "adjudicated, adjudication, adjudications, adjudicator", "labelled, labelling, labels, labeller", None, "plain language (TJ review)")

# =========================================================================== final review fixes (28 October 2026)
def ix(prefix):
    hits = [i for i in range(len(P)) if i not in DEL and cur(i).startswith(prefix)]
    assert len(hits) == 1, (prefix, hits)
    return hits[0]


# 1 no earlier extraction / analysis / table, except one sentence in 5.1
i = ix("A character-level survey of sum24Hr"); t = cur(i); k = t.index("The raw files declare the ISO-8859-1")
T[i] = t[:k] + f"The raw files declare the ISO-8859-1 character encoding; reading them with the wrong encoding turns ½ into Â½ (for example '{_ex['earlier_table']}' instead of '{_ex['raw_file']}'), so the encoding must be set explicitly."
log(i, t[k:], T[i][k:], "extract.encoding_example", "final review: the encoding point rephrased as a lesson for users; the comparison with the earlier table and the count of 103 removed")
i = ix("Applying the classifier to all 1,759 DDRs"); t = cur(i); a = t.index("The ported classifier was first checked"); b = t.index("Table 4 gives")
T[i] = t[:a] + "The classifier was also checked against an independent earlier extraction of the same archive by the author, with identical results for all 1,759 reports. " + t[b:]
log(i, t[a:b], "The classifier was also checked against an independent earlier extraction of the same archive by the author, with identical results for all 1,759 reports.", "classifier.faithfulness_classified_on_old_text;classifier.faithfulness_row_mismatches", "final review: the one remaining mention of the earlier extraction")
subany("; recomputing the dataset from the raw XML gave the same 1,421 rows as the earlier analysis, identical in every column.", ".", "timeline.rows", "final review: comparison with the earlier analysis removed")
subany(" The days_from_first_ddr column of the dataset is unchanged from the earlier analysis.", "", None, "final review: sentence removed")
subany("Comparisons with the author's earlier extraction are reported but are not needed to reproduce any figure.", "The check against the author's earlier extraction (Section 5.1) is reported but is not needed to reproduce any figure. Agreement between the classifier and the author's labels can be recomputed from the published paired labels, but checking the labels themselves requires the source narratives from the Equinor dataset.", None, "final review: matches the single mention in Section 5.1; third review: how the agreement can be checked")

# 2 and 6 Section 5.2 merged; construction group and production group; plain words
i49 = ix("Of the 50 sampled records"); i50 = ix("26 of the 50 sampled reports"); i51 = ix("The 73 EMPTY_RECORD DDRs")
setp(i49, "Of the 50 sampled reports, 26 (52%) were labelled construction and 24 (48%) non-construction. The construction group (39 reports) split 23 construction to 16 non-construction, and the production group (11 reports) split 3 to 8. The 26 construction reports that the classifier missed fall into three kinds: genuine drilling reported without a hole size (9); other operations, such as hydraulic fracturing or fishing, with no corresponding pattern (10); and non-standard terms, such as \"CMT\" for cement (7); 9 + 10 + 7 = 26. Scaled to the 383-report frame, this is about 199 reports, so a complete pattern set would classify about 85.4% of the 1,759 reports (95% confidence interval 82.5 to 88.3%). The arithmetic, including the stratum-weighted check, is in Appendix B.",
     "Section 5.2, two paragraphs (counts and plain result)", "audit.construction_calls;audit.sample_size;audit.sample_construction;audit.sample_production;audit.construction_calls_construction_era;audit.construction_calls_production_era;audit.miss_reason.NO_HOLE_SIZE;audit.miss_reason.OTHER_MISS;audit.miss_reason.NONSTANDARD_TERMINOLOGY;audit.residual_miss_ddrs;audit.attainable_rate_pct;audit.attainable_ci_low_pct;audit.attainable_ci_high_pct",
     "final review: the two paragraphs merged so that 26 of 50 appears once; construction group and production group; code labels replaced by plain words")
delp(i50, "merged into the first paragraph of Section 5.2 (final review)")
sub(i51, "The 73 EMPTY_RECORD DDRs are excluded", "The 73 DDRs whose narrative is the literal string \"None\" are excluded", None, "final review: plain words instead of the code label")
subany("were labelled NON_CONSTRUCTION, so the attainable rate", "were labelled non-construction, so the attainable rate", None, "final review: plain words")
i = ix("Two records were assigned to a stratum"); t = cur(i)
T[i] = t.replace("to a stratum that does not reflect", "to a group that does not reflect").replace("production-era stratum", "production group")
log(i, "stratum, production-era stratum", "group, production group", None, "final review: construction group and production group")

# 3.4 plain words for the category names (code labels stay in repository files)
subany("(for example BOP_RISER, GENERIC_TRIP, PRODUCTION_MON, and EMPTY_RECORD)", "(for example BOP and riser handling, generic trips, production monitoring, and empty records)", None, "final review: plain words in Section 3.4")
subany("The 73 records in EMPTY_RECORD have a sum24Hr field", "The 73 empty records have a sum24Hr field", None, "final review: plain words in Section 3.4")

# 3 Section 5.6 definition
subany("The kick-off depth of a sidetrack is the depth at which it leaves its parent wellbore. Kick-off here means", "Kick-off here means", None, "final review: one definition sentence")
subany("is consistent with the latter and is not used. It was read from the parent's last", "is consistent with the latter and is not used. The kick-off depth was read from the parent's last", None, "final review: the dangling pronoun fixed")

# 4 Section 3.3
i = ix("Each DDR's sum24Hr narrative is classified"); t = cur(i)
a = t.index("Before matching, fraction characters"); b = t.index("The priority order is the order listed above.")
t = t[:a] + "Fraction characters such as ½ and ¼, routine in the mixed units of drilling reports, are stored as single special characters that a pattern written as \"1/2\" does not match, so they are converted to that form before matching. " + t[b:]
a = t.index("Hole and casing size separate the drilling phases:"); b = t.index("the remaining phases are matched on keywords alone. ") + len("the remaining phases are matched on keywords alone. ")
T[i] = t[:a] + t[b:]
log(i, "fraction sentence; list of hole and casing sizes", "fraction sentence rewritten; the size list deleted (Table 2 carries it)", "classifier.phase_table", "final review")

# 8 Abstract
app(ix("Sidetrack kick-off depths were recovered for all 15 sidetracks by one rule; where NOD"), "The results show that neither the structured fields nor the national register alone gives a complete well history; the narrative reports are needed to correct both.", None, "final review: closing sentence of the abstract")

# reference verification, in-text (28 October 2026)
sub(ix("Several studies have extracted"), "Hoffimann et al. (2017) applied deep natural language processing to classify sentences in drilling reports from hundreds of wells in a single field as", "Hoffimann et al. (2018) applied deep natural language processing to classify sentences in 9,670 daily reports from a field of 303 wells as", "literature.hoffimann_2018", "published SPE version cited (SPE-191505-MS, 2018); description with the verified figures (author check, 28 October 2026)")
i = ix("Several studies have extracted"); t = cur(i); k = t.index("Zhang et al. (2022) compared")
T[i] = t[:k] + "Zhang et al. (2022) built a rule-based detector for five unscheduled events (stuck pipe, lost circulation, water influx, gas influx and H2S) in about 128,000 free-text remarks from daily mud reports; the rule-based model was precise but missed events, with accuracy falling to 65.18% on a larger test set, and a hybrid that used its output to train a weakly supervised deep learning model improved detection by more than 20 percentage points."
log(i, t[k:], T[i][k:], "literature.zhang_2022", "description corrected against the source PDF (author check, 28 October 2026)")
sub(ix("The Volve dataset itself"), "Tunkiel et al. (2020)", "Tunkiel et al. (2021)", None, "year corrected (J Pet Sci Eng 196: 108069, 2021; author check, 28 October 2026)")
app(ix("The common limitation across the published DDR work"), "The audit in this paper measures the same weakness of rule-based classification, the events it misses, directly on the unclassified residual.", "literature.zhang_2022", "added with the corrected Zhang et al. description")

# 10 hole sizes in running text: 17 1/2 in. becomes 17½ in. (quotations are not touched: they carry inch marks, not 'in.')
GL = {"1/2": "½", "1/4": "¼", "3/4": "¾", "3/8": "⅜", "5/8": "⅝"}
for j in range(len(P)):
    if j in DEL: continue
    tj = cur(j); nj = re.sub(r"(\d+) (\d/\d) in\.", lambda m: m.group(1) + GL[m.group(2)] + " in.", tj)
    if nj != tj: T[j] = nj; log(j, "17 1/2 in. style", "17½ in. style", None, "final review: hole sizes written with the fraction character in running text")

# the author's own edits in Word (kept when the draft is rebuilt): the author line, and the affiliation note deleted
sub(1, "T. Appalla, Independent Researcher", "Tejaswy Appalla", None, "the author's edit in Word (2026-10-28): author line")
delp(3, "the author deleted the affiliation note in Word (2026-10-28)")

# style revision pass over the original paragraphs
for j in range(len(P)):
    if j in DEL: continue
    tj = cur(j); nj = restyle(tj)
    if nj != tj: T[j] = nj
log("Whole text", "draft wording", "sentence-level style revision of the body text (Sections 1 to 8)", None, "style revision of 2026-11-02: no number, table, figure, reference or quotation changed; the Abstract, the opening paragraph of the Conclusions, the AI disclosure and the availability statement untouched (yellow notes mark the first two); old and new text in manuscript/style_diff.md")


# =========================================================================== external review round (5 November 2026): original paragraphs, after the style revision
# New Section references use the old numbering of Section 5 (5.3 to 5.7); a pass at the end shifts them by one when the new Section 5.3 (phase label agreement) is inserted.
# '@AGR@' stands for the number of the new subsection (replaced at the end).
RV = "external review (5 November 2026)"
agr = val("agreement.per_phase"); cs = val("agreement.causes_proposed")
_ord = sorted(agr.items(), key=lambda kv: (-kv[1][0], kv[0]))
_ph = ", ".join(f"{k} {v[0]}" for k, v in _ord)

# title
sub(0, "A Complete Operational History of the Equinor Volve Dataset", "An Auditable Reconstruction of the Equinor Volve Dataset", None, RV + ": title")

# abstract
sub(ix("Daily Drilling Reports (DDRs) are the most complete operational record"), "and no such timeline has been published for an openly available field dataset.", "and, to the author's knowledge, no such timeline has been published for an openly available field dataset.", None, RV + ": novelty claim qualified")
iab = ix("A deterministic, priority-ordered, rule-based classifier assigns")
setp(iab, "A deterministic, priority-ordered, rule-based classifier assigns each DDR's 24-hour narrative to one of 13 phases. It assigns a phase to 1,303 DDRs, a coverage of 74.1%. A stratified audit of 50 records, drawn from the 383 unclassified DDRs that carry a genuine narrative, found 26 (52%) describing construction operations the classifier missed: drilling progress reported without a hole size, non-standard abbreviations, and operations such as fishing and fracturing for which no pattern exists. "
     f"The author, a petroleum engineer, labelled the main operation of 52 classified reports (four per phase) as an engineer would read them, which is not the classifier's priority rule. The frequency-weighted agreement with the classifier was {val('agreement.weighted_pct')}% (30 of 52 reports unweighted), which is agreement with engineering interpretation and not accuracy against a reference standard. The audit identified substantial disagreement between the classifier and the author's single-report labels. Post-hoc inspection suggested incidental keyword matches, differences in phase interpretation and possible dependence on campaign context. The effect of adding neighbouring reports was not tested.",
     "abstract paragraph on the classifier and the audit", "classifier.classified_pct;audit.construction_calls;agreement.agree;agreement.n;agreement.weighted_pct", RV + ": 74.1% is coverage; the estimated recoverable coverage leaves the abstract; the weighted agreement leads and the framing follows the third review")
sub(ix("Of 24 wellbores with a defensible NOD counterpart"), "Of 24 wellbores with a defensible NOD counterpart, 22 agree exactly on total depth. 15/9-F-15 differs by 15 m, and 15/9-19 S differs by 227 m because the DDR archive does not cover that wellbore's final drilling.",
    "Of 21 wellbores matched to NOD by name, 19 agree on total depth within 0.5 m, and the 3 technical sidetracks matched by depth agree as well. 15/9-F-15 differs by 15 m, for a cause that remains unresolved, and 15/9-19 S differs by 227 m because the DDR archive does not cover that wellbore's final drilling.",
    "td.name_matched;td.name_matched_within_0p5;td.depth_matched", RV + ": depth validation split into name-matched and depth-matched wellbores; F-15 unresolved")
sub(ix("Sidetrack kick-off depths were recovered for all 15 sidetracks by one rule; where NOD"), "an open depth-time-phase dataset of 1,421 records, with per-wellbore durations to total depth, published with the classifier code. It supports days-versus-depth benchmarking and records-based screening",
    "an open depth-time-phase dataset of 1,421 records (the DDRs with a valid measured depth, of 1,759 in all), with per-wellbore elapsed days and reports to total depth, published with the classifier code. It supports the comparison of wellbores by reports against depth and records-based screening",
    "timeline.rows;data.n_ddrs", RV + ": 1,421 against 1,759 explained; no benchmarking claim")
sub(ix("Sidetrack kick-off depths were recovered for all 15 sidetracks by one rule; where NOD"), "recovered for all 15 sidetracks by one rule;", "recovered for all 15 sidetracks by a fixed order of preference;", None, RV)

# 3.3 and Section 3.5
sub(ix("The classifier assigns the sum24Hr narrative of each DDR"), "On Volve platform wells the 12¼ in. hole is usually the section above the reservoir.",
    "On Volve platform wells the 12¼ in. hole usually ends above the reservoir (Hugin Formation); in 15/9-F-4, for example, the 12¼ in. section ended at 2,770 m MD and pressure samples were taken in the Hugin Formation at 3,417.5 m MD, in the 8½ in. section.",
    "hugin.f4_pressure_point_md_m;hugin.f4_12_25in_section_td_m", RV + ": reservoir position stated with the F-4 evidence; no Hugin top depth is given because the archive holds none")
sub(ix("In the 15/9-19 series the DDR narratives describe"), "became stuck at 3,272 m. The string was backed off and cut, a sidetrack plug was set, and new hole was kicked off from 2,911 m as 15/9-19 BT2,",
    "became stuck at 3,272 m. A backoff attempt released the string too high, the string was cut at 3,164 m, a sidetrack plug was set between 2,983 and 2,835 m, and new hole was drilled from 2,911 m as 15/9-19 BT2,",
    "b19.string_cut_m;b19.sidetrack_plug_m", RV + ": 15/9-19 B events checked against the narratives")
sub(ix("In the 15/9-19 series the DDR narratives describe"), "Well 15/9-19 S followed the same sequence, with stuck pipe at approximately 2,741 m, a backed-off and cut string, sidetrack language in the narrative (\"MU BHA FOR SIDE TRACK\") and new hole from approximately 1,536 m as 15/9-19 ST2.",
    "Well 15/9-19 S followed a similar sequence. The hole packed off at 2,732 m and attempts to work the pipe free were made at 2,741 m, a cutter was detonated at 2,658 m, the pipe was cut at 2,516 m, three cement plugs were set (the last from 1,543 to 1,430 m), and the narrative uses sidetrack language (\"MU BHA FOR SIDE TRACK\"). Cement was then drilled out to 1,486 m, and new hole was drilled as 15/9-19 ST2 from a depth between 1,486 m and 1,536 m, the measured depth of the first ST2 report.",
    "s19.packed_off_m;s19.stuck_pipe_depth_m;s19.cutter_detonated_m;s19.pipe_cut_m;kickoff.19ST2.cement_plugs_m;kickoff.19ST2.range_m", RV + ": the narratives support a cut string and no backoff for 15/9-19 S; 2,741 m kept as the depth of the attempts to free the pipe")

# 5.1 coverage
sub(ix("5.1 Classification Rate"), "Classification Rate", "Coverage", None, RV + ": 74.1% is coverage")
i51 = ix("The classifier assigns a phase to 1,303 of the 1,759 DDRs")
sub(i51, "assigns a phase to 1,303 of the 1,759 DDRs (74.1%) and leaves 456 unclassified (25.9%) (Table 4).", "assigns a phase to 1,303 of the 1,759 DDRs, a coverage of 74.1%, and leaves 456 unclassified (25.9%) (Table 4). Coverage is the share of reports that match a pattern. It does not measure whether the phase is correct (Section @AGR@).", None, RV + ": coverage defined")
sub(i51, "classified phases on the depth-versus-time curves of four representative wellbores.", "classified phases on the depth-versus-time curves of representative wellbores in four panels. The phase colours are single-report labels.", None, RV)
app(ix("Percentages are rounded independently"), "Phases are single-report labels assigned by the classifier (Section @AGR@).", None, RV + ": Table 4 caveat")

# 5.2 estimated recoverable coverage (design-based)
sub(ix("5.2 Stratified Audit and Attainable Classification Rate"), "Attainable Classification Rate", "Estimated Recoverable Coverage", None, RV)
setp(ix("A complete pattern set would classify"), "Of the 50 sampled reports, 26 (52%) were labelled construction and 24 (48%) non-construction. The construction group (39 reports) split 23 construction to 16 non-construction, and the production group (11 reports) split 3 to 8. Of the 26 construction reports that the classifier missed, 9 reported genuine drilling without a hole size, 10 described other operations with no corresponding pattern, such as hydraulic fracturing or fishing, and 7 used non-standard terms, such as \"CMT\" for cement. "
     "Weighting the two groups by their share of the 383-report frame gives 51.8% construction (design-based 95% interval 39.1 to 64.5%, normal approximation, with only 11 records in the production group), which corresponds to about 198 reports. The estimated recoverable coverage is therefore 85.3% (95% interval 82.6 to 88.1%): the share of the 1,759 reports that would carry a phase if the patterns also caught the construction content of the unclassified reports. It estimates how much construction content the patterns leave unassigned and does not guarantee that a recovered report would receive the correct phase. The arithmetic, with the Wilson interval for comparison, is in Appendix B.",
     "Section 5.2, first paragraph", "audit.design_proportion_pct;audit.design_ci_low_pct;audit.design_ci_high_pct;audit.recoverable_residual_ddrs;audit.recoverable_coverage_pct;audit.recoverable_coverage_ci_low_pct;audit.recoverable_coverage_ci_high_pct;audit.construction_calls;audit.miss_reason.NO_HOLE_SIZE;audit.miss_reason.OTHER_MISS;audit.miss_reason.NONSTANDARD_TERMINOLOGY",
     RV + ": design-based estimate (stratum-weighted, finite-population correction) replaces the Wilson figures, which move to Appendix B; named estimated recoverable coverage")
sub(ix("No text method can classify the 73 DDRs"), "They are excluded from the attainable rate, and even a perfect pattern set", "They are excluded from the recoverable coverage, and even a perfect pattern set", None, RV)

# 5.4 total depth (old numbering)
i54 = ix("Of the 26 wellbores, 24 have a defensible NOD counterpart")
setp(i54, "Of the 26 wellbores, 21 are matched to NOD by name, 3 technical sidetracks are matched by depth and 2 parent legs are unmatched (below). Of the 21 name-matched wellbores, 19 agree on total depth within 0.5 m. 15/9-F-15 differs by 15 m (0.4%) and 15/9-19 S by 227 m. The reports state the total depth of 15/9-F-15 as 4,090 m (\"Drilled 8 1/2\" hole from 3889m to 4090m (TD).\"), NOD records 4,105 m, and the cause of the 15 m difference is unresolved. Among the 19 F-series wellbores matched by literal name, 18 (94.7%) agree within 0.5 m, and 15/9-F-15 is again the exception. The 3 depth-matched sidetracks agree by construction of the match. 15/9-F-7 and 15/9-F-9 share a total depth of 1,085 m, and NOD independently records 1,085 m for each, which rules out a duplication in the extraction.",
     "Section 5.4, second paragraph", "td.name_matched;td.name_matched_within_0p5;td.depth_matched;td.diff.15/9-F-15;td.diff.15/9-19 S;td.f15_nod_td_m;td.f15_reports_state_td_m;td.f15_reports_mentioning_4105;td.fseries_name_matched_n;td.fseries_name_matched_exact;td.fseries_name_matched_exact_pct",
     RV + ": 19 of 21 name-matched wellbores within 0.5 m, depth-matched sidetracks reported separately; F-15 cause unresolved, evidence from the reports")
sub(ix("Exact: difference of 0.5 m or less."), "Exact: difference of 0.5 m or less.", "Within 0.5 m: difference of 0.5 m or less. The three technical sidetracks (15/9-19 BT2, 19 ST2 and F-11 T2) have no NOD record of their own and are matched to the NOD record whose total depth agrees. Agreement within 0.5 m is therefore the matching condition for them.", "td.depth_matched;td.depth_matched_within_0p5", RV)

# 5.5 spud: F-11 final category stated once
sub(ix("Spud date was compared across three sources"), "Applied mechanically, the rules reproduce 25 of the 26 assignments. The exception is 15/9-F-11, which was assigned Exact by inspection and is unresolved under the rule. NOD records a pre-drill campaign (6 to 17 April 2012) that is absent from the DDR archive, and the archive's 2013 reports describe a fresh spud from seabed, including the 30-inch conductor. The records do not show how the two campaigns relate.",
    "The final category of 15/9-F-11 is Unresolved: NOD records a pre-drill campaign (6 to 17 April 2012) that is absent from the DDR archive, and the archive's 2013 reports describe a fresh spud from seabed, including the 30-inch conductor. The records do not show how the two campaigns relate. The earlier call of Exact, made by inspection, was not retained.",
    "spud.unresolved;spud.F-11.predrill_period", RV + ": F-11 final category stated once; the earlier inspection call is not retained")

# 5.6 kick-off: fixed order of preference, precedence and confidence
i56 = ix("Kick-off depth was recovered from the DDRs")
sub(i56, "One rule was applied to all sidetracks, and the depth was read from the last report of the parent and the first report of the sidetrack. The kick-off is the depth at which the narrative first reports new formation or departure from the parent hole. Where the narrative states none, it is the depth at which the kick-off or window was started, and for casing exits by a milled window it is the top of the window. Where the narrative is empty, it is the measured depth at the parent-to-child transition.",
    "The depth was read from the last report of the parent and the first report of the sidetrack, in a fixed order of preference: (1) a depth stated for the point where the narrative first reports new formation or departure from the parent hole, or where the kick-off started; (2) for a casing exit by a milled window, the top of the window; (3) where the narrative names the kick-off event but gives no depth, the measured depth of the same report; (4) where the narrative is empty, the measured depth at the parent-to-child transition. The first step with evidence is used. A milled window gives a window interval and no single departure depth. Step 2 therefore applies to it. Confidence follows from the evidence: HIGH where the narrative states the depth together with the departure or the window top, MEDIUM where it states the start of the kick-off or the event without a departure depth, and LOW where the evidence is an interval or the narrative is empty. These definitions describe the grades assigned in Table 7.",
    "kickoff.order_step_counts", RV + ": the one rule replaced by an explicit order of preference with precedence and confidence definitions")
sub(ix("NOD's wlbKickOffPoint agrees with the recovered depth"), "15/9-19 ST2, which rests on the measured depth alone,", "15/9-19 ST2, which lies between 1,486 and 1,536 m and rests on the measured depth at the transition,", "kickoff.19ST2.range_m", RV)

# 5.7 duration (old numbering) and 6.1
sub(ix("The 1,421-row depth-time-phase dataset can be queried directly."), "allow wellbores drilled from the same platform to be compared, phase durations can be extracted for offset-well planning, and the classified phases locate casing, cementing and P&A operations in time and depth for each wellbore.",
    "allow wellbores drilled from the same platform to be compared, and the classified phases locate casing, cementing and P&A operations in time and depth for each wellbore as single-report labels. Phase counts and durations should not be used directly for offset-well planning, because the phases are single-report labels that agree with the author's labels for 61.0% of reports weighted by phase size (Section @AGR@) and the archive has gaps.", "agreement.weighted_pct", RV + ": offset-well planning claim removed")
sub(ix("The 1,421-row depth-time-phase dataset can be queried directly."), "a user can bound how much of any phase-based statistic is missing. At the attainable-rate estimate, roughly 199 DDRs of construction content remain unassigned, mostly drilling progress reported without a hole size. Table 8 offers elapsed days, reports and metres per report-day to total depth for each wellbore as a first benchmark, and the gap flag marks wellbores whose elapsed time cannot be read as drilling time.",
    "a user can bound how much of any phase-based statistic is missing: roughly 198 reports with construction content remain unassigned, mostly drilling progress reported without a hole size. Table 8 gives elapsed days, reports and metres per report to total depth for each wellbore. Metres per report is not a rate of penetration. It includes non-drilling days, gaps between reports and, for 15/9-F-1, two campaigns. The gap flag marks wellbores whose elapsed time cannot be read as drilling time.",
    "audit.recoverable_residual_ddrs", RV + ": m per report, with the statement that it is not a rate of penetration; recoverable coverage")

# 6.3 shared-hole principle
sub(ix("Assessments of depleted fields for CO2 storage"), "Wellbores that share a physical interval, such as the four wellbores of the 15/9-F-1 family, which share the hole above 1,364 m MD, are not independent penetrations above their kick-off depths.",
    "A sidetrack shares the hole of its parent above its kick-off depth. The wellbores of one family are therefore not independent penetrations above that depth. The 15/9-F-1 family shares the hole above 1,364 m MD, the five wellbores of the 15/9-F-15 family share it above about 1,380 m MD, and 15/9-19 S, ST2 and A share it above the kick-off of each sidetrack (15/9-19 ST2 leaves 15/9-19 S between 1,486 and 1,536 m, and 15/9-19 A leaves it, according to NOD, at 2,178 m).",
    "kickoff.F-1_family_shared_hole_above_m;kickoff.19ST2.range_m", RV + ": shared-hole principle stated generally with three examples")

# 6.4 comma splice
sub(ix("The audit protocol, the placeholder checks"), "of one operator over the life of one field, Applying it elsewhere", "of one operator over the life of one field. Applying it elsewhere", None, RV + ": comma splice")

# 7 Limitations
sub(ix("The classifier assigns a single primary phase to each DDR."), "The Cementing count therefore underrepresents the days on which cementing occurred alongside another operation.",
    "The Cementing count therefore underrepresents the days on which cementing occurred alongside another operation. Each report is also classified on its own, without the neighbouring reports or the state of the campaign. The author's labels of 52 classified reports, made on the same terms, agreed with the classifier for 61.0% of reports weighted by phase size (30 of 52; Section @AGR@). This is agreement with the author's interpretation and not accuracy against a reference standard, and the effect of adding neighbouring reports was not tested. The causes of the disagreements were assigned by the AI tool from the narratives.", "agreement.agree;agreement.n;agreement.weighted_pct", RV + ": limitation on single-report classification")
sub(ix("The audit labelled construction content only."), "which makes the attainable rate conservative with respect to those phases.", "which makes the recoverable coverage conservative with respect to those phases. The coverage counts construction content found in unclassified reports and does not guarantee that a recovered report would receive the correct phase.", None, RV)
sub(ix("The audit labelled construction content only."), "The interval of 82.5 to 88.3% reflects the modest sample size.", "The design-based interval of 82.6 to 88.1% reflects the modest sample size and rests on a normal approximation, which is optimistic with 11 records in one group.", "audit.recoverable_coverage_ci_low_pct;audit.recoverable_coverage_ci_high_pct", RV)
i100 = ix("Kick-off depths were read from the narratives by one rule")
sub(i100, "Kick-off depths were read from the narratives by one rule, and two of them rest on weaker evidence, 15/9-19 ST2 on the measured depth alone and", "Kick-off depths were read from the narratives in a fixed order of preference (Section 5.6), and two of them rest on weaker evidence, 15/9-19 ST2 on the measured depth at the transition (between 1,486 and 1,536 m) and", "kickoff.19ST2.range_m", RV)
sub(i100, "The four wellbores of the 15/9-F-1 family (F-1, F-1 A, F-1 B and F-1 C) share the hole above 1,364 m MD, and F-1, F-1 A and F-1 B share it above approximately 2,617 to 2,620 m MD. Any formation-level analysis that treats them as independent must account for this. Metres per report-day are rates per reported day, and gaps between reports in the archive affect the elapsed time to total depth (the gap flag in Table 8).",
    "A sidetrack shares the hole of its parent above its kick-off depth. The four wellbores of the 15/9-F-1 family share the hole above 1,364 m MD (F-1, F-1 A and F-1 B share it above approximately 2,617 to 2,620 m MD), the five wellbores of the 15/9-F-15 family share it above about 1,380 m MD, and the same holds for 15/9-19 S, ST2 and A. Any formation-level analysis that treats these wellbores as independent must account for this. Metres per report are not rates of penetration, and gaps between reports in the archive affect the elapsed time to total depth (the gap flag in Table 8).",
    "kickoff.F-1_family_shared_hole_above_m;kickoff.F-1_F-1A_F-1B_shared_hole_above_m", RV + ": shared-hole principle stated generally; m per report")
sub(ix("No isolated ablation was run"), "on the classification rate.", "on coverage.", None, RV)
sub(ix("The analysis starts from the raw XML"), "The near-exact agreement with NOD on total depth (22 of 24) indicates", "The agreement with NOD on total depth (19 of 21 name-matched wellbores within 0.5 m) indicates", "td.name_matched;td.name_matched_within_0p5", RV)

# 8 Conclusions (the opening paragraph is left for the author)
sub(ix("A deterministic, 13-phase rule-based classifier assigns"), "assigns 1,303 of 1,759 Volve WITSML DDRs (74.1%) to a construction phase,", "assigns a phase to 1,303 of 1,759 Volve WITSML DDRs, a coverage of 74.1%,", None, RV + ": coverage")
sub(ix("A stratified audit finds that 52%"), "which gives an estimated attainable classification rate of 85.4% (95% CI 82.5 to 88.3%).", "which gives an estimated recoverable coverage of 85.3% (95% CI 82.6 to 88.1%).", "audit.recoverable_coverage_pct;audit.recoverable_coverage_ci_low_pct;audit.recoverable_coverage_ci_high_pct", RV + ": design-based estimate")
setp(ix("Reconstructed total depth agrees exactly"), "Reconstructed total depth agrees with the NOD register within 0.5 m for 19 of 21 wellbores matched by name, and for the 3 technical sidetracks matched by depth. The two differences are 227 m on 15/9-19 S, where the archive holds no reports for the final drilling, and 15 m on 15/9-F-15, whose cause is unresolved.",
     "Conclusions bullet on total depth", "td.name_matched;td.name_matched_within_0p5;td.depth_matched;td.diff.15/9-F-15;td.diff.15/9-19 S", RV + ": F-15 is no longer called explained")
sub(ix("Future work should enlarge the audit sample"), "close the identified pattern gaps,", "close the identified pattern gaps, classify each report together with its neighbouring reports and the state of the campaign,", None, RV)


# third review
sub(ix("Daily Drilling Reports (DDRs) are the primary operational record"), "total depth and spud date are validated for every wellbore against an independent national register, the NOD FactPages (NOD 2026a).", "total depth and spud date are compared for every wellbore with an independent national register, the NOD FactPages (NOD 2026a), and the unmatched and unresolved cases are reported.", None, RV + ": no claim of validation for every wellbore")
sub(ix("The Volve dataset is an established benchmark"), "Commercial analyses of Volve DDRs for subsets of wells have been described informally. ", "", None, RV + ": uncited sentence deleted")
sub(ix("Published DDR work relies on proprietary or synthetic data"), "using a documented sampling frame and a Wilson-score interval (Wilson 1927), and with validation of total depth and spud date against a national register for the complete wellbore population.", "an agreement audit of classified reports against the author's labels, and a comparison of total depth and spud date with a national register for the complete wellbore population.", None, RV + ": methods summary includes the agreement audit; the Wilson interval is no longer foregrounded")
sub(ix("Sidetrack kick-off depths were recovered for all 15 sidetracks by a fixed order"), "and the method transfers to other WITSML 1.4-series drillReport archives.", "and the method may be applied to other WITSML 1.4-series archives after adaptation and validation.", None, RV + ": transfer claim qualified")
sub(ix("The audit protocol, the placeholder checks"), "transfer directly to WITSML 1.4-series drillReport archives (tested here on 1.4.0.0).", "can be applied to WITSML 1.4-series drillReport archives after adaptation and validation (tested here on 1.4.0.0).", None, RV)
sub(ix("The timeline dataset holds 1,421 rows"), "Fig. 3 plots report number against measured depth for all 26 wellbores.", "Fig. 3 plots report number against measured depth for the reports of all 26 wellbores, pooled.", None, RV)
sub(ix("The 1,421-row depth-time-phase dataset can be queried directly."), "Because the classifier is deterministic and the audit quantifies its residual, a user can bound how much of any phase-based statistic is missing: roughly 198 reports with construction content remain unassigned, mostly drilling progress reported without a hole size.",
    "The residual audit estimates the aggregate amount of construction content left unassigned. It does not establish phase-specific completeness or bound errors in phase counts and durations. The estimate is roughly 198 reports, mostly drilling progress reported without a hole size.", "audit.recoverable_residual_ddrs", RV + ": the 'bound' claim replaced")
# figure captions
sub(ix("Fig. 2: Depth versus time for four representative wellbores"), "Depth versus time for four representative wellbores, coloured by classified phase.", "Depth versus time for six wellbores in four panels (15/9-19 S; 15/9-F-14; 15/9-F-1, F-1 B and F-1 C; 15/9-F-7), coloured by the phase assigned to each report. The phases are single-report labels.", None, RV + ": caption matches the panels")
sub(ix("Fig. 3: Report number"), "versus measured depth for all 26 wellbores, coloured by hole section (other phases and unclassified reports in grey).", "versus measured depth, with the reports of all 26 wellbores pooled (individual wellbore curves are not identified) and coloured by selected assigned phase categories (grey: other assigned phases and unclassified reports). The counts in the legend are reports with a valid depth only, and the phases are single-report labels.", None, RV)
sub(ix("Fig. 4: Reconstructed WITSML maximum MD"), "are not plotted.", "are not plotted. Circles mark the 21 wellbores matched by name and diamonds the 3 technical sidetracks matched by depth.", "td.name_matched;td.depth_matched", RV + ": distinct markers for depth-matched sidetracks")
sub(ix("Fig. 5: Spud date offset"), "is excluded because NOD does not register it separately.", "is excluded because NOD does not register it separately. A dot coloured by category marks the end of every bar and makes zero-day offsets visible, and 15/9-F-11 is shown as Unresolved.", None, RV + ": zero-length bars visible; F-11 Unresolved")


# flush the edited paragraphs
for i, text in T.items():
    write_par(P[i], text)
for i in sorted(DEL):
    P[i]._p.getparent().remove(P[i]._p)
P[IDX_A[0]]._p.addprevious(P[IDX_E[0]]._p)          # reference order: the 2025 guidelines come before the 2026 FactPages pages

# figures replace the placeholders
for i, fn, w in [(134, "figure1_depth_vs_time.png", 6.5), (136, "figure2_days_vs_depth.png", 6.0), (138, "figure3_td_validation.png", 5.2), (140, "figure4_spud_offset.png", 5.4)]:
    RESOLVED.append(dict(location=f"Figures (paragraph {i})", note=P[i].text))
    for r in P[i].runs: P[i]._p.remove(r._r)
    P[i].add_run().add_picture(f"outputs/figures/{fn}", width=Inches(w))
    sp = P[i]._p.pPr.find(qn("w:spacing"))
    if sp is not None and sp.get(qn("w:line")) is not None: del sp.attrib[qn("w:line")]       # a multiple line height clips inline images
    P[i].paragraph_format.keep_with_next = True                                               # the image stays with its caption below it
    P[i + 1].paragraph_format.keep_with_next = None                                           # the caption does not hold on to the next figure

# =========================================================================== tables
t1 = doc.tables[0]
def set_cell(cell, text):
    par = cell.paragraphs[0]
    if par.runs:
        par.runs[0].text = text; return
    tbl = cell._tc.getparent().getparent()                    # empty cell: copy the run format of a non-empty cell in the same column
    col = cell._tc.getparent().findall("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tc").index(cell._tc)
    for tr in tbl.findall("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tr"):
        tcs = tr.findall("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tc")
        for r in tcs[col].iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}r"):
            nr = copy.deepcopy(r); par._p.append(nr); Run(nr, par).text = text; return
    par.add_run(text)
set_cell(t1.rows[3].cells[1], "99.94%"); set_cell(t1.rows[3].cells[2], "1,758"); set_cell(t1.rows[3].cells[3], "1 record missing (1980 sentinel)")
log("Table 1, row rig", "100.0% / 1,759", "99.94% / 1,758, note: 1 record missing (1980 sentinel)", "table1.rig_npd_name_alias.count;table1.rig_npd_name_alias.pct", "the v2 value counted the constant column 'name' (decision 17)")
set_cell(t1.rows[4].cells[0], "forecast24hr (genuine)"); set_cell(t1.rows[4].cells[1], "94.14%"); set_cell(t1.rows[4].cells[2], "1,656"); set_cell(t1.rows[4].cells[3], '103 literal "None" strings excluded')
log("Table 1, row forecast24hr", "100.0% / 1,759", '94.14% / 1,656, note: 103 literal "None" strings excluded', "table1.forecast24hr_genuine.count;table1.forecast24hr_genuine.pct", "treated like sum24Hr (decision 18, deliberate change)")
for row in doc.tables[1].rows:
    c0 = row.cells[0].text.strip()
    if c0 in ("Reservoir drilling", "Surface casing"): set_cell(row.cells[0], {"Reservoir drilling": "12¼ in. and smaller hole", "Surface casing": "Surface hole and casing"}[c0])
log("Table 2", "Reservoir drilling; Surface casing", "12¼ in. and smaller hole; Surface hole and casing", None, "label-only change (TJ review): counts unchanged (256 and 66), classifier patterns frozen")
t4 = doc.tables[3]
set_cell(t4.rows[1].cells[1], "6"); set_cell(t4.rows[1].cells[2], "15/9-19 A, F-10, F-15 A, F-15 B, F-15 C, F-15 D")
set_cell(t4.rows[2].cells[2], "Administrative spud precedes operational start by days to weeks (15/9-19 B, F-1 A, F-1 B, F-1 C, F-5, F-9 A, F-11 B, F-14)")
set_cell(t4.rows[6].cells[1], "5"); set_cell(t4.rows[6].cells[2], "15/9-19 BT2, 19 S, 19 ST2, F-9, F-11 (for F-11 see the text)")
log("Table 4, row Unresolved", "4, 15/9-19 series", "5: 15/9-19 BT2, 19 S, 19 ST2, F-9, F-11", "spud.unresolved", "correction of the v2 detail cell (19 B is a definitional offset, F-9 is unresolved) and 15/9-F-11 moves from Exact to Unresolved under the NOD pre-drill-else-main rule (decision 47)")
log("Table 4, row Exact", "7", "6: 15/9-19 A, F-10, F-15 A, F-15 B, F-15 C, F-15 D", "spud.exact", "15/9-F-11 moves to Unresolved under the NOD pre-drill-else-main rule (decision 47)")
log("Table 4, row Definitional offset", "(no wellbores listed)", "wellbores listed", "spud.definitional_offset", "detail added from the spud table")

W = nsdecls("w"); BORD = '<w:tcBorders><w:top w:val="single" w:color="808080" w:sz="4"/><w:left w:val="single" w:color="808080" w:sz="4"/><w:bottom w:val="single" w:color="808080" w:sz="4"/><w:right w:val="single" w:color="808080" w:sz="4"/></w:tcBorders>'
MAR = '<w:tcMar><w:top w:type="dxa" w:w="40"/><w:left w:type="dxa" w:w="80"/><w:bottom w:type="dxa" w:w="40"/><w:right w:type="dxa" w:w="80"/></w:tcMar>'


TBLPR0 = copy.deepcopy(doc.tables[2]._tbl.tblPr)      # table properties of the existing tables, kept before new tables are inserted


def make_table(header, rows, widths, hl=frozenset(), right=frozenset()):
    def cell(text, w, head=False, h=False, rt=False):
        shd = '<w:shd w:fill="E7E6E6" w:color="auto" w:val="clear"/>' if head else ""
        b = "<w:b/><w:bCs/>" if head else ""
        hh = '<w:highlight w:val="yellow"/>' if h else ""
        return (f'<w:tc><w:tcPr><w:tcW w:type="dxa" w:w="{w}"/>{BORD}{shd}{MAR}</w:tcPr><w:p><w:pPr><w:jc w:val="{"right" if rt else "left"}"/></w:pPr><w:r><w:rPr>'
                f'<w:rFonts w:ascii="Times New Roman" w:cs="Times New Roman" w:eastAsia="Times New Roman" w:hAnsi="Times New Roman"/>{b}<w:sz w:val="18"/><w:szCs w:val="18"/>{hh}</w:rPr>'
                f'<w:t xml:space="preserve">{escape(text)}</w:t></w:r></w:p></w:tc>')
    xml = "".join('<w:tr><w:trPr><w:cantSplit/><w:tblHeader/></w:trPr>' + "".join(cell(h, w, head=True) for h, w in zip(header, widths)) + "</w:tr>" for _ in [0])
    for ri, row in enumerate(rows):
        xml += '<w:tr><w:trPr><w:cantSplit/></w:trPr>' + "".join(cell(c, widths[ci], h=(ri, ci) in hl, rt=ci in right) for ci, c in enumerate(row)) + "</w:tr>"
    grid = "".join('<w:gridCol w:w="%d"/>' % w for w in widths)
    tbl = parse_xml(f'<w:tbl {W}><w:tblGrid>{grid}</w:tblGrid>{xml}</w:tbl>')
    tbl.insert(0, copy.deepcopy(TBLPR0))
    return tbl


fm = lambda x, d=0: f"{x:,.{d}f}"
def fdepth(x): return fm(x, 1) if float(x) % 1 else fm(x)
def fdiff(x):
    if x is None or (isinstance(x, float) and pd.isna(x)): return ""
    return "0" if float(x) == 0 else (f"{x:+,.1f}" if float(x) % 1 else f"{x:+,.0f}")

body_t, head_t, cap_t, note_t, bullet_t = P[48], P[53], P[55], P[56], P[98]


# ---- Abbreviations (final review) and reference entries (verified against the source PDFs, 28 October 2026)
def fp(prefix):
    hits = [p for p in P if p.text.startswith(prefix)]; assert len(hits) == 1, (prefix, len(hits)); return hits[0]


ABB = [("BHA", "bottom-hole assembly", "heading"), ("DP", "drill pipe", "DDR"), ("EMW", "equivalent mud weight", "DP"), ("EZSV", "drillable cement retainer or bridge plug (Halliburton trade name)", "EMW"), ("FIT", "formation integrity test", "EZSV"), ("LCM", "lost circulation material", "FIT"), ("LWD", "logging while drilling", "LCM"),
       ("MWD", "measurement while drilling", "MD"), ("SG", "specific gravity", "RKB"),
       ("VSP", "vertical seismic profile", "TVD"), ("WOW", "waiting on weather", "WITSML")]
anchor_of = {"heading": [p for p in P if p.style.name.startswith("Heading") and p.text.strip() == "Abbreviations"][0]}
tmpl = fp("BOP  =")
for abbr, exp, after in ABB:
    anc = anchor_of[after] if after in anchor_of else fp(after + "  =")
    anchor_of[abbr] = new_par_after(anc._p, tmpl, f"{abbr}  =  {exp}", renum=False)
log("Abbreviations", "BOP, CI, DDR, MD, NOD, P&A, RKB, TD, TVD, WITSML", "adds BHA, DP, EMW, EZSV, FIT, LCM, LWD, MWD, SG, VSP, WOW (MT and POOH, no longer used in the text, are not listed)", None, "final review: abbreviations used in the quotations and in Table 2")


def ref_run_sub(prefix, old, new):
    p = fp(prefix)
    for r in p.runs:
        if old in r.text: r.text = r.text.replace(old, new); return
    raise AssertionError((prefix, old))


write_par(fp("Hoffimann, J."), "Hoffimann, J., Mao, Y., Wesley, A., and Taylor, A. 2018. Sequence Mining and Pattern Analysis in Drilling Reports with Deep Natural Language Processing. Presented at the SPE Annual Technical Conference and Exhibition, Dallas, Texas, USA, 24–26 September. SPE-191505-MS. https://doi.org/10.2118/191505-MS.")
ref_run_sub("Tunkiel, A.T.", "2020.", "2021.")
ref_run_sub("Priyadarshy, S.", "Houston, Texas, USA. OTC-27918-MS", "Houston, Texas, USA, 1–4 May. OTC-27918-MS")
ref_run_sub("Sidahmed, M.", "The Woodlands, Texas, USA. SPE-173429-MS", "The Woodlands, Texas, USA, 3–5 March. SPE-173429-MS")
log("References", "Hoffimann 2017 (arXiv); Tunkiel 2020; Priyadarshy and Sidahmed without conference days", "Hoffimann 2018 (SPE-191505-MS); Tunkiel 2021; conference days added (1-4 May; 3-5 March)", None, "all references verified against the source PDFs by the author on 28 October 2026 (decision 73)")

# ---- Table 4 rebuilt with a Rule column (the category rules moved out of the text of Section 5.5)
RULE = {"Exact agreement": "R4: WITSML date within 1 day of the NOD date, and the first report or free-text spud follows it by at most 1 day.",
        "Definitional offset": "R6: WITSML date within 8 days of the NOD date, and the free-text operational start follows it by 2 to 20 days. R5a: a parent leg whose NOD record is claimed by a technical sidetrack and that has no free-text spud date of its own (15/9-19 B).",
        "WITSML data-entry error": "R2: WITSML date differs from the first report or free-text spud by more than 30 days, while the NOD date agrees with them within 3 days.",
        "NOD date marks later campaign": "R3: WITSML date within 7 days of the first report, but more than 1 year from the NOD date.",
        "Inherited parent spud date": "R1: the sidetrack carries the same spud date as its parent.",
        "Unresolved": "R5b: a technical sidetrack whose NOD record is its parent leg's (15/9-19 BT2 with 19 B, 19 ST2 with 19 SR). R7: any wellbore that no other rule fits."}
rows4 = []
for r in t4.rows[1:]:
    c = [x.text for x in r.cells]
    if c[0] == "Wellbore-identity conflation": c[0] = "NOD date marks later campaign"
    rows4.append([c[0], c[1], RULE.get(c[0], ""), c[2]])
tbl4 = make_table(["Outcome", "Wellbores", "Rule", "Detail"], rows4, [1700, 800, 3900, 2960])
t4._tbl.addnext(tbl4); t4._tbl.getparent().remove(t4._tbl)
note4 = new_par_after(tbl4, note_t, "Rules are applied in the order R1 (inherited), R5a (parent leg) and R5b (technical sidetrack), R2 (error), R3 (later campaign), R4 (exact), R6 (definitional offset), R7 (unresolved). Unresolved includes 15/9-19 S, F-9 and F-11 (R7).")
log("Table 4", "three columns (Outcome, Wellbores, Detail); category named Wellbore-identity conflation", "four columns with a Rule column; category named NOD date marks later campaign", "spud.rule_thresholds_days;spud.table4",
    "TJ review: rules moved from the text of Section 5.5 into the table; the technical-sidetrack rule now names the wellbores it applies to (15/9-19 BT2, 19 ST2 and the parent leg 19 B)")

# ---- Table 1 (example report, Section 3.1) and Table 2 (phases, Section 3.3)
ex = val("example.ddr"); DISP = {"Reservoir drilling": "12¼ in. and smaller hole", "Surface casing": "Surface hole and casing"}
_full = " ".join(pd.read_parquet("data/interim/ddr.parquet", columns=["filename", "sum24Hr"]).set_index("filename").loc[ex["filename"], "sum24Hr"].split())
assert len(_full.split()) == ex["sum24Hr_words_total"] and all(f in _full for f in ex["sum24Hr_fragments"])          # the full summary, checked against the registry
sumtxt = "“" + _full + "”"; fctxt = ex["forecast24hr"]
rows1 = [["wellbore", ex["wellbore"], "the wellbore the report belongs to"],
         ["date_report", ex["date_report"], "the day the report covers"],
         ["md (m)", fm(ex["md_m"]), "measured depth reached, along the hole"],
         ["dTimSpud", ex["dTimSpud"], "spud date in the report header, the same in every report of the wellbore"],
         ["md_kickoff", "absent", "kick-off depth field: empty in this report, as in most reports (Table 3)"],
         ["md_csg_last (m)", fdepth(ex["md_csg_last_m"]), "depth of the last casing shoe"],
         ["forecast24hr", fctxt, "the plan for the next 24 hours"],
         ["sum24Hr", sumtxt, "free-text summary of the past 24 hours: the text the classifier reads"],
         ["Phase assigned", f"{DISP.get(ex['phase'], ex['phase'])} (priority {ex['phase_priority']})", "the classifier's result: the 12¼ in. hole matches the pattern of that phase"]]
tbl1 = make_table(["Field", "Value", "Meaning"], rows1, [1700, 4300, 3360])
a1 = new_par_after(P[21]._p, body_t, "Table 1 shows one report as stored in the archive: the structured fields the pipeline uses and the free-text summary that the classifier reads, quoted in full. Fig. 1 shows the same report as a page of the original PDF version of the Daily Drilling Report.", renum=False)
c1 = new_par_after(a1._p, cap_t, "Table 1: Example DDR as stored in the archive", renum=False)
c1._p.addnext(tbl1)
n1 = new_par_after(tbl1, note_t, f"Source: Equinor Volve dataset (Equinor 2018), file {ex['filename']}. The summary of {ex['sum24Hr_words_total']} words and the forecast are quoted in full. The kick-off field is empty in this report, as in most reports (Table 3).", renum=False)
_img = P[134]._p                                         # the first figure paragraph (image) and its caption are the templates
fig1 = copy.deepcopy(_img); n1._p.addnext(fig1)
fig1p = Paragraph(fig1, P[134]._parent)
for _r in list(fig1p.runs): fig1.remove(_r._r)
fig1p.add_run().add_picture("outputs/figures/example_ddr_crop.png", width=Inches(6.5))
fig1p.paragraph_format.keep_with_next = True
fcap = new_par_after(fig1, P[135], "Fig. 1: Page of the original Daily Drilling Report for " + ex["wellbore"] + ", 23 November 2013 (Equinor Volve dataset, PDF version). Table 1 shows the same report as stored in the WITSML archive.", renum=False)
fcap.paragraph_format.keep_with_next = None
log("Section 3.1", "(no example report)", "Table 1: one real report (15/9-F-15 D, 2013-11-23), summary quoted in full, with the fields explained; Fig. 1 shows its original PDF page", "example.ddr;table1.md_kickoff_m.pct", "TJ review: abridged example DDR")

GLYPH = {"1/2": "\u00bd", "1/4": "\u00bc", "3/4": "\u00be", "3/8": "\u215c", "5/8": "\u215d"}
READ = {"tagged sea bt": "tagged sea bottom"}           # the pattern matches the abbreviation seen in the report ("Tagged sea btm"); shown in full
rows2 = [[str(r["priority"]), DISP.get(r["phase"], r["phase"]).replace(" / ", "/"), ", ".join(re.sub(r"(\d+) (\d/\d)", lambda m: m.group(1) + GLYPH[m.group(2)], x) for x in r["sizes_in"]) or "none", ", ".join(READ.get(x, x) for x in r["words"]) or "(size only)"] for r in val("classifier.phase_table")]
tbl2 = make_table(["Priority", "Phase", "Hole and casing sizes (in.)", "Example trigger words"], rows2, [800, 2400, 2100, 4060])
a2 = new_par_after(P[25]._p, body_t, "Table 2 lists the 13 phases in priority order with representative triggers taken from the pattern table of the repository (outputs/stage4_priority_rules.csv). Sizes are matched in the spellings found in the reports, for example 17 1/2 or 17.5; words are matched without regard to case; each phase has further patterns that are not shown.", renum=False)
c2 = new_par_after(a2._p, cap_t, "Table 2: Phases in priority order with representative triggers", renum=False)
c2._p.addnext(tbl2)
n2 = new_par_after(tbl2, note_t, "A report is assigned to the highest-priority phase with a match; a report that matches no pattern is Unclassified. The triggers shown are simplified: the actual expressions impose context and distance limits (for example, a size must lie close to the word hole or casing), and all of them are listed in src/classifier_v3.py. Both casing sizes in the table occur in the reports: 14 in. in %d DDRs (%s) and 10¾ in. in %d DDRs (%d wellbores), %d of which also mention a tie-back or the combined 9⅝ x 10¾ in. string." % (val("casing.14in_ddrs"), ", ".join(val("casing.14in_wellbores")), val("casing.10_3_4in_ddrs"), len(val("casing.10_3_4in_wellbores")), val("casing.10_3_4in_tieback_or_combination_ddrs")), renum=False)
log("Section 3.3", "(no phase table)", "Table 2: 13 phases, priority, sizes and trigger words from the frozen pattern table", "classifier.phase_table", "TJ review: generated from outputs/stage4_priority_rules.csv")

# ---- Table 5 (kick-off) and the text around it
kt = pd.DataFrame(val("kickoff.table"))
MET = {"depth in text": "depth in text", "event in text, depth from md": "event in text, depth from md", "depth sequence (narrative empty)": "depth sequence (narrative empty)"}
rows5 = []
for ri, r in enumerate(kt.itertuples()):
    parent = "15/9-19 S (per NOD)" if str(r.parent).startswith("none") else r.parent
    rows5.append([r.sidetrack, parent, fdepth(r.ddr_kickoff_depth_m), MET[r.method], "" if pd.isna(r.nod_wlbKickOffPoint_m) else fdepth(r.nod_wlbKickOffPoint_m), fdiff(r.nod_minus_ddr_m), r.confidence])
for _r in rows5:
    if _r[0] == "15/9-19 ST2": _r[2] = "%s to %s" % tuple(fdepth(x) for x in val("kickoff.19ST2.range_m"))
    if _r[0] == "15/9-F-11 B": _r[3] = "end of stated interval (%s to %s m)" % tuple(fm(x) for x in val("kickoff.F-11 B.interval_m"))
tbl5 = make_table(["Sidetrack", "Parent", "Kick-off depth (m MD)", "Method", "NOD kick-off (m)", "NOD minus DDR (m)", "Confidence"], rows5, [1350, 1500, 1050, 2260, 900, 1100, 1200], right={2, 4, 5})
A = new_par_after(P[67]._p, body_t, f"All 15 sidetracks by designation (15/9-19 A, 19 B, 19 BT2 and 19 ST2, F-1 A, F-1 B and F-1 C, F-9 A, F-11 A, F-11 B and F-11 T2, and F-15 A to F-15 D) yielded a kick-off depth (Table 5). For 11 the depth is written in the narrative; for 3 (15/9-F-1 A, F-1 B and F-15 D) the narrative names the kick-off event but not the depth, which is taken from the measured depth of the same report; for 1 (15/9-19 ST2) both reports at the transition are empty and the depth is the measured depth there, the weakest case. For 15/9-F-1 C the last F-1 B report of 22 February 2014 reads \"Commenced time drilling to1364 m. 50% formation obtained at 1364 m.\", and the first F-1 C report drills 17 1/2 in. hole from that depth, so the kick-off is 1,364 m. The depth of 3,059 m that the narratives report on 13 March 2014 is the start of the 8 1/2 in. section, after casing was run, not the kick-off. 15/9-19 A is a sidetrack whose kick-off is the top of a milled window at 2,178 m (window milled from 2,178 to 2,183 m), a depth that NOD also records.")
cap5 = new_par_after(A._p, cap_t, "Table 5: Sidetrack kick-off depths, 15 sidetracks")
cap5._p.addnext(tbl5)
note5 = new_par_after(tbl5, note_t, f"Depths are m MD. NOD minus DDR is NOD's wlbKickOffPoint minus the recovered depth; blank where NOD has no value. NOD lists 15/9-19 S as the parent; the re-entry from which 15/9-19 A was drilled (NOD 15/9-19 SR2, 1997) has no WITSML reports, so the kick-off is read from the 15/9-19 A reports. Parent follows the designation chain, each sidetrack being listed under the wellbore designated before it. " + ", ".join(val("kickoff.shallower_than_parent_kickoff")[:-1]).replace("15/9-", "") + " and " + val("kickoff.shallower_than_parent_kickoff")[-1].replace("15/9-", "") + " kick off at a depth shallower than the kick-off of that parent and leave the hole shared with earlier wellbores of their family (Section 6.3). For 15/9-19 ST2 the range runs from the depth to which cement was drilled out to the measured depth at the transition, and Table 8 uses 1,536 m.")
log("Section 5.6", "(no kick-off table)", "Table 5: sidetrack, parent, kick-off depth, method, NOD value, difference, confidence", "kickoff.table;kickoff.method_counts;kickoff.nod_comparison", "new table from the kick-off table (author-approved, no highlighting)")
log("Section 5.6", "Twelve free-text and two depth-sequence recoveries; 15th sidetrack unidentified; the F-1 C example 'Drilled and oriented 8 1/2\" from 3059 m'",
    "11 depth in text, 3 event in text with depth from md, 1 depth sequence; 15 recovered; F-1 C 1,364 m; 3,059 m is the 8 1/2 in. section start; 19 A (2,178 m) is the 15th sidetrack",
    "kickoff.method_counts;kickoff.proposed_depth.15/9-F-1 C;kickoff.proposed_depth.15/9-19 A", "decisions 27, 32, 40; open item 2 resolved")

# ---- 5.7 Duration
dt = pd.DataFrame(val("duration.table")); dl = pd.DataFrame(val("duration.drilled_length_and_rate_sidetracks")).set_index("wellbore"); do = pd.DataFrame(val("duration.drilled_length_and_rate_originals")).set_index("wellbore")
rows6 = []
for ri, r in enumerate(dt.itertuples()):
    src = dl if r.wellbore in dl.index else do
    ind = r.wellbore in val("duration.indicative_only")
    rows6.append([r.wellbore + (" (indicative)" if ind else ""), r.first_ddr, fdepth(r.td_md_m), r.td_date, fm(r.elapsed_days_to_td), fm(r.ddrs_to_td), "yes" if r.gap_flag else "", fdepth(src.loc[r.wellbore, "drilled_length_m"]), fm(src.loc[r.wellbore, "m_per_report_day"], 1)])
tbl6 = make_table(["Wellbore", "First report", "TD (m)", "TD reached", "Elapsed days to TD", "Reports to TD", "Gap flag", "Drilled length (m)", "m per report"], rows6, [1650, 1050, 800, 1050, 900, 800, 650, 1230, 1230], right={2, 4, 5, 7, 8})
h57 = new_par_after(P[69]._p, head_t, "5.7 Duration to Total Depth")
a57 = new_par_after(h57._p, body_t, f"Table 6 gives, for each wellbore, the first report (the 1980 date sentinel excluded), the date total depth was first reached (the maximum valid depth of Table 3), the elapsed calendar days from the first report to that date, the number of reports in that span (inclusive), the drilled length (total depth minus the kick-off depth of Table 5 for the 15 sidetracks, total depth for the other 11) and metres per report-day (drilled length divided by the number of reports). Elapsed days and reports agree where a wellbore was reported daily and differ where the archive has gaps; wellbores whose elapsed days exceed twice their reports are flagged. Seven of the 26 are flagged (15/9-19 S, F-1, F-4, F-5, F-9, F-14 and F-15). F-1 reaches its total depth of 3,632 m on 17 August 2013, 2,085 days after its first report on 2 December 2007, in 31 reports, four of them from 2007. 15/9-19 B (3,272 m) and 15/9-F-11 (347 m) end at the depth of an abandoned parent leg or stub (Section 5.4), so their durations are indicative only. Drilled lengths and rates for sidetracks depend on the kick-off depths of Section 5.6; rates are per reported day, not per elapsed day, and for F-1 they mix two campaigns. Per-phase report counts for each wellbore and well family are published with the duration table.")
cap6 = new_par_after(a57._p, cap_t, "Table 6: Duration to total depth (TD) and drilled length, 26 wellbores")
cap6._p.addnext(tbl6)
note6 = new_par_after(tbl6, note_t, "Gap flag: elapsed days to TD exceed twice the reports to TD. Drilled length is total depth minus the Table 5 kick-off depth for sidetracks and total depth for original wellbores; for the original wellbores this is measured depth from the rig datum and includes the water depth. (indicative): TD is the depth of an abandoned parent leg or stub. For 15/9-19 ST2 the kick-off used is 1,536 m, the deeper end of the range of 1,486 to 1,536 m (Table 7), so its drilled length is a minimum.")
log("Section 5.7 (new)", "(no duration results)", "new subsection and Table 6: first report, TD, TD date, elapsed days, reports to TD, gap flag, drilled length, m per report-day", "duration.table;duration.drilled_length_and_rate_sidetracks;duration.drilled_length_and_rate_originals;duration.n_gap_flagged",
    "TJ answers to the Stage 9 questions")

# new conclusion bullet after the spud bullet (paragraph 98)
cb = new_par_after(P[98]._p, bullet_t, f"Sidetrack kick-off depths were recovered for all 15 sidetracks by one rule; for 15/9-F-1 C the kick-off is 1,364 m, not the 3,059 m start of the 8 1/2 in. section, and the four wellbores of the 15/9-F-1 family share their hole above that depth.")
log("Conclusions (new bullet)", "(none)", "kick-off result for all 15 sidetracks, F-1 C 1,364 m", "kickoff.proposed_depth.15/9-F-1 C;kickoff.F-1_family_shared_hole_above_m", "new result")

# draft banner after the affiliation note

# ---- Conclusions: summary paragraph before the numbered list (TJ review round 3, text exactly as supplied)
IH = [i for i in range(len(P)) if P[i].style.name.startswith("Heading") and P[i].text.strip() == "8 Conclusions"]; assert len(IH) == 1
concl = new_par_after(P[IH[0]]._p, body_t, "This paper shows three things. First, a field's daily drilling reports can be turned into a construction history that is checked against the regulator's register, with explicit checks on selected reconstructed properties and audits of classification coverage and label agreement, using a method anyone can inspect and rerun. Second, the structured fields of a WITSML archive cannot be trusted on their own: spud dates, kick-off depths and placeholder values all needed the narrative or the national register to correct them, and a kick-off read naively from the narrative can pick up the start of a hole section instead of the point where the sidetrack leaves its parent (3,059 m against 1,364 m for 15/9-F-1 C). Third, the national register alone does not give a complete inventory of what was drilled: abandoned parent legs, shared upper hole and missing campaigns appear only when the reports are reconstructed. For anyone screening old wells for CO2 storage or decommissioning, the practical lesson is to reconstruct the well history from the reports before relying on either source alone.", renum=False)
# yellow notes: the Abstract and the opening paragraph of the Conclusions are left for the author to rewrite (style revision, 2026-11-02)
_ab = [p for p in P if p.style.name.startswith("Heading") and p.text.strip() == "Abstract"][0]
new_par_after(_ab._p, body_t, "⟦[TJ: rewrite in your own words]⟧", renum=False)
new_par_after(concl._p, body_t, "⟦[TJ: rewrite in your own words]⟧", renum=False)
log("Conclusions", "(no summary paragraph)", "summary paragraph before the numbered list", "kickoff.proposed_depth.15/9-F-1 C", "TJ review round 3: text as supplied by the author")

# ---- Appendix B: audit arithmetic
hB = new_par_after(P[143]._p, P[142], "Appendix B: Audit Arithmetic", renum=False)
pB1 = new_par_after(hB._p, P[143], "This appendix gives the arithmetic behind the attainable classification rate of Section 5.2.", renum=False)
pB2 = new_par_after(pB1._p, P[143], POST(OLD50), renum=False)
log("Appendix B (new)", "(arithmetic was in Section 5.2)", "full arithmetic and stratum-weighted check", "audit.sample_proportion;audit.wilson_low;audit.wilson_high;audit.scale_frame_over_total;audit.residual_miss;audit.observed_rate;audit.stratum_weighted_rate_pct", "TJ review: moved from Section 5.2")

# =========================================================================== external review round (5 November 2026): code-built paragraphs, tables, numbering
def pedit(par, old, new, rid, reason):
    t = par.text; assert t.count(old) == 1, (old[:70], t.count(old))
    write_par(par, t.replace(old, new)); LOG.append(dict(location="Section 5.6/5.7 and table notes", old=old[:160], new=new, id=rid or "", reason=RV + ": " + reason))


# Section 5.6, the text around Table 7
pedit(A, "The depth is written in the narrative for 11 of them.", "The depth is written in the narrative for 11 of them (step 1 for 9 and step 2 for 2).", "kickoff.order_step_counts", "steps of the order of preference")
pedit(A, "and the depth is taken from the measured depth of the same report. For 15/9-19 ST2 both reports at the transition are empty. The depth is the measured depth there, which makes it the weakest case.",
      "and the depth is taken from the measured depth of the same report (step 3). For 15/9-19 ST2 both reports at the transition are empty (step 4). The kick-off lies between 1,486 m, the depth to which cement was drilled out in the 15/9-19 S report of 18 December 1992 (the day before the transition), and 1,536 m, the measured depth at the transition. Three cement plugs had been set above it, the last from 1,543 to 1,430 m, and the confidence is LOW.",
      "kickoff.19ST2.range_m;kickoff.19ST2.cement_plugs_m;kickoff.19ST2.lower_bound_report", "15/9-19 ST2 reported as a range; the report that gives the lower bound is named")
pedit(A, "reads \"Commenced time drilling to1364 m.", "reads \"Commenced time drilling to1364 [sic] m.", None, "[sic] for the missing space in the report")
# Section 5.7
pedit(a57, "the drilled length and the metres per report-day.", "the drilled length and the metres per report.", None, "m per report")
pedit(a57, "Elapsed days and reports agree where a wellbore was reported daily and differ where the archive has gaps.", "With inclusive counting, the number of reports equals the elapsed days plus 1 for a wellbore reported daily, and falls short of that where the archive has gaps.", None, "inclusive counting")
pedit(a57, "and the rate divides it by the number of reports.", "and metres per report divides it by the number of reports.", None, "m per report")
pedit(a57, "The rates are per reported day, and for F-1 they mix two campaigns.", "Metres per report is not a rate of penetration. It includes non-drilling days, gaps between reports and, for F-1, two campaigns.", None, "not a rate of penetration")
pedit(a57, "Drilled lengths and rates for sidetracks depend", "Drilled lengths and metres per report for sidetracks depend", None, "m per report")
pedit(cb, "by one rule.", "by a fixed order of preference.", None, "order of preference")
pedit(note6, "so its drilled length is a minimum.", f"so its drilled length is a minimum ({fm(val('duration.19ST2_drilled_length_range_m')[0])} m, or {fm(val('duration.19ST2_drilled_length_range_m')[1])} m at 1,486 m, which gives {val('duration.19ST2_m_per_report_range')[0]} to {val('duration.19ST2_m_per_report_range')[1]} m per report).", "duration.19ST2_drilled_length_range_m;duration.19ST2_m_per_report_range", "19 ST2 range")
pedit(note6, "from the rig datum", "from the rotary kelly bushing (RKB)", None, "datum named")

# Table 5 (total depth): outcome words and the depth-matched sidetracks
t5 = [t for t in doc.tables if t.rows[0].cells[0].text.startswith("Wellbore (WITSML)")]; assert len(t5) == 1
for row in t5[0].rows[1:]:
    c = [x.text for x in row.cells]
    if c[5].startswith("Technical sidetrack, matched to"):
        set_cell(row.cells[4], "Within 0.5 m (by depth)"); set_cell(row.cells[5], c[5].replace("matched to", "matched by depth to"))
    elif c[4] == "Exact": set_cell(row.cells[4], "Within 0.5 m")
    elif c[4] == "Close": set_cell(row.cells[4], "More than 0.5 m")
    if c[0] == "15/9-F-15": set_cell(row.cells[5], "TD stated as 4,090 m in the reports; cause of the 15 m difference unresolved")
log("Table 5", "Outcome Exact / Close", "Within 0.5 m (by depth for the three technical sidetracks) / More than 0.5 m", "td.name_matched;td.depth_matched", RV + ": depth-matched sidetracks reported separately; F-15 note")

# Appendix B: design-based arithmetic first, the Wilson figures as a comparison
da = val("audit.design_arithmetic"); wl = val("audit.sample_proportion")
pedit(pB1, "attainable classification rate", "estimated recoverable coverage", None, "Appendix B")
write_par(pB2, f"The two groups were sampled in near-proportion to their size (39 of 296, {val('audit.design_sampling_fraction_construction_pct')}%, and 11 of 87, {val('audit.design_sampling_fraction_production_pct')}%). The sample proportions of construction reports are 23/39 = {da['p_construction']:.4f} and 3/11 = {da['p_production']:.4f}, and the group weights are 296/383 = {da['W_construction']:.4f} and 87/383 = {da['W_production']:.4f}. "
          f"The stratified proportion is therefore {da['W_construction']:.4f} × {da['p_construction']:.4f} + {da['W_production']:.4f} × {da['p_production']:.4f} = {da['p_stratified']:.4f}. Its variance is the sum over the two groups of W² (1 − f) p (1 − p) / (n − 1), where f is the sampling fraction. The sum is {da['variance']:.4f}, the standard error is {da['se']:.4f}, and the 95% interval is {da['p_stratified']:.4f} ± 1.96 × {da['se']:.4f}, or {da['ci_low']:.3f} to {da['ci_high']:.3f} (normal approximation, with only 11 records in the production group). "
          f"The sample comes from the 383 records with a genuine narrative among the 456 unclassified records, and the proportion is scaled by 383/1,759 = {val('audit.scale_frame_over_total'):.4f}. The estimated residual is {da['p_stratified']:.4f} × {val('audit.scale_frame_over_total'):.4f} = {da['residual']:.4f}, or {val('audit.recoverable_residual_pp')} percentage points (approximately {val('audit.recoverable_residual_ddrs')} DDRs). "
          f"Adding the observed coverage (1,303/1,759 = {val('audit.observed_rate'):.4f}) gives an estimated recoverable coverage of {val('audit.recoverable_coverage_pct')}%. Scaling the interval in the same way gives {val('audit.observed_rate'):.4f} + {da['ci_low']:.3f} × {val('audit.scale_frame_over_total'):.4f} = {da['recovery_ci_low']:.3f} and {val('audit.observed_rate'):.4f} + {da['ci_high']:.3f} × {val('audit.scale_frame_over_total'):.4f} = {da['recovery_ci_high']:.3f}, a 95% interval of {val('audit.recoverable_coverage_ci_low_pct')} to {val('audit.recoverable_coverage_ci_high_pct')}%.")
pWil = new_par_after(pB2._p, P[143], f"For comparison, the unstratified sample proportion is 26/50 = {wl:.3f} with a Wilson-score 95% interval (Wilson 1927) of {val('audit.wilson_low'):.3f} to {val('audit.wilson_high'):.3f}. Scaling by {val('audit.scale_frame_over_total'):.4f} gives a residual of {val('audit.residual_miss'):.4f} (approximately {val('audit.residual_miss_ddrs')} DDRs) and an estimated recoverable coverage of {val('audit.attainable_rate_pct')}%, with the interval {val('audit.observed_rate'):.4f} + {val('audit.wilson_low'):.3f} × {val('audit.scale_frame_over_total'):.4f} = {val('audit.observed_rate') + val('audit.wilson_low') * val('audit.scale_frame_over_total'):.3f} and {val('audit.observed_rate'):.4f} + {val('audit.wilson_high'):.3f} × {val('audit.scale_frame_over_total'):.4f} = {val('audit.observed_rate') + val('audit.wilson_high') * val('audit.scale_frame_over_total'):.3f}, or {val('audit.attainable_ci_low_pct')} to {val('audit.attainable_ci_high_pct')}%. The two estimates differ by 0.1 percentage point.", renum=False)
log("Appendix B", "attainable classification rate 85.4% (Wilson) with the stratum-weighted check 85.3%", "design-based estimated recoverable coverage 85.3% (82.6 to 88.1%), Wilson 85.4% (82.5 to 88.3%) as a comparison", "audit.design_arithmetic;audit.recoverable_coverage_pct;audit.attainable_rate_pct", RV)

# abbreviations: drop any that the text no longer uses
_abp = [p for p in doc.paragraphs if re.match(r"^\S+  =  ", p.text)]
_body = " ".join(p.text for p in doc.paragraphs if p not in _abp) + " " + " ".join(c.text for t in doc.tables for r in t.rows for c in r.cells)
for p in _abp:
    ab = p.text.split("  =  ")[0]
    if not re.search(r"(?<![A-Za-z])" + re.escape(ab) + r"(?![A-Za-z])", _body, re.I):
        log("Abbreviations", p.text, "(removed: not used in the text)", None, RV); p._p.getparent().remove(p._p)

# Section numbering: the new Section 5.3 (phase label agreement) moves the old 5.3 to 5.7 up by one
_SECRE = re.compile(r"(Sections? )5\.([3-7])\b"); _HEAD = re.compile(r"^5\.([3-7])(?= )")
def _all_pars(d):
    for p in d.paragraphs: yield p
    for t in d.tables:
        for r in t.rows:
            for c in r.cells:
                for p in c.paragraphs: yield p
_n_ref = _n_head = 0
for p in _all_pars(doc):
    for r in p.runs:
        t0 = r.text; t1 = _SECRE.sub(lambda m: m.group(1) + "5." + str(int(m.group(2)) + 1), t0)
        if p.style.name.startswith("Heading 2"): t1 = _HEAD.sub(lambda m: "5." + str(int(m.group(1)) + 1), t1)
        if t1 != t0: r.text = t1; _n_ref += t0 != t1 and not p.style.name.startswith("Heading"); _n_head += p.style.name.startswith("Heading")
print("section references shifted:", _n_ref, "| headings shifted:", _n_head)
assert _n_head == 5, _n_head
log("Section 5", "5.3 Timeline Dataset to 5.7 Duration to Total Depth", "5.4 to 5.8; the new Section 5.3 is Phase Label Agreement", None, RV + ": new subsection inserted; every reference to Sections 5.3 to 5.7 moves with it")

# the new Section 5.3
_h = [p for p in doc.paragraphs if p.style.name.startswith("Heading 2") and p.text.startswith("5.4 Timeline Dataset")]; assert len(_h) == 1
_prev = _h[0]._p.getprevious()
_cs = val("agreement.causes_proposed"); _CK = {"inc": "incidental keyword", "ctx": "campaign context", "win": "whipstock or window milling under Workover", "sch": "phase-scheme ambiguity", "mix": "mixed day", "unx": "unclear from the text (author to say)"}
assert sum(_cs.values()) == 22 and set(_cs) == set(_CK.values())
_ph_txt = ", ".join(f"{k} {v[0]}" for k, v in sorted(val("agreement.per_phase").items(), key=lambda kv: (-kv[1][0], kv[0])))
_s53 = [("5.3 Phase Label Agreement", head_t),
        ("The classified phases were checked with a second audit. Four reports were drawn at random from each of the 13 phases, 52 of the 1,303 classified reports, with the seed recorded in the repository. The author, a petroleum engineer, labelled the main operation of each day from the report alone, without seeing the assigned phase, as an engineer would read it. That reading is not the classifier's priority rule. The result is therefore agreement with engineering interpretation and not accuracy against a reference standard.", body_t),
        (f"The frequency-weighted agreement is {val('agreement.weighted_pct')}%. It weights the agreement rate of each phase (reports agreeing out of four) by the share of the 1,303 classified reports that the phase holds, the sum over the 13 phases of (N_h / 1,303) × (k_h / 4), where N_h is the number of classified reports in phase h. The raw count is {val('agreement.agree')} of {val('agreement.n')} reports ({round(val('agreement.pct'))}%). The stratified design-based 95% interval of the weighted agreement is {val('agreement.weighted_ci_low_pct')} to {val('agreement.weighted_ci_high_pct')}% (normal approximation, finite-population correction). With four reports per phase, and {val('agreement.phases_zero_variance')} of the 13 phases at 0 of 4 or 4 of 4, the interval is approximate and fragile. For comparison only, the Wilson interval for 30 of 52, which treats the reports as one simple random sample, is {val('agreement.wilson_low_pct')} to {val('agreement.wilson_high_pct')}% (Wilson 1927). Agreement by phase, out of four reports each, was {_ph_txt}. All four sampled Cementing reports and all four Workover reports disagreed.", body_t),
        (f"The audit identified substantial disagreement between the classifier and the author's single-report labels. Post-hoc inspection suggested incidental keyword matches, differences in phase interpretation and possible dependence on campaign context. The effect of adding neighbouring reports was not tested. The AI tool assigned indicative causes to the 22 disagreements from the narratives: {_cs[_CK['inc']]} an incidental keyword, {_cs[_CK['ctx']]} campaign context (for example, pulling tubing during an abandonment campaign, or waiting on weather before retrieving a riser), {_cs[_CK['win']]} whipstock or window milling that the classifier assigns to Workover and the author labelled Intermediate drilling, {_cs[_CK['sch']]} casing runs that the size-based phase names place in Intermediate casing and the author labelled Liner/Casing run, {_cs[_CK['mix']]} a day that mixes waiting and rigging up, and {_cs[_CK['unx']]} unexplained. The author did not assign the causes. Coverage (Section 5.1) counts the reports that carry a phase, and the agreement indicates how far the assigned phase matches the author's reading of a report on its own. Table 4 and the phase colours in Figs. 2 and 3 should be read as single-report labels.", body_t)]
_anc = _prev
for _txt, _tp in _s53:
    _np = new_par_after(_anc, _tp, _txt, renum=False); _anc = _np._p
log("Section 5.3 (new)", "(no phase label agreement)", "single-report blind agreement 30 of 52, Wilson interval, frequency-weighted agreement, agreement by phase, causes of disagreement", "agreement.agree;agreement.n;agreement.pct;agreement.wilson_low_pct;agreement.wilson_high_pct;agreement.weighted_pct;agreement.weighted_ci_low_pct;agreement.weighted_ci_high_pct;agreement.phases_zero_variance;agreement.per_phase;agreement.causes_proposed", RV + ": weighted agreement leads, the raw count follows, a design-based interval is given and Wilson is a comparison; framing agreed in the third review")
# a bullet in the Conclusions
_ib = ix("A stratified audit finds that 52%")
new_par_after(P[_ib]._p, bullet_t, f"The author's labels of 52 classified reports, read one at a time, agreed with the classifier for {val('agreement.weighted_pct')}% of reports weighted by phase size ({val('agreement.agree')} of {val('agreement.n')} unweighted). This is agreement with engineering interpretation and not accuracy against a reference standard. Post-hoc inspection suggested incidental keyword matches, differences in phase interpretation and possible dependence on campaign context, and the effect of neighbouring reports was not tested.", renum=False)
log("Conclusions (new bullet)", "(none)", "single-report agreement", "agreement.agree;agreement.weighted_pct", RV)
for p in _all_pars(doc):
    for r in p.runs:
        if "@AGR@" in r.text: r.text = r.text.replace("@AGR@", "5.3")
assert not any("@AGR@" in p.text for p in _all_pars(doc))
doc.core_properties.title = "Field-Scale Well Construction Timeline Reconstruction from WITSML Daily Drilling Reports: An Auditable Reconstruction of the Equinor Volve Dataset"

assert STYLE_USED == set(range(len(STYLE))), ("style entries not applied", [STYLE[k][1][:50] for k in set(range(len(STYLE))) - STYLE_USED])
_sent = lambda t: re.split(r"(?<=[.!?])\s+(?=[A-Z0-9(‘“\"'])", t.strip())
_md = ["# Style revision: old and new text by section", "", "Sentence by sentence, as built by `src/stage12_manuscript.py` from `src/stage12_style_text.py`. Numbers, quotations, table and figure references are checked by the script (no number or reference is added; "
       "every quotation is kept). Numbers or references that no longer appear in a paragraph are listed under it; they are repeats of arithmetic or of a reference given elsewhere.", ""]
_cur = None
for e in STYLE_LOG:
    if e["section"] != _cur: _cur = e["section"]; _md += [f"## {_cur}", ""]
    o, n = _sent(e["old"]), _sent(e["new"])
    _md += ["| Old | New |", "|---|---|", "| " + "<br><br>".join(f"{k + 1}. " + x.replace("|", "\|") for k, x in enumerate(o)) + " | " + "<br><br>".join(f"{k + 1}. " + x.replace("|", "\|") for k, x in enumerate(n)) + " |", ""]
    if e["removed_numbers"] or e["dropped_refs"]: _md += [f"Not repeated in the new text: numbers {e['removed_numbers']}, references {e['dropped_refs']}.", ""]
open("manuscript/style_diff.md", "w", encoding="utf-8", newline="\n").write("\n".join(_md))
# ---- author-owned blocks: the Abstract and the opening paragraphs of the Conclusions are rewritten by the author in Word. When the author's saved file holds a text
# that differs from the generated one, a rebuild keeps the author's version (the saved file is read before anything is written).
def _blocks(d):
    ps = d.paragraphs
    head = lambda t: [i for i, q in enumerate(ps) if q.style.name.startswith("Heading") and q.text.strip() == t]
    ia, ic = head("Abstract"), head("8 Conclusions")
    if len(ia) != 1 or len(ic) != 1: return None
    a, c = [], []
    i = ia[0] + 1
    while i < len(ps) and not ps[i].style.name.startswith("Heading"): a.append(ps[i]); i += 1
    i = ic[0] + 1
    while i < len(ps) and ps[i].style.name != "List Paragraph" and not ps[i].style.name.startswith("Heading"): c.append(ps[i]); i += 1
    return a, c


_AUTHOR_FILE = os.environ.get("VOLVE_AUTHOR_FILE", "manuscript/paper2_draft.docx")
if os.path.exists(_AUTHOR_FILE):
    try: _ext, _gen = _blocks(docx.Document(_AUTHOR_FILE)), _blocks(doc)
    except Exception as _e: _ext = _gen = None; print("author file not read:", _e)
    if _ext and _gen:
        _t = lambda blk: [q.text.strip() for q in blk if not q.text.strip().startswith("[TJ: rewrite")]
        for _name, _k in (("Abstract", 0), ("opening paragraph of the Conclusions", 1)):
            if _t(_ext[_k]) != _t(_gen[_k]) and _t(_ext[_k]):
                _first = _gen[_k][0]._p
                for _q in _ext[_k]: _first.addprevious(copy.deepcopy(_q._p))
                for _q in _gen[_k]: _q._p.getparent().remove(_q._p)
                log("Author's text", f"generated {_name}", f"{_name} as saved by the author in Word, kept", None, "carried over from the saved draft (the author rewrites these in Word)")
                print("kept the author's", _name)

os.makedirs("manuscript", exist_ok=True)
OUT = os.environ.get("VOLVE_DRAFT_OUT", "manuscript/paper2_draft.docx")      # normally the tracked draft; another path when Word holds the file open
doc.save(OUT)

# =========================================================================== CHANGES.md and the checks
d2 = docx.Document(OUT)
hl_texts = []
for p in d2.paragraphs:
    for r in p.runs:
        if r.font.highlight_color is not None: hl_texts.append((p.text[:60], r.text))
for t in d2.tables:
    for row in t.rows:
        for c in row.cells:
            for p in c.paragraphs:
                for r in p.runs:
                    if r.font.highlight_color is not None: hl_texts.append(("table", r.text))
open_notes = [t for _, t in hl_texts if t.startswith("[TJ:")]
prov = [t for _, t in hl_texts if not t.startswith("[TJ:")]
assert not prov, f"unexpected highlighted text: {prov}"      # no kick-off value carries highlighting after the author sign-off
json.dump(dict(log=LOG, resolved=RESOLVED, open_notes=open_notes, highlighted_non_note_runs=prov), open("data/interim/stage12_log.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("saved", OUT, "|", len(LOG), "log entries |", len(RESOLVED), "resolved notes |", len(open_notes), "open notes |", len(prov), "highlighted values")
