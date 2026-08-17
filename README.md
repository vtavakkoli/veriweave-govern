<div align="center">

# VeriWeave Govern

**Deterministic runtime governance, calibrated evidence validation, human-review routing, tamper-evident audit, and reproducible scientific evaluation for enterprise AI agents.**

[![CI](https://github.com/vtavakkoli/veriweave-govern/actions/workflows/ci.yml/badge.svg)](https://github.com/vtavakkoli/veriweave-govern/actions/workflows/ci.yml)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-green.svg)](LICENSE)
[![Research](https://img.shields.io/badge/GovernBench-30%20seeds-purple.svg)](RESEARCH.md)
[![Publication](https://img.shields.io/badge/validation-EU%20%2B%20Austria-5a46d6.svg)](research/validation/README.md)

[Quick start](#quick-start) · [Research](RESEARCH.md) · [Publication validation](#publication-validation) · [Architecture](docs/ARCHITECTURE.md) · [Security](SECURITY.md)

</div>

> [!NOTE]
> VeriWeave Govern is open-source research and engineering software. It can
> support governance, evidence generation, testing and readiness assessments,
> but it is **not legal advice, regulatory certification, or a complete
> production authorization boundary**.

## What it does

VeriWeave Govern sits in the execution path of an AI agent, workflow, API
gateway or tool router. It evaluates a proposed action against versioned
organizational policies, validates required evidence, applies deterministic
precedence, routes accountable human review and records a tamper-evident audit
envelope.

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

The final authorization path does **not require an LLM**. LLMs may assist with
policy drafting, candidate evidence retrieval, document classification or
explanation, but deterministic policy/evidence controls remain responsible for
the final runtime decision.

## Core capabilities

| Area | Capability |
|---|---|
| Policy | Versioned YAML bundles, owners, lifecycle metadata, explicit predicates |
| Evaluation | Safe predicate DSL without Python `eval`; deterministic `deny > review > allow` |
| Fail-safe | Unknown/unmatched actions route to review rather than implicit allow |
| Evidence | Required-evidence gates, authority/freshness/signature checks, learned research calibration |
| Human oversight | Explicit accountable review queues and high-impact escalation |
| Integrity | Policy hashes, append-only SHA-256 audit chaining, optional HMAC signatures |
| Explainability | Matched rules, missing evidence, reasons, legal-source provenance and counterfactuals |
| Research | GovernBench, 30-seed evaluation, 95% CIs, GASR, calibration, ablations and temporal replay |
| Publication | 150 EU/Austria cases, blind annotation, OPA, Cedar and real local Ollama baseline |
| Performance | Real Docker API load matrix across multiple concurrency levels |
| Consulting | Evidence-backed readiness workflow and VeriWeave Governance Readiness Index (VGRI) |

## Quick start

```bash
cp .env.example .env
# Replace all development secrets before any real deployment.
docker compose up --build -d govern
```

Open the dashboard at `http://localhost:8080`, OpenAPI at
`http://localhost:8080/docs`, and health at `http://localhost:8080/health`.

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
|---|---|
| `GET` | `/health` | Service and policy health |
| `GET` | `/v1/policies` | Active policy metadata and hashes |
| `POST` | `/v1/policies/reload` | Reload active bundles |
| `POST` | `/v1/evaluate` | Evaluate an agent action |
| `GET` | `/v1/audit` | Read recent audit records |
| `GET` | `/v1/audit/verify` | Verify the audit chain |

## Evaluation layers

### 1. End-to-end service benchmark

The engineering benchmark starts the real service container, submits manually
authored governance scenarios through the public API, verifies
decision/evidence/audit behavior, and measures latency/throughput.

```bash
make benchmark
```

Outputs include `results/benchmark-report.html` and
`results/benchmark-results.json`.

### 2. GovernBench scientific evaluation

The synthetic research layer adds independent generated benchmark realizations,
learned evidence calibration, adversarial attacks, temporal policy evolution,
baselines, ablations, confidence intervals and counterfactual certificates.

```bash
make research
```

Default configuration is **30 independent seeds × 2,000 cases/seed** across
public administration, healthcare, financial services, software-engineering
agents and enterprise-office agents.

The committed synthetic reference run reports VeriWeave accuracy `0.9888` with
95% CI `[0.9876, 0.9899]`, macro-F1 `0.9836`, and evidence AUROC `0.9836`.
These are **synthetic/oracle-labelled results**, not evidence of real-world
compliance effectiveness.

### 3. Publication validation

The publication layer is deliberately separate from GovernBench. It contains
**150 regulation-grounded candidate cases**:

- 50 public-administration actions;
- 50 enterprise IT / DevOps actions;
- 50 data-handling / AI-governance actions.

The source registry is snapshot-versioned and links each case to official EU
and Austrian legal sources. The set includes current-law cases and separately
marked future-effective Austrian NISG 2026 readiness cases. The six 25-case CSV
partitions are intentionally small enough for manual review.

The first publication run generates two blind annotation worksheets under
`results/publication/`; they omit provisional labels, provisional rationales,
prohibition metadata and system predictions. The report computes Cohen's kappa
when both independent worksheets are complete and switches to human-adjudicated
ground truth only after all 150 adjudications are present.

The external publication comparators are:

| Method | Publication implementation |
|---|---|
| RBAC | deterministic reference baseline |
| ABAC | deterministic reference baseline |
| OPA/Rego | real OPA 1.17.0 engine |
| Cedar | real `cedar-policy-cli` 4.12.0 |
| Local LLM | real Ollama structured-output call, default `gemma3n:e2b` |
| VeriWeave | deterministic governor with separately trained evidence calibrator |

Prepare the local edge model:

```bash
ollama pull gemma3n:e2b
ollama list
```

Then run the publication profile:

```bash
docker compose --profile publication up --build \
  --abort-on-container-exit --exit-code-from publication publication
```

The Docker runner reaches host Ollama through
`http://host.docker.internal:11434`. Override `OLLAMA_BASE_URL` or
`OLLAMA_MODEL` if needed.

For the complete paper artifact, run the synthetic study plus the full Docker
publication suite:

```bash
make research
make publication-suite
```

`publication-suite` runs the end-to-end benchmark, the OPA/Cedar/Ollama
regulation-grounded comparison, and a real API load matrix. The load matrix
defaults to at least 10,000 requests at each concurrency level `1,4,16,32`
(at least 40,000 requests total). For an approximately 100,000-request run:

```bash
LOAD_MATRIX_REQUESTS_PER_LEVEL=25000 make publication-load
```

Publication results are written to:

```text
results/publication/
├── report.html
├── report.json
├── calibration-reliability.svg
├── predictions.csv
├── external-details.jsonl
├── annotator-a.csv
├── annotator-b.csv
└── adjudication.csv

results/
├── benchmark-report.html
├── benchmark-results.json
├── load-matrix.html
└── load-matrix.json
```

Until the two annotation sheets and adjudication are complete, the publication
report is visibly marked **DRAFT — HUMAN VALIDATION REQUIRED**. The repository
does not invent human-study results.

See [`research/validation/README.md`](research/validation/README.md) and
[`research/policy_baselines/README.md`](research/policy_baselines/README.md).

## Baselines and ablations

GovernBench includes RBAC, ABAC, a deterministic language-style proxy and
VeriWeave. The proxy is explicitly **not** labelled as an actual LLM
experiment. The publication profile adds actual OPA, Cedar and Ollama execution.

Ablations remove the evidence gate, contradiction detection, human-review gate,
OOD fail-safe, deny precedence and temporal replay to quantify which controls
contribute to safety.

## Evidence calibration

The evidence model exposes a trust score used by a thresholded acceptance gate.
Research reports Brier score, Expected Calibration Error, AUROC/AUPRC,
reliability bins and a generated SVG reliability diagram. The score should not
be presented as a perfectly calibrated real-world probability without separate
empirical calibration evidence.

## Counterfactual governance certificates

Research certificates contain the observed decision, accepted/minimal evidence,
missing evidence, policy version, reasons, legal-source provenance and
decision-changing counterfactuals. Production deployments should bind
certificates to the real audit-chain record/hash rather than treat a research
certificate as a standalone security token.

## Human validation

[`docs/HUMAN_EVALUATION.md`](docs/HUMAN_EVALUATION.md) defines the independent
annotation and adjudication protocol. Human results are reported only after
actual annotations are supplied.

## Standards and legal-source boundary

[`standards/`](standards/) contains technical crosswalks for selected public
concepts from the EU AI Act, NIST AI RMF and high-level ISO/IEC 42001
objectives. `research/validation/regulatory_sources.json` adds a publication
snapshot of official EU/Austrian sources used by the 150-case validation set.

These mappings support research, evidence navigation and assessment work; they
do not create automatic legal conformity or certification.

## Consulting use

[`docs/CONSULTING.md`](docs/CONSULTING.md) defines a reusable assessment model:
AI/agent inventory, tool/action inventory, risk/data classification, policy
digitization, client-case testing, governance red-teaming, evidence-gap
analysis, runtime pilot, reviewer operating model and remediation roadmap.

```bash
python -m consulting.readiness consulting/assessment-template.json
```

## Repository structure

```text
app/                         production FastAPI service and governance engine
benchmark/                   end-to-end service and load-matrix benchmarks
research/                    GovernBench and publication research code
research/validation/         EU/Austria cases and official-source registry
research/policy_baselines/   OPA and Cedar publication policies
consulting/                  assessment/readiness utilities
standards/                   technical governance crosswalks
config/policies/             example runtime policies
docs/                        architecture, science, human study and consulting
tests/                       runtime, research and publication-contract tests
results/research-v1/         versioned synthetic reference results
```

## Production boundary

Before production use, add or validate identity/workload authentication,
authorization for administrative endpoints, durable persistence, tenant
isolation, secret management, rate limiting, observability/SIEM integration,
backups, key rotation, signed policy approval workflows, operational runbooks
and independent security review. See [`SECURITY.md`](SECURITY.md) and
[`ROADMAP.md`](ROADMAP.md).

## Project status

**v0.4.0 is the publication-validation edition.** It is suitable for research,
demonstrations, controlled pilots, benchmark development, consulting
assessments and integration work. Real-world regulatory effectiveness claims
still require completed independent annotation, adjudication and
organization-specific validation.

## Citation and license

Citation metadata is provided in [`CITATION.cff`](CITATION.cff). Licensed under
the **Apache License 2.0**; see [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).
