"""Stage 2a: export workspace.default.volve_ddr_master once, as strings, to data/interim/old/ (comparison only)."""
import json, subprocess
import pandas as pd

def sql(stmt):
    body = {"warehouse_id": "187078b1fdfb9a56", "wait_timeout": "50s", "disposition": "INLINE", "format": "JSON_ARRAY", "statement": stmt}
    out = subprocess.run(["databricks", "api", "post", "/api/2.0/sql/statements", "--profile", "volve", "--json", json.dumps(body)],
                         capture_output=True, text=True, check=True).stdout
    d = json.loads(out); assert d["status"]["state"] == "SUCCEEDED", d["status"]
    cols = [c["name"] for c in d["manifest"]["schema"]["columns"]]
    rows = list(d["result"].get("data_array", []))
    return cols, rows, d["manifest"]["total_chunk_count"]

cols, rows, nch = sql("SELECT * FROM workspace.default.volve_ddr_master ORDER BY filename")
print(len(rows), "rows in chunk 0 of", nch)
assert nch == 1
pd.DataFrame(rows, columns=cols, dtype="string").to_parquet("data/interim/old/volve_ddr_master.parquet", index=False)
