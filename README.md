# VeriWeave Govern

**VeriWeave Govern** is a local-first policy enforcement and evidence-governance control plane for enterprise AI agents.

It turns approved organizational policies into deterministic runtime decisions and records:

- what an agent attempted;
- which policy version matched;
- what evidence was supplied;
- whether that evidence met the required trust threshold;
- why the action was allowed, denied, or routed to human review;
- which review queue owns the decision;
- the tamper-evident audit record created for the evaluation.

The product direction combines **Policy-as-Skill** governance concepts with the provenance and verification methods developed in **VeriWeave-VITA-PRO**.

> **Status:** product-quality MVP and integration foundation. It is not a legal-compliance certification, autonomous legal decision-maker, or complete production security boundary by itself.

## Why it is different

Many AI-governance products primarily document systems after deployment. VeriWeave Govern is designed to sit directly in the execution path of an AI agent or automated workflow.

```text
Agent requests an action
          |
          v
VeriWeave Govern
  - match active policy rules
  - validate required evidence
  - enforce deny / review / allow
  - route accountable human review
  - append a tamper-evident audit record
          |
          v
Action proceeds only under organizational controls
```

## MVP capabilities

- FastAPI governance service with OpenAPI documentation
- YAML policy bundles with versions, owners, status, tags, and rules
- safe predicate DSL without Python `eval`
- deterministic precedence: `deny > review > allow`
- fail-safe review when no policy rule matches
- evidence-quality scoring and required-evidence gates
- explicit human-review queues
- policy-content and policy-set hashes
- append-only SHA-256 audit chain
- optional HMAC audit signatures
- audit-chain verification endpoint
- interactive browser dashboard
- hardened Docker Compose baseline
- unit tests for allow, escalation, human review, denial, precedence, fail-safe behavior, and audit tampering
- end-to-end Docker benchmark with manually defined scenarios and HTML/JSON reports

## Run with Docker

```bash
cp .env.example .env
# Replace the development signing key in .env
docker compose up --build -d govern
```

Open:

- Dashboard: `http://localhost:8080`
- OpenAPI: `http://localhost:8080/docs`
- Health: `http://localhost:8080/health`

Stop the service:

```bash
docker compose down
```

## Run the comprehensive benchmark

The benchmark starts a real VeriWeave Govern container, waits for its health check, submits manually authored governance scenarios through the public API, verifies the decisions and evidence behavior, runs a concurrent latency profile, validates the signed audit chain, and writes a self-contained HTML report.

### Detached Docker run

```bash
mkdir -p results
docker compose up --build -d test
docker compose logs -f test
```

The legacy Compose command is equivalent:

```bash
docker-compose up --build -d test
```

The benchmark container exits when the run is complete. Generated files are written to the host:

```text
results/benchmark-report.html
results/benchmark-results.json
```

Open `results/benchmark-report.html` in any browser. The report includes:

- scenario pass/fail accuracy;
- expected and actual decisions;
- matched policy rules and review queues;
- missing and rejected evidence;
- full request and response details;
- mean, median, P95, P99, and maximum latency;
- sequentially aggregated throughput;
- decision distribution;
- policy-set hash;
- audit-chain integrity and head hash.

### Foreground run with exit status

For local development or CI, use the foreground target. It returns a nonzero exit code when a scenario, performance request, or audit-integrity check fails.

```bash
make benchmark
```

To use the detached workflow and wait for its result:

```bash
make benchmark-detached
```

### Configure benchmark load

```bash
BENCHMARK_ITERATIONS=25 \
BENCHMARK_CONCURRENCY=8 \
docker compose up --build --abort-on-container-exit --exit-code-from test test
```

Defaults are 10 iterations per benchmark scenario and concurrency 4.

### Add or change scenarios

Edit [`benchmark/scenarios.json`](benchmark/scenarios.json). Each scenario contains:

- an identifier, name, category, and description;
- the complete `/v1/evaluate` request;
- expected HTTP status and governance decision;
- optional matched-rule, review-queue, missing-evidence, evidence-score, signature, and reason assertions;
- an optional `benchmark: false` flag for correctness-only cases such as API validation errors.

The supplied catalog covers:

1. low-risk allow with trusted evidence;
2. escalation when required evidence is absent;
3. rejection of outdated and unsigned evidence;
4. protected-data exfiltration denial;
5. deny-over-review precedence;
6. high-impact human-review routing;
7. missing risk-assessment detection;
8. production deployment controls;
9. missing rollback-plan detection;
10. fail-safe handling of unknown actions;
11. fail-safe handling of uncovered external sending;
12. API request validation.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
python -m pip install -e ".[dev]"
ruff check app benchmark tests
pytest -q
python -m app.main
```

Against an already running service, the benchmark can also be executed directly:

```bash
veriweave-govern-benchmark \
  --base-url http://localhost:8080 \
  --iterations 10 \
  --concurrency 4
```

## Example evaluation

```bash
curl -X POST http://localhost:8080/v1/evaluate \
  -H "Content-Type: application/json" \
  -d '{
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

A response contains the final decision, matched policy rules, evidence assessments, active policy-set hash, review queue, and audit envelope.

## API

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Service and policy health |
| `GET` | `/v1/policies` | Active policy metadata and hashes |
| `POST` | `/v1/policies/reload` | Reload active policy bundles |
| `POST` | `/v1/evaluate` | Evaluate an agent action |
| `GET` | `/v1/audit` | Recent audit records and chain integrity |
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

Supported operators are `exists`, `eq`, `neq`, `in`, `not_in`, `contains`, `starts_with`, `gte`, `lte`, and `truthy`.

## Product roadmap

The next milestone should add:

1. OIDC and workload identity
2. PostgreSQL and schema migrations
3. tenant isolation and role-based administration
4. signed policy bundles and approval workflows
5. ServiceNow, Jira, BMC Helix, SharePoint, and Confluence connectors
6. direct VeriWeave PRO evidence certificates
7. OpenTelemetry and SIEM export
8. external audit anchoring and key rotation

See [Architecture](docs/ARCHITECTURE.md) for the system boundary and production-hardening roadmap.
