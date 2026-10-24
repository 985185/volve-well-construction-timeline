"""Run the whole pipeline from the repository root, in stage order, from a clean clone.

Inputs needed: (a) the Volve DDR XML in data/raw/ddr_xml/, (b) the NOD wellbore snapshot of 2026-10-24 in data/raw/nod/
(wellbore_development_all_20261024.csv and wellbore_exploration_all_20261024.csv), (c) the files tracked in this repository.

Steps marked optional compare the rerun with the author's earlier Databricks tables or catalog. They print a SKIPPED message and exit 0 when
those files are not available, and no reported number depends on running them: the registry reads their committed results.
Usage:  python -X utf8 src/run_pipeline.py            (all steps)
        python -X utf8 src/run_pipeline.py --through 9  (stop after stage 9)
"""
import os
import subprocess
import sys
import time

# (stage, script, optional)
STEPS = [
    (1, "stage1_expected.py", True), (1, "stage1_manifest.py", False), (1, "stage1_nod.py", False),
    (2, "stage2_extract.py", False), (2, "stage2_diff.py", True), (2, "stage2_text_diff.py", True),
    (3, "stage3_quality.py", False),
    (4, "stage4_faithfulness.py", True), (4, "stage4_classify.py", False), (4, "stage4_rules_table.py", False),
    (5, "stage5_timeline.py", False),
    (6, "stage6_prepare.py", False), (6, "stage6_publish_adjudications.py", True), (6, "stage6_estimates.py", False),
    (7, "stage7_td.py", False), (7, "stage7_spud.py", False),
    (8, "stage8_f1c.py", False), (8, "stage8_kickoff.py", False), (8, "stage8b_kickoff_table.py", False), (8, "stage8d_apply_signoff.py", False),
    (9, "stage9_duration.py", False),
    (10, "stage10_fig2_index.py", False), (10, "figure1_depth_vs_time.py", False), (10, "figure2_days_vs_depth.py", False),
    (10, "figure3_td_validation.py", False), (10, "figure4_spud_offset.py", False),
    (11, "stage11_registry.py", False),
    (12, "stage12_manuscript.py", False), (12, "stage12_changes.py", False), (12, "stage12_check.py", False),
]
through = int(sys.argv[sys.argv.index("--through") + 1]) if "--through" in sys.argv else 99
for d in ("data/interim", "data/raw/nod", "outputs/figures", "manuscript"):
    os.makedirs(d, exist_ok=True)
if not os.path.isdir("data/raw/ddr_xml") or not os.listdir("data/raw/ddr_xml"):
    sys.exit("data/raw/ddr_xml/ is empty: place the Volve DDR XML files there first (see README).")
os.makedirs("local_private", exist_ok=True)
log = []
for stage, script, optional in STEPS:
    if stage > through: break
    t0 = time.time()
    r = subprocess.run([sys.executable, "-X", "utf8", f"src/{script}"], capture_output=True, text=True, encoding="utf-8")
    skipped = r.returncode == 0 and "SKIPPED" in r.stdout
    status = ("skipped (optional)" if optional else "ok, optional part skipped") if skipped else ("ok" if r.returncode == 0 else f"FAILED (exit {r.returncode})")
    print(f"[stage {stage:>2}] {script:<34} {status:<26} {time.time() - t0:5.1f} s")
    if skipped: print("           " + next(l for l in r.stdout.splitlines() if "SKIPPED" in l)[:200])
    log.append((script, status))
    if r.returncode != 0:
        print(r.stdout[-1500:], r.stderr[-2500:])
        sys.exit(1)
print(f"done: {sum(s.startswith('ok') for _, s in log)} steps ok, {sum(s.startswith('skipped') for _, s in log)} optional steps skipped entirely")
