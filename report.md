# QFF 2026 Phase 2 — PS-S1 Technical Report

**Team:** Swarup, Biswajit, Arhaan Sethi, Shorya Pratap Singh Chandrawat<br>
**Team name:** Chicken Leg Piece<br>
**Phase 1 repository:** [qff2026-phase1-s1-chicken-leg-piece](https://github.com/ShoryaPratapSinghChandrawat/qff2026-phase1-s1-chicken-leg-piece)<br>
**Problem:** PS-S1, open-chain transverse-field Ising ground state

## 1. Summary

We solve the seven required N=4 transverse-field Ising instances using the supplied Hamiltonians and official HVA ansatz. All `g × layer × seed` combinations are retained: 7 field values, four layers, and seeds 0, 1, and 2, for 84 raw optimizer records and 28 best-of-three aggregates. The exact E0 and E1 references agree with the supplied metadata within `1e-9`. At L=4, the largest absolute variational energy error is `5.88e-13`; the strict `|energy error| < 1e-3` criterion is already reached at L=3 for `g=1.00, 1.50, 2.00`, while the other four values first meet it at L=4.

The common Bell experiment gives ideal fidelity 1 for both tested pairs. Under the supplied synthetic channel and 4,096 shots per measurement basis, the adjacent pair has fidelity `0.959839 ± 0.002184`, while the distance-3 pair has `0.938354 ± 0.002685`.

Processor D is a connected six-qubit, seven-edge chorded ring with native RZZ. The design targets a measured two-qubit gate-count bottleneck, not routing: the open-chain HVA already uses zero routing SWAPs on A and B. For the selected N=4, L=3 circuit, both A and B use 18 generic two-qubit gates in either representation; D uses 18 when expressed in CX form and 9 when expressed in its native RZZ form. The official model assigns the same baseline p2 to all three gate families. The added controlled comparison therefore evaluates the practical effect of the shorter native RZZ circuit under the declared synthetic model, without attributing better per-gate physical fidelity to RZZ.

Two separate research extensions are included: a same-parameter A/B/D two-qubit-error sensitivity grid, and exact N=4/N=6 finite-size spectral-gap and entanglement-entropy diagnostics. The optional N=6 VQE work is incomplete; it is not presented as a completed bonus tier.

## 2. Problem and method

The supplied instances define the open-chain Hamiltonian

`H = -J Σ(i=0..N-2) Z_i Z_(i+1) - g Σ(i=0..N-1) X_i`, with `J=1`.

We load the Pauli strings and locked exact energies from each supplied JSON instance, preserving the official qubit-label ordering and open boundary condition. The required calculation uses N=4 at `g={0.25, 0.50, 0.75, 1.00, 1.25, 1.50, 2.00}`. For each value, the official exact diagonalization routine is compared with both supplied E0 and E1 at absolute tolerance `1e-9`.

The official HVA starts from `|+>^N` and applies trainable nearest-neighbour ZZ interactions and single-qubit RX rotations in each layer. The locked seeds are 0, 1, and 2. For each `(g,L)`, the aggregate chooses the lowest final energy among those three starts; every reported field is drawn from that same selected raw row. The complete raw table retains all parameters, termination messages, success flags, optimizer calls, energies, overlaps, observables, and runtimes. Two optimizer starts reached their iteration limits and remain marked unsuccessful; they were not relabelled based on energy.

The report distinguishes exact VQE accuracy, finite-size diagnostics, resource counts, and synthetic noisy simulation. None of these is a hardware measurement.

## 3. Processor D design and measured bottleneck

The selected processor has six nodes, seven edges, graph diameter 3, and native basis `[rz, sx, x, rzz]`. It passes the unchanged official `check_processor_d.py` for both 4 and 6 required qubits. The topology scan retained three Pareto-equivalent RZZ candidates; `chorded_ring` is selected by the recorded deterministic lexical tie-break, not by a unique fidelity or connectivity advantage.

**The bottleneck measured in this instance is the ZZ interaction implementation.** A and B both compile the open-chain HVA with zero routing SWAPs. At N=4, L=2, the CX-RZ-CX construction uses 12 two-qubit gates on A/B, while the RZZ representation uses 6 on D. For the selected N=4, L=3, g=1.00, seed-2 circuit, the resource table reports:

| Processor | HVA encoding | Generic 2Q gates | Depth | 2Q depth | Routing SWAPs |
|---|---|---:|---:|---:|---:|
| A | CX | 18 | 36 | 12 | 0 |
| A | RZZ | 18 | 36 | 12 | 0 |
| B | CX | 18 | 36 | 12 | 0 |
| B | RZZ | 18 | 36 | 12 | 0 |
| D | CX | 18 | 58 | 12 | 0 |
| D | RZZ | 9 | 24 | 6 | 0 |

The RZZ implementation halves the counted two-qubit gates and two-qubit depth for this selected circuit. D's CX-form depth is longer because its native basis does not provide the same direct interaction representation; the useful D comparison is its native RZZ row. Both encodings are shown so the resource claim is auditable and the comparison does not conflate a logical circuit representation with a processor basis.

The baseline error rates are `p1=0.001`, `p2=0.005`, and `p_readout=0.01`, matching the official minimum allowed rates. These are synthetic benchmark assumptions. In particular, the official model gives RZZ the same p2 as CX/CZ. The topology therefore reduces the number of modeled two-qubit error locations when the ansatz is compiled natively as RZZ; the model does not support a claim that an individual RZZ gate is physically better than CX. No calibration, crosstalk, drift, leakage, or hardware-specific gate variation is represented.

## 4. Bell experiment

The common Bell benchmark compares an adjacent physical pair (0–1, graph distance 1) and a distance-3 pair (1–4). The distance-3 implementation uses seven two-qubit gates versus one for the adjacent pair. The runner uses the official 4,096 shots for each of XX, YY, and ZZ; the resource and Bell tables retain the required schema.

| Pair | Graph distance | 2Q gates | Ideal fidelity | Noisy fidelity ± standard error |
|---|---:|---:|---:|---:|
| 0–1 | 1 | 1 | 1.000000 | 0.959839 ± 0.002184 |
| 1–4 | 3 | 7 | 1.000000 | 0.938354 ± 0.002685 |

The lower fidelity of the longer path is consistent with greater exposure to the synthetic two-qubit channel. It is a shot-based simulation under the official model, not a device test. Fidelity is calculated as `(1 + XX − YY + ZZ)/4`; the reported standard error is the root-sum-square of the three expectation standard errors divided by four.

![Bell comparison](results/figures/bell_comparison.png)

## 5. Exact and variational results

The exact-reference table covers all seven locked N=4 field values; all E0 and E1 metadata discrepancies are below `1e-9`. The L=4 best-of-three energy errors range from approximately `6.7e-15` to `5.9e-13`, with fidelities numerically equal to one at displayed precision. Minimum tested layer counts under the strict threshold are:

| g | Minimum L with `|ΔE| < 1e-3` | L=4 absolute energy error |
|---:|---:|---:|
| 0.25 | 4 | 6.66e-15 |
| 0.50 | 4 | 3.02e-13 |
| 0.75 | 4 | 2.50e-13 |
| 1.00 | 3 | 2.28e-13 |
| 1.25 | 4 | 2.10e-13 |
| 1.50 | 3 | 1.82e-13 |
| 2.00 | 3 | 5.88e-13 |

The best-of-three threshold pattern is empirical for this initialization and optimizer budget, not a universal depth law. At L=3, g=1.25 narrowly misses the threshold (`0.001207`), while g=1.00, 1.50, and 2.00 meet it. All 84 raw starts, including two iteration-limit stops, remain available for inspection.

Across the L=4 selected states, transverse magnetization `mx` rises from 0.204 at g=0.25 to 0.952 at g=2.00. Nearest-neighbour `Czz_nn` falls from 0.965 to 0.252, and `mz2` falls from 0.967 to 0.372. The finite-size `mz` one-point expectation remains approximately zero in these symmetric finite-chain states; this does not imply that Z correlations vanish. The smooth changes are finite-size diagnostics, not a thermodynamic phase-transition estimate.

![N=4 observables](results/figures/phase_observables_vs_g.png)

## 6. Noisy S1 simulation and controlled p2 sensitivity

### Required D noisy results

The required noisy table evaluates the selected converged-layer D circuits at g=0.5 (L=4, seed 0), g=1.0 (L=3, seed 2), and g=2.0 (L=3, seed 2), using the official synthetic noise model. It reports energy and observables, and density-matrix state fidelity. **The `fidelity_noisy_dm` values model gate noise only; no readout noise or readout sampling is folded into density-matrix state fidelity.** Readout flip probability is used by measured shot experiments such as the Bell test. The density matrix contains no measurement stage, so readout does not act on it.

| g | L | Noisy energy | Energy error vs exact E0 | Gate-noisy density-matrix fidelity |
|---:|---:|---:|---:|---:|
| 0.50 | 4 | −3.127356 | 0.299678 | 0.892449 |
| 1.00 | 3 | −4.493048 | 0.265723 | 0.923128 |
| 2.00 | 3 | −7.841450 | 0.535349 | 0.919267 |

### Same-parameter A/B/D comparison

The supplemental comparison fixes the selected logical HVA parameters for each of g=0.5, 1.0, and 2.0, uses the RZZ logical representation, and applies the same official transpile/layout and density-matrix method on A, B, and D. It tests `alpha={1, 1.25, 1.5, 2}` with `p2=0.005 × alpha`, while holding `p1=0.001` and the configured `p_readout=0.01` fixed. There are 36 rows in `results/additional/p2_processor_comparison.csv`; alpha=1 for D reproduces the official D noisy S1 energy and fidelity. At all 12 tested `g × alpha` points, D has lower energy error and higher fidelity than A and B. There is no crossing in this finite tested grid. A and B are identical under the supplied open-chain connectivity and equal rates.

| g | α | A/B energy error | D energy error | A/B fidelity | D fidelity |
|---:|---:|---:|---:|---:|---:|
| 0.5 | 1.00 | 0.458867 | 0.299678 | 0.841744 | 0.892449 |
| 0.5 | 2.00 | 0.713099 | 0.437022 | 0.760515 | 0.847926 |
| 1.0 | 1.00 | 0.417150 | 0.265723 | 0.885660 | 0.923128 |
| 1.0 | 2.00 | 0.663242 | 0.395330 | 0.823741 | 0.890038 |
| 2.0 | 1.00 | 0.828235 | 0.535349 | 0.880369 | 0.919267 |
| 2.0 | 2.00 | 1.305433 | 0.787981 | 0.816361 | 0.884997 |

At alpha=1, the result reflects the modeled reduction in two-qubit gate locations under D's native RZZ compilation, along with the official synthetic channel and compiler choices. The alpha sweep shows that this advantage persists over the tested p2 range. It cannot establish performance on calibrated hardware or under gate-family-specific physical errors. Readout is held at its official value but is not included in the density-matrix state fidelity, as described above.

![Controlled A/B/D p2 sensitivity](results/figures/p2_processor_comparison.png)

## 7. Finite-size research and N=6 boundary

The exact finite-size extension reports the spectral gap `E1−E0` and half-chain von Neumann entropy for N=4 and N=6. At g=0.25, the gaps are approximately 0.007325 (N=4) and 0.000458 (N=6), and the entropies are 0.9893 and 0.9996 bits. At g=1.0, the gaps are 0.694593 and 0.482147, with entropies 0.4110 and 0.4732 bits. These results indicate a small finite-size gap on the ordered side and a smooth change across the sampled fields; two system sizes do not support a thermodynamic extrapolation or critical-point estimate.

A separate N=6 VQE attempt saved 84 starts for L=1..4 and validated exact references. Only g=2.0 reaches the strict layer threshold by L=4; the other six values do not. The N=6 tier remains incomplete and is not claimed as bonus credit. It is separated from all official N=4 tables.

![Finite-size gap and entanglement](results/figures/criticality_gap_entropy.png)

## 8. Reproducibility, integrity, and limitations

The official `qff_sim.py` and starter copy are byte-identical to the supplied official hash; the embedded official manifest has 25 entries. Processor D passes the unchanged checker at 4 and 6 qubits. The notebook is saved executed with `RECOMPUTE=False`, displaying the saved result tables and figures. `verify_submission.py` independently checks source hashes, official schemas, raw-grid coverage, aggregates and references, Bell equations and the 4,096-shot runner setting, noisy D rows, both CX/RZZ resource rows, all 36 supplemental A/B/D comparison rows, the notebook, figures, documentation, and D checker results.

The official required noisy S1 table covers D; the A/B/D noisy comparison is supplemental and limited to three selected field values. All noisy results use simplified synthetic assumptions, not calibrated noise. Equal p2 across CX/CZ/RZZ is a modeling choice, not a physical finding. The optional N=6 variational tier is incomplete. Best-of-three may miss a better optimizer basin. The exact gap and entropy work is finite-size only. No hardware execution or thermodynamic extrapolation is claimed.

## AI disclosure

Arena.ai Agent Mode and Codex were used to inspect the supplied challenge materials, implement and run analysis/validation code, review outputs, and draft this report and documentation. The team should review the package and its claims before submission.
