"""Stage 6b: blind review workbook for TJ. Contains NO old calls, categories or reasons. Row order shuffled with a recorded seed."""
import random
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

SEED = 20261024
m = pd.read_csv("data/interim/audit_old50_filename_map.csv")
d = pd.read_parquet("data/interim/ddr.parquet")[["filename", "sum24Hr"]]
rows = m[["filename", "wellbore", "day", "stratum"]].merge(d, on="filename", validate="one_to_one").sort_values("filename").reset_index(drop=True)
assert len(rows) == 50 and rows.filename.is_unique
order = list(range(50)); random.Random(SEED).shuffle(order)          # shuffle the filename-sorted rows
rows = rows.iloc[order].reset_index(drop=True)

wb = Workbook(); ws = wb.active; ws.title = "review"
hdr = ["record_id", "wellbore", "date", "stratum", "sum24Hr", "my_call", "my_miss_reason", "my_note"]
ws.append(hdr)
for r in rows.itertuples():
    ws.append([r.filename, r.wellbore, r.day, r.stratum, r.sum24Hr.strip(), None, None, None])
for c in ws[1]:
    c.font = Font(bold=True); c.fill = PatternFill("solid", fgColor="DDDDDD")
for col, w in zip("ABCDEFGH", [30, 16, 12, 17, 90, 20, 28, 40]): ws.column_dimensions[col].width = w
for row in ws.iter_rows(min_row=2):
    for c in row: c.alignment = Alignment(wrap_text=True, vertical="top")
    for c in row[5:]: c.fill = PatternFill("solid", fgColor="FFF9D6")
dv1 = DataValidation(type="list", formula1='"CONSTRUCTION,NON_CONSTRUCTION"', allow_blank=True)
dv2 = DataValidation(type="list", formula1='"NO_HOLE_SIZE,OTHER_MISS,NONSTANDARD_TERMINOLOGY"', allow_blank=True)
ws.add_data_validation(dv1); ws.add_data_validation(dv2); dv1.add("F2:F51"); dv2.add("G2:G51")
ws.freeze_panes = "B2"
info = wb.create_sheet("info")
for line in [["Blind review of 50 unclassified DDR narratives (IPTC-25544-MS audit)"],
             ["Fill in my_call (CONSTRUCTION or NON_CONSTRUCTION) for every row."],
             ["my_miss_reason (only if CONSTRUCTION): NO_HOLE_SIZE, OTHER_MISS, NONSTANDARD_TERMINOLOGY; leave blank otherwise."],
             ["my_note: optional free text."],
             ["Row order is shuffled; shuffle seed", SEED, "(Python random.Random(seed).shuffle over the 50 rows sorted by filename)."],
             ["record_id is the DDR file name in the raw archive. This file holds no earlier calls."],
             ["Contains DDR narrative text: do not commit or publish."]]:
    info.append(line)
info.column_dimensions["A"].width = 110
wb.save("outputs/audit_blind_review.xlsx")
chk = pd.read_excel("outputs/audit_blind_review.xlsx", sheet_name="review")
print(chk.shape, list(chk.columns)); print(chk[["my_call", "my_miss_reason", "my_note"]].notna().sum().to_dict())
print("strata:", chk.stratum.value_counts().to_dict(), "| first 5 ids:", chk.record_id.head(5).tolist())
print("old-call words present anywhere in the sheet headers:", any(h in " ".join(chk.columns).lower() for h in ["adjud", "reason", "category"]))
