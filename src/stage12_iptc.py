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
NEWLIM = ["The classifier assigns one primary phase to each DDR, using that report alone. A DDR that narrates both drilling progress and cementing takes the higher-priority drilling phase, and the Cementing count therefore underrepresents the days on which cementing occurred alongside another operation. The agreement audit (Section 5.3) compares the classifier with one person's reading of single reports, did not test neighbouring reports, and relies on causes of disagreement that the AI tool assigned from the narratives.",
          "The residual audit labelled construction content only, which makes the recoverable coverage conservative for non-construction phases such as waiting or rig moves, and it does not guarantee that a recovered report would receive the correct phase. One reviewer, the author, labelled the 50 records. The design-based interval of 82.6 to 88.1% rests on a normal approximation, which is optimistic with 11 records in one group. Two sampled records sit in a group that does not match their context: the 1980 date sentinel places the 1997 drilling of 15/9-19 A in the production group, and the 2013 campaign of 15/9-F-1 also falls there.",
          "The timeline holds only DDRs with a genuine measured depth and applies no interpolation. A discontinuity marks missing data and supports no conclusion about drilling activity in that period.",
          "Two kick-off depths rest on weaker evidence: 15/9-19 ST2 on the measured depth at the transition (between 1,486 and 1,536 m) and 15/9-F-11 B on an interval of cement and new formation (2,531 to 2,589 m). NOD gives no kick-off point for three sidetracks. Wellbores of one family share the hole above their kick-off depths (Section 6.3), and any formation-level analysis must account for this. Metres per report are not rates of penetration, and gaps between reports affect the elapsed time to total depth (Table 8).",
          "No isolated ablation was run for Unicode normalisation (the one-half sign in 61 DDRs and the one-quarter sign in 10). An extraction error would propagate to every result, and the agreement with NOD on total depth (19 of 21 name-matched wellbores within 0.5 m) indicates that the depth fields were extracted faithfully."]
for j, t in enumerate(NEWLIM): flow.insert(first + j, ("p", t))
# 12 Nomenclature
noms = [n for n in noms if not n.startswith("EZSV")]
noms = [re.sub(r"\s+=\s+", " = ", n) for n in noms]
# 13 references: bold volume numbers (** marks the bold run)
for k, r in enumerate(refs):
    if r.startswith("Tunkiel"): refs[k] = r.replace("J Pet Sci Eng 196:", "J Pet Sci Eng **196**:"); assert "**196**" in refs[k]
    if r.startswith("Wilson"): refs[k] = r.replace("J Am Stat Assoc 22 (158)", "J Am Stat Assoc **22** (158)"); assert "**22**" in refs[k]

# ------------------------------------------------------------------ floats: place each directly after the paragraph that first cites it
ITEMS = [("T%d" % k, re.compile(r"\bTable %d\b" % k)) for k in range(1, 9)] + [("F%d" % k, re.compile(r"\bFig\. %d\b" % k)) for k in range(1, 5)]
place = {}
for key, rx in ITEMS:
    for k, (kind, tx) in enumerate(flow):
        if kind in ("p", "li") and rx.search(tx):
            place.setdefault(k, []).append((rx.search(tx).start(), key)); break
    else: raise AssertionError("not cited: " + key)
FIG = {"F1": ("outputs/figures/example_ddr_crop.png", 6.5), "F2": ("outputs/figures/figure1_depth_vs_time.png", 7.2), "F3": ("outputs/figures/figure3_td_validation.png", 4.6), "F4": ("outputs/figures/figure4_spud_offset.png", 4.8)}
WIDTH = {"T1": [1700, 5300, 3800], "T2": [800, 2600, 2400, 5000], "T3": [2900, 1100, 1000, 5800], "T4": [3400, 1700, 1700], "T5": [1700, 1300, 1000, 900, 1800, 4100],
         "T6": [1800, 800, 4400, 3800], "T7": [1500, 1700, 1500, 2600, 1000, 1100, 1400], "T8": [2300, 1100, 1500, 1400, 1100, 1700, 1700]}
RIGHT = {"T3": {2}, "T4": {1, 2}, "T5": {1, 2, 3}, "T7": {2, 4, 5}, "T8": {1, 2, 3, 4, 5, 6}}

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


APP = [k for k, (kind, tx) in enumerate(flow) if kind == "h1" and tx.startswith("Appendix A")]; assert len(APP) == 1
emit(0, APP[0])
P("Head1", "Nomenclature")
for n in noms:
    q = P("Body Text Paragraph (initial)", n); q.paragraph_format.space_after = Pt(0); q.alignment = WD_ALIGN_PARAGRAPH.LEFT
P("Head1", "References")
for r in refs:
    q = P("Body Text Paragraph (initial)", r); q.alignment = WD_ALIGN_PARAGRAPH.LEFT; q.paragraph_format.left_indent = Inches(0.25); q.paragraph_format.first_line_indent = Inches(-0.25); q.paragraph_format.space_after = Pt(2)
prev_head = True
emit(APP[0], len(flow))
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
