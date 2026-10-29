#!/usr/bin/env python3
"""Additional readout correction and p2-only ZNE for saved PS-S1 circuits.

Uses the official synthetic baseline rates for data circuits, fixes p1/readout
while scaling p2, and writes only under results/additional/ and
results/figures/additional_*.png. This is not hardware evidence.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from qiskit import ClassicalRegister, QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit.quantum_info import Statevector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import qff_sim as sim  # noqa: E402

SCOPE = "additional, not part of the official required results"
GS = (0.5, 1.0, 2.0)
P1 = 0.001
P2 = 0.005
P_READOUT = 0.01
SCALES = (1.0, 1.5, 2.0)  # scales p2 only; p1 and readout stay fixed
SHOTS = sim.SHOTS
BOOTSTRAPS = 400


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, columns: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="raise", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def measured_circuit(logical, basis: str) -> QuantumCircuit:
    qc = logical.copy()
    if basis == "X":
        qc.h(range(logical.num_qubits))
    cr = ClassicalRegister(logical.num_qubits, "m")
    qc.add_register(cr)
    qc.measure(range(logical.num_qubits), cr)
    return qc


def run_counts(logical: QuantumCircuit, processor: dict, basis: str, *, p1: float,
               p2: float, p_ro: float, shots: int, seed: int) -> dict[str, int]:
    measured = measured_circuit(logical, basis)
    transpiled = sim.transpile_for(measured, processor)
    noise = sim.official_noise_model(p1=p1, p2=p2, p_ro=p_ro)
    backend = AerSimulator(noise_model=noise, seed_simulator=seed)
    return backend.run(transpiled, shots=shots, seed_simulator=seed).result().get_counts()


def calibration_counts(n: int, processor: dict) -> dict[tuple[int, int], dict[str, int]]:
    """Independent single-qubit assignment calibration, re-used for all g/scales.

    Ideal |0>/<1> preparation is simulated with p1=p2=0; only the declared
    synthetic readout bit flip p_ro=0.01 is present in these calibration runs.
    """
    output = {}
    for q in range(n):
        for prepared in (0, 1):
            qc = QuantumCircuit(n)
            if prepared:
                qc.x(q)
            cr = ClassicalRegister(n, "m")
            qc.add_register(cr)
            qc.measure(range(n), cr)
            transpiled = sim.transpile_for(qc, processor)
            noise = sim.official_noise_model(p1=0.0, p2=0.0, p_ro=P_READOUT)
            backend = AerSimulator(noise_model=noise, seed_simulator=sim.SEED + q + 100 * prepared)
            counts = backend.run(transpiled, shots=SHOTS,
                                 seed_simulator=sim.SEED + q + 100 * prepared).result().get_counts()
            output[(q, prepared)] = counts
    return output


def sample_counts(counts: dict[str, int], shots: int, rng: np.random.Generator) -> dict[str, int]:
    keys = sorted(counts)
    frequencies = np.asarray([counts[k] for k in keys], dtype=np.int64)
    draw = rng.multinomial(shots, frequencies / frequencies.sum())
    return {key: int(value) for key, value in zip(keys, draw) if value}


def assignment_z_weights(cal: dict[tuple[int, int], dict[str, int]], n: int) -> list[np.ndarray]:
    """Return local weights w where E_true[Z] = E_observed[w(observed bit)]."""
    weights = []
    for q in range(n):
        columns = []
        for prepared in (0, 1):
            counts = cal[(q, prepared)]
            total = sum(counts.values())
            observed = [0, 0]
            for key, count in counts.items():
                bit = sim.counts_to_x(key)[q]
                observed[bit] += count
            columns.append(np.asarray(observed, dtype=float) / total)
        assignment = np.column_stack(columns)  # row observed, column prepared
        weights.append(np.linalg.solve(assignment.T, np.asarray([1.0, -1.0])))
    return weights


def shot_stats(counts: dict[str, int], n: int, basis: str,
               weights: list[np.ndarray] | None = None) -> dict[str, float]:
    total = sum(counts.values())
    if total <= 0:
        raise ValueError("empty counts")
    accum = defaultdict(float)
    for key, count in counts.items():
        bits = sim.counts_to_x(key)
        z = np.asarray([1.0 - 2.0 * bits[q] if weights is None else weights[q][bits[q]]
                        for q in range(n)], dtype=float)
        w = count / total
        if basis == "X":
            accum["x_sum"] += w * float(np.sum(z))
        else:
            zz = [z[q] * z[q + 1] for q in range(n - 1)]
            accum["zz_sum"] += w * float(np.sum(zz))
            accum["czz_nn"] += w * float(np.mean(zz))
            mz2 = (n + 2.0 * sum(z[i] * z[j] for i in range(n) for j in range(i + 1, n))) / (n * n)
            accum["mz2"] += w * float(mz2)
            accum["mz"] += w * float(np.mean(z))
    return {k: float(v) for k, v in accum.items()}


def combined_metrics(z_counts, x_counts, n: int, g: float,
                     weights: list[np.ndarray] | None = None) -> dict[str, float]:
    z = shot_stats(z_counts, n, "Z", weights)
    x = shot_stats(x_counts, n, "X", weights)
    mx = x["x_sum"] / n
    return {
        "energy": -z["zz_sum"] - g * x["x_sum"],
        "mx": mx,
        "czz_nn": z["czz_nn"],
        "mz2": z["mz2"],
        "mz": z["mz"],
    }


def zne_zero(values: np.ndarray) -> float:
    design = np.column_stack([np.ones(len(SCALES)), np.asarray(SCALES, dtype=float)])
    intercept = np.linalg.lstsq(design, values, rcond=None)[0][0]
    return float(intercept)


def bootstrap_metrics(count_grid, calibration, n: int, g: float, rng: np.random.Generator):
    """Bootstrap multinomial measurement and calibration counts, returning methods."""
    draws = {name: defaultdict(list) for name in ("raw", "readout_corrected", "zne", "zne_readout_corrected")}
    for _ in range(BOOTSTRAPS):
        cal_sample = {key: sample_counts(counts, SHOTS, rng) for key, counts in calibration.items()}
        weights = assignment_z_weights(cal_sample, n)
        raw_by_scale, corrected_by_scale = [], []
        for scale in SCALES:
            z_sample = sample_counts(count_grid[(scale, "Z")], SHOTS, rng)
            x_sample = sample_counts(count_grid[(scale, "X")], SHOTS, rng)
            raw_by_scale.append(combined_metrics(z_sample, x_sample, n, g))
            corrected_by_scale.append(combined_metrics(z_sample, x_sample, n, g, weights))
        for name, values in (("raw", raw_by_scale[0]),
                             ("readout_corrected", corrected_by_scale[0])):
            for observable, value in values.items():
                draws[name][observable].append(value)
        for observable in raw_by_scale[0]:
            draws["zne"][observable].append(zne_zero(np.asarray([r[observable] for r in raw_by_scale])))
            draws["zne_readout_corrected"][observable].append(
                zne_zero(np.asarray([r[observable] for r in corrected_by_scale])))
    return {method: {obs: np.asarray(values, dtype=float) for obs, values in obs_rows.items()}
            for method, obs_rows in draws.items()}


def main() -> None:
    processor = sim.load_processor(str(ROOT / "processors/processor_D.json"))
    selections = json.loads((ROOT / "results/raw/s1_noisy_selection.json").read_text(encoding="utf-8"))
    raw_rows = read_csv(ROOT / "results/raw/s1_seed_runs.csv")
    raw_index = {(float(r["g"]), int(r["layers"]), int(r["seed"])): r for r in raw_rows}
    exact_rows = {float(r["g"]): r for r in read_csv(ROOT / "results/tables/s1_exact_reference.csv")}
    calibrations = calibration_counts(4, processor)
    data_grid = {}
    targets = {}
    circuit_info = {}
    for gi, g in enumerate(GS):
        selection = selections[f"{g:.1f}"]
        layers, seed = int(selection["layers"]), int(selection["seed"])
        theta = np.asarray(selection["theta"], dtype=float)
        selected_raw = raw_index[(g, layers, seed)]
        if not np.allclose(theta, np.asarray(json.loads(selected_raw["theta_json"]), dtype=float), atol=1e-12, rtol=0):
            raise RuntimeError(f"saved noisy selection differs from raw theta at g={g}")
        circuit, params = sim.hva_ansatz(4, layers, zz_mode="rzz")
        bound = circuit.assign_parameters(dict(zip(params, theta)))
        H = sim.tfim_hamiltonian(4, J=1.0, g=g, periodic=False)
        state = Statevector(bound)
        exact_state = sim.expectations(state, sim.observable_ops(4))
        ideal_energy = float(np.real(state.expectation_value(H)))
        targets[g] = {**exact_state, "energy": ideal_energy}
        circuit_info[g] = (layers, seed)
        for scale in SCALES:
            p2_scaled = P2 * scale
            for basis in ("Z", "X"):
                seed_sim = sim.SEED + 1000 * gi + int(scale * 10) + (0 if basis == "Z" else 100)
                data_grid[(scale, basis, g)] = run_counts(
                    bound, processor, basis, p1=P1, p2=p2_scaled, p_ro=P_READOUT,
                    shots=SHOTS, seed=seed_sim)
                print(f"MEASURED g={g:g} alpha_p2={scale:g} basis={basis} shots={SHOTS}", flush=True)

    # One globally re-used calibration set: 2 preparations per logical qubit.
    rows = []
    value_groups = defaultdict(dict)
    se_groups = defaultdict(dict)
    for gi, g in enumerate(GS):
        count_grid = {(scale, basis): data_grid[(scale, basis, g)]
                      for scale in SCALES for basis in ("Z", "X")}
        base_weights = assignment_z_weights(calibrations, 4)
        point = {}
        for method in ("raw", "readout_corrected", "zne", "zne_readout_corrected"):
            if method == "raw":
                point[method] = combined_metrics(count_grid[(1.0, "Z")], count_grid[(1.0, "X")], 4, g)
            elif method == "readout_corrected":
                point[method] = combined_metrics(count_grid[(1.0, "Z")], count_grid[(1.0, "X")], 4, g, base_weights)
            elif method == "zne":
                per_scale = [combined_metrics(count_grid[(scale, "Z")], count_grid[(scale, "X")], 4, g)
                             for scale in SCALES]
                point[method] = {obs: zne_zero(np.asarray([r[obs] for r in per_scale])) for obs in per_scale[0]}
            else:
                per_scale = [combined_metrics(count_grid[(scale, "Z")], count_grid[(scale, "X")], 4, g, base_weights)
                             for scale in SCALES]
                point[method] = {obs: zne_zero(np.asarray([r[obs] for r in per_scale])) for obs in per_scale[0]}
        rng = np.random.default_rng(650000 + gi)
        boot = bootstrap_metrics(count_grid, calibrations, 4, g, rng)
        for observable in ("energy", "mx", "czz_nn", "mz2", "mz"):
            target = targets[g][observable]
            entry = {"scope": SCOPE, "g": g, "layers": circuit_info[g][0], "seed": circuit_info[g][1],
                     "observable": observable, "ideal_selected_circuit_target": target,
                     "target_definition": "noiseless expectation of the same saved selected HVA parameters",
                     "alpha_p2_scales": "1.0;1.5;2.0", "p1_fixed": P1, "p2_baseline": P2,
                     "p_readout_fixed": P_READOUT, "shots_per_basis_per_scale": SHOTS,
                     "bootstrap_replicates": BOOTSTRAPS,
                     "readout_calibration_model": "ideal prep; p1=p2=0; p_readout=0.01 synthetic; local single-qubit matrices"}
            for method in ("raw", "readout_corrected", "zne", "zne_readout_corrected"):
                estimate = float(point[method][observable])
                standard_error = float(np.std(boot[method][observable], ddof=1))
                entry[f"{method}_value"] = estimate
                entry[f"{method}_se"] = standard_error
                entry[f"{method}_abs_error"] = abs(estimate - target)
                value_groups[(g, observable)][method] = estimate
                se_groups[(g, observable)][method] = standard_error
            rows.append(entry)
        for observable in ("energy", "mx", "czz_nn", "mz2", "mz"):
            vals = {m: (point[m][observable], float(np.std(boot[m][observable], ddof=1)))
                    for m in point}
            print(f"MITIGATION g={g:g} {observable}: " + "; ".join(
                f"{m}={vals[m][0]:+.6f}±{vals[m][1]:.3g} abs_err={abs(vals[m][0]-targets[g][observable]):.6g}"
                for m in ("raw", "readout_corrected", "zne", "zne_readout_corrected")), flush=True)

    columns = list(rows[0])
    write_csv(ROOT / "results/additional/mitigation_d_results.csv", columns, rows)
    calibration_circuits = 2 * 4
    baseline_circuits = len(GS) * 2
    zne_extra_circuits = len(GS) * 2 * (len(SCALES) - 1)
    calibration_shots = calibration_circuits * SHOTS
    baseline_shots = baseline_circuits * SHOTS
    zne_extra_shots = zne_extra_circuits * SHOTS
    cost = [{
        "scope": SCOPE,
        "data_experiment": "N=4 selected D HVA; Z basis for ZZ/mz observables, X basis for mx/energy terms",
        "official_baseline_data_circuits_at_alpha_1": baseline_circuits,
        "additional_p2_scale_data_circuits_at_alpha_1_5_and_2": zne_extra_circuits,
        "readout_calibration_circuits_reused": calibration_circuits,
        "total_unique_data_circuits": baseline_circuits + zne_extra_circuits,
        "total_unique_circuits_including_calibration": baseline_circuits + zne_extra_circuits + calibration_circuits,
        "shots_per_circuit": SHOTS,
        "baseline_data_shots_at_alpha_1": baseline_shots,
        "additional_shots_for_p2_scales": zne_extra_shots,
        "readout_calibration_shots": calibration_shots,
        "total_data_and_calibration_shots": baseline_shots + zne_extra_shots + calibration_shots,
        "extra_circuits_vs_raw_alpha_1": zne_extra_circuits + calibration_circuits,
        "extra_shots_vs_raw_alpha_1": zne_extra_shots + calibration_shots,
        "calibration_reuse": "same eight local assignment circuits reused across all three g values and all p2 scales",
        "noise_settings": "data: p1=0.001, p2=0.005*alpha, p_readout=0.01; calibration: ideal state prep, p1=p2=0, p_readout=0.01",
    }]
    write_csv(ROOT / "results/additional/mitigation_d_costs.csv", list(cost[0]), cost)

    fig, axes = plt.subplots(len(GS), 5, figsize=(17, 10), constrained_layout=True)
    methods = ("raw", "readout_corrected", "zne", "zne_readout_corrected")
    method_labels = ("Raw", "Readout", "ZNE", "ZNE+RO")
    colors = ("#777777", "#1f77b4", "#ff7f0e", "#2ca02c")
    for gi, g in enumerate(GS):
        for oi, observable in enumerate(("energy", "mx", "czz_nn", "mz2", "mz")):
            ax = axes[gi, oi]
            values = [value_groups[(g, observable)][m] for m in methods]
            errors = [se_groups[(g, observable)][m] for m in methods]
            ax.errorbar(range(4), values, yerr=errors, fmt="o", capsize=3, color="#222222")
            ax.axhline(targets[g][observable], color="#b22222", linestyle="--", linewidth=1,
                       label="noiseless selected-circuit target")
            ax.set_xticks(range(4), method_labels, rotation=25)
            ax.set_title(f"g={g:g}: {observable}", fontsize=9)
            ax.grid(alpha=0.2)
            if gi == 0 and oi == 0:
                ax.legend(fontsize=7)
    fig.suptitle("Additional, not part of the official required results — D readout correction and p2-only ZNE\n"
                 "Points are estimates; bars are bootstrap standard errors; noise is synthetic", fontsize=12)
    fig.savefig(ROOT / "results/figures/additional_mitigation_d.png", dpi=300)
    plt.close(fig)
    print(f"MITIGATION_COSTS: baseline data {baseline_circuits} circuits/{baseline_shots} shots; "
          f"ZNE extra {zne_extra_circuits} circuits/{zne_extra_shots} shots; "
          f"calibration {calibration_circuits} circuits/{calibration_shots} shots; "
          f"total {baseline_circuits+zne_extra_circuits+calibration_circuits} circuits/"
          f"{baseline_shots+zne_extra_shots+calibration_shots} shots; p2 scales only; figure dpi=300")


if __name__ == "__main__":
    main()
