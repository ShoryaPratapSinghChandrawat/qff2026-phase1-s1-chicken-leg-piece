#!/usr/bin/env python3
"""Exact sparse finite-size scaling for additional PS-S1 research only.

No required result table is read or written. Outputs are confined to
results/additional/ and results/figures/additional_*.png.
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
from scipy.sparse.linalg import eigsh
from qiskit.quantum_info import Statevector, partial_trace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import qff_sim as sim  # noqa: E402

SCOPE = "additional, not part of the official required results"
SIZES = (4, 6, 8, 10, 12)
G_VALUES = tuple(round(0.25 + 0.05 * i, 2) for i in range(36))
OFFICIAL_G = (0.25, 0.50, 0.75, 1.00, 1.25, 1.50, 2.00)
TOL = 1e-9


def write_csv(path: Path, columns: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="raise", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sparse_low_energy(H, n: int, g: float):
    matrix = H.to_matrix(sparse=True).tocsr()
    seed = 91000 + n
    rng = np.random.default_rng(seed)
    v0 = rng.normal(size=matrix.shape[0])
    vals, vecs = eigsh(matrix, k=2, which="SA", tol=1e-12, maxiter=50000,
                       ncv=min(matrix.shape[0], 40), v0=v0)
    order = np.argsort(vals)
    vals = np.asarray(vals[order], dtype=float)
    vecs = vecs[:, order]
    imag_max = float(np.max(np.abs(vecs.imag)))
    if imag_max > 1e-12:
        raise RuntimeError(f"eigsh eigenvectors have non-negligible imaginary part for N={n}, g={g}: {imag_max}")
    vecs = np.asarray(vecs.real, dtype=float)
    # Normalize signs for reproducible serialized calculations. Observables do
    # not depend on this convention, but it stabilizes diagnostics.
    for j in range(vecs.shape[1]):
        pivot = int(np.argmax(np.abs(vecs[:, j])))
        if vecs[pivot, j] < 0:
            vecs[:, j] *= -1
    if not np.all(np.isfinite(vals)) or not np.all(np.isfinite(vecs)):
        raise RuntimeError(f"eigsh returned non-finite result for N={n}, g={g}")
    return vals, vecs


def half_chain_entropy(vector: np.ndarray, n: int) -> float:
    state = Statevector(vector / np.linalg.norm(vector))
    reduced = partial_trace(state, list(range(n // 2, n)))
    eig = np.linalg.eigvalsh(np.asarray(reduced.data, dtype=complex)).real
    eig = np.clip(eig, 0.0, None)
    eig = eig[eig > 1e-14]
    return float(-np.sum(eig * np.log2(eig)))


def crossings(rows: list[dict]) -> list[dict]:
    by_key = {(int(r["N"]), float(r["g"])): float(r["gap_times_N"]) for r in rows}
    out = []
    for n1, n2 in zip(SIZES[:-1], SIZES[1:]):
        found = []
        for g0, g1 in zip(G_VALUES[:-1], G_VALUES[1:]):
            d0 = by_key[(n1, g0)] - by_key[(n2, g0)]
            d1 = by_key[(n1, g1)] - by_key[(n2, g1)]
            if d0 == 0:
                found.append(g0)
            elif d0 * d1 < 0:
                found.append(g0 + (g1 - g0) * (-d0) / (d1 - d0))
        if by_key[(n1, G_VALUES[-1])] == by_key[(n2, G_VALUES[-1])]:
            found.append(G_VALUES[-1])
        if not found:
            out.append({"scope": SCOPE, "quantity": "N times gap", "N_small": n1,
                        "N_large": n2, "g_crossing_linear_interpolation": "NA",
                        "status": "no sign-change crossing on sampled grid"})
        else:
            for g_cross in sorted(set(found)):
                out.append({"scope": SCOPE, "quantity": "N times gap", "N_small": n1,
                            "N_large": n2, "g_crossing_linear_interpolation": g_cross,
                            "status": "linear interpolation between 0.05-spaced grid points"})
    return out


def main() -> None:
    output = ROOT / "results/additional"
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    ref_checks = []
    for n in SIZES:
        rng = np.random.default_rng(91000 + n)
        for g in G_VALUES:
            H = sim.tfim_hamiltonian(n, J=1.0, g=g, periodic=False)
            vals, vecs = sparse_low_energy(H, n, g)
            gap = float(vals[1] - vals[0])
            obs = sim.observable_ops(n)
            psi0 = Statevector(vecs[:, 0])
            mz2_n2 = float(np.real(psi0.expectation_value(obs["mz2"])))
            entropy = half_chain_entropy(vecs[:, 0], n)
            meta_e0 = meta_e1 = "NA"
            d0 = d1 = "NA"
            checked = False
            if n in (4, 6) and g in OFFICIAL_G:
                official_path = ROOT / "data/s1" / f"tfim_open_N{n}_g{g:.2f}.json"
                instance = json.loads(official_path.read_text(encoding="utf-8"))
                meta_e0 = float(instance["meta"]["E0_exact"])
                meta_e1 = float(instance["meta"]["E1_exact"])
                d0 = abs(float(vals[0]) - meta_e0)
                d1 = abs(float(vals[1]) - meta_e1)
                if d0 > TOL or d1 > TOL:
                    raise RuntimeError(f"official metadata mismatch N={n}, g={g}: E0={d0}, E1={d1}")
                checked = True
                ref_checks.append((n, g, d0, d1))
            rows.append({
                "scope": SCOPE, "solver": "scipy.sparse.linalg.eigsh",
                "N": n, "g": g, "E0_sparse": float(vals[0]), "E1_sparse": float(vals[1]),
                "gap": gap, "gap_times_N": gap * n,
                "half_chain_entropy_bits": entropy, "mz2_over_N2": mz2_n2,
                "reference_checked": checked, "E0_metadata": meta_e0,
                "E1_metadata": meta_e1, "E0_abs_diff": d0, "E1_abs_diff": d1,
                "eigsh_tolerance": 1e-12, "deterministic_v0_seed": 91000 + n,
            })
            print(f"N={n} g={g:.2f} gap={gap:.10g} N_gap={gap*n:.10g} "
                  f"S_half={entropy:.8f} Mz2_N2={mz2_n2:.8f}", flush=True)

    columns = list(rows[0])
    write_csv(output / "finite_size_scaling.csv", columns, rows)
    cross_rows = crossings(rows)
    write_csv(output / "finite_size_crossings.csv", list(cross_rows[0]), cross_rows)

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8), constrained_layout=True)
    colors = {4: "#1f77b4", 6: "#ff7f0e", 8: "#2ca02c", 10: "#d62728", 12: "#9467bd"}
    for n in SIZES:
        rr = [r for r in rows if r["N"] == n]
        gs = [r["g"] for r in rr]
        axes[0].plot(gs, [r["gap_times_N"] for r in rr], color=colors[n], label=f"N={n}")
        axes[1].plot(gs, [r["half_chain_entropy_bits"] for r in rr], color=colors[n], label=f"N={n}")
        axes[2].plot(gs, [r["mz2_over_N2"] for r in rr], color=colors[n], label=f"N={n}")
    for ax in axes:
        ax.axvline(1.0, color="black", linestyle="--", linewidth=1,
                   label=r"$g_c=1$ (infinite chain)")
        ax.grid(alpha=0.25)
    axes[0].set(xlabel="g", ylabel="N(E1−E0)", title="Scaled finite-size gap")
    axes[1].set(xlabel="g", ylabel="Half-chain entropy (bits)", title="Ground-state entanglement")
    axes[2].set(xlabel="g", ylabel=r"$\langle M_z^2\rangle/N^2$", title="Longitudinal order diagnostic")
    axes[0].legend(ncol=2, fontsize=8)
    axes[1].legend(ncol=2, fontsize=8)
    axes[2].legend(ncol=2, fontsize=8)
    fig.suptitle("Additional, not part of the official required results — exact sparse open TFIM, N≤12")
    fig.savefig(ROOT / "results/figures/additional_finite_size_scaling.png", dpi=300)
    plt.close(fig)

    observed = [float(r["g_crossing_linear_interpolation"]) for r in cross_rows
                if r["g_crossing_linear_interpolation"] != "NA"]
    if observed:
        crossing_sentence = ", ".join(
            f"N={r['N_small']} vs {r['N_large']}: g≈{float(r['g_crossing_linear_interpolation']):.4f}"
            for r in cross_rows if r["g_crossing_linear_interpolation"] != "NA")
    else:
        crossing_sentence = "no sign-change crossings were found on the sampled grid"
    interpretation = (
        f"{SCOPE.capitalize()}: Exact sparse diagonalization on the open TFIM at N=4,6,8,10,12 and "
        f"36 fields from g=0.25 to 2.00 in 0.05 steps shows the finite-size trends in N(E1−E0), "
        f"half-chain entropy, and <Mz^2>/N^2; adjacent-size N-gap crossings from linear interpolation are {crossing_sentence}. "
        f"The known infinite-chain critical value is g_c=1. The crossings and changing entropy/order diagnostics near g=1 "
        f"are consistent with finite-size critical scaling, but this N≤12 open-chain data set does not establish a new "
        f"critical point, critical exponent, thermodynamic limit, or hardware behavior. N=4 and N=6 sparse E0/E1 values "
        f"were each checked against all seven official reference files at absolute tolerance {TOL:g} "
        f"({len(ref_checks)} size-field pairs; {2*len(ref_checks)} eigenvalue comparisons passed)."
    )
    (output / "finite_size_scaling_interpretation.md").write_text(
        "# Additional finite-size scaling interpretation\n\n" + interpretation + "\n",
        encoding="utf-8", newline="")
    print(f"FINITE_SIZE_OK: rows={len(rows)}; official N=4/6 checks={len(ref_checks)} size-field pairs "
          f"({2*len(ref_checks)} E0/E1 comparisons); crossings={len(observed)}; figure dpi=300")


if __name__ == "__main__":
    main()
