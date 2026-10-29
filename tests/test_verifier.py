from __future__ import annotations
import csv
from pathlib import Path
import pytest
import verify_submission as verifier

ROOT = Path(__file__).resolve().parents[1]


def read_rows(relative):
    with (ROOT / relative).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_duplicate_raw_seed_key_is_rejected():
    rows = [
        {"N": "4", "g": "0.25", "layers": "1", "seed": "0"},
        {"N": "4", "g": "0.25", "layers": "1", "seed": "0"},
    ]
    with pytest.raises(AssertionError, match="duplicate key"):
        verifier.validate_raw_grid(rows)


def test_nonfinite_required_numeric_field_is_rejected_with_location():
    with pytest.raises(AssertionError, match=r"fixture.csv:2: energy is non-finite"):
        verifier.require_finite_columns([{"energy": "NaN"}], {"energy"}, "fixture.csv")


def test_duplicate_aggregate_row_is_rejected():
    aggregates = read_rows("results/tables/s1_results.csv")
    raw = read_rows("results/raw/s1_seed_runs.csv")
    exact = read_rows("results/tables/s1_exact_reference.csv")
    layer = read_rows("results/tables/layer_study.csv")
    aggregates.append(dict(aggregates[0]))
    raw_index = {(int(r["N"]), float(r["g"]), int(r["layers"]), int(r["seed"])): r for r in raw}
    exact_index = {(float(r["g"]),): r for r in exact}
    with pytest.raises(AssertionError, match="duplicate key"):
        verifier.validate_aggregates(aggregates, raw_index, exact_index, layer)


def test_aggregate_must_match_best_raw_seed():
    aggregates = read_rows("results/tables/s1_results.csv")
    raw = read_rows("results/raw/s1_seed_runs.csv")
    exact = read_rows("results/tables/s1_exact_reference.csv")
    layer = read_rows("results/tables/layer_study.csv")
    aggregates[0]["best_energy"] = str(float(aggregates[0]["best_energy"]) + 0.1)
    raw_index = {(int(r["N"]), float(r["g"]), int(r["layers"]), int(r["seed"])): r for r in raw}
    exact_index = {(float(r["g"]),): r for r in exact}
    with pytest.raises(AssertionError, match="best_energy not from minimum-energy seed"):
        verifier.validate_aggregates(aggregates, raw_index, exact_index, layer)


def test_official_template_schemas_are_parsed():
    source = ROOT / "handoff_payload/OFFICIAL_KIT/templates/results_columns.md"
    schemas = verifier.parse_template_schemas(source.read_text(encoding="utf-8"))
    assert schemas["bell.csv"] == ["pair", "pair_distance", "condition", "two_qubit_gates", "XX", "XX_se", "YY", "YY_se", "ZZ", "ZZ_se", "fidelity", "fidelity_se"]
    assert "s1_results.csv" in schemas and "s1_noisy.csv" in schemas
