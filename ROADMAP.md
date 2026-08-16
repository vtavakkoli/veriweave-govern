# Product and research roadmap

This roadmap communicates direction, not a binding delivery commitment.

## Delivered in v0.3 — Scientific governance benchmark foundation

- GovernBench synthetic multi-domain generator and adversarial families
- 30-seed evaluation with confidence intervals and safety metrics
- learned evidence calibration
- baseline/ablation framework
- counterfactual governance certificates and temporal replay
- human-evaluation protocol
- standards crosswalks and consulting readiness tooling

**Boundary:** the committed benchmark is synthetic/oracle-labelled. External validity remains an explicit next milestone.

## Milestone 1 — Real-world scientific validation

- independently annotated sanitized governance cases
- 10–20 practitioner human study, with inter-rater agreement
- human-only vs human+VeriWeave evaluation
- pinned official OPA and Cedar engine runs
- real organizational policy/evidence case studies where approvals permit
- dataset/version cards, provenance, train/test isolation and reproducibility bundle

**Exit criteria:** core effectiveness claims are supported by independently reviewed non-synthetic cases and reproducible baseline runs.

## Milestone 2 — Hardened single-tenant pilot

- OIDC authentication and workload identity
- PostgreSQL persistence and migrations
- role-based administration
- quotas/rate limits and idempotency
- structured logs, metrics and OpenTelemetry traces
- secret-manager integration/key rotation
- backup, restore, retention and operational runbooks

## Milestone 3 — Governed policy lifecycle

- signed policy bundles and trusted publisher keys
- draft/review/approve/activate/deprecate/revoke states
- four-eyes approval and separation of duties
- policy diff, validation, rollback and effective dates
- immutable approval evidence linked to active policy sets

## Milestone 4 — Enterprise integrations

- ServiceNow/Jira/BMC review queues
- SharePoint/Confluence/Git policy synchronization
- SIEM and immutable-object-storage audit export
- API-gateway, agent-platform and semantic-router adapters
- asynchronous review completion

## Milestone 5 — Multi-tenant platform

- tenant isolation and tenant-scoped encryption
- organization/project/environment namespaces
- delegated administration and fine-grained authorization
- usage metering, migration and disaster recovery

## Milestone 6 — Evidence certification research

- provenance-robust evidence selection
- counterfactual omitted-evidence checks integrated with runtime audit
- temporal supersession detection
- claim-level support/contradiction certificates
- calibrated thresholds validated on human-labelled corpora
- formal/differential policy analysis with external verification engines
