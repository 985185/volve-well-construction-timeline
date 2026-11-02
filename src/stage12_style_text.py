"""Style revision of the manuscript text (2026-11-02). Reads src/stage12_style_text*.txt (in name order): blocks of "@@ <section> | <start of the old paragraph>" followed by the new paragraph on one line.
src/stage12_manuscript.py applies each block to the paragraph that starts with the old text, and checks that no number or reference is added and that every quotation is kept."""
import glob

STYLE = []
for _f in sorted(glob.glob("src/stage12_style_text*.txt")):
    _sec = _prefix = None
    for line in open(_f, encoding="utf-8").read().splitlines():
        if line.startswith("@@ "):
            _sec, _prefix = [x.strip() for x in line[3:].split(" | ", 1)]
        elif line.strip() and _prefix is not None:
            STYLE.append((_sec, _prefix, line.strip())); _prefix = None
