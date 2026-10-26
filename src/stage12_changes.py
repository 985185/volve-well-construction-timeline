"""Stage 12: write manuscript/CHANGES.md from data/interim/stage12_log.json (written by stage12_manuscript.py) and the registry check."""
import collections
import json
import subprocess
import sys

L = json.load(open("data/interim/stage12_log.json", encoding="utf-8"))
chk = subprocess.run([sys.executable, "-X", "utf8", "src/stage12_check.py"], capture_output=True, text=True).stdout.strip().splitlines()
reg = json.load(open("outputs/numbers_registry.json", encoding="utf-8"))
cut = lambda s, n=330: s if len(s) <= n else s[:n].rstrip() + " ..."

out = ["# Manuscript change log (DRAFT)", "",
       "Base file: `inputs/paper2_v2.docx`. Section 1 of this log gives table numbers as in v2; in the draft every table number is two higher (Tables 1 and 2 are new), and Section 2 uses the draft numbers. Draft: `manuscript/paper2_draft.docx`, built by `src/stage12_manuscript.py` on 2026-10-24 from `outputs/numbers_registry.json` "
       f"({len(reg)} entries). Every change below carries the registry id of the new value (where the change is a number) and the reason. "
       "Yellow highlighting in the draft marks open [TJ:] notes only. The kick-off depths were signed off by the author in `outputs/kickoff_signoff.xlsx` (section 5). No em dashes are used.", "",
       "## 1. Changes", ""]
for n, e in enumerate(L["log"], 1):
    ids = f" Registry id: `{e['id'].replace(';', '`, `')}`." if e["id"] else ""
    out.append(f"{n}. **{e['location']}.** Old: {cut(e['old'])} New: {cut(e['new'])}{ids} Reason: {e['reason']}.")
out += ["", "## 2. Unchanged v2 numbers", "",
        "All other numbers in the v2 text and tables are unchanged and match the registry: 1,759 DDRs, 26 wellbores, 11 families; Table 4 (phase distribution, all 14 rows); the audit numbers (383, 296 + 87, 39 + 11, 26 of 50, 23 of 39, 3 of 11, 9 + 10 + 7, 0.385 to 0.652, 0.2177, 0.1132, about 199 DDRs, 85.4%, 82.5 to 88.3%, 0.518, 85.3%, 4.2%); the 1,421-row timeline; Table 5 (total depth, all 26 rows: 22 exact, F-15 15 m, 19 S 227 m, 19 B and F-11 unmatched); Table 6 totals (26 wellbores; the category counts changed and are listed in section 1: 6, 8, 4, 1, 2, 5 against v2 7, 8, 4, 1, 2, 4); the F-12 and F-1 dates; the 61 and 10 DDRs with fractions; the 14.10% kick-off population.", ""]
out += ["## 3. [TJ:] notes cleared as resolved", ""]
for r in L["resolved"]:
    out.append(f"- {r['location']}: {cut(r['note'], 260)}")
out += ["", "## 4. [TJ:] notes still open in the draft", ""]
for t in L["open_notes"]:
    out.append(f"- {cut(t, 400)}")
out += ["- Not a [TJ:] note but open: the release label and year of the WITSML 1.4.0.0 schema could not be verified (decision 45), so the Energistics reference cites the schema version declared in the files with an access date; and the Sidahmed et al. (2015) check used the Crossref record because OnePetro returned 403 (decision 44).", ""]
out += ["## 5. Kick-off sign-off", "",
        "The kick-off depths were proposed by an AI tool and signed off by the author in `outputs/kickoff_signoff.xlsx` (read by `src/stage8d_apply_signoff.py`): 15 rows reviewed, 15 approved (Y), 0 marked N, 0 author depths entered, 0 author notes, so no row was changed. "
        "The AI's first proposals for 15/9-19 A, 15/9-F-9 A and 15/9-F-11 B were rejected earlier (decision 40) and the table values kept. The Table 5 and Table 6 values derived from these depths are final, and no value in the draft is highlighted as provisional.", ""]
out += ["## 6. Check: every number in the draft against the registry", "", "`src/stage12_check.py` (output `outputs/manuscript_registry_check.csv`):", ""]
out += [f"    {x}" for x in chk]
out += ["", "A number is accepted when its value equals a registry value (sign-insensitive; a percentage may be written as a proportion). The test is by value, so it shows that each number exists in the registry, not that it sits in the right sentence; the sentences with new numbers were written from the registry entries named in section 1.", ""]
open("manuscript/CHANGES.md", "w", encoding="utf-8").write("\n".join(out))
print(len(out), "lines;", len(L["log"]), "changes;", len(L["resolved"]), "resolved;", len(L["open_notes"]), "open")
