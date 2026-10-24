"""Stage 4a: export workspace.default.volve_ddr_classified once (comparison only)."""
import json, subprocess
import pandas as pd
body = {"warehouse_id": "187078b1fdfb9a56", "wait_timeout": "50s", "statement": "SELECT * FROM workspace.default.volve_ddr_classified ORDER BY filename"}
d = json.loads(subprocess.run(["databricks", "api", "post", "/api/2.0/sql/statements", "--profile", "volve", "--json", json.dumps(body)], capture_output=True, text=True, check=True).stdout)
assert d["status"]["state"] == "SUCCEEDED" and d["manifest"]["total_chunk_count"] == 1
cols = [c["name"] for c in d["manifest"]["schema"]["columns"]]
df = pd.DataFrame(d["result"]["data_array"], columns=cols, dtype="string")
df.to_parquet("data/interim/old/volve_ddr_classified.parquet", index=False); print(len(df), cols)
