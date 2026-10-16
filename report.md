# PS-S1 simulation report

## Pooled A/B comparison (first result)

| g | architecture | n | converged | failed | mean sampled E | mean abs total error | mean relative abs error | mean shot SEM |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.5 | Processor A_branch | 3 | 3 | 0 | -3.10018 | 0.326855 | 0.0953755 | 0.0268557 |
| 0.5 | Processor B_ref12 | 3 | 3 | 0 | -3.12207 | 0.304964 | 0.0889877 | 0.026705 |
| 1 | Processor A_branch | 3 | 3 | 0 | -4.36019 | 0.398582 | 0.0837573 | 0.037403 |
| 1 | Processor B_ref12 | 3 | 3 | 0 | -4.40511 | 0.35366 | 0.0743175 | 0.0370011 |
| 1.5 | Processor A_branch | 3 | 2 | 1 | -6.0472 | 0.456691 | 0.0702181 | 0.0416518 |
| 1.5 | Processor B_ref12 | 3 | 2 | 1 | -6.00871 | 0.495184 | 0.0761366 | 0.0419727 |

All measurements are local simulations under the stated synthetic channel model. The pooled means average three VQE initializations per field and architecture; the nine matched pairs are the independent comparison units for the descriptive paired statistic. Shot SEM is not a confidence interval.

### Paired sampled-energy difference

A minus B over the nine matched `(g, initialization seed)` pairs: **mean 0.0094401; sample SD 0.0534977; SEM 0.0178326; n=9**. No CI is claimed.

### Sampled error decomposition

The sampled energy is the sum of its separately measured ZZ and X contributions. These are mean signed contributions to noisy-minus-exact error over the three fields and three starts per architecture; component errors can have opposite signs.

| architecture | mean ZZ contribution | mean X contribution | mean total signed error |
| --- | --- | --- | --- |
| Processor A_branch | 0.149143 | 0.2449 | 0.394043 |
| Processor B_ref12 | 0.151747 | 0.232856 | 0.384602 |

The decomposition closes to floating-point precision on a per-run basis (check `noisy_error_decomposition.csv`). `shot_sem_total` combines independent Pauli-group SEMs in quadrature.

## Supplementary E4 ansatz-pattern study

The experiment followed the frozen `docs/EXPERIMENT_PLAN.md`: 27 pattern/field/start combinations, 18 new ring/star optimizations, and identical logical parameters mapped to both A/B graphs. The primary maps/settings were not changed. This table reports generated means over starts; it is separate from the canonical Stage 1 comparison.

| pattern | architecture | runs | optimizer successes | optimizer failures | mean CX | mean depth | mean routing SWAPs | mean noisy abs error | mean shot SEM |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| path | Processor A_branch | 9 | 8 | 1 | 9 | 23 | 0 | 0.36933 | 0.0351789 |
| path | Processor B_ref12 | 9 | 8 | 1 | 9 | 23 | 0 | 0.381917 | 0.0352807 |
| ring | Processor A_branch | 9 | 9 | 0 | 27 | 55 | 5 | 0.813639 | 0.0405854 |
| ring | Processor B_ref12 | 9 | 9 | 0 | 12 | 28 | 0 | 0.528862 | 0.0377325 |
| star | Processor A_branch | 9 | 9 | 0 | 9 | 25 | 0 | 0.622585 | 0.0338163 |
| star | Processor B_ref12 | 9 | 9 | 0 | 9 | 25 | 0 | 0.618462 | 0.0338927 |

Pooled matched A-minus-B sampled-energy differences by pattern (nine field/seed pairs):

| pattern | matched pairs | mean A−B | sample SD | SEM |
| --- | --- | --- | --- | --- |
| path | 9 | -0.0125868 | 0.0699834 | 0.0233278 |
| ring | 9 | 0.284776 | 0.122527 | 0.0408422 |
| star | 9 | 0.00412326 | 0.0326867 | 0.0108956 |

Descriptive observation: the ring mapped to mean CX 27 / 12 and mean routing SWAPs 5 / 0 on A/B; its pooled paired noisy A−B mean was 0.284776 J (sample SD 0.122527, SEM 0.0408422). For star, mean CX was 9 / 9 and mean noisy absolute error was 0.622585 / 0.618462 J. These are finite local-simulation summaries, not hardware or causal performance claims.

See `results/supplementary/tables/E4_ansatz_patterns.csv` for each run and `E4_paired_differences.csv` for field-specific pairs. Shot SEM is per run; the paired SEM is across matched initialization/field pairs.

## Exact references

| g | exact E₀ | max spectrum diff | Σ⟨Xᵢ⟩ |
| --- | --- | --- | --- |
| 0.5 | -3.42703 | 3.10862e-15 | 1.84051 |
| 1 | -4.75877 | 5.32907e-15 | 3.24038 |
| 1.5 | -6.50389 | 3.55271e-15 | 3.66011 |

The maximum spectral discrepancies in the table are checked directly from generated spectra; the full eigenvalue spectra and exact observables are retained in the cross-check artifacts. The source-confirmed model is an open chain; the undefined magnetization axis/normalization remains explicitly disclosed.

## Canonical VQE and separate restart

All nine starts, including the seed-42 `g=1.5` iteration-limit failure, are visible in the README table and `ideal_architecture_results.csv`. The restart diagnostic is stored separately and is not substituted for that canonical run. The exact reference is used only for post-optimization classification and error measurement, not as the VQE objective.

## Architecture, routing and noise

The two fixed graphs are the guide's A/B references, with five and nine physical nodes. Compilation uses basis `{rz,sx,x,cx}`, level one, Sabre layout/routing and transpiler seed 42. The generated tables record actual pass traces, initial/final layouts, routing SWAP evidence, final-circuit SWAP count, CX count, depth, and semantic preservation. No hardware calibration is implied. The noise model uses per-gate depolarizing channels and symmetric readout flips as recorded in the processor JSON and per-run results; Z/X observables use independent simulator seeds and 4096 shots each.

## Provenance and limitations

The October 14, 2026 guide is the governing specification. The input Hamiltonian data file records the exact guide page for the model. The magnetization wording is genuinely underspecified; the Hamiltonian and boundary condition are not. The supplied source ZIP and `Problem_Statment_Details.pdf` were absent from the workspace, so ZIP extraction/hash verification is unavailable. No hardware, portal, organizer contact, submission, publication or push is claimed. The separate AI policy was not supplied, and no project license was added without all-member approval.
