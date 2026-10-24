"""Stage 2: parse WITSML DDR XML to data/interim/ddr.parquet. All values are raw strings; absent tag = null, empty tag = ''."""
import collections, os, sys
import pandas as pd
from lxml import etree

RAW = "data/raw/ddr_xml"
NS = {"w": "http://www.witsml.org/schemas/1series"}
FIELDS = {  # column: xpath relative to drillReport
    "well": "w:nameWell", "wellbore": "w:nameWellbore",
    "date_report": "w:statusInfo/w:dTim", "dTimSpud": "w:wellboreInfo/w:dTimSpud",
    "md": "w:statusInfo/w:md", "md_kickoff": "w:statusInfo/w:mdKickoff", "md_csg_last": "w:statusInfo/w:mdCsgLast",
    "operator": "w:wellboreInfo/w:operator", "forecast24hr": "w:statusInfo/w:forecast24Hr",
    "drill_complete": "w:wellboreInfo/w:dateDrillComplete", "sum24Hr": "w:statusInfo/w:sum24Hr",
    "report_no": "w:statusInfo/w:reportNo",
}

def first(node, xp):
    r = node.xpath(xp, namespaces=NS)
    if not r:
        return None
    return r[0].text if r[0].text is not None else ""

rows, problems = [], []
for name in sorted(os.listdir(RAW)):
    root = etree.parse(os.path.join(RAW, name), etree.XMLParser(resolve_entities=False)).getroot()
    reps = root.xpath("//w:drillReport", namespaces=NS)
    if len(reps) != 1:
        problems.append((name, len(reps))); continue
    rep = reps[0]
    row = {"filename": name, "schema_version": root.get("version")}
    for col, xp in FIELDS.items():
        row[col] = first(rep, xp)
    rigs = rep.xpath("w:wellboreInfo/w:rigAlias[w:namingSystem='NPD Name']/w:name", namespaces=NS)
    row["rig"] = (rigs[0].text or "") if rigs else None
    row["n_rig_npd_name"] = str(len(rigs))
    row["n_activity"] = str(len(rep.xpath("w:statusInfo/w:activity | w:activity", namespaces=NS)))
    rows.append(row)

if problems:
    print("STOP: files without exactly one drillReport:", problems); sys.exit(1)
cols = ["filename", "well", "wellbore", "date_report", "dTimSpud", "md", "md_kickoff", "md_csg_last", "rig", "operator",
        "forecast24hr", "drill_complete", "sum24Hr", "report_no", "schema_version", "n_rig_npd_name", "n_activity"]
df = pd.DataFrame(rows)[cols].astype("string")
os.makedirs("data/interim", exist_ok=True)
df.to_parquet("data/interim/ddr.parquet", index=False)
print(len(df), "rows")
print(df.schema_version.value_counts(dropna=False).to_dict())
print("null counts:", df.isna().sum()[lambda s: s > 0].to_dict())
print("rig alias counts:", df.n_rig_npd_name.value_counts().to_dict())
