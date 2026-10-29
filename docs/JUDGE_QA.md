# Judge Q&A — PS-S1

Answers are limited to the supplied instances and generated local evidence. “Not measured” is intentional where no experiment was run.

### 1. What Hamiltonian and boundary condition did you solve, and how are the Pauli labels interpreted?

The locked PS-S1 instances specify the open-chain transverse-field Ising Hamiltonian
`H = -J Σ_i Z_i Z_{i+1} - g Σ_i X_i`, with `J=1`; for N=4 the sums contain three bonds and four transverse-field terms. The JSON metadata specifies open boundary conditions and Qiskit label ordering (qubit 0 is the right-most label character). We load each operator directly from the supplied JSON rather than reconstructing a possibly different boundary convention. Evidence: `data/s1/tfim_open_N4_g1.00.json`, `meta.model`, `meta.boundary`, `meta.J`, `meta.g`, `operator`, `meta.label_order`.

### 2. What ansatz did you use, and why is it appropriate for this model?

The official HVA begins in `|+>^N`, applies one trainable ZZ interaction layer over open-chain bonds and one trainable RX layer over qubits per layer, with two shared parameters (`gamma_l`, `beta_l`) per layer. The entangling pattern follows the open chain. Source: unchanged `starter/qff_sim.py`, `hva_ansatz`; N=4/L rows and parameter counts in `results/tables/s1_results.csv`, `n_params`. We use the D-native RZZ form for D resource/noise circuits; the ideal VQE energy search uses the official CX construction.

### 3. How reliable is the optimizer result with only three seeds?

It is a limited best-of-three search, not a guarantee of the global minimum from arbitrary starts. The locked seeds are 0, 1, and 2 at every required g and L. Two starts terminate with the optimizer’s iteration-limit flag and remain `success=False`: g=1.5/L=4/seed 2 and g=2.0/L=4/seed 0. We do not relabel them as converged based on their energies. All 84 start records, termination messages, and timings are retained in `results/raw/s1_seed_runs.csv`, `seed`, `success`, `message`, `energy_err`, `optimizer_calls`, `runtime_seconds`.

### 4. How do you know the exact reference and aggregate table are trustworthy?

For each of the seven N=4 instances, the computed lowest two eigenvalues were compared against supplied metadata at absolute tolerance 1e-9; all seven passed. For every `(g,L)`, the aggregate selects the lowest final energy among seeds 0/1/2 and copies the energy, observables, F/F2, optimizer calls, parameter count, and D gate count from that same seed. Independent audit comparison found zero mismatches across the 28 aggregates. Evidence: `results/tables/s1_exact_reference.csv`, E0/E1 metadata differences; `src/run_s1.py`, `get_reference` and aggregation; `results/raw/s1_seed_runs.csv`; `results/tables/s1_results.csv`.

### 5. Why choose chorded-ring/RZZ when ring/RZZ and grid/RZZ tie?

The three Pareto rows are equal on the measured dimensions: N=4 L=2 two-qubit count 6, depth 17, zero SWAPs, adjacent Bell mean 1, far Bell mean 7, diameter 3. The recorded sort key then ranks basis (`CX<CZ<RZZ`) and topology name in ascending lexical order. With RZZ common, `chorded_ring` precedes `grid_2x3` and `ring`. This is a deterministic naming tie-break—not evidence that the chorded ring is uniquely better. Evidence: `results/tables/d_candidates.csv`, the three `pareto=True` rows and columns named above; `src/scan_processor_d.py`, `sortkey`; selected edges in `processors/processor_D.json`.

### 6. Does the lower RZZ gate count prove better physical performance than CX?

No. A and B have zero routing SWAPs, so routing was not the measured bottleneck. The CX-RZ-CX representation uses 18 generic two-qubit gates at the selected L=3; native RZZ uses 18 on A/B and 9 on D. A controlled synthetic p2 comparison shows D ahead on the tested grid because the native circuit has fewer two-qubit locations under equal per-gate p2. The model does not establish physical RZZ/CX error equivalence. Evidence: `results/tables/resources.csv`, selected HVA rows; unchanged `starter/qff_sim.py`, `TWO_Q`/`circuit_metrics`; Processor D error rates in `processors/processor_D.json`.

### 7. What noise is included, and what is not?

The official synthetic channel uses p1=0.001, p2=0.005, and readout flip 0.01 where measurement sampling is performed. Both the required D-only S1 density-matrix rows and the supplemental A/B/D p2 comparison model gate noise only; readout is not folded into density-matrix state fidelity. Bell uses measured counts and the official shot-based protocol. The p2 sweeps hold p1/readout fixed and scale only p2, so they are sensitivity studies—not hardware calibration or measured crosstalk. Evidence: `results/tables/s1_noisy.csv`; `results/additional/p2_sensitivity.csv`, `alpha_p2`, p1/p2/p_readout; `src/run_extensions.py`; `starter/qff_sim.py`, noisy helper docstrings.

### 8. How are the Bell fidelity and uncertainty computed, and what does the far pair show?

For each basis, parity estimates the expectation and standard error from 4,096 shots. Fidelity is `F=(1+XX−YY+ZZ)/4`, and `SE(F)=sqrt(SE_XX²+SE_YY²+SE_ZZ²)/4`. The adjacent 0–1 pair has distance 1 and one two-qubit gate; farthest pair 1–4 has distance 3 and seven gates. Noisy F is 0.959839±0.002184 versus 0.938354±0.002685. All four rows reproduce the helper’s formulas exactly. Evidence: `results/tables/bell.csv`, pair/condition rows and correlation/SE columns; `src/run_bell.py` (shots); `starter/qff_sim.py`, `bell_experiment` and `parity_expectation`.

### 9. Can the finite-size results locate the thermodynamic critical point?

No. The required VQE is N=4; an exact N=6 gap/half-chain entropy calculation is supplemental and no size extrapolation was performed. The finite-size crossover is smooth. The `mz` one-point diagnostic is near zero in the selected symmetric ground states while `mx`, `Czz_nn`, and `mz2` vary; this does not mean longitudinal correlations vanish. We make no critical exponent or thermodynamic critical-point claim. Evidence: `results/tables/s1_results.csv`, observables; `results/additional/criticality.csv`, `N`, `g`, `gap`, `half_chain_entropy_bits`.

### 10. Can another person reproduce the package, and is it submitted?

The verified kit is preserved under `handoff_payload/OFFICIAL_KIT/`; its manifest checks 25/25 entries, and the official source/checker hashes are recorded in `docs/AUDIT_LOG.md`. `main.ipynb` is executed with `RECOMPUTE=False` to load saved results and display the saved plots. Run `python verify_submission.py` from the repository root for the complete saved-package audit. Evidence: `README.md`, `docs/STATUS.md`, `docs/AUDIT_LOG.md`, and the verifier output.


### 11. What does the controlled A/B/D p2 study add?

It reuses the same saved logical parameters for each of g=0.5, 1.0, and 2.0 on A/B/D, varies p2 by alpha={1,1.25,1.5,2}, and keeps p1=0.001 and configured readout=0.01 fixed. D has lower energy error and higher gate-noisy density-matrix fidelity at all 12 tested g×alpha points. Readout is not part of the density-matrix state fidelity because that calculation does not measure. This is a supplemental synthetic-model comparison, not hardware evidence. Source: `results/additional/p2_processor_comparison.csv`.

### 12. Why list both CX and RZZ resource rows?

The two encodings separate logical interaction decomposition from processor-native execution. They show that A/B already need no SWAPs for the open chain, while D's RZZ basis reduces the counted two-qubit gates from 18 to 9 for the selected L=3 circuit. D's CX-form depth is 58, so the report uses the native RZZ row for the D advantage and discloses both. Source: `results/tables/resources.csv`.
