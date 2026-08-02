<div align="center">

# VeriWeave Govern

**Deterministic policy enforcement, evidence validation, human-review routing, and tamper-evident audit for enterprise AI agents.**

[![CI](https://github.com/vtavakkoli/veriweave-govern/actions/workflows/ci.yml/badge.svg)](https://github.com/vtavakkoli/veriweave-govern/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/docker-compose-2496ED.svg?logo=docker&logoColor=white)](docker-compose.yml)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-green.svg)](LICENSE)
[![Status: MVP](https://img.shields.io/badge/status-product--quality%20MVP-7c3aed.svg)](#project-status)

[Quick start](#quick-start) · [Architecture](docs/ARCHITECTURE.md) · [Benchmark](#benchmark) · [Security](SECURITY.md) · [Roadmap](ROADMAP.md) · [License](#license)

</div>

> [!NOTE]
> VeriWeave Govern is open-source software under the Apache License 2.0.
> It is an engineering and research MVP, not a legal-compliance certification
> or a complete production authorization boundary.

## Overview

VeriWeave Govern is a local-first governance control plane designed to sit in
the execution path of an AI agent, automated workflow, API gateway, or tool
router. It evaluates an intended action against approved organizational
policies, validates the evidence required to justify that action, and returns a
deterministic `allow`, `review`, or `deny` decision.

Every decision records:

- the attempted action and relevant context;
- the active policy set and matched rule versions;
- supplied, accepted, rejected, and missing evidence;
- deterministic precedence and decision reasons;
- the accountable human-review queue, when required;
- a hash-chained audit envelope suitable for later verification.

The product direction combines **Policy-as-Skill** governance concepts with
provenance and verification methods developed in **VeriWeave-VITA-PRO**.

## Why VeriWeave Govern

Many governance tools primarily document systems after deployment. VeriWeave
Govern is intended to enforce policy **before an agent action proceeds**.

```text
Agent / workflow / API gateway
              |
              v
      VeriWeave Govern API
      - match active rules
      - validate evidence
      - apply deny > review > allow
      - identify accountable reviewer
      - append audit record
              |
       +------+------+
       |      |      |
     allow  review  deny
```

The decision path is deterministic and does not require an LLM. LLMs or
retrieval systems may provide candidate evidence, but policy enforcement and
evidence gates remain explicit and testable.

## Core capabilities

| Area | Capability |
|---|---|
| Policy | Versioned YAML policy bundles with owners, lifecycle status, tags, and rules |
| Evaluation | Safe predicate DSL without Python `eval` |
| Precedence | Deterministic `deny > review > allow` reduction |
| Fail-safe behavior | Unmatched actions are routed to review rather than silently allowed |
| Evidence | Required-evidence gates, quality scoring, freshness, signatures, and authority checks |
| Human oversight | Explicit review queues carried in policy and decision responses |
| Integrity | Policy-content hashes, policy-set hashes, and append-only SHA-256 audit chaining |
| Verification | Optional HMAC audit signatures and audit-chain verification endpoint |
| Operations | FastAPI, OpenAPI, browser dashboard, health endpoint, Docker Compose, and CI |
| Evaluation | Unit tests plus an end-to-end benchmark with HTML and JSON reports |

## Quick start

### Docker Compose

```bash
cp .env.example .env
# Replace every development secret before use.
docker compose up --build -d govern
```

Open:

- Dashboard: `http://localhost:8080`
- OpenAPI: `http://localhost:8080/docs`
- Health: `http://localhost:8080/health`

Stop the service:

```bash
docker compose down --volumes --remove-orphans
```

### Local development

```bash
python -m venv .venv
source .venv/bin/activate       # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
ruff check app benchmark tests
pytest -q
python -m app.main
```

## Example evaluation

```bash
curl --request POST http://localhost:8080/v1/evaluate \
  --header 'Content-Type: application/json' \
  --data '{
    "agent_id": "procurement-agent",
    "action": "summarize",
    "context": {
      "impact": "low",
      "environment": "test",
      "data_classification": "internal"
    },
    "evidence": [{
      "evidence_id": "ev-001",
      "source_id": "approved-policy-library",
      "source_version": "2026.1",
      "evidence_type": "policy_reference",
      "content": "Policy section 4 permits read-only summarization with recorded evidence.",
      "authority": 90,
      "current": true,
      "signed": true
    }]
  }'
```

The response includes the final decision, matched rules, evidence assessments,
policy-set hash, review queue, reasons, and audit envelope.

## API surface

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Service and policy health |
| `GET` | `/v1/policies` | Active policy metadata and hashes |
| `POST` | `/v1/policies/reload` | Reload active policy bundles |
| `POST` | `/v1/evaluate` | Evaluate an agent action |
| `GET` | `/v1/audit` | Read recent audit records and integrity status |
| `GET` | `/v1/audit/verify` | Verify the complete audit chain |

## Policy example

```yaml
id: enterprise-ai-governance
name: Enterprise AI Governance Baseline
version: 1.0.0
status: active
owner: AI Governance Office
rules:
  - id: high-impact-human-review
    when:
      - field: context.impact
        operator: in
        value: [high, critical]
    decision: review
    required_evidence:
      - business_justification
      - risk_assessment
    min_evidence_score: 0.65
    review_queue: ai-governance-board
    reason: High-impact AI actions require documented evidence and human oversight.
```

Supported operators are `exists`, `eq`, `neq`, `in`, `not_in`, `contains`,
`starts_with`, `gte`, `lte`, and `truthy`.

## Benchmark

The benchmark starts a real service container, waits for readiness, submits
manually authored governance scenarios through the public API, validates the
expected decisions and evidence behavior, profiles concurrent latency, checks
the signed audit chain, and writes self-contained reports.

```bash
make benchmark
```

Generated artifacts:

```text
results/benchmark-report.html
results/benchmark-results.json
```

A detached workflow is also available:

```bash
make benchmark-detached
```

Configure benchmark load with environment variables:

```bash
BENCHMARK_ITERATIONS=25 \
BENCHMARK_CONCURRENCY=8 \
docker compose up --build --abort-on-container-exit --exit-code-from test test
```

The supplied scenarios cover trusted evidence, missing evidence, outdated or
unsigned evidence, protected-data exfiltration, deny-over-review precedence,
high-impact review, production controls, rollback evidence, fail-safe handling,
and API validation.

## Repository structure

```text
veriweave-govern/
├── app/                  FastAPI service and governance engine
├── benchmark/            End-to-end benchmark runner and scenarios
├── config/policies/      Example policy bundles
├── docs/                 Architecture and operational documentation
├── tests/                Deterministic unit tests
├── results/              Generated benchmark artifacts
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## Security and production boundary

This repository is an integration foundation, not a complete production
security boundary or legal-compliance certification. Before production use,
add identity, authorization, durable storage, tenant isolation, secret
management, rate limiting, observability, backup, key rotation, policy approval
workflows, and independent security review.

See [`SECURITY.md`](SECURITY.md) for vulnerability reporting and
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the current system boundary.

## Roadmap

The production roadmap includes OIDC and workload identity, PostgreSQL and
migrations, tenant isolation, signed policy bundles, four-eyes approval,
enterprise review-system connectors, VeriWeave evidence certificates,
OpenTelemetry and SIEM export, key rotation, and external audit anchoring.

See [`ROADMAP.md`](ROADMAP.md) for milestones and exit criteria.

## Project status

**Version 0.2.0 is a product-quality MVP and integration foundation.** It is
appropriate for evaluation, demonstrations, controlled pilots, research, and
integration development. It is not yet presented as a certified compliance
product, autonomous legal decision-maker, or production authorization boundary.

## Contributing and support

Read [`CONTRIBUTING.md`](CONTRIBUTING.md) and
[`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) before proposing changes. Use
[`SUPPORT.md`](SUPPORT.md) for support channels and scope. Security issues must
follow the private process in [`SECURITY.md`](SECURITY.md).

## Citation

Citation metadata is provided in [`CITATION.cff`](CITATION.cff). GitHub can
generate BibTeX and other formats from the repository's **Cite this repository**
control.

## License

Licensed under the **Apache License 2.0**. You may use, modify, and distribute
this software subject to the terms in [`LICENSE`](LICENSE). Attribution notices
are provided in [`NOTICE`](NOTICE).
