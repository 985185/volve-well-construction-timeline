"""Stage 6d: blind audit workbook for the classified records. Four classified DDRs per phase (13 phases, 52 records), drawn with a recorded seed from the
filename-sorted classified population. The visible sheet holds no assigned phase; the key is on a hidden sheet. Contains DDR narrative text: untracked."""
import random
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

SEED, PER_PHASE = 20261105, 4
c = pd.read_parquet("data/interim/classified_new.parquet")[["filename", "wellbore", "date_report", "phase"]]
d = pd.read_parquet("data/interim/ddr.parquet")[["filename", "sum24Hr"]]
c = c[c.phase != "Unclassified"].merge(d, on="filename", validate="one_to_one").sort_values("filename").reset_index(drop=True)
assert len(c) == 1303 and c.phase.nunique() == 13
rng = random.Random(SEED); picked = []
for ph in sorted(c.phase.unique()):                    # phases in alphabetical order; the pool of each phase is sorted by filename
    pool = c[c.phase == ph]; picked += rng.sample(list(pool.index), PER_PHASE)
rows = c.loc[picked].reset_index(drop=True); assert len(rows) == 52 and rows.filename.is_unique
order = list(range(52)); rng.shuffle(order); rows = rows.iloc[order].reset_index(drop=True)   # shuffled, so the order does not reveal the phase
DISPLAY = {"Spud / Conductor": "Spud/Conductor", "Surface casing": "Surface hole and casing", "Intermediate drilling": "Intermediate drilling", "Intermediate casing": "Intermediate casing",
           "Reservoir drilling": "12¼ in. and smaller hole", "Liner / Casing run": "Liner/Casing run", "Cementing": "Cementing", "Completion": "Completion", "P&A": "P&A",
           "Logging / Testing": "Logging/Testing", "Workover": "Workover", "Waiting / Downtime": "Waiting/Downtime", "Rig move / Setup": "Rig move/Setup"}
assert set(DISPLAY) == set(c.phase.unique())
CHOICES = list(DISPLAY.values()) + ["none fits"]

wb = Workbook(); ws = wb.active; ws.title = "review"
ws.append(["record_id", "wellbore", "date", "sum24Hr", "my_phase", "my_note"])
for r in rows.itertuples():
    ws.append([r.filename, r.wellbore, r.date_report[:10], r.sum24Hr.strip(), None, None])
for cell in ws[1]: cell.font = Font(bold=True); cell.fill = PatternFill("solid", fgColor="DDDDDD")
for col, w in zip("ABCDEF", [30, 16, 12, 90, 30, 40]): ws.column_dimensions[col].width = w
for row in ws.iter_rows(min_row=2):
    for cell in row: cell.alignment = Alignment(wrap_text=True, vertical="top")
    for cell in row[4:]: cell.fill = PatternFill("solid", fgColor="FFF9D6")
dv = DataValidation(type="list", formula1='"' + ",".join(CHOICES) + '"', allow_blank=True, showErrorMessage=False); ws.add_data_validation(dv); dv.add("E2:E53")
ws.freeze_panes = "B2"
info = wb.create_sheet("info")
for line in [["Blind audit of 52 classified DDRs (IPTC-25544-MS), four per phase."],
             ["my_phase: the main operation of the day, chosen without seeing the assigned phase. Pick from the list, or write 'none fits'. Any other text is accepted."],
             ["my_note: note ties here (for example 'also Cementing'), and anything else worth recording."],
             ["Phase names: " + "; ".join(DISPLAY.values())],
             ["Draw: Python random.Random(seed).sample, four per phase, seed", SEED, "pools sorted by filename, phases in alphabetical order of the classifier names, rows then shuffled with the same generator."],
             ["The assigned phase is on the hidden sheet 'key'. Contains DDR narrative text: do not commit or publish."]]:
    info.append(line)
info.column_dimensions["A"].width = 110
key = wb.create_sheet("key"); key.append(["record_id", "assigned_phase", "assigned_phase_display"])
for r in rows.itertuples(): key.append([r.filename, r.phase, DISPLAY[r.phase]])
key.sheet_state = "hidden"
wb.save("outputs/classified_audit_blind.xlsx")
chk = pd.read_excel("outputs/classified_audit_blind.xlsx", sheet_name="review")
print(chk.shape, list(chk.columns), "| phases per draw:", rows.phase.value_counts().unique().tolist(), "| wellbores:", rows.wellbore.nunique())
print("visible sheets:", [s.title for s in wb.worksheets if s.sheet_state == "visible"])
