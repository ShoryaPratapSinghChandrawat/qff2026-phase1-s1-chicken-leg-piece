# Presentation Pitch & Viva Defense Guide

**Problem Statement:** PS-S1 (Transverse-Field Ising Model Ground State Simulation)
**Team:** Chicken Leg Piece (Swarup, Biswajit, Arhaan Sethi, Shorya Pratap Singh Chandrawat)
**Repository:** `PS-S1_public_GITHUB_UPLOAD` (Phase 2 at Root, Phase 1 in `phase1/`)

---

## 1. 5-Minute Pitch Script

### Minute 0:00 – 1:00: Hook, Context & Scope
> "Good morning, judges. We are team **Chicken Leg Piece**, presenting our completed solution for **PS-S1: Transverse-Field Ising Model Ground-State Simulation**.
>
> In quantum computing, simulating strongly correlated quantum systems is a leading path toward quantum utility. The 1D transverse-field Ising model captures the physics of quantum phase transitions between magnetic order and quantum disorder.
>
> Our approach prioritizes **rigorous scientific honesty, 100% reproducible data, and verifiable hardware-efficient transpilation**. All our reported numbers come from audited CSV datasets generated under the official QFF 2026 Phase 2 kit, evaluated with simulated depolarizing noise on Qiskit Aer. We make no unbacked claims of quantum advantage or physical hardware execution."

### Minute 1:00 – 2:00: Algorithm & Layer Convergence ($N=4$)
> "We implemented the Hamiltonian Variational Ansatz (HVA) with alternating $ZZ$ entangling layers and single-qubit $RX$ rotations, evaluated across all seven locked transverse field values ($g \in \{0.25, 0.50, 0.75, 1.00, 1.25, 1.50, 2.00\}$) and layers $L=1$ to $4$ using three fixed initialization seeds (0, 1, 2).
>
> All 84 raw starts are preserved in our repository—including two runs that hit iteration limits. At layer $L=4$, our best-of-three variational energies match exact diagonalization references down to machine precision, with energy errors below $6 \times 10^{-13}$ across all fields.
>
> The competition's strict threshold of $|E - E_0| < 10^{-3}$ is achieved at **$L=3$ for $g=1.00, 1.50, 2.00$**, and at **$L=4$ for $g=0.25, 0.50, 0.75, 1.25$**. At higher fields, the ground state aligns closer to the paramagnetic product state $|+\rangle^{\otimes 4}$, enabling faster convergence."

### Minute 2:00 – 3:00: Processor D Design & Measured Bottleneck
> "Our architectural analysis revealed a crucial insight: **routing is not the bottleneck**. Because the open-chain HVA only couples nearest neighbors, Processors A and B compile the circuits with **zero routing SWAPs**.
>
> Instead, the true physical bottleneck is the **two-qubit gate count of the $ZZ$ interaction**. On standard CX-based processors (like A and B), synthesizing an $e^{-i \theta Z_i Z_{i+1}}$ interaction requires a composite CX–RZ–CX sequence—demanding two 2Q gates per interaction.
>
> We designed **Processor D**: a 6-qubit, 7-edge chorded ring with native $RZZ$ interaction support, passing all official validation rules. Under Processor D's native $RZZ$ basis, each $ZZ$ term is executed with **a single two-qubit gate**. For the selected $N=4, L=3$ circuit at $g=1.00$:
> - Processors A and B require **18 two-qubit gates** and depth 36.
> - Processor D requires only **9 two-qubit gates** and depth 24—a **50% reduction in two-qubit operations** with zero routing overhead."

### Minute 3:00 – 4:00: Noise Modeling & Common Bell Benchmark
> "Under the official synthetic noise model ($p_1 = 0.001, p_2 = 0.005, p_{\text{readout}} = 0.01$ with 4,096 shots per basis), we evaluated both Bell pairs and noisy ground states on Processor D:
> - The **direct Bell pair (0–1)** at distance 1 achieves a noisy state fidelity of **$0.9598 \pm 0.0022$** with 1 CX gate.
> - The **farthest Bell pair (1–4)** at distance 3 achieves a noisy fidelity of **$0.9384 \pm 0.0027$** using 7 CX gates (1 entangling gate + 2 SWAPs).
>
> Furthermore, in our 36-row controlled noise comparison across $p_2$ multipliers from $1.0\times$ to $2.0\times$, Processor D's 50% gate reduction translated directly into lower noisy energy errors and higher density-matrix fidelities than Processors A and B across all 12 tested configurations."

### Minute 4:00 – 5:00: Supplemental Research & Verification
> "Beyond required deliverables, we conducted extensive supplemental research:
> 1. **Optional $N=6$ Extension:** Evaluated 204 starts; achieved $|E - E_0| < 10^{-3}$ across all seven fields (e.g. $L=4$ at $g=2.0$, $L=10$ at $g=1.0$).
> 2. **Finite-Size Scaling:** Sparse-spectrum diagonalization from $N=4$ up to $N=12$ over 36 field values, tracing energy gaps and entanglement entropy crossings.
> 3. **Error Mitigation:** Zero-Noise Extrapolation (ZNE) and readout calibration on Processor D, demonstrating up to 80% error reduction on noisy ground state energies.
>
> Our entire pipeline is validated via `python verify_submission.py` and `pytest -q` in under 15 seconds, backed by SHA-256 manifests. Thank you, and we welcome your questions."

---

## 2. Top 12 Judge Viva Questions & Data-Backed Answers

### Q1: What are the minimal layer depths required to reach $|E - E_0| < 10^{-3}$ for each field value?
**Answer:**
From `results/tables/s1_results.csv`, the minimal layer depths and corresponding energy errors are:
- $g = 0.25$: $L_{\min} = 4$ (error: $6.661 \times 10^{-15}$, fidelity: $> 0.999999$)
- $g = 0.50$: $L_{\min} = 4$ (error: $3.024 \times 10^{-13}$, fidelity: $> 0.999999$)
- $g = 0.75$: $L_{\min} = 4$ (error: $2.496 \times 10^{-13}$, fidelity: $> 0.999999$)
- $g = 1.00$: $L_{\min} = 3$ (error: $1.560 \times 10^{-4}$, fidelity: $0.999966$)
- $g = 1.25$: $L_{\min} = 4$ (error: $2.105 \times 10^{-13}$, fidelity: $> 0.999999$)
- $g = 1.50$: $L_{\min} = 3$ (error: $3.227 \times 10^{-4}$, fidelity: $0.999953$)
- $g = 2.00$: $L_{\min} = 3$ (error: $1.154 \times 10^{-4}$, fidelity: $0.999987$)

### Q2: Why is the layer count non-monotonic across the transverse field range?
**Answer:**
The layer depths are 4, 4, 4, 3, 4, 3, 3. The non-monotonicity arises from the interplay between the initial state and the Hamiltonian:
- In the ferromagnetic regime ($g < 1$), the ground state has strong $ZZ$ correlations, requiring sufficient entangling layers ($L=4$) to rotate away from the initial $|+\rangle^{\otimes 4}$ state.
- In the strong paramagnetic regime ($g \ge 1.5$), the ground state approaches the product state $|+\rangle^{\otimes 4}$, which the ansatz prepares at $L=0$. Hence, fewer layers ($L=3$) suffice.
- At $g=1.25$, the system is in an intermediate crossover region where $L=3$ narrowly misses the threshold (error $1.207 \times 10^{-3} > 1.0 \times 10^{-3}$), requiring $L=4$ ($2.105 \times 10^{-13}$).

### Q3: Why did you choose a chorded-ring topology with native RZZ for Processor D?
**Answer:**
Because the open-chain TFIM maps onto linear topologies with **0 routing SWAPs** on both Processor A (5-qubit cross) and Processor B (9-qubit grid), routing overhead was zero. The measured bottleneck was the decomposition of $ZZ$ rotations into two CX gates.
Processor D introduces native $RZZ$ gates (`["rz", "sx", "x", "rzz"]`), enabling direct one-gate execution of $ZZ(\theta)$. Its 6-qubit, 7-edge chorded-ring graph accommodates 4-qubit and 6-qubit open chains without routing while passing all official rules in `tools/check_processor_d.py`.

### Q4: What exact resource savings does Processor D achieve?
**Answer:**
From `results/tables/resources.csv`, for the selected $N=4, L=3$ circuit at $g=1.00$:
- **Processor A:** 18 two-qubit gates (CX), depth 36, 2Q-depth 12, 0 SWAPs.
- **Processor B:** 18 two-qubit gates (CX), depth 36, 2Q-depth 12, 0 SWAPs.
- **Processor D (native RZZ):** **9 two-qubit gates (RZZ)**, depth 24, 2Q-depth 6, 0 SWAPs.
This halves the two-qubit gate count and two-qubit depth. When expressed in standard CX form on D, the count remains 18, demonstrating that the saving stems specifically from native hardware basis alignment.

### Q5: What were the measured Bell state fidelities on Processor D?
**Answer:**
From `results/tables/bell.csv` (measured with 4,096 shots per Pauli basis under the official noise model):
- **Direct pair (0–1, distance 1):** 1 CX gate. $\langle XX \rangle = 0.9463$, $\langle YY \rangle = -0.9468$, $\langle ZZ \rangle = 0.9463$. Noisy state fidelity = **$0.959839 \pm 0.002184$** (Ideal: 1.0).
- **Farthest pair (1–4, distance 3):** 7 CX gates (1 Bell CX + 2 routing SWAPs). $\langle XX \rangle = 0.9253$, $\langle YY \rangle = -0.9033$, $\langle ZZ \rangle = 0.9248$. Noisy state fidelity = **$0.938354 \pm 0.002685$** (Ideal: 1.0).

### Q6: Did your team run these circuits on physical quantum hardware?
**Answer:**
**No.** All calculations were executed locally using Qiskit Aer with the official competition noise model ($p_1 = 0.001, p_2 = 0.005, p_{\text{readout}} = 0.01$). The error bars represent shot-noise standard errors ($\sigma / \sqrt{N_{\text{shots}}}$), not device drift or physical calibration errors. We make zero hardware claims.

### Q7: Why are there 2 failed optimizer starts in the N=4 dataset?
**Answer:**
In `results/raw/s1_seed_runs.csv`, 82 starts converged successfully, while 2 starts reached the maximum iteration limit (`success=False`). In accordance with strict hackathon integrity guidelines, we **never delete, hide, or restart** non-converged runs. Both failed runs retain their exact optimizer termination messages and are included in our submission verifier.

### Q8: What does the multi-seed stability analysis reveal?
**Answer:**
From `docs/SEED_STABILITY.md`, testing three independent seeds (0, 1, 2) revealed that near the critical point ($g=1.00, L=3$), only Seed 2 converged below the $10^{-3}$ threshold ($1.560 \times 10^{-4}$), while Seeds 0 and 1 stalled at $\approx 2 \times 10^{-2}$. In contrast, in the paramagnetic regime ($g=1.25, L=4$), all three seeds reached $< 10^{-11}$. This demonstrates why multi-start optimization is required to avoid local minima in parameterized quantum circuits.

### Q9: How does Processor D perform under higher noise levels compared to A and B?
**Answer:**
In our 36-row controlled study (`results/additional/p2_processor_comparison.csv`), we tested $p_2$ multipliers of $1\times, 1.25\times, 1.5\times,$ and $2\times$ holding circuit parameters identical. Across all 12 tested configurations, Processor D consistently yielded lower noisy energy error and higher density-matrix fidelity than Processors A and B (e.g., at $g=1.0, 2\times p_2$, D energy error is $0.518$ vs $0.938$ on A/B). This is because D exposes the state to only 9 two-qubit noise channels instead of 18.

### Q10: What did you achieve in the optional N=6 bonus tier?
**Answer:**
In `results/additional/s1_n6_results.csv`, we completed 204 starts across $L=1..8$ (and $L=1..12$ for critical fields $g=0.5, 0.75, 1.0$). All seven fields reached the $|E - E_0| < 10^{-3}$ threshold:
$g=2.0 (L=4), g=1.5 (L=5), g=0.25 (L=8), g=1.25 (L=8), g=0.50 (L=9), g=0.75 (L=9), g=1.00 (L=10)$.
For $g=0.5, 0.75, 1.0, 1.25$, the minimal threshold row carries `success=False` (due to iteration limits), with confirmed convergence at higher depths.

### Q11: What error mitigation methods were evaluated, and what were the quantitative gains?
**Answer:**
In `results/additional/mitigation_d_results.csv`, we implemented readout error calibration and Zero-Noise Extrapolation (ZNE) via digital two-qubit error scaling ($\alpha \in \{1.0, 1.5, 2.0\}$) with Richardson extrapolation:
- At $g=0.50$: Raw energy error $0.300 \to$ Mitigated error **$0.061$** (80% error reduction).
- At $g=1.00$: Raw energy error $0.266 \to$ Mitigated error **$0.053$** (80% error reduction).
- At $g=2.00$: Raw energy error $0.535 \to$ Mitigated error **$0.119$** (78% error reduction).
Total experimental cost was 26 circuits and 106,496 shots.

### Q12: How can the judges independently verify every claim in your report?
**Answer:**
By running our automated validator:
```bash
python verify_submission.py
python -m pytest -q
```
In 15 seconds, the script verifies all 25 official kit hashes, validates all table schemas, recomputes exact and noisy references, verifies Processor D compliance, and confirms that `report.md` matches `docs/report.md` byte-for-byte.

