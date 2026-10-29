# Phase 2 PS-S1 status and checkpoint record

## State at checkpoint

**Stages A–D are complete; final local validation passes.** Integrity/bootstrap, official notebook smoke test, Processor D scan/freeze, Bell results, exact references, all required N=4 VQE starts and aggregates, layer study, noisy D rows, resource comparison, required figures, research extensions, executed `main.ipynb`, README/report, number audit, viva sheet, verifier, and pytest suite are complete. A local-only package commit and subsequent audit-closure commit exist; no remote, portal, push, publication, organizer contact, or submission action has occurred.

The verified source payload is `handoff_payload/OFFICIAL_KIT/` and was not edited. The v3.4 paste and the v3.4 master-prompt section are saved at repository root. The project `README.md` necessarily replaces the kit's project-root README after copying; its original official content is preserved byte-exactly at `reference/official-kit/README.md`. The validator checks the entire payload manifest and all work-copy hashes, with that one README destination exception explicitly recorded.

## Clock, deadline source, and elapsed checkpoints

- Latest shell clock capture: `2026-10-29T11:10:06+00:00` (UTC), equivalent to `2026-10-29T16:40:06+05:30` in Asia/Kolkata. This is a sandbox clock capture, not a competition start time.
- Prior captured shell time: `2026-10-29T10:16:45+00:00`; elapsed interval from that capture to this one: 18 minutes 24 seconds. Earlier capture intervals are retained in `docs/AUDIT_LOG.md`; none is the competition elapsed time.
- User/team-relayed source: a 24-hour competition window. The actual start timestamp/date was not supplied or captured, so time remaining and the real two-hour reserve window cannot be calculated.
- Embedded official DOCX (inspected in place using namespace-aware OOXML text extraction) says the hackathon runs Day 1 6:00 PM through Day 2 6:00 PM IST; the official README and DOCX give a final commit/repository-URL deadline of Day 2 5:40 PM IST. These are relative day labels; the event date is not provided in the kit files.
- The final two hours should remain reserved per instruction; because the actual start/date is unknown, no claim is made that the current checkpoint is inside or outside that reserve. Local Git commits do not represent an official portal submission; no remote push or submission is claimed.
- The Phase 1 local baseline commit is `163599ad2cb8691d3b62f5b8bd9ca3730679b715`; its Git remote list is empty and no public Phase 1 URL was found in the supplied local README/metadata.

## Environment and integrity

- OS/shell: Linux, bash. PowerShell is unavailable; no PowerShell command is claimed.
- Dedicated environment: `.venv`, Python 3.13.16; Qiskit 1.4.6; qiskit-aer 0.18.0; NumPy 2.4.6; SciPy 1.17.1; Matplotlib 3.11.2; notebook 7.6.3; nbconvert 7.17.2; ipykernel 7.4.0; test-only pytest 9.2.0, pluggy 1.7.0 and iniconfig 2.3.1. `pip check`: `No broken requirements found.` Exact local list is `requirements-local-lock.txt`; pytest is a separate dev addition and official `requirements.txt` remains unchanged.
- The exact paste was accessible at `QFF2026_PHASE2_ALL_IN_ONE_PASTE_BUNDLE.txt` (140,139 bytes); `MASTER_PROMPT_v3.4.md` is 33,837 bytes. Safe embedded kit records were decoded to `handoff_payload/OFFICIAL_KIT/`, header sizes and SHA-256 values checked, and the official `MANIFEST.sha256` passed all 25/25 listed file checks. No missing-kit substitution was made.
- Official DOCX remains `.docx` in the verified payload; its text was inspected using Python stdlib `zipfile` + namespace-aware XML parsing. Attempting to import `python-docx` in `.venv` failed because it is not in the pinned requirements; the OOXML extraction succeeded without converting or editing the DOCX.
- Work copies of `qff_sim.py` and `tools/check_processor_d.py` match official SHA-256 values `dd0305834f88164f01f9b2a17f7333eb48a966cb81951b1953eed0e218de4cfc` and `09b1af7ddc8ee17b369e15308847ffc371dacb7820f5b3e101824b2d1deb85b4`. Locked instance JSONs, schema, official starter, and requirements remain unmodified. Official payload is the source of truth.

## Completed scientific work

### Bootstrap / Stage A

- Executed the official starter notebook in the dedicated environment; it completed without cell errors in 4.463 seconds. It reported Qiskit 1.4.6/Aer 0.18.0, Processor D check OK, and simulation output. nbconvert gave nonfatal warnings about an unsupported `cwd` config option and one missing cell ID. The executed smoke-test artifact is `results/starter_sim_executed.ipynb`; it is explicitly not final benchmark evidence.
- Temporary ring Processor D passed the official checker for required-qubit sizes 4 and 6; this placeholder was replaced by the selected D.
- Screened 12 variants: four topologies × CX/CZ/RZZ. All candidates passed validation and all six forced-layout Bell compile checks (72 compile combinations total). Pareto set: ring/RZZ, grid_2x3/RZZ, chorded_ring/RZZ; all tie on the six recorded Pareto dimensions. `src/scan_processor_d.py` sorts by `(n4_two_q,n4_depth,far_bell_mean_two_q,graph_diameter,basis_rank,topology_name)`; with RZZ tied, ascending lexical name selects `chorded_ring` before `grid_2x3` and `ring`. The frozen `processors/processor_D.json` matches that recorded tie-break; selection is not claimed to be uniquely superior by measured performance.
- D has 6 qubits and 7 edges `(0,1),(0,3),(0,5),(1,2),(2,3),(3,4),(4,5)`, graph diameter 3. Final JSON passed `tools/check_processor_d.py processors/processor_D.json 4` and `... 6`.
- Candidate metrics at N=4,L=2: A=12 two-qubit gates/depth 25/0 SWAP; B=12/25/0; D=6/17/0. Candidate table and Pareto diagnostics are `results/tables/d_candidates.csv` and `results/tables/d_shortlist_bell_diagnostics.csv`.
- Official Bell experiment wrote four rows to `results/tables/bell.csv` at 4,096 shots per basis. Adjacent `0-1` noisy F=`0.959839 ± 0.002184`; distance-3 `1-4` noisy F=`0.938354 ± 0.002685`; ideal values were 1.0.

### Stage B: exact references / VQE / noisy / resources

- Exact spectra: all seven N=4 instances match supplied E0/E1 metadata at absolute tolerance `1e-9`.
- Pilot L-BFGS-B: success, E=`-4.69498844916`, 270 function calls, 0.367 seconds. Production optimizer selection and settings are in raw metadata and `src/run_s1.py`.
- N=4 sweep: all 7 g values × L=1..4 × seeds 0,1,2; 84 raw start rows, 28 aggregate rows and 28 layer-study rows. Sum of per-start optimizer wall times captured by the script: 161.41 seconds. Two `success=False` iteration-limit records were retained: `(g=1.5,L=4,seed=2)` with energy error `1.6149e-5`, and `(g=2.0,L=4,seed=0)` with energy error `9.0195e-4`. The aggregate rule is best final energy among required seeds and copies every aggregate field from that winning seed.
- Strict best-of-three minimum L for `|energy error|<1e-3`: g=0.25→4, 0.50→4, 0.75→4, 1.00→3, 1.25→4, 1.50→3, 2.00→3. L=4 errors are at most `5.88e-13` in the CSV.
- Noisy density-matrix runs on D use selected circuits `(g=.5,L=4,seed=0)`, `(g=1,L=3,seed=2)`, `(g=2,L=3,seed=2)`. Noisy fidelities are `0.892449`, `0.923128`, `0.919267`; noisy energy errors are `0.299678`, `0.265723`, `0.535349` respectively. Values are from the official synthetic model, not hardware.
- `resources.csv` contains the selected L=3 HVA and ZZ Bell circuit on A/B/D. HVA A/B: 18 two-qubit gates, depth 36, two-qubit depth 12, no SWAPs; D: 9, depth 24, two-qubit depth 6, no SWAPs.
- Required figures produced: `phase_observables_vs_g.png`, `layer_study_convergence.png`, `bell_comparison.png`, `processor_D_topology.png`, `noisy_vs_ideal_energy.png`.

### Separate research extensions

- Exact gap/half-chain entropy: 14 rows (N=4 and 6 × 7 locked g values), saved to `results/additional/criticality.csv` with `results/figures/criticality_gap_entropy.png`.
- p2-only hypothetical sensitivity: 12 rows at alpha `{1,1.25,1.5,2}` × g `{0.5,1,2}`. The isolated extension helper matched official alpha=1 energy and fidelity exactly at all three g values. Results are in `results/additional/p2_sensitivity.csv`; figure labels explicitly say synthetic/hypothetical, not measured crosstalk.
- Optional N=6 VQE was attempted after the mandatory N=4 checks, but only L=1..4 was completed; exact references and 84 start rows are saved under `results/additional/s1_n6_*`. Only g=2.0 reached the strict layer threshold by L=4, and one iteration-limit start is retained. This is an incomplete bonus attempt, not a completed N=6 tier. PS-S2/PS-S3; N=6 noisy D results; full N=6 A/B/D resource/capacity tables; ZNE/readout mitigation; live hardware; portal use; publish/push/submit were not run. No exact thermodynamic critical point is claimed.

## Reproducibility and final audit status

- `main.ipynb` is executed with `RECOMPUTE=False`; it checks reference metadata, runs Processor D checks for 4/6, verifies 84/28/28 result coverage, prints key rows, and renders seven figures. Latest clean-kernel nbconvert invocation exited 0 in 4.522 seconds; only a kernel transport warning occurred (no cell errors). Images are embedded in the executed notebook.
- Final official starter smoke test: `.venv/bin/jupyter nbconvert --to notebook --execute starter/starter_sim.ipynb --output starter_sim_executed.ipynb --output-dir results --ExecutePreprocessor.timeout=1800` exited 0 in 4.365 seconds, wrote `results/starter_sim_executed.ipynb`; no cell errors. The official starter still warns of one missing cell ID and the ephemeral kernel’s unencrypted TCP transport.
- `.venv/bin/python -m pytest -q`: `3 passed in 1.30s`. `.venv/bin/python -m pip check`: `No broken requirements found.` `.venv/bin/python verify_submission.py`: exit 0; output confirms manifest/work-copy hashes 25/25, schemas/coverage/figures/notebook/audit valid, D checks at 4 and 6, 84 raw starts, two non-converged starts retained, three noisy rows, and three alpha=1 baseline comparisons.
- `README.md`, `report.md`, the audit/number docs, verifier, and test suite are maintained. Number audit maps key claims to source paths, row selectors, and columns. The official DOCX gives an approximate 4–8 page report target; rendered page count is NOT VERIFIED because no approved Markdown-to-PDF/print renderer is available in this environment.
- Final user-requested audit rechecked the source payload manifest, checker at 4/6, table schemas and data, Bell equations, VQE seed-to-aggregate provenance, noisy rows/parameters, notebook outputs, selection key, resource coverage, and Git state. Detailed commands, corrected verification-command mistakes, and outputs are in `docs/AUDIT_LOG.md`.
- Added `docs/DEMO_WALKTHROUGH.md`, `docs/RESULTS_AT_GLANCE.md`, and `docs/JUDGE_QA.md` using verified saved results and existing figures only; no new figure, simulation, optimizer run, or measurement was introduced. The submission verifier now checks that these handoff documents exist.
- The actual candidate runner is `src/scan_processor_d.py`; the requested `stage_a_pipeline.py` path does not exist. `d_candidates.csv` is at `results/tables/d_candidates.csv`. The selection key ends with ascending lexical topology name, which uniquely resolves the three identical RZZ Pareto rows to chorded_ring. This audit clarified the comment and report; no D selection or dependent result changed.
- Source/number checks found no scientific-data mismatch. The official `cx` metric is described as a generic two-qubit-family count for RZZ/CZ candidates. The resources table has the six expected HVA/Bell-auto-layout × A/B/D rows; no required row is missing. The work folder initially had no `.git`; the initial Git repository/commits were created later by the prior local agent.
- Current `HEAD` remains `72c73da84b62c89e8fd7014eb6a0cd2b508f1ccf`. Its author/committer identity `Arena.ai Agent Mode <agent@local.invalid>` is not verified as a team submission identity. No further commit was made during this audit. Seven tracked audit/documentation clarifications plus four new rubric/judge docs and the separate optional N=6 runner are uncommitted for human review; Git status is dirty. No remote is configured, and the Phase 1 baseline remains untouched.
- Submission destination remains unresolved: Phase 1 local repo has no remote URL and the public Phase 1 URL is absent; v3.4 prohibits remote/portal action without human authorization. No push or portal submission is attempted.

## Rubric-first final mission (2026-10-29)

- Created `docs/FINAL_RUBRIC_MATRIX.md` with official DOCX section/table and evidence mapping; it records verified PASS items, portal/repository NOT VERIFIED, and optional N=6 bonus incomplete. Official source hashes and the 25/25 manifest are included.
- A fresh deep check independently recomputed all N=4 raw energies, F/F2, four observables, noisy-D energies/fidelities, Bell F/SE; all passed. Official checker at N=4 and N=6 passed. Verifier, pytest, pip check, and diff check passed after the matrix was added; see the matrix and audit log for exact output.
- N=6 attempt is explicitly supplemental and incomplete: 7/7 exact E0/E1 checks and 84 unique starts through L=4 validate; only g=2 reached the strict threshold, one failed iteration-limit message is retained, and N=6 noisy D/resource tier is absent. No N=6 rows were added to official N=4 tables.
- No confirmed defect was found in mandatory N=4 scientific outputs, so no scientific output was regenerated or altered. Documentation was corrected to disclose the partial N=6 result. No remote action or new commit was made.


## Clean release-copy finalization (2026-10-29)

This section records the Windows finalization of the standalone release copy extracted from the user-supplied `workspace-01a18784-d25e-7f03-a991-0a1c874bcb3f.zip`. It is the release folder, separate from the active edited `qff2026-phase2-s1-work` workspace; no files in that active worktree were changed. Earlier entries above describe the archive's prior Linux checkpoint and are historical.

- Added the public Phase 1 URL supplied in the request and named all four team members in the README/report. Removed the old README warning banner and missing-link sentence while retaining an AI-use disclosure.
- Updated `processors/processor_D.json::justification` to state the measured bottleneck: A/B have zero HVA routing SWAPs; the CX-RZ-CX interaction uses 12 two-qubit gates at N=4,L=2 versus 6 for RZZ, and the selected L=3 circuit uses 18 versus 9. The documented p1/p2/readout rates are .001/.005/.01; the synthetic model assigns RZZ the same p2 as CX/CZ.
- Expanded `results/tables/resources.csv` to nine schema-correct rows: both CX and RZZ HVA encodings on A/B/D, plus Bell auto-layout rows on A/B/D. The official `s1_results.csv`, `s1_noisy.csv`, Bell results and raw VQE tables were not regenerated. `s1_noisy.csv` remains D-only, and the report explicitly says density-matrix state fidelity models gate noise only, with no readout noise folded in.
- Added `src/compare_processor_p2.py`, `results/additional/p2_processor_comparison.csv` (36 rows), and the 300-DPI `results/figures/p2_processor_comparison.png`. It reuses saved selected HVA parameters across A/B/D at g=.5,1,2 and alpha=1,1.25,1.5,2; p1=.001 and configured readout=.01 are fixed. D has lower energy error and higher gate-noisy state fidelity at all 12 tested g×alpha points under this synthetic model.
- Kept exact N=4/N=6 gap and half-chain entropy results and plots. No N=6 optional VQE job was running when checked. The existing N=6 VQE data remains incomplete and is not claimed as a bonus.
- Added byte-identical `docs/report.md`; updated README, number audit, judge Q&A, demo, viva, and rubric evidence. Re-executed `main.ipynb` in saved-results mode (`RECOMPUTE=False`) with the p2 comparison figure visible inline.
- Final environment used for the Windows rerun: Python 3.11.9; Qiskit 1.4.6; qiskit-aer 0.18.0; NumPy 2.4.6; SciPy 1.17.1; Matplotlib 3.11.2; nbconvert 7.17.2; notebook 7.6.3. `jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=-1 main.ipynb` exited 0. It emitted non-fatal Windows ZMQ warnings.
- `verify_submission.py` exited 0, including official manifest/work-copy hashes 25/25, exact CSV schemas, finite numeric values, raw/aggregate/reference checks, Bell/noisy/resource checks, all 36 p2 comparison rows, notebook/docs/figures, and both Processor D checks. Direct N=4 and N=6 checker invocations each printed `OK - Processor D satisfies all design rules.`
- The standalone release copy did not contain Git metadata initially; it is now the local release target. No remote was added, no push was run, and no portal action was taken. The Phase 2 target remote is not yet configured. The user-requested push commands are provided separately.

- Pinned test dependencies were installed into a temporary package-local directory, the existing `tests/` suite passed (`13 passed in 10.24s`), then the temporary dependencies and generated caches were removed. `pip check` in the dedicated simulation environment reported `No broken requirements found.`
- Added `.gitattributes` with `* -text` so Git on Windows preserves the byte-exact official source files and the release SHA-256 inventory instead of converting line endings.
