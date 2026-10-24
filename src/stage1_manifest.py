"""Stage 1b: verify downloaded DDR XML against the catalog and write data/raw/manifest.csv (path, sha256, bytes)."""
import csv, hashlib, os

RAW = "data/raw/ddr_xml"
exp = {r["file_name"]: int(r["bytes"]) for r in csv.DictReader(open("data/raw/expected_from_catalog.csv", encoding="utf-8"))}
got = {}
rows = []
for n in sorted(os.listdir(RAW)):
    p = os.path.join(RAW, n)
    b = open(p, "rb").read()
    got[n] = len(b)
    rows.append((p.replace("\\", "/"), hashlib.sha256(b).hexdigest(), len(b), b.lstrip(b"\xef\xbb\xbf")[:1] == b"<"))
print("expected files/bytes:", len(exp), sum(exp.values()))
print("got files/bytes:     ", len(got), sum(got.values()))
print("missing:", sorted(set(exp) - set(got))[:5], "extra:", sorted(set(got) - set(exp))[:5])
diff = [(n, exp[n], got[n]) for n in got if n in exp and exp[n] != got[n]]
print("size mismatches:", len(diff), diff[:5])
print("not starting with '<':", [r[0] for r in rows if not r[3]][:5])
with open("data/raw/manifest.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["path", "sha256", "bytes"])
    w.writerows((r[0], r[1], r[2]) for r in rows)
print("distinct sha256:", len({r[1] for r in rows}))
