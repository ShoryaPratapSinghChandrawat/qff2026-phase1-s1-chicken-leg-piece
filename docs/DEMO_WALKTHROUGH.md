# Three-minute judge demonstration — Phase 2 PS-S1

**Goal:** tell one evidence-led story: proposed processor → compiled circuits → exact-checked variational result → Bell check → modeled noise and limitations. Use saved outputs; do not launch a sweep during the demo.

## Before the timer

From the repository root (the directory containing `README.md`, `qff_sim.py`, and `main.ipynb`), keep `main.ipynb` on its saved outputs (`RECOMPUTE=False`). Prepare tabs for `results/figures/processor_D_topology.png`, `results/tables/resources.csv`, `results/figures/bell_comparison.png`, `results/tables/bell.csv`, `results/figures/phase_observables_vs_g.png`, `results/figures/layer_study_convergence.png`, `results/tables/s1_results.csv`, `results/figures/noisy_vs_ideal_energy.png`, `results/figures/p2_sensitivity.png`, and `results/figures/p2_processor_comparison.png`.

## Timed walkthrough

### 0:00–0:25 — Set the scientific question

**Open:** `main.ipynb` at its title and validation output.

**Say:** “This is PS-S1, the open four-spin transverse-field Ising chain. We compare an HVA/VQE ground-state estimate with the locked exact references over seven field strengths. The notebook is already executed; the saved-results mode is intentional, so this demonstration does not spend time recomputing.”

**Point to:** the 7/7 exact-reference metadata check and the processor checker output for 4 and 6 logical qubits.

**Why it matters:** it establishes the reference and execution gates before discussing a variational result.

### 0:25–0:55 — Show the processor proposal

**Open:** `results/figures/processor_D_topology.png`, then `processors/processor_D.json`; optionally show the three Pareto rows in `results/tables/d_candidates.csv`.

**Say:** “Processor D is a six-node, seven-edge chorded ring with RZZ native ZZ interactions. Three RZZ topologies tie on the measured Pareto dimensions. The recorded final key sorts the topology name lexically after the metric and basis fields, so `chorded_ring` is selected reproducibly—not because the graph was measured to be uniquely superior.”

**Point to:** the chord edge `(0,3)`, the seven-edge list, and the tie rows.

**Why it matters:** the design is a transparent benchmark proposal, not a claim about calibrated hardware.

### 0:55–1:15 — Connect topology to compiled resources

**Open:** `results/tables/resources.csv`; compare the HVA row for A/B/D, then the Bell auto-layout rows.

**Say:** “A and B already need zero routing SWAPs for this open-chain HVA. For the selected N=4,L=3,g=1.0 parameters, the CX form uses 18 generic two-qubit gates on A/B/D; the native RZZ form uses 18/18/9. The measured bottleneck is the interaction decomposition, not connectivity. Both encodings and the Bell circuit have separate resource labels.”

**Why it matters:** it ties graph/gate choice to observed circuit cost without implying noisy A/B results.

### 1:15–1:40 — Verify entanglement on short and long links

**Open:** `results/figures/bell_comparison.png`, then `results/tables/bell.csv`.

**Say:** “The directly connected pair 0–1 is distance 1; the farthest pair 1–4 is distance 3. Each of XX, YY, and ZZ used 4,096 shots per basis. The noisy Bell fidelity falls from 0.959839 ± 0.002184 on the adjacent pair to 0.938354 ± 0.002685 on the far pair, which compiles to seven rather than one two-qubit gate.”

**Point to:** the four rows and all three correlations; fidelity uses `(1+XX−YY+ZZ)/4`.

**Why it matters:** this is the common, shot-based check of the proposed connectivity under the supplied synthetic channel.

### 1:40–2:15 — Show the phase response and convergence

**Open:** `results/figures/phase_observables_vs_g.png` and `results/figures/layer_study_convergence.png`; use `results/tables/s1_results.csv` for exact rows if asked.

**Say:** “Across the seven fields, `mx` increases while nearest-neighbour `Czz_nn` and `mz2` decrease. At L=4 the maximum absolute energy error is 5.88×10⁻¹³. The strict 10⁻³ best-of-three threshold is reached at L=3 for g=1.0, 1.5, and 2.0, and at L=4 for 0.25, 0.5, 0.75, and 1.25.”

**Point to:** exact and VQE curves; the L=3 point at g=1.25 just misses the threshold (error 0.001207).

**Why it matters:** exact agreement is measurable, while the layer chart shows where the ansatz/optimizer budget is and is not sufficient.

### 2:15–2:45 — Separate ideal accuracy from modeled noise

**Open:** `results/figures/noisy_vs_ideal_energy.png` and `results/figures/p2_sensitivity.png`; optionally show `results/tables/s1_noisy.csv`.

**Say:** “The three converged D circuits were re-evaluated as noisy density matrices from saved parameters. Their fidelities are 0.892449, 0.923128, and 0.919267 at g=0.5, 1.0, and 2.0. The supplemental p2-only sweep doubles the model’s two-qubit depolarizing rate from 0.005 to 0.01 and lowers fidelity; at alpha=1 it matches the official baseline.”

**Why it matters:** the result quantifies sensitivity to the assumed channel. It is not device calibration, measured crosstalk, or a readout-noise test.

### 2:45–3:00 — Close with limits and handoff

**Say:** “The VQE is N=4 with three required seeds, and two starts reached the iteration limit; both remain in the raw table. A supplemental same-parameter A/B/D p2 comparison shows D ahead on the tested synthetic grid, not on calibrated hardware. N=6 gap/entropy is finite-size research, while the optional N=6 VQE tier is incomplete. No thermodynamic critical-point claim is made.”

**Point to:** `results/raw/s1_seed_runs.csv`, `docs/STATUS.md`, and `docs/JUDGE_QA.md` if challenged.

## Timing fallback

If the demo runs short, skip the notebook scroll but retain the exact-check sentence. If it runs long, keep the Processor D tie disclosure, the far-pair Bell result, the L=4 energy bound, and the synthetic-noise limitation; do not omit optimizer failures or imply hardware evidence.
