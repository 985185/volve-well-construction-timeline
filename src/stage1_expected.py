"""Stage 1a: pull the expected DDR XML file list (name, bytes, rel_path) from the metadata catalog."""
import csv, json, subprocess, sys

STMT = ("SELECT file_name, file_size_bytes, rel_path FROM workspace.default.volve_metadata_catalog "
        "WHERE file_name RLIKE '_[0-9]{4}_[0-9]{2}_[0-9]{2}\\.xml$' ORDER BY file_name")
body = {"warehouse_id": "187078b1fdfb9a56", "wait_timeout": "50s", "statement": STMT}
out = subprocess.run(["databricks", "api", "post", "/api/2.0/sql/statements", "--profile", "volve",
                      "--json", json.dumps(body)], capture_output=True, text=True, check=True).stdout
d = json.loads(out)
assert d["status"]["state"] == "SUCCEEDED", d["status"]
assert not d["manifest"]["truncated"] and d["manifest"]["total_chunk_count"] == 1
rows = d["result"]["data_array"]
with open("data/raw/expected_from_catalog.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["file_name", "bytes", "rel_path"]); w.writerows(rows)
print(len(rows), sum(int(r[1]) for r in rows))
