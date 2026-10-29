# Numeric claim audit — Phase 2 PS-S1

This ledger maps numeric statements in `README.md` and `report.md` to the source-of-record row(s) and column(s). CSVs retain canonical precision; prose values are rounded. The required N=4 results remain separate from the supplemental p2 comparison, finite-size diagnostics, and incomplete N=6 VQE files.

| Claim | Evidence path | Row selector | Columns / derivation |
|---|---|---|---|
| Team members and Phase 1 continuity | `README.md`; user-provided Phase 1 URL | Four named team members | Phase 1 link: `https://github.com/ShoryaPratapSinghChandrawat/qff2026-phase1-s1-chicken-leg-piece` |
| Bell adjacent pair 0–1: distance 1, one 2Q gate, ideal/noisy correlations and fidelity ± SE | `results/tables/bell.csv` | `pair=0-1`, ideal/noisy | `pair_distance`, `two_qubit_gates`, `XX/YY/ZZ`, `_se`, `fidelity`, `fidelity_se` |
| Bell far pair 1–4: distance 3, seven 2Q gates, ideal/noisy correlations and fidelity ± SE | `results/tables/bell.csv` | `pair=1-4`, ideal/noisy | Same columns as above |
| Bell shots: 4,096 per measurement basis | `src/run_bell.py`; official settings | runner constant and locked setting | `SHOTS`; `verify_submission.py` checks `shots=4096` |
| Processor D six nodes, seven edges, chorded-ring graph, native RZZ | `processors/processor_D.json` | single JSON object | `num_qubits`, `edges`, `basis_gates`; checker passes for 4 and 6 |
| Three RZZ Pareto candidates and deterministic selected tie-break | `results/tables/d_candidates.csv`; `src/scan_processor_d.py` | all 12 variants; filter `pareto=True` | Pareto/resource columns and documented final sort key; chorded ring is lexical tie-break, not unique superiority |
| L=2 measured bottleneck: A/B 12 CX-RZ-CX 2Q gates versus D/RZZ 6; zero SWAPs | `results/tables/d_candidates.csv` | selected chorded-ring/RZZ candidate | `A_n4_hva_two_q`, B comparison, `n4_two_q`, depths and SWAPs |
| Selected N=4,L=3,g=1.00,seed=2 resources in both encodings | `results/tables/resources.csv` | labels `s1_hva_g1.00_L3_best_seed2_cx` and `_rzz`, each on A/B/D | `logical_2q`, `two_q`, `depth`, `two_q_depth`, `swaps`, `routing_overhead_2q`; generic 2Q family includes CX/CZ/RZZ |
| Bell auto-layout resource comparison | `results/tables/resources.csv` | `bell_auto_layout_ZZ`, processors A/B/D | Official resource columns; pair-specific Bell paths are in `bell.csv` |
| Exact N=4 references, seven g values, 1e-9 tolerance | `results/tables/s1_exact_reference.csv`; supplied JSON | all seven g rows | E0/E1 metadata differences |
| L=4 VQE energies/errors/fidelity/observables | `results/tables/s1_results.csv` | N=4, L=4, each g | `best_energy`, `energy_err`, `fidelity`, `mx`, `czz_nn`, `mz2` and exact columns |
| Strict minimum L at |ΔE|<1e-3 | `results/tables/layer_study.csv` | each g; scan L=1..4 | `abs_energy_err`; strict inequality |
| Raw optimizer coverage and retained failures | `results/raw/s1_seed_runs.csv` | all 84 g×L×seed rows; two iteration-limit rows | `success`, `message`, `energy_err`, calls and parameters |
| Required noisy Processor D energy, observables and gate-noisy state fidelity | `results/tables/s1_noisy.csv` | g=0.5, 1.0, 2.0 | `layers`, `energy_noisy`, `fidelity_noisy_dm`, `mx_noisy`, `czz_nn_noisy`, `mz2_noisy`; readout is not folded into DM state fidelity |
| Supplemental 36-row same-parameter A/B/D p2 comparison | `results/additional/p2_processor_comparison.csv` | 3 g × 3 processors × 4 alpha | `energy_error_noisy`, `fidelity_noisy_dm`, p1/p2/readout, gate counts/depth/SWAPs; D wins both metrics at all 12 g×alpha points |
| D-only p2 sensitivity and alpha=1 baseline | `results/additional/p2_sensitivity.csv` | each g×alpha | p2=`0.005×alpha`; p1=.001; readout=.01; alpha=1 checked against official D table |
| Exact N=4/N=6 gap and half-chain entropy | `results/additional/criticality.csv` | N=4/6, all g | `gap`, `half_chain_entropy_bits`, E0/E1 and metadata differences; no extrapolation |
| Partial optional N=6 VQE | `results/additional/s1_n6_*` | seven g × L=1..4 × seeds 0..2 | 84 raw starts; only g=2.0 meets threshold by L=4; not claimed as completed bonus |
| Baseline synthetic error rates | `processors/processor_D.json`; official helper | D processor settings | p1=.001, p2=.005, p_readout=.01; equal p2 across CX/CZ/RZZ is a model assumption |
| Official source integrity | `handoff_payload/OFFICIAL_KIT/MANIFEST.sha256`; `verify_submission.py` | all 25 entries | SHA-256; official `qff_sim.py` hash is `dd0305834f88164f01f9b2a17f7333eb48a966cb81951b1953eed0e218de4cfc` |
| Report copies | `report.md`; `docs/report.md` | entire files | verifier requires byte-identical contents |

Every displayed figure is sourced from the corresponding CSVs above. The executed notebook prints row coverage and renders the required and supplemental plots; it uses saved data by default.
