"""Stage 8d: apply the author's kick-off sign-off. Reads the author columns (author_approved, author_depth, author_note) of outputs/kickoff_signoff.xlsx, which are TJ's and are never written here,
and writes them next to the AI proposal in outputs/kickoff_proposal.csv with the final depth used downstream.
final_depth_m = author_depth where the author entered one, otherwise the table depth (ddr_kickoff_depth_m) for a row the author approved (Y). A row marked N without an author depth stops the script."""
import pandas as pd

x = pd.read_excel("outputs/kickoff_signoff.xlsx", sheet_name="signoff").loc[:, lambda d: ~d.columns.str.endswith(".1")]   # the workbook repeats the four proposed_* columns; pandas names the repeats *.1
assert len(x) == 15 and x.author_approved.isin(["Y", "N"]).all(), "every row needs author_approved = Y or N"
assert (x.proposed_depth == x.proposed_depth).all()
x["final_depth_m"] = x.author_depth.where(x.author_depth.notna(), x.ddr_kickoff_depth_m)
n_rows = x[x.author_approved == "N"]
assert n_rows.author_depth.notna().all(), f"marked N without an author depth: {n_rows.sidetrack.tolist()}"
x["final_source"] = x.author_depth.notna().map({True: "author depth", False: "table depth, author approved"})
changed = x[x.final_depth_m != x.ddr_kickoff_depth_m]
x.to_csv("outputs/kickoff_proposal.csv", index=False)
print("rows:", len(x), "| approved Y:", int((x.author_approved == "Y").sum()), "| marked N:", n_rows.sidetrack.tolist(), "| author depth entered:", int(x.author_depth.notna().sum()),
      "| author notes:", int(x.author_note.notna().sum()), "| final differs from table:", changed.sidetrack.tolist())
