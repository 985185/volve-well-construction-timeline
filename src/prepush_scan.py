"""Pre-push scan of every tracked file. Run from the repository root:  python -X utf8 src/prepush_scan.py
Exit code 1 if any finding.

(a) narrative text in DATA files (csv, xlsx, json): a column named sum24Hr or forecast24hr, or a quoted span of more than 15 words
    (an ellipsis is not a word, decision 53). Quotations in manuscript/*.docx and manuscript/*.pdf are exempt (decision 67): the limit is for data files.
(b) secrets and identifiers in every tracked file: tokens, keys, private-key headers, MCP server configs, and the author's email address and Databricks workspace host (read from local_private/env_notes.md when present).
(c) tracked files over 50 MB; tracked files under data/raw, data/interim, local_private, inputs/databricks_export.
"""
import json
import os
import re
import subprocess
import sys
import zipfile

import openpyxl
import pandas as pd

files = subprocess.run(["git", "ls-files"], capture_output=True, text=True, encoding="utf-8").stdout.splitlines()
COLS = re.compile(r"^(sum24hr|forecast24hr)$", re.I)
DQ = re.compile(r"(?<![\w.,;:!?/])\"(?=[A-Za-z])([^\"]*?)\"(?=[\s.,;:)]|$)|“([^”]*)”")      # a double quote after a digit is an inch mark, not an opening quotation mark
SQ = re.compile(r"(?<![\w.,;:!?])'([^']{20,}?)'(?=[\s.,;:)]|$)")
SECRET = re.compile(r"dapi[0-9a-f]{20,}|ghp_[A-Za-z0-9]{20,}|github_pat_\w{20,}|sk-[A-Za-z0-9_-]{20,}|xox[bap]-[\w-]{10,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY|"
                    r"(?i:(?:token|secret|password|passwd|api[_-]?key|bearer)\s*[:=]\s*[\"']?[A-Za-z0-9_\-./+=]{16,})|mcpServers")
# the author's email address and workspace host are read from the gitignored local notes (never written in a tracked file)
LOCAL = []
if os.path.exists("local_private/env_notes.md"):
    LOCAL = re.findall(r"<(?:workspace-host|user-email)>` = `([^`]+)`", open("local_private/env_notes.md", encoding="utf-8").read())
    LOCAL += [v.split(".")[0] for v in LOCAL if "databricks" in v]
FORBIDDEN_DIRS = ("data/raw/", "data/interim/", "local_private/", "inputs/databricks_export/")
findings = {"a_columns": [], "a_long_quotes": [], "b_secrets": [], "c_big_or_forbidden": []}


def words(span):
    return len([w for w in span.split() if w.strip(".…")])


def quotes(f, loc, t):
    for rx in (DQ, SQ):
        for m in rx.finditer(t):
            span = next((g for g in m.groups() if g is not None), "")
            if words(span) > 15: findings["a_long_quotes"].append((f, loc, words(span), span[:80]))


def walk(f, o, path=""):
    if isinstance(o, str): quotes(f, path, o)
    elif isinstance(o, dict):
        for k, v in o.items(): walk(f, v, f"{path}/{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o): walk(f, v, f"{path}[{i}]")


def raw_texts(f):
    low = f.lower()
    if low.endswith((".png", ".parquet", ".pdf")): return
    if low.endswith((".docx", ".xlsx")):
        for n in zipfile.ZipFile(f).namelist():
            yield zipfile.ZipFile(f).read(n).decode("utf-8", errors="replace")
    else:
        yield open(f, "rb").read().decode("utf-8", errors="replace")


for f in files:
    if os.path.getsize(f) > 50 * 1024 * 1024 or f.startswith(FORBIDDEN_DIRS): findings["c_big_or_forbidden"].append(f)
    if os.path.basename(f) in ("claude_desktop_config.json", ".mcp.json", ".databrickscfg", ".env") or f.startswith(".claude/"): findings["b_secrets"].append((f, "configuration file tracked"))
    for t in ([] if f == "src/prepush_scan.py" else raw_texts(f)):      # the scan script holds the patterns themselves
        m = SECRET.search(t)
        if m: findings["b_secrets"].append((f, m.group(0)[:40]))
        for v in LOCAL:
            if v in t: findings["b_secrets"].append((f, "local identifier (see local_private/env_notes.md)"))
    low = f.lower()
    if low.endswith(".json"): walk(f, json.load(open(f, encoding="utf-8")))
    elif low.endswith(".csv"):
        df = pd.read_csv(f, dtype=str, keep_default_na=False, encoding="utf-8-sig")
        findings["a_columns"] += [(f, c) for c in df.columns if COLS.match(c)]
        for c in df.columns:
            for i, v in enumerate(df[c]): quotes(f, f"{c}[{i}]", v)
    elif low.endswith(".xlsx"):
        for ws in openpyxl.load_workbook(f, read_only=True):
            for r, row in enumerate(ws.iter_rows(values_only=True), 1):
                if r == 1: findings["a_columns"] += [(f, str(c)) for c in row if c and COLS.match(str(c))]
                for c, v in enumerate(row):
                    if isinstance(v, str): quotes(f, f"{ws.title}!r{r}c{c}", v)
n_exempt = sum(1 for f in files if f.startswith("manuscript/") and f.lower().endswith((".docx", ".pdf")))
print(f"{len(files)} tracked files scanned; {n_exempt} manuscript docx/pdf exempt from the quote-length check (decision 67)")
for k, v in findings.items():
    print(f"{k}: {len(v)}")
    for x in v[:20]: print("   ", x)
sys.exit(1 if any(findings.values()) else 0)
