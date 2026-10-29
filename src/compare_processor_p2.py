#!/usr/bin/env python3
"""Compare one saved logical HVA circuit across A/B/D and both ZZ encodings.

This supplemental runner writes only resources.csv, one additional CSV, and one
figure. It does not rerun VQE or change the official S1 result tables.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from qiskit_aer import AerSimulator
from qiskit.quantum_info import DensityMatrix, SparsePauliOp, Statevector, state_fidelity

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import qff_sim as sim  # noqa: E402

ALPHAS = (1.0, 1.25, 1.5, 2.0)
P1 = 0.001
P2_BASE = 0.005
P_READOUT = 0.01
REPRESENTATIVE_G = (0.5, 1.0, 2.0)
RESOURCE_COLUMNS = [
    "ps", "circuit_label", "processor", "executable", "logical_qubits",
    "physical_qubits", "logical_2q", "two_q", "depth", "two_q_depth",
    "swaps", "routing_overhead_2q",
]
SENSITIVITY_COLUMNS = [
    "g", "layers", "seed", "processor", "logical_zz_mode", "alpha_p2",
    "p1", "p2", "p_readout", "energy_noisy", "exact_E0",
    "energy_error_noisy", "fidelity_noisy_dm", "two_q_gates", "two_q_depth",
    "depth", "swaps", "state_fidelity_gate_noise_only",
]


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        return reader.fieldnames or [], list(reader)


def write_csv(path: Path, columns: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def metric_row(label: str, processor_label: str, metrics: dict) -> dict:
    return {
        "ps": "PS-S1",
        "circuit_label": label,
        "processor": processor_label,
        "executable": metrics.get("executable", False),
        "logical_qubits": metrics.get("logical_qubits", "NA"),
        "physical_qubits": metrics.get("physical_qubits", "NA"),
        "logical_2q": metrics.get("logical_cx", "NA"),
        "two_q": metrics.get("cx", "NA"),
        "depth": metrics.get("depth", "NA"),
        "two_q_depth": metrics.get("two_q_depth", "NA"),
        "swaps": metrics.get("swaps", "NA"),
        "routing_overhead_2q": metrics.get("cx_overhead", "NA"),
    }


def noisy_density_matrix(circuit, processor: dict, p2: float) -> DensityMatrix:
    """Official transpilation/layout with custom p2; readout is unused without measurement."""
    transpiled = sim.transpile_for(circuit, processor)
    _, logical_final_wires = sim._layout_maps(transpiled, circuit.num_qubits)
    save = transpiled.copy()
    save.save_density_matrix(qubits=logical_final_wires, label="rho")
    noise = sim.official_noise_model(p1=P1, p2=p2, p_ro=P_READOUT)
    backend = AerSimulator(method="density_matrix", noise_model=noise, seed_simulator=sim.SEED)
    result = backend.run(save).result()
    return DensityMatrix(result.data()["rho"])


def main() -> None:
    raw_header, raw_rows = read_csv(ROOT / "results/raw/s1_seed_runs.csv")
    required_raw = {"N", "g", "layers", "seed", "energy", "theta_json"}
    if not required_raw.issubset(raw_header):
        raise RuntimeError(f"raw seed table is missing: {sorted(required_raw-set(raw_header))}")
    selections = json.loads((ROOT / "results/raw/s1_noisy_selection.json").read_text(encoding="utf-8"))
    proc_d = sim.load_processor(str(ROOT / "processors/processor_D.json"))
    processors = [sim.PROCESSOR_A, sim.PROCESSOR_B, proc_d]
    for proc in processors[:2]:
        proc.setdefault("basis_gates", list(sim.BASIS_GATES))

    # Use the converged g=1,L=3,seed=2 parameters from the raw required sweep.
    base_selection = selections["1.0"]
    base_seed = int(base_selection["seed"])
    base_layers = int(base_selection["layers"])
    base_g = 1.0
    raw_base = next(
        row for row in raw_rows
        if int(row["N"]) == 4 and float(row["g"]) == base_g
        and int(row["layers"]) == base_layers and int(row["seed"]) == base_seed
    )
    theta_base = np.asarray(json.loads(raw_base["theta_json"]), dtype=float)
    if not np.allclose(theta_base, np.asarray(base_selection["theta"], dtype=float), atol=1e-12, rtol=0):
        raise RuntimeError("saved selection parameters do not match the raw seed row")

    # Rebuild the resource table with explicit source representation labels. The
    # old native A/B CX rows and D RZZ row must match before they are relabelled.
    old_header, old_resources = read_csv(ROOT / "results/tables/resources.csv")
    if old_header != RESOURCE_COLUMNS:
        raise RuntimeError(f"resources.csv schema changed: {old_header}")
    old_label = f"s1_hva_g1.00_L3_best_seed{base_seed}"
    old_by_key = {(row["circuit_label"], row["processor"]): row for row in old_resources}
    if len(old_by_key) != len(old_resources):
        raise RuntimeError("resources.csv has duplicate circuit/processor rows")
    new_resources = []
    for proc in processors:
        proc_label = proc["name"][-1]
        native_mode = "rzz" if proc_label == "D" else "cx"
        for mode in ("cx", "rzz"):
            circuit, params = sim.hva_ansatz(4, base_layers, zz_mode=mode)
            bound = circuit.assign_parameters(dict(zip(params, theta_base)))
            metrics = sim.circuit_metrics(bound, proc)
            if not metrics.get("executable"):
                raise RuntimeError(f"HVA {mode} circuit is not executable on Processor {proc_label}")
            row = metric_row(f"{old_label}_{mode}", proc_label, metrics)
            if mode == native_mode:
                original = old_by_key.get((old_label, proc_label)) or old_by_key.get((f"{old_label}_{native_mode}", proc_label))
                if original is None:
                    raise RuntimeError(f"missing prior native resource row for {proc_label}")
                for field in RESOURCE_COLUMNS[4:]:
                    if str(original[field]) != str(row[field]):
                        raise RuntimeError(
                            f"native resource mismatch on {proc_label}/{mode}/{field}: "
                            f"saved={original[field]} recomputed={row[field]}"
                        )
            new_resources.append(row)

    # Preserve the existing Bell auto-layout rows unchanged.
    bell_rows = [row for row in old_resources if row["circuit_label"] == "bell_auto_layout_ZZ"]
    if len(bell_rows) != 3 or {row["processor"] for row in bell_rows} != {"A", "B", "D"}:
        raise RuntimeError("expected the three existing Bell auto-layout resource rows")
    new_resources.extend(bell_rows)
    write_csv(ROOT / "results/tables/resources.csv", RESOURCE_COLUMNS, new_resources)

    # The same RZZ-form logical ansatz and same saved seed parameters are
    # transpiled for A/B/D. Only the processor's native basis and topology vary.
    sensitivity_rows = []
    for g in REPRESENTATIVE_G:
        selection = selections[f"{g:.1f}"]
        layers = int(selection["layers"])
        seed = int(selection["seed"])
        theta = np.asarray(selection["theta"], dtype=float)
        raw_selected = next(
            row for row in raw_rows
            if int(row["N"]) == 4 and float(row["g"]) == g
            and int(row["layers"]) == layers and int(row["seed"]) == seed
        )
        if not np.allclose(theta, np.asarray(json.loads(raw_selected["theta_json"]), dtype=float), atol=1e-12, rtol=0):
            raise RuntimeError(f"saved parameters do not match raw run for g={g}")
        instance = json.loads((ROOT / "data/s1" / f"tfim_open_N4_g{g:.2f}.json").read_text(encoding="utf-8"))
        hamiltonian = SparsePauliOp.from_list([(label, float(coef)) for label, coef in instance["operator"]])
        energies, vectors = np.linalg.eigh(hamiltonian.to_matrix())
        exact_e0 = float(energies[0])
        exact_psi = Statevector(vectors[:, 0])
        logical, params = sim.hva_ansatz(4, layers, zz_mode="rzz")
        bound = logical.assign_parameters(dict(zip(params, theta)))

        for proc in processors:
            proc_label = proc["name"][-1]
            metrics = sim.circuit_metrics(bound, proc)
            for alpha in ALPHAS:
                p2 = P2_BASE * alpha
                density = noisy_density_matrix(bound, proc, p2)
                energy = float(np.real(density.expectation_value(hamiltonian)))
                fidelity = float(state_fidelity(exact_psi, density))
                sensitivity_rows.append({
                    "g": g, "layers": layers, "seed": seed, "processor": proc_label,
                    "logical_zz_mode": "rzz", "alpha_p2": alpha, "p1": P1,
                    "p2": p2, "p_readout": P_READOUT, "energy_noisy": energy,
                    "exact_E0": exact_e0, "energy_error_noisy": energy - exact_e0,
                    "fidelity_noisy_dm": fidelity, "two_q_gates": metrics["cx"],
                    "two_q_depth": metrics["two_q_depth"], "depth": metrics["depth"],
                    "swaps": metrics["swaps"], "state_fidelity_gate_noise_only": True,
                })
    write_csv(ROOT / "results/additional/p2_processor_comparison.csv", SENSITIVITY_COLUMNS, sensitivity_rows)

    # Plot each field separately, with processor identity visible in both panels.
    colors = {"A": "#1f77b4", "B": "#ff7f0e", "D": "#2ca02c"}
    fig, axes = plt.subplots(3, 2, figsize=(12, 12), sharex=True)
    for i, g in enumerate(REPRESENTATIVE_G):
        for proc_label in ("A", "B", "D"):
            rows = sorted(
                (row for row in sensitivity_rows if row["g"] == g and row["processor"] == proc_label),
                key=lambda row: row["alpha_p2"],
            )
            alphas = [row["alpha_p2"] for row in rows]
            axes[i, 0].plot(alphas, [row["energy_error_noisy"] for row in rows], marker="o",
                            color=colors[proc_label], label=f"Processor {proc_label}")
            axes[i, 1].plot(alphas, [row["fidelity_noisy_dm"] for row in rows], marker="s",
                            color=colors[proc_label], label=f"Processor {proc_label}")
        axes[i, 0].set_ylabel(f"g={g:g}\nNoisy energy error")
        axes[i, 1].set_ylabel(f"g={g:g}\nGate-noisy fidelity")
        axes[i, 0].legend(frameon=False)
        axes[i, 1].legend(frameon=False)
        axes[i, 0].grid(alpha=0.25)
        axes[i, 1].grid(alpha=0.25)
    axes[-1, 0].set_xlabel("Two-qubit error multiplier α")
    axes[-1, 1].set_xlabel("Two-qubit error multiplier α")
    fig.suptitle("Same logical HVA parameters across A/B/D; synthetic p2 sensitivity\n"
                 "Density-matrix fidelity includes gate noise only (readout is not measured)", y=1.01)
    fig.tight_layout()
    figure_path = ROOT / "results/figures/p2_processor_comparison.png"
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(figure_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Wrote resources.csv with {len(new_resources)} rows (CX/RZZ HVA on A/B/D + 3 Bell rows).")
    print(f"Wrote p2_processor_comparison.csv with {len(sensitivity_rows)} rows.")
    print(f"Wrote {figure_path.relative_to(ROOT)} at 300 DPI.")
    for g in REPRESENTATIVE_G:
        print(f"g={g:g} baseline alpha=1 energy error / fidelity by processor:")
        for proc_label in ("A", "B", "D"):
            row = next(r for r in sensitivity_rows if r["g"] == g and r["processor"] == proc_label and r["alpha_p2"] == 1.0)
            print(f"  {proc_label}: {row['energy_error_noisy']:+.6f} / {row['fidelity_noisy_dm']:.6f}; "
                  f"2q={row['two_q_gates']}, depth={row['depth']}, swaps={row['swaps']}")


if __name__ == "__main__":
    main()
