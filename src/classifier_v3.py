# ==============================================================================
# Drilling Phase Classifier v3 (final) -- companion code for IPTC-25544-MS
#
# This is the exact, verbatim pattern set used to produce the phase-classified
# table (workspace.default.volve_ddr_classified) reported in the paper:
# 1,303 of 1,759 DDRs classified (74.1%), 456 Unclassified (25.9%).
#
# Provenance: recovered from an internal source notebook (Paper_2.py) during
# manuscript reconstruction. This is "Classifier v3 (final)" -- the version
# explicitly named as final in that notebook, with changes from v2:
#   1. Removed an over-matching combined casing-string pattern from
#      "Intermediate casing"
#   2. Added coring language to "Reservoir drilling"
#   3. Added tieback-casing language to "Liner / Casing run"
#   4. Moved "EVO plug" language from "Completion" to "P&A"
# No later version of this pattern set exists in the source corpus.
#
# STATUS: verbatim, unmodified. No patterns, priorities, phase names, or
# matching logic have been reformatted, reordered, simplified, or otherwise
# altered from the version that produced the paper's reported figures. The
# only addition is the classify_ddr() convenience wrapper at the bottom of
# this file, which is not part of the original classifier logic -- it exists
# only to expose normalise_text() + classify_v3() as a single-call API.
#
# Usage:
#   from classifier_v3 import classify_ddr
#   classify_ddr('DRLD 17 1/2" HOLE FROM 500M TO 620M.')
#   -> 'Intermediate drilling'
# ==============================================================================

import re

# ------------------------------------------------------------------------------
# normalise_text -- Unicode fraction normalisation, applied to raw sum24hr text
# BEFORE classify_v3() is called. Handles the four non-ASCII fraction glyphs
# observed in the Volve DDR free-text corpus.
# ------------------------------------------------------------------------------
def normalise_text(t):
    t = str(t)
    t = t.replace("½", " 1/2")
    t = t.replace("¼", " 1/4")
    t = t.replace("¾", " 3/4")
    t = t.replace("⅛", " 1/8")
    return t

# ------------------------------------------------------------------------------
# PHASES_V3 -- verbatim priority-ordered pattern table, 13 categories.
# Lower priority number wins on multiple matches (see classify_v3 below).
# ------------------------------------------------------------------------------
PHASES_V3 = [
    ("Spud / Conductor",      1, [
        r"36.{0,5}(?:hole|HO|BHA)", r"30.{0,5}conductor",
        r"\bspud\b", r"tagged sea bt",
        r"wash.{0,10}down.{0,20}conductor"
    ]),
    ("Surface casing",        2, [
        r"26.{0,5}(?:hole|BHA|section)", r"20.{0,5}casing",
        r"RIH.{0,20}20.{0,5}cas", r"running.{0,15}20.{0,5}cas",
        r"ran.{0,10}20.{0,5}casing", r"land.{0,10}20.{0,5}casing"
    ]),
    ("Intermediate drilling", 3, [
        r"17.{0,3}1.2.{0,5}(?:hole|section|BHA)",
        r"17\.5.{0,5}(?:hole|section)",
        r"drilling.{0,15}17.{0,3}(?:1.2|5)",
        r"drilled.{0,15}17.{0,3}(?:1.2|5)"
    ]),
    ("Intermediate casing",   4, [
        r"13.{0,3}3.8.{0,10}(?:casing|cas|liner)",
        r"10.{0,3}3.4.{0,10}(?:casing|cas|liner)",   # removed combined string
        r"RIH.{0,20}(?:13|10.{0,3}3).{0,10}(?:casing|liner|cas)",
        r"running.{0,15}(?:13|10.{0,3}3).{0,10}(?:casing|liner)",
        r"ran.{0,15}(?:13|10.{0,3}3).{0,10}(?:casing|liner)",
        r"14.{0,5}(?:casing|liner).{0,5}(?:run|ran|RIH)",
        r"ran.{0,10}14.{0,5}casing",
        r"RIH.{0,15}14.{0,5}casing"
    ]),
    ("Reservoir drilling",    5, [
        r"12.{0,3}1.4.{0,5}(?:hole|section|BHA)",
        r"12\.25.{0,5}(?:hole|section)",
        r"drilling.{0,15}12.{0,3}(?:1.4|25)",
        r"drilled.{0,15}12.{0,3}(?:1.4|25)",
        r"8.{0,3}1.2.{0,5}(?:hole|section|BHA)",
        r"8\.5.{0,5}(?:hole|section)",
        r"drilling.{0,15}8.{0,3}(?:1.2|5)",
        r"drilled.{0,15}8.{0,3}(?:1.2|5)",
        r"8½.{0,5}(?:hole|section)",
        r"6.{0,3}(?:hole|section)",
        r"\bcore.{0,10}(?:cut|no|barrel)\b",   # coring
        r"cut core", r"\bcoring\b"
    ]),
    ("Liner / Casing run",    6, [
        r"\bliner\b", r"running.{0,15}liner",
        r"RIH.{0,20}liner", r"landing.{0,15}liner",
        r"ran.{0,15}liner", r"set.{0,10}liner hanger",
        r"RIH.{0,20}casing", r"running.{0,15}casing",
        r"ran.{0,15}casing", r"P.U.{0,15}casing",
        r"9.{0,3}5.8.{0,10}(?:casing|liner|screen)",
        r"7.{0,5}liner", r"7.{0,5}casing",
        r"tieback.{0,15}casing", r"tie.back.{0,15}casing",
        r"surface tieback", r"ran.{0,15}tieback"
    ]),
    ("Cementing",             7, [
        r"\bcement\b", r"\bcemented\b", r"\bcementing\b",
        r"bumped plug", r"displaced.{0,20}cement",
        r"pumped.{0,15}cement", r"mixed.{0,10}cement",
        r"bullhead.{0,10}cement", r"\bWOC\b",
        r"waiting on cement"
    ]),
    ("Completion",            8, [
        r"\bcompletion\b", r"production packer",
        r"\bpacker\b", r"\btubing\b",
        r"perforat", r"production string",
        r"\bESP\b", r"gas lift", r"inflow test",
        r"sand screen", r"gravel pack"
    ]),
    ("P&A",                   9, [
        r"set.{0,20}\bplug\b", r"\bplug\b.{0,20}set",
        r"\bEZSV\b", r"\bEVO plug\b", r"P&A",
        r"cut.{0,10}(?:casing|csg|tubing)",
        r"CUT.{0,10}(?:CASING|CSG|TUBING|TBG)",
        r"\babandon", r"plug.{0,10}abandon",
        r"milling.{0,15}(?:casing|csg)",
        r"pull.{0,15}(?:casing|csg).{0,10}(?:fish|surface)",
        r"cement plug"
    ]),
    ("Logging / Testing",    10, [
        r"\blogging\b", r"\bLWD\b", r"\bMWD\b", r"\bVSP\b",
        r"\bwireline\b", r"\bWL\b.{0,10}(?:log|run|RIH)",
        r"formation test", r"\bDST\b", r"drill stem test",
        r"\bPLT\b", r"RST log", r"gyro survey",
        r"\bFIT\b", r"formation integrity test",
        r"pressure point", r"\bLOT\b"
    ]),
    ("Workover",             11, [
        r"\bworkover\b", r"coiled tubing",
        r"sidetrack", r"window.{0,15}mill", r"\bwhipstock\b"
    ]),
    ("Waiting / Downtime",   12, [
        r"\bWOW\b", r"waiting on weather", r"wait.{0,15}weather",
        r"rig maintenance", r"general maintenance",
        r"\bstandby\b", r"wait.{0,10}parts",
        r"no crane operation", r"OFS strike",
        r"rig operations suspended"
    ]),
    ("Rig move / Setup",     13, [
        r"skidded rig", r"rig.{0,10}move", r"positioned rig",
        r"\bmooring\b", r"ballast",
        r"anchor.{0,10}(?:wire|chain|test)",
        r"skidded.{0,15}(?:cantilever|to well)"
    ]),
]

# ------------------------------------------------------------------------------
# classify_v3 -- takes already-normalised text, returns the lowest-priority
# matching phase label, or "Unclassified" if no pattern matches.
# ------------------------------------------------------------------------------
def classify_v3(text_norm):
    tl = text_norm.lower()
    matches = []
    for phase_name, priority, patterns in PHASES_V3:
        if re.search("|".join(patterns), tl, flags=re.IGNORECASE):
            matches.append((priority, phase_name))
    if not matches:
        return "Unclassified"
    return sorted(matches)[0][1]

# ------------------------------------------------------------------------------
# classify_ddr -- convenience wrapper (not part of the original v3 logic).
# Takes a raw sum24Hr string and returns its phase label, applying
# normalise_text() then classify_v3() in the same order used to build
# workspace.default.volve_ddr_classified.
# ------------------------------------------------------------------------------
def classify_ddr(text):
    return classify_v3(normalise_text(text))


if __name__ == "__main__":
    examples = [
        'DRLD 17 1/2" HOLE FROM 500M TO 620M.',
        "RAN 9 5/8\" LINER TO 3200M.",
        "WOC. CEMENT PLUG SET AT 1500M.",
        "This text matches nothing in the pattern set.",
    ]
    for e in examples:
        print(f"{classify_ddr(e)!r:30s} <- {e!r}")
