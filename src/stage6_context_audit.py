"""Stage 6f: context audit workbook for the classified records. A NEW stratified sample, four classified DDRs per phase (13 phases, 52 records), drawn with a recorded seed from the
filename-sorted classified population after removing the 52 records of the single-report blind audit (stage6_classified_audit.py, reproduced here and checked against its key sheet).
Each sampled day D is shown with the reports of the same wellbore on D-2, D-1, D, D+1 and D+2. The assigned phase is on a hidden sheet. Contains DDR narrative text: untracked."""
import math, random
import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

SEED_OLD, SEED, PER_PHASE = 20261105, 20261106, 4
DISPLAY = {"Spud / Conductor": "Spud/Conductor", "Surface casing": "Surface hole and casing", "Intermediate drilling": "Intermediate drilling", "Intermediate casing": "Intermediate casing",
           "Reservoir drilling": "12¼ in. and smaller hole", "Liner / Casing run": "Liner/Casing run", "Cementing": "Cementing", "Completion": "Completion", "P&A": "P&A",
           "Logging / Testing": "Logging/Testing", "Workover": "Workover", "Waiting / Downtime": "Waiting/Downtime", "Rig move / Setup": "Rig move/Setup"}
d = pd.read_parquet("data/interim/ddr.parquet")[["filename", "wellbore", "date_report", "md", "sum24Hr"]]
c = pd.read_parquet("data/interim/classified_new.parquet")[["filename", "phase"]]
c = c[c.phase != "Unclassified"].merge(d, on="filename", validate="one_to_one").sort_values("filename").reset_index(drop=True)
assert len(c) == 1303 and set(c.phase) == set(DISPLAY)

# the earlier 52, reproduced with the earlier seed (same generator calls) and checked against the earlier workbook's key
rng = random.Random(SEED_OLD); old = []
for ph in sorted(c.phase.unique()): old += [c.filename[i] for i in rng.sample(list(c[c.phase == ph].index), PER_PHASE)]
oldkey = {r[0] for r in load_workbook("outputs/classified_audit_blind.xlsx")["key"].iter_rows(min_row=2, values_only=True)}
assert set(old) == oldkey and len(old) == 52, "earlier draw not reproduced"

pool_all = c[~c.filename.isin(old)].reset_index(drop=True)          # sorted by filename
rng = random.Random(SEED); picked = []
for ph in sorted(pool_all.phase.unique()):
    idx = list(pool_all[pool_all.phase == ph].index); picked += rng.sample(idx, min(PER_PHASE, len(idx)))   # Workover has 6 classified reports, 4 already used: 2 remain
rows = pool_all.loc[picked].reset_index(drop=True); assert len(rows) == 50 and rows.filename.is_unique and not set(rows.filename) & set(old)
order = list(range(len(rows))); rng.shuffle(order); rows = rows.iloc[order].reset_index(drop=True)

d["day"] = pd.to_datetime(d.date_report.str[:10]); by = {(r.wellbore, r.day): r for r in d.itertuples()}
assert len(by) == len(d)                                              # one report per wellbore and day
def md_txt(m): return "md n/a" if m in ("-999.99", "0") else f"md {m} m"
def block(r):
    D = pd.Timestamp(r.date_report[:10]); out = []
    for k in (-2, -1, 0, 1, 2):
        t = D + pd.Timedelta(days=k); x = by.get((r.wellbore, t)); tag = ">>> D (day to judge) <<<" if k == 0 else f"D{k:+d}"
        out.append(f"[{tag}] {t.date()}: " + (f"{md_txt(x.md)}. " + " ".join(str(x.sum24Hr).split()) if x is not None else "no report"))
    return "\n\n".join(out)

wb = Workbook(); ws = wb.active; ws.title = "review"
ws.append(["record_id", "wellbore", "context block", "my_phase", "needed_context", "my_note"])
CH = list(DISPLAY.values()) + ["Other (write in note)", "Can't tell"]
maxlines = 0
for i, r in enumerate(rows.itertuples(), start=2):
    b = block(r); ws.append([r.filename, r.wellbore, b, None, None, None])
    lines = sum(math.ceil(max(len(p), 1) / 105) for p in b.split("\n")); maxlines = max(maxlines, lines); ws.row_dimensions[i].height = min(409, 15 * lines + 6)
for cell in ws[1]: cell.font = Font(bold=True); cell.fill = PatternFill("solid", fgColor="DDDDDD")
for col, w in zip("ABCDEF", [30, 16, 115, 30, 14, 40]): ws.column_dimensions[col].width = w
for row in ws.iter_rows(min_row=2):
    for cell in row: cell.alignment = Alignment(wrap_text=True, vertical="top")
    for cell in row[3:]: cell.fill = PatternFill("solid", fgColor="FFF9D6")
dv = DataValidation(type="list", formula1='"' + ",".join(CH) + '"', allow_blank=True, showErrorMessage=False); ws.add_data_validation(dv); dv.add("D2:D51")
dv2 = DataValidation(type="list", formula1='"Y,N"', allow_blank=True); ws.add_data_validation(dv2); dv2.add("E2:E51")
ws.freeze_panes = "B2"
info = wb.create_sheet("info")
for line in [["Context audit of 50 classified DDRs (IPTC-25544-MS), four per phase (two for Workover, the only reports left), drawn from the classified reports not used in the single-report blind audit."],
             ["context block: the same wellbore's reports on D-2, D-1, D, D+1, D+2 (full text). The day to judge is marked >>> D <<<. 'no report' means the archive has no report for that date. md n/a marks a placeholder depth."],
             ["my_phase: the phase that is the primary description of day D, chosen without seeing the assigned phase. needed_context: Y if you needed the neighbouring reports to decide, N if D alone was enough. my_note: optional."],
             ["Phase names: " + "; ".join(DISPLAY.values())],
             ["Draw: Python random.Random(seed).sample, four per phase, seed", SEED, "pool = classified reports minus the 52 earlier records (earlier seed", SEED_OLD, "), sorted by filename; phases in alphabetical order of the classifier names; rows then shuffled with the same generator."],
             ["The assigned phase is on the hidden sheet 'key' (paper's phase names). Contains DDR narrative text: do not commit or publish."]]:
    info.append(line)
info.column_dimensions["A"].width = 110
key = wb.create_sheet("key"); key.append(["record_id", "assigned_phase"])
for r in rows.itertuples(): key.append([r.filename, DISPLAY[r.phase]])
key.sheet_state = "hidden"
wb.save("outputs/classified_audit_context.xlsx")
chk = pd.read_excel("outputs/classified_audit_context.xlsx", sheet_name="review")
print(chk.shape, list(chk.columns), "| per phase:", rows.phase.value_counts().to_dict(), "| overlap with earlier 52:", len(set(rows.filename) & set(old)), "| max block lines:", maxlines)
print("neighbour coverage (no report counts per offset):", {k: int(sum((r.wellbore, pd.Timestamp(r.date_report[:10]) + pd.Timedelta(days=k)) not in by for r in rows.itertuples())) for k in (-2, -1, 1, 2)})
print("visible sheets:", [s.title for s in wb.worksheets if s.sheet_state == "visible"])
