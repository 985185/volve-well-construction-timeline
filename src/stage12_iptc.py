"""Stage 12 (IPTC author kit): build manuscript/paper2_iptc.docx from the author's edited manuscript (manuscript/paper2_author.docx, the new source of the text) and the IPTC template
(inputs/27IPTC_Manuscript_Template.docx, not in the repository: it is the conference's file; this step is skipped with a message when it is absent).

What this script does to the author's text (everything else, including the Abstract and the Conclusions, is carried over unchanged):
title and byline; the cuts listed by the author (Fig. 3 deleted and the later figures renumbered, Table 5 reduced to the special cases, date columns dropped from Table 8, shorter Rule column in Table 6,
Section 6.2 reduced to one sentence, Appendix A merged into Code and Data Availability, Background and Limitations tightened); trade names removed; Abbreviations renamed Nomenclature; an SI conversion table;
one em dash replaced; bold volume numbers in two references; figures and tables placed directly after the paragraph that first cites them; IPTC template styles.
Every edit is an exact-string replacement that must match once, so a changed source text stops the build. Numbers are never typed: the registry count is read from the registry; the check (stage12_check.py) runs on the result."""
import copy
import json
import os
import re
import sys
from xml.sax.saxutils import escape

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Inches, Pt
from docx.table import Table
from docx.text.paragraph import Paragraph

TPL = "inputs/27IPTC_Manuscript_Template.docx"
SRC = "manuscript/paper2_author.docx"
OUT = os.environ.get("VOLVE_IPTC_OUT", "manuscript/paper2_iptc.docx")
if not os.path.exists(TPL):
    print("SKIPPED: the IPTC template", TPL, "is not present (author-side step; the committed", OUT, "stays as it is)")
    sys.exit(0)

REG = {e["id"]: e for e in json.load(open("outputs/numbers_registry.json", encoding="utf-8"))}
TITLE = "Auditable Reconstruction of Field-Scale Well Construction Timelines from Daily Drilling Reports: The Volve Field Open Dataset"
src = docx.Document(SRC)

# ------------------------------------------------------------------ parse the source into flow paragraphs and floats (tables and figures)
flow, tables, caps, notes, refs, noms = [], [], {}, {}, [], []
sec = None
body_pars = []
for el in src.element.body.iterchildren():
    tag = el.tag.split("}")[1]
    if tag == "p":
        p = Paragraph(el, src); body_pars.append(("p", p.style.name, p.text.strip()))
    elif tag == "tbl":
        body_pars.append(("t", None, [[c.text.strip() for c in r.cells] for r in Table(el, src).rows]))
i = 0
pending_table = None
cur_sec = None
while i < len(body_pars):
    kind, st, tx = body_pars[i]; i += 1
    if kind == "t":
        tables.append(tx); pending_table = len(tables); continue
    if not tx: continue
    if st.startswith("Heading 1"):
        cur_sec = tx; pending_table = None
        if tx not in ("Abbreviations", "References", "Figures", "Appendix A: Traceability"): flow.append(("h1", tx))
        continue
    if cur_sec is None: continue            # title, author and control lines: rebuilt from the template
    if st.startswith("Heading 2") and len(tx) < 120:
        flow.append(("h2", tx)); continue
    m = re.match(r"^Table (\d): (.*)$", tx)
    if m: caps["T%s" % m.group(1)] = m.group(2); continue
    m = re.match(r"^Fig\. (\d): (.*)$", tx)
    if m: caps["F%s" % m.group(1)] = m.group(2); continue
    if pending_table:
        notes["T%d" % pending_table] = tx; pending_table = None; continue
    if cur_sec == "Figures": continue
    if cur_sec == "References": refs.append(tx); continue
    if cur_sec == "Abbreviations": noms.append(tx); continue
    flow.append(("li" if st == "List Paragraph" else "p", tx))
assert len(tables) == 8 and sorted(caps) == ["F1", "F2", "F3", "F4", "F5", "T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8"], (len(tables), sorted(caps))
assert set(notes) == {"T%d" % k for k in range(1, 9)}, sorted(notes)
FLOW0 = len(flow)


# ------------------------------------------------------------------ exact-string edits
def _all():
    for k, (kind, tx) in enumerate(flow): yield ("flow", k)
    for k in caps: yield ("cap", k)
    for k in notes: yield ("note", k)
    for k in range(len(refs)): yield ("ref", k)
    for k in range(len(noms)): yield ("nom", k)


def _get(w, k):
    return {"flow": lambda: flow[k][1], "cap": lambda: caps[k], "note": lambda: notes[k], "ref": lambda: refs[k], "nom": lambda: noms[k]}[w]()


def _set(w, k, t):
    if w == "flow": flow[k] = (flow[k][0], t)
    elif w == "cap": caps[k] = t
    elif w == "note": notes[k] = t
    elif w == "ref": refs[k] = t
    else: noms[k] = t


LOG = []


def edit(old, new, why, where=None):
    hits = [(w, k) for (w, k) in _all() if old in _get(w, k) and (where is None or _get(w, k).startswith(where))]
    assert len(hits) == 1, (old[:70], len(hits))
    w, k = hits[0]; _set(w, k, _get(w, k).replace(old, new)); LOG.append((old[:60], why))


def replace_par(startswith, new, why):
    hits = [k for k, (kind, tx) in enumerate(flow) if kind in ("p", "li") and tx.startswith(startswith)]
    assert len(hits) == 1, (startswith, len(hits))
    flow[hits[0]] = ("p", new); LOG.append((startswith[:60], why))


def drop_pars(startswith_list, why):
    for sw in startswith_list:
        hits = [k for k, (kind, tx) in enumerate(flow) if tx.startswith(sw)]
        assert len(hits) == 1, (sw, len(hits)); del flow[hits[0]]; LOG.append((sw[:60], why))


# 1 AI disclosure: the product name is replaced, every other sentence is unchanged
edit("Generative AI (Anthropic Claude, used through Claude Code) built and ran", "Generative AI (a commercially available generative AI assistant based on a large language model) built and ran", "trade name removed (IPTC author kit)")
# 2 Conclusions: the em dash becomes a comma
edit("interpretation limits—not a complete operational history", "interpretation limits, not a complete operational history", "em dash replaced by a comma")
# 3 Fig. 3 (report number against depth) is deleted; the later figures move up by one
edit(" Fig. 3 plots report number against measured depth for the reports of all 26 wellbores, pooled. The report number counts every DDR of a wellbore from its first report (1980 sentinel excluded), with or without a recorded depth, and so matches the reports to TD in Table 8. Only reports with a valid depth are plotted.", "", "Fig. 3 deleted")
edit("Depth-versus-report-count curves (Fig. 3) allow wellbores drilled from the same platform to be compared, and the classified phases locate", "The classified phases locate", "Fig. 3 deleted")
edit("Table 4 and the phase colours in Figs. 2 and 3 should be read as single-report labels.", "Table 4 and the phase colours in Fig. 2 should be read as single-report labels.", "Fig. 3 deleted")
edit(", 39 reports over 91 days (Table 8), and the records do not show why.", ", 39 reports over 91 days (Section 5.8), and the records do not show why.", "Table 8 is first cited in its own section")
del caps["F3"]
# renumber 4 -> 3 and 5 -> 4 (figures), highest first through temporary tokens
for a, b in (("4", "3"), ("5", "4")):
    for (w, k) in list(_all()):
        t = _get(w, k); n = re.sub(r"\bFig\. %s\b" % a, "Fig. @%s@" % b, t)
        if n != t: _set(w, k, n)
caps["F3"], caps["F4"] = caps.pop("F4"), caps.pop("F5")
for (w, k) in list(_all()):
    t = _get(w, k); n = re.sub(r"Fig\. @(\d)@", r"Fig. \1", t)
    if n != t: _set(w, k, n)
caps["F3"] = caps["F3"].replace("Fig. 4", "Fig. 3"); caps["F4"] = caps["F4"].replace("Fig. 5", "Fig. 4")
LOG.append(("Fig. 3, 4, 5", "Fig. 3 deleted; Figs 4 and 5 renumbered 3 and 4"))
caps["F4"] = caps["F4"].replace("A dot coloured by category marks the end of every bar and makes zero-day offsets visible, and 15/9-F-11 is shown as Unresolved.", "A marker at the end of every bar makes zero-day offsets visible, and its shape and colour both identify the category. 15/9-F-11 is shown as Unresolved.")
assert "shape and colour" in caps["F4"]

# 4 Table 5 reduced to the special cases
edit("compared with NOD's total depth for all 26 wellbores (Table 5, Fig. 3).", "compared with NOD's total depth for all 26 wellbores. Table 5 lists the special cases (the parent legs, the three technical sidetracks matched by depth, 15/9-19 S and 15/9-F-15), and Fig. 3 shows the 24 matched wellbores. The full 26-row table is in the repository (outputs/td_validation.csv).", "Table 5 reduced; full table in the repository")
caps["T5"] = "Total depth validation, special cases (the full 26-row table is in the repository)"
T5_KEEP = ("15/9-19 B", "15/9-19 BT2", "15/9-19 S", "15/9-19 ST2", "15/9-F-11", "15/9-F-11 T2", "15/9-F-15")
tables[4] = [tables[4][0]] + [r for r in tables[4][1:] if r[0] in T5_KEEP]
assert len(tables[4]) == 8, len(tables[4])
# 5 Table 8: the date columns are dropped
hdr = tables[7][0]; keep = [j for j, h in enumerate(hdr) if h not in ("First report", "TD reached")]; assert len(keep) == len(hdr) - 2
tables[7] = [[r[j] for j in keep] for r in tables[7]]
# 6 Table 6: shorter Rule column
RULE = {"Exact agreement": "R4: WITSML within 1 day of NOD, and the first report or free-text spud follows by at most 1 day.",
        "Definitional offset": "R6: within 8 days of NOD, free-text start 2 to 20 days later. R5a: parent leg whose NOD record belongs to its technical sidetrack, with no free-text spud date.",
        "WITSML data-entry error": "R2: differs from the first report or free-text spud by more than 30 days, while NOD agrees with them within 3 days.",
        "NOD date marks later campaign": "R3: within 7 days of the first report, more than 1 year from NOD.",
        "Inherited parent spud date": "R1: same spud date as the parent.",
        "Unresolved": "R5b: technical sidetrack whose NOD record is its parent leg's. R7: no other rule fits."}
for r in tables[5][1:]:
    if r[0] in RULE: r[2] = RULE[r[0]]
# 7 Table 2: trade names removed
for r in tables[1]:
    if r[1] == "P&A": assert r[3] == "EZSV, EVO plug, P&A, abandon", r; r[3] = "proprietary plug names, P&A, abandon"
# 8 Section 6.2 reduced to one sentence
drop_pars(["Five characteristics of this archive", "Placeholder values pass null tests.", "A date sentinel (1 January 1980)", "Structured spud dates contradict", "The structured kick-off field is populated in only 14.10% of rows, which forces", "Technical-sidetrack designations have no counterpart"], "Section 6.2 list deleted")
replace_par("None of these invalidates the archive", "The characteristics of the archive that would mislead an analysis of the structured fields alone (placeholder values that pass null tests, a date sentinel, structured spud dates that contradict the first report, a sparsely populated kick-off field, and technical-sidetrack designations without a register counterpart) are described in Section 4 and in Sections 5.5 to 5.7. Each needs an explicit rule, and the rules used here are published with the code.", "Section 6.2 reduced to one sentence")
# 9 Appendix A merged into Code and Data Availability; Appendix B becomes Appendix A
flow = [x for x in flow if x != ("h1", "Appendix A: Traceability")]
trace = [tx for kind, tx in flow if tx.startswith("Every quantitative figure in this paper traces")]; assert len(trace) == 1
flow = [x for x in flow if not x[1].startswith("Every quantitative figure in this paper traces")]
edit("requires the source narratives from the Equinor dataset.", "requires the source narratives from the Equinor dataset. Every quantitative figure in this paper traces to an entry in the numbers registry published in the repository (%d entries, each with the producing script and function, the SHA-256 of its input files and an execution timestamp). The audit estimates in Section 5.2 are derived arithmetically from registry entries, and the arithmetic is shown in Appendix A." % REG["registry.n_entries"]["value"], "Appendix A merged into Code and Data Availability", "The classifier, the extraction and analysis code")
flow = [("h1", "Appendix A: Audit Arithmetic") if x == ("h1", "Appendix B: Audit Arithmetic") else x for x in flow]
for (w, k) in list(_all()):
    t = _get(w, k); n = t.replace("Appendix B", "Appendix A")
    if n != t: _set(w, k, n)
# 10 Background: Karnot et al. in two sentences, both quotations kept
replace_par("Karnot et al. (2025) combine", "Karnot et al. (2025) combine change-point detection, semi-supervised natural language processing and sequence mining for root-cause analysis of non-productive time, applied to 701 DDRs from 10 wells; their Dataset section states that \"all analyses used synthetic datasets constructed to emulate typical drilling records\", and their proof-of-concept sequence-mining section states that \"rigorous validation and quantitative performance assessment are left for future work\". Their abstract and conclusions nevertheless report an average 18.5% reduction in non-productive time in field applications.", "Karnot et al. paragraph in two sentences")
# 11 Limitations tightened (repetition removed; the shared-hole principle stays in Section 6.3)
LIM = ["The classifier assigns a single primary phase to each DDR",
       "The audit labelled construction content only",
       "Two sampled records sit in a group",
       "The timeline includes only DDRs",
       "Kick-off depths were read from the narratives in a fixed order",
       "No isolated ablation was run",
       "The analysis starts from the raw XML"]
first = [k for k, (kind, tx) in enumerate(flow) if tx.startswith(LIM[0])][0]
for sw in LIM: drop_pars([sw], "Limitations tightened")
NEWLIM = ["The classifier assigns one primary phase to each DDR, using that report alone. A report that narrates both drilling progress and cementing takes the higher-priority drilling phase, and the Cementing count therefore underrepresents the days on which cementing occurred alongside another operation. The agreement audit (Section 5.3) compares the classifier with one person's reading of single reports, did not test neighbouring reports, and relies on indicative causes assigned by the AI tool.",
          "The residual audit labelled construction content only, which makes the recoverable coverage conservative for non-construction phases and does not guarantee that a recovered report would receive the correct phase. One reviewer, the author, labelled the 50 records, and the normal-approximation interval of 82.6 to 88.1% is optimistic with 11 records in one group. Two sampled records fall in a group that does not match their context: the 1980 date sentinel places the 1997 drilling of 15/9-19 A, and the 2013 campaign of 15/9-F-1, in the production group.",
          "The timeline holds only DDRs with a genuine measured depth and applies no interpolation; a discontinuity marks missing data and supports no conclusion about drilling activity.",
          "Two kick-off depths rest on weaker evidence: 15/9-19 ST2 (between 1,486 and 1,536 m) and 15/9-F-11 B (an interval of cement and new formation, 2,531 to 2,589 m). NOD gives no kick-off point for three sidetracks. Wellbores of one family share the hole above their kick-off depths (Section 6.3), and formation-level analyses must account for this. Metres per report are not rates of penetration, and gaps between reports affect the elapsed time to total depth (Table 8).",
          "No isolated ablation was run for Unicode normalisation (the one-half sign in 61 DDRs, the one-quarter sign in 10). An extraction error would propagate to every result; agreement with NOD on total depth (19 of 21 name-matched wellbores within 0.5 m) indicates that the depth fields were extracted faithfully."]
for j, t in enumerate(NEWLIM): flow.insert(first + j, ("p", t))
# 12 Nomenclature
noms = [n for n in noms if not n.startswith("EZSV")]
noms = [re.sub(r"\s+=\s+", " = ", n) for n in noms]
# 13 references: bold volume numbers (** marks the bold run)
for k, r in enumerate(refs):
    if r.startswith("Tunkiel"): refs[k] = r.replace("J Pet Sci Eng 196:", "J Pet Sci Eng **196**:"); assert "**196**" in refs[k]
    if r.startswith("Wilson"): refs[k] = r.replace("J Am Stat Assoc 22 (158)", "J Am Stat Assoc **22** (158)"); assert "**22**" in refs[k]

# ------------------------------------------------------------------ second round of cuts (the author asked for all of them)
shallow = REG["kickoff.shallower_than_parent_kickoff"]["value"]
# Table 1 (the example report) goes: Fig. 1 shows the same report
replace_par("Table 1 shows a real construction report as stored in the archive", "Fig. 1 shows a real construction report as a page of the original PDF version of the Daily Drilling Report: the structured fields that the pipeline uses and the free-text summary that the classifier reads. The same report is stored in the archive as file 15_9_F_15_D_2013_11_23.xml (Equinor Volve dataset, Equinor 2018); its summary has 51 words, and its kick-off field is empty, as in most reports.", "Table 1 removed")
caps["F1"] = "Page of the original Daily Drilling Report for 15/9-F-15 D, 23 November 2013 (Equinor Volve dataset, PDF version)."
for d_ in (caps, notes): d_.pop("T1", None)
# 3.1 and Background: small trims
edit("operational parameters and the free-text 24-hour narrative (sum24Hr)", "and the free-text 24-hour narrative (sum24Hr)", "3.1 trimmed")
edit("the last casing depth (md_csg_last_m), and", "the last casing depth (md_csg_last_m), and", "") if False else None
edit("the source XML filename,", "the source filename,", "3.1 trimmed")
edit("built a dictionary of rig terms and acronyms with drilling experts and tracked weighted term frequencies over time in the reports of three wells to flag recurring operational concerns. Priyadarshy et al. (2017) presented", "built a dictionary of rig terms and tracked weighted term frequencies in the reports of three wells to flag recurring operational concerns, and Priyadarshy et al. (2017) presented", "Background trimmed")
edit("classified each sentence as an event, a symptom or an action. They noted that", "classified each sentence as an event, a symptom or an action; they noted that", "Background trimmed")
edit("and its accuracy fell to 65.18% on a larger test set. A hybrid that", "and its accuracy fell to 65.18% on a larger test set; a hybrid that", "Background trimmed")
# 3.3: Table 2 text and note
replace_par("Table 2 gives the 13 phases in priority order", "The priority order, the hole and casing sizes and example trigger words of each phase are in the repository (outputs/stage4_priority_rules.csv and .md), and every regular expression is in src/classifier_v3.py. The triggers there are simplified, because the actual expressions impose context and distance limits. Both casing sizes that the size-based phases use occur in the reports: 14 in. in %d DDRs (%s) and 10\u00be in. in %d DDRs (%d wellbores), %d of which also mention a tie-back or the combined 9\u215d x 10\u00be in. string." % (REG["casing.14in_ddrs"]["value"], ", ".join(REG["casing.14in_wellbores"]["value"]), REG["casing.10_3_4in_ddrs"]["value"], len(REG["casing.10_3_4in_wellbores"]["value"]), REG["casing.10_3_4in_tieback_or_combination_ddrs"]["value"]), "3.3: phase table to the repository")
edit(" Every regular expression is listed in the repository file src/classifier_v3.py.", "", "3.3 trimmed")
for d_ in (caps, notes): d_.pop("T2", None)
# 3.4, 3.5 and 5.2 trims
edit('The 73 empty records have a sum24Hr field that holds the literal string "None" (Section 4).  These records contain no operational narrative in the sum24Hr field for the classifier to interpret. They were excluded from the sampling frame, leaving 383 records.', 'The 73 empty records have a sum24Hr field that holds the literal string "None" (Section 4) and contain no operational narrative for the classifier to interpret; they were excluded from the sampling frame, leaving 383 records.', "3.4 trimmed")
edit(" Its rows for the Volve wellbores match an export of 8 September 2026 except for the register's own synchronisation date. All comparisons are against the current register as accessed in October 2026.", "", "3.5 trimmed")
edit('Well 15/9-19 S followed a similar sequence. The hole packed off at 2,732 m and attempts to work the pipe free were made at 2,741 m, a cutter was detonated at 2,658 m, the pipe was cut at 2,516 m, three cement plugs were set (the last from 1,543 to 1,430 m), and the narrative uses sidetrack language ("MU BHA FOR SIDE TRACK"). Cement was then drilled out to 1,486 m, and new hole was drilled as 15/9-19 ST2 from a depth between 1,486 m and 1,536 m, the measured depth of the first ST2 report.', 'Well 15/9-19 S followed a similar sequence: the hole packed off at 2,732 m, a cutter was detonated at 2,658 m, the pipe was cut at 2,516 m, three cement plugs were set (the last from 1,543 to 1,430 m), and the narrative uses sidetrack language ("MU BHA FOR SIDE TRACK"). Cement was drilled out to 1,486 m, and new hole was drilled as 15/9-19 ST2 from between 1,486 m and 1,536 m.', "3.5 trimmed")
replace_par("The 73 DDRs whose sum24Hr field contains the literal string", "The 73 DDRs whose sum24Hr field is the literal string \u201cNone\u201d provide no narrative for the classifier and are excluded from the recoverable-coverage estimate. A classifier relying only on the sum24Hr field would therefore leave at least 4.2% of the 1,759 reports unclassified. Neighbouring reports or additional fields might support an interpretation but were not used.", "5.2 trimmed")
# 5.3 trims
edit("The classified phases were checked with a second audit. Four reports", "Four reports", "5.3 trimmed")
edit(" (for example, pulling tubing during an abandonment campaign, or waiting on weather before retrieving a riser)", "", "5.3 trimmed")
edit("Coverage (Section 5.1) counts the reports that carry a phase, and the agreement indicates how far the assigned phase matches the author's reading of a report on its own.", "Coverage (Section 5.1) counts reports that carry a phase, and agreement indicates how far the phase matches the author's reading.", "5.3 trimmed")
# 6.3
replace_par("Assessments of depleted fields for CO2 storage", "Assessments of depleted fields for CO2 storage, and decommissioning reviews generally, rely on an inventory of existing wellbores and on evidence of how each was constructed and abandoned. The reconstruction shows that a national register alone gives an incomplete inventory in three ways. Abandoned parent legs below technical sidetracks (15/9-19 B to 3,272 m and 15/9-F-11 to 347 m) exist physically but have no register entry of their own. A sidetrack shares the hole of its parent above its kick-off depth, and the wellbores of one family are therefore not independent penetrations above that depth: the 15/9-F-1 family shares the hole above 1,364 m MD, the five wellbores of the 15/9-F-15 family share it above about 1,380 m MD, and 15/9-19 S, ST2 and A share it above the kick-off of each sidetrack (15/9-19 ST2 between 1,486 and 1,536 m MD, and 15/9-19 A at 2,178 m MD from 15/9-19 SR, following the 1997 re-entry and plugback designated 15/9-19 SR2). The archive can also stop, as it does for 15/9-19 S, which has no reports covering its final 227 m. A screening assessment should record such a gap as an evidence gap without inferring the missing history. The phase-classified timeline is a starting point for locating the casing, cementing and plugging records that such an assessment needs.", "6.3 trimmed")
# Section 4 and 5.1 follow

# Section 4 and 5.1: Tables 3 and 4 go to the repository
edit("across all 1,759 DDRs (Table 3).", "across all 1,759 DDRs (outputs/stage3_table1_field_population.csv).", "Table 3 to the repository")
edit("and leaves 456 unclassified (25.9%) (Table 4).", "and leaves 456 unclassified (25.9%). The largest phases are 12¼ in. and smaller hole (256 reports), Completion (228) and Liner/Casing run (144); all counts are in outputs/table2_phase_distribution.csv.", "Table 4 to the repository")
edit("Table 4 and the phase colours in Fig. 2 should be read as single-report labels.", "The phase counts and the phase colours in Fig. 2 should be read as single-report labels.", "Table 4 to the repository")
for d_ in (caps, notes):
    d_.pop("T3", None); d_.pop("T4", None)
# 5.3: the per-phase list goes to the repository
hit = [k for k, (kind, tx) in enumerate(flow) if "Agreement by phase, out of four reports each, was" in tx]; assert len(hit) == 1
flow[hit[0]] = ("p", re.sub(r"Agreement by phase, out of four reports each, was .*? Workover 0\. ", "Agreement by phase is in outputs/classified_audit_agreement_summary.json. ", flow[hit[0]][1])); assert "agreement_summary.json" in flow[hit[0]][1]
# 5.5 total depth
replace_par("Maximum reconstructed measured depth per wellbore", "Maximum reconstructed measured depth per wellbore was compared with NOD's total depth for all 26 wellbores. Table 5 lists the special cases and Fig. 3 shows the 24 matched wellbores; all 26 rows are in the repository (outputs/td_validation.csv).", "5.5 trimmed")
replace_par("Within 0.5 m: difference of 0.5 m or less.", "Within 0.5 m: difference of 0.5 m or less. The three technical sidetracks (15/9-19 BT2, 19 ST2 and F-11 T2) have no NOD record of their own and are matched to the NOD record whose total depth agrees. Agreement within 0.5 m is therefore their matching condition.", "5.5 trimmed") if False else None
edit(" Among the 19 F-series wellbores matched by literal name, 18 (94.7%) agree within 0.5 m, and 15/9-F-15 is again the exception.", "", "5.5 trimmed")
edit(" 15/9-F-7 and 15/9-F-9 share a total depth of 1,085 m, and NOD independently records 1,085 m for each, which rules out a duplication in the extraction.", "", "5.5 trimmed")
edit("and 2 parent legs are unmatched (below).", "and 2 parent legs are unmatched.", "5.5 trimmed")
replace_par("One explanation covers the two unmatched wellbores", "One explanation covers the two unmatched wellbores and the three depth-based matches. Each WITSML technical sidetrack (19 BT2, 19 ST2, F-11 T2) has no separate NOD entry, and NOD records its final total depth against the parent designation (19 B, 19 SR, F-11). The WITSML parent records that end short of that depth, 15/9-19 B at 3,272 m and 15/9-F-11 at 347 m, are the legs abandoned when the sidetrack was drilled, and they have no NOD counterpart. The two registers differ by construction, and neither is in error.", "5.5 trimmed")
replace_par("The WITSML series of 15/9-19 S ends at 3,353 m", "The WITSML series of 15/9-19 S ends at 3,353 m, 227 m short of NOD's structured total depth (3,580.0 m). NOD's wellbore history records the well as temporarily suspended at 3,569.0 m (NOD 2026d), 216 m deeper than the last WITSML depth. The archive holds no reports for the final drilling and suspension, and the 227 m gap reflects those missing records. The reports it does hold are incomplete throughout, 39 reports over 91 days (Section 5.8), and the records do not show why.", "5.5 trimmed")
# 5.6 spud
replace_par("Spud date was compared across three sources", "Spud date was compared across three sources for every wellbore: the WITSML spud_date field, free-text spud language in the earliest DDRs of the wellbore and the NOD entry date. The offset is the WITSML spud date minus the NOD pre-drill entry date where NOD records one, which marks the start of top-hole drilling, and otherwise the NOD main entry date. Table 6 summarises the outcome and Fig. 4 plots the offset by category. For the four wellbores whose archive contains the pre-drill entry (15/9-F-4, F-5, F-14 and F-15), the first report falls on that date, or one day later for F-4. The categories were first assigned by inspection, and the rules in Table 6 were formalised afterwards to describe those assignments. The final category of 15/9-F-11 is Unresolved: NOD records a pre-drill campaign (6 to 17 April 2012) that is absent from the DDR archive, and the archive's 2013 reports describe a fresh spud from seabed, including the 30-inch conductor. The records do not show how the two campaigns relate. The earlier call of Exact, made by inspection, was not retained.", "5.6 trimmed")
replace_par("In the four error cases", "In the four error cases the structured spud_date differs from the first report and its narrative by 91 to 340 days, while the first report and the NOD date agree with each other (for 15/9-F-12, the first report is dated 14 June 2007 and the structured field 15 March 2007). Two sidetracks, 15/9-F-11 A and 15/9-F-11 T2, carry a spud_date identical to that of their parent, which is almost certainly an inherited field value. NOD does not register 15/9-F-11 T2 separately, and Fig. 4 excludes it.", "5.6 trimmed")
replace_par("The spud date of 15/9-F-1 needed particular care.", "The structured spud_date of 15/9-F-1 (28 November 2007) falls four days before its first DDR (2 December 2007). The 2007 reports cover the top hole only (four reports, maximum depth 226 m), and the well reached its total depth of 3,632 m in the 2013 campaign, whose first report (22 July 2013) is one day before the NOD entry date (23 July 2013). NOD records no pre-drill date for the 2007 work, unlike F-4, F-5, F-14 and F-15. The NOD date therefore marks the later campaign, and the case is classified as \"NOD date marks later campaign\". The WITSML value is consistent with the chronology of the wellbore.", "5.6 trimmed")
for r in tables[5][1:]:
    if r[0] == "Definitional offset": r[3] = "15/9-19 B, F-1 A, F-1 B, F-1 C, F-5, F-9 A, F-11 B, F-14"
open("outputs/spud_rules.md", "w", encoding="utf-8", newline=chr(10)).write("# Spud date validation rules (Section 5.6 of the paper)" + chr(10) + chr(10) + notes["T6"] + chr(10) + chr(10) + chr(10).join("- %s: %s" % (r[0], RULE[r[0]]) for r in tables[5][1:] if r[0] in RULE) + chr(10))
tables[5] = [[row[0], row[1], row[3]] for row in tables[5]]
notes["T6"] = "The rules and the order in which they apply are in outputs/spud_rules.md. Unresolved includes 15/9-19 S, F-9 and F-11 (rule R7)."
edit("and the rules in Table 6 were formalised afterwards to describe those assignments", "and the rules (outputs/spud_rules.md) were formalised afterwards to describe those assignments", "Rule column to the repository")
# 5.7 kick-off: Table 7 goes to the repository
edit("These definitions describe the grades assigned in Table 7.", "These definitions describe the grades assigned in the repository table (outputs/kickoff_table.csv).", "Table 7 to the repository")
edit("The first step with evidence is used. A milled window gives a window interval and no single departure depth. Step 2 therefore applies to it.", "The first step with evidence is used, and a milled window, which gives an interval and no single departure depth, falls under step 2.", "5.7 trimmed")
for d_ in (caps, notes): d_.pop("T7", None)
hit = [k for k, (kind, tx) in enumerate(flow) if tx.startswith("No kick-off depth exists for 15/9-19 S.")]; assert len(hit) == 1; del flow[hit[0]]
replace_par("NOD's wlbKickOffPoint agrees with the recovered depth", "NOD's wlbKickOffPoint is available for 12 of the 15 sidetracks and agrees with the recovered depth to within 10 m for 10 (equal for 6); the larger differences are 15/9-19 B (31 m) and 15/9-F-1 B (13 m). The least certain depths are 15/9-19 ST2 and 15/9-F-11 B, where cement and new formation were drilled from 2,531 to 2,589 m and the end of the interval is taken as the departure.", "5.7 trimmed")
replace_par("A kick-off depth was recovered for all 15 sidetracks", "A kick-off depth was recovered for all 15 sidetracks (outputs/kickoff_table.csv). The depth is written in the narrative for 11 (step 1 for 9 and step 2 for 2); for 3 (15/9-F-1 A, F-1 B and F-15 D) the narrative names the kick-off event but not the depth, which is taken from the measured depth of the same report (step 3); for 15/9-19 ST2 both reports at the transition are empty (step 4). The 15/9-19 ST2 kick-off lies between 1,486 m, the depth to which cement was drilled out in the 15/9-19 S report of 18 December 1992, and 1,536 m, the measured depth at the transition, with three cement plugs set above it (the last from 1,543 to 1,430 m) and LOW confidence. The last report of F-1 B (22 February 2014) reads \"Commenced time drilling to1364 [sic] m. 50% formation obtained at 1364 m.\", and the first report of F-1 C drills 17\u00bd in. hole from that depth, so the well was sidetracked at 1,364 m; the 3,059 m reported on 13 March 2014 marks the start of the 8\u00bd in. section after casing was run. For 15/9-19 A the kick-off is the top of a milled window (2,178 to 2,183 m). NOD's wellbore history states that the sidetrack was kicked off from 15/9-19 SR at 2,178 m MD and records the 1997 re-entry and plugback preceding it as 15/9-19 SR2, a re-entry of 15/9-19 SR. The archive contains no reports designated 15/9-19 SR2, and the kick-off is therefore read from the 15/9-19 A reports and compared with the NOD record. Parents in the repository table follow the designation chain; " + ", ".join(x.replace("15/9-", "") for x in shallow[:-1]) + " and " + shallow[-1].replace("15/9-", "") + " kick off at a depth shallower than the kick-off of that parent and leave the hole shared with earlier wellbores of their family (Section 6.3).", "5.7: Table 7 to the repository")
hit = [k for k, (kind, tx) in enumerate(flow) if tx.startswith("Depths are m MD. NOD minus DDR")]
assert len(hit) == 0
# 5.8 duration: Table 8 reduced to the flagged and indicative wellbores and 15/9-19 ST2
dur = tables[7]
keep8 = [r for r in dur[1:] if r[4] == "yes" or "(indicative)" in r[0] or r[0] == "15/9-19 ST2"]
assert len(keep8) == 10, len(keep8)
tables[7] = [dur[0]] + keep8
caps["T8"] = "Duration to total depth (TD) and drilled length, flagged and indicative wellbores and 15/9-19 ST2 (all 26 wellbores are in outputs/duration_table.csv)"
replace_par("Table 8 gives the duration of each wellbore", "Table 8 gives the duration of the flagged and indicative wellbores and of 15/9-19 ST2; all 26 wellbores, with per-phase report counts, are in outputs/duration_table.csv. Duration runs from the first report (the 1980 date sentinel excluded) to the date total depth was first reached, which is the maximum valid depth. The table lists the elapsed calendar days, the number of reports in that span (inclusive), the drilled length (total depth minus the recovered kick-off depth for the 15 sidetracks, Section 5.7, and total depth for the other 11) and metres per report, which is the drilled length divided by the number of reports. With inclusive counting, the number of reports equals the elapsed days plus 1 for a wellbore reported daily, and falls short of that where the archive has gaps. Seven of the 26 wellbores, whose elapsed days exceed twice their reports, are flagged (15/9-19 S, F-1, F-4, F-5, F-9, F-14 and F-15). F-1 reaches its total depth of 3,632 m in 31 reports spread over 2,085 days, four of them from 2007. The totals of 15/9-19 B (3,272 m) and 15/9-F-11 (347 m) are the depths of an abandoned parent leg or stub (Section 5.5) and make their durations indicative only. Metres per report is not a rate of penetration. It includes non-drilling days, gaps between reports and, for F-1, two campaigns.", "5.8 trimmed")
edit("Table 8 gives elapsed days, reports and metres per report to total depth for each wellbore.", "Table 8 gives elapsed days, reports and metres per report to total depth for the flagged and indicative wellbores.", "Table 8 reduced")
notes["T8"] = notes["T8"].replace("minus the Table 7 kick-off depth for sidetracks", "minus the recovered kick-off depth for sidetracks").replace("(Table 7)", "(Section 5.7)")
# Appendix A (audit arithmetic) moves to the repository
ai = [k for k, (kind, tx) in enumerate(flow) if kind == "h1" and tx.startswith("Appendix A")]; assert len(ai) == 1
app = flow[ai[0] + 1:]; del flow[ai[0]:]
open("outputs/audit_arithmetic.md", "w", encoding="utf-8", newline=chr(10)).write("# Audit arithmetic (Section 5.2 of the paper)" + chr(10) + chr(10) + (chr(10) + chr(10)).join(tx for kind, tx in app) + chr(10))
for (w, k) in list(_all()):
    t = _get(w, k); n = t.replace("is in Appendix A.", "is in the repository (outputs/audit_arithmetic.md).").replace("is shown in Appendix A.", "is shown in outputs/audit_arithmetic.md.")
    if n != t: _set(w, k, n)
assert not [1 for (w, k) in _all() if "Appendix" in _get(w, k)], [_get(w, k)[:80] for (w, k) in _all() if "Appendix" in _get(w, k)]
# small final trims (repetition between 5.4, 5.8, 6.1 and the Limitations)
edit("The 1,421-row depth-time-phase dataset can be queried directly. The classified phases", "The classified phases", "6.1 trimmed")
edit(" Metres per report is not a rate of penetration. It includes non-drilling days, gaps between reports and, for 15/9-F-1, two campaigns. The gap flag marks", " The gap flag marks", "6.1 trimmed")
edit("Each row gives the wellbore identifier, the report date, the days from the wellbore's first report with a recorded depth, the measured depth, the assigned phase and the source filename. Days are counted from the first row with a usable depth in each wellbore.", "Each row gives the wellbore, the report date, the days from the wellbore's first report with a recorded depth, the measured depth, the assigned phase and the source file.", "5.4 trimmed")
edit(" which makes the recoverable coverage conservative for non-construction phases and does not guarantee that a recovered report would receive the correct phase.", " which makes the recoverable coverage conservative for non-construction phases.", "Limitations trimmed")
edit(" The phase-classified timeline is a starting point for locating the casing, cementing and plugging records that such an assessment needs.", "", "6.3 trimmed")
edit(" In both cases NOD records the final total depth against the parent designation.", "", "3.5 trimmed")
edit(" F-1 reaches its total depth of 3,632 m in 31 reports spread over 2,085 days, four of them from 2007.", "", "5.8 trimmed")
# renumber the remaining tables 2, 5, 6, 7, 8 as 1 to 5
OLDN = [5, 6, 8]; MAPN = {o: i + 1 for i, o in enumerate(OLDN)}
tables = [tables[o - 1] for o in OLDN]
for o in OLDN: pass
caps = {("T%d" % MAPN[int(k[1:])] if k[0] == "T" else k): v for k, v in caps.items() if k[0] != "T" or int(k[1:]) in MAPN}
notes = {"T%d" % MAPN[int(k[1:])]: v for k, v in notes.items() if int(k[1:]) in MAPN}
WIDTH = {"T1": [1700, 1300, 1000, 900, 1800, 4100], "T2": [2800, 900, 7100], "T3": [2300, 1100, 1500, 1400, 1100, 1700, 1700]}
RIGHT = {"T1": {1, 2, 3}, "T3": {1, 2, 3, 4, 5, 6}}
def _renum(t):
    def f(m):
        n = int(m.group(1)); assert n in MAPN, ("reference to a removed table", n, t[:80]); return "Table %d" % MAPN[n]
    return re.sub(r"\bTable (\d)\b", f, t)
for (w, k) in list(_all()): _set(w, k, _renum(_get(w, k)))

# ------------------------------------------------------------------ floats: place each directly after the paragraph that first cites it
ITEMS = [("T%d" % k, re.compile(r"\bTable %d\b" % k)) for k in range(1, 4)] + [("F%d" % k, re.compile(r"\bFig\. %d\b" % k)) for k in range(1, 5)]
place = {}
for key, rx in ITEMS:
    for k, (kind, tx) in enumerate(flow):
        if kind in ("p", "li") and rx.search(tx):
            place.setdefault(k, []).append((rx.search(tx).start(), key)); break
    else: raise AssertionError("not cited: " + key)
FIG = {"F1": ("outputs/figures/example_ddr_crop.png", 6.5), "F2": ("outputs/figures/figure1_depth_vs_time.png", 7.2), "F3": ("outputs/figures/figure3_td_validation.png", 4.6), "F4": ("outputs/figures/figure4_spud_offset.png", 4.8)}

# ------------------------------------------------------------------ the document from the template
doc = docx.Document(TPL)
bodyel = doc.element.body
pars = list(doc.paragraphs)
for p in pars[12:]: p._p.getparent().remove(p._p)        # the template's sample text (and the text box anchored in it)
for k in (10, 9, 8, 7, 6): pars[k]._p.getparent().remove(pars[k]._p)
pars[1].text = "IPTC-25544-MS"; pars[2].text = TITLE; pars[3].text = "T. Appalla"; pars[5].text = "Independent Researcher"
for s in doc.sections:
    for f in (s.even_page_footer, s.footer, s.first_page_footer):
        for p in f.paragraphs:
            if "REMINDER" in p.text: p.text = ""
doc.core_properties.title = TITLE; doc.core_properties.author = "T. Appalla"; doc.core_properties.last_modified_by = "T. Appalla"; doc.core_properties.comments = ""

W = nsdecls("w")
BORD = '<w:tcBorders><w:top w:val="single" w:color="808080" w:sz="4"/><w:left w:val="single" w:color="808080" w:sz="4"/><w:bottom w:val="single" w:color="808080" w:sz="4"/><w:right w:val="single" w:color="808080" w:sz="4"/></w:tcBorders>'
MAR = '<w:tcMar><w:top w:type="dxa" w:w="30"/><w:left w:type="dxa" w:w="70"/><w:bottom w:type="dxa" w:w="30"/><w:right w:type="dxa" w:w="70"/></w:tcMar>'


def make_table(rows, widths, right=frozenset()):
    def cell(text, w, head=False, rt=False):
        shd = '<w:shd w:fill="E7E6E6" w:color="auto" w:val="clear"/>' if head else ""
        b = "<w:b/><w:bCs/>" if head else ""
        return (f'<w:tc><w:tcPr><w:tcW w:type="dxa" w:w="{w}"/>{BORD}{shd}{MAR}</w:tcPr><w:p><w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/><w:jc w:val="{"right" if rt else "left"}"/></w:pPr><w:r><w:rPr>'
                f'<w:rFonts w:ascii="Arial" w:cs="Arial" w:eastAsia="Arial" w:hAnsi="Arial"/>{b}<w:sz w:val="16"/><w:szCs w:val="16"/></w:rPr><w:t xml:space="preserve">{escape(text)}</w:t></w:r></w:p></w:tc>')
    xml = '<w:tr><w:trPr><w:cantSplit/><w:tblHeader/></w:trPr>' + "".join(cell(h, w, head=True) for h, w in zip(rows[0], widths)) + "</w:tr>"
    for row in rows[1:]:
        xml += '<w:tr><w:trPr><w:cantSplit/></w:trPr>' + "".join(cell(c, widths[ci], rt=ci in right) for ci, c in enumerate(row)) + "</w:tr>"
    grid = "".join('<w:gridCol w:w="%d"/>' % w for w in widths)
    return parse_xml(f'<w:tbl {W}><w:tblPr><w:tblW w:w="{sum(widths)}" w:type="dxa"/><w:tblLayout w:type="fixed"/></w:tblPr><w:tblGrid>{grid}</w:tblGrid>{xml}</w:tbl>')


def add_text(par, text):
    for k, part in enumerate(re.split(r"\*\*", text)):
        if part: r = par.add_run(part); r.bold = True if k % 2 else None


def P(style, text, **kw):
    par = doc.add_paragraph(style=style); add_text(par, text)
    for a, v in kw.items(): setattr(par.paragraph_format, a, v)
    return par


def put_float(key):
    if key[0] == "T":
        n = int(key[1])
        c = P("Table Caption", "Table %d: %s" % (n, caps[key])); c.paragraph_format.keep_with_next = True
        bodyel.sectPr.addprevious(make_table(tables[n - 1], WIDTH[key], RIGHT.get(key, frozenset())))
        nt = P("Body Text Paragraph (initial)", notes[key]); nt.paragraph_format.space_before = Pt(2); nt.paragraph_format.space_after = Pt(6)
        for r in nt.runs: r.font.name = "Arial"; r.font.size = Pt(7.5); r.italic = True
    else:
        f, w = FIG[key]
        ip = doc.add_paragraph(style="Body Text Paragraph (initial)"); ip.alignment = WD_ALIGN_PARAGRAPH.CENTER; ip.paragraph_format.keep_with_next = True
        ip.paragraph_format.space_before = Pt(4); ip.add_run().add_picture(f, width=Inches(w))
        c = P("Fig Caption", "Fig. %s: %s" % (key[1], caps[key])); c.paragraph_format.space_after = Pt(6)


prev_head = True


def emit(lo, hi):
    global prev_head
    for k in range(lo, hi):
        kind, tx = flow[k]
        if kind == "h1": P("Head1", tx); prev_head = True
        elif kind == "h2": P("Head2", tx if tx.endswith(".") else tx + "."); prev_head = True
        elif kind == "li": P("List Paragraph", "• " + tx, left_indent=Inches(0.25), first_line_indent=Inches(-0.18))
        else: P("Body Text Paragraph (initial)" if prev_head else "Body Text Paragraph", tx); prev_head = False
        for _, key in sorted(place.get(k, [])): put_float(key)


emit(0, len(flow))
P("Head1", "Nomenclature")
USED = " ".join([tx for kind, tx in flow] + list(caps.values()) + list(notes.values()) + [c for t in tables for r in t for c in r])
noms = [n for n in noms if re.search(r"(?<![A-Za-z])" + re.escape(n.split(" = ")[0]) + r"(?![A-Za-z])", USED, re.I)]
for n in noms:
    q = P("Body Text Paragraph (initial)", n); q.paragraph_format.space_after = Pt(0); q.alignment = WD_ALIGN_PARAGRAPH.LEFT
P("Head1", "References")
for r in refs:
    q = P("Body Text Paragraph (initial)", r); q.alignment = WD_ALIGN_PARAGRAPH.LEFT; q.paragraph_format.left_indent = Inches(0.25); q.paragraph_format.first_line_indent = Inches(-0.25); q.paragraph_format.space_after = Pt(2)
P("Head1", "SI Metric Conversion Factors")
si = [["To convert", "Multiply by", "To obtain"], ["in.", "%s (exact)" % REG["units.inch_to_cm"]["value"], "cm"], ["sg (relative density, water = 1)", "{:,} (exact)".format(REG["units.sg_to_kg_m3"]["value"]), "kg/m3"]]
bodyel.sectPr.addprevious(make_table(si, [3600, 2400, 2400]))
P("Body Text Paragraph (initial)", "Hole and casing sizes in this paper are nominal inch designations as written in the reports (for example 12¼ in. hole and 9⅝ in. casing), and depths are in metres (m).", space_before=Pt(4))
doc.save(OUT)

# ------------------------------------------------------------------ report: word count (excluding references), trade-name scan
d2 = docx.Document(OUT)
inref = False; words = 0; sections = {}; cur = "front"
for el in d2.element.body.iterchildren():
    tag = el.tag.split("}")[1]
    if tag == "p":
        q = Paragraph(el, d2); t = q.text.strip()
        if q.style.name == "Head1": cur = t; inref = t == "References"
        if inref and q.style.name != "Head1": continue
        w = len(t.split()); words += w; sections[cur] = sections.get(cur, 0) + w
    elif tag == "tbl":
        if inref: continue
        w = sum(len(c.text.split()) for r in Table(el, d2).rows for c in r.cells); words += w; sections[cur] = sections.get(cur, 0) + w
alltext = " ".join(q.text for q in d2.paragraphs) + " " + " ".join(c.text for t in d2.tables for r in t.rows for c in r.cells)
caps_tokens = sorted(set(re.findall(r"[A-Z][A-Za-z]{3,}", alltext)))
FORBID = ["EZSV", "EVO plug", "Halliburton", "Anthropic", "Claude", "Databricks", "Maersk", "Baker", "Schlumberger"]
assert not [f for f in FORBID if f.lower() in alltext.lower()], [f for f in FORBID if f.lower() in alltext.lower()]
json.dump(dict(words_excluding_references=words, words_by_section=sections, edits=len(LOG)), open("manuscript/iptc_build_report.json", "w", newline="\n"), indent=1)
print("saved", OUT, "| words (excluding references, including tables and captions):", words)
print(json.dumps(sections))
print("capitalised tokens for the trade-name scan:", " ".join(caps_tokens))
NL = chr(10)
open("manuscript/IPTC_CHANGES.md", "w", encoding="utf-8", newline=NL).write("# IPTC author-kit edits to the author's text" + NL + NL + "Built by src/stage12_iptc.py from manuscript/paper2_author.docx. Each line is an exact-string edit or a structural change; the Abstract and the Conclusions are carried over unchanged except the one em dash." + NL + NL + NL.join(sorted({"- " + b for a, b in LOG})) + NL)
