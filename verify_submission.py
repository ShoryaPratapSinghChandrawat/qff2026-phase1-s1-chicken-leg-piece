#!/usr/bin/env python3
"""Strict local PS-S1 N=4 validation against the embedded official kit.

This verifier validates saved outputs; it never launches the VQE sweep or a
Bell shot experiment. Density-matrix checks are limited to the three saved
required noisy-D circuits.
"""
from __future__ import annotations
import csv
import hashlib
import json
import math
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from scipy.sparse.linalg import eigsh
from qiskit_aer import AerSimulator
from qiskit.quantum_info import DensityMatrix, SparsePauliOp, Statevector, partial_trace, state_fidelity

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import qff_sim as sim  # noqa: E402

G = (0.25, 0.50, 0.75, 1.00, 1.25, 1.50, 2.00)
LAYERS = (1, 2, 3, 4)
SEEDS = (0, 1, 2)
TOL = 2e-9
EXPECTED_EXTRA_HEADERS = {
    "s1_exact_reference.csv": ["N", "g", "exact_E0", "exact_E1", "E0_metadata", "E1_metadata",
        "E0_abs_diff", "E1_abs_diff", "mx_exact", "czz_nn_exact", "mz2_exact", "mz_exact"],
    "layer_study.csv": ["g", "layers", "best_seed", "best_energy", "energy_err", "abs_energy_err",
        "any_seed_success", "optimizer_calls_winner"],
}
NUMERIC_COLUMNS = {
    "bell.csv": {"pair_distance", "two_qubit_gates", "XX", "XX_se", "YY", "YY_se", "ZZ", "ZZ_se", "fidelity", "fidelity_se"},
    "resources.csv": {"logical_qubits", "physical_qubits", "logical_2q", "two_q", "depth", "two_q_depth", "swaps", "routing_overhead_2q"},
    "s1_results.csv": {"N", "g", "layers", "best_energy", "exact_E0", "energy_err", "fidelity", "fidelity_2", "mx", "mx_exact", "czz_nn", "czz_nn_exact", "mz2", "mz2_exact", "mz", "optimizer_calls", "n_params", "two_q_on_D"},
    "s1_noisy.csv": {"g", "layers", "mx_noisy", "czz_nn_noisy", "mz2_noisy", "energy_noisy", "fidelity_noisy_dm"},
    "s1_exact_reference.csv": {"N", "g", "exact_E0", "exact_E1", "E0_metadata", "E1_metadata", "E0_abs_diff", "E1_abs_diff", "mx_exact", "czz_nn_exact", "mz2_exact", "mz_exact"},
    "layer_study.csv": {"g", "layers", "best_seed", "best_energy", "energy_err", "abs_energy_err", "optimizer_calls_winner"},
}
RAW_NUMERIC = {"N", "g", "layers", "seed", "energy", "exact_E0", "energy_err", "fidelity", "fidelity_2", "mx", "czz_nn", "mz2", "mz", "optimizer_calls", "n_params", "two_q_on_D", "status", "runtime_seconds"}
RAW_REQUIRED = ["N", "g", "layers", "seed", "energy", "exact_E0", "energy_err", "fidelity", "fidelity_2", "mx", "czz_nn", "mz2", "mz", "optimizer_calls", "n_params", "two_q_on_D", "success", "status", "message", "runtime_seconds", "theta_json"]

ADDITIONAL_SCHEMAS = {
    "s1_n6_seed_runs.csv": ["N", "g", "layers", "seed", "energy", "exact_E0", "exact_E1", "energy_err", "fidelity", "fidelity_2", "mx", "czz_nn", "mz2", "mz", "optimizer_calls", "n_params", "success", "status", "message", "runtime_seconds", "theta_json"],
    "s1_n6_exact_reference.csv": ["N", "g", "exact_E0", "exact_E1", "E0_metadata", "E1_metadata", "E0_abs_diff", "E1_abs_diff", "mx_exact", "czz_nn_exact", "mz2_exact", "mz_exact"],
    "s1_n6_results.csv": ["N", "g", "layers", "best_seed", "best_energy", "exact_E0", "energy_err", "fidelity", "fidelity_2", "mx", "mx_exact", "czz_nn", "czz_nn_exact", "mz2", "mz2_exact", "mz", "optimizer_calls", "n_params"],
    "s1_n6_layer_study.csv": ["N", "g", "layers", "best_seed", "best_energy", "energy_err", "abs_energy_err", "any_seed_success", "optimizer_calls_winner"],
    "s1_n6_minimal_layers.csv": ["scope", "N", "g", "minimal_L_abs_err_lt_1e-3", "threshold_met_within_L1_to_L8", "selected_seed", "selected_L", "selected_energy_error", "selected_optimizer_success", "failed_starts_at_selected_L", "selection_rule"],
    "s1_n6_resources.csv": ["scope", "circuit_label", "N", "g", "layers", "seed", "selection_status", "processor", "zz_mode", "executable", "reason", "logical_qubits", "physical_qubits", "logical_2q", "two_q", "depth", "two_q_depth", "swaps", "routing_overhead_2q", "selected_energy_error", "optimizer_success"],
    "finite_size_scaling.csv": ["scope", "solver", "N", "g", "E0_sparse", "E1_sparse", "gap", "gap_times_N", "half_chain_entropy_bits", "mz2_over_N2", "reference_checked", "E0_metadata", "E1_metadata", "E0_abs_diff", "E1_abs_diff", "eigsh_tolerance", "deterministic_v0_seed"],
    "finite_size_crossings.csv": ["scope", "quantity", "N_small", "N_large", "g_crossing_linear_interpolation", "status"],
    "mitigation_d_results.csv": ["scope", "g", "layers", "seed", "observable", "ideal_selected_circuit_target", "target_definition", "alpha_p2_scales", "p1_fixed", "p2_baseline", "p_readout_fixed", "shots_per_basis_per_scale", "bootstrap_replicates", "readout_calibration_model", "raw_value", "raw_se", "raw_abs_error", "readout_corrected_value", "readout_corrected_se", "readout_corrected_abs_error", "zne_value", "zne_se", "zne_abs_error", "zne_readout_corrected_value", "zne_readout_corrected_se", "zne_readout_corrected_abs_error"],
    "mitigation_d_costs.csv": ["scope", "data_experiment", "official_baseline_data_circuits_at_alpha_1", "additional_p2_scale_data_circuits_at_alpha_1_5_and_2", "readout_calibration_circuits_reused", "total_unique_data_circuits", "total_unique_circuits_including_calibration", "shots_per_circuit", "baseline_data_shots_at_alpha_1", "additional_shots_for_p2_scales", "readout_calibration_shots", "total_data_and_calibration_shots", "extra_circuits_vs_raw_alpha_1", "extra_shots_vs_raw_alpha_1", "calibration_reuse", "noise_settings"],
}

ADDITIONAL_SCOPE = "additional, not part of the official required results"
N6_G = (0.25, 0.50, 0.75, 1.00, 1.25, 1.50, 2.00)
G_EXTEND = {0.5, 0.75, 1.0}
N6_LAYERS_BASE = tuple(range(1, 9))
N6_LAYERS_EXT = tuple(range(1, 13))


def n6_layers_for_g(g: float) -> tuple[int, ...]:
    return N6_LAYERS_EXT if round(float(g), 2) in G_EXTEND else N6_LAYERS_BASE


FINITE_SIZES = (4, 6, 8, 10, 12)
FINITE_G = tuple(round(0.25 + 0.05 * i, 2) for i in range(36))
MITIGATION_G = (0.5, 1.0, 2.0)
MITIGATION_OBSERVABLES = ("energy", "mx", "czz_nn", "mz2", "mz")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def close(actual, expected, tol: float, label: str) -> None:
    require(math.isfinite(float(actual)), f"{label}: non-finite actual value {actual!r}")
    require(math.isfinite(float(expected)), f"{label}: non-finite expected value {expected!r}")
    require(abs(float(actual) - float(expected)) <= tol,
            f"{label}: got {actual}, expected {expected} (tolerance {tol})")


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    require(path.is_file(), f"missing required file: {path.relative_to(ROOT)}")
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        require(reader.fieldnames is not None, f"{path.relative_to(ROOT)}: missing CSV header")
        return list(reader.fieldnames), list(reader)


def parse_template_schemas(text: str) -> dict[str, list[str]]:
    """Extract required output column names from the official Markdown schema."""
    schemas: dict[str, list[str]] = {}
    for line in text.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 3:
            continue
        match = re.search(r"`([^`]+\.csv)`", cells[0])
        if not match:
            continue
        columns = []
        for item in cells[2].split(","):
            name = item.strip().split("(", 1)[0].strip()
            if name:
                columns.append(name)
        schemas[match.group(1)] = columns
    return schemas


def require_unique(rows: list[dict], key_fn, label: str) -> dict[tuple, dict]:
    indexed: dict[tuple, dict] = {}
    for row_number, row in enumerate(rows, start=2):
        key = key_fn(row)
        require(key not in indexed, f"{label}:{row_number}: duplicate key {key}")
        indexed[key] = row
    return indexed


def require_finite_columns(rows: list[dict], columns: set[str], label: str) -> None:
    for row_number, row in enumerate(rows, start=2):
        for column in columns:
            value = row.get(column)
            require(value is not None and str(value).strip() != "",
                    f"{label}:{row_number}: blank required numeric field {column}")
            try:
                number = float(value)
            except (TypeError, ValueError):
                raise AssertionError(f"{label}:{row_number}: {column} is not numeric: {value!r}")
            require(math.isfinite(number), f"{label}:{row_number}: {column} is non-finite: {value!r}")


def verify_manifest() -> int:
    source = ROOT / "handoff_payload/OFFICIAL_KIT"
    manifest = source / "MANIFEST.sha256"
    require(manifest.is_file(), "missing official source manifest handoff_payload/OFFICIAL_KIT/MANIFEST.sha256")
    checked = 0
    for line_no, line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        parts = line.split("  ", 1)
        require(len(parts) == 2, f"official manifest line {line_no}: expected '<sha256>  <path>'")
        expected, rel = parts
        path = Path(rel)
        require(not path.is_absolute() and ".." not in path.parts,
                f"official manifest line {line_no}: unsafe path {rel!r}")
        source_file = source / path
        require(source_file.is_file(), f"official payload missing: {rel}")
        digest = hashlib.sha256(source_file.read_bytes()).hexdigest()
        require(digest == expected, f"official payload hash mismatch: {rel}")
        destination = (ROOT / "reference/official-kit/README.md") if rel == "README.md" else ROOT / path
        require(destination.is_file(), f"official work-copy missing: {destination.relative_to(ROOT)}")
        copy_digest = hashlib.sha256(destination.read_bytes()).hexdigest()
        require(copy_digest == expected,
                f"official work-copy hash mismatch: {destination.relative_to(ROOT)} (source {rel})")
        checked += 1
    require(checked == 25, f"official manifest expected 25 entries, found {checked}")
    return checked


def validate_raw_grid(raw: list[dict[str, str]]) -> dict[tuple[int, float, int, int], dict[str, str]]:
    label = "results/raw/s1_seed_runs.csv"
    keys = require_unique(raw, lambda r: (int(r["N"]), float(r["g"]), int(r["layers"]), int(r["seed"])), label)
    expected = {(4, g, layer, seed) for g in G for layer in LAYERS for seed in SEEDS}
    require(set(keys) == expected,
            f"{label}: expected exact (N,g,layers,seed) grid of {len(expected)} rows; "
            f"missing={sorted(expected-set(keys))[:5]}, unexpected={sorted(set(keys)-expected)[:5]}")
    for row_number, row in enumerate(raw, 2):
        for column in RAW_NUMERIC:
            try:
                value = float(row[column])
            except (ValueError, TypeError, KeyError):
                raise AssertionError(f"{label}:{row_number}: invalid numeric field {column}={row.get(column)!r}")
            require(math.isfinite(value), f"{label}:{row_number}: non-finite {column}")
        require(int(row["n_params"]) == 2 * int(row["layers"]),
                f"{label}:{row_number}: n_params={row['n_params']} but HVA requires 2*layers")
        require(int(row["optimizer_calls"]) > 0, f"{label}:{row_number}: optimizer_calls must be positive")
        require(float(row["runtime_seconds"]) >= 0, f"{label}:{row_number}: negative runtime_seconds")
        require(str(row["success"]).lower() in {"true", "false", "1", "0"},
                f"{label}:{row_number}: invalid success flag {row['success']!r}")
        if str(row["success"]).lower() in {"false", "0"}:
            require(row.get("message", "").strip(),
                    f"{label}:{row_number}: non-converged run lacks its termination message")
        try:
            theta = json.loads(row["theta_json"])
        except (json.JSONDecodeError, TypeError) as exc:
            raise AssertionError(f"{label}:{row_number}: invalid theta_json: {exc}")
        require(isinstance(theta, list) and len(theta) == 2 * int(row["layers"]),
                f"{label}:{row_number}: theta_json must contain 2*layers parameters")
        require(all(math.isfinite(float(value)) for value in theta),
                f"{label}:{row_number}: theta_json contains non-finite parameter")
    return keys


def independently_check_exact_and_raw(raw: list[dict[str, str]], exact_rows: list[dict[str, str]]) -> dict[float, tuple]:
    exact_by_g = require_unique(exact_rows, lambda r: (float(r["g"]),), "results/tables/s1_exact_reference.csv")
    require(set(g for (g,) in exact_by_g) == set(G), "s1_exact_reference.csv: expected all seven locked g values")
    references = {}
    for g in G:
        instance_path = ROOT / "data/s1" / f"tfim_open_N4_g{g:.2f}.json"
        require(instance_path.is_file(), f"missing official S1 instance: {instance_path.relative_to(ROOT)}")
        instance = json.loads(instance_path.read_text(encoding="utf-8"))
        hamiltonian = SparsePauliOp.from_list([(label, float(coef)) for label, coef in instance["operator"]])
        constructed_open_chain = sim.tfim_hamiltonian(4, J=1.0, g=g, periodic=False)
        require(np.allclose(hamiltonian.to_matrix(), constructed_open_chain.to_matrix(), atol=1e-12, rtol=0),
                f"{instance_path.name}: locked operator does not match open-chain TFIM convention")
        values, states = sim.exact_spectrum(hamiltonian, 2)
        e0, e1 = float(values[0]), float(values[1])
        close(e0, instance["meta"]["E0_exact"], 1e-9, f"{instance_path.name}: exact E0 metadata")
        close(e1, instance["meta"]["E1_exact"], 1e-9, f"{instance_path.name}: exact E1 metadata")
        record = exact_by_g[(g,)]
        close(record["exact_E0"], e0, 1e-9, f"s1_exact_reference.csv g={g}: exact_E0")
        close(record["exact_E1"], e1, 1e-9, f"s1_exact_reference.csv g={g}: exact_E1")
        close(record["E0_metadata"], instance["meta"]["E0_exact"], 1e-12,
              f"s1_exact_reference.csv g={g}: E0_metadata")
        close(record["E1_metadata"], instance["meta"]["E1_exact"], 1e-12,
              f"s1_exact_reference.csv g={g}: E1_metadata")
        close(record["E0_abs_diff"], abs(e0-float(instance["meta"]["E0_exact"])), 1e-9,
              f"s1_exact_reference.csv g={g}: E0_abs_diff")
        close(record["E1_abs_diff"], abs(e1-float(instance["meta"]["E1_exact"])), 1e-9,
              f"s1_exact_reference.csv g={g}: E1_abs_diff")
        ops = sim.observable_ops(4)
        exact_obs = sim.expectations(states[0], ops)
        for field, key in (("mx_exact", "mx"), ("czz_nn_exact", "czz_nn"), ("mz2_exact", "mz2"), ("mz_exact", "mz")):
            close(record[field], exact_obs[key], TOL, f"s1_exact_reference.csv g={g}: {field}")
        references[g] = (hamiltonian, values, states, exact_obs)
    for row_number, row in enumerate(raw, 2):
        g, layer = float(row["g"]), int(row["layers"])
        hamiltonian, values, states, _ = references[g]
        parameters = json.loads(row["theta_json"])
        circuit, params = sim.hva_ansatz(4, layer, zz_mode="cx")
        state = Statevector(circuit.assign_parameters(dict(zip(params, parameters))))
        energy = float(np.real(state.expectation_value(hamiltonian)))
        label = f"results/raw/s1_seed_runs.csv:{row_number} g={g} L={layer} seed={row['seed']}"
        close(row["energy"], energy, TOL, f"{label}: energy")
        close(row["exact_E0"], values[0], 1e-9, f"{label}: exact_E0")
        close(row["energy_err"], energy-float(values[0]), TOL, f"{label}: energy_err")
        require(float(row["energy_err"]) >= -1e-9, f"{label}: energy below exact-reference tolerance")
        fidelity = float(state_fidelity(states[0], state))
        fidelity2 = fidelity + float(state_fidelity(states[1], state))
        close(row["fidelity"], fidelity, TOL, f"{label}: fidelity")
        close(row["fidelity_2"], fidelity2, TOL, f"{label}: fidelity_2")
        require(-1e-12 <= fidelity <= 1 + 1e-12,
                f"{label}: fidelity outside [0,1]")
        require(-1e-12 <= fidelity2 <= 1 + 1e-12,
                f"{label}: fidelity_2 outside [0,1]")
        obs = sim.expectations(state, sim.observable_ops(4))
        for key in ("mx", "czz_nn", "mz2", "mz"):
            close(row[key], obs[key], TOL, f"{label}: {key}")
    return references


def validate_aggregates(aggregates, raw_index, exact_by_g, layer_rows):
    label = "results/tables/s1_results.csv"
    aggregate_index = require_unique(aggregates,
        lambda r: (int(r["N"]), float(r["g"]), int(r["layers"])), label)
    expected = {(4, g, layer) for g in G for layer in LAYERS}
    require(set(aggregate_index) == expected,
            f"{label}: aggregate coverage/duplicate mismatch; expected {len(expected)} unique N/g/L rows")
    layer_index = require_unique(layer_rows, lambda r: (float(r["g"]), int(r["layers"])),
                                 "results/tables/layer_study.csv")
    require(set(layer_index) == {(g, layer) for g in G for layer in LAYERS},
            "results/tables/layer_study.csv: expected 28 unique g/layers rows")
    field_map = {
        "best_energy": "energy", "exact_E0": "exact_E0", "energy_err": "energy_err",
        "fidelity": "fidelity", "fidelity_2": "fidelity_2", "mx": "mx", "czz_nn": "czz_nn",
        "mz2": "mz2", "mz": "mz", "optimizer_calls": "optimizer_calls",
        "n_params": "n_params", "two_q_on_D": "two_q_on_D",
    }
    for key, aggregate in aggregate_index.items():
        _, g, layer = key
        starts = [raw_index[(4, g, layer, seed)] for seed in SEEDS]
        winner = min(starts, key=lambda r: float(r["energy"]))
        row_label = f"{label} N={key[0]} g={g} L={layer}"
        for aggregate_field, raw_field in field_map.items():
            close(aggregate[aggregate_field], winner[raw_field], TOL,
                  f"{row_label}: {aggregate_field} not from minimum-energy seed {winner['seed']}")
        exact = exact_by_g[(g,)]
        for field, exact_field in (("mx_exact", "mx_exact"), ("czz_nn_exact", "czz_nn_exact"), ("mz2_exact", "mz2_exact")):
            close(aggregate[field], exact[exact_field], TOL, f"{row_label}: {field} vs exact reference")
        layer_row = layer_index[(g, layer)]
        require(int(layer_row["best_seed"]) == int(winner["seed"]),
                f"results/tables/layer_study.csv g={g} L={layer}: best_seed does not match aggregate winner")
        close(layer_row["best_energy"], winner["energy"], TOL,
              f"results/tables/layer_study.csv g={g} L={layer}: best_energy")
        close(layer_row["energy_err"], winner["energy_err"], TOL,
              f"results/tables/layer_study.csv g={g} L={layer}: energy_err")
        close(layer_row["abs_energy_err"], abs(float(winner["energy_err"])), TOL,
              f"results/tables/layer_study.csv g={g} L={layer}: abs_energy_err")
        expected_success = any(str(r["success"]).lower() in {"true", "1"} for r in starts)
        require(str(layer_row["any_seed_success"]).lower() in {"true", "false", "1", "0"},
                f"results/tables/layer_study.csv g={g} L={layer}: invalid any_seed_success")
        actual_success = str(layer_row["any_seed_success"]).lower() in {"true", "1"}
        require(actual_success == expected_success,
                f"results/tables/layer_study.csv g={g} L={layer}: any_seed_success mismatch")
        require(int(layer_row["optimizer_calls_winner"]) == int(winner["optimizer_calls"]),
                f"results/tables/layer_study.csv g={g} L={layer}: optimizer_calls_winner mismatch")
    # The layer table must report the first tested L strictly below the official threshold.
    for g in G:
        qualifying = [layer for layer in LAYERS
                      if abs(float(aggregate_index[(4, g, layer)]["energy_err"])) < 1e-3]
        for layer in LAYERS:
            reported_error = abs(float(aggregate_index[(4, g, layer)]["energy_err"]))
            require(math.isfinite(reported_error), f"{label} g={g} L={layer}: non-finite energy error")
        require(qualifying, f"{label} g={g}: no tested layer meets strict |energy error| < 1e-3")
        print(f"PASS: minimum tested layer at g={g:.2f} for strict threshold is L={min(qualifying)}")


def validate_bell(bell_rows, processor):
    label = "results/tables/bell.csv"
    index = require_unique(bell_rows, lambda r: (r["pair"], r["condition"]), label)
    expected = {("0-1", "ideal"), ("0-1", "noisy"), ("1-4", "ideal"), ("1-4", "noisy")}
    require(set(index) == expected, f"{label}: expected the four adjacent/farthest × ideal/noisy rows")
    coupling = sim.coupling_map_from_edges(processor["edges"], processor["num_qubits"])
    expected_distances = {"0-1": coupling.distance(0, 1), "1-4": coupling.distance(1, 4)}
    require(expected_distances == {"0-1": 1, "1-4": 3},
            f"processors/processor_D.json: expected adjacent 0-1 and graph-farthest 1-4; got {expected_distances}")
    for (pair, condition), row in index.items():
        close(row["pair_distance"], expected_distances[pair], 0, f"{label} {pair}/{condition}: pair_distance")
        fidelity = (1 + float(row["XX"]) - float(row["YY"]) + float(row["ZZ"])) / 4
        fidelity_se = math.sqrt(sum(float(row[f"{basis}_se"])**2 for basis in ("XX", "YY", "ZZ"))) / 4
        close(row["fidelity"], fidelity, 1e-12, f"{label} {pair}/{condition}: fidelity equation")
        close(row["fidelity_se"], fidelity_se, 1e-12, f"{label} {pair}/{condition}: fidelity_se equation")
        require(0 <= float(row["fidelity"]) <= 1 + 1e-12,
                f"{label} {pair}/{condition}: fidelity outside [0,1]")
        if condition == "ideal":
            close(row["XX"], 1, 1e-12, f"{label} {pair}: ideal XX")
            close(row["YY"], -1, 1e-12, f"{label} {pair}: ideal YY")
            close(row["ZZ"], 1, 1e-12, f"{label} {pair}: ideal ZZ")
            close(row["fidelity"], 1, 1e-12, f"{label} {pair}: ideal fidelity")
    # The official schema has no shots column; verify the runner uses the locked shot count.
    runner = (ROOT / "src/run_bell.py").read_text(encoding="utf-8")
    require("shots=4096" in runner, "src/run_bell.py: expected 4096 shots per basis")


def validate_resources(resource_rows, raw_index, processor):
    label = "results/tables/resources.csv"
    index = require_unique(resource_rows,
        lambda r: (r["circuit_label"], r["processor"]), label)
    g, layer = 1.0, 3
    starts = [raw_index[(4, g, layer, seed)] for seed in SEEDS]
    winner = min(starts, key=lambda r: float(r["energy"]))
    base_label = f"s1_hva_g1.00_L3_best_seed{int(winner['seed'])}"
    expected = {(f"{base_label}_{mode}", p) for mode in ("cx", "rzz") for p in ("A", "B", "D")} | {
        ("bell_auto_layout_ZZ", p) for p in ("A", "B", "D")}
    require(set(index) == expected,
            f"{label}: expected CX/RZZ HVA and Bell auto-layout rows on A/B/D")
    theta = json.loads(winner["theta_json"])
    processors = (sim.PROCESSOR_A, sim.PROCESSOR_B, processor)
    compare_fields = {
        "logical_qubits": "logical_qubits", "physical_qubits": "physical_qubits",
        "logical_2q": "logical_cx", "two_q": "cx", "depth": "depth",
        "two_q_depth": "two_q_depth", "swaps": "swaps", "routing_overhead_2q": "cx_overhead",
    }
    for proc in processors:
        processor_name = proc["name"][-1]
        for mode in ("cx", "rzz"):
            circuit, params = sim.hva_ansatz(4, 3, zz_mode=mode)
            bound = circuit.assign_parameters(dict(zip(params, theta)))
            metrics = sim.circuit_metrics(bound, proc)
            row = index[(f"{base_label}_{mode}", processor_name)]
            row_label = f"{label} {base_label}_{mode}/{processor_name}"
            require(str(row["executable"]).lower() == "true", f"{row_label}: required circuit not executable")
            for out_col, metric_col in compare_fields.items():
                close(row[out_col], metrics[metric_col], 0, f"{row_label}: {out_col} vs official circuit_metrics")
        bell_metrics = sim.circuit_metrics(sim.bell_circuit("ZZ"), proc)
        row = index[("bell_auto_layout_ZZ", processor_name)]
        row_label = f"{label} bell_auto_layout_ZZ/{processor_name}"
        require(str(row["executable"]).lower() == "true", f"{row_label}: Bell circuit not executable")
        for out_col, metric_col in compare_fields.items():
            close(row[out_col], bell_metrics[metric_col], 0, f"{row_label}: {out_col} vs official circuit_metrics")


def validate_p2_processor_comparison(raw_index, processor_d, resource_rows):
    label = "results/additional/p2_processor_comparison.csv"
    path = ROOT / label
    header, rows = read_csv(path)
    expected_header = ["g", "layers", "seed", "processor", "logical_zz_mode", "alpha_p2",
        "p1", "p2", "p_readout", "energy_noisy", "exact_E0", "energy_error_noisy",
        "fidelity_noisy_dm", "two_q_gates", "two_q_depth", "depth", "swaps",
        "state_fidelity_gate_noise_only"]
    require(header == expected_header, f"{label}: unexpected schema {header}")
    require(len(rows) == 36, f"{label}: expected 36 rows, found {len(rows)}")
    key = lambda r: (float(r["g"]), r["processor"], float(r["alpha_p2"]))
    index = require_unique(rows, key, label)
    gs, alphas = (0.5, 1.0, 2.0), (1.0, 1.25, 1.5, 2.0)
    expected_keys = {(g, proc, alpha) for g in gs for proc in ("A", "B", "D") for alpha in alphas}
    require(set(index) == expected_keys, f"{label}: unexpected processor/g/alpha coverage")
    selections = json.loads((ROOT / "results/raw/s1_noisy_selection.json").read_text(encoding="utf-8"))
    processors = {"A": sim.PROCESSOR_A, "B": sim.PROCESSOR_B, "D": processor_d}
    resources = {(r["circuit_label"], r["processor"]): r for r in resource_rows}
    baseline_label = "s1_hva_g1.00_L3_best_seed2_rzz"
    require((baseline_label, "D") in resources, f"{label}: missing D RZZ resource row")
    for g in gs:
        selection = selections[str(g)]
        layers, seed = int(selection["layers"]), int(selection["seed"])
        raw = raw_index[(4, g, layers, seed)]
        theta = np.asarray(json.loads(raw["theta_json"]), dtype=float)
        require(np.allclose(theta, np.asarray(selection["theta"], dtype=float), atol=TOL, rtol=0),
                f"{label} g={g}: parameters differ from selected raw run")
        instance = json.loads((ROOT / "data/s1" / f"tfim_open_N4_g{g:.2f}.json").read_text(encoding="utf-8"))
        hamiltonian = SparsePauliOp.from_list([(pauli, float(coef)) for pauli, coef in instance["operator"]])
        eigvals, eigvecs = np.linalg.eigh(hamiltonian.to_matrix())
        exact_e0 = float(eigvals[0])
        exact_state = Statevector(eigvecs[:, 0])
        logical, params = sim.hva_ansatz(4, layers, zz_mode="rzz")
        bound = logical.assign_parameters(dict(zip(params, theta)))
        for proc_name, proc in processors.items():
            metrics = sim.circuit_metrics(bound, proc)
            for alpha in alphas:
                row = index[(g, proc_name, alpha)]
                row_label = f"{label} g={g}/{proc_name}/alpha={alpha}"
                require(int(row["layers"]) == layers and int(row["seed"]) == seed,
                        f"{row_label}: selected layer/seed mismatch")
                require(row["logical_zz_mode"] == "rzz", f"{row_label}: expected RZZ logical representation")
                for col, expected in (("p1", 0.001), ("p2", 0.005 * alpha), ("p_readout", 0.01)):
                    close(row[col], expected, 1e-15, f"{row_label}: {col}")
                close(row["exact_E0"], exact_e0, TOL, f"{row_label}: exact_E0")
                close(row["energy_error_noisy"], float(row["energy_noisy"]) - exact_e0,
                      TOL, f"{row_label}: energy_error_noisy")
                require(str(row["state_fidelity_gate_noise_only"]).lower() == "true",
                        f"{row_label}: density-matrix fidelity must be labelled gate-noise-only")
                for col, metric in (("two_q_gates", "cx"), ("two_q_depth", "two_q_depth"),
                                    ("depth", "depth"), ("swaps", "swaps")):
                    close(row[col], metrics[metric], 0, f"{row_label}: {col}")
                transpiled = sim.transpile_for(bound, proc)
                _, final_wires = sim._layout_maps(transpiled, bound.num_qubits)
                save = transpiled.copy()
                save.save_density_matrix(qubits=final_wires, label="rho")
                noise = sim.official_noise_model(p1=0.001, p2=0.005 * alpha, p_ro=0.01)
                backend = AerSimulator(method="density_matrix", noise_model=noise, seed_simulator=sim.SEED)
                density = DensityMatrix(backend.run(save).result().data()["rho"])
                energy = float(np.real(density.expectation_value(hamiltonian)))
                fidelity = float(state_fidelity(exact_state, density))
                close(row["energy_noisy"], energy, TOL, f"{row_label}: recomputed energy_noisy")
                close(row["fidelity_noisy_dm"], fidelity, TOL, f"{row_label}: recomputed gate-only fidelity")
    # Verify the alpha=1 D rows reproduce the official D-only noisy table.
    official_header, official_rows = read_csv(ROOT / "results/tables/s1_noisy.csv")
    official = {float(r["g"]): r for r in official_rows}
    for g in gs:
        row = index[(g, "D", 1.0)]
        close(row["energy_noisy"], official[g]["energy_noisy"], TOL, f"{label} g={g}: official D energy")
        close(row["fidelity_noisy_dm"], official[g]["fidelity_noisy_dm"], TOL, f"{label} g={g}: official D fidelity")
    # In this explicitly tested grid, D beats both CX processors on both reported metrics.
    for g in gs:
        for alpha in alphas:
            d = index[(g, "D", alpha)]
            for proc_name in ("A", "B"):
                other = index[(g, proc_name, alpha)]
                require(float(d["energy_error_noisy"]) < float(other["energy_error_noisy"]),
                        f"{label} g={g}/alpha={alpha}: Processor D energy error is not lower than {proc_name}")
                require(float(d["fidelity_noisy_dm"]) > float(other["fidelity_noisy_dm"]),
                        f"{label} g={g}/alpha={alpha}: Processor D fidelity is not higher than {proc_name}")


def validate_noisy(noisy_rows, raw, references, processor):
    label = "results/tables/s1_noisy.csv"
    index = require_unique(noisy_rows, lambda r: (float(r["g"]),), label)
    require(set(index) == {(0.5,), (1.0,), (2.0,)}, f"{label}: required g rows are 0.5, 1.0, 2.0")
    raw_index = {(float(r["g"]), int(r["layers"]), int(r["seed"])): r for r in raw}
    selection_path = ROOT / "results/raw/s1_noisy_selection.json"
    require(selection_path.is_file(), "missing required file: results/raw/s1_noisy_selection.json")
    selections = json.loads(selection_path.read_text(encoding="utf-8"))
    for g in (0.5, 1.0, 2.0):
        row = index[(g,)]
        passing = []
        for layer in LAYERS:
            best_at_layer = min((raw_index[(g, layer, seed)] for seed in SEEDS),
                                key=lambda r: float(r["energy"]))
            if abs(float(best_at_layer["energy_err"])) < 1e-3:
                passing.append(layer)
        if passing:
            selected_layer = min(passing)
        else:
            selected_layer = min(LAYERS, key=lambda L: abs(float(min(
                (raw_index[(g, L, seed)] for seed in SEEDS), key=lambda r: float(r["energy"]))["energy_err"])))
        require(int(row["layers"]) == selected_layer,
                f"{label} g={g}: expected selection layer {selected_layer}, got {row['layers']}")
        selected_raw = min((raw_index[(g, selected_layer, seed)] for seed in SEEDS),
                           key=lambda r: float(r["energy"]))
        require(str(selected_raw["success"]).lower() in {"true", "1"},
                f"{label} g={g}: selected noisy circuit is marked non-converged")
        selection = selections.get(str(g)) or selections.get(f"{g:.1f}")
        require(selection is not None, f"results/raw/s1_noisy_selection.json: missing g={g}")
        require(int(selection["layers"]) == selected_layer and int(selection["seed"]) == int(selected_raw["seed"]),
                f"results/raw/s1_noisy_selection.json g={g}: not the best seed at selected layer")
        close(selection["ideal_energy"], selected_raw["energy"], TOL,
              f"results/raw/s1_noisy_selection.json g={g}: ideal_energy")
        close(selection["energy_err"], selected_raw["energy_err"], TOL,
              f"results/raw/s1_noisy_selection.json g={g}: energy_err")
        theta = json.loads(selected_raw["theta_json"])
        selection_theta = selection.get("theta")
        require(isinstance(selection_theta, list) and len(selection_theta) == len(theta),
                f"results/raw/s1_noisy_selection.json g={g}: invalid theta list")
        require(np.allclose(np.asarray(selection_theta, dtype=float), np.asarray(theta, dtype=float), atol=TOL, rtol=0),
                f"results/raw/s1_noisy_selection.json g={g}: selected parameters differ from raw seed")
        close(row["layers"], selected_layer, 0, f"{label} g={g}: layers")
        instance = json.loads((ROOT / "data/s1" / f"tfim_open_N4_g{g:.2f}.json").read_text(encoding="utf-8"))
        hamiltonian = SparsePauliOp.from_list([(p, float(c)) for p, c in instance["operator"]])
        circuit, params = sim.hva_ansatz(4, selected_layer, zz_mode="rzz")
        bound = circuit.assign_parameters(dict(zip(params, theta)))
        density = sim.noisy_density_matrix(bound, processor)
        energy = float(np.real(density.expectation_value(hamiltonian)))
        fidelity = sim.noisy_state_fidelity(bound, references[g][2][0], processor)
        close(row["energy_noisy"], energy, TOL, f"{label} g={g}: energy_noisy")
        close(row["fidelity_noisy_dm"], fidelity, TOL, f"{label} g={g}: fidelity_noisy_dm")
        observables = sim.noisy_expectations(bound, sim.observable_ops(4), processor)
        for column, key in (("mx_noisy", "mx"), ("czz_nn_noisy", "czz_nn"), ("mz2_noisy", "mz2")):
            close(row[column], observables[key], TOL, f"{label} g={g}: {column}")


def _as_bool(value, label: str) -> bool:
    normalized = str(value).strip().lower()
    require(normalized in {"true", "false", "1", "0"}, f"{label}: expected boolean, got {value!r}")
    return normalized in {"true", "1"}


def _read_additional_tables() -> dict[str, list[dict[str, str]]]:
    tables = {}
    for name, expected_header in ADDITIONAL_SCHEMAS.items():
        header, rows = read_csv(ROOT / "results/additional" / name)
        require(header == expected_header,
                f"results/additional/{name}: schema mismatch; expected {expected_header}, got {header}")
        tables[name] = rows
    return tables


def validate_n6_research(tables: dict[str, list[dict[str, str]]]) -> tuple[int, int]:
    raw_name = "s1_n6_seed_runs.csv"
    exact_name = "s1_n6_exact_reference.csv"
    aggregate_name = "s1_n6_results.csv"
    layer_name = "s1_n6_layer_study.csv"
    minimal_name = "s1_n6_minimal_layers.csv"
    resource_name = "s1_n6_resources.csv"
    raw, exact, aggregates = (tables[raw_name], tables[exact_name], tables[aggregate_name])
    layers, minimal, resources = (tables[layer_name], tables[minimal_name], tables[resource_name])
    label = lambda name: f"results/additional/{name}"

    expected_raw_keys = {(6, g, layer, seed) for g in N6_G for layer in n6_layers_for_g(g) for seed in SEEDS}
    require(len(raw) == len(expected_raw_keys), f"{label(raw_name)}: expected {len(expected_raw_keys)} rows, got {len(raw)}")
    raw_index = require_unique(raw, lambda r: (int(r["N"]), float(r["g"]), int(r["layers"]), int(r["seed"])), label(raw_name))
    require(set(raw_index) == expected_raw_keys, f"{label(raw_name)}: missing or unexpected N/g/layer/seed coverage")
    require(len(exact) == len(N6_G), f"{label(exact_name)}: expected 7 rows, got {len(exact)}")
    exact_by_g = require_unique(exact, lambda r: (float(r["g"]),), label(exact_name))
    require(set(exact_by_g) == {(g,) for g in N6_G}, f"{label(exact_name)}: incorrect g coverage")
    expected_aggregate_keys = {(6, g, layer) for g in N6_G for layer in n6_layers_for_g(g)}
    require(len(aggregates) == len(expected_aggregate_keys), f"{label(aggregate_name)}: expected {len(expected_aggregate_keys)} rows, got {len(aggregates)}")
    aggregate_by_key = require_unique(aggregates, lambda r: (int(r["N"]), float(r["g"]), int(r["layers"])), label(aggregate_name))
    require(set(aggregate_by_key) == expected_aggregate_keys, f"{label(aggregate_name)}: incorrect N/g/layer coverage")
    require(len(layers) == len(expected_aggregate_keys), f"{label(layer_name)}: expected {len(expected_aggregate_keys)} rows, got {len(layers)}")
    layer_by_key = require_unique(layers, lambda r: (int(r["N"]), float(r["g"]), int(r["layers"])), label(layer_name))
    require(set(layer_by_key) == expected_aggregate_keys, f"{label(layer_name)}: incorrect N/g/layer coverage")
    require(len(minimal) == len(N6_G), f"{label(minimal_name)}: expected 7 rows, got {len(minimal)}")
    minimal_by_g = require_unique(minimal, lambda r: (float(r["g"]),), label(minimal_name))
    require(set(minimal_by_g) == {(g,) for g in N6_G}, f"{label(minimal_name)}: incorrect g coverage")
    require(len(resources) == 15, f"{label(resource_name)}: expected 15 rows (one A capacity + 14 B/D), got {len(resources)}")
    resource_by_key = require_unique(resources, lambda r: (r["circuit_label"], r["processor"]), label(resource_name))

    raw_numeric = {"N", "g", "layers", "seed", "energy", "exact_E0", "exact_E1", "energy_err", "fidelity", "fidelity_2", "mx", "czz_nn", "mz2", "mz", "optimizer_calls", "n_params", "status", "runtime_seconds"}
    exact_numeric = {"N", "g", "exact_E0", "exact_E1", "E0_metadata", "E1_metadata", "E0_abs_diff", "E1_abs_diff", "mx_exact", "czz_nn_exact", "mz2_exact", "mz_exact"}
    aggregate_numeric = {"N", "g", "layers", "best_seed", "best_energy", "exact_E0", "energy_err", "fidelity", "fidelity_2", "mx", "mx_exact", "czz_nn", "czz_nn_exact", "mz2", "mz2_exact", "mz", "optimizer_calls", "n_params"}
    layer_numeric = {"N", "g", "layers", "best_seed", "best_energy", "energy_err", "abs_energy_err", "optimizer_calls_winner"}
    for rows, columns, table_label in ((raw, raw_numeric, label(raw_name)), (exact, exact_numeric, label(exact_name)),
                                       (aggregates, aggregate_numeric, label(aggregate_name)), (layers, layer_numeric, label(layer_name))):
        require_finite_columns(rows, columns, table_label)
    failed = []
    for key, row in raw_index.items():
        n, g, layer, seed = key
        require(n == 6, f"{label(raw_name)}: row {key} has N != 6")
        close(row["exact_E0"], exact_by_g[(g,)]["exact_E0"], TOL, f"{label(raw_name)} {key}: exact_E0")
        close(row["exact_E1"], exact_by_g[(g,)]["exact_E1"], TOL, f"{label(raw_name)} {key}: exact_E1")
        close(row["energy_err"], float(row["energy"]) - float(row["exact_E0"]), TOL, f"{label(raw_name)} {key}: energy_err")
        theta = np.asarray(json.loads(row["theta_json"]), dtype=float)
        require(theta.ndim == 1 and len(theta) == int(row["n_params"]) and np.all(np.isfinite(theta)),
                f"{label(raw_name)} {key}: invalid saved parameter vector")
        circuit, params = sim.hva_ansatz(6, layer, zz_mode="cx")
        require(len(params) == len(theta), f"{label(raw_name)} {key}: parameter count does not match HVA")
        state = Statevector(circuit.assign_parameters(dict(zip(params, theta))))
        hamiltonian = sim.tfim_hamiltonian(6, J=1.0, g=g, periodic=False)
        energy = float(np.real(state.expectation_value(hamiltonian)))
        close(row["energy"], energy, TOL, f"{label(raw_name)} {key}: recomputed energy")
        values, eigenstates = sim.exact_spectrum(hamiltonian, 2)
        ground_fidelity = float(state_fidelity(eigenstates[0], state))
        first_fidelity = float(state_fidelity(eigenstates[1], state))
        obs = sim.expectations(state, sim.observable_ops(6))
        for column, expected in (("fidelity", ground_fidelity), ("fidelity_2", ground_fidelity + first_fidelity),
                                 ("mx", obs["mx"]), ("czz_nn", obs["czz_nn"]), ("mz2", obs["mz2"]), ("mz", obs["mz"])):
            close(row[column], expected, TOL, f"{label(raw_name)} {key}: {column}")
        success = _as_bool(row["success"], f"{label(raw_name)} {key}: success")
        if not success:
            failed.append(row)
            require(row["message"].strip(), f"{label(raw_name)} {key}: non-success start lost its message")
        require(-TOL <= float(row["fidelity"]) <= 1.0 + TOL and -TOL <= float(row["fidelity_2"]) <= 1.0 + TOL,
                f"{label(raw_name)} {key}: fidelity outside [0,1]")
        require(float(row["runtime_seconds"]) >= 0 and float(row["optimizer_calls"]) >= 0,
                f"{label(raw_name)} {key}: negative runtime or optimizer call count")
    require(len(failed) == 88,
            f"{label(raw_name)}: expected to retain the 88 recorded optimizer non-success flags, got {len(failed)}")

    for g in N6_G:
        obj = json.loads((ROOT / "data/s1" / f"tfim_open_N6_g{g:.2f}.json").read_text(encoding="utf-8"))
        hamiltonian = sim.tfim_hamiltonian(6, J=1.0, g=g, periodic=False)
        values, eigenstates = sim.exact_spectrum(hamiltonian, 2)
        obs = sim.expectations(eigenstates[0], sim.observable_ops(6))
        ref = exact_by_g[(g,)]
        for column, expected in (("exact_E0", values[0]), ("exact_E1", values[1]),
                                 ("E0_metadata", obj["meta"]["E0_exact"]), ("E1_metadata", obj["meta"]["E1_exact"]),
                                 ("E0_abs_diff", abs(values[0] - float(obj["meta"]["E0_exact"]))),
                                 ("E1_abs_diff", abs(values[1] - float(obj["meta"]["E1_exact"]))),
                                 ("mx_exact", obs["mx"]), ("czz_nn_exact", obs["czz_nn"]),
                                 ("mz2_exact", obs["mz2"]), ("mz_exact", obs["mz"])):
            close(ref[column], expected, TOL, f"{label(exact_name)} g={g}: {column}")
        require(float(ref["E0_abs_diff"]) <= 1e-9 and float(ref["E1_abs_diff"]) <= 1e-9,
                f"{label(exact_name)} g={g}: official reference tolerance exceeded")

    for g in N6_G:
        for layer in n6_layers_for_g(g):
            key = (6, g, layer)
            starts = [raw_index[(6, g, layer, seed)] for seed in SEEDS]
            winner = min(starts, key=lambda row: float(row["energy"]))
            aggregate = aggregate_by_key[key]
            layer_row = layer_by_key[key]
            expected_fields = (("best_seed", int(winner["seed"])), ("best_energy", float(winner["energy"])),
                               ("exact_E0", float(winner["exact_E0"])), ("energy_err", float(winner["energy_err"])),
                               ("fidelity", float(winner["fidelity"])), ("fidelity_2", float(winner["fidelity_2"])),
                               ("mx", float(winner["mx"])), ("czz_nn", float(winner["czz_nn"])),
                               ("mz2", float(winner["mz2"])), ("mz", float(winner["mz"])),
                               ("optimizer_calls", int(winner["optimizer_calls"])), ("n_params", int(winner["n_params"])))
            for column, expected in expected_fields:
                close(aggregate[column], expected, TOL, f"{label(aggregate_name)} {key}: {column}")
            for column, expected in (("mx_exact", exact_by_g[(g,)]["mx_exact"]),
                                     ("czz_nn_exact", exact_by_g[(g,)]["czz_nn_exact"]),
                                     ("mz2_exact", exact_by_g[(g,)]["mz2_exact"])):
                close(aggregate[column], expected, TOL, f"{label(aggregate_name)} {key}: {column}")
            close(layer_row["best_seed"], int(winner["seed"]), 0, f"{label(layer_name)} {key}: best_seed")
            close(layer_row["best_energy"], float(winner["energy"]), TOL, f"{label(layer_name)} {key}: best_energy")
            close(layer_row["energy_err"], float(winner["energy_err"]), TOL, f"{label(layer_name)} {key}: energy_err")
            close(layer_row["abs_energy_err"], abs(float(winner["energy_err"])), TOL, f"{label(layer_name)} {key}: abs_energy_err")
            require(_as_bool(layer_row["any_seed_success"], f"{label(layer_name)} {key}: any_seed_success") ==
                    any(_as_bool(row["success"], f"{label(raw_name)} {key}: success") for row in starts),
                    f"{label(layer_name)} {key}: any_seed_success is inconsistent")
            close(layer_row["optimizer_calls_winner"], int(winner["optimizer_calls"]), 0,
                  f"{label(layer_name)} {key}: optimizer_calls_winner")

    for g in N6_G:
        layers_for_g_val = n6_layers_for_g(g)
        passes = [layer for layer in layers_for_g_val
                  if abs(float(layer_by_key[(6, g, layer)]["abs_energy_err"])) < 1e-3]
        first_pass = min(passes) if passes else None
        if first_pass is not None:
            candidates = [raw_index[(6, g, first_pass, seed)] for seed in SEEDS]
            selected = min(candidates, key=lambda row: float(row["energy"]))
            expected_minimum = str(first_pass)
        else:
            selected = min((row for (n, row_g, _layer, _seed), row in raw_index.items() if n == 6 and row_g == g),
                           key=lambda row: abs(float(row["energy_err"])))
            expected_minimum = f"NOT_REACHED_L<={max(layers_for_g_val)}"
        record = minimal_by_g[(g,)]
        require(str(record["minimal_L_abs_err_lt_1e-3"]) == expected_minimum,
                f"{label(minimal_name)} g={g}: minimum threshold layer is inconsistent")
        require(_as_bool(record["threshold_met_within_L1_to_L8"], f"{label(minimal_name)} g={g}: threshold flag") == (first_pass is not None),
                f"{label(minimal_name)} g={g}: threshold flag is inconsistent")
        close(record["selected_seed"], int(selected["seed"]), 0, f"{label(minimal_name)} g={g}: selected_seed")
        close(record["selected_L"], int(selected["layers"]), 0, f"{label(minimal_name)} g={g}: selected_L")
        close(record["selected_energy_error"], float(selected["energy_err"]), TOL,
              f"{label(minimal_name)} g={g}: selected_energy_error")
        require(_as_bool(record["selected_optimizer_success"], f"{label(minimal_name)} g={g}: success") ==
                _as_bool(selected["success"], f"{label(raw_name)} selected g={g}: success"),
                f"{label(minimal_name)} g={g}: selected success flag is inconsistent")
        failed_at_layer = sum(not _as_bool(raw_index[(6, g, int(selected["layers"]), seed)]["success"],
                                          f"{label(raw_name)} g={g} L={selected['layers']}: success") for seed in SEEDS)
        close(record["failed_starts_at_selected_L"], failed_at_layer, 0, f"{label(minimal_name)} g={g}: failed_starts_at_selected_L")

    capacity = [row for row in resources if row["processor"] == "A"]
    require(len(capacity) == 1, f"{label(resource_name)}: expected one Processor A capacity row")
    cap = capacity[0]
    require(cap["reason"] == "not executable: needs 6 qubits, has 5" and
            cap["selection_status"] == "processor_capacity" and not _as_bool(cap["executable"], f"{label(resource_name)} capacity executable"),
            f"{label(resource_name)}: Processor A capacity exception is missing or incorrect")
    require(int(cap["logical_qubits"]) == 6 and int(cap["physical_qubits"]) == 5,
            f"{label(resource_name)}: Processor A capacity counts are incorrect")
    expected_resource_keys = {("n6_optional_capacity_check", "A")}
    proc_b = sim.PROCESSOR_B
    proc_d = sim.load_processor(str(ROOT / "processors/processor_D.json"))
    for g in N6_G:
        selection = minimal_by_g[(g,)]
        layer, seed = int(selection["selected_L"]), int(selection["selected_seed"])
        winner = raw_index[(6, g, layer, seed)]
        theta = np.asarray(json.loads(winner["theta_json"]), dtype=float)
        expected_error = float(winner["energy_err"])
        expected_status = ("first_threshold_layer" if
                           _as_bool(selection["threshold_met_within_L1_to_L8"], f"{label(minimal_name)} g={g}: threshold flag")
                           else "best_available_threshold_not_reached")
        mode_by_processor = (("B", "cx", proc_b), ("D", "rzz", proc_d))
        for processor_label, mode, processor in mode_by_processor:
            key_label = f"n6_hva_g{g:.2f}_L{layer}_best_seed{seed}_{mode}"
            expected_resource_keys.add((key_label, processor_label))
            resource = resource_by_key[(key_label, processor_label)]
            require(resource["scope"] == ADDITIONAL_SCOPE and resource["zz_mode"] == mode and
                    resource["processor"] == processor_label and resource["selection_status"] == expected_status,
                    f"{label(resource_name)} {key_label}/{processor_label}: selection metadata mismatch")
            close(resource["N"], 6, 0, f"{label(resource_name)} {key_label}: N")
            close(resource["g"], g, 0, f"{label(resource_name)} {key_label}: g")
            close(resource["layers"], layer, 0, f"{label(resource_name)} {key_label}: layers")
            close(resource["seed"], seed, 0, f"{label(resource_name)} {key_label}: seed")
            require(resource["reason"] == "", f"{label(resource_name)} {key_label}: executable row has a failure reason")
            require(_as_bool(resource["executable"], f"{label(resource_name)} {key_label}: executable"),
                    f"{label(resource_name)} {key_label}: expected executable circuit")
            close(resource["selected_energy_error"], expected_error, TOL,
                  f"{label(resource_name)} {key_label}: selected_energy_error")
            require(_as_bool(resource["optimizer_success"], f"{label(resource_name)} {key_label}: optimizer_success") ==
                    _as_bool(winner["success"], f"{label(raw_name)} {key_label}: success"),
                    f"{label(resource_name)} {key_label}: optimizer flag mismatch")
            circuit, params = sim.hva_ansatz(6, layer, zz_mode=mode)
            metrics = sim.circuit_metrics(circuit.assign_parameters(dict(zip(params, theta))), processor)
            require(metrics.get("executable", False), f"{label(resource_name)} {key_label}: recomputed circuit is not executable")
            for column, metric_key in (("logical_qubits", "logical_qubits"), ("physical_qubits", "physical_qubits"),
                                       ("logical_2q", "logical_cx"), ("two_q", "cx"), ("depth", "depth"),
                                       ("two_q_depth", "two_q_depth"), ("swaps", "swaps"),
                                       ("routing_overhead_2q", "cx_overhead")):
                close(resource[column], metrics[metric_key], 0, f"{label(resource_name)} {key_label}: {column}")
    require(set(resource_by_key) == expected_resource_keys,
            f"{label(resource_name)}: incorrect Processor B/D N=6 resource keys")
    return len(raw), len(failed)


def _independent_crossings(rows: list[dict[str, str]]) -> list[tuple[int, int, str, str]]:
    scaled_gap = {(int(row["N"]), float(row["g"])): float(row["gap_times_N"]) for row in rows}
    expected = []
    for n_small, n_large in zip(FINITE_SIZES[:-1], FINITE_SIZES[1:]):
        found = []
        for g0, g1 in zip(FINITE_G[:-1], FINITE_G[1:]):
            delta0 = scaled_gap[(n_small, g0)] - scaled_gap[(n_large, g0)]
            delta1 = scaled_gap[(n_small, g1)] - scaled_gap[(n_large, g1)]
            if delta0 == 0:
                found.append(g0)
            elif delta0 * delta1 < 0:
                found.append(g0 + (g1 - g0) * (-delta0) / (delta1 - delta0))
        if scaled_gap[(n_small, FINITE_G[-1])] == scaled_gap[(n_large, FINITE_G[-1])]:
            found.append(FINITE_G[-1])
        if not found:
            expected.append((n_small, n_large, "NA", "no sign-change crossing on sampled grid"))
        else:
            expected.extend((n_small, n_large, f"{value:.15g}", "linear interpolation between 0.05-spaced grid points")
                            for value in sorted(set(found)))
    return expected


def validate_finite_size_research(tables: dict[str, list[dict[str, str]]]) -> int:
    rows = tables["finite_size_scaling.csv"]
    crossing_rows = tables["finite_size_crossings.csv"]
    label = "results/additional/finite_size_scaling.csv"
    require(len(rows) == 180, f"{label}: expected 180 rows, got {len(rows)}")
    by_key = require_unique(rows, lambda r: (int(r["N"]), float(r["g"])), label)
    expected_keys = {(n, g) for n in FINITE_SIZES for g in FINITE_G}
    require(set(by_key) == expected_keys, f"{label}: incorrect N/g coverage")
    numeric = {"N", "g", "E0_sparse", "E1_sparse", "gap", "gap_times_N", "half_chain_entropy_bits", "mz2_over_N2", "eigsh_tolerance", "deterministic_v0_seed"}
    require_finite_columns(rows, numeric, label)
    for row in rows:
        n, g = int(row["N"]), float(row["g"])
        require(row["scope"] == ADDITIONAL_SCOPE and row["solver"] == "scipy.sparse.linalg.eigsh",
                f"{label} N={n} g={g}: scope/solver metadata mismatch")
        e0, e1 = float(row["E0_sparse"]), float(row["E1_sparse"])
        gap = float(row["gap"])
        require(e1 > e0 and gap > 0, f"{label} N={n} g={g}: non-positive excitation gap")
        close(gap, e1 - e0, 1e-10, f"{label} N={n} g={g}: gap")
        close(row["gap_times_N"], gap * n, 1e-10, f"{label} N={n} g={g}: gap_times_N")
        entropy, mz2_n2 = float(row["half_chain_entropy_bits"]), float(row["mz2_over_N2"])
        require(-1e-10 <= entropy <= n / 2 + 1e-10, f"{label} N={n} g={g}: entropy outside physical bounds")
        require(-1e-10 <= mz2_n2 <= 1 + 1e-10, f"{label} N={n} g={g}: normalized magnetization outside physical bounds")
        close(row["eigsh_tolerance"], 1e-12, 0, f"{label} N={n} g={g}: eigsh tolerance")
        close(row["deterministic_v0_seed"], 91000 + n, 0, f"{label} N={n} g={g}: deterministic seed")

    reference_count = 0
    checked_fields = (0.25, 0.50, 0.75, 1.00, 1.25, 1.50, 2.00)
    for n, g in expected_keys:
        row = by_key[(n, g)]
        checked_expected = n in (4, 6) and g in checked_fields
        require(_as_bool(row["reference_checked"], f"{label} N={n} g={g}: reference_checked") == checked_expected,
                f"{label} N={n} g={g}: reference_checked flag is inconsistent")
        if checked_expected:
            reference_count += 1
            obj = json.loads((ROOT / "data/s1" / f"tfim_open_N{n}_g{g:.2f}.json").read_text(encoding="utf-8"))
            for metadata_col, diff_col, energy_col in (("E0_metadata", "E0_abs_diff", "E0_sparse"),
                                                       ("E1_metadata", "E1_abs_diff", "E1_sparse")):
                metadata = float(obj["meta"][metadata_col.replace("_metadata", "_exact")])
                close(row[metadata_col], metadata, 0, f"{label} N={n} g={g}: {metadata_col}")
                close(row[diff_col], abs(float(row[energy_col]) - metadata), 1e-12,
                      f"{label} N={n} g={g}: {diff_col}")
                require(float(row[diff_col]) <= 1e-9, f"{label} N={n} g={g}: official reference mismatch")
        else:
            require(row["E0_metadata"] == "NA" and row["E1_metadata"] == "NA" and
                    row["E0_abs_diff"] == "NA" and row["E1_abs_diff"] == "NA",
                    f"{label} N={n} g={g}: unchecked reference fields must be NA")
    require(reference_count == 14, f"{label}: expected 14 N=4/6 official reference checks, got {reference_count}")

    # Re-solve the sparse spectra and recompute the gap, entropy, and order diagnostic.
    for n in FINITE_SIZES:
        rng = np.random.default_rng(91000 + n)
        matrix_seed = rng.normal(size=2**n)
        for g in FINITE_G:
            row = by_key[(n, g)]
            hamiltonian = sim.tfim_hamiltonian(n, J=1.0, g=g, periodic=False)
            matrix = hamiltonian.to_matrix(sparse=True).tocsr()
            eigvals, eigvecs = eigsh(matrix, k=2, which="SA", tol=1e-12, maxiter=50000,
                                     ncv=min(matrix.shape[0], 40), v0=matrix_seed.copy())
            order = np.argsort(eigvals)
            eigvals = np.asarray(eigvals[order], dtype=float)
            ground = np.asarray(eigvecs[:, order[0]].real, dtype=float)
            close(row["E0_sparse"], eigvals[0], 1e-9, f"{label} N={n} g={g}: recomputed E0")
            close(row["E1_sparse"], eigvals[1], 1e-9, f"{label} N={n} g={g}: recomputed E1")
            close(row["gap"], eigvals[1] - eigvals[0], 1e-9, f"{label} N={n} g={g}: recomputed gap")
            state = Statevector(ground)
            reduced = partial_trace(state, list(range(n // 2, n)))
            eigenvalues = np.linalg.eigvalsh(np.asarray(reduced.data, dtype=complex)).real
            eigenvalues = np.clip(eigenvalues, 0.0, None)
            eigenvalues = eigenvalues[eigenvalues > 1e-14]
            entropy = float(-np.sum(eigenvalues * np.log2(eigenvalues)))
            observables = sim.expectations(state, sim.observable_ops(n))
            close(row["half_chain_entropy_bits"], entropy, 2e-9, f"{label} N={n} g={g}: recomputed entropy")
            close(row["mz2_over_N2"], observables["mz2"], 2e-9, f"{label} N={n} g={g}: recomputed Mz2/N2")

    require(len(crossing_rows) == 4, f"results/additional/finite_size_crossings.csv: expected four adjacent-size crossings, got {len(crossing_rows)}")
    expected_crossings = _independent_crossings(rows)
    require(len(crossing_rows) == len(expected_crossings), "finite-size crossing table has unexpected crossing count")
    for i, (row, expected) in enumerate(zip(crossing_rows, expected_crossings), start=2):
        small, large, crossing, status = expected
        require(row["scope"] == ADDITIONAL_SCOPE and row["quantity"] == "N times gap" and
                int(row["N_small"]) == small and int(row["N_large"]) == large and row["status"] == status,
                f"results/additional/finite_size_crossings.csv:{i}: crossing key/status mismatch")
        if crossing == "NA":
            require(row["g_crossing_linear_interpolation"] == "NA",
                    f"results/additional/finite_size_crossings.csv:{i}: expected NA crossing")
        else:
            close(row["g_crossing_linear_interpolation"], crossing, 1e-10,
                  f"results/additional/finite_size_crossings.csv:{i}: interpolated crossing")
    return reference_count


def validate_mitigation_research(tables: dict[str, list[dict[str, str]]]) -> int:
    from src import run_mitigation_d as mitigation_script

    rows = tables["mitigation_d_results.csv"]
    label = "results/additional/mitigation_d_results.csv"
    require(len(rows) == 15, f"{label}: expected 15 g/observable rows, got {len(rows)}")
    by_key = require_unique(rows, lambda r: (float(r["g"]), r["observable"]), label)
    expected_keys = {(g, observable) for g in MITIGATION_G for observable in MITIGATION_OBSERVABLES}
    require(set(by_key) == expected_keys, f"{label}: incorrect g/observable coverage")
    numeric = {"g", "layers", "seed", "ideal_selected_circuit_target", "p1_fixed", "p2_baseline", "p_readout_fixed", "shots_per_basis_per_scale", "bootstrap_replicates"}
    for method in ("raw", "readout_corrected", "zne", "zne_readout_corrected"):
        numeric.update({f"{method}_value", f"{method}_se", f"{method}_abs_error"})
    require_finite_columns(rows, numeric, label)
    selections = json.loads((ROOT / "results/raw/s1_noisy_selection.json").read_text(encoding="utf-8"))
    raw_rows = read_csv(ROOT / "results/raw/s1_seed_runs.csv")[1]
    raw_index = {(float(row["g"]), int(row["layers"]), int(row["seed"])): row for row in raw_rows}
    expected_targets = {}
    for g in MITIGATION_G:
        selection = selections[f"{g:.1f}"]
        layer, seed = int(selection["layers"]), int(selection["seed"])
        raw = raw_index[(g, layer, seed)]
        theta = np.asarray(selection["theta"], dtype=float)
        require(np.allclose(theta, np.asarray(json.loads(raw["theta_json"]), dtype=float), atol=1e-12, rtol=0),
                f"mitigation selection g={g}: saved parameters do not match selected official run")
        circuit, params = sim.hva_ansatz(4, layer, zz_mode="rzz")
        state = Statevector(circuit.assign_parameters(dict(zip(params, theta))))
        expected_targets[g] = sim.expectations(state, sim.observable_ops(4))
        expected_targets[g]["energy"] = float(np.real(
            state.expectation_value(sim.tfim_hamiltonian(4, J=1.0, g=g, periodic=False))))
    for (g, observable), row in by_key.items():
        selection = selections[f"{g:.1f}"]
        require(row["scope"] == ADDITIONAL_SCOPE and row["target_definition"] ==
                "noiseless expectation of the same saved selected HVA parameters",
                f"{label} g={g} {observable}: scope/target definition mismatch")
        require(row["alpha_p2_scales"] == "1.0;1.5;2.0", f"{label} g={g} {observable}: p2 scale metadata mismatch")
        close(row["layers"], int(selection["layers"]), 0, f"{label} g={g} {observable}: layers")
        close(row["seed"], int(selection["seed"]), 0, f"{label} g={g} {observable}: seed")
        close(row["ideal_selected_circuit_target"], expected_targets[g][observable], TOL,
              f"{label} g={g} {observable}: target is not selected-circuit expectation")
        close(row["p1_fixed"], mitigation_script.P1, 0, f"{label} g={g} {observable}: p1")
        close(row["p2_baseline"], mitigation_script.P2, 0, f"{label} g={g} {observable}: p2")
        close(row["p_readout_fixed"], mitigation_script.P_READOUT, 0, f"{label} g={g} {observable}: readout rate")
        close(row["shots_per_basis_per_scale"], mitigation_script.SHOTS, 0, f"{label} g={g} {observable}: shots")
        close(row["bootstrap_replicates"], mitigation_script.BOOTSTRAPS, 0, f"{label} g={g} {observable}: bootstrap count")
        require("synthetic" in row["readout_calibration_model"].lower(),
                f"{label} g={g} {observable}: calibration model is not labelled synthetic")
        for method in ("raw", "readout_corrected", "zne", "zne_readout_corrected"):
            error_column = f"{method}_abs_error"
            value_column, se_column = f"{method}_value", f"{method}_se"
            close(row[error_column], abs(float(row[value_column]) - float(row["ideal_selected_circuit_target"])), 1e-10,
                  f"{label} g={g} {observable}: {error_column}")
            require(float(row[se_column]) >= 0, f"{label} g={g} {observable}: negative {se_column}")

    cost_rows = tables["mitigation_d_costs.csv"]
    require(len(cost_rows) == 1, "results/additional/mitigation_d_costs.csv: expected one acquisition-cost row")
    cost = cost_rows[0]
    require(cost["scope"] == ADDITIONAL_SCOPE, "mitigation cost row has incorrect scope")
    n_g, n_basis, n_scales, n_qubits = len(mitigation_script.GS), 2, len(mitigation_script.SCALES), 4
    baseline_circuits = n_g * n_basis
    extra_circuits = n_g * n_basis * (n_scales - 1)
    calibration_circuits = 2 * n_qubits
    expected_cost = {
        "official_baseline_data_circuits_at_alpha_1": baseline_circuits,
        "additional_p2_scale_data_circuits_at_alpha_1_5_and_2": extra_circuits,
        "readout_calibration_circuits_reused": calibration_circuits,
        "total_unique_data_circuits": baseline_circuits + extra_circuits,
        "total_unique_circuits_including_calibration": baseline_circuits + extra_circuits + calibration_circuits,
        "shots_per_circuit": mitigation_script.SHOTS,
        "baseline_data_shots_at_alpha_1": baseline_circuits * mitigation_script.SHOTS,
        "additional_shots_for_p2_scales": extra_circuits * mitigation_script.SHOTS,
        "readout_calibration_shots": calibration_circuits * mitigation_script.SHOTS,
        "total_data_and_calibration_shots": (baseline_circuits + extra_circuits + calibration_circuits) * mitigation_script.SHOTS,
        "extra_circuits_vs_raw_alpha_1": extra_circuits + calibration_circuits,
        "extra_shots_vs_raw_alpha_1": (extra_circuits + calibration_circuits) * mitigation_script.SHOTS,
    }
    require_finite_columns(cost_rows, set(expected_cost), "results/additional/mitigation_d_costs.csv")
    for column, expected in expected_cost.items():
        close(cost[column], expected, 0, f"results/additional/mitigation_d_costs.csv: {column}")
    require("reused" in cost["calibration_reuse"].lower() and "p2" in cost["noise_settings"].lower(),
            "mitigation cost row must disclose calibration reuse and p2 scaling")
    return len(rows)


def validate_additional_research() -> tuple[int, int, int, int]:
    tables = _read_additional_tables()
    n6_starts, n6_failures = validate_n6_research(tables)
    finite_references = validate_finite_size_research(tables)
    mitigation_rows = validate_mitigation_research(tables)
    return n6_starts, n6_failures, finite_references, mitigation_rows


def validate():
    source = ROOT / "handoff_payload/OFFICIAL_KIT"
    checked = verify_manifest()
    require(hashlib.sha256((ROOT / "qff_sim.py").read_bytes()).hexdigest() ==
            "dd0305834f88164f01f9b2a17f7333eb48a966cb81951b1953eed0e218de4cfc", "qff_sim.py changed from official copy")
    require(hashlib.sha256((ROOT / "tools/check_processor_d.py").read_bytes()).hexdigest() ==
            "09b1af7ddc8ee17b369e15308847ffc371dacb7820f5b3e101824b2d1deb85b4", "official checker changed")
    template = (source / "templates/results_columns.md").read_text(encoding="utf-8")
    schemas = parse_template_schemas(template)
    require(schemas, "official templates/results_columns.md: no CSV schemas parsed")
    applicable = {"bell.csv", "resources.csv", "s1_results.csv", "s1_noisy.csv"}
    require(applicable <= set(schemas), f"official schema missing applicable tables: {sorted(applicable-set(schemas))}")
    tables = {}
    for name in sorted(applicable):
        header, rows = read_csv(ROOT / "results/tables" / name)
        require(header == schemas[name],
                f"results/tables/{name}: schema mismatch; expected {schemas[name]}, got {header}")
        require_finite_columns(rows, NUMERIC_COLUMNS[name], f"results/tables/{name}")
        tables[name] = rows
    for name, header_expected in EXPECTED_EXTRA_HEADERS.items():
        header, rows = read_csv(ROOT / "results/tables" / name)
        require(header == header_expected,
                f"results/tables/{name}: expected header {header_expected}, got {header}")
        require_finite_columns(rows, NUMERIC_COLUMNS[name], f"results/tables/{name}")
        tables[name] = rows
    raw_header, raw = read_csv(ROOT / "results/raw/s1_seed_runs.csv")
    require(raw_header == RAW_REQUIRED,
            f"results/raw/s1_seed_runs.csv: expected header {RAW_REQUIRED}, got {raw_header}")
    raw_index = validate_raw_grid(raw)
    require(len(tables["s1_results.csv"]) == 28, "results/tables/s1_results.csv: expected 28 rows")
    require(len(tables["s1_noisy.csv"]) == 3, "results/tables/s1_noisy.csv: expected three required noisy-D rows")
    require(len(tables["bell.csv"]) == 4, "results/tables/bell.csv: expected four rows")
    require(len(tables["resources.csv"]) == 9, "results/tables/resources.csv: expected nine rows (both HVA modes plus Bell)")
    references = independently_check_exact_and_raw(raw, tables["s1_exact_reference.csv"])
    exact_by_g = require_unique(tables["s1_exact_reference.csv"], lambda r: (float(r["g"]),),
                                "results/tables/s1_exact_reference.csv")
    validate_aggregates(tables["s1_results.csv"], raw_index, exact_by_g, tables["layer_study.csv"])
    processor_path = ROOT / "processors/processor_D.json"
    processor = sim.load_processor(str(processor_path))
    validate_bell(tables["bell.csv"], processor)
    validate_resources(tables["resources.csv"], raw_index, processor)
    validate_p2_processor_comparison(raw_index, processor, tables["resources.csv"])
    validate_noisy(tables["s1_noisy.csv"], raw, references, processor)
    n6_starts, n6_failures, finite_references, mitigation_rows = validate_additional_research()
    # Preserve failed starts and their recorded termination reason; never filter them out.
    failed = [r for r in raw if str(r["success"]).lower() in {"false", "0"}]
    require(all(r["message"].strip() for r in failed),
            "results/raw/s1_seed_runs.csv: every non-converged start must retain its termination message")
    # Required figures and documentation/handoff files.
    figures = ["phase_observables_vs_g.png", "layer_study_convergence.png", "bell_comparison.png",
               "processor_D_topology.png", "noisy_vs_ideal_energy.png", "criticality_gap_entropy.png", "p2_sensitivity.png",
               "p2_processor_comparison.png", "additional_n6_layer_study.png",
               "additional_finite_size_scaling.png", "additional_mitigation_d.png"]
    for name in figures:
        require((ROOT / "results/figures" / name).is_file(), f"missing required/supplemental figure results/figures/{name}")
    docs = ["README.md", "report.md", "docs/report.md", "main.ipynb", "docs/STATUS.md", "docs/AUDIT_LOG.md",
            "docs/NUMBER_AUDIT.md", "docs/VIVA_DEFENSE.md", "docs/DEMO_WALKTHROUGH.md",
            "docs/RESULTS_AT_GLANCE.md", "docs/JUDGE_QA.md", "docs/FINAL_RUBRIC_MATRIX.md",
            "docs/AUDIT_BASELINE.sha256", "reference/PHASE1_BASELINE_README.md"]
    for name in docs:
        require((ROOT / name).is_file(), f"missing required deliverable: {name}")
    require((ROOT / "report.md").read_bytes() == (ROOT / "docs/report.md").read_bytes(),
            "report.md and docs/report.md must be identical")
    for name in ("README.md", "docs/DEMO_WALKTHROUGH.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        require(not re.search(r"(?:/home/user/|/Users/|[A-Za-z]:\\\\)", text),
                f"{name}: machine-specific absolute path in user instructions")
    require(hashlib.sha256((ROOT / "reference/PHASE1_BASELINE_README.md").read_bytes()).hexdigest() ==
            "00bc6d81839ebfe5afe312ff36837a3305b09125d5f87c27caa7bcb192c5c410",
            "preserved Phase 1 baseline README copy hash mismatch")
    notebook = json.loads((ROOT / "main.ipynb").read_text(encoding="utf-8"))
    code_cells = [cell for cell in notebook["cells"] if cell.get("cell_type") == "code"]
    require(code_cells and all(cell.get("execution_count") is not None for cell in code_cells),
            "main.ipynb: one or more code cells have no saved execution count")
    errors = [output for cell in code_cells for output in cell.get("outputs", []) if output.get("output_type") == "error"]
    require(not errors, "main.ipynb: saved error output present")
    require((ROOT / "results/starter_sim_executed.ipynb").is_file(), "missing official starter smoke-test notebook")
    for n in (4, 6):
        result = subprocess.run([sys.executable, "tools/check_processor_d.py", "processors/processor_D.json", str(n)],
                                cwd=ROOT, text=True, capture_output=True)
        require(result.returncode == 0,
                f"official Processor D checker failed for N={n}: {result.stdout}{result.stderr}")
        print(result.stdout.strip())
    print(f"PASS: official manifest/work-copy hashes={checked}/25; required tables, Bell/noise/resources, supplemental N=6/finite-size/mitigation data, figures, notebook, docs and D checks valid.")
    print(f"PASS: N4 raw starts={len(raw)} (non-success={len(failed)}); N6 starts={n6_starts} (non-success={n6_failures}); finite-size rows=180 (official reference pairs={finite_references}); mitigation rows={mitigation_rows}; supplemental A/B/D p2 rows=36; no N=4 sweep run.")


if __name__ == "__main__":
    try:
        validate()
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
