#!/usr/bin/env python3
"""Extension runner: adds L=9..12 for g=0.5, 0.75, 1.0 only.

Parallelized across CPU cores for efficiency, with safe incremental write.
Appends to results/additional/s1_n6_seed_runs.csv.
Then regenerates ALL derived tables and figures.
"""
from __future__ import annotations
import csv, json, math, sys, time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.optimize import minimize
from qiskit.quantum_info import SparsePauliOp, Statevector, state_fidelity

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import qff_sim as sim

GS = [0.25, 0.50, 0.75, 1.00, 1.25, 1.50, 2.00]
G_EXTEND = [0.5, 0.75, 1.0]
SEEDS = [0, 1, 2]
L_EXTEND = [9, 10, 11, 12]
OPTIONS = {"maxiter": 250, "maxfun": 30000, "ftol": 1e-12, "gtol": 1e-7}
MAX_WORKERS = 4

OUT = ROOT / "results/additional"
RAW = OUT / "s1_n6_seed_runs.csv"
EXACT = OUT / "s1_n6_exact_reference.csv"
AGG = OUT / "s1_n6_results.csv"
LAYER = OUT / "s1_n6_layer_study.csv"

RAW_COLS = [
    "N", "g", "layers", "seed", "energy", "exact_E0", "exact_E1",
    "energy_err", "fidelity", "fidelity_2", "mx", "czz_nn", "mz2", "mz",
    "optimizer_calls", "n_params", "success", "status", "message",
    "runtime_seconds", "theta_json"
]


def run_single_vqe(args):
    g, L, seed, data_dir_str = args
    data_dir = Path(data_dir_str)
    name = f"tfim_open_N6_g{g:.2f}.json"
    obj = json.loads((data_dir / name).read_text(encoding="utf-8"))
    H = SparsePauliOp.from_list([(lab, float(c)) for lab, c in obj["operator"]])
    vals, states = sim.exact_spectrum(H, 2)
    
    qc, params = sim.hva_ansatz(6, L, zz_mode="cx")
    x0 = np.random.default_rng(seed).uniform(-np.pi, np.pi, len(params))
    cost = sim.CountedCost(lambda x: sim.energy_statevector(qc.assign_parameters(dict(zip(params, x))), H))
    
    t0 = time.perf_counter()
    res = minimize(cost, x0, method="L-BFGS-B", jac="3-point", options=OPTIONS)
    elapsed = time.perf_counter() - t0
    
    theta = np.asarray(res.x, dtype=float)
    state = Statevector(qc.assign_parameters(dict(zip(params, theta))))
    obs = sim.expectations(state, sim.observable_ops(6))
    f0 = float(state_fidelity(states[0], state))
    f2 = f0 + float(state_fidelity(states[1], state))
    
    row = {
        "N": 6, "g": g, "layers": L, "seed": seed,
        "energy": float(res.fun),
        "exact_E0": float(vals[0]), "exact_E1": float(vals[1]),
        "energy_err": float(res.fun - float(vals[0])),
        "fidelity": f0, "fidelity_2": f2,
        "mx": obs["mx"], "czz_nn": obs["czz_nn"],
        "mz2": obs["mz2"], "mz": obs["mz"],
        "optimizer_calls": cost.calls,
        "n_params": len(params),
        "success": bool(res.success),
        "status": int(res.status),
        "message": str(res.message),
        "runtime_seconds": elapsed,
        "theta_json": json.dumps(theta.tolist(), separators=(",", ":"))
    }
    return (g, L, seed), row


def write_csv(path, cols, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def minimal_threshold_layer(layer_rows, g, threshold=1e-3):
    passing = [int(row["layers"]) for row in layer_rows
               if float(row["g"]) == float(g) and abs(float(row["energy_err"])) < threshold]
    return min(passing) if passing else None


def main():
    wall_start = time.perf_counter()
    OUT.mkdir(parents=True, exist_ok=True)
    
    # Load exact references
    refs = {}
    for g in GS:
        name = f"tfim_open_N6_g{g:.2f}.json"
        obj = json.loads((ROOT / "data/s1" / name).read_text(encoding="utf-8"))
        H = SparsePauliOp.from_list([(lab, float(c)) for lab, c in obj["operator"]])
        vals, states = sim.exact_spectrum(H, 2)
        ex = sim.expectations(states[0], sim.observable_ops(6))
        refs[g] = (H, vals, states, ex)
    
    # Load existing rows
    done = {}
    if RAW.exists():
        with RAW.open(newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                done[(float(r["g"]), int(r["layers"]), int(r["seed"]))] = r
    print(f"Resuming: {len(done)} rows already in {RAW.name}", flush=True)
    
    # Gather tasks
    tasks = []
    for g in G_EXTEND:
        for L in L_EXTEND:
            for seed in SEEDS:
                if (g, L, seed) not in done:
                    tasks.append((g, L, seed, str(ROOT / "data/s1")))
    
    print(f"Total extension tasks to run: {len(tasks)} (workers={MAX_WORKERS})", flush=True)
    
    if tasks:
        with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_task = {executor.submit(run_single_vqe, t): t for t in tasks}
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    key, row = future.result()
                    done[key] = row
                    # Incremental flush
                    write_csv(RAW, RAW_COLS, list(done.values()))
                    print(f"DONE N6 g={row['g']:.2f} L={row['layers']} seed={row['seed']} | "
                          f"Eerr={row['energy_err']:+.4e} succ={row['success']} "
                          f"calls={row['optimizer_calls']} sec={row['runtime_seconds']:.1f}", flush=True)
                except Exception as exc:
                    print(f"ERROR on task {task}: {exc}", file=sys.stderr, flush=True)
    
    print(f"\nAll tasks finished. Total raw starts in memory: {len(done)}", flush=True)
    
    # Determine layers per g
    g_to_layers = {}
    for (g, L, _s) in done:
        g_to_layers.setdefault(g, set()).add(L)
    g_to_layers = {g: sorted(layers) for g, layers in g_to_layers.items()}
    all_layers = sorted({L for layers in g_to_layers.values() for L in layers})
    max_L = max(all_layers) if all_layers else 8
    
    # Regenerate results and layer study
    ag = []
    lr = []
    for g in GS:
        ex = refs[g][3]
        for L in g_to_layers.get(g, []):
            rr = [done[(g, L, s)] for s in SEEDS if (g, L, s) in done]
            if len(rr) < 3:
                continue
            win = min(rr, key=lambda x: float(x["energy"]))
            ag.append({
                "N": 6, "g": g, "layers": L,
                "best_seed": int(win["seed"]),
                "best_energy": float(win["energy"]),
                "exact_E0": float(win["exact_E0"]),
                "energy_err": float(win["energy_err"]),
                "fidelity": float(win["fidelity"]),
                "fidelity_2": float(win["fidelity_2"]),
                "mx": float(win["mx"]), "mx_exact": ex["mx"],
                "czz_nn": float(win["czz_nn"]), "czz_nn_exact": ex["czz_nn"],
                "mz2": float(win["mz2"]), "mz2_exact": ex["mz2"],
                "mz": float(win["mz"]),
                "optimizer_calls": int(win["optimizer_calls"]),
                "n_params": int(win["n_params"])
            })
            lr.append({
                "N": 6, "g": g, "layers": L,
                "best_seed": int(win["seed"]),
                "best_energy": float(win["energy"]),
                "energy_err": float(win["energy_err"]),
                "abs_energy_err": abs(float(win["energy_err"])),
                "any_seed_success": any(str(r["success"]).strip().lower() in ("true", "1") for r in rr),
                "optimizer_calls_winner": int(win["optimizer_calls"])
            })
    
    write_csv(AGG, list(ag[0]), ag)
    write_csv(LAYER, list(lr[0]), lr)
    print(f"WROTE s1_n6_results.csv ({len(ag)} rows), s1_n6_layer_study.csv ({len(lr)} rows)", flush=True)
    
    # Regenerate minimal layers and resources
    minimal = []
    resource_rows = []
    p_b = sim.PROCESSOR_B
    p_d = sim.load_processor(str(ROOT / "processors/processor_D.json"))
    
    for g in GS:
        layer_rows = [r for r in lr if float(r["g"]) == g]
        chosen_layer = minimal_threshold_layer(layer_rows, g)
        passing = [r for r in layer_rows if abs(float(r["abs_energy_err"])) < 1e-3]
        max_tested = max(g_to_layers.get(g, [8]))
        
        if chosen_layer is not None:
            candidates = [done[(g, chosen_layer, s)] for s in SEEDS if (g, chosen_layer, s) in done]
            winner = min(candidates, key=lambda r: float(r["energy"]))
            role = "first_threshold_layer"
            min_field = str(chosen_layer)
        else:
            winner = min((r for key, r in done.items() if key[0] == g), key=lambda r: abs(float(r["energy_err"])))
            chosen_layer = int(winner["layers"])
            role = "best_available_threshold_not_reached"
            min_field = f"NOT_REACHED_L<={max_tested}"
            
        chosen_seed = int(winner["seed"])
        selected_error = float(winner["energy_err"])
        selected_success = str(winner["success"]).lower() in ("true", "1")
        at_layer = [done[(g, chosen_layer, s)] for s in SEEDS if (g, chosen_layer, s) in done]
        
        sel_rule = f"lowest L meeting strict threshold; best energy among its seeds; otherwise smallest absolute error over L=1..{max_tested} and seeds 0..2"
        minimal.append({
            "scope": "additional, not part of the official required results",
            "N": 6, "g": g,
            "minimal_L_abs_err_lt_1e-3": min_field,
            "threshold_met_within_L1_to_L8": bool(passing),
            "selected_seed": chosen_seed,
            "selected_L": chosen_layer,
            "selected_energy_error": selected_error,
            "selected_optimizer_success": selected_success,
            "failed_starts_at_selected_L": sum(str(r["success"]).lower() not in ("true", "1") for r in at_layer),
            "selection_rule": sel_rule
        })
        print(f"Minimal layer g={g:.2f}: {min_field} (sel_L={chosen_layer}, seed={chosen_seed}, err={selected_error:+.4e})", flush=True)
        
        for proc, mode in ((p_b, "cx"), (p_d, "rzz")):
            qc, params = sim.hva_ansatz(6, chosen_layer, zz_mode=mode)
            bound = qc.assign_parameters(dict(zip(params, json.loads(winner["theta_json"]))))
            metrics = sim.circuit_metrics(bound, proc)
            resource_rows.append({
                "scope": "additional, not part of the official required results",
                "circuit_label": f"n6_hva_g{g:.2f}_L{chosen_layer}_best_seed{chosen_seed}_{mode}",
                "N": 6, "g": g, "layers": chosen_layer, "seed": chosen_seed,
                "selection_status": role, "processor": proc["name"][-1], "zz_mode": mode,
                "executable": True, "reason": "",
                "logical_qubits": metrics["logical_qubits"],
                "physical_qubits": metrics["physical_qubits"],
                "logical_2q": metrics["logical_cx"],
                "two_q": metrics["cx"], "depth": metrics["depth"],
                "two_q_depth": metrics["two_q_depth"],
                "swaps": metrics["swaps"],
                "routing_overhead_2q": metrics["cx_overhead"],
                "selected_energy_error": selected_error,
                "optimizer_success": selected_success
            })
            
    write_csv(OUT / "s1_n6_minimal_layers.csv", list(minimal[0]), minimal)
    
    capacity = {
        "scope": "additional, not part of the official required results",
        "circuit_label": "n6_optional_capacity_check",
        "N": 6, "g": "all", "layers": "N/A", "seed": "N/A",
        "selection_status": "processor_capacity", "processor": "A", "zz_mode": "N/A",
        "executable": False,
        "reason": "not executable: needs 6 qubits, has 5",
        "logical_qubits": 6, "physical_qubits": 5,
        "logical_2q": "NA", "two_q": "NA", "depth": "NA", "two_q_depth": "NA",
        "swaps": "NA", "routing_overhead_2q": "NA",
        "selected_energy_error": "NA", "optimizer_success": "NA"
    }
    resource_rows.insert(0, capacity)
    write_csv(OUT / "s1_n6_resources.csv", list(resource_rows[0]), resource_rows)
    print(f"WROTE s1_n6_minimal_layers.csv ({len(minimal)} rows), s1_n6_resources.csv ({len(resource_rows)} rows)", flush=True)
    
    # Plot figure
    fig, ax = plt.subplots(figsize=(9, 5.5), constrained_layout=True)
    for g in GS:
        rr = sorted((r for r in lr if float(r["g"]) == g), key=lambda r: int(r["layers"]))
        ys = [max(float(r["abs_energy_err"]), 1e-16) for r in rr]
        ax.plot([int(r["layers"]) for r in rr], ys, marker="o", label=f"g={g:g}")
    ax.axhline(1e-3, color="black", linestyle="--", linewidth=1, label="strict threshold 1e-3")
    ax.set_yscale("log")
    ax.set_xticks(list(range(1, max_L + 1)))
    ax.set(xlabel="HVA layers L (N=6)", ylabel="Absolute energy error",
           title="Additional, not part of the official required results: N=6 VQE layer study (seeds 0,1,2)")
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(ncol=2, fontsize=8)
    fig.savefig(ROOT / "results/figures/additional_n6_layer_study.png", dpi=300)
    plt.close(fig)
    print("WROTE results/figures/additional_n6_layer_study.png at 300 DPI", flush=True)
    
    elapsed_total = time.perf_counter() - wall_start
    print(f"\nALL DONE in {elapsed_total:.1f}s ({elapsed_total/60:.1f} min)", flush=True)


if __name__ == "__main__":
    main()
