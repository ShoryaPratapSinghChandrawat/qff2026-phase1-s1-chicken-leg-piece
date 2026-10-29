import csv
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def table(name):
    with (ROOT / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def test_full_submission_validator():
    result = subprocess.run([sys.executable, "verify_submission.py"], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS: official manifest/work-copy hashes=25/25" in result.stdout

def test_all_required_seed_starts_preserved():
    rows = table("results/raw/s1_seed_runs.csv")
    assert len(rows) == 84
    assert {(float(r["g"]), int(r["layers"]), int(r["seed"])) for r in rows} == {
        (g, layer, seed)
        for g in (0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0)
        for layer in (1, 2, 3, 4)
        for seed in (0, 1, 2)
    }

def test_minimum_depth_threshold_results():
    rows = table("results/tables/layer_study.csv")
    got = {}
    for g in (0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0):
        candidates = [r for r in rows if float(r["g"]) == g and float(r["abs_energy_err"]) < 1e-3]
        got[g] = min(int(r["layers"]) for r in candidates) if candidates else None
    assert got == {0.25: 4, 0.5: 4, 0.75: 4, 1.0: 3, 1.25: 4, 1.5: 3, 2.0: 3}
