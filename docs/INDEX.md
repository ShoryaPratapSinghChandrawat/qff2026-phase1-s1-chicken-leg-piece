# Documentation Index & Reviewer Guide

This directory contains complete technical reports, audit logs, presentation scripts, and verification crosswalks for the **QFF 2026 Phase 2 (PS-S1)** project.

---

## 📖 Primary Deliverables

| Document | Description | Target Audience |
|:---|:---|:---|
| **[`report.md`](report.md)** | **Formal Technical Report** (~5 pages): Problem formulation, HVA implementation, Processor D design, Bell experiments, exact references, and research extensions. (Byte-identical to root `report.md`). | **All Reviewers & Judges** |
| **[`PRESENTATION_PITCH.md`](PRESENTATION_PITCH.md)** | **5-Minute Pitch Script & 12 Viva Q&As**: Scripted presentation outline plus top 12 likely judge questions answered with exact CSV-backed figures. | **Presentation Judges** |
| **[`RESULTS_AT_GLANCE.md`](RESULTS_AT_GLANCE.md)** | **Executive Results Summary**: High-level scorecard summarizing $L_{\min}$ convergence, Processor D metrics, and Bell fidelities. | **Quick Review (2 mins)** |
| **[`SEED_STABILITY.md`](SEED_STABILITY.md)** | **Multi-Seed Stability Analysis**: Detailed breakdown of seed-to-seed variance across the 7 field values at their selected minimal layers. | **Algorithmic Reviewers** |

---

## 🔍 Verification, Rubric & Integrity

| Document | Description | Target Audience |
|:---|:---|:---|
| **[`FINAL_RUBRIC_MATRIX.md`](FINAL_RUBRIC_MATRIX.md)** | **Rubric Crosswalk**: Systematic mapping of the official 100-point hackathon evaluation criteria to concrete evidence files in this repository. | **Scoring Judges** |
| **[`NUMBER_AUDIT.md`](NUMBER_AUDIT.md)** | **Numerical Provenance Audit**: Line-by-line audit tracing every single number claimed in the report and README back to reproducible CSVs. | **Technical Auditors** |
| **[`JUDGE_QA.md`](JUDGE_QA.md)** | **Methodological FAQ**: In-depth technical justifications for architecture choices, noise modeling, and non-convex optimization behavior. | **Quantum Computing Judges** |
| **[`VIVA_DEFENSE.md`](VIVA_DEFENSE.md)** | **Theoretical Defense Sheet**: Theoretical underpinnings of the TFIM model, Hamiltonian symmetries, and finite-size scaling. | **Theory & Physics Judges** |

---

## 🛠️ Reproduction & Audit Trail

| Document | Description | Target Audience |
|:---|:---|:---|
| **[`DEMO_WALKTHROUGH.md`](DEMO_WALKTHROUGH.md)** | **Live Demo Walkthrough**: Terminal commands and expected outputs for reproducing the complete simulation pipeline. | **Hands-on Reproducers** |
| **[`STATUS.md`](STATUS.md)** | **Project Status & Checkpoints**: Chronological development history, audit checkpoints, and teammate alignment notes. | **Audit & Project History** |
| **[`AUDIT_LOG.md`](AUDIT_LOG.md)** | **Cryptographic Audit Log**: Historical log of test runs, environment validations, and Git commit checkpoints. | **Integrity Verification** |
| **[`AUDIT_BASELINE.sha256`](AUDIT_BASELINE.sha256)** | **Checksum Baseline**: Cryptographic SHA-256 hashes of baseline documentation deliverables. | **Security / Tamper-evident Check** |

---

## 🚀 Recommended Reading Paths

- **Quick Review (3 Minutes):** Read [`RESULTS_AT_GLANCE.md`](RESULTS_AT_GLANCE.md), then check the 60-second reviewer path in root `README.md`.
- **Full Scientific Evaluation (15 Minutes):** Read [`report.md`](report.md), inspect `main.ipynb`, and review [`FINAL_RUBRIC_MATRIX.md`](FINAL_RUBRIC_MATRIX.md).
- **Viva & Defense Preparation (10 Minutes):** Review [`PRESENTATION_PITCH.md`](PRESENTATION_PITCH.md) and [`SEED_STABILITY.md`](SEED_STABILITY.md).
- **Strict Reproducibility Audit (5 Minutes):** Execute `python verify_submission.py && python -m pytest -q` and inspect [`NUMBER_AUDIT.md`](NUMBER_AUDIT.md).

