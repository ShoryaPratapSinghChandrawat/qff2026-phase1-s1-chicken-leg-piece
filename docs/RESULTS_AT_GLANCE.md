# PS-S1 results at a glance

**Team:** Swarup · Biswajit · Arhaan Sethi · Shorya Pratap Singh Chandrawat · Chicken Leg Piece<br>
**Phase 1:** [public repository](https://github.com/ShoryaPratapSinghChandrawat/qff2026-phase1-s1-chicken-leg-piece)<br>
**Scope:** QFF 2026 Phase 2 PS-S1. All values below come from saved local simulation evidence; no hardware measurements are claimed.

## Processor design and resource comparison

- **Processor D:** six qubits, seven edges, chorded-ring topology, RZZ in its native basis, graph diameter 3. It is selected as the deterministic lexical tie-break among three Pareto-equivalent RZZ candidates, not as uniquely superior. Evidence: `processors/processor_D.json`; all Pareto rows in `results/tables/d_candidates.csv`; tie-break in `src/scan_processor_d.py`.
- **Measured bottleneck:** A and B compile the open-chain HVA with zero routing SWAPs. At N=4,L=2, the CX-RZ-CX construction uses 12 two-qubit gates versus 6 for native RZZ. On selected N=4,L=3,g=1.0,seed=2, A/B/D in CX form use 18/18/18 generic two-qubit gates; native RZZ uses 18/18/9. Depth is 36/36/58 for CX and 36/36/24 for RZZ; all have zero routing SWAPs. Evidence: `results/tables/resources.csv`, HVA labels ending `_cx` and `_rzz`.
- **Resource coverage:** nine rows total: selected HVA in both CX and RZZ form on A/B/D, plus the Bell auto-layout ZZ circuit on A/B/D. The selected CX/RZZ resource labels match the best seed from the raw sweep. The Bell pair-specific gate counts are in `bell.csv`.

## Accuracy and Bell verification

- **Exact references:** all seven N=4 spectra match the supplied E0/E1 metadata within `1e-9`. Evidence: every row in `results/tables/s1_exact_reference.csv`, `E0_abs_diff`, `E1_abs_diff`.
- **VQE:** at L=4, the largest absolute energy error is `5.8797411384e-13`; selected state fidelities are 1 at displayed precision. Evidence: `results/tables/s1_results.csv`, N=4, L=4.
- **Minimum tested L at strict `|energy error| < 1e-3`:** L=4 for g=0.25, 0.50, 0.75, 1.25; L=3 for g=1.00, 1.50, 2.00. This is a best-of-three observed optimizer result, not a general depth guarantee. Evidence: `results/tables/layer_study.csv`, all L=1..4 rows.
- **Bell:** pair 0–1 has graph distance 1, one 2Q gate, noisy F=`0.959839 ± 0.002184`; pair 1–4 has distance 3, seven gates, noisy F=`0.938354 ± 0.002685`. Ideal F is 1 for both. Runner uses 4,096 shots per basis; the table verifies F and its standard-error formula. Evidence: `results/tables/bell.csv`, `src/run_bell.py`.

## Noise and boundaries of inference

- **Required noisy D density matrices:** at g=0.5/L=4/seed 0, g=1.0/L=3/seed 2, g=2.0/L=3/seed 2, fidelity is `0.892449`, `0.923128`, `0.919267`, with energy errors `0.299678`, `0.265723`, `0.535349`. `fidelity_noisy_dm` models gate noise only; readout noise is not folded into density-matrix state fidelity. Evidence: `results/tables/s1_noisy.csv`.
- **Supplemental controlled A/B/D p2 comparison:** `results/additional/p2_processor_comparison.csv` contains 36 rows using the same saved logical parameters at g={0.5,1.0,2.0} and alpha={1,1.25,1.5,2}; p2=`0.005×alpha`, p1=`0.001`, and configured readout=`0.01`. At all 12 tested g×alpha points D has lower energy error and higher gate-noisy density-matrix fidelity than A/B. Readout is not part of that density-matrix fidelity. This is a result under the supplied synthetic model, not a hardware finding. The figure is `results/figures/p2_processor_comparison.png`.
- **Finite-size analysis (additional):** 180 exact sparse-spectrum rows cover N=4, 6, 8, 10, 12 and 36 fields. Adjacent-size `N × gap` crossings are interpolated from the 0.05 grid and trend toward the known infinite-chain `g_c=1`; they do not establish a thermodynamic critical point (`results/additional/finite_size_scaling.csv`, `finite_size_crossings.csv`).
- **N=6 (additional):** 204 starts cover all seven locked fields (L=1..8 for g=0.25, 1.25, 1.50, 2.00; L=1..12 for g=0.50, 0.75, 1.00 × seeds 0, 1, 2) and preserve 88 optimizer non-success flags. The strict $|\Delta E| < 10^{-3}$ threshold is met across all seven fields: L=4 for g=2.0; L=5 for 1.5; L=8 for g=0.25 and 1.25; L=9 for g=0.50 and 0.75; and L=10 for g=1.00. At g=0.50, 0.75, 1.00, and 1.25, the minimal threshold-crossing layer has `selected_optimizer_success=False`. This is an additional research study, not an official required tier.
- **Mitigation (additional):** 15 g/observable rows use 400 bootstrap replicates, readout correction, and p2-only ZNE against the noiseless same-circuit target; all values are synthetic, not hardware results. Two required N=4 starts and 88 N=6 starts retain `success=False` and their recorded messages. Processor D is uncalibrated.

**Reproducibility:** run `python verify_submission.py`; `main.ipynb` is saved executed with `RECOMPUTE=False`. Full evidence paths and number selectors are in `docs/NUMBER_AUDIT.md`; report at the repository root and identical copy at `docs/report.md`.
