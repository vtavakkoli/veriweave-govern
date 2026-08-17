<div align="center">

# VeriWeave Govern 

**Deterministic runtime governance, calibrated evidence validation, human-review routing, tamper-evident audit, and reproducible scientific evaluation for enterprise AI agents.**

[![CI](https://github.com/vtavakkoli/veriweave-govern/actions/workflows/ci.yml/badge.svg)](https://github.com/vtavakkoli/veriweave-govern/actions/workflows/ci.yml)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-green.svg)](LICENSE)
[![Research](https://img.shields.io/badge/GovernBench-30%20seeds-purple.svg)](RESEARCH.md)

[Quick start](#quick-start) · [Scientific evaluation](RESEARCH.md) · [Architecture](docs/ARCHITECTURE.md) · [Consulting model](docs/CONSULTING.md) · [Security](SECURITY.md)

</div>

> [!NOTE]
> VeriWeave Govern is open-source research and engineering software. It can support governance, evidence generation, testing, and readiness assessments, but it is **not legal advice, regulatory certification, or a complete production authorization boundary**.

## What it does

VeriWeave Govern sits in the execution path of an AI agent, workflow, API gateway, or tool router. It evaluates a proposed action against versioned organizational policies, validates required evidence, applies deterministic precedence, routes accountable human review, and records a tamper-evident audit envelope.

```text
Agent / workflow / API gateway
              |
              v
      VeriWeave Govern
      - match versioned rules
      - validate evidence
      - deny > review > allow
      - route human oversight
      - record audit evidence
              |
       +------+------+
       |      |      |
     allow  review  deny
```

The final authorization path does **not require an LLM**. LLMs may assist with policy drafting, candidate evidence retrieval, document classification, or explanation, but deterministic policy/evidence controls remain responsible for the final runtime decision.

## Core capabilities

| Area | Capability |
|---|---|
| Policy | Versioned YAML bundles, owners, lifecycle metadata, explicit predicates |
| Evaluation | Safe predicate DSL without Python `eval`; deterministic `deny > review > allow` |
| Fail-safe | Unknown/unmatched actions route to review rather than implicit allow |
| Evidence | Required-evidence gates, authority/freshness/signature checks, research calibration |
| Human oversight | Explicit accountable review queues and high-impact escalation |
| Integrity | Policy hashes, append-only SHA-256 audit chaining, optional HMAC signatures |
| Explainability | Matched rules, missing evidence, reasons, counterfactual decision changes |
| Research | GovernBench, 30-seed evaluation, 95% CIs, GASR, calibration, ablations, temporal replay |
| Standards | Technical crosswalks for EU AI Act, NIST AI RMF, and high-level ISO/IEC 42001 objectives |
| Consulting | Evidence-backed readiness workflow and VeriWeave Governance Readiness Index (VGRI) |

## Quick start

```bash
cp .env.example .env
# Replace all development secrets before any real deployment.
docker compose up --build -d govern
```

Open the dashboard at `http://localhost:8080`, OpenAPI at `http://localhost:8080/docs`, and health at `http://localhost:8080/health`.

Local development and package installation require **Python 3.13**.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
make lint
make test
```

## Runtime API

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Service and policy health |
| `GET` | `/v1/policies` | Active policy metadata and hashes |
| `POST` | `/v1/policies/reload` | Reload active bundles |
| `POST` | `/v1/evaluate` | Evaluate an agent action |
| `GET` | `/v1/audit` | Read recent audit records |
| `GET` | `/v1/audit/verify` | Verify the audit chain |

## Two benchmark layers

### 1. End-to-end service benchmark

The original engineering benchmark starts the real service container, submits manually authored governance scenarios through the public API, verifies decisions/evidence/audit behavior, and measures latency/throughput.

```bash
make benchmark
```

### 2. GovernBench scientific evaluation

The research layer adds independent generated benchmark realizations, learned evidence calibration, adversarial attacks, temporal policy evolution, baselines, ablations, confidence intervals, counterfactual certificates, and a human-evaluation protocol.

```bash
make research
# or a fast development run
make research-quick
```

Default scientific configuration: **30 independent seeds × 2,000 cases/seed** across public administration, healthcare, financial services, software-engineering agents, and enterprise-office agents.

The committed synthetic reference run reports VeriWeave accuracy `0.9888` with 95% CI `[0.9876, 0.9899]`, macro-F1 `0.9836`, and evidence AUROC `0.9836`. These numbers are **synthetic/oracle-labelled**, not evidence of real-world compliance effectiveness. See [`results/research-v1/`](results/research-v1/) and [`docs/SCIENTIFIC_EVALUATION.md`](docs/SCIENTIFIC_EVALUATION.md).

Research metrics include accuracy, macro-F1, false-allow/deny/review rates, Governance Attack Success Rate (GASR), Brier score, Expected Calibration Error, AUROC/AUPRC, temporal replay accuracy, and bootstrap 95% confidence intervals.

## Baselines and ablations

Built-in baselines: RBAC, ABAC, a deterministic language-style proxy, and VeriWeave. The language-style proxy is explicitly **not** labelled as an actual LLM experiment. OPA/Rego and Cedar policy examples plus an external executable contract are included so official policy engines can be run and version-pinned for publication-quality comparisons.

Ablations remove the evidence gate, contradiction detection, human-review gate, OOD fail-safe, deny precedence, and temporal replay to quantify which controls contribute to safety.

## Counterfactual governance certificates

The research layer can produce a machine-readable governance certificate with the observed decision, accepted/minimal evidence, missing evidence, policy version, reasons, and decision-changing counterfactuals such as removing evidence or changing data exposure to `external + secret`.

Production deployments should bind certificates to the real audit-chain record/hash rather than treating a research certificate as a standalone security token.

## Human validation

The repository intentionally does not invent human-study results. [`docs/HUMAN_EVALUATION.md`](docs/HUMAN_EVALUATION.md) defines a protocol for independently annotated cases, decision time/confidence, pairwise Cohen's kappa, and human-only vs human+VeriWeave comparison. A CSV template and scorer are included.

## Standards crosswalks

[`standards/`](standards/) maps technical capabilities to selected public concepts from Regulation (EU) 2024/1689, the NIST AI RMF 1.0 functions, and the public objectives of ISO/IEC 42001:2023. These mappings support evidence navigation and assessment work; they do not create automatic legal conformity or ISO certification.

## Consulting use

[`docs/CONSULTING.md`](docs/CONSULTING.md) defines a reusable assessment model: AI/agent inventory, tool/action inventory, risk and data-classification mapping, policy digitization, GovernBench/client-case testing, governance red-teaming, evidence-gap analysis, runtime pilot, reviewer operating model, and remediation roadmap.

The optional VGRI utility scores policy coverage, evidence quality, human oversight, auditability, security, resilience, and operational readiness. It is a transparent readiness indicator, not a certification score.

```bash
python -m consulting.readiness consulting/assessment-template.json
```

## Repository structure

```text
app/                    production FastAPI service and governance engine
benchmark/              end-to-end service benchmark
research/               GovernBench, calibration, metrics, baselines, experiments
consulting/             assessment/readiness utilities
standards/              technical governance crosswalks
config/policies/         example runtime policies
docs/                   architecture, science, human study, cases, consulting
tests/                  runtime and research tests
results/research-v1/    versioned synthetic reference results
```

## Production boundary

Before production use, add or validate identity/workload authentication, authorization for administrative endpoints, durable persistence, tenant isolation, secret management, rate limiting, observability/SIEM integration, backups, key rotation, signed policy approval workflows, operational runbooks, and independent security review. See [`SECURITY.md`](SECURITY.md) and [`ROADMAP.md`](ROADMAP.md).

## Project status

**v0.3.0 is a scientific-governance benchmark edition and integration foundation.** It is suitable for research, demonstrations, controlled pilots, benchmark development, consulting assessments, and integration work. Real-world claims require real data, independent annotation, and organization-specific validation.

## Citation and license

Citation metadata is provided in [`CITATION.cff`](CITATION.cff). Licensed under the **Apache License 2.0**; see [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).
