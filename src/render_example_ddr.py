"""Render the original Daily Drilling Report PDF of the example report to PNG (author-side step, not part of run_pipeline.py: it needs the PDF, which is not in the repository,
and PyMuPDF, which is not in requirements.txt).
Usage:  python -X utf8 src/render_example_ddr.py <wellbore file stem, e.g. 15_9_F_15_D_2013_11_23> <pdf folder> [<output prefix>]
Writes <prefix>_full.png (page 1, 200 dpi) and <prefix>_crop.png (the report header, the summary of the past 24 hours and the plan for the next 24 hours, 200 dpi;
the crop is the top part of page 1, x 30 to 565 pt and y 38 to 340 pt of the A4 page, which is legible at 6.5 in. page width).
The Volve DDR PDFs hold no personal names (checked on the text layer of all 99 F-15 D reports). The values of Rig Name and Drilling contractor are covered by solid boxes (IPTC author-kit review: no company or product names except the data owner and the operator, which stay visible)."""
import os
import sys

import pymupdf

stem, folder = sys.argv[1], sys.argv[2]
prefix = sys.argv[3] if len(sys.argv) > 3 else "outputs/figures/example_ddr"
doc = pymupdf.open(os.path.join(folder, stem + ".pdf"))
page = doc[0]
# solid boxes over the values of the Rig Name and Drilling contractor fields (found on the text layer of this report; the operator stays visible)
for lab in ("MÆRSK", "INSPIRER", "Maersk", "Drilling"):
    for r in page.search_for(lab):
        if 125 < r.y0 < 150 and r.x0 > 108: page.draw_rect(r + (-1.0, -1.0, 1.0, 1.0), color=None, fill=(0, 0, 0))
page.get_pixmap(dpi=200).save(prefix + "_full.png")
page.get_pixmap(dpi=200, clip=pymupdf.Rect(30, 38, 565, 340)).save(prefix + "_crop.png")
print("pages:", len(doc), "| wrote", prefix + "_full.png", prefix + "_crop.png")
