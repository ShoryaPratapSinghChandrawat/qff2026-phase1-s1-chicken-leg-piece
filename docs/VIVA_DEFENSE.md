# Viva defense sheet — QFF 2026 Phase 2 PS-S1

Answers below distinguish measured simulation evidence from assumptions and unrun comparisons. Source paths are relative to the project root.

1. **Why do you say L=4 is needed on the ordered side?**
   The official threshold is strict `|energy error| < 1e-3`, applied to the best of required seeds at each tested layer. The recorded minima are L=4 at g=0.25, 0.50, 0.75 and 1.25, versus L=3 at g=1.00, 1.50 and 2.00 (`results/tables/layer_study.csv`). The pattern is not strictly monotonic; g=1.25 misses by a small amount at L=3. We describe greater depth at several low-field points as an empirical result consistent with stronger Z correlations/near-degeneracy, not a universal law.

2. **Why report F2 in addition to ground-state fidelity F?**
   In the ordered finite chain E0 and E1 can be close; a variational state can have appreciable weight in their two-dimensional low-energy subspace even if a single eigenvector overlap looks less favorable. `fidelity_2` is retained in every aggregate row; it is not substituted for F. See `results/tables/s1_results.csv` and exact gaps in `results/additional/criticality.csv`.

3. **What does `mz` say, and did you force it to zero?**
   No. `mz` was calculated from the selected state. For the L=4 best states it is exactly zero or within floating-point roundoff across the grid (`s1_results.csv`, column `mz`). This is consistent with a symmetry-preserving finite-size state; `mz2` remains nonzero and measures squared longitudinal magnetization. The implementation does not hard-code `mz=0`.

4. **Which observable best shows the crossover?**
   `mx` rises from about 0.204 at g=0.25 to 0.952 at g=2.0; nearest-neighbour `Czz_nn` falls from about 0.965 to 0.252, and `mz2` from about 0.967 to 0.372. `mx` most directly tracks the growing transverse-field polarization, while the other two show the loss of longitudinal order. The curves are smooth at N=4; we do not claim a thermodynamic singularity.

5. **How were aggregate results chosen?**
   For each `(N=4,g,L)`, we chose the lowest final energy among seeds 0, 1 and 2, then copied all reported state properties, fidelities and call counts from that same run. We did not separately cherry-pick an observable or optimizer status. All 84 starts remain in `results/raw/s1_seed_runs.csv`.

6. **Were all optimizers successful?**
   No. Two L-BFGS-B starts ended at the iteration limit: g=1.5,L=4,seed=2 (energy error 1.6149e-5) and g=2.0,L=4,seed=0 (9.0195e-4). Both have `success=False` and their original termination messages remain in raw output. Other seeds furnish the selected minima; we have not changed failure flags.

7. **Why this Processor D topology if the Pareto candidates tied?**
   The screen retained ring/RZZ, 2×3-grid/RZZ, and chorded-ring/RZZ with equal recorded HVA and Bell metrics. A deterministic tie-break selected the chorded ring. It has six qubits, seven edges and diameter three; the added chord supplies connectivity while keeping the graph compact. We do not claim a unique performance optimum (`results/tables/d_candidates.csv`, `processors/processor_D.json`).

8. **Does the RZZ gate count prove RZZ is physically better than CX?**
   No. The official metric key `cx` counts the generic two-qubit gate family. Under the supplied synthetic noise model the p2 value is the same for CX, CZ and RZZ. D compiles to fewer two-qubit gate locations for this HVA, but no calibrated device data establishes real RZZ/CX error equivalence or advantage.

9. **Why are there no routing SWAPs in the reported S1 HVA?**
   Its entanglers follow the open-chain nearest-neighbour pattern, which is available on A, B and D; the selected D graph contains the needed edges. Thus the measured HVA compilation reports zero routing SWAPs. The far-pair Bell circuit is different: the distance-3 pair uses seven two-qubit gates, so S1 HVA counts should not be confused with that diagnostic (`resources.csv`, `bell.csv`).

10. **Why is the far-pair Bell fidelity lower?**
    The pair 1–4 is three graph hops apart and requires seven compiled two-qubit gates versus one on direct pair 0–1. More noisy operations accumulate. Simulated fidelity is 0.938354±0.002685 versus 0.959839±0.002184 for the adjacent pair. The ideal values are one. All figures are under the official synthetic channel and shot protocol, not hardware measurements (`results/tables/bell.csv`).

11. **Were A and B also run under noise for PS-S1?**
    The official required `s1_noisy.csv` rows are on D. A separate controlled A/B/D comparison now reuses the same logical parameters at three g values and four p2 multipliers; D has lower energy error and higher gate-noisy fidelity at all 12 tested grid points. This is supplemental synthetic evidence, not a hardware comparison. See `results/additional/p2_processor_comparison.csv`.

12. **What does the p2 sensitivity mean?**
    Two tables serve distinct purposes. `p2_sensitivity.csv` varies p2 on D only and its alpha=1 row matches the official D baseline. `p2_processor_comparison.csv` holds selected logical parameters fixed across A/B/D at g=0.5, 1.0, and 2.0 while testing alpha={1,1.25,1.5,2}; D has lower energy error and higher gate-noisy fidelity across all 12 g×alpha points. p1=.001 and configured readout=.01 are held fixed, but readout is not folded into density-matrix fidelity without measurement. This is a synthetic sensitivity analysis, not crosstalk measurement or hardware calibration.

13. **What do the N=4/N=6 gap and entropy curves prove about criticality?**
    The additional study has 180 sparse-spectrum rows for N=4,6,8,10,12 over 36 fields. It reports `E1−E0`, `N × gap`, half-chain entropy, and `<Mz²>/N²`; 14 N=4/N=6 points are checked against official references. Adjacent-size scaled-gap crossings are interpolated between the 0.05-spaced g samples and approach the known infinite-chain `g_c=1` as N increases. These finite-size data do not establish a thermodynamic limit or exponent (`results/additional/finite_size_scaling.csv`, `finite_size_crossings.csv`).

14. **Did you run the optional N=6 variational tier or PS-S2/PS-S3?**
    No complete bonus tier is claimed. The N=6 supplemental run validates seven exact E0/E1 references and retains 168 starts for L=1..8, including 56 optimizer non-success flags. Four of seven g values meet the strict threshold; g=.5,.75,1.0 do not by L=8. At g=1.25, the selected threshold result has an unsuccessful optimizer flag. Processor A capacity and B/D resource records are included, but no N=6 noisy-D study is included. The separate N=4 D mitigation study is synthetic, with readout correction and p2-only ZNE. PS-S2/PS-S3 are outside this PS-S1 package.

15. **What is the competition deadline and was the repository submitted?**
    The official kit gives relative times: Day 1 6:00 PM to Day 2 6:00 PM IST, with the final commit/repository URL due Day 2 5:40 PM IST. The event date/start time is not present in the available kit or captured clock log, so remaining time cannot be calculated. No remote URL, portal access or submission confirmation was available; no push or submission was attempted. Human authorization and a confirmed repository destination are required.
