# PS-S1: four-spin transverse-field Ising ground state

**Release candidate for QFF 2026 Phase 1 · SRM University-AP**  
**Team:** Ising Ground-State Lab · Chicken Leg Piece

> **Local release candidate / not submitted.** The exact October 14, 2026 SRM QFF Master Guide was supplied and directly reviewed. It confirms the PS-S1 Hamiltonian terms, A/B-only Phase 1 scope, reference-graph freedom, noise/compiler/shots baseline, and October 17 deadline. It does not define the magnetization axis or normalization; this candidate states its measurement conventions explicitly. No portal access, publication, or submission is claimed.

## Problem

Estimate the ground state of the open four-spin TFIM

\[
H=-J\sum_{i=0}^{2} Z_iZ_{i+1}-g\sum_{i=0}^{3}X_i,
\qquad J=1,
\qquad g\in\{0.5,1.0,1.5\}.
\]

We use exact diagonalization and VQE, then compare ideal compiled and controlled noisy simulation evidence for two fixed candidate coupling graphs:

- **A_branch** (5 physical nodes): `(0,1), (1,2), (1,3), (3,4)`.
- **B_ref12** (9 physical nodes): `(0,1), (1,2), (1,6), (2,3), (2,6), (2,5), (3,4), (4,5), (5,6), (6,7), (6,8), (8,0)`.

These match the current guide's A/B reference examples; the guide explicitly permits participant-designed coupling maps. They are fixed candidate maps, not hardware calibrations. Graph motif counts are descriptive topology features, not circuit performance.

## Reproduce locally

Python 3.13 was used for the recorded candidate environment. From this directory:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip check
.venv/bin/python -m pytest -q
EXEC_DIR="$(mktemp -d)"
PATH="$PWD/.venv/bin:$PATH" .venv/bin/python -m nbconvert --to notebook --execute main.ipynb --output main.executed.ipynb --output-dir "$EXEC_DIR" --ExecutePreprocessor.kernel_name=python3 --ExecutePreprocessor.timeout=1800
```

The notebook uses the standard `python3` kernelspec, only relative project paths, and no website or network resources. The full run is CPU-heavy: the nine 16-parameter ideal VQE starts dominate runtime. See `docs/CLEAN_REPRODUCTION.md` for the actual validation ledger after execution.

## Method and conventions

- Seven-term Pauli Hamiltonian is cross-checked against an independently assembled dense matrix; sparse and free-fermion references provide additional checks. In Qiskit labels the rightmost Pauli character acts on logical qubit 0.
- VQE ansatz: RY+CX, four full RY layers, three nearest-neighbor entangler sweeps (`reps=3`, 16 parameters). L-BFGS-B uses exact parameter-shift gradients. Initialization seeds: 42, 7, 21.
- The original `g=1.5`, seed-42, `maxiter=500` result remains classified as an iteration-limit failure. A continuation from its saved parameters is a separate diagnostic, never a replacement.
- Observables: `Mz_per_site=<sum Z>/4`, `Mx_per_site=<sum X>/4`, `Mz2_normalized=<(sum Z)^2>/16`, and each of the three nearest-neighbor `ZZ` correlators. Tables contain exact, ideal VQE, and signed-error columns.
- Common compilation: `{rz,sx,x,cx}`, optimization level 1, SABRE layout and routing, transpiler seed 42. Synthetic Aer noise: single-qubit depolarizing `p=0.001` on RZ/SX/X, CX depolarizing `p=0.005`, symmetric readout flip `p=0.01`; A/B both use 4096 shots per measurement basis. Noise is simulated, not hardware calibration.
- Sampling uncertainty is calculated per shot within each commuting measurement group. Independent Z/X simulator seeds are used and their energy standard errors are combined in quadrature. Ideal variational error, noise-induced shift, total noisy error, and shot standard error are distinct.
- The `1e-6` absolute energy criterion is a project reporting convention only, not an organizer mandate.

## Main files

| File | Purpose |
|---|---|
| `main.ipynb` | Standard-kernel Stage 1 workflow; excludes optional Processor D/E4 and web app. |
| `src/` | TFIM, exact references, VQE, measurements, noise, routing, and graph analyses. |
| `processors/processor_A.json`, `processor_B.json` | Frozen candidate graph and common simulation assumptions. |
| `run_exact_validation.py`, `run_graph_analysis.py`, `run_benchmark.py`, `run_noisy.py` | Reproducible analysis runners. |
| `results/tables/` | Canonical exact, topology, ideal-resource, restart, and noisy tables. |
| `results/raw/` | Per-run optimizer records and sampled counts. |
| `results/figures/` | Generated primary A/B visuals. |
| `results/experiment_manifest.json` | Relative-path SHA-256/source and generated-artifact manifest. |
| `report.md` | Concise interpretation, failure, scope, and limitations. |
| `AI_DISCLOSURE.md` | Truthful assistance disclosure; not a claim of organizer-policy compliance. |

`supplementary/e4_path_ring_star/` defines the separate E4 path/ring/star runner and frozen four-node graph configs; its results are isolated under `results/supplementary/` and not loaded by `main.ipynb`.

`extras/legacy/results_pre_rebaseline/` contains historical `A_linear`/`B_kit8` outputs from the prior candidate. They are not merged into the current primary results. The earlier shallow COBYLA provenance and its optional `scripts/run_vqe_baseline_legacy.py` runner remain legacy and are not called by canonical runs; no root `run_vqe_baseline.py` is part of the canonical path. The optional website is intentionally excluded from this candidate; it remains in the untouched original workspace.

## State and limitations

This is a **local candidate**, not a submitted repository. No hardware job, portal selection check, organizer contact, public GitHub push, or submission was performed. The current guide and older source distinctions are documented in `docs/SOURCES.md`; the private source audit and team-lead checklist are outside the candidate. The undefined magnetization convention, absence of hardware data, AI-policy confirmation, contributor approval and license decision remain limitations.
