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
- **Finite-size research:** exact N=4/N=6 spectral gaps and half-chain entanglement entropy are included. The optional N=6 VQE attempt is clearly marked incomplete and is not claimed as a bonus completion.

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

The verifier checks the embedded official manifest and hashes, schemas and numeric finiteness, the 84 raw optimizer starts and 28 aggregates, exact-reference agreement, Bell formulas and shot setting, noisy D rows, both CX/RZZ resource encodings, all 36 supplemental A/B/D p2-sensitivity rows, saved figures, the executed notebook, and Processor D at 4 and 6 qubits. It recomputes validation quantities from the saved parameters; it does not launch the 84-start optimizer sweep or Bell experiment. The notebook defaults to `RECOMPUTE=False` and displays saved results and figures, including the 300-DPI p2 comparison.

The commands that regenerate results are intentionally separate: `src/run_s1.py` launches all 84 optimizer starts; `src/run_bell.py` reruns Bell measurements; `src/finish_stage_b.py` regenerates required noise/resources; and scripts in `src/` regenerate supplemental results. Leave `RECOMPUTE=False` for a saved-output review.

## Research extensions

- `results/additional/p2_sensitivity.csv` and `results/figures/p2_sensitivity.png`: D-only hypothetical p2 multiplier sweep, with `p1=0.001` and `p_readout=0.01` held fixed.
- `results/additional/p2_processor_comparison.csv` and `results/figures/p2_processor_comparison.png`: same-parameter A/B/D comparison across the same multipliers, with `p1=0.001` and `p_readout=0.01` fixed. Density-matrix state fidelity includes gate noise only; readout is not folded into it.
- `results/additional/criticality.csv` and `results/figures/criticality_gap_entropy.png`: exact finite-size gap and half-chain entropy for N=4 and N=6. These data do not establish a thermodynamic critical point.
- `results/additional/s1_n6_*`: partial N=6 VQE work, 84 starts over L=1..4. Only `g=2.0` meets the strict layer threshold by L=4; the optional tier is incomplete.

## Limitations

The noise model is synthetic and assigns the same `p2=0.005` to CX, CZ, and RZZ at baseline. Thus fewer RZZ gate locations reduce exposure under this model, but the data do not show that a physical RZZ gate is intrinsically less error-prone than CX. The 36-row comparison covers three representative field values and four multipliers, not all operating conditions. Processor D is not calibrated hardware. Required noisy density-matrix results in `results/tables/s1_noisy.csv` are on D; the extra A/B/D comparison is supplemental. Best-of-three is a limited optimizer budget, and all non-converged starts remain flagged in the raw table. N=6 VQE is partial and receives no bonus claim.

## AI disclosure

Arena.ai Agent Mode and Codex were used to inspect the supplied challenge materials, implement reproducibility and analysis code, run simulations and validation, inspect generated outputs, and draft the report and documentation. The team should review the package and its claims before submission.
