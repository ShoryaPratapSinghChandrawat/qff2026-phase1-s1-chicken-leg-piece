# QFF 2026 Phase 2 — PS-S1 | Chicken Leg Piece

**Team:** Swarup · Biswajit · Arhaan Sethi · Shorya Pratap Singh Chandrawat<br>
**Problem:** PS-S1, the open-chain transverse-field Ising ground-state simulation.<br>
**Phase 1 repository:** [qff2026-phase1-s1-chicken-leg-piece](https://github.com/ShoryaPratapSinghChandrawat/qff2026-phase1-s1-chicken-leg-piece)

This release contains the Phase 2 PS-S1 implementation, saved evidence, reproducibility checks, and research extensions. The official Phase 2 inputs and simulator remain preserved in `handoff_payload/OFFICIAL_KIT/`; `qff_sim.py` and `starter/qff_sim.py` match the official SHA-256 `dd0305834f88164f01f9b2a17f7333eb48a966cb81951b1953eed0e218de4cfc`.

## Results at a glance

- **Exact and variational solution:** all seven locked `g` values (`0.25` through `2.00`), layers `L=1..4`, and seeds `0,1,2` are represented. L=4 reaches absolute energy error below `6e-13` at every `g`. The strict `<1e-3` best-of-three threshold is first met at L=3 for `g=1.00, 1.50, 2.00`, and at L=4 for the other four values.
- **Processor D:** a connected six-qubit chorded ring with seven edges and native RZZ. The official checker passes for 4 and 6 qubits. On the selected N=4, L=3 HVA, the native RZZ implementation uses 9 generic two-qubit gates on D versus 18 on A/B, with no routing SWAPs. In the explicit CX representation, A/B/D use 18 gates; D's RZZ hardware basis does not reduce that CX-form count.
- **Measured bottleneck:** A and B already compile this open-chain HVA with zero SWAPs. The measured improvement is the RZZ interaction encoding: the CX-RZ-CX construction takes 12 versus 6 two-qubit gates at L=2, and 18 versus 9 at the selected L=3. The companion CX/RZZ resource rows make the comparison visible for every processor.
- **Bell experiment:** four ideal/noisy rows, 4,096 shots per basis. Noisy fidelity is `0.959839 ± 0.002184` for adjacent pair 0–1 and `0.938354 ± 0.002685` for distance-3 pair 1–4.
- **Noise research:** the required `s1_noisy.csv` results use D. A separate 36-row controlled comparison reuses the same saved logical HVA parameters across A/B/D for `g={0.5,1.0,2.0}` and `p2` multipliers `{1,1.25,1.5,2}`. D has lower noisy energy error and higher gate-noisy density-matrix fidelity than A/B at all 12 tested `g × multiplier` settings. This is a synthetic sensitivity result, not hardware evidence.
- **Additional research (not part of the official required results):** the optional N=6 sweep has 168 saved starts through L=8, the finite-size study has 180 exact sparse-spectrum rows for N=4, 6, 8, 10, and 12, and the D mitigation study has 15 rows with 400 bootstrap replicates each. These are supplementary results; the N=6 tier remains incomplete.

See [report.md](report.md) for methods, tables, figures, results, and limitations; [docs/FINAL_RUBRIC_MATRIX.md](docs/FINAL_RUBRIC_MATRIX.md) for the evidence map; and [docs/NUMBER_AUDIT.md](docs/NUMBER_AUDIT.md) for numeric provenance.

## Reproduce and verify (Windows PowerShell)

Run from the repository root. The original saved simulation package records Python 3.13.16. The final notebook and verifier were also rerun on Python 3.11.9 with the same core package versions; both environments use the package pins in `requirements-local-lock.txt`.

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-local-lock.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe tools/check_processor_d.py processors/processor_D.json 4
.\.venv\Scripts\python.exe tools/check_processor_d.py processors/processor_D.json 6
.\.venv\Scripts\python.exe verify_submission.py
.\.venv\Scripts\python.exe -m jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=-1 main.ipynb
```

The verifier checks the embedded official manifest and hashes, official schemas, all required N=4 outputs, the 168 N=6 starts and derived summaries/resources, all 180 finite-size rows and reference/crossing checks, all 15 mitigation rows and their target/error/cost consistency, the 36-row A/B/D p2 comparison, figures, the executed notebook, and Processor D at 4 and 6 qubits. It recomputes outputs from saved parameters and sparse spectra; it does not launch the optimizer sweep or Bell experiment. The notebook defaults to `RECOMPUTE=False` and displays saved results and figures.

The single command for the complete Stage B noisy/resource regeneration is `make regenerate-stage-b`. It runs `src/finish_stage_b.py`, then `src/compare_processor_p2.py` to restore both HVA encodings and Bell rows in the nine-row resources table, then runs the verifier; the command returns nonzero if the final table or any other saved output is incomplete. The optimizer and Bell experiment are separate: `src/run_s1.py` launches the 84 required starts and `src/run_bell.py` reruns Bell measurements. Leave `RECOMPUTE=False` for a saved-output review.

For convenience, activate `.venv` and run `make test`, `make verify`, `make notebook`, or `make regenerate-stage-b`. The CI workflow at `.github/workflows/ci.yml` checks dependency consistency, the test suite, and the submission verifier on Python 3.11 and 3.13.

## Additional research (not part of the official required results)

- `results/additional/p2_sensitivity.csv` and `results/figures/p2_sensitivity.png`: D-only hypothetical p2 multiplier sweep, with `p1=0.001` and `p_readout=0.01` held fixed.
- `results/additional/p2_processor_comparison.csv` and `results/figures/p2_processor_comparison.png`: same-parameter A/B/D comparison across the same multipliers, with `p1=0.001` and `p_readout=0.01` fixed. Density-matrix state fidelity includes gate noise only; readout is not folded into it.
- `results/additional/finite_size_scaling.csv`, `finite_size_crossings.csv`, `finite_size_scaling_interpretation.md`, and `results/figures/additional_finite_size_scaling.png`: exact sparse results for N=4, 6, 8, 10, 12 over 36 fields from 0.25 to 2.00. Crossings are linear interpolations of adjacent-size `N × gap` curves on the 0.05 grid; with `g_c=1` as the known infinite-chain value, the finite N≤12 data show trends near 1 but do not establish a thermodynamic critical point.
- `results/additional/mitigation_d_results.csv`, `mitigation_d_costs.csv`, and `results/figures/additional_mitigation_d.png`: readout correction and zero-noise extrapolation for D at `g={0.5,1,2}`. The synthetic study scales `p2` only, uses 400 bootstrap replicates per observable row, and compares with the noiseless expectation of the same selected HVA circuit.
- `results/additional/s1_n6_*` and `results/figures/additional_n6_layer_study.png`: 168 N=6 starts across all seven `g`, L=1..8, and seeds 0,1,2; 56 optimizer non-success flags remain preserved. The strict threshold is reached at L=8 for `g=0.25,1.25`, L=5 for `g=1.5`, and L=4 for `g=2.0`; it is not reached through L=8 for `g=0.5,0.75,1.0`. At `g=1.25`, the selected threshold result has `success=False`. Processor A capacity and B/D resource rows are in `s1_n6_resources.csv`; the optional N=6 tier is still incomplete.

## Limitations

All noise and mitigation results use a synthetic model; Processor D is not calibrated hardware. The mitigation study applies p2-only scales and shared calibration counts, not hardware noise scaling. Best-of-three is a limited optimizer budget, and all non-converged N=4/N=6 starts remain flagged in raw data. The N=6 VQE does not reach the threshold at three of seven g values and is not claimed as a completed bonus tier. Finite-size crossings are diagnostic interpolations on a discrete field grid, not a thermodynamic extrapolation.

## AI disclosure

Arena.ai Agent Mode and Codex were used to inspect the supplied challenge materials, implement reproducibility and analysis code, run simulations and validation, inspect generated outputs, and draft the report and documentation. The team should review the package and its claims before submission.
